"""
lod.py - Level of Detail (LOD) Generation & Simplification Engine
Generates low-poly silhouette and envelope meshes for distant streaming,
enforcing polygon budgets and RenderWare compatibility.
"""

import numpy as np
from .rw_dff import DFFMesh


class LODGenerator:
    @staticmethod
    def create_bounding_envelope_lod(high_mesh, lod_texture_name="bldg_facade_modern"):
        """
        Creates a simplified envelope LOD mesh from a high-detail mesh.
        Calculates axis-aligned or stepped bounding boxes preserving outer silhouette.
        """
        verts = np.asarray(high_mesh.vertices, dtype=np.float32)
        if len(verts) == 0:
            return None

        min_pt = verts.min(axis=0)
        max_pt = verts.max(axis=0)

        # Create 8-vertex bounding box LOD
        x0, y0, z0 = min_pt
        x1, y1, z1 = max_pt

        lod_mesh = DFFMesh()
        mat_id = lod_mesh.add_material(lod_texture_name)

        lod_mesh.vertices = [
            [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],  # Bottom 0-3
            [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1],  # Top 4-7
        ]

        lod_mesh.normals = [
            [0, 0, -1], [0, 0, -1], [0, 0, -1], [0, 0, -1],
            [0, 0, 1],  [0, 0, 1],  [0, 0, 1],  [0, 0, 1],
        ]

        # Simple UV tiling
        h = max(z1 - z0, 1.0)
        lod_mesh.uvs = [
            [0, 0], [1, 0], [1, 1], [0, 1],
            [0, h * 0.1], [1, h * 0.1], [1, h * 0.1 + 1], [0, h * 0.1 + 1]
        ]

        # 12 triangles for 6 box faces
        lod_mesh.triangles = [
            # Bottom
            (0, 1, 2, mat_id), (0, 2, 3, mat_id),
            # Top
            (4, 6, 5, mat_id), (4, 7, 6, mat_id),
            # Front (y0)
            (0, 4, 5, mat_id), (0, 5, 1, mat_id),
            # Back (y1)
            (2, 6, 7, mat_id), (2, 7, 3, mat_id),
            # Left (x0)
            (0, 3, 7, mat_id), (0, 7, 4, mat_id),
            # Right (x1)
            (1, 5, 6, mat_id), (1, 6, 2, mat_id),
        ]

        return lod_mesh

    @staticmethod
    def simplify_mesh(high_mesh, target_reduction=0.7):
        """
        Subsamples vertices and creates a reduced triangle mesh.
        """
        verts = np.asarray(high_mesh.vertices, dtype=np.float32)
        tris = high_mesh.triangles
        if len(tris) <= 12:
            return LODGenerator.create_bounding_envelope_lod(high_mesh)

        step = max(2, int(1.0 / (1.0 - target_reduction)))
        # Subsample triangles
        reduced_tris = tris[::step]
        if len(reduced_tris) < 4:
            reduced_tris = tris[:4]

        # Remap vertices
        used_indices = set()
        for v0, v1, v2, _ in reduced_tris:
            used_indices.update([v0, v1, v2])

        old_to_new = {}
        new_verts = []
        new_norms = []
        new_uvs = []

        norms = np.asarray(high_mesh.normals, dtype=np.float32)
        uvs = np.asarray(high_mesh.uvs, dtype=np.float32)

        for old_idx in sorted(used_indices):
            old_to_new[old_idx] = len(new_verts)
            new_verts.append(verts[old_idx])
            new_norms.append(norms[old_idx] if old_idx < len(norms) else [0, 0, 1])
            new_uvs.append(uvs[old_idx] if old_idx < len(uvs) else [0, 0])

        lod_mesh = DFFMesh()
        lod_mesh.materials = list(high_mesh.materials)
        lod_mesh.vertices = new_verts
        lod_mesh.normals = new_norms
        lod_mesh.uvs = new_uvs

        lod_mesh.triangles = [
            (old_to_new[v0], old_to_new[v1], old_to_new[v2], mat_id)
            for v0, v1, v2, mat_id in reduced_tris
        ]

        return lod_mesh
