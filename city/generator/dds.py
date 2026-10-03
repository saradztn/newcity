"""
dds.py - High-Performance Binary DirectDraw Surface (DDS) Generator
Supports DXT1 (BC1), DXT5 (BC3), and uncompressed 32-bit RGBA/BGRA formats
with automatic mipmap chain generation.
Compatible with MTA:SA (DirectX 9) and RenderWare.
"""

import struct
import numpy as np
from PIL import Image
import io


DDS_MAGIC = b'DDS '

# DDSD Flags
DDSD_CAPS = 0x00000001
DDSD_HEIGHT = 0x00000002
DDSD_WIDTH = 0x00000004
DDSD_PITCH = 0x00000008
DDSD_PIXELFORMAT = 0x00001000
DDSD_MIPMAPCOUNT = 0x00020000
DDSD_LINEARSIZE = 0x00080000

# DDSCAPS Flags
DDSCAPS_COMPLEX = 0x00000008
DDSCAPS_TEXTURE = 0x00001000
DDSCAPS_MIPMAP = 0x00400000

# DDPF Flags
DDPF_ALPHAPIXELS = 0x00000001
DDPF_ALPHA = 0x00000002
DDPF_FOURCC = 0x00000004
DDPF_RGB = 0x00000040


def rgb_to_565(r, g, b):
    r5 = (r * 31.0 / 255.0 + 0.5).astype(np.uint16)
    g6 = (g * 63.0 / 255.0 + 0.5).astype(np.uint16)
    b5 = (b * 31.0 / 255.0 + 0.5).astype(np.uint16)
    return (r5 << 11) | (g6 << 5) | b5


def c565_to_rgb(c):
    r = (((c >> 11) & 0x1F).astype(np.float32) * (255.0 / 31.0))
    g = (((c >> 5) & 0x3F).astype(np.float32) * (255.0 / 63.0))
    b = ((c & 0x1F).astype(np.float32) * (255.0 / 31.0))
    return np.stack([r, g, b], axis=-1)


