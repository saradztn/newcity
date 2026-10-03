"""
lighting_assets.py - Photorealistic Lighting Textures Generator
Generates sun disc textures with atmospheric limb darkening, light shaft sampling
dither noise, volumetric street light cones, and color-temperature halos.
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from .dds import save_image_to_dds


class LightingAssetGenerator:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _save(self, image, base_name, fmt='DXT5'):
        dds_path = os.path.join(self.output_dir, f"{base_name}.dds")
        png_path = os.path.join(self.output_dir, f"{base_name}.png")
        save_image_to_dds(image, dds_path, format_type=fmt, generate_mips=True)
        image.save(png_path)
        return dds_path

    def build_sun_disc(self, size=256):
        """Generates realistic sun disc with core limb darkening and Mie corona."""
        arr = np.zeros((size, size, 4), dtype=np.uint8)
        center = (size / 2.0, size / 2.0)
        y, x = np.ogrid[:size, :size]
        dist = np.sqrt((x - center[0]) ** 2 + (y - center[1]) ** 2) / (size / 2.0)

        # Core disc: dist < 0.22
        # Corona: 0.22 <= dist < 1.0
        # Limb darkening formula: I(mu) = 1 - u(1 - mu)
        core_mask = dist < 0.22
        corona_falloff = np.clip(1.0 - ((dist - 0.22) / 0.78), 0.0, 1.0) ** 3.0

        r = np.zeros((size, size), dtype=np.float32)
        g = np.zeros((size, size), dtype=np.float32)
        b = np.zeros((size, size), dtype=np.float32)
        alpha = np.zeros((size, size), dtype=np.float32)

        # Core: pure bright white
        r[core_mask] = 255.0
        g[core_mask] = 255.0
        b[core_mask] = 245.0
        alpha[core_mask] = 255.0

        # Corona: golden-orange Rayleigh/Mie scattering
        corona_mask = ~core_mask
        r[corona_mask] = 255.0 * corona_falloff[corona_mask]
        g[corona_mask] = 210.0 * corona_falloff[corona_mask]
        b[corona_mask] = 130.0 * corona_falloff[corona_mask]
        alpha[corona_mask] = 255.0 * corona_falloff[corona_mask]

        arr[..., 0] = np.clip(r, 0, 255).astype(np.uint8)
        arr[..., 1] = np.clip(g, 0, 255).astype(np.uint8)
        arr[..., 2] = np.clip(b, 0, 255).astype(np.uint8)
        arr[..., 3] = np.clip(alpha, 0, 255).astype(np.uint8)

        img = Image.fromarray(arr, mode='RGBA')
        self._save(img, "sun_disc", 'DXT5')

    def build_godray_dither(self, size=128):
        """Generates high-frequency noise for dithered light shaft integration."""
        np.random.seed(901)
        # Blue noise / uniform jitter in [0..255]
        noise = np.random.randint(0, 256, (size, size), dtype=np.uint8)
        rgba = np.stack([noise, noise, noise, np.full_like(noise, 255)], axis=-1)
        img = Image.fromarray(rgba, mode='RGBA')
        self._save(img, "godray_dither", 'DXT1')

    def build_streetlight_volumetric(self, width=256, height=512):
        """Volumetric light cone expanding downwards from streetlight fixture."""
        arr = np.zeros((height, width, 4), dtype=np.uint8)
        y, x = np.ogrid[:height, :width]
        norm_y = y / float(height)
        norm_x = (x - width / 2.0) / (width / 2.0)

        # Cone expands with Y: radius = 0.05 at top, 0.95 at bottom
        cone_radius = 0.05 + 0.90 * norm_y
        dist_from_cone = np.abs(norm_x) / cone_radius

        # Falloffs: radial across cone + vertical along beam
        radial_falloff = np.clip(1.0 - (dist_from_cone ** 2), 0.0, 1.0)
        vertical_falloff = np.clip(1.0 - (norm_y ** 1.3), 0.0, 1.0)
        intensity = radial_falloff * vertical_falloff

        arr[..., 0] = 255
        arr[..., 1] = 240
        arr[..., 2] = 200
        arr[..., 3] = (intensity * 230.0).astype(np.uint8)

        img = Image.fromarray(arr, mode='RGBA')
        self._save(img, "light_cone_mask", 'DXT5')

    def build_streetlight_halos(self, size=128):
        """Creates light fixture halos for different bulb color temperatures."""
        y, x = np.ogrid[:size, :size]
        center = size / 2.0
        dist = np.sqrt((x - center) ** 2 + (y - center) ** 2) / center
        falloff = np.clip(1.0 - dist, 0.0, 1.0) ** 2.2

        # 1. Warm Sodium Vapor (~2100K) - Orange Amber
        arr_sodium = np.zeros((size, size, 4), dtype=np.uint8)
        arr_sodium[..., 0] = 255
        arr_sodium[..., 1] = 160
        arr_sodium[..., 2] = 40
        arr_sodium[..., 3] = (falloff * 255.0).astype(np.uint8)
        self._save(Image.fromarray(arr_sodium, mode='RGBA'), "halo_sodium", 'DXT5')

        # 2. Modern Cool LED (~5500K) - Crisp Blue-White
        arr_led = np.zeros((size, size, 4), dtype=np.uint8)
        arr_led[..., 0] = 220
        arr_led[..., 1] = 235
        arr_led[..., 2] = 255
        arr_led[..., 3] = (falloff * 255.0).astype(np.uint8)
        self._save(Image.fromarray(arr_led, mode='RGBA'), "halo_led", 'DXT5')

    def generate_all(self):
        print("Generating lighting and sun assets...")
        self.build_sun_disc()
        self.build_godray_dither()
        self.build_streetlight_volumetric()
        self.build_streetlight_halos()
        print("Lighting assets generated successfully.")
