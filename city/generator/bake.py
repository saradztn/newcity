"""
bake.py - Comprehensive Vertex Lighting Baker for RenderWare Models
Bakes realistic skylight ambient, street canyon height falloff, emissive window/sign surfaces,
and local point light falloff (streetlamps, shop spill) directly into vertex colors.
Eliminates unlit white models in GTA SA / MTA:SA.
"""

import numpy as np


class VertexBaker:
    """Calculates prelit vertex colors for 3D meshes."""

    @staticmethod
    def bake(mesh, lights=None, emissive_materials=None):
        """
        Calculates prelit vertex colors for the mesh.
        mesh: DFFMesh instance
        lights: list of dicts: {'pos': (x,y,z), 'color': (r,g,b), 'radius': float, 'intensity': float}
        emissive_materials: set or list of material indices or texture names that are self-illuminated
        """
        num_verts = len(mesh.vertices)
        if num_verts == 0:
            return

        verts = np.asarray(mesh.vertices, dtype=np.float32)
        norms = np.asarray(mesh.normals, dtype=np.float32)
        if len(norms) != num_verts:
            norms = np.zeros((num_verts, 3), dtype=np.float32)
            norms[:, 2] = 1.0

        # 1. Base Hemispherical Skylight Ambient
        # Upward faces (roofs, streets): cool sky tint
        # Vertical faces (walls): canyon tint
        # Downward faces (undersides, ceilings): ground bounce
        nz = norms[:, 2]
        sky_amb = np.array([145.0, 155.0, 185.0], dtype=np.float32)
        canyon_amb = np.array([110.0, 115.0, 135.0], dtype=np.float32)
        ground_bounce = np.array([75.0, 80.0, 95.0], dtype=np.float32)

        # Interpolate based on normal Z
        up_weight = np.clip(nz, 0.0, 1.0)[:, None]
        down_weight = np.clip(-nz, 0.0, 1.0)[:, None]
        side_weight = np.clip(1.0 - up_weight - down_weight, 0.0, 1.0)

        baked = (up_weight * sky_amb) + (side_weight * canyon_amb) + (down_weight * ground_bounce)

        # 2. Height Canyon Falloff
        z_min = verts[:, 2].min()
        z_max = verts[:, 2].max()
        z_span = max(1.0, z_max - z_min)
        z_norm = np.clip((verts[:, 2] - z_min) / z_span, 0.0, 1.0)[:, None]
        # Deeper street canyons are slightly shadowed from open sky
        height_mult = 0.82 + 0.35 * z_norm
        baked *= height_mult

        # 3. Local Point Lights (Street lamps, neon signs, shop displays)
        if lights:
            for lt in lights:
                lpos = np.array(lt['pos'], dtype=np.float32)
                lcol = np.array(lt['color'], dtype=np.float32)
                lrad = float(lt.get('radius', 18.0))
                lint = float(lt.get('intensity', 1.0))

                delta = lpos[None, :] - verts
                dists = np.linalg.norm(delta, axis=1)
                mask = dists < lrad
                if not np.any(mask):
                    continue

                d_masked = dists[mask]
                delta_masked = delta[mask]
                norms_masked = norms[mask]

                # Normalized light direction
                inv_d = 1.0 / np.maximum(d_masked, 0.001)
                ldir = delta_masked * inv_d[:, None]

                # Lambertian N dot L
                ndotl = np.clip((norms_masked * ldir).sum(axis=1), 0.0, 1.0)

                # Quadratic distance attenuation
                att = ((1.0 - d_masked / lrad) ** 2) * lint

                contrib = lcol[None, :] * (att * ndotl)[:, None]
                baked[mask] += contrib

        # 4. Emissive Material Overrides
        if emissive_materials:
            emissive_set = set(emissive_materials)
            # Find all vertices belonging to emissive triangles
            emissive_vert_indices = set()
            for tri in mesh.triangles:
                v0, v1, v2, mat_id = tri
                mat_name = mesh.materials[mat_id]['texture'] if mat_id < len(mesh.materials) else ""
                if mat_id in emissive_set or mat_name in emissive_set or "emissive" in mat_name or "sign" in mat_name or "neon" in mat_name:
                    emissive_vert_indices.add(v0)
                    emissive_vert_indices.add(v1)
                    emissive_vert_indices.add(v2)

            for vi in emissive_vert_indices:
                baked[vi] = np.array([245.0, 250.0, 255.0], dtype=np.float32)

        # 5. Pack as RGBA uint8
        baked = np.clip(baked, 0.0, 255.0).astype(np.uint8)
        alpha = np.full((num_verts, 1), 255, dtype=np.uint8)
        mesh.colors = np.hstack([baked, alpha]).tolist()
