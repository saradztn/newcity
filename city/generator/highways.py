"""
highways.py - Elevated Highway Overpasses, Ramps, and Interchanges
Generates multi-lane elevated highway structures with concrete piers/bents,
Jersey crash barriers, exit/entrance ramps, and overhead directional gantries.
"""

import numpy as np
from .rw_dff import DFFMesh
from .collision import COLBuilder, COL_MAT_PAVEMENT, COL_MAT_CONCRETE, COL_MAT_METAL
from .lod import LODGenerator


class HighwayBuilder:
    @staticmethod
    def build_elevated_span(name, start_pos, end_pos, width=24.0, height_clearance=8.0, pier_spacing=30.0):
        """
        Builds an elevated highway span with concrete deck,
        Jersey barriers on edges, and cylindrical/rectangular support piers.
        """
        p0 = np.array(start_pos, dtype=np.float32)
        p1 = np.array(end_pos, dtype=np.float32)

        span_vec = p1 - p0
        span_len = float(np.linalg.norm(span_vec[:2]))
        num_segments = max(2, int(span_len / 10.0))

        mesh = DFFMesh()
        mat_road = mesh.add_material("highway_albedo")
        mat_conc = mesh.add_material("concrete_albedo")
        mat_metal = mesh.add_material("metal_industrial_albedo")

        col = COLBuilder(f"col_{name}")
        half_w = width * 0.5
        barrier_h = 1.1  # Standard Jersey barrier height (1.1m)
        barrier_w = 0.45
        deck_thick = 1.2

        verts = []
        norms = []
        uvs = []
        cols = []

        tangent = span_vec / max(span_len, 1e-4)
        side = np.array([-tangent[1], tangent[0], 0.0], dtype=np.float32)

        # Build deck slices
        ts = np.linspace(0.0, 1.0, num_segments + 1)
        for i, t in enumerate(ts):
            p = p0 + span_vec * t
            z_road = p[2]

            # Cross-section vertices:
            # 0: Left barrier outer bottom (Z = z_road - deck_thick)
            # 1: Left barrier top (Z = z_road + barrier_h)
            # 2: Left road edge (Z = z_road)
            # 3: Road center (Z = z_road + 0.04)
            # 4: Right road edge (Z = z_road)
            # 5: Right barrier top (Z = z_road + barrier_h)
            # 6: Right barrier outer bottom (Z = z_road - deck_thick)

            pt0 = p - side * (half_w + barrier_w) - np.array([0, 0, deck_thick])
            pt1 = p - side * (half_w + barrier_w * 0.5) + np.array([0, 0, barrier_h])
            pt2 = p - side * half_w
            pt3 = p + np.array([0, 0, 0.04])
            pt4 = p + side * half_w
            pt5 = p + side * (half_w + barrier_w * 0.5) + np.array([0, 0, barrier_h])
            pt6 = p + side * (half_w + barrier_w) - np.array([0, 0, deck_thick])

            verts.extend([pt0, pt1, pt2, pt3, pt4, pt5, pt6])
            norms.extend([[0, 0, 1]] * 7)
            u_v = float(t * span_len * 0.1)
            uvs.extend([
                [0.0, u_v], [0.5, u_v],
                [0.0, u_v], [0.5, u_v], [1.0, u_v],
                [0.5, u_v], [1.0, u_v]
            ])
            cols.extend([[255, 255, 255, 255]] * 7)

        triangles = []
        col_faces = []

        for i in range(num_segments):
            b0 = i * 7
            b1 = (i + 1) * 7

            # Left barrier outer wall
            triangles.append((b0 + 0, b1 + 0, b1 + 1, mat_conc))
            triangles.append((b0 + 0, b1 + 1, b0 + 1, mat_conc))
            col_faces.append((b0 + 0, b1 + 0, b1 + 1, COL_MAT_CONCRETE))
            col_faces.append((b0 + 0, b1 + 1, b0 + 1, COL_MAT_CONCRETE))

            # Left barrier inner wall
            triangles.append((b0 + 1, b1 + 1, b1 + 2, mat_conc))
            triangles.append((b0 + 1, b1 + 2, b0 + 2, mat_conc))
            col_faces.append((b0 + 1, b1 + 1, b1 + 2, COL_MAT_CONCRETE))
            col_faces.append((b0 + 1, b1 + 2, b0 + 2, COL_MAT_CONCRETE))

            # Road surface left
            triangles.append((b0 + 2, b1 + 2, b1 + 3, mat_road))
            triangles.append((b0 + 2, b1 + 3, b0 + 3, mat_road))
            col_faces.append((b0 + 2, b1 + 2, b1 + 3, COL_MAT_PAVEMENT))
            col_faces.append((b0 + 2, b1 + 3, b0 + 3, COL_MAT_PAVEMENT))

            # Road surface right
            triangles.append((b0 + 3, b1 + 3, b1 + 4, mat_road))
            triangles.append((b0 + 3, b1 + 4, b0 + 4, mat_road))
            col_faces.append((b0 + 3, b1 + 3, b1 + 4, COL_MAT_PAVEMENT))
            col_faces.append((b0 + 3, b1 + 4, b0 + 4, COL_MAT_PAVEMENT))

            # Right barrier inner wall
            triangles.append((b0 + 4, b1 + 4, b1 + 5, mat_conc))
            triangles.append((b0 + 4, b1 + 5, b0 + 5, mat_conc))
            col_faces.append((b0 + 4, b1 + 4, b1 + 5, COL_MAT_CONCRETE))
            col_faces.append((b0 + 4, b1 + 5, b0 + 5, COL_MAT_CONCRETE))

            # Right barrier outer wall
            triangles.append((b0 + 5, b1 + 5, b1 + 6, mat_conc))
            triangles.append((b0 + 5, b1 + 6, b0 + 6, mat_conc))
            col_faces.append((b0 + 5, b1 + 5, b1 + 6, COL_MAT_CONCRETE))
            col_faces.append((b0 + 5, b1 + 6, b0 + 6, COL_MAT_CONCRETE))

        # Add heavy concrete support piers
        num_piers = max(1, int(span_len / pier_spacing))
        pier_ts = np.linspace(0.15, 0.85, num_piers)
        for pt_t in pier_ts:
            pier_center = p0 + span_vec * pt_t
            pz_top = pier_center[2] - deck_thick
            pz_bottom = pz_top - height_clearance
            pr = 1.4  # Pier radius

            # 8-sided cylinder pier
            pier_b = len(verts)
            for a_i in range(8):
                ang = a_i * (2.0 * np.pi / 8.0)
                px = pier_center[0] + pr * np.cos(ang)
                py = pier_center[1] + pr * np.sin(ang)
                verts.append([px, py, pz_bottom])
                verts.append([px, py, pz_top])
                norms.append([float(np.cos(ang)), float(np.sin(ang)), 0.0])
                norms.append([float(np.cos(ang)), float(np.sin(ang)), 0.0])
                uvs.append([float(a_i / 8.0), 0.0])
                uvs.append([float(a_i / 8.0), 1.0])
                cols.extend([[255, 255, 255, 255], [255, 255, 255, 255]])

            for a_i in range(8):
                nxt = (a_i + 1) % 8
                v00 = pier_b + a_i * 2
                v01 = pier_b + a_i * 2 + 1
                v10 = pier_b + nxt * 2
                v11 = pier_b + nxt * 2 + 1
                triangles.append((v00, v10, v11, mat_conc))
                triangles.append((v00, v11, v01, mat_conc))
                col_faces.append((v00, v10, v11, COL_MAT_CONCRETE))
                col_faces.append((v00, v11, v01, COL_MAT_CONCRETE))

            # Pier collision box
            col.add_box(
                (pier_center[0] - pr, pier_center[1] - pr, pz_bottom),
                (pier_center[0] + pr, pier_center[1] + pr, pz_top),
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

    @staticmethod
    def build_ramp(name, start_ground, end_elevated, width=8.0, control_pt=None):
        """
        Builds a curving, climbing single/dual-lane highway ramp.
        Smoothly elevates from ground level to overpass level with concrete safety walls.
        """
        p0 = np.array(start_ground, dtype=np.float32)
        p2 = np.array(end_elevated, dtype=np.float32)

        if control_pt is None:
            p1 = p0 + (p2 - p0) * 0.5 + np.array([-20.0, 10.0, 0.0])
        else:
            p1 = np.array(control_pt, dtype=np.float32)

        num_pts = 16
        ts = np.linspace(0.0, 1.0, num_pts)
        pts = []
        for t in ts:
            # Quadratic Bézier: (1-t)^2 p0 + 2(1-t)t p1 + t^2 p2
            pt = (1.0 - t) ** 2 * p0 + 2.0 * (1.0 - t) * t * p1 + (t ** 2) * p2
            pts.append(pt)

        mesh = DFFMesh()
        mat_road = mesh.add_material("asphalt_albedo")
        mat_conc = mesh.add_material("concrete_albedo")
        col = COLBuilder(f"col_{name}")

        half_w = width * 0.5
        wall_h = 1.0
        wall_w = 0.35

        verts = []
        norms = []
        uvs = []
        cols = []

        for i, p in enumerate(pts):
            if i == 0:
                tangent = pts[1] - pts[0]
            elif i == num_pts - 1:
                tangent = pts[-1] - pts[-2]
            else:
                tangent = pts[i + 1] - pts[i - 1]

            t_len = np.linalg.norm(tangent[:2])
            side = np.array([-tangent[1], tangent[0], 0.0], dtype=np.float32) / max(t_len, 1e-4)

            # Left wall top, left road edge, center, right road edge, right wall top
            pt_lw = p - side * (half_w + wall_w) + np.array([0, 0, wall_h])
            pt_le = p - side * half_w
            pt_c  = p + np.array([0, 0, 0.03])
            pt_re = p + side * half_w
            pt_rw = p + side * (half_w + wall_w) + np.array([0, 0, wall_h])

            verts.extend([pt_lw, pt_le, pt_c, pt_re, pt_rw])
            norms.extend([[0, 0, 1]] * 5)
            u_v = float(i * 0.25)
            uvs.extend([[0.0, u_v], [0.2, u_v], [0.5, u_v], [0.8, u_v], [1.0, u_v]])
            cols.extend([[255, 255, 255, 255]] * 5)

        triangles = []
        col_faces = []

        for i in range(num_pts - 1):
            b0 = i * 5
            b1 = (i + 1) * 5

            # Left wall
            triangles.append((b0 + 0, b1 + 0, b1 + 1, mat_conc))
            triangles.append((b0 + 0, b1 + 1, b0 + 1, mat_conc))
            col_faces.append((b0 + 0, b1 + 0, b1 + 1, COL_MAT_CONCRETE))
            col_faces.append((b0 + 0, b1 + 1, b0 + 1, COL_MAT_CONCRETE))

            # Road surface
            triangles.append((b0 + 1, b1 + 1, b1 + 2, mat_road))
            triangles.append((b0 + 1, b1 + 2, b0 + 2, mat_road))
            triangles.append((b0 + 2, b1 + 2, b1 + 3, mat_road))
            triangles.append((b0 + 2, b1 + 3, b0 + 3, mat_road))
            col_faces.append((b0 + 1, b1 + 1, b1 + 2, COL_MAT_PAVEMENT))
            col_faces.append((b0 + 1, b1 + 2, b0 + 2, COL_MAT_PAVEMENT))
            col_faces.append((b0 + 2, b1 + 2, b1 + 3, COL_MAT_PAVEMENT))
            col_faces.append((b0 + 2, b1 + 3, b0 + 3, COL_MAT_PAVEMENT))

            # Right wall
            triangles.append((b0 + 3, b1 + 3, b1 + 4, mat_conc))
            triangles.append((b0 + 3, b1 + 4, b0 + 4, mat_conc))
            col_faces.append((b0 + 3, b1 + 3, b1 + 4, COL_MAT_CONCRETE))
            col_faces.append((b0 + 3, b1 + 4, b0 + 4, COL_MAT_CONCRETE))

        mesh.vertices = verts
        mesh.normals = norms
        mesh.uvs = uvs
        mesh.colors = cols
        mesh.triangles = triangles

        col.add_mesh(verts, col_faces, default_mat=COL_MAT_PAVEMENT)
        lod_mesh = LODGenerator.simplify_mesh(mesh, target_reduction=0.7)
        return mesh, col, lod_mesh
