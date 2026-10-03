"""
roads.py - Comprehensive Road Network Graph & Procedural Road Geometry Engine
Defines Road Nodes, Edges, Spline Curves, Elevations, Lanes, and Cross-Sections.
Generates multi-lane highways, boulevards with medians, downtown streets,
residential streets, coastal curves, ramps, curbs, gutters, and sidewalks.
"""

import numpy as np
from .rw_dff import DFFMesh
from .collision import COLBuilder, COL_MAT_PAVEMENT, COL_MAT_CONCRETE
from .lod import LODGenerator


class RoadNode:
    def __init__(self, node_id, position, node_type="intersection"):
        self.id = node_id
        self.position = np.array(position, dtype=np.float32)  # (x, y, z)
        self.node_type = node_type  # 'intersection', 't_junction', 'roundabout', 'dead_end', 'ramp'
        self.connected_edges = []


class RoadSegment:
    def __init__(self, segment_id, start_node, end_node, road_class="arterial_downtown",
                 lanes=4, width=16.0, speed_class=35, is_one_way=False,
                 has_sidewalk=True, sidewalk_width=2.5, has_median=False,
                 median_width=2.0, control_points=None):
        self.id = segment_id
        self.start_node = start_node
        self.end_node = end_node
        self.road_class = road_class  # 'highway', 'boulevard', 'arterial_downtown', 'residential', 'coastal', 'ramp'
        self.lanes = lanes
        self.width = width
        self.speed_class = speed_class
        self.is_one_way = is_one_way
        self.has_sidewalk = has_sidewalk
        self.sidewalk_width = sidewalk_width
        self.has_median = has_median
        self.median_width = median_width
        self.control_points = control_points or []

    def get_spline_points(self, num_samples=20):
        """Generates smoothly interpolated 3D spline centerline points."""
        p0 = self.start_node.position
        p3 = self.end_node.position

        if len(self.control_points) >= 2:
            p1 = np.array(self.control_points[0], dtype=np.float32)
            p2 = np.array(self.control_points[1], dtype=np.float32)
        elif len(self.control_points) == 1:
            p1 = np.array(self.control_points[0], dtype=np.float32)
            p2 = (p1 + p3) * 0.5
        else:
            # Straight road
            p1 = p0 + (p3 - p0) * 0.333
            p2 = p0 + (p3 - p0) * 0.666

        ts = np.linspace(0.0, 1.0, num_samples)
        points = []
        for t in ts:
            # Cubic Bézier curve: B(t) = (1-t)^3 p0 + 3(1-t)^2 t p1 + 3(1-t) t^2 p2 + t^3 p3
            pt = ((1.0 - t) ** 3 * p0 +
                  3.0 * (1.0 - t) ** 2 * t * p1 +
                  3.0 * (1.0 - t) * (t ** 2) * p2 +
                  (t ** 3) * p3)
            points.append(pt)
        return points


class RoadNetworkGraph:
    def __init__(self):
        self.nodes = {}
        self.segments = {}

    def add_node(self, node_id, position, node_type="intersection"):
        node = RoadNode(node_id, position, node_type)
        self.nodes[node_id] = node
        return node

    def add_segment(self, segment_id, start_id, end_id, road_class="arterial_downtown",
                    lanes=4, width=16.0, speed_class=35, is_one_way=False,
                    has_sidewalk=True, sidewalk_width=2.5, has_median=False,
                    median_width=2.0, control_points=None):
        start_node = self.nodes[start_id]
        end_node = self.nodes[end_id]
        seg = RoadSegment(
            segment_id, start_node, end_node, road_class, lanes, width,
            speed_class, is_one_way, has_sidewalk, sidewalk_width,
            has_median, median_width, control_points
        )
        self.segments[segment_id] = seg
        start_node.connected_edges.append(seg)
        end_node.connected_edges.append(seg)
        return seg


