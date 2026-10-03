"""
collision.py - GTA:SA COL3 Binary Collision Generator
Creates fully standard COL3 collision files with precise bounding boxes,
bounding spheres, collision boxes, and collision mesh (int16 fixed-point
vertices and indexed triangular faces with surface materials).
"""

import struct
import numpy as np


# GTA SA Material IDs for collisions
COL_MAT_DEFAULT  = 0
COL_MAT_CONCRETE = 1
COL_MAT_GRASS    = 2
COL_MAT_DIRT     = 3
COL_MAT_PAVEMENT = 5  # Standard road/street surface
COL_MAT_METAL    = 6
COL_MAT_GLASS    = 7
COL_MAT_SAND     = 18
COL_MAT_WATER    = 19
COL_MAT_WOOD     = 20
COL_MAT_STONE    = 26


class COLBuilder:
    def __init__(self, model_name="col_model"):
        self.model_name = model_name
        self.boxes = []      # list of (min_pt, max_pt, material_id)
        self.spheres = []    # list of (center, radius, material_id)
        self.vertices = []   # list of (x, y, z) float
        self.faces = []      # list of (v0, v1, v2, material_id)

    def add_box(self, min_pt, max_pt, material=COL_MAT_CONCRETE):
        self.boxes.append((min_pt, max_pt, material))

    def add_sphere(self, center, radius, material=COL_MAT_CONCRETE):
        self.spheres.append((center, radius, material))

    def add_mesh(self, vertices, faces, default_mat=COL_MAT_CONCRETE):
        """
        Adds 3D vertices and triangular faces.
        vertices: (N, 3) float
        faces: list of (v0, v1, v2) or (v0, v1, v2, material_id)
        """
        base_v = len(self.vertices)
        for v in vertices:
            self.vertices.append((float(v[0]), float(v[1]), float(v[2])))

        for f in faces:
            if len(f) == 3:
                v0, v1, v2 = f
                mat = default_mat
            else:
                v0, v1, v2, mat = f
            self.faces.append((base_v + v0, base_v + v1, base_v + v2, mat))

    def build_binary(self):
        # Calculate global bounding box and sphere
        all_pts = []
        for v in self.vertices:
            all_pts.append(v)
        for b_min, b_max, _ in self.boxes:
            all_pts.append(b_min)
            all_pts.append(b_max)
        for c, r, _ in self.spheres:
            all_pts.append((c[0] - r, c[1] - r, c[2] - r))
            all_pts.append((c[0] + r, c[1] + r, c[2] + r))

        if not all_pts:
            all_pts = [(-1, -1, -1), (1, 1, 1)]

        arr = np.array(all_pts, dtype=np.float32)
        b_min = arr.min(axis=0)
        b_max = arr.max(axis=0)
        center = (b_min + b_max) * 0.5
        dists = np.linalg.norm(arr - center, axis=1)
        radius = float(dists.max()) if len(dists) > 0 else 1.0

        # Offsets are relative to file offset 4 (after 'COL3')
        # Header is 120 bytes total. Start of payload = 120 - 4 = 116.
        cur_offset = 116

        # Spheres section
        num_spheres = len(self.spheres)
        offset_spheres = cur_offset if num_spheres > 0 else 0
        sphere_bytes = bytearray()
        for (cx, cy, cz), r, mat in self.spheres:
            # 12 bytes center, 4 bytes radius, 4 bytes TSurface
            sphere_bytes.extend(struct.pack('<ffffBBBB', cx, cy, cz, r, mat, 0, 255, 0))
        cur_offset += len(sphere_bytes)

        # Boxes section
        num_boxes = len(self.boxes)
        offset_boxes = cur_offset if num_boxes > 0 else 0
        box_bytes = bytearray()
        for (minx, miny, minz), (maxx, maxy, maxz), mat in self.boxes:
            # 24 bytes bounds, 4 bytes TSurface
            box_bytes.extend(struct.pack('<ffffffBBBB', minx, miny, minz, maxx, maxy, maxz, mat, 0, 255, 0))
        cur_offset += len(box_bytes)

        # Vertices section
        num_verts = len(self.vertices)
        offset_verts = cur_offset if num_verts > 0 else 0
        vert_bytes = bytearray()
        for vx, vy, vz in self.vertices:
            # Fixed-point x128 clamped to int16 range
            ix = int(np.clip(vx * 128.0, -32768, 32767))
            iy = int(np.clip(vy * 128.0, -32768, 32767))
            iz = int(np.clip(vz * 128.0, -32768, 32767))
            vert_bytes.extend(struct.pack('<hhh', ix, iy, iz))

        # 4-byte alignment padding for vertices
        pad_len = (4 - (len(vert_bytes) % 4)) % 4
        vert_bytes.extend(b'\x00' * pad_len)
        cur_offset += len(vert_bytes)

        # Faces section
        num_faces = len(self.faces)
        offset_faces = cur_offset if num_faces > 0 else 0
        face_bytes = bytearray()
        for a, b, c, mat in self.faces:
            face_bytes.extend(struct.pack('<HHHBB', a, b, c, mat, 0))
        cur_offset += len(face_bytes)

        # Header fields
        name_clean = self.model_name.encode('ascii')[:21].ljust(22, b'\x00')
        model_id = 0

        bounds_data = struct.pack(
            '<fffffffff f',
            b_min[0], b_min[1], b_min[2],
            b_max[0], b_max[1], b_max[2],
            center[0], center[1], center[2],
            radius
        )

        flags = 2  # Not empty
        header_fields = struct.pack(
            '<HHHBB IIIIII IIII',
            num_spheres,
            num_boxes,
            num_faces,
            0,             # num_lines
            0,             # pad
            flags,
            offset_spheres,
            offset_boxes,
            0,             # offset_lines
            offset_verts,
            offset_faces,
            0,             # offset_triangle_planes
            0,             # shadow_faces
            0,             # offset_shadow_verts
            0              # offset_shadow_faces
        )

        header_minus_size = name_clean + struct.pack('<H', model_id) + bounds_data + header_fields
        payload = bytes(sphere_bytes) + bytes(box_bytes) + bytes(vert_bytes) + bytes(face_bytes)

        # Total size after fileSize field (4 bytes) is len(header_minus_size) + len(payload)
        file_size = len(header_minus_size) + len(payload)
        return b'COL3' + struct.pack('<I', file_size) + header_minus_size + payload

    def save(self, filepath):
        data = self.build_binary()
        with open(filepath, 'wb') as f:
            f.write(data)
        return len(data)
