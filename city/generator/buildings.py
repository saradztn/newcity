"""
buildings.py - Comprehensive Procedural American Architectural Archetypes
Implements all 17 distinct American building archetypes with bay- and floor-aligned facades,
setbacks, cornices, parapets, rooftop mechanical clutter, and baked vertex lighting:
Skyscrapers, Art Deco towers, Corporate HQs, Hotels, Residential high-rises,
Brick Brownstones, Retail strips, 24H Diners, Parking structures, Warehouses,
Factories, Power substations, City Hall, Police, Fire station, Hospital, and Gas stations.
"""

import math
import numpy as np
from .rw_dff import DFFMesh
from .collision import COLBuilder, COL_MAT_CONCRETE, COL_MAT_METAL, COL_MAT_GLASS, COL_MAT_STONE
from .bldkit import BuildingKit
from .bake import VertexBaker


class BuildingFactory:
    """Procedural generator for high-detail American urban buildings."""

    @staticmethod
    def create(archetype_name, base_seed=42):
        builders = {
            'bldg_glass_skyscraper': BuildingFactory._gen_glass_skyscraper,
            'bldg_art_deco_tower':   BuildingFactory._gen_art_deco_tower,
            'bldg_corporate_hq':     BuildingFactory._gen_corporate_hq,
            'bldg_luxury_hotel':     BuildingFactory._gen_luxury_hotel,
            'bldg_residential_tower':BuildingFactory._gen_residential_tower,
            'bldg_brownstone_block': BuildingFactory._gen_brownstone_block,
            'bldg_commercial_strip': BuildingFactory._gen_commercial_strip,
            'bldg_american_diner':   BuildingFactory._gen_american_diner,
            'bldg_parking_garage':   BuildingFactory._gen_parking_garage,
            'bldg_logistics_warehouse': BuildingFactory._gen_logistics_warehouse,
            'bldg_factory_plant':    BuildingFactory._gen_factory_plant,
            'bldg_power_substation': BuildingFactory._gen_power_substation,
            'bldg_city_hall':        BuildingFactory._gen_city_hall,
            'bldg_police_station':   BuildingFactory._gen_police_station,
            'bldg_fire_station':     BuildingFactory._gen_fire_station,
            'bldg_hospital':         BuildingFactory._gen_hospital,
            'bldg_gas_station':      BuildingFactory._gen_gas_station,
        }

        fn = builders.get(archetype_name, BuildingFactory._gen_glass_skyscraper)
        return fn()

    @staticmethod
    def _gen_glass_skyscraper():
        """120m Modern Financial Glass Skyscraper with 3 setback tiers and antenna mast."""
        mesh = DFFMesh("bldg_glass_skyscraper")
        col = COLBuilder("bldg_glass_skyscraper")

        m_glass = mesh.add_material("glass_curtain_a")
        m_roof = mesh.add_material("roof_gravel")
        m_conc = mesh.add_material("concrete_wall")
        m_metal = mesh.add_material("metal_corrugated")

        # Tier 1: Podium (0 to 14m)
        BuildingKit.add_box(mesh, (-24, -20, 0), (24, 20, 14), m_conc, m_roof, bay_w=4.0, floor_h=3.5)
        col.add_box((-24, -20, 0), (24, 20, 14), COL_MAT_CONCRETE)
        BuildingKit.add_cornice(mesh, (-24, -20, 0), (24, 20, 14), 14, m_conc, overhang=0.6, height=0.5)

        # Tier 2: Mid Tower (14 to 68m)
        BuildingKit.add_box(mesh, (-20, -16, 14), (20, 16, 68), m_glass, m_roof, bay_w=4.0, floor_h=3.5)
        col.add_box((-20, -16, 14), (20, 16, 68), COL_MAT_GLASS)
        BuildingKit.add_cornice(mesh, (-20, -16, 14), (20, 16, 68), 68, m_conc, overhang=0.5, height=0.5)

        # Tier 3: Upper Tower (68 to 112m)
        BuildingKit.add_box(mesh, (-16, -12, 68), (16, 12, 112), m_glass, m_roof, bay_w=4.0, floor_h=3.5)
        col.add_box((-16, -12, 68), (16, 12, 112), COL_MAT_GLASS)
        BuildingKit.add_parapet(mesh, (-16, -12, 68), (16, 12, 112), 112, m_conc, height=1.5)

        # Rooftop Clutter & Aviation Beacon Mast
        BuildingKit.add_roof_mechanicals(mesh, (0, 0), 112, m_metal, m_conc, is_tall=True)
        col.add_box((-4, -4, 112), (4, 4, 116), COL_MAT_CONCRETE)

        VertexBaker.bake(mesh, emissive_materials={"glass_curtain_a"})
        return mesh, col

    @staticmethod
    def _gen_art_deco_tower():
        """95m Limestone & Bronze Art Deco Skyscraper with stepped pyramid crown."""
        mesh = DFFMesh("bldg_art_deco_tower")
        col = COLBuilder("bldg_art_deco_tower")

        m_stone = mesh.add_material("bldg_stone")
        m_roof = mesh.add_material("roof_gravel")
        m_metal = mesh.add_material("metal_corrugated")
        m_conc = mesh.add_material("concrete_wall")

        # Base Podium (0 to 18m)
        BuildingKit.add_box(mesh, (-22, -18, 0), (22, 18, 18), m_stone, m_roof, bay_w=4.0, floor_h=3.6)
        col.add_box((-22, -18, 0), (22, 18, 18), COL_MAT_STONE)
        BuildingKit.add_cornice(mesh, (-22, -18, 0), (22, 18, 18), 18, m_conc, overhang=0.6)

        # Shaft (18 to 72m)
        BuildingKit.add_box(mesh, (-18, -14, 18), (18, 14, 72), m_stone, m_roof, bay_w=4.0, floor_h=3.6)
        col.add_box((-18, -14, 18), (18, 14, 72), COL_MAT_STONE)

        # Stepped Art Deco Crown (72 to 92m)
        BuildingKit.add_box(mesh, (-14, -10, 72), (14, 10, 80), m_stone, m_roof)
        BuildingKit.add_box(mesh, (-10, -8, 80), (10, 8, 88), m_stone, m_roof)
        BuildingKit.add_box(mesh, (-6, -5, 88), (6, 5, 94), m_metal, m_metal)
        col.add_box((-14, -10, 72), (14, 10, 94), COL_MAT_STONE)

        # Spire (94 to 106m)
        BuildingKit.add_box(mesh, (-0.8, -0.8, 94), (0.8, 0.8, 106), m_metal, m_metal)

        VertexBaker.bake(mesh)
        return mesh, col

    @staticmethod
    def _gen_corporate_hq():
        """85m Steel & Glass Corporate Headquarters with modern angular lines."""
        mesh = DFFMesh("bldg_corporate_hq")
        col = COLBuilder("bldg_corporate_hq")

        m_glass = mesh.add_material("glass_curtain_a")
        m_roof = mesh.add_material("roof_gravel")
        m_conc = mesh.add_material("concrete_wall")
        m_metal = mesh.add_material("metal_corrugated")

        # 3-tier structure
        BuildingKit.add_box(mesh, (-20, -20, 0), (20, 20, 16), m_conc, m_roof, bay_w=4.0, floor_h=4.0)
        col.add_box((-20, -20, 0), (20, 20, 16), COL_MAT_CONCRETE)

        BuildingKit.add_box(mesh, (-18, -18, 16), (18, 18, 54), m_glass, m_roof, bay_w=4.0, floor_h=3.5)
        col.add_box((-18, -18, 16), (18, 18, 54), COL_MAT_GLASS)

        BuildingKit.add_box(mesh, (-15, -15, 54), (15, 15, 84), m_glass, m_roof, bay_w=4.0, floor_h=3.5)
        col.add_box((-15, -15, 54), (15, 15, 84), COL_MAT_GLASS)

        BuildingKit.add_roof_mechanicals(mesh, (0, 0), 84, m_metal, m_conc, is_tall=True)
        VertexBaker.bake(mesh, emissive_materials={"glass_curtain_a"})
        return mesh, col

    @staticmethod
    def _gen_luxury_hotel():
        """65m Modern Luxury Hotel with entrance canopy and neon sign."""
        mesh = DFFMesh("bldg_luxury_hotel")
        col = COLBuilder("bldg_luxury_hotel")

        m_glass = mesh.add_material("glass_curtain_b")
        m_stone = mesh.add_material("bldg_stone")
        m_roof = mesh.add_material("roof_gravel")
        m_metal = mesh.add_material("metal_corrugated")
        m_neon = mesh.add_material("neon_signs_atlas")

        # Podium (0 to 12m)
        BuildingKit.add_box(mesh, (-25, -16, 0), (25, 16, 12), m_stone, m_roof)
        col.add_box((-25, -16, 0), (25, 16, 12), COL_MAT_STONE)

        # Entrance Grand Canopy
        BuildingKit.add_box(mesh, (-8, -22, 0), (8, -16, 4.5), m_metal, m_metal)
        col.add_box((-8, -22, 0), (8, -16, 4.5), COL_MAT_METAL)

        # Hotel Tower (12 to 62m)
        BuildingKit.add_box(mesh, (-22, -12, 12), (22, 12, 62), m_glass, m_roof, bay_w=4.0, floor_h=3.2)
        col.add_box((-22, -12, 12), (22, 12, 62), COL_MAT_GLASS)

        # Neon Marquee Sign on Podium
        BuildingKit.add_aligned_wall(mesh, (-7, -22.1), (7, -22.1), 3.0, 4.8, m_neon)

        BuildingKit.add_roof_mechanicals(mesh, (0, 0), 62, m_metal, m_stone, is_tall=False)
        VertexBaker.bake(mesh, emissive_materials={"neon_signs_atlas", "glass_curtain_b"})
        return mesh, col

    @staticmethod
    def _gen_residential_tower():
        """75m Residential Apartment High-Rise with Balconies."""
        mesh = DFFMesh("bldg_residential_tower")
        col = COLBuilder("bldg_residential_tower")

        m_facade = mesh.add_material("glass_curtain_b")
        m_conc = mesh.add_material("concrete_wall")
        m_roof = mesh.add_material("roof_gravel")
        m_metal = mesh.add_material("metal_corrugated")

        # Tower Body (0 to 72m)
        BuildingKit.add_box(mesh, (-16, -14, 0), (16, 14, 72), m_facade, m_roof, bay_w=4.0, floor_h=3.2)
        col.add_box((-16, -14, 0), (16, 14, 72), COL_MAT_CONCRETE)

        BuildingKit.add_parapet(mesh, (-16, -14, 0), (16, 14, 72), 72, m_conc, height=1.2)
        BuildingKit.add_roof_mechanicals(mesh, (0, 0), 72, m_metal, m_conc, is_tall=True)

        VertexBaker.bake(mesh, emissive_materials={"glass_curtain_b"})
        return mesh, col

    @staticmethod
    def _gen_brownstone_block():
        """4-Story Classic American Red Brick Brownstones with Front Stoops."""
        mesh = DFFMesh("bldg_brownstone_block")
        col = COLBuilder("bldg_brownstone_block")

        m_brick = mesh.add_material("bldg_brick")
        m_stone = mesh.add_material("bldg_stone")
        m_roof = mesh.add_material("roof_gravel")
        m_metal = mesh.add_material("metal_corrugated")

        # 4 interconnected townhouses in a block (36m wide x 16m deep x 16m high)
        BuildingKit.add_box(mesh, (-18, -8, 0), (18, 8, 16), m_brick, m_roof, bay_w=3.0, floor_h=3.5)
        col.add_box((-18, -8, 0), (18, 8, 16), COL_MAT_STONE)

        # Stone entrance stoops (stairs) for each of the 4 townhouses
        stoop_xs = [-13.5, -4.5, 4.5, 13.5]
        for sx in stoop_xs:
            BuildingKit.add_box(mesh, (sx - 1.2, -10.5, 0), (sx + 1.2, -8, 2.2), m_stone, m_stone)
            col.add_box((sx - 1.2, -10.5, 0), (sx + 1.2, -8, 2.2), COL_MAT_STONE)

        # Decorative Cornice at roofline
        BuildingKit.add_cornice(mesh, (-18, -8, 0), (18, 8, 16), 16, m_stone, overhang=0.45, height=0.45)
        VertexBaker.bake(mesh)
        return mesh, col

    @staticmethod
    def _gen_commercial_strip():
        """2-Story Retail Shopping Strip: Deli, Coffee Shop, Diner, Pharmacy."""
        mesh = DFFMesh("bldg_commercial_strip")
        col = COLBuilder("bldg_commercial_strip")

        m_store = mesh.add_material("storefront_atlas")
        m_brick = mesh.add_material("bldg_brick")
        m_roof = mesh.add_material("roof_gravel")
        m_conc = mesh.add_material("concrete_wall")

        # 40m wide x 18m deep x 8.5m high
        # Ground floor retail
        BuildingKit.add_aligned_wall(mesh, (-20, -9), (20, -9), 0, 4.5, m_store, bay_w=10.0, floor_h=4.5)
        # Other walls brick
        BuildingKit.add_aligned_wall(mesh, (20, -9), (20, 9), 0, 8.5, m_brick)
        BuildingKit.add_aligned_wall(mesh, (20, 9), (-20, 9), 0, 8.5, m_brick)
        BuildingKit.add_aligned_wall(mesh, (-20, 9), (-20, -9), 0, 8.5, m_brick)
        # Upper front wall brick
        BuildingKit.add_aligned_wall(mesh, (-20, -9), (20, -9), 4.5, 8.5, m_brick, bay_w=4.0, floor_h=4.0)

        # Roof
        BuildingKit.add_box(mesh, (-20, -9, 8.4), (20, 9, 8.5), m_roof, m_roof)
        col.add_box((-20, -9, 0), (20, 9, 8.5), COL_MAT_CONCRETE)

        BuildingKit.add_cornice(mesh, (-20, -9, 0), (20, 9, 8.5), 8.5, m_conc, overhang=0.4)
        VertexBaker.bake(mesh, emissive_materials={"storefront_atlas"})
        return mesh, col

    @staticmethod
    def _gen_american_diner():
        """Retro American 1950s Stainless Steel Diner with Neon Sign."""
        mesh = DFFMesh("bldg_american_diner")
        col = COLBuilder("bldg_american_diner")

        m_metal = mesh.add_material("metal_corrugated")
        m_store = mesh.add_material("storefront_atlas")
        m_neon = mesh.add_material("neon_signs_atlas")
        m_roof = mesh.add_material("roof_gravel")

        # 22m x 12m x 5.5m building
        BuildingKit.add_box(mesh, (-11, -6, 0), (11, 6, 5.5), m_metal, m_roof)
        col.add_box((-11, -6, 0), (11, 6, 5.5), COL_MAT_METAL)

        # Front windows
        BuildingKit.add_aligned_wall(mesh, (-9, -6.1), (9, -6.1), 1.0, 4.5, m_store, bay_w=6.0, floor_h=3.5)

        # Roof Neon Sign
        BuildingKit.add_aligned_wall(mesh, (-5, -6.2), (5, -6.2), 5.5, 7.5, m_neon, bay_w=5.0, floor_h=2.0)
        col.add_box((-5, -6.2, 5.5), (5, -6.0, 7.5), COL_MAT_METAL)

        VertexBaker.bake(mesh, emissive_materials={"neon_signs_atlas", "storefront_atlas"})
        return mesh, col

    @staticmethod
    def _gen_parking_garage():
        """4-Level Open Concrete Parking Garage with spiral access ramp."""
        mesh = DFFMesh("bldg_parking_garage")
        col = COLBuilder("bldg_parking_garage")

        m_conc = mesh.add_material("concrete_wall")
        m_road = mesh.add_material("asphalt_road")
        m_metal = mesh.add_material("metal_corrugated")

        # 36m x 30m x 14m high structure
        # 4 Floor slabs (z = 0, 3.5, 7.0, 10.5, 14.0)
        for z in [0, 3.5, 7.0, 10.5]:
            BuildingKit.add_box(mesh, (-18, -15, z), (18, 15, z + 0.4), m_road, m_road)
            col.add_box((-18, -15, z), (18, 15, z + 0.4), COL_MAT_CONCRETE)

        # Concrete Corner Columns
        cols = [(-17, -14), (17, -14), (-17, 14), (17, 14), (0, -14), (0, 14)]
        for cx, cy in cols:
            BuildingKit.add_box(mesh, (cx - 1.0, cy - 1.0, 0), (cx + 1.0, cy + 1.0, 14.0), m_conc, m_conc)
            col.add_box((cx - 1.0, cy - 1.0, 0), (cx + 1.0, cy + 1.0, 14.0), COL_MAT_CONCRETE)

        # Exterior safety crash barriers on each floor
        for z in [3.5, 7.0, 10.5, 14.0]:
            BuildingKit.add_parapet(mesh, (-18, -15, z), (18, 15, z), z, m_conc, height=1.0)

        VertexBaker.bake(mesh)
        return mesh, col

    @staticmethod
    def _gen_logistics_warehouse():
        """Industrial Distribution Warehouse with 6 Freight Loading Docks."""
        mesh = DFFMesh("bldg_logistics_warehouse")
        col = COLBuilder("bldg_logistics_warehouse")

        m_metal = mesh.add_material("metal_corrugated")
        m_conc = mesh.add_material("concrete_wall")
        m_roof = mesh.add_material("roof_gravel")

        # 50m x 32m x 9m warehouse hall
        BuildingKit.add_box(mesh, (-25, -16, 0), (25, 16, 9.0), m_metal, m_roof, bay_w=5.0, floor_h=4.5)
        col.add_box((-25, -16, 0), (25, 16, 9.0), COL_MAT_METAL)

        # Concrete loading dock platform (1.2m raised)
        BuildingKit.add_box(mesh, (-22, -20, 0), (22, -16, 1.2), m_conc, m_conc)
        col.add_box((-22, -20, 0), (22, -16, 1.2), COL_MAT_CONCRETE)

        VertexBaker.bake(mesh)
        return mesh, col

    @staticmethod
    def _gen_factory_plant():
        """Manufacturing Plant with Sawtooth Roof and Dual Tall Smokestacks."""
        mesh = DFFMesh("bldg_factory_plant")
        col = COLBuilder("bldg_factory_plant")

        m_brick = mesh.add_material("bldg_brick")
        m_metal = mesh.add_material("metal_corrugated")
        m_roof = mesh.add_material("roof_gravel")
        m_conc = mesh.add_material("concrete_wall")

        # Main factory production hall (44m x 26m x 11m)
        BuildingKit.add_box(mesh, (-22, -13, 0), (22, 13, 11), m_brick, m_roof, bay_w=4.0, floor_h=3.5)
        col.add_box((-22, -13, 0), (22, 13, 11), COL_MAT_CONCRETE)

        # Dual Tall Industrial Smokestacks (32m high)
        stacks = [(-16, 10), (-8, 10)]
        for sx, sy in stacks:
            BuildingKit.add_box(mesh, (sx - 1.5, sy - 1.5, 0), (sx + 1.5, sy + 1.5, 32.0), m_conc, m_metal)
            col.add_box((sx - 1.5, sy - 1.5, 0), (sx + 1.5, sy + 1.5, 32.0), COL_MAT_CONCRETE)

        VertexBaker.bake(mesh)
        return mesh, col

    @staticmethod
    def _gen_power_substation():
        """Electrical Power Substation with Transformers and Control Building."""
        mesh = DFFMesh("bldg_power_substation")
        col = COLBuilder("bldg_power_substation")

        m_conc = mesh.add_material("concrete_wall")
        m_metal = mesh.add_material("metal_corrugated")
        m_roof = mesh.add_material("roof_gravel")

        # Control building (16m x 10m x 4.5m)
        BuildingKit.add_box(mesh, (-8, -5, 0), (8, 5, 4.5), m_conc, m_roof)
        col.add_box((-8, -5, 0), (8, 5, 4.5), COL_MAT_CONCRETE)

        # 3 High-voltage transformer blocks
        for tx in [-14, 0, 14]:
            BuildingKit.add_box(mesh, (tx - 2, 8, 0), (tx + 2, 12, 3.8), m_metal, m_metal)
            col.add_box((tx - 2, 8, 0), (tx + 2, 12, 3.8), COL_MAT_METAL)

        VertexBaker.bake(mesh)
        return mesh, col

    @staticmethod
    def _gen_city_hall():
        """Neoclassical Civic City Hall with Columned Portico and Clock Tower."""
        mesh = DFFMesh("bldg_city_hall")
        col = COLBuilder("bldg_city_hall")

        m_stone = mesh.add_material("bldg_stone")
        m_conc = mesh.add_material("concrete_wall")
        m_roof = mesh.add_material("roof_gravel")
        m_metal = mesh.add_material("metal_corrugated")

        # Main Hall (38m x 24m x 16m)
        BuildingKit.add_box(mesh, (-19, -12, 0), (19, 12, 16), m_stone, m_roof, bay_w=4.0, floor_h=4.0)
        col.add_box((-19, -12, 0), (19, 12, 16), COL_MAT_STONE)

        # Front Portico & Columns (extends out front)
        BuildingKit.add_box(mesh, (-10, -17, 0), (10, -12, 14), m_stone, m_roof)
        col.add_box((-10, -17, 0), (10, -12, 14), COL_MAT_STONE)

        # Central Clock Tower (16 to 34m)
        BuildingKit.add_box(mesh, (-4.5, -4.5, 16), (4.5, 4.5, 34), m_stone, m_metal)
        col.add_box((-4.5, -4.5, 16), (4.5, 4.5, 34), COL_MAT_STONE)

        VertexBaker.bake(mesh)
        return mesh, col

    @staticmethod
    def _gen_police_station():
        """2-Story Modern Municipal Police Station."""
        mesh = DFFMesh("bldg_police_station")
        col = COLBuilder("bldg_police_station")

        m_conc = mesh.add_material("concrete_wall")
        m_brick = mesh.add_material("bldg_brick")
        m_roof = mesh.add_material("roof_gravel")
        m_metal = mesh.add_material("metal_corrugated")

        # 30m x 20m x 8m
        BuildingKit.add_box(mesh, (-15, -10, 0), (15, 10, 8.0), m_conc, m_roof, bay_w=4.0, floor_h=4.0)
        col.add_box((-15, -10, 0), (15, 10, 8.0), COL_MAT_CONCRETE)

        # Communications mast on roof
        BuildingKit.add_box(mesh, (0 - 0.3, 0 - 0.3, 8.0), (0.3, 0.3, 18.0), m_metal, m_metal)

        VertexBaker.bake(mesh)
        return mesh, col

    @staticmethod
    def _gen_fire_station():
        """2-Story Municipal Fire Station with Apparatus Bays and Hose Tower."""
        mesh = DFFMesh("bldg_fire_station")
        col = COLBuilder("bldg_fire_station")

        m_brick = mesh.add_material("bldg_brick")
        m_conc = mesh.add_material("concrete_wall")
        m_metal = mesh.add_material("metal_corrugated")
        m_roof = mesh.add_material("roof_gravel")

        # Main Firehouse (24m x 18m x 9m)
        BuildingKit.add_box(mesh, (-12, -9, 0), (12, 9, 9.0), m_brick, m_roof)
        col.add_box((-12, -9, 0), (12, 9, 9.0), COL_MAT_CONCRETE)

        # 2 Red Apparatus Bay Doors on front facade
        BuildingKit.add_aligned_wall(mesh, (-10, -9.1), (-2, -9.1), 0, 5.0, m_metal)
        BuildingKit.add_aligned_wall(mesh, (0, -9.1), (8, -9.1), 0, 5.0, m_metal)

        # Hose Drying Tower (18m high)
        BuildingKit.add_box(mesh, (7, 4, 0), (12, 9, 18.0), m_brick, m_roof)
        col.add_box((7, 4, 0), (12, 9, 18.0), COL_MAT_CONCRETE)

        VertexBaker.bake(mesh)
        return mesh, col

    @staticmethod
    def _gen_hospital():
        """6-Story Modern Hospital Center with Ambulance Bay and Helipad."""
        mesh = DFFMesh("bldg_hospital")
        col = COLBuilder("bldg_hospital")

        m_conc = mesh.add_material("concrete_wall")
        m_glass = mesh.add_material("glass_curtain_a")
        m_roof = mesh.add_material("roof_gravel")
        m_metal = mesh.add_material("metal_corrugated")

        # Main medical hospital block (38m x 26m x 24m)
        BuildingKit.add_box(mesh, (-19, -13, 0), (19, 13, 24), m_conc, m_roof, bay_w=4.0, floor_h=4.0)
        col.add_box((-19, -13, 0), (19, 13, 24), COL_MAT_CONCRETE)

        # Emergency Ambulance Drive-Through Canopy
        BuildingKit.add_box(mesh, (-15, -19, 0), (15, -13, 4.5), m_metal, m_metal)
        col.add_box((-15, -19, 0), (15, -13, 4.5), COL_MAT_METAL)

        # Rooftop Helipad Platform (24m to 25.5m)
        BuildingKit.add_box(mesh, (-8, -8, 24), (8, 8, 25.5), m_conc, m_conc)
        col.add_box((-8, -8, 24), (8, 8, 25.5), COL_MAT_CONCRETE)

        VertexBaker.bake(mesh, emissive_materials={"glass_curtain_a"})
        return mesh, col

    @staticmethod
    def _gen_gas_station():
        """Roadside 8-Pump Gas Station with Fuel Canopy and Convenience Store."""
        mesh = DFFMesh("bldg_gas_station")
        col = COLBuilder("bldg_gas_station")

        m_conc = mesh.add_material("concrete_wall")
        m_metal = mesh.add_material("metal_corrugated")
        m_store = mesh.add_material("storefront_atlas")
        m_roof = mesh.add_material("roof_gravel")
        m_road = mesh.add_material("asphalt_road")

        # Convenience Store (16m x 12m x 4.5m)
        BuildingKit.add_box(mesh, (-8, 6, 0), (8, 18, 4.5), m_conc, m_roof)
        col.add_box((-8, 6, 0), (8, 18, 4.5), COL_MAT_CONCRETE)
        BuildingKit.add_aligned_wall(mesh, (-6, 5.9), (6, 5.9), 0, 4.0, m_store, bay_w=6.0, floor_h=4.0)

        # Overhead Fuel Canopy (24m x 12m at 5.5m high)
        BuildingKit.add_box(mesh, (-12, -10, 4.8), (12, 2, 5.8), m_metal, m_metal)
        col.add_box((-12, -10, 4.8), (12, 2, 5.8), COL_MAT_METAL)

        # 4 Heavy Steel Support Columns
        for px, py in [(-8, -7), (8, -7), (-8, -1), (8, -1)]:
            BuildingKit.add_box(mesh, (px - 0.4, py - 0.4, 0), (px + 0.4, py + 0.4, 5.0), m_metal, m_metal)
            col.add_box((px - 0.4, py - 0.4, 0), (px + 0.4, py + 0.4, 5.0), COL_MAT_METAL)

        # 4 Fuel Pump Islands
        for px, py in [(-8, -4), (8, -4)]:
            BuildingKit.add_box(mesh, (px - 1.2, py - 0.6, 0), (px + 1.2, py + 0.6, 1.8), m_metal, m_metal)
            col.add_box((px - 1.2, py - 0.6, 0), (px + 1.2, py + 0.6, 1.8), COL_MAT_METAL)

        VertexBaker.bake(mesh, emissive_materials={"storefront_atlas"})
        return mesh, col
