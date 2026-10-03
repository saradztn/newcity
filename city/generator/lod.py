"""
lod.py - Simplified Level-of-Detail (LOD) Mesh Generator
Constructs lightweight bounding envelope meshes for long-distance rendering.
Ensures zero pop-in while keeping GPU vertex processing minimal.
"""

import numpy as np
from .rw_dff import DFFMesh
from .bldkit import BuildingKit
from .bake import VertexBaker


def generate_lod_mesh(base_mesh, lod_texture_name="concrete_wall"):
    """
    Creates an optimized low-polygon proxy envelope matching the bounding box
    of the high-detail model.
    """
    verts = np.asarray(base_mesh.vertices, dtype=np.float32)
    lod_mesh = DFFMesh(name=f"{base_mesh.name}_lod")

    if len(verts) == 0:
        min_pt = (-1.0, -1.0, 0.0)
        max_pt = (1.0, 1.0, 2.0)
    else:
        min_pt = verts.min(axis=0)
        max_pt = verts.max(axis=0)

    # Use first material texture from base mesh if available, else default
    chosen_tex = lod_texture_name
    if len(base_mesh.materials) > 0 and base_mesh.materials[0]['texture']:
        chosen_tex = base_mesh.materials[0]['texture']

    mat_id = lod_mesh.add_material(chosen_tex)
    BuildingKit.add_box(lod_mesh, min_pt, max_pt, mat_id, mat_id)
    VertexBaker.bake(lod_mesh)

    return lod_mesh
