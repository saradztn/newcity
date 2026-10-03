"""
terrain.py - Procedural American Coastal & Hill Terrain Generator
Generates realistic multi-elevation topography: coastal shoreline, gentle plains,
rolling residential hills, river valleys, and road-carved embankments.
Positioned accurately at custom world origin coordinates.
"""

import numpy as np
from .rw_dff import DFFMesh
from .collision import COLBuilder, COL_MAT_GRASS, COL_MAT_SAND, COL_MAT_STONE
from .lod import LODGenerator


class TerrainGenerator:
    def __init__(self, origin_x=-4076.838, origin_y=492.024, base_z=161.427, width=1200.0, length=1200.0):
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.base_z = base_z
        self.width = width
        self.length = length

    def sample_elevation(self, x, y):
        """
        Analytic elevation function relative to base_z:
        - Western edge (x - OX < -250): Coastal taper
        - Central area (-250 <= x - OX <= 250): Urban plain around base_z
        - Eastern area (x - OX > 250): Rolling hills rising above base_z
        """
        macro_x = x - self.origin_x
        macro_y = y - self.origin_y

        if macro_x < -250.0:
            t = np.clip((macro_x + 350.0) / 100.0, 0.0, 1.0)
            local_z = (t - 1.0) * 4.0
        elif macro_x < 250.0:
            local_z = 0.8 * np.sin(macro_x * 0.01) + 0.6 * np.cos(macro_y * 0.015)
        else:
            hill_t = (macro_x - 250.0) / 350.0
            local_z = hill_t * 22.0 + 3.0 * np.sin(macro_x * 0.02) * np.cos(macro_y * 0.02)

        return float(self.base_z + local_z)

    def sample_normal(self, x, y, eps=1.0):
        z_r = self.sample_elevation(x + eps, y)
        z_l = self.sample_elevation(x - eps, y)
        z_u = self.sample_elevation(x, y + eps)
        z_d = self.sample_elevation(x, y - eps)

        dx = (z_r - z_l) / (2.0 * eps)
        dy = (z_u - z_d) / (2.0 * eps)

        norm = np.array([-dx, -dy, 1.0], dtype=np.float32)
        norm /= np.linalg.norm(norm)
        return norm

    def generate_chunk_mesh(self, min_x, min_y, max_x, max_y, grid_res=12):
        xs = np.linspace(min_x, max_x, grid_res)
        ys = np.linspace(min_y, max_y, grid_res)

        mesh = DFFMesh()
        mat_grass = mesh.add_material("grass_albedo")
        mat_sand = mesh.add_material("sand_albedo")
        mat_stone = mesh.add_material("concrete_albedo")

        col = COLBuilder(f"terrain_{int(min_x)}_{int(min_y)}")

        verts = []
        norms = []
        uvs = []
        cols = []

        for j, y in enumerate(ys):
            for i, x in enumerate(xs):
                z = self.sample_elevation(x, y)
                n = self.sample_normal(x, y)
                verts.append([x, y, z])
                norms.append([float(n[0]), float(n[1]), float(n[2])])
                uvs.append([x / 20.0, y / 20.0])
                ao = int(np.clip(200 + n[2] * 55, 120, 255))
                cols.append([ao, ao, ao, 255])

        mesh.vertices = verts
        mesh.normals = norms
        mesh.uvs = uvs
        mesh.colors = cols

        triangles = []
        col_faces = []

        for j in range(grid_res - 1):
            for i in range(grid_res - 1):
                idx0 = j * grid_res + i
                idx1 = idx0 + 1
                idx2 = (j + 1) * grid_res + i
                idx3 = idx2 + 1

                z_avg = (verts[idx0][2] + verts[idx1][2] + verts[idx2][2]) / 3.0
                slope = 1.0 - norms[idx0][2]

                if z_avg < self.base_z - 2.0:
                    mat_id = mat_sand
                    col_mat = COL_MAT_SAND
                elif slope > 0.45:
                    mat_id = mat_stone
                    col_mat = COL_MAT_STONE
                else:
                    mat_id = mat_grass
                    col_mat = COL_MAT_GRASS

                triangles.append((idx0, idx1, idx2, mat_id))
                col_faces.append((idx0, idx1, idx2, col_mat))

                triangles.append((idx1, idx3, idx2, mat_id))
                col_faces.append((idx1, idx3, idx2, col_mat))

        mesh.triangles = triangles
        col.add_mesh(verts, col_faces, default_mat=COL_MAT_GRASS)
        lod_mesh = LODGenerator.simplify_mesh(mesh, target_reduction=0.75)

        return mesh, col, lod_mesh
