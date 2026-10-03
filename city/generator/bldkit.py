"""
bldkit.py - Architectural Building Kit for American Metropolises
Provides floor- and bay-aligned facade mapping, tiered setbacks, cornices,
rooftop mechanical clutter (HVAC chillers, water tanks, antenna beacons),
entrance canopies, and storefront podiums.
"""

import math
import numpy as np


class BuildingKit:
    @staticmethod
    def add_quad(mesh, p0, p1, p2, p3, uv0=(0, 0), uv1=(1, 0), uv2=(1, 1), uv3=(0, 1), mat_id=0, normal=None):
        """
        Adds a textured quad (2 triangles CCW) to mesh.
        p0, p1, p2, p3: (x, y, z)
        """
        if normal is None:
            v1 = np.array(p1) - np.array(p0)
            v2 = np.array(p3) - np.array(p0)
            n = np.cross(v1, v2)
            n_len = np.linalg.norm(n)
            norm = (n / n_len).tolist() if n_len > 0.001 else [0.0, 0.0, 1.0]
        else:
            norm = normal

        base_v = len(mesh.vertices)
        mesh.vertices.extend([p0, p1, p2, p3])
        mesh.normals.extend([norm, norm, norm, norm])
        mesh.uvs.extend([uv0, uv1, uv2, uv3])

        # Triangles CCW: (0, 1, 2) and (0, 2, 3)
        mesh.triangles.append((base_v + 0, base_v + 1, base_v + 2, mat_id))
        mesh.triangles.append((base_v + 0, base_v + 2, base_v + 3, mat_id))

    @staticmethod
    def add_aligned_wall(mesh, p_start, p_end, z_bottom, z_top, mat_id, bay_w=4.0, floor_h=3.5):
        """
        Creates a vertical wall with bay- and floor-aligned UV coordinates.
        Ensures windows and floor slabs are never sliced or distorted.
        """
        x0, y0 = p_start
        x1, y1 = p_end
        dx = x1 - x0
        dy = y1 - y0
        length = math.hypot(dx, dy)
        height = max(1.0, z_top - z_bottom)

        nb = max(1, int(round(length / bay_w)))
        nf = max(1, int(round(height / floor_h)))

        # Wall normal (perpendicular in XY plane, facing outward)
        nx = -dy / length if length > 0.001 else 0.0
        ny = dx / length if length > 0.001 else 0.0
        norm = [nx, ny, 0.0]

        p0 = (x0, y0, z_bottom)
        p1 = (x1, y1, z_bottom)
        p2 = (x1, y1, z_top)
        p3 = (x0, y0, z_top)

        uv0 = (0.0, float(nf))
        uv1 = (float(nb), float(nf))
        uv2 = (float(nb), 0.0)
        uv3 = (0.0, 0.0)

        BuildingKit.add_quad(mesh, p0, p1, p2, p3, uv0, uv1, uv2, uv3, mat_id, normal=norm)

    @staticmethod
    def add_box(mesh, min_pt, max_pt, mat_sides, mat_top, mat_bottom=None, bay_w=4.0, floor_h=3.5):
        """Creates a multi-face architectural box with bay-aligned sides and flat roof/floor."""
        x0, y0, z0 = min_pt
        x1, y1, z1 = max_pt

        # 4 Vertical walls
        BuildingKit.add_aligned_wall(mesh, (x0, y0), (x1, y0), z0, z1, mat_sides, bay_w, floor_h) # South
        BuildingKit.add_aligned_wall(mesh, (x1, y0), (x1, y1), z0, z1, mat_sides, bay_w, floor_h) # East
        BuildingKit.add_aligned_wall(mesh, (x1, y1), (x0, y1), z0, z1, mat_sides, bay_w, floor_h) # North
        BuildingKit.add_aligned_wall(mesh, (x0, y1), (x0, y0), z0, z1, mat_sides, bay_w, floor_h) # West

        # Top roof (horizontal)
        u_span = max(1.0, (x1 - x0) / 4.0)
        v_span = max(1.0, (y1 - y0) / 4.0)
        p_t0 = (x0, y0, z1)
        p_t1 = (x1, y0, z1)
        p_t2 = (x1, y1, z1)
        p_t3 = (x0, y1, z1)
        BuildingKit.add_quad(mesh, p_t0, p_t1, p_t2, p_t3, (0, 0), (u_span, 0), (u_span, v_span), (0, v_span), mat_top, normal=[0, 0, 1])

        # Bottom floor (if specified)
        if mat_bottom is not None:
            p_b0 = (x0, y1, z0)
            p_b1 = (x1, y1, z0)
            p_b2 = (x1, y0, z0)
            p_b3 = (x0, y0, z0)
            BuildingKit.add_quad(mesh, p_b0, p_b1, p_b2, p_b3, (0, 0), (u_span, 0), (u_span, v_span), (0, v_span), mat_bottom, normal=[0, 0, -1])

    @staticmethod
    def add_cornice(mesh, min_pt, max_pt, z_level, mat_conc, overhang=0.45, height=0.40):
        """Adds an architectural ledge/cornice band projecting outward."""
        x0, y0, _ = min_pt
        x1, y1, _ = max_pt
        ox0, oy0 = x0 - overhang, y0 - overhang
        ox1, oy1 = x1 + overhang, y1 + overhang
        z0, z1 = z_level, z_level + height
        BuildingKit.add_box(mesh, (ox0, oy0, z0), (ox1, oy1, z1), mat_conc, mat_conc, mat_conc, bay_w=overhang*4, floor_h=height)

    @staticmethod
    def add_parapet(mesh, min_pt, max_pt, z_roof, mat_wall, height=1.1, thickness=0.35):
        """Adds a protective safety parapet wall around the perimeter of a rooftop."""
        x0, y0, _ = min_pt
        x1, y1, _ = max_pt
        # South parapet
        BuildingKit.add_box(mesh, (x0, y0, z_roof), (x1, y0 + thickness, z_roof + height), mat_wall, mat_wall)
        # North parapet
        BuildingKit.add_box(mesh, (x0, y1 - thickness, z_roof), (x1, y1, z_roof + height), mat_wall, mat_wall)
        # West parapet
        BuildingKit.add_box(mesh, (x0, y0 + thickness, z_roof), (x0 + thickness, y1 - thickness, z_roof + height), mat_wall, mat_wall)
        # East parapet
        BuildingKit.add_box(mesh, (x1 - thickness, y0 + thickness, z_roof), (x1, y1 - thickness, z_roof + height), mat_wall, mat_wall)

    @staticmethod
    def add_roof_mechanicals(mesh, center_pt, z_roof, mat_metal, mat_conc, is_tall=False):
        """
        Adds authentic American rooftop clutter:
        Elevator penthouse, HVAC chillers, water tank, and communication mast.
        """
        cx, cy = center_pt

        # 1. Elevator Machine Penthouse
        BuildingKit.add_box(
            mesh,
            (cx - 3.5, cy - 3.0, z_roof),
            (cx + 3.5, cy + 3.0, z_roof + 4.2),
            mat_conc, mat_conc
        )

        # 2. HVAC Cooling Chillers
        BuildingKit.add_box(
            mesh,
            (cx - 7.5, cy - 2.0, z_roof),
            (cx - 4.5, cy + 2.0, z_roof + 1.8),
            mat_metal, mat_metal
        )
        BuildingKit.add_box(
            mesh,
            (cx + 4.5, cy - 2.0, z_roof),
            (cx + 7.5, cy + 2.0, z_roof + 1.8),
            mat_metal, mat_metal
        )

        # 3. Classic American Wooden/Steel Rooftop Water Tank
        BuildingKit.add_box(
            mesh,
            (cx - 2.0, cy + 5.0, z_roof),
            (cx + 2.0, cy + 9.0, z_roof + 1.5),
            mat_metal, mat_metal # steel support frame
        )
        BuildingKit.add_box(
            mesh,
            (cx - 1.8, cy + 5.2, z_roof + 1.5),
            (cx + 1.8, cy + 8.8, z_roof + 5.0),
            mat_conc, mat_metal # tank body
        )

        # 4. Spire / Aviation Warning Mast on Tall Towers
        if is_tall:
            mast_base = z_roof + 4.2
            BuildingKit.add_box(
                mesh,
                (cx - 0.35, cy - 0.35, mast_base),
                (cx + 0.35, cy + 0.35, mast_base + 14.0),
                mat_metal, mat_metal
            )
            # Aviation flashing beacon light cap
            BuildingKit.add_box(
                mesh,
                (cx - 0.2, cy - 0.2, mast_base + 14.0),
                (cx + 0.2, cy + 0.2, mast_base + 14.6),
                mat_metal, mat_metal
            )
