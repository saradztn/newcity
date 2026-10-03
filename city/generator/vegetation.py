"""
vegetation.py - Botanical Models: California Fan Palms and American Broadleaf Oaks
Generates natural trees with textured trunks and alpha-tested foliage canopies.
Includes collision trunks and low-poly LOD envelopes.
"""

import math
from .rw_dff import DFFMesh
from .collision import COLBuilder, COL_MAT_WOOD
from .bldkit import BuildingKit
from .bake import VertexBaker


class VegetationFactory:
    @staticmethod
    def create(veg_type):
        builders = {
            'veg_fan_palm': VegetationFactory._gen_fan_palm,
            'veg_oak_tree': VegetationFactory._gen_oak_tree,
        }
        fn = builders.get(veg_type, VegetationFactory._gen_fan_palm)
        return fn()

    @staticmethod
    def _gen_fan_palm():
        """12m California Fan Palm with curved trunk and radiating fronds."""
        mesh = DFFMesh("veg_fan_palm")
        col = COLBuilder("veg_fan_palm")

        m_trunk = mesh.add_material("concrete_wall")
        m_frond = mesh.add_material("palm_frond")

        # Palm Trunk (0 to 11m, radius 0.35m)
        num_segs = 8
        r = 0.35
        for i in range(num_segs):
            a0 = (i / num_segs) * 2 * math.pi
            a1 = ((i + 1) / num_segs) * 2 * math.pi
            p0 = (r * math.cos(a0), r * math.sin(a0), 0)
            p1 = (r * math.cos(a1), r * math.sin(a1), 0)
            p2 = (r * 0.8 * math.cos(a1), r * 0.8 * math.sin(a1), 11.0)
            p3 = (r * 0.8 * math.cos(a0), r * 0.8 * math.sin(a0), 11.0)
            BuildingKit.add_quad(mesh, p0, p1, p2, p3, (0, 0), (1, 0), (1, 4), (0, 4), m_trunk)

        col.add_box((-0.4, -0.4, 0), (0.4, 0.4, 11.0), COL_MAT_WOOD)

        # Radiating Fan Fronds at crown (11m to 13m)
        num_fronds = 10
        for i in range(num_fronds):
            ang = (i / num_fronds) * 2 * math.pi
            fx = 3.2 * math.cos(ang)
            fy = 3.2 * math.sin(ang)
            # Slanted quad from trunk top outward
            p0 = (0, 0, 11.0)
            p1 = (fx * 0.5 - fy * 0.2, fy * 0.5 + fx * 0.2, 12.2)
            p2 = (fx, fy, 11.2)
            p3 = (fx * 0.5 + fy * 0.2, fy * 0.5 - fx * 0.2, 12.2)
            BuildingKit.add_quad(mesh, p0, p1, p2, p3, (0, 0), (0, 1), (1, 1), (1, 0), m_frond)

        VertexBaker.bake(mesh)
        return mesh, col

    @staticmethod
    def _gen_oak_tree():
        """10m American Broadleaf Oak Tree with branching canopy."""
        mesh = DFFMesh("veg_oak_tree")
        col = COLBuilder("veg_oak_tree")

        m_trunk = mesh.add_material("concrete_wall")
        m_leaves = mesh.add_material("oak_leaves")

        # Trunk (0 to 4.5m)
        BuildingKit.add_box(mesh, (-0.4, -0.4, 0), (0.4, 0.4, 4.5), m_trunk, m_trunk)
        col.add_box((-0.45, -0.45, 0), (0.45, 0.45, 4.5), COL_MAT_WOOD)

        # Leafy Canopy Box Layers (4m to 10m)
        BuildingKit.add_box(mesh, (-3.5, -3.5, 4.0), (3.5, 3.5, 7.5), m_leaves, m_leaves)
        BuildingKit.add_box(mesh, (-2.5, -2.5, 7.0), (2.5, 2.5, 9.8), m_leaves, m_leaves)

        VertexBaker.bake(mesh)
        return mesh, col
