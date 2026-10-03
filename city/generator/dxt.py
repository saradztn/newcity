"""
dxt.py - Vectorized DXT1 / DXT5 Block Encoder and Mipmap Chain Generator
Encodes raw RGBA image arrays into Direct3D 9 standard BC1 (DXT1) and BC3 (DXT5) blocks.
Conforms strictly to RenderWare 3.6 / GTA SA PC texture specifications.
"""

import struct
import numpy as np
from PIL import Image


def _blocks(img):
    """Reshapes (H, W, C) image into (N, 16, C) 4x4 blocks."""
    h, w, c = img.shape
    return img.reshape(h // 4, 4, w // 4, 4, c).transpose(0, 2, 1, 3, 4).reshape(-1, 16, c)


def _to565(c):
    """Quantizes (N, 3) float [0..255] RGB into uint16 5:6:5 representation."""
    c = np.clip(np.rint(c), 0, 255).astype(np.int32)
    r = (c[..., 0] * 31 + 127) // 255
    g = (c[..., 1] * 63 + 127) // 255
    b = (c[..., 2] * 31 + 127) // 255
    return (r << 11) | (g << 5) | b


def _from565(v):
    """Expands uint16 5:6:5 integer back into (N, 3) float [0..255] RGB."""
    r = (v >> 11) & 31
    g = (v >> 5) & 63
    b = v & 31
    r = (r << 3) | (r >> 2)
    g = (g << 2) | (g >> 4)
    b = (b << 3) | (b >> 2)
    return np.stack([r, g, b], -1).astype(np.float32)


def encode_dxt1_blocks(px):
    """
    Compresses (N, 16, 3) 4x4 pixel blocks into (N, 8) DXT1 bytes using
    Principal Component Analysis (PCA) along the maximum variance axis.
    """
    N = px.shape[0]
    mean = px.mean(axis=1, keepdims=True)
    d = px - mean
    cov = np.einsum('nki,nkj->nij', d, d) / 16.0
    cov += np.eye(3)[None] * 1e-6
    _, v = np.linalg.eigh(cov)
    axis = v[:, :, -1]  # (N, 3) principal axis

    t = np.einsum('nki,ni->nk', d, axis)
    tmin = t.min(axis=1)
    tmax = t.max(axis=1)

    inset = (tmax - tmin) / 16.0
    ca = mean[:, 0] + axis * (tmin + inset)[:, None]
    cb = mean[:, 0] + axis * (tmax - inset)[:, None]

    qa = _to565(ca)
    qb = _to565(cb)

    swap = qa < qb
    q0 = np.where(swap, qb, qa)
    q1 = np.where(swap, qa, qb)
    same = (q0 == q1)

    c0 = _from565(q0)
    c1 = _from565(q1)
    pal = np.stack([c0, c1, (2 * c0 + c1) / 3.0, (c0 + 2 * c1) / 3.0], 1)

    dist = ((px[:, :, None, :] - pal[:, None, :, :]) ** 2).sum(-1)
    idx = dist.argmin(-1).astype(np.uint32)
    idx[same] = 0

    bits = np.zeros(N, np.uint32)
    for k in range(16):
        bits |= idx[:, k] << np.uint32(2 * k)

    out = np.zeros((N, 8), np.uint8)
    out[:, 0] = (q0 & 255)
    out[:, 1] = (q0 >> 8) & 255
    out[:, 2] = (q1 & 255)
    out[:, 3] = (q1 >> 8) & 255
    for k in range(4):
        out[:, 4 + k] = (bits >> np.uint32(8 * k)) & 255
    return out


def encode_alpha_blocks(a):
    """Compresses (N, 16) float [0..255] alpha into (N, 8) DXT5 alpha blocks."""
    N = a.shape[0]
    a0 = np.clip(np.rint(a.max(axis=1)), 0, 255)
    a1 = np.clip(np.rint(a.min(axis=1)), 0, 255)
    same = (a0 == a1)
    a0 = np.where(same, np.minimum(a0 + 1, 255), a0)
    a1 = np.where(same & (a0 == 255), 254, a1)

    pal = np.zeros((N, 8))
    pal[:, 0] = a0
    pal[:, 1] = a1
    for i in range(1, 7):
        pal[:, 1 + i] = ((7 - i) * a0 + i * a1) / 7.0

    dist = np.abs(a[:, :, None] - pal[:, None, :])
    idx = dist.argmin(-1).astype(np.uint64)
    bits = np.zeros(N, np.uint64)
    for k in range(16):
        bits |= idx[:, k] << np.uint64(3 * k)

    out = np.zeros((N, 8), np.uint8)
    out[:, 0] = a0.astype(np.uint8)
    out[:, 1] = a1.astype(np.uint8)
    for k in range(6):
        out[:, 2 + k] = ((bits >> np.uint64(8 * k)) & np.uint64(255)).astype(np.uint8)
    return out


def encode_mip_level(img, fmt='DXT1'):
    """img: uint8 (H, W, 3 or 4); fmt: 'DXT1' or 'DXT5' -> raw bytes."""
    h, w = img.shape[:2]
    assert h % 4 == 0 and w % 4 == 0, f"Dimensions must be divisible by 4: {w}x{h}"
    chunks = []
    imgf = img.astype(np.float32)
    B = _blocks(imgf)

    for s in range(0, len(B), 65536):
        blk = B[s:s + 65536]
        if fmt.upper() == 'DXT1':
            chunks.append(encode_dxt1_blocks(blk[..., :3]))
        else:
            al = encode_alpha_blocks(blk[..., 3] if blk.shape[-1] > 3 else np.full(blk.shape[:2], 255.0))
            co = encode_dxt1_blocks(blk[..., :3])
            chunks.append(np.concatenate([al, co], axis=1))

    return np.concatenate(chunks).tobytes()


def build_mip_pyramid(pil_image):
    """Downsamples image cleanly down to 1x1 using Box / Lanczos filter."""
    img_arr = np.array(pil_image, dtype=np.uint8)
    pyramid = [img_arr]
    cur = img_arr
    while cur.shape[0] > 1 or cur.shape[1] > 1:
        nh = max(1, cur.shape[0] // 2)
        nw = max(1, cur.shape[1] // 2)
        chans = [
            np.asarray(Image.fromarray(cur[..., c]).resize((nw, nh), Image.Resampling.BOX))
            for c in range(cur.shape[2])
        ]
        cur = np.stack(chans, -1)
        pyramid.append(cur)
    return pyramid


def compress_mipmap_chain(pil_image, fmt='DXT1'):
    """Returns list of (width, height, raw_bytes) for all mip levels down to 1x1."""
    if pil_image.mode not in ('RGB', 'RGBA'):
        pil_image = pil_image.convert('RGBA' if fmt.upper() == 'DXT5' else 'RGB')

    pyramid = build_mip_pyramid(pil_image)
    chain = []

    for lvl in pyramid:
        h, w = lvl.shape[:2]
        ph, pw = max(4, ((h + 3) // 4) * 4), max(4, ((w + 3) // 4) * 4)
        if (ph, pw) != (h, w):
            lvl = np.pad(lvl, ((0, ph - h), (0, pw - w), (0, 0)), mode='edge')
        chain.append((w, h, encode_mip_level(lvl, fmt)))

    return chain
