"""
rw_dff.py - RenderWare 3.6 DFF Binary Stream Generator
Generates fully compliant RenderWare Clump files for GTA:SA / MTA:SA.
Features exact binary structuring for FrameList, Geometry with Normals, UVs,
Prelit vertex colors, MaterialList with D3D9 texture references, BinMesh PLG,
and Atomic chunks.
"""

import struct
import numpy as np


RW_VERSION_SA = 0x1803FFFF  # RenderWare 3.6.0.3 (GTA:SA standard)

# RW Chunk IDs
ID_STRUCT        = 0x01
ID_STRING        = 0x02
ID_EXTENSION     = 0x03
ID_TEXTURE       = 0x06
ID_MATERIAL      = 0x07
ID_MATERIALLIST  = 0x08
ID_FRAMELIST     = 0x0E
ID_GEOMETRY      = 0x0F
ID_CLUMP         = 0x10
ID_ATOMIC        = 0x14
ID_GEOMETRYLIST  = 0x1A
ID_BINMESHPLG    = 0x050E

# Geometry format flags
rpGEOMETRYTRISTRIP               = 0x0001
rpGEOMETRYPOSITIONS              = 0x0002
rpGEOMETRYTEXTURED               = 0x0004
rpGEOMETRYPRELIT                 = 0x0008
rpGEOMETRYNORMALS                = 0x0010
rpGEOMETRYLIGHT                  = 0x0020
rpGEOMETRYMODULATEMATERIALCOLOR  = 0x0040
rpGEOMETRYTEXTURED2              = 0x0080


def make_rw_chunk(chunk_id, data, version=RW_VERSION_SA):
    """Wraps binary data with a 12-byte RenderWare chunk header."""
    return struct.pack('<III', chunk_id, len(data), version) + data


def make_string_chunk(text, version=RW_VERSION_SA):
    """Builds an aligned RenderWare string chunk (null-terminated, 4-byte padded)."""
    raw = text.encode('ascii', errors='ignore') + b'\x00'
    pad = (4 - (len(raw) % 4)) % 4
    if pad > 0:
        raw += b'\x00' * pad
    return make_rw_chunk(ID_STRING, raw, version)


def compute_bounding_sphere(vertices):
    """Calculates minimal enclosing bounding sphere (cx, cy, cz, radius)."""
    if len(vertices) == 0:
        return 0.0, 0.0, 0.0, 1.0
    min_pt = vertices.min(axis=0)
    max_pt = vertices.max(axis=0)
    center = (min_pt + max_pt) * 0.5
    dists = np.linalg.norm(vertices - center, axis=1)
    radius = float(dists.max()) if len(dists) > 0 else 1.0
    return float(center[0]), float(center[1]), float(center[2]), radius


