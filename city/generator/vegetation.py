"""
vegetation.py - Procedural American Vegetation System
Generates diverse botanical models with RenderWare LODs and collisions:
California Fan Palms, American Oaks, Conical Pines, Shrubs, and Grass Tufts.
"""

import numpy as np
from .rw_dff import DFFMesh
from .collision import COLBuilder, COL_MAT_WOOD, COL_MAT_GRASS
from .lod import LODGenerator
from .buildings import add_box_geometry


class VegetationBuilder:
    @staticmethod
    def build_palm_tree(name="veg_palm_tree", height=14.0):
        """California / Mexican Fan Palm with slender trunk and frond crown."""
        mesh = DFFMesh()
        mat_trunk = mesh.add_material("concrete_albedo")
        mat_frond = mesh.add_material("palm_frond_albedo")
        col = COLBuilder(f"col_{name}")

        tr = 0.32
        # Trunk cylinder (8 segments)
        num_trunk_slices = 6
        zs = np.linspace(0.0, height, num_trunk_slices)
        verts = []
        norms = []
        uvs = []
        cols = []

        for j, z in enumerate(zs):
            # Trunk slightly tapers from 0.32m to 0.22m
            t_r = tr * (1.0 - 0.3 * (z / height))
            for i in range(8):
                ang = i * (2.0 * np.pi / 8.0)
                px = float(t_r * np.cos(ang))
                py = float(t_r * np.sin(ang))
                verts.append([px, py, z])
                norms.append([float(np.cos(ang)), float(np.sin(ang)), 0.0])
                uvs.append([float(i / 8.0), float(z / 2.0)])
                cols.append([255, 255, 255, 255])

        triangles = []
        for j in range(num_trunk_slices - 1):
            for i in range(8):
                nxt = (i + 1) % 8
                i00 = j * 8 + i
                i01 = j * 8 + nxt
                i10 = (j + 1) * 8 + i
                i11 = (j + 1) * 8 + nxt
                triangles.append((i00, i10, i11, mat_trunk))
                triangles.append((i00, i11, i01, mat_trunk))

        # Palm crown: 12 radiating frond leaf cards
        num_fronds = 12
        for f_i in range(num_fronds):
            f_ang = f_i * (2.0 * np.pi / num_fronds)
            # Frond projects outward 3.5m and drops slightly
            dx = float(np.cos(f_ang))
            dy = float(np.sin(f_ang))
            tip_x = dx * 3.5
            tip_y = dy * 3.5
            tip_z = height - 0.8

            fb = len(verts)
            # Cross billboard quad for the frond leaf
            verts.extend([
                [0.0, 0.0, height],
                [tip_x, tip_y, tip_z],
                [tip_x + dy * 0.8, tip_y - dx * 0.8, tip_z],
                [dy * 0.4, -dx * 0.4, height + 0.3],
            ])
            norms.extend([[0, 0, 1]] * 4)
            uvs.extend([[0, 0], [1, 0], [1, 1], [0, 1]])
            cols.extend([[255, 255, 255, 255]] * 4)

            triangles.append((fb + 0, fb + 1, fb + 2, mat_frond))
            triangles.append((fb + 0, fb + 2, fb + 3, mat_frond))

        mesh.vertices = verts
        mesh.normals = norms
        mesh.uvs = uvs
        mesh.colors = cols
        mesh.triangles = triangles

        # Collision cylinder on trunk only (fronds have no collision)
        col.add_box((-tr*1.2, -tr*1.2, 0.0), (tr*1.2, tr*1.2, height*0.65), COL_MAT_WOOD)
        lod = LODGenerator.create_bounding_envelope_lod(mesh, "palm_frond_albedo")
        return mesh, col, lod

    @staticmethod
    def build_oak_tree(name="veg_oak_tree", height=9.0):
        """American Oak with sturdy trunk and broad deciduous canopy."""
        mesh = DFFMesh()
        mat_trunk = mesh.add_material("concrete_albedo")
        mat_leaves = mesh.add_material("oak_leaves_albedo")
        col = COLBuilder(f"col_{name}")

        # Trunk box
        tr = 0.45
        trunk_h = height * 0.40
        add_box_geometry(mesh, (-tr, -tr, 0.0), (tr, tr, trunk_h), mat_trunk, (1.0, 0.5))
        col.add_box((-tr*1.2, -tr*1.2, 0.0), (tr*1.2, tr*1.2, trunk_h), COL_MAT_WOOD)

        # Foliage canopy volume (intersecting dome boxes)
        cr = height * 0.45
        add_box_geometry(mesh, (-cr, -cr, trunk_h * 0.8), (cr, cr, height), mat_leaves, (0.5, 0.5))

        lod = LODGenerator.create_bounding_envelope_lod(mesh, "oak_leaves_albedo")
        return mesh, col, lod

    @staticmethod
    def build_pine_tree(name="veg_pine_tree", height=12.0):
        """Conical American Pine / Fir tree."""
        mesh = DFFMesh()
        mat_trunk = mesh.add_material("concrete_albedo")
        mat_leaves = mesh.add_material("oak_leaves_albedo")
        col = COLBuilder(f"col_{name}")

        tr = 0.30
        add_box_geometry(mesh, (-tr, -tr, 0.0), (tr, tr, height * 0.3), mat_trunk, (1.0, 0.5))
        col.add_box((-tr*1.2, -tr*1.2, 0.0), (tr*1.2, tr*1.2, height * 0.3), COL_MAT_WOOD)

        # 3 stacked conical/pyramidal foliage tiers
        tiers = [(0.2, 0.5, 2.5), (0.45, 0.75, 2.0), (0.7, 1.0, 1.4)]
        for t_bot, t_top, t_rad in tiers:
            z0 = height * t_bot
            z1 = height * t_top
            add_box_geometry(mesh, (-t_rad, -t_rad, z0), (t_rad, t_rad, z1), mat_leaves, (0.5, 0.5))

        lod = LODGenerator.create_bounding_envelope_lod(mesh, "oak_leaves_albedo")
        return mesh, col, lod

    @staticmethod
    def build_shrub(name="veg_shrub"):
        """Low manicured decorative bush."""
        mesh = DFFMesh()
        mat_leaves = mesh.add_material("oak_leaves_albedo")
        col = COLBuilder(f"col_{name}")

        add_box_geometry(mesh, (-0.8, -0.8, 0.0), (0.8, 0.8, 1.1), mat_leaves, (1.0, 1.0))
        col.add_box((-0.8, -0.8, 0.0), (0.8, 0.8, 1.1), COL_MAT_GRASS)
        lod = LODGenerator.create_bounding_envelope_lod(mesh, "oak_leaves_albedo")
        return mesh, col, lod
