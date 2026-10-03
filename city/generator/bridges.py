"""
bridges.py - Bridge Generator (Viaducts, Girder Spans, and Suspension Pylons)
Generates high-detail bridge deck models with expansion joints, pedestrian walkways,
structural steel trusses / concrete bents, water piers, and matching COL3 collisions.
"""

import numpy as np
from .rw_dff import DFFMesh
from .collision import COLBuilder, COL_MAT_PAVEMENT, COL_MAT_CONCRETE, COL_MAT_METAL
from .lod import LODGenerator


class BridgeBuilder:
    @staticmethod
    def build_viaduct_bridge(name, start_pos, end_pos, width=22.0, pier_depth=12.0):
        """
        Builds a multi-span road viaduct with concrete girders, safety railings,
        and deep piers rooted into water or valley terrain.
        """
        p0 = np.array(start_pos, dtype=np.float32)
        p1 = np.array(end_pos, dtype=np.float32)

        span_vec = p1 - p0
        span_len = float(np.linalg.norm(span_vec[:2]))
        num_segments = max(4, int(span_len / 8.0))

        mesh = DFFMesh()
        mat_road = mesh.add_material("asphalt_albedo")
        mat_conc = mesh.add_material("concrete_albedo")
        mat_metal = mesh.add_material("metal_industrial_albedo")
        col = COLBuilder(f"col_{name}")

        half_w = width * 0.5
        railing_h = 1.2
        deck_thick = 1.5

        tangent = span_vec / max(span_len, 1e-4)
        side = np.array([-tangent[1], tangent[0], 0.0], dtype=np.float32)

        verts = []
        norms = []
        uvs = []
        cols = []

        ts = np.linspace(0.0, 1.0, num_segments + 1)
        for i, t in enumerate(ts):
            p = p0 + span_vec * t
            z = p[2]

            # Cross-section:
            # 0: Left railing top (z + railing_h)
            # 1: Left walkway outer (z)
            # 2: Left road edge (z)
            # 3: Road center (z + 0.04)
            # 4: Right road edge (z)
            # 5: Right walkway outer (z)
            # 6: Right railing top (z + railing_h)
            # 7: Left girder bottom (z - deck_thick)
            # 8: Right girder bottom (z - deck_thick)

            pt0 = p - side * half_w + np.array([0, 0, railing_h])
            pt1 = p - side * half_w
            pt2 = p - side * (half_w - 2.5)
            pt3 = p + np.array([0, 0, 0.04])
            pt4 = p + side * (half_w - 2.5)
            pt5 = p + side * half_w
            pt6 = p + side * half_w + np.array([0, 0, railing_h])
            pt7 = p - side * (half_w * 0.7) - np.array([0, 0, deck_thick])
            pt8 = p + side * (half_w * 0.7) - np.array([0, 0, deck_thick])

            verts.extend([pt0, pt1, pt2, pt3, pt4, pt5, pt6, pt7, pt8])
            norms.extend([[0, 0, 1]] * 9)
            u_v = float(t * span_len * 0.1)
            uvs.extend([
                [0.0, u_v], [0.1, u_v], [0.25, u_v], [0.5, u_v],
                [0.75, u_v], [0.9, u_v], [1.0, u_v], [0.3, u_v], [0.7, u_v]
            ])
            cols.extend([[255, 255, 255, 255]] * 9)

        triangles = []
        col_faces = []

        for i in range(num_segments):
            b0 = i * 9
            b1 = (i + 1) * 9

            # Left walkway & railing
            triangles.append((b0 + 0, b1 + 0, b1 + 1, mat_metal))
            triangles.append((b0 + 0, b1 + 1, b0 + 1, mat_metal))
            col_faces.append((b0 + 0, b1 + 0, b1 + 1, COL_MAT_METAL))
            col_faces.append((b0 + 0, b1 + 1, b0 + 1, COL_MAT_METAL))

            triangles.append((b0 + 1, b1 + 1, b1 + 2, mat_conc))
            triangles.append((b0 + 1, b1 + 2, b0 + 2, mat_conc))
            col_faces.append((b0 + 1, b1 + 1, b1 + 2, COL_MAT_CONCRETE))
            col_faces.append((b0 + 1, b1 + 2, b0 + 2, COL_MAT_CONCRETE))

            # Road surface
            triangles.append((b0 + 2, b1 + 2, b1 + 3, mat_road))
            triangles.append((b0 + 2, b1 + 3, b0 + 3, mat_road))
            triangles.append((b0 + 3, b1 + 3, b1 + 4, mat_road))
            triangles.append((b0 + 3, b1 + 4, b0 + 4, mat_road))
            col_faces.append((b0 + 2, b1 + 2, b1 + 3, COL_MAT_PAVEMENT))
            col_faces.append((b0 + 2, b1 + 3, b0 + 3, COL_MAT_PAVEMENT))
            col_faces.append((b0 + 3, b1 + 3, b1 + 4, COL_MAT_PAVEMENT))
            col_faces.append((b0 + 3, b1 + 4, b0 + 4, COL_MAT_PAVEMENT))

            # Right walkway & railing
            triangles.append((b0 + 4, b1 + 4, b1 + 5, mat_conc))
            triangles.append((b0 + 4, b1 + 5, b0 + 5, mat_conc))
            col_faces.append((b0 + 4, b1 + 4, b1 + 5, COL_MAT_CONCRETE))
            col_faces.append((b0 + 4, b1 + 5, b0 + 5, COL_MAT_CONCRETE))

            triangles.append((b0 + 5, b1 + 5, b1 + 6, mat_metal))
            triangles.append((b0 + 5, b1 + 6, b0 + 6, mat_metal))
            col_faces.append((b0 + 5, b1 + 5, b1 + 6, COL_MAT_METAL))
            col_faces.append((b0 + 5, b1 + 6, b0 + 6, COL_MAT_METAL))

        # Build piers along the viaduct
        num_piers = max(1, int(span_len / 35.0))
        for pt_t in np.linspace(0.2, 0.8, num_piers):
            p_pos = p0 + span_vec * pt_t
            pz_top = p_pos[2] - deck_thick
            pz_bot = pz_top - pier_depth
            pr = 1.6

            # Pier cylinder
            pier_base = len(verts)
            for a_i in range(8):
                ang = a_i * (2.0 * np.pi / 8.0)
                px = p_pos[0] + pr * np.cos(ang)
                py = p_pos[1] + pr * np.sin(ang)
                verts.append([px, py, pz_bot])
                verts.append([px, py, pz_top])
                norms.append([float(np.cos(ang)), float(np.sin(ang)), 0.0])
                norms.append([float(np.cos(ang)), float(np.sin(ang)), 0.0])
                uvs.extend([[float(a_i / 8.0), 0.0], [float(a_i / 8.0), 1.0]])
                cols.extend([[255, 255, 255, 255], [255, 255, 255, 255]])

            for a_i in range(8):
                nxt = (a_i + 1) % 8
                v00 = pier_base + a_i * 2
                v01 = pier_base + a_i * 2 + 1
                v10 = pier_base + nxt * 2
                v11 = pier_base + nxt * 2 + 1
                triangles.append((v00, v10, v11, mat_conc))
                triangles.append((v00, v11, v01, mat_conc))
                col_faces.append((v00, v10, v11, COL_MAT_CONCRETE))
                col_faces.append((v00, v11, v01, COL_MAT_CONCRETE))

            col.add_box(
                (p_pos[0] - pr, p_pos[1] - pr, pz_bot),
                (p_pos[0] + pr, p_pos[1] + pr, pz_top),
                COL_MAT_CONCRETE
            )

        mesh.vertices = verts
        mesh.normals = norms
        mesh.uvs = uvs
        mesh.colors = cols
        mesh.triangles = triangles

        col.add_mesh(verts, col_faces, default_mat=COL_MAT_PAVEMENT)
        lod_mesh = LODGenerator.simplify_mesh(mesh, target_reduction=0.7)
        return mesh, col, lod_mesh
