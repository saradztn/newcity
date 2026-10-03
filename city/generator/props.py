"""
props.py - American Street Furniture, Traffic Infrastructure, and Props
Generates high-detail 3D models and exact COL3 collisions for:
Fire hydrants, USPS mailboxes, utility poles, traffic signs, dumpsters,
benches, bus shelters, parking meters, traffic signals, billboards,
manholes, and highway guardrails.
"""

import numpy as np
from .rw_dff import DFFMesh
from .collision import COLBuilder, COL_MAT_CONCRETE, COL_MAT_METAL, COL_MAT_WOOD, COL_MAT_PAVEMENT
from .lod import LODGenerator
from .buildings import add_box_geometry


class PropsBuilder:
    @staticmethod
    def build_fire_hydrant(name="prop_hydrant"):
        """Classic American cast iron fire hydrant."""
        mesh = DFFMesh()
        mat_red = mesh.add_material("signs_atlas_albedo")
        col = COLBuilder(f"col_{name}")

        # Base flange and barrel
        add_box_geometry(mesh, (-0.2, -0.2, 0.0), (0.2, 0.2, 0.85), mat_red, (1.0, 1.0))
        # Side nozzle caps
        add_box_geometry(mesh, (-0.32, -0.1, 0.45), (0.32, 0.1, 0.65), mat_red, (1.0, 1.0))
        # Top bonnet and operating nut
        add_box_geometry(mesh, (-0.12, -0.12, 0.85), (0.12, 0.12, 1.0), mat_red, (1.0, 1.0))

        col.add_box((-0.25, -0.25, 0.0), (0.25, 0.25, 1.0), COL_MAT_METAL)
        lod = LODGenerator.create_bounding_envelope_lod(mesh, "signs_atlas_albedo")
        return mesh, col, lod

    @staticmethod
    def build_mailbox(name="prop_mailbox"):
        """USPS Blue Collection Mailbox."""
        mesh = DFFMesh()
        mat_metal = mesh.add_material("metal_industrial_albedo")
        col = COLBuilder(f"col_{name}")

        w, d, h = 0.6, 0.6, 1.25
        add_box_geometry(mesh, (-w*0.5, -d*0.5, 0.0), (w*0.5, d*0.5, h), mat_metal, (1.0, 1.0))
        col.add_box((-w*0.5, -d*0.5, 0.0), (w*0.5, d*0.5, h), COL_MAT_METAL)
        lod = LODGenerator.create_bounding_envelope_lod(mesh, "metal_industrial_albedo")
        return mesh, col, lod

    @staticmethod
    def build_utility_pole(name="prop_utility_pole", height=10.0):
        """American wooden utility pole with crossarm and transformer."""
        mesh = DFFMesh()
        mat_wood = mesh.add_material("concrete_albedo")
        mat_metal = mesh.add_material("metal_industrial_albedo")
        col = COLBuilder(f"col_{name}")

        r = 0.18
        # Main vertical pole
        add_box_geometry(mesh, (-r, -r, 0.0), (r, r, height), mat_wood, (0.5, 0.1))
        col.add_box((-r*1.2, -r*1.2, 0.0), (r*1.2, r*1.2, height), COL_MAT_WOOD)

        # Crossarm near top
        arm_w, arm_d, arm_h = 2.4, 0.15, 0.15
        az = height - 0.8
        add_box_geometry(mesh, (-arm_w*0.5, -arm_d*0.5, az), (arm_w*0.5, arm_d*0.5, az + arm_h), mat_wood, (1.0, 1.0))

        # Cylindrical pole transformer
        tr = 0.35
        add_box_geometry(mesh, (0.1, -tr, az - 1.4), (0.1 + tr*2, tr, az - 0.2), mat_metal, (1.0, 1.0))

        lod = LODGenerator.create_bounding_envelope_lod(mesh, "concrete_albedo")
        return mesh, col, lod

    @staticmethod
    def build_traffic_signal(name="prop_traffic_signal", mast_reach=7.5):
        """Mast-arm overhead traffic signal pole with vehicle signal heads."""
        mesh = DFFMesh()
        mat_metal = mesh.add_material("metal_industrial_albedo")
        mat_sign = mesh.add_material("signs_atlas_albedo")
        col = COLBuilder(f"col_{name}")

        # Vertical upright pole (6.5m)
        r = 0.2
        add_box_geometry(mesh, (-r, -r, 0.0), (r, r, 6.5), mat_metal, (0.5, 0.2))
        col.add_box((-r*1.5, -r*1.5, 0.0), (r*1.5, r*1.5, 6.5), COL_MAT_METAL)

        # Horizontal mast arm cantilever extending over traffic lanes
        add_box_geometry(mesh, (0.0, -0.12, 6.1), (mast_reach, 0.12, 6.35), mat_metal, (0.2, 1.0))

        # Signal head 1 (hanging at x=4.0)
        add_box_geometry(mesh, (3.7, -0.2, 5.0), (4.3, 0.2, 6.1), mat_sign, (1.0, 1.0))
        # Signal head 2 (hanging at mast end)
        add_box_geometry(mesh, (mast_reach - 0.8, -0.2, 5.0), (mast_reach - 0.2, 0.2, 6.1), mat_sign, (1.0, 1.0))

        lod = LODGenerator.create_bounding_envelope_lod(mesh, "metal_industrial_albedo")
        return mesh, col, lod

    @staticmethod
    def build_dumpster(name="prop_dumpster"):
        """Green commercial steel dumpster."""
        mesh = DFFMesh()
        mat_metal = mesh.add_material("metal_industrial_albedo")
        col = COLBuilder(f"col_{name}")

        w, d, h = 2.2, 1.4, 1.3
        add_box_geometry(mesh, (-w*0.5, -d*0.5, 0.0), (w*0.5, d*0.5, h), mat_metal, (0.8, 0.8))
        col.add_box((-w*0.5, -d*0.5, 0.0), (w*0.5, d*0.5, h), COL_MAT_METAL)
        lod = LODGenerator.create_bounding_envelope_lod(mesh, "metal_industrial_albedo")
        return mesh, col, lod

    @staticmethod
    def build_street_bench(name="prop_bench"):
        """Park / sidewalk slatted bench."""
        mesh = DFFMesh()
        mat_wood = mesh.add_material("concrete_albedo")
        mat_metal = mesh.add_material("metal_industrial_albedo")
        col = COLBuilder(f"col_{name}")

        # Seat and backrest
        add_box_geometry(mesh, (-1.0, -0.3, 0.45), (1.0, 0.3, 0.52), mat_wood, (1.0, 1.0))
        add_box_geometry(mesh, (-1.0, 0.25, 0.52), (1.0, 0.32, 0.95), mat_wood, (1.0, 1.0))
        # Cast iron legs
        for lx in [-0.85, 0.85]:
            add_box_geometry(mesh, (lx - 0.04, -0.3, 0.0), (lx + 0.04, 0.3, 0.45), mat_metal, (1.0, 1.0))

        col.add_box((-1.0, -0.35, 0.0), (1.0, 0.35, 0.95), COL_MAT_WOOD)
        lod = LODGenerator.create_bounding_envelope_lod(mesh, "concrete_albedo")
        return mesh, col, lod

    @staticmethod
    def build_bus_shelter(name="prop_bus_shelter"):
        """Modern transit glass bus stop shelter."""
        mesh = DFFMesh()
        mat_metal = mesh.add_material("metal_industrial_albedo")
        mat_glass = mesh.add_material("bldg_glass_albedo")
        col = COLBuilder(f"col_{name}")

        w, d, h = 3.6, 1.8, 2.6
        # Rear glass wall
        add_box_geometry(mesh, (-w*0.5, d*0.5 - 0.1, 0.0), (w*0.5, d*0.5, h), mat_glass, (0.5, 0.5))
        # Side glass panel
        add_box_geometry(mesh, (-w*0.5, -d*0.5, 0.0), (-w*0.5 + 0.1, d*0.5, h), mat_glass, (0.5, 0.5))
        # Roof canopy
        add_box_geometry(mesh, (-w*0.55, -d*0.55, h), (w*0.55, d*0.55, h + 0.15), mat_metal, (0.5, 0.5))

        col.add_box((-w*0.5, -d*0.5, 0.0), (w*0.5, d*0.5, h + 0.15), COL_MAT_METAL)
        lod = LODGenerator.create_bounding_envelope_lod(mesh, "metal_industrial_albedo")
        return mesh, col, lod

    @staticmethod
    def build_traffic_sign(name="prop_sign_stop"):
        """American roadside traffic sign mounted on galvanized steel post."""
        mesh = DFFMesh()
        mat_metal = mesh.add_material("metal_industrial_albedo")
        mat_sign = mesh.add_material("signs_atlas_albedo")
        col = COLBuilder(f"col_{name}")

        # Square post
        add_box_geometry(mesh, (-0.03, -0.03, 0.0), (0.03, 0.03, 2.2), mat_metal, (0.1, 0.5))
        # Sign face board
        add_box_geometry(mesh, (-0.38, -0.04, 1.45), (0.38, 0.0, 2.2), mat_sign, (1.0, 1.0))

        col.add_box((-0.4, -0.05, 0.0), (0.4, 0.05, 2.2), COL_MAT_METAL)
        lod = LODGenerator.create_bounding_envelope_lod(mesh, "signs_atlas_albedo")
        return mesh, col, lod

    @staticmethod
    def build_guardrail_segment(name="prop_guardrail", length=12.0):
        """Galvanized steel W-beam highway safety guardrail."""
        mesh = DFFMesh()
        mat_metal = mesh.add_material("metal_industrial_albedo")
        col = COLBuilder(f"col_{name}")

        # Horizontal W-beam rail (height 0.55m to 0.85m)
        add_box_geometry(mesh, (0.0, -0.1, 0.55), (length, 0.0, 0.85), mat_metal, (0.5, 1.0))
        # Support posts every 2.0m
        num_posts = int(length / 2.0) + 1
        for px in np.linspace(0.0, length, num_posts):
            add_box_geometry(mesh, (px - 0.06, -0.22, 0.0), (px + 0.06, -0.1, 0.90), mat_metal, (1.0, 1.0))

        col.add_box((0.0, -0.25, 0.0), (length, 0.05, 0.90), COL_MAT_METAL)
        lod = LODGenerator.create_bounding_envelope_lod(mesh, "metal_industrial_albedo")
        return mesh, col, lod
