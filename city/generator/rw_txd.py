"""
rw_txd.py - RenderWare 3.6 TXD (Texture Dictionary) Binary Generator
Conforms strictly to Direct3D 9 RpRasterPC_Header specification (88 bytes).
Ensures GTA SA and MTA:SA correctly bind all native textures without falling back
to untextured white models.
"""

import struct
from PIL import Image
from .dds import get_raw_dxt_mipmaps

RW_VERSION_SA = 0x1803FFFF  # RenderWare 3.6.0.3

ID_STRUCT        = 0x01
ID_EXTENSION     = 0x03
ID_TEXTURENATIVE = 0x15
ID_TEXDICTIONARY = 0x16

D3DFMT_DXT1 = 0x31545844  # 'DXT1'
D3DFMT_DXT5 = 0x35545844  # 'DXT5'

RASTER_1555   = 0x0100
RASTER_565    = 0x0200
RASTER_4444   = 0x0400
RASTER_8888   = 0x0500
RASTER_MIPMAP = 0x0080


def make_rw_chunk(chunk_id, data, version=RW_VERSION_SA):
    return struct.pack('<III', chunk_id, len(data), version) + data


class TXDBuilder:
    def __init__(self):
        self.textures = []  # list of (name, pil_image, format_type, has_alpha)

    def add_texture(self, name, pil_image, format_type='DXT1', has_alpha=False):
        """Registers a texture into the dictionary."""
        clean_name = name.split('.')[0][:31]
        if format_type.upper() == 'DXT5':
            has_alpha = True
        self.textures.append((clean_name, pil_image, format_type, has_alpha))

    def build_binary(self):
        num_textures = len(self.textures)
        # TextureDictionary struct: count (uint16), deviceId (uint16 = 9 for Direct3D 9)
        dict_struct = make_rw_chunk(ID_STRUCT, struct.pack('<HH', num_textures, 9))

        native_chunks = []
        for name, img, fmt, has_alpha in self.textures:
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            is_dxt1 = (fmt.upper() == 'DXT1')
            d3d_fmt = D3DFMT_DXT1 if is_dxt1 else D3DFMT_DXT5

            if is_dxt1:
                raster_fmt = (RASTER_1555 if has_alpha else RASTER_565) | RASTER_MIPMAP
                depth = 16
            else:
                raster_fmt = RASTER_4444 | RASTER_MIPMAP
                depth = 32

            flags = 0x08 | (1 if has_alpha else 0)

            mips = get_raw_dxt_mipmaps(img, fmt.upper(), generate_mips=True)
            num_mips = len(mips)

            # Build name buffers (32 bytes null-padded)
            name_bytes = name.encode('ascii')[:31].ljust(32, b'\x00')
            mask_bytes = b''.ljust(32, b'\x00')

            w0, h0, _ = mips[0]

            # Direct3D 9 RpRasterPC_Header (88 bytes total):
            # TextureFormat (72 bytes):
            #   platformId: uint32 = 9 (D3D9)
            #   filter_and_addressing: uint32 = 0x1106 (linear-mip-linear 0x06, wrapU 0x01, wrapV 0x01)
            #   name: 32 bytes
            #   maskName: 32 bytes
            # RasterFormat (16 bytes):
            #   rasterFormat: uint32
            #   d3dFormat: uint32
            #   width: uint16
            #   height: uint16
            #   depth: uint8
            #   numLevels: uint8
            #   rasterType: uint8 = 4 (rwRASTERTYPETEXTURE)
            #   compression: uint8 = flags
            hdr = struct.pack(
                '<II32s32sIIHHBBBB',
                9,                  # platformId = Direct3D 9
                0x1106,             # linear-mip-linear + wrap/wrap
                name_bytes,
                mask_bytes,
                raster_fmt,
                d3d_fmt,
                w0,
                h0,
                depth,
                num_mips,
                4,                  # rasterType = texture
                flags
            )

            # Mipmap data blocks: for each mip level, uint32 size followed by raw DXT bytes
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