class RoadGeometryBuilder:
    @staticmethod
    def build_segment_geometry(segment, sample_res=16):
        """
        Constructs high-detail RenderWare mesh and collision for a road segment.
        Includes road surface, curbs, gutters, and sidewalks.
        """
        centerline = segment.get_spline_points(sample_res)
        num_pts = len(centerline)

        mesh = DFFMesh()
        is_highway = (segment.road_class == "highway" or segment.lanes >= 6)
        tex_road = "highway_albedo" if is_highway else "asphalt_albedo"
        mat_road = mesh.add_material(tex_road)
        mat_curb = mesh.add_material("concrete_albedo")
        mat_sidewalk = mesh.add_material("sidewalk_albedo")

        col = COLBuilder(f"col_{segment.id}")

        half_w = segment.width * 0.5
        sw_w = segment.sidewalk_width if segment.has_sidewalk else 0.0
        curb_h = 0.18  # Curb height in meters (standard American curb)

        verts = []
        norms = []
        uvs = []
        cols = []

        # 8 cross-section points per slice along road:
        # 0: Left Sidewalk Outer (Z = base_z + curb_h)
        # 1: Left Sidewalk Inner / Top Curb (Z = base_z + curb_h)
        # 2: Left Curb Gutter / Road Edge (Z = base_z)
        # 3: Road Centerline Crown (Z = base_z + 0.05)
        # 4: Right Curb Gutter / Road Edge (Z = base_z)
        # 5: Right Sidewalk Inner / Top Curb (Z = base_z + curb_h)
        # 6: Right Sidewalk Outer (Z = base_z + curb_h)

        accum_dist = 0.0
        slice_offsets = [0.0]

        for i in range(1, num_pts):
            d = np.linalg.norm(centerline[i] - centerline[i - 1])
            accum_dist += d
            slice_offsets.append(accum_dist)

        for i in range(num_pts):
            p = centerline[i]
            # Tangent vector
            if i == 0:
                tangent = centerline[1] - centerline[0]
            elif i == num_pts - 1:
                tangent = centerline[-1] - centerline[-2]
            else:
                tangent = centerline[i + 1] - centerline[i - 1]

            t_len = np.linalg.norm(tangent[:2])
            if t_len > 1e-4:
                # Perpendicular normal in 2D (horizontal plane)
                side = np.array([-tangent[1], tangent[0], 0.0], dtype=np.float32) / t_len
            else:
                side = np.array([1.0, 0.0, 0.0], dtype=np.float32)

            v_dist = slice_offsets[i]

            # Cross-section points:
            # 0: Left sidewalk outer
            pt0 = p - side * (half_w + sw_w) + np.array([0, 0, curb_h])
            # 1: Left sidewalk curb top
            pt1 = p - side * half_w + np.array([0, 0, curb_h])
            # 2: Left road edge
            pt2 = p - side * half_w
            # 3: Road center (slight crown)
            pt3 = p + np.array([0, 0, 0.04])
            # 4: Right road edge
            pt4 = p + side * half_w
            # 5: Right sidewalk curb top
            pt5 = p + side * half_w + np.array([0, 0, curb_h])
            # 6: Right sidewalk outer
            pt6 = p + side * (half_w + sw_w) + np.array([0, 0, curb_h])

            verts.extend([pt0, pt1, pt2, pt3, pt4, pt5, pt6])

            # Normals:
            n_up = [0.0, 0.0, 1.0]
            n_left_curb = [float(-side[0]), float(-side[1]), 0.0]
            n_right_curb = [float(side[0]), float(side[1]), 0.0]
            norms.extend([n_up, n_up, n_up, n_up, n_up, n_up, n_up])

            # UV coordinates
            u_v = v_dist * 0.1
            uvs.extend([
                [0.0, u_v], [1.0, u_v],     # Sidewalk left
                [0.0, u_v], [0.5, u_v], [1.0, u_v], # Road surface
                [0.0, u_v], [1.0, u_v]      # Sidewalk right
            ])

            cols.extend([[255, 255, 255, 255]] * 7)

        mesh.vertices = verts
        mesh.normals = norms
        mesh.uvs = uvs
        mesh.colors = cols

        tris = []
        col_faces = []

        for i in range(num_pts - 1):
            b0 = i * 7
            b1 = (i + 1) * 7

            # Left sidewalk top: (pt0, pt1)
            tris.append((b0 + 0, b1 + 0, b1 + 1, mat_sidewalk))
            tris.append((b0 + 0, b1 + 1, b0 + 1, mat_sidewalk))
            col_faces.append((b0 + 0, b1 + 0, b1 + 1, COL_MAT_CONCRETE))
            col_faces.append((b0 + 0, b1 + 1, b0 + 1, COL_MAT_CONCRETE))

            # Left curb face: (pt1, pt2)
            tris.append((b0 + 1, b1 + 1, b1 + 2, mat_curb))
            tris.append((b0 + 1, b1 + 2, b0 + 2, mat_curb))
            col_faces.append((b0 + 1, b1 + 1, b1 + 2, COL_MAT_CONCRETE))
            col_faces.append((b0 + 1, b1 + 2, b0 + 2, COL_MAT_CONCRETE))

            # Road left half: (pt2, pt3)
            tris.append((b0 + 2, b1 + 2, b1 + 3, mat_road))
            tris.append((b0 + 2, b1 + 3, b0 + 3, mat_road))
            col_faces.append((b0 + 2, b1 + 2, b1 + 3, COL_MAT_PAVEMENT))
            col_faces.append((b0 + 2, b1 + 3, b0 + 3, COL_MAT_PAVEMENT))

            # Road right half: (pt3, pt4)
            tris.append((b0 + 3, b1 + 3, b1 + 4, mat_road))
            tris.append((b0 + 3, b1 + 4, b0 + 4, mat_road))
            col_faces.append((b0 + 3, b1 + 3, b1 + 4, COL_MAT_PAVEMENT))
            col_faces.append((b0 + 3, b1 + 4, b0 + 4, COL_MAT_PAVEMENT))

            # Right curb face: (pt4, pt5)
            tris.append((b0 + 4, b1 + 4, b1 + 5, mat_curb))
            tris.append((b0 + 4, b1 + 5, b0 + 5, mat_curb))
            col_faces.append((b0 + 4, b1 + 4, b1 + 5, COL_MAT_CONCRETE))
            col_faces.append((b0 + 4, b1 + 5, b0 + 5, COL_MAT_CONCRETE))

            # Right sidewalk top: (pt5, pt6)
            tris.append((b0 + 5, b1 + 5, b1 + 6, mat_sidewalk))
            tris.append((b0 + 5, b1 + 6, b0 + 6, mat_sidewalk))
            col_faces.append((b0 + 5, b1 + 5, b1 + 6, COL_MAT_CONCRETE))
            col_faces.append((b0 + 5, b1 + 6, b0 + 6, COL_MAT_CONCRETE))

        mesh.triangles = tris
        col.add_mesh(verts, col_faces, default_mat=COL_MAT_PAVEMENT)

        # Generate LOD
        lod_mesh = LODGenerator.simplify_mesh(mesh, target_reduction=0.70)
        return mesh, col, lod_mesh
