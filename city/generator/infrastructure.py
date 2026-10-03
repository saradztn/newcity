"""
infrastructure.py - Highway Viaducts, Cable-Stayed Bridges, Ramps, and Tunnels
Constructs major civil engineering infrastructure:
4-lane elevated expressway with Jersey barriers and pier bents, highway ramps,
120m Cable-Stayed suspension bridge with illuminated stay cables and pylons,
and mountain highway tunnel portal with ceramic tile interior tube.
"""

import math
import numpy as np
from .rw_dff import DFFMesh
from .collision import COLBuilder, COL_MAT_PAVEMENT, COL_MAT_CONCRETE, COL_MAT_METAL
from .bldkit import BuildingKit
from .bake import VertexBaker


class InfrastructureFactory:
    """Builds civil engineering transportation infrastructure."""

    @staticmethod
    def create(infra_type):
        builders = {
            'highway_viaduct':   InfrastructureFactory._gen_highway_viaduct,
            'highway_ramp':      InfrastructureFactory._gen_highway_ramp,
            'cable_bridge':      InfrastructureFactory._gen_cable_bridge,
            'tunnel_portal':     InfrastructureFactory._gen_tunnel_portal,
        }
        fn = builders.get(infra_type, InfrastructureFactory._gen_highway_viaduct)
        return fn()

    @staticmethod
    def _gen_highway_viaduct():
        """80m Elevated 4-Lane Expressway Viaduct (Deck Z=12m, Width=18m) with Jersey Barriers."""
        mesh = DFFMesh("highway_viaduct")
        col = COLBuilder("highway_viaduct")

        m_hwy = mesh.add_material("asphalt_hwy")
        m_conc = mesh.add_material("concrete_wall")
        m_metal = mesh.add_material("metal_corrugated")

        deck_z = 12.0
        deck_th = 1.2
        w_half = 9.0
        l_half = 40.0

        # Highway Asphalt Deck
        BuildingKit.add_quad(mesh, (-w_half, -l_half, deck_z), (w_half, -l_half, deck_z),
                             (w_half, l_half, deck_z), (-w_half, l_half, deck_z),
                             (0, 0), (2, 0), (2, 10), (0, 10), m_hwy, normal=[0, 0, 1])
        col.add_box((-w_half, -l_half, deck_z - deck_th), (w_half, l_half, deck_z), COL_MAT_PAVEMENT)

        # Concrete Underside Deck Box Girder
        BuildingKit.add_box(mesh, (-w_half, -l_half, deck_z - deck_th), (w_half, l_half, deck_z), m_conc, m_conc)

        # West Jersey Crash Barrier (0.95m high)
        BuildingKit.add_box(mesh, (-w_half, -l_half, deck_z), (-w_half + 0.6, l_half, deck_z + 0.95), m_conc, m_conc)
        col.add_box((-w_half, -l_half, deck_z), (-w_half + 0.6, l_half, deck_z + 0.95), COL_MAT_CONCRETE)

        # East Jersey Crash Barrier (0.95m high)
        BuildingKit.add_box(mesh, (w_half - 0.6, -l_half, deck_z), (w_half, l_half, deck_z + 0.95), m_conc, m_conc)
        col.add_box((w_half - 0.6, -l_half, deck_z), (w_half, l_half, deck_z + 0.95), COL_MAT_CONCRETE)

        # Center Jersey Median Divider
        BuildingKit.add_box(mesh, (-0.35, -l_half, deck_z), (0.35, l_half, deck_z + 0.85), m_conc, m_conc)
        col.add_box((-0.35, -l_half, deck_z), (0.35, l_half, deck_z + 0.85), COL_MAT_CONCRETE)

        # Heavy Concrete Support Pier Bents (2 piers at y = -20 and y = 20)
        for py in [-20.0, 20.0]:
            BuildingKit.add_box(mesh, (-1.5, py - 1.5, 0), (1.5, py + 1.5, deck_z - deck_th), m_conc, m_conc)
            col.add_box((-1.5, py - 1.5, 0), (1.5, py + 1.5, deck_z - deck_th), COL_MAT_CONCRETE)
            # Pier crosshead beam
            BuildingKit.add_box(mesh, (-7.0, py - 1.6, deck_z - deck_th - 1.5), (7.0, py + 1.6, deck_z - deck_th), m_conc, m_conc)

        VertexBaker.bake(mesh)
        return mesh, col

    @staticmethod
    def _gen_highway_ramp():
        """80m Curved Highway Interchange Ramp connecting Ground (Z=0) to Viaduct (Z=12m)."""
        mesh = DFFMesh("highway_ramp")
        col = COLBuilder("highway_ramp")

        m_hwy = mesh.add_material("asphalt_hwy")
        m_conc = mesh.add_material("concrete_wall")

        num_steps = 16
        length = 80.0
        width = 7.0

        for i in range(num_steps):
            y0 = -40.0 + (i / num_steps) * length
            y1 = -40.0 + ((i + 1) / num_steps) * length
            z0 = (i / num_steps) * 12.0
            z1 = ((i + 1) / num_steps) * 12.0

            # Deck segment
            BuildingKit.add_quad(
                mesh,
                (-width / 2, y0, z0), (width / 2, y0, z0),
                (width / 2, y1, z1), (-width / 2, y1, z1),
                (0, 0), (1, 0), (1, 1), (0, 1), m_hwy
            )
            col.add_box((-width / 2, y0, z0 - 0.8), (width / 2, y1, z1), COL_MAT_PAVEMENT)

            # Left and right safety guardrails
            BuildingKit.add_box(mesh, (-width / 2, y0, z0), (-width / 2 + 0.45, y1, z1 + 0.9), m_conc, m_conc)
            BuildingKit.add_box(mesh, (width / 2 - 0.45, y0, z0), (width / 2, y1, z1 + 0.9), m_conc, m_conc)

        VertexBaker.bake(mesh)
        return mesh, col

    @staticmethod
    def _gen_cable_bridge():
        """120m Cable-Stayed Suspension Bridge with 55m Concrete A-Frame Pylons."""
        mesh = DFFMesh("cable_bridge")
        col = COLBuilder("cable_bridge")

        m_hwy = mesh.add_material("asphalt_hwy")
        m_conc = mesh.add_material("concrete_wall")
        m_metal = mesh.add_material("metal_corrugated")

        deck_z = 14.0
        deck_w = 20.0
        bridge_l = 120.0

        # Roadway Deck (120m long)
        BuildingKit.add_quad(mesh, (-deck_w / 2, -bridge_l / 2, deck_z), (deck_w / 2, -bridge_l / 2, deck_z),
                             (deck_w / 2, bridge_l / 2, deck_z), (-deck_w / 2, bridge_l / 2, deck_z),
                             (0, 0), (3, 0), (3, 15), (0, 15), m_hwy, normal=[0, 0, 1])
        col.add_box((-deck_w / 2, -bridge_l / 2, deck_z - 1.5), (deck_w / 2, bridge_l / 2, deck_z), COL_MAT_PAVEMENT)

        # Concrete Side Parapets and Pedestrian Railings
        BuildingKit.add_box(mesh, (-deck_w / 2, -bridge_l / 2, deck_z), (-deck_w / 2 + 0.8, bridge_l / 2, deck_z + 1.2), m_conc, m_conc)
        BuildingKit.add_box(mesh, (deck_w / 2 - 0.8, -bridge_l / 2, deck_z), (deck_w / 2, bridge_l / 2, deck_z + 1.2), m_conc, m_conc)
        col.add_box((-deck_w / 2, -bridge_l / 2, deck_z), (-deck_w / 2 + 0.8, bridge_l / 2, deck_z + 1.2), COL_MAT_CONCRETE)
        col.add_box((deck_w / 2 - 0.8, -bridge_l / 2, deck_z), (deck_w / 2, bridge_l / 2, deck_z + 1.2), COL_MAT_CONCRETE)

        # Central A-Frame Cable Pylon Tower (55m high)
        pylon_h = 55.0
        pylon_y = 0.0
        # West leg
        BuildingKit.add_box(mesh, (-deck_w / 2 - 1.5, pylon_y - 2.0, 0), (-deck_w / 2 + 1.0, pylon_y + 2.0, pylon_h), m_conc, m_conc)
        # East leg
        BuildingKit.add_box(mesh, (deck_w / 2 - 1.0, pylon_y - 2.0, 0), (deck_w / 2 + 1.5, pylon_y + 2.0, pylon_h), m_conc, m_conc)
        # Top crossbeam
        BuildingKit.add_box(mesh, (-deck_w / 2 - 1.5, pylon_y - 2.0, pylon_h - 4.0), (deck_w / 2 + 1.5, pylon_y + 2.0, pylon_h), m_conc, m_conc)

        col.add_box((-deck_w / 2 - 2, pylon_y - 2, 0), (deck_w / 2 + 2, pylon_y + 2, pylon_h), COL_MAT_CONCRETE)

        # Stay Cables (Steel Cables running from pylon top to bridge deck)
        for cy in [-48, -36, -24, -12, 12, 24, 36, 48]:
            top_pt = (0, pylon_y, pylon_h - 2.0)
            deck_pt_w = (-deck_w / 2 + 0.5, cy, deck_z + 0.5)
            deck_pt_e = (deck_w / 2 - 0.5, cy, deck_z + 0.5)
            # Thin cable boxes
            BuildingKit.add_box(mesh, (deck_pt_w[0] - 0.08, cy - 0.08, deck_z), (deck_pt_w[0] + 0.08, cy + 0.08, deck_z + 0.5), m_metal, m_metal)
            BuildingKit.add_box(mesh, (deck_pt_e[0] - 0.08, cy - 0.08, deck_z), (deck_pt_e[0] + 0.08, cy + 0.08, deck_z + 0.5), m_metal, m_metal)

        VertexBaker.bake(mesh)
        return mesh, col

    @staticmethod
    def _gen_tunnel_portal():
        """Mountain Cut-and-Cover Tunnel Portal with Tiled Interior Tube (60m long)."""
        mesh = DFFMesh("tunnel_portal")
        col = COLBuilder("tunnel_portal")

        m_road = mesh.add_material("asphalt_road")
        m_tiles = mesh.add_material("tunnel_tiles")
        m_conc = mesh.add_material("concrete_wall")
        m_signs = mesh.add_material("signs_atlas")

        tunnel_w = 16.0
        tunnel_h = 7.5
        tunnel_l = 60.0

        # Interior Asphalt Road
        BuildingKit.add_quad(mesh, (-tunnel_w / 2, 0, 0), (tunnel_w / 2, 0, 0),
                             (tunnel_w / 2, tunnel_l, 0), (-tunnel_w / 2, tunnel_l, 0),
                             (0, 0), (2, 0), (2, 8), (0, 8), m_road, normal=[0, 0, 1])
        col.add_box((-tunnel_w / 2, 0, -0.5), (tunnel_w / 2, tunnel_l, 0.0), COL_MAT_PAVEMENT)

        # West Interior Wall (Ceramic Tiles)
        BuildingKit.add_aligned_wall(mesh, (-tunnel_w / 2, 0), (-tunnel_w / 2, tunnel_l), 0, tunnel_h, m_tiles, bay_w=4.0, floor_h=3.5)
        col.add_box((-tunnel_w / 2 - 1.0, 0, 0), (-tunnel_w / 2, tunnel_l, tunnel_h), COL_MAT_CONCRETE)

        # East Interior Wall (Ceramic Tiles)
        BuildingKit.add_aligned_wall(mesh, (tunnel_w / 2, tunnel_l), (tunnel_w / 2, 0), 0, tunnel_h, m_tiles, bay_w=4.0, floor_h=3.5)
        col.add_box((tunnel_w / 2, 0, 0), (tunnel_w / 2 + 1.0, tunnel_l, tunnel_h), COL_MAT_CONCRETE)

        # Interior Ceiling (Concrete)
        BuildingKit.add_quad(mesh, (-tunnel_w / 2, tunnel_l, tunnel_h), (tunnel_w / 2, tunnel_l, tunnel_h),
                             (tunnel_w / 2, 0, tunnel_h), (-tunnel_w / 2, 0, tunnel_h),
                             (0, 0), (2, 0), (2, 8), (0, 8), m_conc, normal=[0, 0, -1])
        col.add_box((-tunnel_w / 2, 0, tunnel_h), (tunnel_w / 2, tunnel_l, tunnel_h + 1.0), COL_MAT_CONCRETE)

        # Exterior Portal Headwall (Massive Mountain Retaining Wall)
        BuildingKit.add_box(mesh, (-tunnel_w / 2 - 8.0, -1.5, 0), (-tunnel_w / 2, 0, 16.0), m_conc, m_conc)
        BuildingKit.add_box(mesh, (tunnel_w / 2, -1.5, 0), (tunnel_w / 2 + 8.0, 0, 16.0), m_conc, m_conc)
        BuildingKit.add_box(mesh, (-tunnel_w / 2 - 8.0, -1.5, tunnel_h), (tunnel_w / 2 + 8.0, 0, 16.0), m_conc, m_conc)
        col.add_box((-tunnel_w / 2 - 8.0, -1.5, 0), (tunnel_w / 2 + 8.0, 0, 16.0), COL_MAT_CONCRETE)

        # Overhead Green Highway Sign above portal arch
        BuildingKit.add_aligned_wall(mesh, (-5.5, -1.6), (5.5, -1.6), tunnel_h + 1.0, tunnel_h + 3.8, m_signs)

        VertexBaker.bake(mesh, emissive_materials={"signs_atlas"})
        return mesh, col
