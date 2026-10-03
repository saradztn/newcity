"""
terrain.py - Procedural American Coastal & Hill Terrain Generator
Generates realistic multi-elevation topography: coastal shoreline, gentle plains,
rolling residential hills, river valleys, and road-carved embankments.
Exports high-detail DFF models and exact COL3 collision files.
"""

import numpy as np
from .rw_dff import DFFMesh
from .collision import COLBuilder, COL_MAT_GRASS, COL_MAT_SAND, COL_MAT_STONE
from .lod import LODGenerator


class TerrainGenerator:
    def __init__(self, origin_x=0.0, origin_y=0.0, width=1200.0, length=1200.0):
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.width = width
        self.length = length

    def sample_elevation(self, x, y):
        """
        Analytic elevation function:
        - Western edge (x < -200): Coastal beach transitioning to ocean (Z -> 0)
        - Central area (-200 <= x <= 300): Flat urban plain (Z ~ 4 - 6m)
        - Eastern area (x > 300): Rolling hills rising to Z ~ 35m
        - River cutting through Y ~ -100 to 0
        """
        # Global macro slope rising to the east
        macro_x = (x - self.origin_x)
        macro_y = (y - self.origin_y)

        # Base elevation: low at coast (west), rises in eastern foothills
        if macro_x < -250.0:
            # Beach / shoreline taper down to sea level
            t = np.clip((macro_x + 350.0) / 100.0, 0.0, 1.0)
            base_z = t * 3.5
        elif macro_x < 250.0:
            # Urban plain: gently undulating 3.5m to 7.0m
            base_z = 4.0 + 1.5 * np.sin(macro_x * 0.01) + 1.0 * np.cos(macro_y * 0.015)
        else:
            # Hills: rising up to 35m
            hill_t = (macro_x - 250.0) / 350.0
            base_z = 7.0 + hill_t * 28.0 + 4.0 * np.sin(macro_x * 0.02) * np.cos(macro_y * 0.02)

        # River valley depression
        river_dist = np.abs(macro_y - (50.0 * np.sin(macro_x * 0.008)))
        if river_dist < 60.0 and macro_x < 150.0:
            river_depth = (1.0 - (river_dist / 60.0) ** 2) * 4.5
            base_z = max(0.5, base_z - river_depth)

        return float(base_z)

    def sample_normal(self, x, y, eps=1.0):
        """Computes surface normal via central finite differences."""
        z_r = self.sample_elevation(x + eps, y)
        z_l = self.sample_elevation(x - eps, y)
        z_u = self.sample_elevation(x, y + eps)
        z_d = self.sample_elevation(x, y - eps)

        dx = (z_r - z_l) / (2.0 * eps)
        dy = (z_u - z_d) / (2.0 * eps)

        norm = np.array([-dx, -dy, 1.0], dtype=np.float32)
        norm /= np.linalg.norm(norm)
        return norm

    def generate_chunk_mesh(self, min_x, min_y, max_x, max_y, grid_res=16):
        """
        Creates a high-detail terrain chunk DFFMesh and matching COLBuilder.
        """
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

                # UV coordinates (tiled every 20 meters)
                uvs.append([x / 20.0, y / 20.0])

                # Vertex colors: darker in crevices, brighter on ridges
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

                # Select material based on elevation and slope
                z_avg = (verts[idx0][2] + verts[idx1][2] + verts[idx2][2]) / 3.0
                slope = 1.0 - norms[idx0][2]

                if z_avg < 2.0:
                    mat_id = mat_sand
                    col_mat = COL_MAT_SAND
                elif slope > 0.45:
                    mat_id = mat_stone
                    col_mat = COL_MAT_STONE
                else:
                    mat_id = mat_grass
                    col_mat = COL_MAT_GRASS

                # Triangle 1: (idx0, idx1, idx2)
                triangles.append((idx0, idx1, idx2, mat_id))
                col_faces.append((idx0, idx1, idx2, col_mat))

                # Triangle 2: (idx1, idx3, idx2)
                triangles.append((idx1, idx3, idx2, mat_id))
                col_faces.append((idx1, idx3, idx2, col_mat))

        mesh.triangles = triangles

        # Build collision mesh
        col.add_mesh(verts, col_faces, default_mat=COL_MAT_GRASS)

        # Build LOD
        lod_mesh = LODGenerator.simplify_mesh(mesh, target_reduction=0.75)

        return mesh, col, lod_mesh