class DFFMesh:
    """Represents a RenderWare 3.6 3D Mesh and generates DFF binary Clump."""
    def __init__(self, name="mesh"):
        self.name = name
        self.vertices = []      # (N, 3) float
        self.normals = []       # (N, 3) float
        self.uvs = []           # (N, 2) float
        self.colors = []        # (N, 4) uint8 RGBA
        self.triangles = []     # (M, 4) uint16 (v0, v1, v2, material_id)
        self.materials = []     # list of dicts: {'texture': 'name', 'color': (255,255,255,255)}

    def add_material(self, texture_name="", color=(255, 255, 255, 255)):
        clean_name = texture_name.split('.')[0] if texture_name else ""
        for i, m in enumerate(self.materials):
            if m['texture'] == clean_name and m['color'] == color:
                return i
        mat_id = len(self.materials)
        self.materials.append({
            'texture': clean_name,
            'color': color
        })
        return mat_id

    def build_binary(self):
        """Constructs full binary RenderWare Clump (DFF) payload."""
        verts = np.asarray(self.vertices, dtype=np.float32)
        norms = np.asarray(self.normals, dtype=np.float32)
        uvs = np.asarray(self.uvs, dtype=np.float32)
        num_verts = len(verts)

        if len(self.colors) > 0:
            cols = np.asarray(self.colors, dtype=np.uint8)
        else:
            cols = np.full((num_verts, 4), 255, dtype=np.uint8)

        # Ensure normals match vertices
        if len(norms) != num_verts:
            norms = np.zeros((num_verts, 3), dtype=np.float32)
            norms[:, 2] = 1.0

        # Ensure UVs match vertices
        if len(uvs) != num_verts:
            uvs = np.zeros((num_verts, 2), dtype=np.float32)

        tris = self.triangles
        num_triangles = len(tris)

        # 1. Build Geometry Struct
        # Format flags: Positions, Textured (1 UV set = 1 << 16), Prelit, Normals, Modulate
        flags = (1 << 16) | rpGEOMETRYPOSITIONS | rpGEOMETRYTEXTURED | rpGEOMETRYPRELIT | rpGEOMETRYNORMALS | rpGEOMETRYMODULATEMATERIALCOLOR

        geom_struct_hdr = struct.pack(
            '<IIII',
            flags, num_triangles, num_verts, 1
        )

        # Prelit colors (RGBA uint8)
        prelit_bytes = cols.tobytes()

        # UV coordinates (float32 pairs)
        uv_bytes = uvs.tobytes()

        # Triangle array (RenderWare order: v1, v0, mat_id, v2)
        tri_bytes_list = []
        for tri in tris:
            v0, v1, v2, mat_id = tri
            tri_bytes_list.append(struct.pack('<HHHH', v1, v0, mat_id, v2))
        tri_bytes = b''.join(tri_bytes_list)

        # Morph target 0
        cx, cy, cz, rad = compute_bounding_sphere(verts)
        morph_hdr = struct.pack('<ffffII', cx, cy, cz, rad, 1, 1)
        morph_bytes = morph_hdr + verts.tobytes() + norms.tobytes()

        geometry_struct_data = geom_struct_hdr + prelit_bytes + uv_bytes + tri_bytes + morph_bytes
        geometry_struct_chunk = make_rw_chunk(ID_STRUCT, geometry_struct_data)

        # 2. Build MaterialList
        num_mats = max(1, len(self.materials))
        matlist_struct_data = struct.pack('<i', num_mats) + struct.pack(f'<{num_mats}i', *([-1] * num_mats))
        matlist_struct_chunk = make_rw_chunk(ID_STRUCT, matlist_struct_data)

        mat_chunks = []
        mats_to_process = self.materials if len(self.materials) > 0 else [{'texture': '', 'color': (255, 255, 255, 255)}]
        for mat in mats_to_process:
            has_tex = bool(mat.get('texture'))
            r, g, b, a = mat.get('color', (255, 255, 255, 255))
            mat_struct_data = struct.pack(
                '<IBBBBIifff',
                0,                   # flags
                r, g, b, a,          # color RGBA
                0,                   # unused
                1 if has_tex else 0, # isTextured
                1.0,                 # ambient
                0.0,                 # specular
                1.0                  # diffuse
            )
            mat_struct_chunk = make_rw_chunk(ID_STRUCT, mat_struct_data)

            tex_chunk = b''
            if has_tex:
                tex_name = mat['texture']
                # Filter 6 (LinearMipLinear), Addressing 0x11 (WrapU | WrapV)
                tex_struct_data = b'\x06\x11\x00\x00'
                tex_struct_chunk = make_rw_chunk(ID_STRUCT, tex_struct_data)
                tex_name_chunk = make_string_chunk(tex_name)
                tex_mask_chunk = make_string_chunk("")
                tex_ext_chunk = make_rw_chunk(ID_EXTENSION, b'')
                tex_chunk = make_rw_chunk(ID_TEXTURE, tex_struct_chunk + tex_name_chunk + tex_mask_chunk + tex_ext_chunk)

            mat_ext_chunk = make_rw_chunk(ID_EXTENSION, b'')
            mat_chunk = make_rw_chunk(ID_MATERIAL, mat_struct_chunk + tex_chunk + mat_ext_chunk)
            mat_chunks.append(mat_chunk)

        matlist_chunk = make_rw_chunk(ID_MATERIALLIST, matlist_struct_chunk + b''.join(mat_chunks))

        # 3. BinMesh Plugin Chunk (inside Geometry Extension)
        # Group triangles by material
        mesh_splits = {}
        for tri in tris:
            v0, v1, v2, mat_id = tri
            if mat_id not in mesh_splits:
                mesh_splits[mat_id] = []
            mesh_splits[mat_id].extend([v0, v1, v2])

        if not mesh_splits:
            mesh_splits[0] = []

        total_indices = sum(len(idx_list) for idx_list in mesh_splits.values())
        binmesh_data = [struct.pack('<III', 0, len(mesh_splits), total_indices)]
        for m_id, idx_list in mesh_splits.items():
            binmesh_data.append(struct.pack('<II', len(idx_list), m_id))
            if len(idx_list) > 0:
                binmesh_data.append(struct.pack(f'<{len(idx_list)}I', *idx_list))

        binmesh_chunk = make_rw_chunk(ID_BINMESHPLG, b''.join(binmesh_data))
        geom_ext_chunk = make_rw_chunk(ID_EXTENSION, binmesh_chunk)

        geometry_chunk = make_rw_chunk(ID_GEOMETRY, geometry_struct_chunk + matlist_chunk + geom_ext_chunk)

        # 4. GeometryList Chunk
        geomlist_struct = make_rw_chunk(ID_STRUCT, struct.pack('<I', 1))
        geomlist_chunk = make_rw_chunk(ID_GEOMETRYLIST, geomlist_struct + geometry_chunk)

        # 5. FrameList Chunk (Root Frame)
        frame_data = struct.pack(
            '<fffffffff fff iI',
            1.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, 0.0, 1.0,
            0.0, 0.0, 0.0,
            -1,
            0x00020003
        )
        framelist_struct = make_rw_chunk(ID_STRUCT, struct.pack('<I', 1) + frame_data)
        framelist_ext = make_rw_chunk(ID_EXTENSION, b'')
        framelist_chunk = make_rw_chunk(ID_FRAMELIST, framelist_struct + framelist_ext)

        # 6. Atomic Chunk
        atomic_struct_data = struct.pack('<IIII', 0, 0, 5, 0)
        atomic_struct = make_rw_chunk(ID_STRUCT, atomic_struct_data)
        atomic_ext = make_rw_chunk(ID_EXTENSION, b'')
        atomic_chunk = make_rw_chunk(ID_ATOMIC, atomic_struct + atomic_ext)

        # 7. Clump Chunk (Root)
        clump_struct = make_rw_chunk(ID_STRUCT, struct.pack('<III', 1, 0, 0))
        clump_ext = make_rw_chunk(ID_EXTENSION, b'')
        clump_data = clump_struct + framelist_chunk + geomlist_chunk + atomic_chunk + clump_ext

        return make_rw_chunk(ID_CLUMP, clump_data)

    def save(self, filepath):
        data = self.build_binary()
        with open(filepath, 'wb') as f:
            f.write(data)
        return len(data)
