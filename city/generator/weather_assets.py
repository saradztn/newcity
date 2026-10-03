"""
weather_assets.py - Atmosphere & Weather Textures Generator
Generates cloud layer coverage textures (cirrus, cumulus, storm overcast),
rain drop streak masks, camera lens rain splash textures, and fog density maps.
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from .dds import save_image_to_dds
from .textures import generate_perlin_noise_2d


class WeatherAssetGenerator:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _save(self, image, base_name, fmt='DXT5'):
        dds_path = os.path.join(self.output_dir, f"{base_name}.dds")
        png_path = os.path.join(self.output_dir, f"{base_name}.png")
        save_image_to_dds(image, dds_path, format_type=fmt, generate_mips=True)
        image.save(png_path)
        return dds_path

    def build_clouds_cumulus(self, width=512, height=512):
        """Puffy cumulus cloud density map."""
        noise1 = generate_perlin_noise_2d(width, height, octaves=4, persistence=0.5, seed=801)
        noise2 = generate_perlin_noise_2d(width, height, octaves=5, persistence=0.6, seed=802)
        cloud_density = np.clip((noise1 * 0.7 + noise2 * 0.3 - 0.35) * 2.2, 0.0, 1.0)

        # White clouds with alpha density
        rgb = np.full((height, width, 3), 255, dtype=np.uint8)
        alpha = (cloud_density * 255.0).astype(np.uint8)
        rgba = np.dstack([rgb, alpha])
        img = Image.fromarray(rgba, mode='RGBA')
        self._save(img, "clouds_cumulus", 'DXT5')

    def build_clouds_storm(self, width=512, height=512):
        """Dense, ominous dark storm clouds."""
        noise1 = generate_perlin_noise_2d(width, height, octaves=5, persistence=0.55, seed=803)
        noise2 = generate_perlin_noise_2d(width, height, octaves=6, persistence=0.6, seed=804)
        storm_density = np.clip((noise1 * 0.6 + noise2 * 0.4 - 0.15) * 1.8, 0.0, 1.0)

        # Dark grey/slate tones ~ (45, 48, 55)
        r = (45 + 25 * noise1).astype(np.uint8)
        g = (48 + 25 * noise1).astype(np.uint8)
        b = (56 + 28 * noise1).astype(np.uint8)
        alpha = (storm_density * 255.0).astype(np.uint8)
        rgba = np.dstack([r, g, b, alpha])
        img = Image.fromarray(rgba, mode='RGBA')
        self._save(img, "clouds_storm", 'DXT5')

    def build_rain_lens_droplets(self, width=512, height=512):
        """Camera lens water droplets for wet weather post-processing."""
        img = Image.new('RGBA', (width, height), (128, 128, 255, 0)) # Normal tangent (0,0,1)
        draw = ImageDraw.Draw(img)
        np.random.seed(805)

        for _ in range(120):
            cx = np.random.randint(20, width - 20)
            cy = np.random.randint(20, height - 20)
            radius = np.random.randint(6, 22)
            # Water droplet dome: ring of refractive normals
            for r in range(radius, 0, -2):
                alpha = int(255 * (r / float(radius)))
                # Tangent normal distortion towards center
                draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(128, 128, 255, alpha))

        # Streak trails (gravity running droplets)
        for _ in range(25):
            sx = np.random.randint(40, width - 40)
            sy = np.random.randint(20, height // 2)
            s_len = np.random.randint(40, 160)
            draw.line([(sx, sy), (sx + np.random.randint(-5, 5), sy + s_len)], fill=(128, 128, 255, 180), width=3)

        self._save(img, "rain_lens_droplets", 'DXT5')

    def generate_all(self):
        print("Generating weather and atmospheric assets...")
        self.build_clouds_cumulus()
        self.build_clouds_storm()
        self.build_rain_lens_droplets()
        print("Weather assets generated successfully.")
