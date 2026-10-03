"""
rw_txd.py - RenderWare 3.6 TXD (Texture Dictionary) Binary Generator
Creates standard GTA:SA compatible .txd files containing DXT1, DXT5,
or 32-bit native textures with full mipmap levels.
"""

import struct
from PIL import Image
from .dds import get_raw_dxt_mipmaps


RW_VERSION_SA = 0x1803FFFF

ID_STRUCT         = 0x01
ID_EXTENSION      = 0x03
ID_TEXTURENATIVE  = 0x15
ID_TEXDICTIONARY  = 0x16

D3DFMT_DXT1 = 0x31545844  # 'DXT1'
D3DFMT_DXT5 = 0x35545844  # 'DXT5'
D3DFMT_A8R8G8B8 = 21


def make_rw_chunk(chunk_id, data, version=RW_VERSION_SA):
    return struct.pack('<III', chunk_id, len(data), version) + data


class TXDBuilder:
    def __init__(self):
        self.textures = []  # list of (name, pil_image, format_type)

    def add_texture(self, name, pil_image, format_type='DXT1'):
        """Registers a texture into the dictionary."""
        # Sanitize name up to 31 chars
        clean_name = name.split('.')[0][:31]
        self.textures.append((clean_name, pil_image, format_type))

    def build_binary(self):
        num_textures = len(self.textures)
        dict_struct = make_rw_chunk(ID_STRUCT, struct.pack('<HH', num_textures, 9))

        native_chunks = []
        for name, img, fmt in self.textures:
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            is_dxt1 = (fmt.upper() == 'DXT1')
            d3d_fmt = D3DFMT_DXT1 if is_dxt1 else D3DFMT_DXT5
            raster_fmt = 0x1500 if is_dxt1 else 0x1700
            depth = 4 if is_dxt1 else 8

            mips = get_raw_dxt_mipmaps(img, fmt.upper(), generate_mips=True)
            num_mips = len(mips)
            total_data_size = sum(len(b) for _, _, b in mips)

            # Build name buffers (32 bytes null-padded)
            name_bytes = name.encode('ascii')[:31].ljust(32, b'\x00')
            mask_bytes = b''.ljust(32, b'\x00')

            w0, h0, _ = mips[0]

            hdr = struct.pack(
                '<IBBB32s32sIIHHBBBBI',
                9,                  # platformId = Direct3D 9
                0x02,               # filterFlags = linear
                0x01,               # wrapU = wrap
                0x01,               # wrapV = wrap
                name_bytes,
                mask_bytes,
                raster_fmt,
                d3d_fmt,
                w0,
                h0,
                depth,
                num_mips,
                4,                  # rasterType = texture
                8 if is_dxt1 else 8,# dxtCompression
                total_data_size
            )

            # Append mip levels: each has uint32 size followed by raw bytes
            mip_payload = bytearray()
            for _, _, b in mips:
                mip_payload.extend(struct.pack('<I', len(b)))
                mip_payload.extend(b)

            native_struct = make_rw_chunk(ID_STRUCT, hdr + bytes(mip_payload))
            native_ext = make_rw_chunk(ID_EXTENSION, b'')
            native_chunks.append(make_rw_chunk(ID_TEXTURENATIVE, native_struct + native_ext))

        dict_ext = make_rw_chunk(ID_EXTENSION, b'')
        dict_data = dict_struct + b''.join(native_chunks) + dict_ext
        return make_rw_chunk(ID_TEXDICTIONARY, dict_data)

    def save(self, filepath):
        data = self.build_binary()
        with open(filepath, 'wb') as f:
            f.write(data)
        return len(data)
