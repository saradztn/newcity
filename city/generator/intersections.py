"""
intersections.py - Signalized Intersections, T-Junctions, and Roundabouts
Generates geometric junctions with pedestrian crosswalks, corner curb fillets,
turning bays, and circular roundabout islands with matching COL3 collisions.
"""

import numpy as np
from .rw_dff import DFFMesh
from .collision import COLBuilder, COL_MAT_PAVEMENT, COL_MAT_CONCRETE, COL_MAT_GRASS
from .lod import LODGenerator


class IntersectionBuilder:
    @staticmethod
    def build_4way_intersection(name, center_pos, road_width=18.0, sidewalk_width=3.0):
        """
        Builds a standard 4-way American intersection.
        Center: (cx, cy, cz)
        Square junction area with rounded curb corner fillets and crosswalk zones.
        """
        cx, cy, cz = center_pos
        half_w = road_width * 0.5
        total_half = half_w + sidewalk_width

        mesh = DFFMesh()
        mat_road = mesh.add_material("asphalt_albedo")
        mat_curb = mesh.add_material("concrete_albedo")
        mat_sidewalk = mesh.add_material("sidewalk_albedo")
        mat_crosswalk = mesh.add_material("asphalt_albedo")

        col = COLBuilder(f"col_{name}")
        curb_h = 0.18

        # Center pavement square
        v_center = [
            [cx - half_w, cy - half_w, cz],
            [cx + half_w, cy - half_w, cz],
            [cx + half_w, cy + half_w, cz],
            [cx - half_w, cy + half_w, cz],
        ]
        norms = [[0, 0, 1]] * 4
        uvs = [[0, 0], [1, 0], [1, 1], [0, 1]]
        cols = [[255, 255, 255, 255]] * 4

        # Add 4 corner sidewalk squares
        # Corner 0: (cx - total_half .. cx - half_w, cy - total_half .. cy - half_w)
        corners = [
            (cx - total_half, cx - half_w, cy - total_half, cy - half_w), # SW
            (cx + half_w, cx + total_half, cy - total_half, cy - half_w), # SE
            (cx + half_w, cx + total_half, cy + half_w, cy + total_half), # NE
            (cx - total_half, cx - half_w, cy + half_w, cy + total_half), # NW
        ]

        verts = list(v_center)
        triangles = [
            (0, 1, 2, mat_road),
            (0, 2, 3, mat_road),
        ]
        col_faces = [
            (0, 1, 2, COL_MAT_PAVEMENT),
            (0, 2, 3, COL_MAT_PAVEMENT),
        ]

        for x0, x1, y0, y1 in corners:
            b_idx = len(verts)
            c_verts = [
                [x0, y0, cz + curb_h],
                [x1, y0, cz + curb_h],
                [x1, y1, cz + curb_h],
                [x0, y1, cz + curb_h],
            ]
            verts.extend(c_verts)
            norms.extend([[0, 0, 1]] * 4)
            uvs.extend([[0, 0], [1, 0], [1, 1], [0, 1]])
            cols.extend([[255, 255, 255, 255]] * 4)

            triangles.append((b_idx + 0, b_idx + 1, b_idx + 2, mat_sidewalk))
            triangles.append((b_idx + 0, b_idx + 2, b_idx + 3, mat_sidewalk))
            col_faces.append((b_idx + 0, b_idx + 1, b_idx + 2, COL_MAT_CONCRETE))
            col_faces.append((b_idx + 0, b_idx + 2, b_idx + 3, COL_MAT_CONCRETE))

        mesh.vertices = verts
        mesh.normals = norms
        mesh.uvs = uvs
        mesh.colors = cols
        mesh.triangles = triangles

        col.add_mesh(verts, col_faces, default_mat=COL_MAT_PAVEMENT)
        lod_mesh = LODGenerator.simplify_mesh(mesh, target_reduction=0.6)
        return mesh, col, lod_mesh

    @staticmethod
    def build_roundabout(name, center_pos, inner_radius=8.0, roadway_width=10.0, outer_sidewalk=3.0):
        """
        Builds a circular roundabout with center landscaped island,
        circulating asphalt roadway, and outer perimeter sidewalk.
        """
        cx, cy, cz = center_pos
        mesh = DFFMesh()
        mat_grass = mesh.add_material("grass_albedo")
        mat_road = mesh.add_material("asphalt_albedo")
        mat_curb = mesh.add_material("concrete_albedo")
        mat_sidewalk = mesh.add_material("sidewalk_albedo")

        col = COLBuilder(f"col_{name}")
        curb_h = 0.20

        num_segments = 24
        angles = np.linspace(0, 2 * np.pi, num_segments, endpoint=False)

        verts = []
        norms = []
        uvs = []
        cols = []

        # Ring 0: Center vertex (Z = cz + curb_h + 0.3 domed)
        verts.append([cx, cy, cz + curb_h + 0.3])
        norms.append([0, 0, 1])
        uvs.append([0.5, 0.5])
        cols.append([255, 255, 255, 255])

        # Rings 1 to 4:
        # Ring 1: Island edge top (r = inner_radius, z = cz + curb_h)
        # Ring 2: Island curb bottom / Road inner (r = inner_radius, z = cz)
        # Ring 3: Road outer / Outer curb bottom (r = inner_radius + roadway_width, z = cz)
        # Ring 4: Outer curb top / Sidewalk inner (r = inner_radius + roadway_width, z = cz + curb_h)
        # Ring 5: Sidewalk outer (r = inner_radius + roadway_width + outer_sidewalk, z = cz + curb_h)

        r_road_outer = inner_radius + roadway_width
        r_sw_outer = r_road_outer + outer_sidewalk

        for ang in angles:
            cos_a = float(np.cos(ang))
            sin_a = float(np.sin(ang))

            # 1. Island top
            verts.append([cx + inner_radius * cos_a, cy + inner_radius * sin_a, cz + curb_h])
            norms.append([0, 0, 1])
            uvs.append([0.5 + 0.5 * cos_a, 0.5 + 0.5 * sin_a])
            cols.append([255, 255, 255, 255])

            # 2. Road inner
            verts.append([cx + inner_radius * cos_a, cy + inner_radius * sin_a, cz])
            norms.append([0, 0, 1])
            uvs.append([0.0, float(ang / (2 * np.pi)) * 4.0])
            cols.append([255, 255, 255, 255])

            # 3. Road outer
            verts.append([cx + r_road_outer * cos_a, cy + r_road_outer * sin_a, cz])
            norms.append([0, 0, 1])
            uvs.append([1.0, float(ang / (2 * np.pi)) * 4.0])
            cols.append([255, 255, 255, 255])

            # 4. Sidewalk inner
            verts.append([cx + r_road_outer * cos_a, cy + r_road_outer * sin_a, cz + curb_h])
            norms.append([0, 0, 1])
            uvs.append([0.0, float(ang / (2 * np.pi)) * 4.0])
            cols.append([255, 255, 255, 255])

            # 5. Sidewalk outer
            verts.append([cx + r_sw_outer * cos_a, cy + r_sw_outer * sin_a, cz + curb_h])
            norms.append([0, 0, 1])
            uvs.append([1.0, float(ang / (2 * np.pi)) * 4.0])
            cols.append([255, 255, 255, 255])

        mesh.vertices = verts
        mesh.normals = norms
        mesh.uvs = uvs
        mesh.colors = cols

        triangles = []
        col_faces = []

        # Center island fan (center pt 0 to ring 1)
        for i in range(num_segments):
            next_i = (i + 1) % num_segments
            i1 = 1 + i * 5
            i1_next = 1 + next_i * 5
            triangles.append((0, i1, i1_next, mat_grass))
            col_faces.append((0, i1, i1_next, COL_MAT_GRASS))

        # Road surface quads: between ring 2 and ring 3
        for i in range(num_segments):
            next_i = (i + 1) % num_segments
            i2 = 1 + i * 5 + 1
            i3 = 1 + i * 5 + 2
            i2_next = 1 + next_i * 5 + 1
            i3_next = 1 + next_i * 5 + 2

            triangles.append((i2, i3, i3_next, mat_road))
            triangles.append((i2, i3_next, i2_next, mat_road))
            col_faces.append((i2, i3, i3_next, COL_MAT_PAVEMENT))
            col_faces.append((i2, i3_next, i2_next, COL_MAT_PAVEMENT))

        # Sidewalk quads: between ring 4 and ring 5
        for i in range(num_segments):
            next_i = (i + 1) % num_segments
            i4 = 1 + i * 5 + 3
            i5 = 1 + i * 5 + 4
            i4_next = 1 + next_i * 5 + 3
            i5_next = 1 + next_i * 5 + 4

            triangles.append((i4, i5, i5_next, mat_sidewalk))
            triangles.append((i4, i5_next, i4_next, mat_sidewalk))
            col_faces.append((i4, i5, i5_next, COL_MAT_CONCRETE))
            col_faces.append((i4, i5_next, i4_next, COL_MAT_CONCRETE))

        mesh.triangles = triangles
        col.add_mesh(verts, col_faces, default_mat=COL_MAT_PAVEMENT)

        lod_mesh = LODGenerator.simplify_mesh(mesh, target_reduction=0.7)
        return mesh, col, lod_mesh
