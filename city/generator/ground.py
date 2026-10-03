"""
ground.py - Modular Ground Block Cells, Road Corridors, and Intersections
Constructs seamless ground cells spanning street centerline to centerline:
Asphalt roadways, painted crosswalks, 0.16m raised concrete curbs with chamfered corners,
sidewalk paving slabs, plazas with fountains, urban parks, and exact matching COL3 collisions.
"""

import math
import numpy as np
from .rw_dff import DFFMesh
from .collision import COLBuilder, COL_MAT_PAVEMENT, COL_MAT_CONCRETE, COL_MAT_GRASS
from .bldkit import BuildingKit
from .bake import VertexBaker


class GroundCellFactory:
    """Creates seamless city ground blocks with matching collision meshes."""

    @staticmethod
    def create(cell_type):
        builders = {
            'block_downtown': GroundCellFactory._gen_block_downtown,
            'block_plaza':    GroundCellFactory._gen_block_plaza,
            'block_park':     GroundCellFactory._gen_block_park,
            'block_industrial': GroundCellFactory._gen_block_industrial,
            'road_intersection': GroundCellFactory._gen_road_intersection,
            'road_straight':  GroundCellFactory._gen_road_straight,
        }
        fn = builders.get(cell_type, GroundCellFactory._gen_block_downtown)
        return fn()

    @staticmethod
    def _gen_block_downtown():
        """Standard 80m x 80m Downtown Block: 4 surrounding streets, curbs, sidewalks, and building plot."""
        mesh = DFFMesh("block_downtown")
        col = COLBuilder("block_downtown")

        m_road = mesh.add_material("asphalt_road")
        m_cross = mesh.add_material("crosswalk")
        m_curb = mesh.add_material("curb_stone")
        m_side = mesh.add_material("sidewalk_paver")
        m_plot = mesh.add_material("concrete_wall")

        # Half-extents: 40m x 40m (total 80m x 80m)
        # 1. Road perimeter (40 to 34m from center = 6m road half-width)
        # z = 0.0
        # South road
        BuildingKit.add_quad(mesh, (-40, -40, 0), (40, -40, 0), (40, -34, 0), (-40, -34, 0),
                             (0, 0), (10, 0), (10, 1.5), (0, 1.5), m_road, normal=[0, 0, 1])
        # North road
        BuildingKit.add_quad(mesh, (-40, 34, 0), (40, 34, 0), (40, 40, 0), (-40, 40, 0),
                             (0, 0), (10, 0), (10, 1.5), (0, 1.5), m_road, normal=[0, 0, 1])
        # West road
        BuildingKit.add_quad(mesh, (-40, -34, 0), (-34, -34, 0), (-34, 34, 0), (-40, 34, 0),
                             (0, 0), (1.5, 0), (1.5, 8.5), (0, 8.5), m_road, normal=[0, 0, 1])
        # East road
        BuildingKit.add_quad(mesh, (34, -34, 0), (40, -34, 0), (40, 34, 0), (34, 34, 0),
                             (0, 0), (1.5, 0), (1.5, 8.5), (0, 8.5), m_road, normal=[0, 0, 1])

        col.add_box((-40, -40, -0.5), (40, 40, 0.0), COL_MAT_PAVEMENT)

        # 2. Raised Curb (34m perimeter, 0.16m height)
        curb_h = 0.16
        # South curb
        BuildingKit.add_box(mesh, (-34, -34, 0), (34, -33.6, curb_h), m_curb, m_curb)
        # North curb
        BuildingKit.add_box(mesh, (-34, 33.6, 0), (34, 34, curb_h), m_curb, m_curb)
        # West curb
        BuildingKit.add_box(mesh, (-34, -33.6, 0), (-33.6, 33.6, curb_h), m_curb, m_curb)
        # East curb
        BuildingKit.add_box(mesh, (33.6, -33.6, 0), (34, 33.6, curb_h), m_curb, m_curb)

        # 3. Sidewalk surface (33.6m to 30.0m perimeter, z = curb_h)
        # South sidewalk
        BuildingKit.add_quad(mesh, (-33.6, -33.6, curb_h), (33.6, -33.6, curb_h), (33.6, -30.0, curb_h), (-33.6, -30.0, curb_h),
                             (0, 0), (16, 0), (16, 2), (0, 2), m_side, normal=[0, 0, 1])
        # North sidewalk
        BuildingKit.add_quad(mesh, (-33.6, 30.0, curb_h), (33.6, 30.0, curb_h), (33.6, 33.6, curb_h), (-33.6, 33.6, curb_h),
                             (0, 0), (16, 0), (16, 2), (0, 2), m_side, normal=[0, 0, 1])
        # West sidewalk
        BuildingKit.add_quad(mesh, (-33.6, -30.0, curb_h), (-30.0, -30.0, curb_h), (-30.0, 30.0, curb_h), (-33.6, 30.0, curb_h),
                             (0, 0), (2, 0), (2, 15), (0, 15), m_side, normal=[0, 0, 1])
        # East sidewalk
        BuildingKit.add_quad(mesh, (30.0, -30.0, curb_h), (33.6, -30.0, curb_h), (33.6, 30.0, curb_h), (30.0, 30.0, curb_h),
                             (0, 0), (2, 0), (2, 15), (0, 15), m_side, normal=[0, 0, 1])

        # 4. Central Building Plot (30m x 30m, z = curb_h)
        BuildingKit.add_quad(mesh, (-30, -30, curb_h), (30, -30, curb_h), (30, 30, curb_h), (-30, 30, curb_h),
                             (0, 0), (15, 0), (15, 15), (0, 15), m_plot, normal=[0, 0, 1])

        col.add_box((-34, -34, 0.0), (34, 34, curb_h), COL_MAT_CONCRETE)

        VertexBaker.bake(mesh)
        return mesh, col

    @staticmethod
    def _gen_block_plaza():
        """Public Financial District Plaza: Water fountain pool, trees, paved square."""
        mesh = DFFMesh("block_plaza")
        col = COLBuilder("block_plaza")

        m_road = mesh.add_material("asphalt_road")
        m_curb = mesh.add_material("curb_stone")
        m_side = mesh.add_material("sidewalk_paver")
        m_conc = mesh.add_material("concrete_wall")
        m_water = mesh.add_material("water_normal")

        # Base block road and curb
        curb_h = 0.16
        BuildingKit.add_quad(mesh, (-40, -40, 0), (40, -40, 0), (40, -34, 0), (-40, -34, 0), (0,0), (10,0), (10,1.5), (0,1.5), m_road, normal=[0,0,1])
        BuildingKit.add_quad(mesh, (-40, 34, 0), (40, 34, 0), (40, 40, 0), (-40, 40, 0), (0,0), (10,0), (10,1.5), (0,1.5), m_road, normal=[0,0,1])
        BuildingKit.add_quad(mesh, (-40, -34, 0), (-34, -34, 0), (-34, 34, 0), (-40, 34, 0), (0,0), (1.5,0), (1.5,8.5), (0,8.5), m_road, normal=[0,0,1])
        BuildingKit.add_quad(mesh, (34, -34, 0), (40, -34, 0), (40, 34, 0), (34, 34, 0), (0,0), (1.5,0), (1.5,8.5), (0,8.5), m_road, normal=[0,0,1])

        col.add_box((-40, -40, -0.5), (40, 40, 0.0), COL_MAT_PAVEMENT)

        # Plaza Paved Square (34m x 34m at curb_h)
        BuildingKit.add_quad(mesh, (-34, -34, curb_h), (34, -34, curb_h), (34, 34, curb_h), (-34, 34, curb_h),
                             (0, 0), (16, 0), (16, 16), (0, 16), m_side, normal=[0, 0, 1])
        col.add_box((-34, -34, 0.0), (34, 34, curb_h), COL_MAT_CONCRETE)

        # Central Fountain Basin (Radius 8m, rim height 0.75m)
        num_segs = 16
        r_inner, r_outer = 7.2, 8.4
        for i in range(num_segs):
            a0 = (i / num_segs) * 2 * math.pi
            a1 = ((i + 1) / num_segs) * 2 * math.pi

            # Outer rim segment
            p0 = (r_outer * math.cos(a0), r_outer * math.sin(a0), curb_h)
            p1 = (r_outer * math.cos(a1), r_outer * math.sin(a1), curb_h)
            p2 = (r_outer * math.cos(a1), r_outer * math.sin(a1), curb_h + 0.75)
            p3 = (r_outer * math.cos(a0), r_outer * math.sin(a0), curb_h + 0.75)
            BuildingKit.add_quad(mesh, p0, p1, p2, p3, (0, 0), (1, 0), (1, 1), (0, 1), m_conc)

        # Fountain Water Surface
        BuildingKit.add_quad(mesh, (-7.2, -7.2, curb_h + 0.55), (7.2, -7.2, curb_h + 0.55),
                             (7.2, 7.2, curb_h + 0.55), (-7.2, 7.2, curb_h + 0.55),
                             (0, 0), (2, 0), (2, 2), (0, 2), m_water, normal=[0, 0, 1])
        col.add_box((-8.4, -8.4, curb_h), (8.4, 8.4, curb_h + 0.75), COL_MAT_CONCRETE)

        VertexBaker.bake(mesh)
        return mesh, col

    @staticmethod
    def _gen_block_park():
        """Urban Green Park: Grass lawns, stone pathways, perimeter trees and benches."""
        mesh = DFFMesh("block_park")
        col = COLBuilder("block_park")

        m_road = mesh.add_material("asphalt_road")
        m_curb = mesh.add_material("curb_stone")
        m_side = mesh.add_material("sidewalk_paver")
        m_grass = mesh.add_material("grass_paver")

        curb_h = 0.16
        # Perimeter roads
        BuildingKit.add_quad(mesh, (-40, -40, 0), (40, -40, 0), (40, -34, 0), (-40, -34, 0), (0,0), (10,0), (10,1.5), (0,1.5), m_road, normal=[0,0,1])
        BuildingKit.add_quad(mesh, (-40, 34, 0), (40, 34, 0), (40, 40, 0), (-40, 40, 0), (0,0), (10,0), (10,1.5), (0,1.5), m_road, normal=[0,0,1])
        BuildingKit.add_quad(mesh, (-40, -34, 0), (-34, -34, 0), (-34, 34, 0), (-40, 34, 0), (0,0), (1.5,0), (1.5,8.5), (0,8.5), m_road, normal=[0,0,1])
        BuildingKit.add_quad(mesh, (34, -34, 0), (40, -34, 0), (40, 34, 0), (34, 34, 0), (0,0), (1.5,0), (1.5,8.5), (0,8.5), m_road, normal=[0,0,1])
        col.add_box((-40, -40, -0.5), (40, 40, 0.0), COL_MAT_PAVEMENT)

        # Sidewalk border
        BuildingKit.add_quad(mesh, (-34, -34, curb_h), (34, -34, curb_h), (34, -30, curb_h), (-34, -30, curb_h), (0,0), (16,0), (16,2), (0,2), m_side, normal=[0,0,1])
        BuildingKit.add_quad(mesh, (-34, 30, curb_h), (34, 30, curb_h), (34, 34, curb_h), (-34, 34, curb_h), (0,0), (16,0), (16,2), (0,2), m_side, normal=[0,0,1])
        BuildingKit.add_quad(mesh, (-34, -30, curb_h), (-30, -30, curb_h), (-30, 30, curb_h), (-34, 30, curb_h), (0,0), (2,0), (2,15), (0,15), m_side, normal=[0,0,1])
        BuildingKit.add_quad(mesh, (30, -30, curb_h), (34, -30, curb_h), (34, 30, curb_h), (30, 30, curb_h), (0,0), (2,0), (2,15), (0,15), m_side, normal=[0,0,1])

        # Central Grass Lawn (30m x 30m)
        BuildingKit.add_quad(mesh, (-30, -30, curb_h), (30, -30, curb_h), (30, 30, curb_h), (-30, 30, curb_h),
                             (0, 0), (12, 0), (12, 12), (0, 12), m_grass, normal=[0, 0, 1])
        # Cross pathway through park
        BuildingKit.add_quad(mesh, (-30, -2.5, curb_h + 0.01), (30, -2.5, curb_h + 0.01),
                             (30, 2.5, curb_h + 0.01), (-30, 2.5, curb_h + 0.01),
                             (0, 0), (15, 0), (15, 1.2), (0, 1.2), m_side, normal=[0, 0, 1])
        BuildingKit.add_quad(mesh, (-2.5, -30, curb_h + 0.01), (2.5, -30, curb_h + 0.01),
                             (2.5, 30, curb_h + 0.01), (-2.5, 30, curb_h + 0.01),
                             (0, 0), (1.2, 0), (1.2, 15), (0, 15), m_side, normal=[0, 0, 1])

        col.add_box((-34, -34, 0.0), (34, 34, curb_h), COL_MAT_GRASS)

        VertexBaker.bake(mesh)
        return mesh, col

    @staticmethod
    def _gen_block_industrial():
        """Industrial block with concrete apron and heavy asphalt logistics lanes."""
        mesh = DFFMesh("block_industrial")
        col = COLBuilder("block_industrial")

        m_road = mesh.add_material("asphalt_road")
        m_conc = mesh.add_material("concrete_wall")

        # Full industrial apron slab
        BuildingKit.add_quad(mesh, (-40, -40, 0), (40, -40, 0), (40, 40, 0), (-40, 40, 0),
                             (0, 0), (16, 0), (16, 16), (0, 16), m_conc, normal=[0, 0, 1])
        col.add_box((-40, -40, -0.5), (40, 40, 0.0), COL_MAT_CONCRETE)

        VertexBaker.bake(mesh)
        return mesh, col

    @staticmethod
    def _gen_road_intersection():
        """4-Way Signalized Road Intersection with Crosswalks and Stop Bars."""
        mesh = DFFMesh("road_intersection")
        col = COLBuilder("road_intersection")

        m_road = mesh.add_material("asphalt_road")
        m_cross = mesh.add_material("crosswalk")
        m_curb = mesh.add_material("curb_stone")
        m_side = mesh.add_material("sidewalk_paver")

        # 40m x 40m intersection box
        # Central asphalt intersection
        BuildingKit.add_quad(mesh, (-16, -16, 0), (16, -16, 0), (16, 16, 0), (-16, 16, 0),
                             (0, 0), (4, 0), (4, 4), (0, 4), m_road, normal=[0, 0, 1])

        # 4 Crosswalks on North, South, East, West approaches
        BuildingKit.add_quad(mesh, (-16, -20, 0), (16, -20, 0), (16, -16, 0), (-16, -16, 0), (0, 0), (4, 0), (4, 1), (0, 1), m_cross, normal=[0, 0, 1])
        BuildingKit.add_quad(mesh, (-16, 16, 0), (16, 16, 0), (16, 20, 0), (-16, 20, 0), (0, 0), (4, 0), (4, 1), (0, 1), m_cross, normal=[0, 0, 1])
        BuildingKit.add_quad(mesh, (-20, -16, 0), (-16, -16, 0), (-16, 16, 0), (-20, 16, 0), (0, 0), (1, 0), (1, 4), (0, 4), m_cross, normal=[0, 0, 1])
        BuildingKit.add_quad(mesh, (16, -16, 0), (20, -16, 0), (20, 16, 0), (16, 16, 0), (0, 0), (1, 0), (1, 4), (0, 4), m_cross, normal=[0, 0, 1])

        # 4 Corner Sidewalk quadrants (curb_h = 0.16)
        curb_h = 0.16
        corners = [(-20, -20, -16, -16), (16, -20, 20, -16), (-20, 16, -16, 20), (16, 16, 20, 20)]
        for x0, y0, x1, y1 in corners:
            BuildingKit.add_box(mesh, (x0, y0, 0), (x1, y1, curb_h), m_side, m_side)

        col.add_box((-20, -20, -0.5), (20, 20, 0.0), COL_MAT_PAVEMENT)
        VertexBaker.bake(mesh)
        return mesh, col

    @staticmethod
    def _gen_road_straight():
        """80m Straight 4-Lane Avenue Segment with Sidewalks and Curbs."""
        mesh = DFFMesh("road_straight")
        col = COLBuilder("road_straight")

        m_road = mesh.add_material("asphalt_road")
        m_curb = mesh.add_material("curb_stone")
        m_side = mesh.add_material("sidewalk_paver")

        curb_h = 0.16
        # Road asphalt (24m wide x 80m long)
        BuildingKit.add_quad(mesh, (-12, -40, 0), (12, -40, 0), (12, 40, 0), (-12, 40, 0),
                             (0, 0), (3, 0), (3, 10), (0, 10), m_road, normal=[0, 0, 1])
        col.add_box((-12, -40, -0.5), (12, 40, 0.0), COL_MAT_PAVEMENT)

        # West Sidewalk & Curb (4m wide)
        BuildingKit.add_box(mesh, (-16, -40, 0), (-12, 40, curb_h), m_side, m_side)
        col.add_box((-16, -40, 0), (-12, 40, curb_h), COL_MAT_CONCRETE)

        # East Sidewalk & Curb (4m wide)
        BuildingKit.add_box(mesh, (12, -40, 0), (16, 40, curb_h), m_side, m_side)
        col.add_box((12, -40, 0), (16, 40, curb_h), COL_MAT_CONCRETE)

        VertexBaker.bake(mesh)
        return mesh, col
