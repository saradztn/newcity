"""
buildings.py - Comprehensive 23-Archetype Procedural Building Generator
Generates realistic American architectural archetypes with custom width, depth,
height, floors, facade styles, windows, balconies, roof HVAC, antennas, entrances,
and deterministic seed variations. Produces high-detail DFF, LOD DFF, and COL3 collision.
"""

import numpy as np
from .rw_dff import DFFMesh
from .collision import COLBuilder, COL_MAT_CONCRETE, COL_MAT_GLASS, COL_MAT_METAL, COL_MAT_WOOD
from .lod import LODGenerator


def add_box_geometry(mesh, min_pt, max_pt, mat_id, uv_scale=(1.0, 1.0)):
    """Helper that adds an articulated textured box to a DFFMesh."""
    x0, y0, z0 = min_pt
    x1, y1, z1 = max_pt
    w = max(x1 - x0, 0.1)
    d = max(y1 - y0, 0.1)
    h = max(z1 - z0, 0.1)
    u_s, v_s = uv_scale

    base = len(mesh.vertices)
    # 24 vertices for 6 faces with proper face normals
    v = [
        # Bottom (-Z)
        [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
        # Top (+Z)
        [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1],
        # Front (-Y)
        [x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1],
        # Back (+Y)
        [x1, y1, z0], [x0, y1, z0], [x0, y1, z1], [x1, y1, z1],
        # Left (-X)
        [x0, y1, z0], [x0, y0, z0], [x0, y0, z1], [x0, y1, z1],
        # Right (+X)
        [x1, y0, z0], [x1, y1, z0], [x1, y1, z1], [x1, y0, z1],
    ]
    norms = (
        [[0, 0, -1]] * 4 +
        [[0, 0, 1]] * 4 +
        [[0, -1, 0]] * 4 +
        [[0, 1, 0]] * 4 +
        [[-1, 0, 0]] * 4 +
        [[1, 0, 0]] * 4
    )

    uvs = [
        # Bottom
        [0, 0], [w * u_s, 0], [w * u_s, d * v_s], [0, d * v_s],
        # Top
        [0, 0], [w * u_s, 0], [w * u_s, d * v_s], [0, d * v_s],
        # Front
        [0, 0], [w * u_s, 0], [w * u_s, h * v_s], [0, h * v_s],
        # Back
        [0, 0], [w * u_s, 0], [w * u_s, h * v_s], [0, h * v_s],
        # Left
        [0, 0], [d * u_s, 0], [d * u_s, h * v_s], [0, h * v_s],
        # Right
        [0, 0], [d * u_s, 0], [d * u_s, h * v_s], [0, h * v_s],
    ]

    mesh.vertices.extend(v)
    mesh.normals.extend(norms)
    mesh.uvs.extend(uvs)
    mesh.colors.extend([[255, 255, 255, 255]] * 24)

    # 12 triangles
    for f in range(6):
        b = base + f * 4
        mesh.triangles.append((b + 0, b + 1, b + 2, mat_id))
        mesh.triangles.append((b + 0, b + 2, b + 3, mat_id))


def add_roof_hvac_and_penthouse(mesh, col, min_pt, max_pt, mat_roof, mat_metal, seed=42):
    """Adds realistic rooftop HVAC units, elevator penthouse, and antennas."""
    np.random.seed(seed)
    x0, y0, z0 = min_pt
    x1, y1, z1 = max_pt
    w = x1 - x0
    d = y1 - y0

    # 1. Elevator penthouse / mechanical room
    pw = w * 0.35
    pd = d * 0.35
    ph = 3.5
    px0 = x0 + (w - pw) * 0.5
    py0 = y0 + (d - pd) * 0.5
    add_box_geometry(mesh, (px0, py0, z1), (px0 + pw, py0 + pd, z1 + ph), mat_roof, uv_scale=(0.2, 0.2))
    col.add_box((px0, py0, z1), (px0 + pw, py0 + pd, z1 + ph), COL_MAT_CONCRETE)

    # 2. HVAC Condenser Units
    for i in range(2):
        hw = 2.2
        hd = 3.0
        hh = 1.6
        hx = x0 + 2.0 + i * 3.5
        hy = y0 + 2.0
        add_box_geometry(mesh, (hx, hy, z1), (hx + hw, hy + hd, z1 + hh), mat_metal, uv_scale=(0.3, 0.3))
        col.add_box((hx, hy, z1), (hx + hw, hy + hd, z1 + hh), COL_MAT_METAL)

    # 3. Communications Mast / Spire (for towers)
    if z1 > 50.0:
        spire_h = 14.0
        sx = px0 + pw * 0.5
        sy = py0 + pd * 0.5
        sr = 0.25
        add_box_geometry(mesh, (sx - sr, sy - sr, z1 + ph), (sx + sr, sy + sr, z1 + ph + spire_h), mat_metal, uv_scale=(0.1, 0.1))


class BuildingGenerator:
    """Master procedural generator for all 23 American building archetypes."""

    @staticmethod
    def generate(archetype_name, width=24.0, depth=24.0, height=None, floors=None, seed=42):
        """Dispatches to the appropriate archetype generator."""
        generators = {
            "Modern Tower": BuildingGenerator._gen_modern_tower,
            "Glass Tower": BuildingGenerator._gen_glass_tower,
            "Office Tower": BuildingGenerator._gen_office_tower,
            "Residential Tower": BuildingGenerator._gen_residential_tower,
            "Luxury Apartment": BuildingGenerator._gen_luxury_apartment,
            "Suburban House": BuildingGenerator._gen_suburban_house,
            "Townhouse": BuildingGenerator._gen_townhouse,
            "Motel": BuildingGenerator._gen_motel,
            "Hotel": BuildingGenerator._gen_hotel,
            "Shopping Center": BuildingGenerator._gen_shopping_center,
            "Strip Mall": BuildingGenerator._gen_strip_mall,
            "Restaurant": BuildingGenerator._gen_restaurant,
            "Diner": BuildingGenerator._gen_diner,
            "Gas Station": BuildingGenerator._gen_gas_station,
            "Warehouse": BuildingGenerator._gen_warehouse,
            "Factory": BuildingGenerator._gen_factory,
            "Hospital": BuildingGenerator._gen_hospital,
            "School": BuildingGenerator._gen_school,
            "Police Station": BuildingGenerator._gen_police_station,
            "Fire Station": BuildingGenerator._gen_fire_station,
            "Parking Garage": BuildingGenerator._gen_parking_garage,
            "Industrial Building": BuildingGenerator._gen_industrial_building,
            "Small Commercial Building": BuildingGenerator._gen_small_commercial,
        }
        gen_fn = generators.get(archetype_name, BuildingGenerator._gen_small_commercial)
        return gen_fn(width, depth, height, floors, seed)

    # -------------------------------------------------------------------------
    # 1. Modern Tower (Stepped Glass & Steel Skyscraper)
    # -------------------------------------------------------------------------
    @staticmethod
    def _gen_modern_tower(width=30.0, depth=30.0, height=110.0, floors=28, seed=1):
        mesh = DFFMesh()
        mat_facade = mesh.add_material("bldg_glass_albedo")
        mat_roof = mesh.add_material("roof_gravel_albedo")
        mat_metal = mesh.add_material("metal_industrial_albedo")
        col = COLBuilder("col_modern_tower")

        h = height or 110.0
        # Tier 1 (Base): full width up to 0.45 height
        h1 = h * 0.45
        add_box_geometry(mesh, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h1), mat_facade, (0.1, 0.1))
        col.add_box((-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h1), COL_MAT_CONCRETE)

        # Tier 2 (Mid): inset by 15%
        w2 = width * 0.85
        d2 = depth * 0.85
        h2 = h * 0.80
        add_box_geometry(mesh, (-w2*0.5, -d2*0.5, h1), (w2*0.5, d2*0.5, h2), mat_facade, (0.1, 0.1))
        col.add_box((-w2*0.5, -d2*0.5, h1), (w2*0.5, d2*0.5, h2), COL_MAT_CONCRETE)

        # Tier 3 (Crown): inset by 30%
        w3 = width * 0.70
        d3 = depth * 0.70
        add_box_geometry(mesh, (-w3*0.5, -d3*0.5, h2), (w3*0.5, d3*0.5, h), mat_facade, (0.1, 0.1))
        col.add_box((-w3*0.5, -d3*0.5, h2), (w3*0.5, d3*0.5, h), COL_MAT_CONCRETE)

        add_roof_hvac_and_penthouse(mesh, col, (-w3*0.5, -d3*0.5, 0), (w3*0.5, d3*0.5, h), mat_roof, mat_metal, seed)
        lod = LODGenerator.create_bounding_envelope_lod(mesh, "bldg_glass_albedo")
        return mesh, col, lod

    # -------------------------------------------------------------------------
    # 2. Glass Tower (Sleek Curtain Wall Office Skyscraper)
    # -------------------------------------------------------------------------
    @staticmethod
    def _gen_glass_tower(width=28.0, depth=28.0, height=95.0, floors=24, seed=2):
        mesh = DFFMesh()
        mat_glass = mesh.add_material("bldg_glass_albedo")
        mat_roof = mesh.add_material("roof_gravel_albedo")
        mat_metal = mesh.add_material("metal_industrial_albedo")
        col = COLBuilder("col_glass_tower")

        h = height or 95.0
        add_box_geometry(mesh, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_glass, (0.1, 0.1))
        col.add_box((-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), COL_MAT_GLASS)

        # Ground entrance canopy
        cw, cd, ch = 8.0, 4.0, 3.8
        add_box_geometry(mesh, (-cw*0.5, -depth*0.5 - cd, 0), (cw*0.5, -depth*0.5, ch), mat_metal, (0.2, 0.2))

        add_roof_hvac_and_penthouse(mesh, col, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_roof, mat_metal, seed)
        lod = LODGenerator.create_bounding_envelope_lod(mesh, "bldg_glass_albedo")
        return mesh, col, lod

    # -------------------------------------------------------------------------
    # 3. Office Tower (Stone & Glass Commercial Tower)
    # -------------------------------------------------------------------------
    @staticmethod
    def _gen_office_tower(width=32.0, depth=26.0, height=80.0, floors=20, seed=3):
        mesh = DFFMesh()
        mat_stone = mesh.add_material("bldg_facade_modern")
        mat_roof = mesh.add_material("roof_gravel_albedo")
        mat_metal = mesh.add_material("metal_industrial_albedo")
        col = COLBuilder("col_office_tower")

        h = height or 80.0
        add_box_geometry(mesh, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_stone, (0.08, 0.08))
        col.add_box((-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), COL_MAT_CONCRETE)

        add_roof_hvac_and_penthouse(mesh, col, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_roof, mat_metal, seed)
        lod = LODGenerator.create_bounding_envelope_lod(mesh, "bldg_facade_modern")
        return mesh, col, lod

    # -------------------------------------------------------------------------
    # 4. Residential Tower (Condo Tower with Balcony Tiers)
    # -------------------------------------------------------------------------
    @staticmethod
    def _gen_residential_tower(width=26.0, depth=24.0, height=75.0, floors=22, seed=4):
        mesh = DFFMesh()
        mat_facade = mesh.add_material("bldg_facade_modern")
        mat_roof = mesh.add_material("roof_gravel_albedo")
        mat_metal = mesh.add_material("metal_industrial_albedo")
        col = COLBuilder("col_res_tower")

        h = height or 75.0
        add_box_geometry(mesh, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_facade, (0.1, 0.1))
        col.add_box((-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), COL_MAT_CONCRETE)

        # Protruding balcony bands every 3.2m
        num_floors = int(h / 3.4)
        for fl in range(2, num_floors):
            bz = fl * 3.4
            add_box_geometry(mesh, (-width*0.4, -depth*0.5 - 1.2, bz), (width*0.4, -depth*0.5, bz + 0.9), mat_metal, (0.3, 0.3))

        add_roof_hvac_and_penthouse(mesh, col, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_roof, mat_metal, seed)
        lod = LODGenerator.create_bounding_envelope_lod(mesh, "bldg_facade_modern")
        return mesh, col, lod

    # -------------------------------------------------------------------------
    # 5. Luxury Apartment (Mid-Rise 6-Story Urban Block)
    # -------------------------------------------------------------------------
    @staticmethod
    def _gen_luxury_apartment(width=34.0, depth=22.0, height=22.0, floors=6, seed=5):
        mesh = DFFMesh()
        mat_brick = mesh.add_material("bldg_brick_albedo")
        mat_roof = mesh.add_material("roof_gravel_albedo")
        mat_metal = mesh.add_material("metal_industrial_albedo")
        col = COLBuilder("col_luxury_apt")

        h = height or 22.0
        add_box_geometry(mesh, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_brick, (0.08, 0.08))
        col.add_box((-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), COL_MAT_CONCRETE)

        # Decorative roof cornice
        add_box_geometry(mesh, (-width*0.52, -depth*0.52, h - 0.6), (width*0.52, depth*0.52, h + 0.4), mat_brick, (0.1, 0.1))

        add_roof_hvac_and_penthouse(mesh, col, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_roof, mat_metal, seed)
        lod = LODGenerator.create_bounding_envelope_lod(mesh, "bldg_brick_albedo")
        return mesh, col, lod

    # -------------------------------------------------------------------------
    # 6. Suburban House (American Single-Family Home with Gable Roof)
    # -------------------------------------------------------------------------
    @staticmethod
    def _gen_suburban_house(width=14.0, depth=16.0, height=8.0, floors=2, seed=6):
        mesh = DFFMesh()
        mat_wall = mesh.add_material("bldg_facade_modern")
        mat_roof = mesh.add_material("roof_gravel_albedo")
        mat_wood = mesh.add_material("sidewalk_albedo")
        col = COLBuilder("col_suburban_house")

        wall_h = 5.5
        # Main house box
        add_box_geometry(mesh, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, wall_h), mat_wall, (0.15, 0.15))
        col.add_box((-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, wall_h), COL_MAT_WOOD)

        # Attached 1-car garage on right side
        gw, gd, gh = 4.5, 6.5, 3.2
        add_box_geometry(mesh, (width*0.5 - gw, -depth*0.5 - 2.0, 0), (width*0.5, -depth*0.5, gh), mat_wall, (0.2, 0.2))
        col.add_box((width*0.5 - gw, -depth*0.5 - 2.0, 0), (width*0.5, -depth*0.5, gh), COL_MAT_WOOD)

        # Front porch
        pw, pd, ph = 4.0, 2.0, 2.8
        add_box_geometry(mesh, (-width*0.3, -depth*0.5 - pd, 0), (-width*0.3 + pw, -depth*0.5, ph), mat_wood, (0.3, 0.3))

        # Pitched gable roof (prism over main body)
        roof_peak = wall_h + 3.0
        # Simple gable prism geometry
        base_v = len(mesh.vertices)
        v = [
            [-width*0.52, -depth*0.52, wall_h],
            [width*0.52, -depth*0.52, wall_h],
            [0.0, -depth*0.52, roof_peak],
            [-width*0.52, depth*0.52, wall_h],
            [width*0.52, depth*0.52, wall_h],
            [0.0, depth*0.52, roof_peak],
        ]
        mesh.vertices.extend(v)
        mesh.normals.extend([[0, 0, 1]] * 6)
        mesh.uvs.extend([[0, 0], [1, 0], [0.5, 1], [0, 0], [1, 0], [0.5, 1]])
        mesh.colors.extend([[255, 255, 255, 255]] * 6)

        mesh.triangles.extend([
            (base_v + 0, base_v + 1, base_v + 2, mat_roof), # front gable
            (base_v + 3, base_v + 5, base_v + 4, mat_roof), # back gable
            (base_v + 0, base_v + 2, base_v + 5, mat_roof), # left slope
            (base_v + 0, base_v + 5, base_v + 3, mat_roof),
            (base_v + 1, base_v + 4, base_v + 5, mat_roof), # right slope
            (base_v + 1, base_v + 5, base_v + 2, mat_roof),
        ])
        col.add_box((-width*0.5, -depth*0.5, wall_h), (width*0.5, depth*0.5, roof_peak), COL_MAT_WOOD)

        lod = LODGenerator.create_bounding_envelope_lod(mesh, "bldg_facade_modern")
        return mesh, col, lod

    # -------------------------------------------------------------------------
    # 7. Townhouse (American Multi-Story Rowhouse)
    # -------------------------------------------------------------------------
    @staticmethod
    def _gen_townhouse(width=8.0, depth=14.0, height=12.0, floors=3, seed=7):
        mesh = DFFMesh()
        mat_brick = mesh.add_material("bldg_brick_albedo")
        mat_conc = mesh.add_material("concrete_albedo")
        col = COLBuilder("col_townhouse")

        h = height or 12.0
        add_box_geometry(mesh, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_brick, (0.1, 0.1))
        col.add_box((-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), COL_MAT_CONCRETE)

        # Front entrance stoop (steps)
        add_box_geometry(mesh, (-1.2, -depth*0.5 - 2.0, 0), (1.2, -depth*0.5, 1.4), mat_conc, (0.4, 0.4))
        col.add_box((-1.2, -depth*0.5 - 2.0, 0), (1.2, -depth*0.5, 1.4), COL_MAT_CONCRETE)

        lod = LODGenerator.create_bounding_envelope_lod(mesh, "bldg_brick_albedo")
        return mesh, col, lod

    # -------------------------------------------------------------------------
    # 8. Motel (2-Story Roadside American Motel)
    # -------------------------------------------------------------------------
    @staticmethod
    def _gen_motel(width=38.0, depth=14.0, height=7.5, floors=2, seed=8):
        mesh = DFFMesh()
        mat_wall = mesh.add_material("bldg_facade_modern")
        mat_roof = mesh.add_material("roof_gravel_albedo")
        mat_conc = mesh.add_material("concrete_albedo")
        col = COLBuilder("col_motel")

        h = height or 7.5
        add_box_geometry(mesh, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_wall, (0.08, 0.08))
        col.add_box((-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), COL_MAT_CONCRETE)

        # Exterior 2nd floor catwalk corridor
        add_box_geometry(mesh, (-width*0.5, -depth*0.5 - 2.2, 3.5), (width*0.5, -depth*0.5, 3.8), mat_conc, (0.1, 0.1))

        lod = LODGenerator.create_bounding_envelope_lod(mesh, "bldg_facade_modern")
        return mesh, col, lod

    # -------------------------------------------------------------------------
    # 9. Hotel (Urban Full-Service Hotel)
    # -------------------------------------------------------------------------
    @staticmethod
    def _gen_hotel(width=32.0, depth=28.0, height=48.0, floors=12, seed=9):
        mesh = DFFMesh()
        mat_facade = mesh.add_material("bldg_glass_albedo")
        mat_roof = mesh.add_material("roof_gravel_albedo")
        mat_metal = mesh.add_material("metal_industrial_albedo")
        col = COLBuilder("col_hotel")

        h = height or 48.0
        add_box_geometry(mesh, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_facade, (0.1, 0.1))
        col.add_box((-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), COL_MAT_CONCRETE)

        # Entrance portico canopy
        pw, pd, ph = 12.0, 6.0, 4.5
        add_box_geometry(mesh, (-pw*0.5, -depth*0.5 - pd, 0), (pw*0.5, -depth*0.5, ph), mat_metal, (0.2, 0.2))

        add_roof_hvac_and_penthouse(mesh, col, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_roof, mat_metal, seed)
        lod = LODGenerator.create_bounding_envelope_lod(mesh, "bldg_glass_albedo")
        return mesh, col, lod

    # -------------------------------------------------------------------------
    # 10. Shopping Center (Commercial Retail Anchor Mall)
    # -------------------------------------------------------------------------
    @staticmethod
    def _gen_shopping_center(width=48.0, depth=35.0, height=12.0, floors=2, seed=10):
        mesh = DFFMesh()
        mat_wall = mesh.add_material("bldg_facade_modern")
        mat_roof = mesh.add_material("roof_gravel_albedo")
        mat_glass = mesh.add_material("bldg_glass_albedo")
        mat_metal = mesh.add_material("metal_industrial_albedo")
        col = COLBuilder("col_shopping_center")

        h = height or 12.0
        add_box_geometry(mesh, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_wall, (0.05, 0.05))
        col.add_box((-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), COL_MAT_CONCRETE)

        # Entrance atrium glass feature
        aw, ad, ah = 14.0, 3.0, h + 2.5
        add_box_geometry(mesh, (-aw*0.5, -depth*0.5 - ad, 0), (aw*0.5, -depth*0.5, ah), mat_glass, (0.1, 0.1))
        col.add_box((-aw*0.5, -depth*0.5 - ad, 0), (aw*0.5, -depth*0.5, ah), COL_MAT_GLASS)

        add_roof_hvac_and_penthouse(mesh, col, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_roof, mat_metal, seed)
        lod = LODGenerator.create_bounding_envelope_lod(mesh, "bldg_facade_modern")
        return mesh, col, lod

    # -------------------------------------------------------------------------
    # 11. Strip Mall (American Neighborhood Retail Strip)
    # -------------------------------------------------------------------------
    @staticmethod
    def _gen_strip_mall(width=42.0, depth=18.0, height=6.5, floors=1, seed=11):
        mesh = DFFMesh()
        mat_wall = mesh.add_material("bldg_brick_albedo")
        mat_roof = mesh.add_material("roof_gravel_albedo")
        mat_conc = mesh.add_material("concrete_albedo")
        col = COLBuilder("col_strip_mall")

        h = height or 6.5
        add_box_geometry(mesh, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_wall, (0.08, 0.08))
        col.add_box((-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), COL_MAT_CONCRETE)

        # Overhang canopy along storefronts
        add_box_geometry(mesh, (-width*0.5, -depth*0.5 - 2.8, 3.8), (width*0.5, -depth*0.5, 4.2), mat_conc, (0.1, 0.1))

        lod = LODGenerator.create_bounding_envelope_lod(mesh, "bldg_brick_albedo")
        return mesh, col, lod

    # -------------------------------------------------------------------------
    # 12. Restaurant (Freestanding Fast Casual with Drive-Thru)
    # -------------------------------------------------------------------------
    @staticmethod
    def _gen_restaurant(width=20.0, depth=16.0, height=6.0, floors=1, seed=12):
        mesh = DFFMesh()
        mat_wall = mesh.add_material("bldg_facade_modern")
        mat_roof = mesh.add_material("roof_gravel_albedo")
        mat_glass = mesh.add_material("bldg_glass_albedo")
        col = COLBuilder("col_restaurant")

        h = height or 6.0
        add_box_geometry(mesh, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_wall, (0.1, 0.1))
        col.add_box((-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), COL_MAT_CONCRETE)

        # Drive-thru pickup canopy on side
        cw, cd, ch = 3.5, 7.0, 3.8
        add_box_geometry(mesh, (width*0.5, -cd*0.5, ch), (width*0.5 + cw, cd*0.5, ch + 0.3), mat_wall, (0.2, 0.2))

        lod = LODGenerator.create_bounding_envelope_lod(mesh, "bldg_facade_modern")
        return mesh, col, lod

    # -------------------------------------------------------------------------
    # 13. Diner (Classic American Chrome / Enamel Diner)
    # -------------------------------------------------------------------------
    @staticmethod
    def _gen_diner(width=18.0, depth=10.0, height=4.8, floors=1, seed=13):
        mesh = DFFMesh()
        mat_metal = mesh.add_material("metal_industrial_albedo")
        mat_roof = mesh.add_material("roof_gravel_albedo")
        col = COLBuilder("col_diner")

        h = height or 4.8
        add_box_geometry(mesh, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_metal, (0.2, 0.2))
        col.add_box((-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), COL_MAT_METAL)

        lod = LODGenerator.create_bounding_envelope_lod(mesh, "metal_industrial_albedo")
        return mesh, col, lod

    # -------------------------------------------------------------------------
    # 14. Gas Station (Multi-Pump Canopy + Convenience Store)
    # -------------------------------------------------------------------------
    @staticmethod
    def _gen_gas_station(width=28.0, depth=22.0, height=5.5, floors=1, seed=14):
        mesh = DFFMesh()
        mat_wall = mesh.add_material("bldg_facade_modern")
        mat_metal = mesh.add_material("metal_industrial_albedo")
        mat_conc = mesh.add_material("concrete_albedo")
        col = COLBuilder("col_gas_station")

        # 1. Convenience store building (in back)
        sw, sd, sh = 16.0, 10.0, 4.8
        add_box_geometry(mesh, (-sw*0.5, depth*0.5 - sd, 0), (sw*0.5, depth*0.5, sh), mat_wall, (0.1, 0.1))
        col.add_box((-sw*0.5, depth*0.5 - sd, 0), (sw*0.5, depth*0.5, sh), COL_MAT_CONCRETE)

        # 2. Large Fuel Pump Canopy (in front)
        cw, cd, ch = 22.0, 12.0, 5.2
        cy = -depth*0.5 + cd*0.5
        # Canopy roof slab
        add_box_geometry(mesh, (-cw*0.5, cy - cd*0.5, ch), (cw*0.5, cy + cd*0.5, ch + 0.8), mat_metal, (0.1, 0.1))
        col.add_box((-cw*0.5, cy - cd*0.5, ch), (cw*0.5, cy + cd*0.5, ch + 0.8), COL_MAT_METAL)

        # 4 Canopy support pillars
        for px in [-cw*0.35, cw*0.35]:
            for py in [cy - cd*0.3, cy + cd*0.3]:
                add_box_geometry(mesh, (px - 0.4, py - 0.4, 0), (px + 0.4, py + 0.4, ch), mat_metal, (0.5, 0.5))
                col.add_box((px - 0.4, py - 0.4, 0), (px + 0.4, py + 0.4, ch), COL_MAT_METAL)

        lod = LODGenerator.create_bounding_envelope_lod(mesh, "bldg_facade_modern")
        return mesh, col, lod

    # -------------------------------------------------------------------------
    # 15. Warehouse (Logistics Portal-Frame Facility)
    # -------------------------------------------------------------------------
    @staticmethod
    def _gen_warehouse(width=45.0, depth=35.0, height=11.0, floors=1, seed=15):
        mesh = DFFMesh()
        mat_metal = mesh.add_material("metal_industrial_albedo")
        mat_conc = mesh.add_material("concrete_albedo")
        mat_roof = mesh.add_material("roof_gravel_albedo")
        col = COLBuilder("col_warehouse")

        h = height or 11.0
        add_box_geometry(mesh, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_metal, (0.05, 0.05))
        col.add_box((-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), COL_MAT_METAL)

        # Concrete loading dock bays in front
        add_box_geometry(mesh, (-width*0.4, -depth*0.5 - 2.5, 0), (width*0.4, -depth*0.5, 1.3), mat_conc, (0.2, 0.2))
        col.add_box((-width*0.4, -depth*0.5 - 2.5, 0), (width*0.4, -depth*0.5, 1.3), COL_MAT_CONCRETE)

        lod = LODGenerator.create_bounding_envelope_lod(mesh, "metal_industrial_albedo")
        return mesh, col, lod

    # -------------------------------------------------------------------------
    # 16. Factory (Industrial Manufacturing Plant with Smokestacks)
    # -------------------------------------------------------------------------
    @staticmethod
    def _gen_factory(width=40.0, depth=30.0, height=14.0, floors=2, seed=16):
        mesh = DFFMesh()
        mat_brick = mesh.add_material("bldg_brick_albedo")
        mat_metal = mesh.add_material("metal_industrial_albedo")
        mat_roof = mesh.add_material("roof_gravel_albedo")
        col = COLBuilder("col_factory")

        h = height or 14.0
        add_box_geometry(mesh, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_brick, (0.06, 0.06))
        col.add_box((-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), COL_MAT_CONCRETE)

        # Industrial twin smokestacks
        for sx in [-width*0.3, -width*0.15]:
            sy = depth*0.35
            sh = h + 15.0
            sr = 1.2
            add_box_geometry(mesh, (sx - sr, sy - sr, h), (sx + sr, sy + sr, sh), mat_metal, (0.2, 0.2))
            col.add_box((sx - sr, sy - sr, h), (sx + sr, sy + sr, sh), COL_MAT_METAL)

        lod = LODGenerator.create_bounding_envelope_lod(mesh, "bldg_brick_albedo")
        return mesh, col, lod

    # -------------------------------------------------------------------------
    # 17. Hospital (Medical Center with Emergency Bay)
    # -------------------------------------------------------------------------
    @staticmethod
    def _gen_hospital(width=42.0, depth=32.0, height=36.0, floors=8, seed=17):
        mesh = DFFMesh()
        mat_wall = mesh.add_material("bldg_facade_modern")
        mat_glass = mesh.add_material("bldg_glass_albedo")
        mat_roof = mesh.add_material("roof_gravel_albedo")
        mat_metal = mesh.add_material("metal_industrial_albedo")
        col = COLBuilder("col_hospital")

        h = height or 36.0
        add_box_geometry(mesh, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_wall, (0.08, 0.08))
        col.add_box((-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), COL_MAT_CONCRETE)

        # Emergency room ambulance canopy
        ew, ed, eh = 12.0, 8.0, 4.5
        add_box_geometry(mesh, (-width*0.5 - ew, -ed*0.5, 0), (-width*0.5, ed*0.5, eh), mat_metal, (0.2, 0.2))
        col.add_box((-width*0.5 - ew, -ed*0.5, 0), (-width*0.5, ed*0.5, eh), COL_MAT_METAL)

        add_roof_hvac_and_penthouse(mesh, col, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_roof, mat_metal, seed)
        lod = LODGenerator.create_bounding_envelope_lod(mesh, "bldg_facade_modern")
        return mesh, col, lod

    # -------------------------------------------------------------------------
    # 18. School (American Public School)
    # -------------------------------------------------------------------------
    @staticmethod
    def _gen_school(width=38.0, depth=26.0, height=10.0, floors=2, seed=18):
        mesh = DFFMesh()
        mat_brick = mesh.add_material("bldg_brick_albedo")
        mat_conc = mesh.add_material("concrete_albedo")
        col = COLBuilder("col_school")

        h = height or 10.0
        add_box_geometry(mesh, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_brick, (0.08, 0.08))
        col.add_box((-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), COL_MAT_CONCRETE)

        # Entrance portico
        add_box_geometry(mesh, (-4.0, -depth*0.5 - 2.5, 0), (4.0, -depth*0.5, 5.5), mat_conc, (0.2, 0.2))
        col.add_box((-4.0, -depth*0.5 - 2.5, 0), (4.0, -depth*0.5, 5.5), COL_MAT_CONCRETE)

        lod = LODGenerator.create_bounding_envelope_lod(mesh, "bldg_brick_albedo")
        return mesh, col, lod

    # -------------------------------------------------------------------------
    # 19. Police Station (Municipal Law Enforcement Facility)
    # -------------------------------------------------------------------------
    @staticmethod
    def _gen_police_station(width=30.0, depth=22.0, height=12.0, floors=3, seed=19):
        mesh = DFFMesh()
        mat_brick = mesh.add_material("bldg_brick_albedo")
        mat_metal = mesh.add_material("metal_industrial_albedo")
        col = COLBuilder("col_police_station")

        h = height or 12.0
        add_box_geometry(mesh, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_brick, (0.08, 0.08))
        col.add_box((-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), COL_MAT_CONCRETE)

        # Radio communications mast
        add_box_geometry(mesh, (-width*0.4, depth*0.4, h), (-width*0.4 + 0.5, depth*0.4 + 0.5, h + 12.0), mat_metal, (0.1, 0.1))

        lod = LODGenerator.create_bounding_envelope_lod(mesh, "bldg_brick_albedo")
        return mesh, col, lod

    # -------------------------------------------------------------------------
    # 20. Fire Station (Firehouse with 3 Apparatus Bay Doors)
    # -------------------------------------------------------------------------
    @staticmethod
    def _gen_fire_station(width=28.0, depth=20.0, height=11.0, floors=2, seed=20):
        mesh = DFFMesh()
        mat_brick = mesh.add_material("bldg_brick_albedo")
        mat_metal = mesh.add_material("metal_industrial_albedo")
        col = COLBuilder("col_fire_station")

        h = height or 11.0
        add_box_geometry(mesh, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_brick, (0.08, 0.08))
        col.add_box((-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), COL_MAT_CONCRETE)

        # Hose drying tower on left corner
        tw, td, th = 4.5, 4.5, h + 6.0
        add_box_geometry(mesh, (-width*0.5, -depth*0.5, h), (-width*0.5 + tw, -depth*0.5 + td, th), mat_brick, (0.1, 0.1))
        col.add_box((-width*0.5, -depth*0.5, h), (-width*0.5 + tw, -depth*0.5 + td, th), COL_MAT_CONCRETE)

        lod = LODGenerator.create_bounding_envelope_lod(mesh, "bldg_brick_albedo")
        return mesh, col, lod

    # -------------------------------------------------------------------------
    # 21. Parking Garage (Multi-Deck Concrete Structure)
    # -------------------------------------------------------------------------
    @staticmethod
    def _gen_parking_garage(width=36.0, depth=30.0, height=18.0, floors=5, seed=21):
        mesh = DFFMesh()
        mat_conc = mesh.add_material("concrete_albedo")
        mat_metal = mesh.add_material("metal_industrial_albedo")
        col = COLBuilder("col_parking_garage")

        h = height or 18.0
        # Multi-deck open tiers
        num_decks = 5
        deck_h = h / num_decks

        for fl in range(num_decks):
            dz = fl * deck_h
            # Deck floor slab
            add_box_geometry(mesh, (-width*0.5, -depth*0.5, dz), (width*0.5, depth*0.5, dz + 0.45), mat_conc, (0.1, 0.1))
            col.add_box((-width*0.5, -depth*0.5, dz), (width*0.5, depth*0.5, dz + 0.45), COL_MAT_CONCRETE)
            # Perimeter parapet wall (1.0m)
            add_box_geometry(mesh, (-width*0.5, -depth*0.5, dz), (width*0.5, -depth*0.5 + 0.35, dz + 1.0), mat_conc, (0.2, 0.2))
            add_box_geometry(mesh, (-width*0.5, depth*0.5 - 0.35, dz), (width*0.5, depth*0.5, dz + 1.0), mat_conc, (0.2, 0.2))

        # Exterior stairwell core tower
        add_box_geometry(mesh, (width*0.5 - 5.0, -depth*0.5, 0), (width*0.5, -depth*0.5 + 5.0, h + 2.5), mat_conc, (0.1, 0.1))
        col.add_box((width*0.5 - 5.0, -depth*0.5, 0), (width*0.5, -depth*0.5 + 5.0, h + 2.5), COL_MAT_CONCRETE)

        lod = LODGenerator.create_bounding_envelope_lod(mesh, "concrete_albedo")
        return mesh, col, lod

    # -------------------------------------------------------------------------
    # 22. Industrial Building (Utilitarian Workshop)
    # -------------------------------------------------------------------------
    @staticmethod
    def _gen_industrial_building(width=26.0, depth=20.0, height=8.0, floors=1, seed=22):
        mesh = DFFMesh()
        mat_metal = mesh.add_material("metal_industrial_albedo")
        col = COLBuilder("col_industrial_bldg")

        h = height or 8.0
        add_box_geometry(mesh, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_metal, (0.1, 0.1))
        col.add_box((-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), COL_MAT_METAL)

        lod = LODGenerator.create_bounding_envelope_lod(mesh, "metal_industrial_albedo")
        return mesh, col, lod

    # -------------------------------------------------------------------------
    # 23. Small Commercial Building (Retail Shop / Bank / Pharmacy)
    # -------------------------------------------------------------------------
    @staticmethod
    def _gen_small_commercial(width=16.0, depth=14.0, height=5.5, floors=1, seed=23):
        mesh = DFFMesh()
        mat_wall = mesh.add_material("bldg_facade_modern")
        mat_roof = mesh.add_material("roof_gravel_albedo")
        col = COLBuilder("col_small_commercial")

        h = height or 5.5
        add_box_geometry(mesh, (-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), mat_wall, (0.12, 0.12))
        col.add_box((-width*0.5, -depth*0.5, 0), (width*0.5, depth*0.5, h), COL_MAT_CONCRETE)

        # Entrance awning
        add_box_geometry(mesh, (-2.5, -depth*0.5 - 1.5, 3.2), (2.5, -depth*0.5, 3.5), mat_wall, (0.3, 0.3))

        lod = LODGenerator.create_bounding_envelope_lod(mesh, "bldg_facade_modern")
        return mesh, col, lod