def compress_dxt1_level(img_rgba):
    """Vectorized DXT1 compression of an RGBA image array (H, W, 4) uint8."""
    H, W, _ = img_rgba.shape
    pad_h = (4 - (H % 4)) % 4
    pad_w = (4 - (W % 4)) % 4
    if pad_h > 0 or pad_w > 0:
        img_rgba = np.pad(img_rgba, ((0, pad_h), (0, pad_w), (0, 0)), mode='edge')

    H, W, _ = img_rgba.shape
    rgb = img_rgba[..., :3].astype(np.float32)

    # Reshape into (N, 16, 3) blocks
    blocks = rgb.reshape(H // 4, 4, W // 4, 4, 3).swapaxes(1, 2).reshape(-1, 16, 3)
    N = blocks.shape[0]

    c_min = blocks.min(axis=1)
    c_max = blocks.max(axis=1)

    c0 = rgb_to_565(c_max[:, 0], c_max[:, 1], c_max[:, 2])
    c1 = rgb_to_565(c_min[:, 0], c_min[:, 1], c_min[:, 2])

    # Ensure c0 > c1 for 4-color opaque mode
    swap_mask = c0 < c1
    c0[swap_mask], c1[swap_mask] = c1[swap_mask], c0[swap_mask]
    eq_mask = (c0 == c1) & (c0 < 0xFFFF)
    c0[eq_mask] += 1

    p0 = c565_to_rgb(c0)
    p1 = c565_to_rgb(c1)
    p2 = (2.0 * p0 + p1) / 3.0
    p3 = (p0 + 2.0 * p1) / 3.0

    palette = np.stack([p0, p1, p2, p3], axis=1)  # (N, 4, 3)

    diff = blocks[:, :, None, :] - palette[:, None, :, :]  # (N, 16, 4, 3)
    dist = (diff ** 2).sum(axis=-1)  # (N, 16, 4)
    indices = dist.argmin(axis=-1).astype(np.uint32)  # (N, 16)

    shifts = np.arange(0, 32, 2, dtype=np.uint32)
    idx_packed = (indices << shifts[None, :]).sum(axis=-1).astype(np.uint32)

    out = np.zeros(N, dtype=[('c0', '<u2'), ('c1', '<u2'), ('indices', '<u4')])
    out['c0'] = c0
    out['c1'] = c1
    out['indices'] = idx_packed
    return out.tobytes()


def compress_dxt5_level(img_rgba):
    """Vectorized DXT5 (BC3) compression with alpha block and color block."""
    H, W, _ = img_rgba.shape
    pad_h = (4 - (H % 4)) % 4
    pad_w = (4 - (W % 4)) % 4
    if pad_h > 0 or pad_w > 0:
        img_rgba = np.pad(img_rgba, ((0, pad_h), (0, pad_w), (0, 0)), mode='edge')

    H, W, _ = img_rgba.shape
    N = (H // 4) * (W // 4)

    # 1. Alpha block
    alpha = img_rgba[..., 3]
    blocks_a = alpha.reshape(H // 4, 4, W // 4, 4).swapaxes(1, 2).reshape(-1, 16)
    a_min = blocks_a.min(axis=1)
    a_max = blocks_a.max(axis=1)

    a0 = a_max
    a1 = a_min
    a0_f = a0.astype(np.float32)
    a1_f = a1.astype(np.float32)

    # 8-step alpha interpolation
    pal_a = np.stack([
        a0_f,
        a1_f,
        (6.0 * a0_f + 1.0 * a1_f) / 7.0,
        (5.0 * a0_f + 2.0 * a1_f) / 7.0,
        (4.0 * a0_f + 3.0 * a1_f) / 7.0,
        (3.0 * a0_f + 4.0 * a1_f) / 7.0,
        (2.0 * a0_f + 5.0 * a1_f) / 7.0,
        (1.0 * a0_f + 6.0 * a1_f) / 7.0,
    ], axis=1)

    diff_a = np.abs(blocks_a[:, :, None].astype(np.float32) - pal_a[:, None, :])
    idx_a = diff_a.argmin(axis=2).astype(np.uint64)

    shifts_a = np.arange(0, 48, 3, dtype=np.uint64)
    packed_48 = (idx_a * (np.uint64(1) << shifts_a[None, :])).sum(axis=1)

    alpha_bytes = bytearray(N * 8)
    for i in range(N):
        val = int(packed_48[i])
        alpha_bytes[i * 8: i * 8 + 8] = bytes([
            a0[i], a1[i],
            val & 0xFF, (val >> 8) & 0xFF, (val >> 16) & 0xFF,
            (val >> 24) & 0xFF, (val >> 32) & 0xFF, (val >> 40) & 0xFF
        ])

    # 2. Color block (same as DXT1)
    color_bytes = compress_dxt1_level(img_rgba)

    # Interleave 8 bytes alpha + 8 bytes color
    out = bytearray(N * 16)
    for i in range(N):
        out[i * 16: i * 16 + 8] = alpha_bytes[i * 8: i * 8 + 8]
        out[i * 16 + 8: i * 16 + 16] = color_bytes[i * 8: i * 8 + 8]
    return bytes(out)


def generate_mipmaps(pil_image):
    """Generates downsampled mipmap PIL images down to 1x1."""
    mips = [pil_image]
    w, h = pil_image.size
    while w > 1 or h > 1:
        w = max(1, w // 2)
        h = max(1, h // 2)
        downsampled = pil_image.resize((w, h), Image.Resampling.LANCZOS)
        mips.append(downsampled)
    return mips


def create_dds_header(width, height, mipmap_count, fourcc=b'DXT1'):
    """Builds the 128-byte DDS header."""
    is_dxt1 = (fourcc == b'DXT1')
    block_size = 8 if is_dxt1 else 16
    pitch_or_linear = max(1, ((width + 3) // 4)) * block_size

    flags = DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT | DDSD_LINEARSIZE
    if mipmap_count > 1:
        flags |= DDSD_MIPMAPCOUNT

    caps = DDSCAPS_TEXTURE
    if mipmap_count > 1:
        caps |= DDSCAPS_COMPLEX | DDSCAPS_MIPMAP

    # DDPIXELFORMAT
    ddspf = struct.pack(
        '<II4sIIIII',
        32,              # dwSize
        DDPF_FOURCC,     # dwFlags
        fourcc,          # dwFourCC
        0, 0, 0, 0, 0    # RGBBitCount, R/G/B/A BitMasks
    )

    reserved1 = (0,) * 11
    header = struct.pack(
        '<4sIIIIIII11I32sII4I',
        DDS_MAGIC,
        124,             # dwSize
        flags,
        height,
        width,
        pitch_or_linear,
        0,               # depth
        mipmap_count,
        *reserved1,
        ddspf,
        caps,
        0, 0, 0, 0, 0    # caps2, reserved
    )
    return header


def save_image_to_dds(pil_image, output_path, format_type='DXT1', generate_mips=True):
    """
    Compresses a PIL Image and saves it as a valid DDS file.
    format_type: 'DXT1' or 'DXT5'
    """
    if pil_image.mode != 'RGBA':
        pil_image = pil_image.convert('RGBA')

    width, height = pil_image.size
    mips = generate_mipmaps(pil_image) if generate_mips else [pil_image]
    fourcc = format_type.encode('ascii')

    header = create_dds_header(width, height, len(mips), fourcc)

    data_blocks = []
    for mip in mips:
        arr = np.array(mip, dtype=np.uint8)
        if format_type == 'DXT1':
            block_data = compress_dxt1_level(arr)
        elif format_type == 'DXT5':
            block_data = compress_dxt5_level(arr)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        data_blocks.append(block_data)

    with open(output_path, 'wb') as f:
        f.write(header)
        for b in data_blocks:
            f.write(b)

    return len(header) + sum(len(b) for b in data_blocks)


def get_raw_dxt_mipmaps(pil_image, format_type='DXT1', generate_mips=True):
    """Returns a list of (width, height, raw_bytes) for TXD packaging."""
    if pil_image.mode != 'RGBA':
        pil_image = pil_image.convert('RGBA')

    mips = generate_mipmaps(pil_image) if generate_mips else [pil_image]
    out = []
    for mip in mips:
        arr = np.array(mip, dtype=np.uint8)
        if format_type == 'DXT1':
            b = compress_dxt1_level(arr)
        else:
            b = compress_dxt5_level(arr)
        out.append((mip.width, mip.height, b))
    return out
