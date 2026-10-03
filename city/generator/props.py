"""
props.py - American Street Furniture and Urban Props
Generates high-detail street props with accurate COL3 collision:
Cobra-head streetlights, traffic signal gantries, cast iron fire hydrants,
USPS mailboxes, transit bus shelters, commercial dumpsters, park benches,
and overhead highway directional signs.
"""

from .rw_dff import DFFMesh
from .collision import COLBuilder, COL_MAT_METAL, COL_MAT_CONCRETE, COL_MAT_WOOD
from .bldkit import BuildingKit
from .bake import VertexBaker


class PropFactory:
    @staticmethod
    def create(prop_type):
        builders = {
            'prop_streetlight_cobra': PropFactory._gen_streetlight_cobra,
            'prop_traffic_signal':    PropFactory._gen_traffic_signal,
            'prop_fire_hydrant':      PropFactory._gen_fire_hydrant,
            'prop_usps_mailbox':      PropFactory._gen_usps_mailbox,
            'prop_bus_shelter':       PropFactory._gen_bus_shelter,
            'prop_dumpster':          PropFactory._gen_dumpster,
            'prop_park_bench':        PropFactory._gen_park_bench,
            'prop_highway_sign':      PropFactory._gen_highway_sign,
        }
        fn = builders.get(prop_type, PropFactory._gen_streetlight_cobra)
        return fn()

    @staticmethod
    def _gen_streetlight_cobra():
        """8.5m American Cobra-Head Streetlight Pole with Curved Mast Arm."""
        mesh = DFFMesh("prop_streetlight_cobra")
        col = COLBuilder("prop_streetlight_cobra")

        m_metal = mesh.add_material("metal_corrugated")
        m_neon = mesh.add_material("neon_signs_atlas")

        # Vertical Pole
        BuildingKit.add_box(mesh, (-0.15, -0.15, 0), (0.15, 0.15, 7.5), m_metal, m_metal)
        col.add_box((-0.2, -0.2, 0), (0.2, 0.2, 7.5), COL_MAT_METAL)

        # Curved Mast Arm reaching out 2.5m over street
        BuildingKit.add_box(mesh, (-0.1, 0, 7.3), (0.1, 2.5, 8.2), m_metal, m_metal)

        # Luminaire Cobra Head Fixture
        BuildingKit.add_box(mesh, (-0.25, 2.3, 7.9), (0.25, 2.9, 8.3), m_metal, m_metal)
        # Underside Light Emitter Lens
        BuildingKit.add_quad(mesh, (-0.2, 2.4, 7.89), (0.2, 2.4, 7.89), (0.2, 2.8, 7.89), (-0.2, 2.8, 7.89),
                             (0, 0), (1, 0), (1, 1), (0, 1), m_neon, normal=[0, 0, -1])

        VertexBaker.bake(mesh, emissive_materials={"neon_signs_atlas"})
        return mesh, col

    @staticmethod
    def _gen_traffic_signal():
        """Traffic Signal Mast Arm with 3-Aspect Signal Heads (Red/Yellow/Green)."""
        mesh = DFFMesh("prop_traffic_signal")
        col = COLBuilder("prop_traffic_signal")

        m_metal = mesh.add_material("metal_corrugated")
        m_signs = mesh.add_material("signs_atlas")

        # Vertical Upright Mast (6.5m high)
        BuildingKit.add_box(mesh, (-0.2, -0.2, 0), (0.2, 0.2, 6.5), m_metal, m_metal)
        col.add_box((-0.25, -0.25, 0), (0.25, 0.25, 6.5), COL_MAT_METAL)

        # Horizontal Arm (extends 7m over intersection at 6.0m clearance)
        BuildingKit.add_box(mesh, (-0.15, 0, 5.8), (0.15, 7.0, 6.2), m_metal, m_metal)

        # 2 Signal Heads hanging from mast arm
        for y_pos in [3.0, 6.0]:
            BuildingKit.add_box(mesh, (-0.2, y_pos - 0.2, 4.8), (0.2, y_pos + 0.2, 5.8), m_metal, m_metal)

        VertexBaker.bake(mesh)
        return mesh, col

    @staticmethod
    def _gen_fire_hydrant():
        """Cast Iron American Fire Hydrant with Twin Hose Nozzles."""
        mesh = DFFMesh("prop_fire_hydrant")
        col = COLBuilder("prop_fire_hydrant")

        m_metal = mesh.add_material("metal_corrugated")

        # Cylindrical Body
        BuildingKit.add_box(mesh, (-0.2, -0.2, 0), (0.2, 0.2, 0.75), m_metal, m_metal)
        # Top bonnet cap
        BuildingKit.add_box(mesh, (-0.15, -0.15, 0.75), (0.15, 0.15, 0.9), m_metal, m_metal)
        # Side nozzle caps
        BuildingKit.add_box(mesh, (-0.32, -0.1, 0.4), (0.32, 0.1, 0.55), m_metal, m_metal)

        col.add_box((-0.25, -0.25, 0), (0.25, 0.25, 0.9), COL_MAT_METAL)
        VertexBaker.bake(mesh)
        return mesh, col

    @staticmethod
    def _gen_usps_mailbox():
        """Curbside Blue USPS Mailbox with Mail Drop Slot."""
        mesh = DFFMesh("prop_usps_mailbox")
        col = COLBuilder("prop_usps_mailbox")

        m_metal = mesh.add_material("metal_corrugated")

        # Mailbox body (0.5m x 0.5m x 1.1m)
        BuildingKit.add_box(mesh, (-0.25, -0.25, 0.2), (0.25, 0.25, 1.1), m_metal, m_metal)
        # 4 Stilt Legs
        BuildingKit.add_box(mesh, (-0.22, -0.22, 0), (0.22, 0.22, 0.2), m_metal, m_metal)

        col.add_box((-0.26, -0.26, 0), (0.26, 0.26, 1.15), COL_MAT_METAL)
        VertexBaker.bake(mesh)
        return mesh, col

    @staticmethod
    def _gen_bus_shelter():
        """Glass Transit Bus Stop Shelter with Bench and Advertising Kiosk."""
        mesh = DFFMesh("prop_bus_shelter")
        col = COLBuilder("prop_bus_shelter")

        m_metal = mesh.add_material("metal_corrugated")
        m_glass = mesh.add_material("glass_curtain_a")
        m_store = mesh.add_material("storefront_atlas")

        # 4m wide x 1.8m deep x 2.6m high shelter
        # Steel frame roof
        BuildingKit.add_box(mesh, (-2.0, -0.9, 2.5), (2.0, 0.9, 2.7), m_metal, m_metal)
        col.add_box((-2.0, -0.9, 2.5), (2.0, 0.9, 2.7), COL_MAT_METAL)

        # 4 Steel Corner Posts
        for px, py in [(-1.9, -0.8), (1.9, -0.8), (-1.9, 0.8), (1.9, 0.8)]:
            BuildingKit.add_box(mesh, (px - 0.05, py - 0.05, 0), (px + 0.05, py + 0.05, 2.5), m_metal, m_metal)

        # Back glass panel
        BuildingKit.add_box(mesh, (-1.8, 0.75, 0.2), (1.8, 0.8, 2.4), m_glass, m_glass)
        col.add_box((-1.8, 0.75, 0.2), (1.8, 0.8, 2.4), COL_MAT_CONCRETE)

        # Waiting bench
        BuildingKit.add_box(mesh, (-1.4, 0.2, 0.45), (1.4, 0.6, 0.52), m_metal, m_metal)

        # Lit Advertising Poster Kiosk at side
        BuildingKit.add_box(mesh, (1.8, -0.8, 0), (1.95, 0.8, 2.5), m_store, m_metal)

        VertexBaker.bake(mesh, emissive_materials={"storefront_atlas"})
        return mesh, col

    @staticmethod
    def _gen_dumpster():
        """Commercial Green/Blue Waste Dumpster with Slanted Lid."""
        mesh = DFFMesh("prop_dumpster")
        col = COLBuilder("prop_dumpster")

        m_metal = mesh.add_material("metal_corrugated")

        # 2.2m x 1.4m x 1.3m dumpster box
        BuildingKit.add_box(mesh, (-1.1, -0.7, 0.1), (1.1, 0.7, 1.3), m_metal, m_metal)
        # Caster wheels
        BuildingKit.add_box(mesh, (-1.0, -0.6, 0), (1.0, 0.6, 0.1), m_metal, m_metal)

        col.add_box((-1.1, -0.7, 0), (1.1, 0.7, 1.3), COL_MAT_METAL)
        VertexBaker.bake(mesh)
        return mesh, col

    @staticmethod
    def _gen_park_bench():
        """Wood Slat Park Bench with Cast Iron Armrests and Legs."""
        mesh = DFFMesh("prop_park_bench")
        col = COLBuilder("prop_park_bench")

        m_metal = mesh.add_material("metal_corrugated")
        m_conc = mesh.add_material("concrete_wall")

        # Seat slats (1.8m wide, 0.45m high)
        BuildingKit.add_box(mesh, (-0.9, -0.25, 0.42), (0.9, 0.25, 0.48), m_conc, m_conc)
        # Backrest slats
        BuildingKit.add_box(mesh, (-0.9, 0.22, 0.48), (0.9, 0.28, 0.85), m_conc, m_conc)
        # Metal side legs
        BuildingKit.add_box(mesh, (-0.85, -0.25, 0), (-0.8, 0.28, 0.85), m_metal, m_metal)
        BuildingKit.add_box(mesh, (0.8, -0.25, 0), (0.85, 0.28, 0.85), m_metal, m_metal)

        col.add_box((-0.9, -0.3, 0), (0.9, 0.3, 0.88), COL_MAT_WOOD)
        VertexBaker.bake(mesh)
        return mesh, col

    @staticmethod
    def _gen_highway_sign():
        """Overhead Highway Direction Sign Gantry Spanning 16m."""
        mesh = DFFMesh("prop_highway_sign")
        col = COLBuilder("prop_highway_sign")

        m_metal = mesh.add_material("metal_corrugated")
        m_signs = mesh.add_material("signs_atlas")

        # Two vertical steel truss posts (7.5m high)
        BuildingKit.add_box(mesh, (-8.2, -0.3, 0), (-7.8, 0.3, 7.5), m_metal, m_metal)
        BuildingKit.add_box(mesh, (7.8, -0.3, 0), (8.2, 0.3, 7.5), m_metal, m_metal)
        col.add_box((-8.3, -0.4, 0), (-7.7, 0.4, 7.5), COL_MAT_METAL)
        col.add_box((7.7, -0.4, 0), (8.3, 0.4, 7.5), COL_MAT_METAL)

        # Overhead Cross Truss Beam
        BuildingKit.add_box(mesh, (-8.0, -0.25, 6.8), (8.0, 0.25, 7.5), m_metal, m_metal)

        # Green Highway Destination Sign Board (10m x 2.4m)
        BuildingKit.add_aligned_wall(mesh, (-5.0, -0.3), (5.0, -0.3), 5.2, 7.6, m_signs)

        VertexBaker.bake(mesh, emissive_materials={"signs_atlas"})
        return mesh, col
