"""
infrastructure.py - Power, Communications, and Street Lighting Infrastructure
Generates street light fixtures (Cobra-head arterial, high-mast highway, acorn downtown),
electrical transmission towers, and cellular communications towers.
"""

import numpy as np
from .rw_dff import DFFMesh
from .collision import COLBuilder, COL_MAT_METAL
from .lod import LODGenerator
from .buildings import add_box_geometry


class InfrastructureBuilder:
    @staticmethod
    def build_cobra_streetlight(name="infra_streetlight_cobra", pole_h=9.0, arm_reach=2.8):
        """American Cobra-Head roadway streetlight pole."""
        mesh = DFFMesh()
        mat_metal = mesh.add_material("metal_industrial_albedo")
        col = COLBuilder(f"col_{name}")

        r = 0.16
        # Vertical tapered pole
        add_box_geometry(mesh, (-r, -r, 0.0), (r, r, pole_h), mat_metal, (0.5, 0.2))
        col.add_box((-r*1.5, -r*1.5, 0.0), (r*1.5, r*1.5, pole_h), COL_MAT_METAL)

        # Curved arching davit arm
        add_box_geometry(mesh, (0.0, -0.08, pole_h - 0.2), (arm_reach, 0.08, pole_h + 0.6), mat_metal, (0.3, 1.0))
        # Cobra luminaire fixture
        add_box_geometry(mesh, (arm_reach - 0.5, -0.2, pole_h + 0.3), (arm_reach + 0.3, 0.2, pole_h + 0.6), mat_metal, (1.0, 1.0))

        lod = LODGenerator.create_bounding_envelope_lod(mesh, "metal_industrial_albedo")
        return mesh, col, lod

    @staticmethod
    def build_power_tower(name="infra_power_tower", height=32.0):
        """High-voltage steel lattice transmission tower."""
        mesh = DFFMesh()
        mat_metal = mesh.add_material("metal_industrial_albedo")
        col = COLBuilder(f"col_{name}")

        # 4 Corner steel lattice legs
        base_w = 5.0
        top_w = 1.4
        leg_r = 0.15

        # 4 legs
        legs = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
        for sx, sy in legs:
            add_box_geometry(
                mesh,
                (sx * base_w * 0.5 - leg_r, sy * base_w * 0.5 - leg_r, 0.0),
                (sx * top_w * 0.5 + leg_r, sy * top_w * 0.5 + leg_r, height),
                mat_metal,
                (0.2, 0.1)
            )

        # 3 Crossarms near top
        arm_spans = [(height - 8.0, 10.0), (height - 5.0, 12.0), (height - 2.0, 8.0)]
        for az, span_w in arm_spans:
            add_box_geometry(mesh, (-span_w*0.5, -0.3, az), (span_w*0.5, 0.3, az + 0.6), mat_metal, (0.2, 0.5))

        col.add_box((-base_w*0.5, -base_w*0.5, 0.0), (base_w*0.5, base_w*0.5, height), COL_MAT_METAL)
        lod = LODGenerator.create_bounding_envelope_lod(mesh, "metal_industrial_albedo")
        return mesh, col, lod
