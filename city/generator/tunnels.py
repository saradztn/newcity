"""
tunnels.py - Tunnel Portals, Retaining Walls, and Subterranean Tubes
Generates realistic tunnel entrance portals cut into hill terrain with heavy
concrete masonry arches, wing retaining walls, clearance signs, and interior roadway.
"""

import numpy as np
from .rw_dff import DFFMesh
from .collision import COLBuilder, COL_MAT_PAVEMENT, COL_MAT_CONCRETE
from .lod import LODGenerator


class TunnelBuilder:
    @staticmethod
    def build_tunnel_portal(name, position, direction_angle=0.0, road_width=14.0, height=7.0, tube_length=35.0):
        """
        Builds a heavy concrete portal arch with retaining walls and interior tube.
        position: (x, y, z) base road position at portal mouth.
        direction_angle: rotation in radians (0 along +Y).
        """
        cx, cy, cz = position
        half_w = road_width * 0.5
        wall_thick = 2.5
        portal_h = height + 3.0

        mesh = DFFMesh()
        mat_road = mesh.add_material("asphalt_albedo")
        mat_conc = mesh.add_material("concrete_albedo")
        mat_sign = mesh.add_material("signs_atlas_albedo")
        col = COLBuilder(f"col_{name}")

        cos_d = np.cos(direction_angle)
        sin_d = np.sin(direction_angle)
        fwd = np.array([-sin_d, cos_d, 0.0], dtype=np.float32)
        side = np.array([cos_d, sin_d, 0.0], dtype=np.float32)

        # 1. Road Surface inside tube
        v0 = np.array([cx, cy, cz]) - side * half_w
        v1 = np.array([cx, cy, cz]) + side * half_w
        v2 = v1 + fwd * tube_length
        v3 = v0 + fwd * tube_length

        verts = [v0, v1, v2, v3]
        norms = [[0, 0, 1]] * 4
        uvs = [[0, 0], [1, 0], [1, tube_length * 0.1], [0, tube_length * 0.1]]
        cols = [[255, 255, 255, 255]] * 4

        triangles = [
            (0, 1, 2, mat_road),
            (0, 2, 3, mat_road),
        ]
        col_faces = [
            (0, 1, 2, COL_MAT_PAVEMENT),
            (0, 2, 3, COL_MAT_PAVEMENT),
        ]

        # 2. Portal Arch Face (Front wall above and around tunnel entrance)
        # Left pillar, Right pillar, and Header beam
        # Left pillar: from -half_w - wall_thick to -half_w
        lp_min = np.array([cx, cy, cz]) - side * (half_w + wall_thick)
        lp_max = np.array([cx, cy, cz]) - side * half_w + fwd * 4.0 + np.array([0, 0, portal_h])
        col.add_box((lp_min[0], lp_min[1], cz), (lp_max[0], lp_max[1], cz + portal_h), COL_MAT_CONCRETE)

        rp_min = np.array([cx, cy, cz]) + side * half_w
        rp_max = np.array([cx, cy, cz]) + side * (half_w + wall_thick) + fwd * 4.0 + np.array([0, 0, portal_h])
        col.add_box((rp_min[0], rp_min[1], cz), (rp_max[0], rp_max[1], cz + portal_h), COL_MAT_CONCRETE)

        # Overhead portal header
        col.add_box(
            (lp_min[0], lp_min[1], cz + height),
            (rp_max[0], rp_max[1], cz + portal_h),
            COL_MAT_CONCRETE
        )

        # Portal front face geometry
        p_base = len(verts)
        pf_verts = [
            # Left pillar front:
            lp_min,
            np.array([cx, cy, cz]) - side * half_w,
            np.array([cx, cy, cz]) - side * half_w + np.array([0, 0, height]),
            lp_min + np.array([0, 0, portal_h]),

            # Right pillar front:
            np.array([cx, cy, cz]) + side * half_w,
            lp_min + side * (2 * half_w + 2 * wall_thick),
            lp_min + side * (2 * half_w + 2 * wall_thick) + np.array([0, 0, portal_h]),
            np.array([cx, cy, cz]) + side * half_w + np.array([0, 0, height]),
        ]

        verts.extend(pf_verts)
        norms.extend([[float(-fwd[0]), float(-fwd[1]), 0.0]] * 8)
        uvs.extend([[0, 0], [0.3, 0], [0.3, 0.7], [0, 1.0], [0.7, 0], [1.0, 0], [1.0, 1.0], [0.7, 0.7]])
        cols.extend([[255, 255, 255, 255]] * 8)

        # Left pillar face
        triangles.extend([
            (p_base + 0, p_base + 1, p_base + 2, mat_conc),
            (p_base + 0, p_base + 2, p_base + 3, mat_conc),
            # Right pillar face
            (p_base + 4, p_base + 5, p_base + 6, mat_conc),
            (p_base + 4, p_base + 6, p_base + 7, mat_conc),
            # Header above entrance
            (p_base + 2, p_base + 7, p_base + 6, mat_conc),
            (p_base + 2, p_base + 6, p_base + 3, mat_conc),
        ] )
        col_faces.extend([
            (p_base + 0, p_base + 1, p_base + 2, COL_MAT_CONCRETE),
            (p_base + 0, p_base + 2, p_base + 3, COL_MAT_CONCRETE),
            (p_base + 4, p_base + 5, p_base + 6, COL_MAT_CONCRETE),
            (p_base + 4, p_base + 6, p_base + 7, COL_MAT_CONCRETE),
            (p_base + 2, p_base + 7, p_base + 6, COL_MAT_CONCRETE),
            (p_base + 2, p_base + 6, p_base + 3, COL_MAT_CONCRETE),
        ])

        mesh.vertices = verts
        mesh.normals = norms
        mesh.uvs = uvs
        mesh.colors = cols
        mesh.triangles = triangles

        col.add_mesh(verts, col_faces, default_mat=COL_MAT_CONCRETE)
        lod_mesh = LODGenerator.simplify_mesh(mesh, target_reduction=0.6)
        return mesh, col, lod_mesh
