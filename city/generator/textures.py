"""
textures.py - Photorealistic Procedural Texture Synthesizer & DDS Exporter
Generates multi-layer PBR textures: Albedo, Normal maps (Sobel), Specular/Roughness,
Emissive masks, Puddle maps, and micro-asphalt variation (tire wear, oil, cracks, patches).
Exports to compressed DDS (BC1/BC3) with full mipmap chains.
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from .dds import save_image_to_dds


def generate_sobel_normal_map(height_array, strength=2.0):
    """
    Computes a tangent-space normal map (RGB) from a 2D float height map [0..1]
    using Sobel gradient convolution.
    """
    h, w = height_array.shape
    # Sobel kernels
    # dX: [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
    # dY: [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]
    padded = np.pad(height_array, 1, mode='wrap')

    dx = (
        -1.0 * padded[:-2, :-2] + 1.0 * padded[:-2, 2:] +
        -2.0 * padded[1:-1, :-2] + 2.0 * padded[1:-1, 2:] +
        -1.0 * padded[2:, :-2] + 1.0 * padded[2:, 2:]
    ) * (strength / 8.0)

    dy = (
        -1.0 * padded[:-2, :-2] - 2.0 * padded[:-2, 1:-1] - 1.0 * padded[:-2, 2:] +
         1.0 * padded[2:, :-2] + 2.0 * padded[2:, 1:-1] + 1.0 * padded[2:, 2:]
    ) * (strength / 8.0)

    # Tangent-space normal vector: (-dx, -dy, 1.0) normalized
    norm = np.sqrt(dx * dx + dy * dy + 1.0)
    nx = -dx / norm
    ny = -dy / norm
    nz = 1.0 / norm

    # Map from [-1, 1] to [0, 255]
    r = ((nx * 0.5 + 0.5) * 255.0).astype(np.uint8)
    g = ((ny * 0.5 + 0.5) * 255.0).astype(np.uint8)
    b = ((nz * 0.5 + 0.5) * 255.0).astype(np.uint8)

    return np.stack([r, g, b, np.full_like(r, 255)], axis=-1)


def generate_perlin_noise_2d(width, height, octaves=4, persistence=0.5, seed=42):
    """Generates multi-octave coherent gradient noise."""
    np.random.seed(seed)
    noise = np.zeros((height, width), dtype=np.float32)
    freq = 1.0
    amp = 1.0
    total_amp = 0.0

    for octv in range(octaves):
        grid_w = max(2, int(freq * 4))
        grid_h = max(2, int(freq * 4))
        # Random grid
        rand_grid = np.random.rand(grid_h, grid_w).astype(np.float32)
        # Rescale with PIL
        layer = Image.fromarray((rand_grid * 255.0).astype(np.uint8)).resize(
            (width, height), Image.Resampling.BICUBIC
        )
        layer_arr = np.array(layer, dtype=np.float32) / 255.0
        noise += layer_arr * amp
        total_amp += amp
        amp *= persistence
        freq *= 2.0

    return noise / total_amp


class TextureSynthesizer:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _save_dds_and_png(self, image, base_name, fmt='DXT1'):
        dds_path = os.path.join(self.output_dir, f"{base_name}.dds")
        png_path = os.path.join(self.output_dir, f"{base_name}.png")
        save_image_to_dds(image, dds_path, format_type=fmt, generate_mips=True)
        image.save(png_path)
        return dds_path

    # =========================================================================
    # 1. Asphalt & Road Textures
    # =========================================================================
    def build_road_asphalt(self, width=512, height=512):
        """
        Creates photorealistic asphalt with micro-aggregate variation,
        tire wear tracks, subtle oil drops, cracks, and patch repairs.
        """
        # 1. Base aggregate noise
        noise_fine = generate_perlin_noise_2d(width, height, octaves=5, persistence=0.55, seed=101)
        noise_coarse = generate_perlin_noise_2d(width, height, octaves=3, persistence=0.5, seed=102)

        # Base asphalt color ~ (56, 58, 62)
        base_val = 56.0 + 20.0 * (noise_fine - 0.5) + 12.0 * (noise_coarse - 0.5)
        asphalt_rgb = np.zeros((height, width, 3), dtype=np.float32)
        asphalt_rgb[..., 0] = base_val * 0.95  # R
        asphalt_rgb[..., 1] = base_val * 0.98  # G
        asphalt_rgb[..., 2] = base_val * 1.02  # B (slight cool tint)

        # 2. Tire wear tracks (along Y axis, standard 2-lane layout)
        # Left wheel tracks around x=0.22 and 0.38, right lane around x=0.62 and 0.78
        x_coords = np.linspace(0, 1, width)[None, :]
        wheel_track_left1 = np.exp(-((x_coords - 0.22) ** 2) / (2 * 0.04 ** 2))
        wheel_track_left2 = np.exp(-((x_coords - 0.38) ** 2) / (2 * 0.04 ** 2))
        wheel_track_right1 = np.exp(-((x_coords - 0.62) ** 2) / (2 * 0.04 ** 2))
        wheel_track_right2 = np.exp(-((x_coords - 0.78) ** 2) / (2 * 0.04 ** 2))
        tire_wear = (wheel_track_left1 + wheel_track_left2 + wheel_track_right1 + wheel_track_right2) * 0.35

        # Tire wear polishes and slightly darkens asphalt
        asphalt_rgb *= (1.0 - tire_wear[:, :, None] * 0.25)

        # 3. Centerline oil drip (along lane centers x=0.30 and x=0.70)
        oil1 = np.exp(-((x_coords - 0.30) ** 2) / (2 * 0.025 ** 2))
        oil2 = np.exp(-((x_coords - 0.70) ** 2) / (2 * 0.025 ** 2))
        oil_noise = generate_perlin_noise_2d(width, height, octaves=4, persistence=0.6, seed=103)
        oil_drops = (oil1 + oil2) * (oil_noise > 0.45) * 0.2
        asphalt_rgb *= (1.0 - oil_drops[:, :, None])

        # 4. Asphalt cracks (ridge noise threshold)
        crack_noise = generate_perlin_noise_2d(width, height, octaves=6, persistence=0.65, seed=104)
        cracks = np.abs(crack_noise - 0.5) < 0.015
        asphalt_rgb[cracks] *= 0.45

        # 5. Repaired patches (darker tar rectangular patch)
        patch_mask = np.zeros((height, width), dtype=bool)
        patch_mask[int(height * 0.6):int(height * 0.75), int(width * 0.15):int(width * 0.42)] = True
        # Distort patch edges with noise
        patch_mask &= (noise_fine > 0.3)
        asphalt_rgb[patch_mask] = asphalt_rgb[patch_mask] * 0.65 + np.array([25, 26, 28], dtype=np.float32) * 0.35

        # 6. Road markings
        # Center double yellow line (x around 0.49 and 0.51)
        yellow_line1 = (np.abs(x_coords - 0.49) < 0.007)
        yellow_line2 = (np.abs(x_coords - 0.51) < 0.007)
        # Weathered line edges via fine noise
        yellow_lines = (yellow_line1 | yellow_line2) & (noise_fine > 0.2)
        asphalt_rgb[yellow_lines] = np.array([230, 185, 35], dtype=np.float32)

        # White solid edge lines (x near 0.05 and 0.95)
        edge_white = ((np.abs(x_coords - 0.05) < 0.008) | (np.abs(x_coords - 0.95) < 0.008)) & (noise_fine > 0.2)
        asphalt_rgb[edge_white] = np.array([240, 240, 235], dtype=np.float32)

        # Clamp RGB
        asphalt_rgb = np.clip(asphalt_rgb, 0, 255).astype(np.uint8)
        img_albedo = Image.fromarray(asphalt_rgb, mode='RGB').convert('RGBA')

        # 7. Normal map
        height_map = (noise_fine * 0.6 + noise_coarse * 0.4).astype(np.float32)
        height_map[cracks] -= 0.35
        height_map[patch_mask] += 0.1
        normal_arr = generate_sobel_normal_map(height_map, strength=2.2)
        img_normal = Image.fromarray(normal_arr, mode='RGBA')

        # 8. Puddle Mask (water pools in depressions)
        puddle_noise = generate_perlin_noise_2d(width, height, octaves=3, persistence=0.5, seed=105)
        # Wheel tracks and depressions collect puddles
        puddle_map = np.clip((puddle_noise - 0.42) * 2.5 + tire_wear * 0.4, 0.0, 1.0)
        puddle_arr = (puddle_map * 255.0).astype(np.uint8)
        img_puddle = Image.fromarray(puddle_arr, mode='L').convert('RGBA')

        # 9. Roughness & Specular map
        # Base roughness 0.85, tire tracks lower to 0.65, cracks higher 0.95
        rough_arr = np.full((height, width), 215, dtype=np.uint8)
        rough_arr = np.clip(rough_arr - (tire_wear * 50.0), 100, 255).astype(np.uint8)
        img_roughness = Image.fromarray(rough_arr, mode='L').convert('RGBA')

        self._save_dds_and_png(img_albedo, "asphalt_albedo", 'DXT1')
        self._save_dds_and_png(img_normal, "asphalt_normal", 'DXT1')
        self._save_dds_and_png(img_puddle, "asphalt_puddle", 'DXT1')
        self._save_dds_and_png(img_roughness, "asphalt_roughness", 'DXT1')

    # =========================================================================
    # 2. Highway Asphalt (Multi-Lane with White Dashes)
    # =========================================================================
    def build_highway_asphalt(self, width=512, height=512):
        noise_fine = generate_perlin_noise_2d(width, height, octaves=5, persistence=0.55, seed=201)
        base_val = 52.0 + 18.0 * (noise_fine - 0.5)
        hw_rgb = np.zeros((height, width, 3), dtype=np.float32)
        hw_rgb[..., 0] = base_val * 0.95
        hw_rgb[..., 1] = base_val * 0.98
        hw_rgb[..., 2] = base_val * 1.02

        # White dashed lane dividers (at x=0.33 and x=0.66)
        x_coords = np.linspace(0, 1, width)[None, :]
        y_coords = np.linspace(0, 1, height)[:, None]

        # Dashes: repeat along Y
        dash_pattern = ((y_coords * 8.0) % 1.0) < 0.55
        dash_left = (np.abs(x_coords - 0.33) < 0.007) & dash_pattern
        dash_right = (np.abs(x_coords - 0.66) < 0.007) & dash_pattern

        dashes = (dash_left | dash_right) & (noise_fine > 0.15)
        hw_rgb[dashes] = np.array([242, 242, 238], dtype=np.float32)

        # Yellow left median line (x=0.03) and white right shoulder (x=0.97)
        hw_rgb[(np.abs(x_coords - 0.03) < 0.007) & (noise_fine > 0.15)] = np.array([230, 185, 30], dtype=np.float32)
        hw_rgb[(np.abs(x_coords - 0.97) < 0.007) & (noise_fine > 0.15)] = np.array([240, 240, 235], dtype=np.float32)

        hw_rgb = np.clip(hw_rgb, 0, 255).astype(np.uint8)
        img_albedo = Image.fromarray(hw_rgb, mode='RGB').convert('RGBA')

        normal_arr = generate_sobel_normal_map(noise_fine, strength=2.0)
        img_normal = Image.fromarray(normal_arr, mode='RGBA')

        self._save_dds_and_png(img_albedo, "highway_albedo", 'DXT1')
        self._save_dds_and_png(img_normal, "highway_normal", 'DXT1')

    # =========================================================================
    # 3. Sidewalk & Concrete Textures
    # =========================================================================
    def build_concrete_and_sidewalk(self, width=512, height=512):
        # Sidewalk slab grid: seams every 128 pixels (4x4 slabs)
        noise = generate_perlin_noise_2d(width, height, octaves=4, persistence=0.5, seed=301)
        base_val = 188.0 + 22.0 * (noise - 0.5)

        sw_rgb = np.zeros((height, width, 3), dtype=np.float32)
        sw_rgb[..., 0] = base_val * 1.01
        sw_rgb[..., 1] = base_val * 0.99
        sw_rgb[..., 2] = base_val * 0.96  # warm concrete tone

        # Slab expansion joints (seams)
        grid_step = 128
        seam_mask = np.zeros((height, width), dtype=bool)
        for i in range(0, width, grid_step):
            seam_mask[:, max(0, i-1):min(width, i+2)] = True
        for j in range(0, height, grid_step):
            seam_mask[max(0, j-1):min(height, j+2), :] = True

        # Seams are darker with dirt
        sw_rgb[seam_mask] *= 0.55

        sw_rgb = np.clip(sw_rgb, 0, 255).astype(np.uint8)
        img_sw = Image.fromarray(sw_rgb, mode='RGB').convert('RGBA')

        # Normal map with engraved seams
        height_map = noise.astype(np.float32)
        height_map[seam_mask] -= 0.45
        normal_arr = generate_sobel_normal_map(height_map, strength=2.5)
        img_normal = Image.fromarray(normal_arr, mode='RGBA')

        self._save_dds_and_png(img_sw, "sidewalk_albedo", 'DXT1')
        self._save_dds_and_png(img_normal, "sidewalk_normal", 'DXT1')

        # Structural Concrete (plain barrier/pier concrete)
        conc_noise = generate_perlin_noise_2d(width, height, octaves=4, persistence=0.45, seed=302)
        conc_val = 175.0 + 25.0 * (conc_noise - 0.5)
        conc_rgb = np.stack([conc_val * 1.0, conc_val * 0.99, conc_val * 0.98], axis=-1)
        conc_rgb = np.clip(conc_rgb, 0, 255).astype(np.uint8)
        img_conc = Image.fromarray(conc_rgb, mode='RGB').convert('RGBA')
        img_conc_norm = Image.fromarray(generate_sobel_normal_map(conc_noise, strength=1.8), mode='RGBA')

        self._save_dds_and_png(img_conc, "concrete_albedo", 'DXT1')
        self._save_dds_and_png(img_conc_norm, "concrete_normal", 'DXT1')

    # =========================================================================
    # 4. Building Facades (Modern Glass, Brick, Commercial, Residential)
    # =========================================================================
    def build_facade_textures(self, width=512, height=512):
        # A. Modern Glass Curtain Wall Tower
        img_glass = Image.new('RGBA', (width, height), (35, 55, 75, 255))
        draw_g = ImageDraw.Draw(img_glass)
        emissive_glass = Image.new('L', (width, height), 0)
        draw_em = ImageDraw.Draw(emissive_glass)

        # Window grid: 8 floors, 8 bays
        dx = width // 8
        dy = height // 8
        np.random.seed(401)

        for fy in range(8):
            for fx in range(8):
                x0 = fx * dx + 4
                y0 = fy * dy + 4
                x1 = (fx + 1) * dx - 4
                y1 = (fy + 1) * dy - 4

                # Window glass pane tint
                glass_tint = (40 + np.random.randint(0, 20), 65 + np.random.randint(0, 25), 90 + np.random.randint(0, 30), 255)
                draw_g.rectangle([x0, y0, x1, y1], fill=glass_tint, outline=(140, 145, 150, 255), width=2)

                # Random window night lighting: 40% on, warm or cool
                if np.random.rand() < 0.40:
                    brightness = np.random.randint(160, 255)
                    draw_em.rectangle([x0 + 2, y0 + 2, x1 - 2, y1 - 2], fill=brightness)

        self._save_dds_and_png(img_glass, "bldg_glass_albedo", 'DXT1')
        self._save_dds_and_png(emissive_glass.convert('RGBA'), "bldg_glass_emissive", 'DXT1')

        # B. Red Architectural Brick Facade
        brick_img = Image.new('RGBA', (width, height), (70, 68, 65, 255)) # Mortar background
        draw_b = ImageDraw.Draw(brick_img)
        brick_h = 16
        brick_w = 40
        np.random.seed(402)

        for row, y in enumerate(range(0, height, brick_h)):
            offset = (brick_w // 2) if (row % 2 == 1) else 0
            for x in range(-brick_w, width + brick_w, brick_w):
                bx0 = x + offset + 1
                by0 = y + 1
                bx1 = bx0 + brick_w - 3
                by1 = by0 + brick_h - 3
                shade = np.random.randint(-15, 15)
                r = int(np.clip(152 + shade, 0, 255))
                g = int(np.clip(72 + shade * 0.5, 0, 255))
                b = int(np.clip(58 + shade * 0.4, 0, 255))
                draw_b.rectangle([bx0, by0, bx1, by1], fill=(r, g, b, 255))

        # Add windows into brick facade
        win_w = 48
        win_h = 72
        emissive_brick = Image.new('L', (width, height), 0)
        draw_emb = ImageDraw.Draw(emissive_brick)

        for wy in range(40, height - 60, 110):
            for wx in range(30, width - 40, 95):
                draw_b.rectangle([wx, wy, wx + win_w, wy + win_h], fill=(45, 50, 60, 255), outline=(210, 205, 195, 255), width=3)
                if np.random.rand() < 0.45:
                    draw_emb.rectangle([wx + 4, wy + 4, wx + win_w - 4, wy + win_h - 4], fill=np.random.randint(180, 255))

        self._save_dds_and_png(brick_img, "bldg_brick_albedo", 'DXT1')
        self._save_dds_and_png(emissive_brick.convert('RGBA'), "bldg_brick_emissive", 'DXT1')

        # C. Modern Concrete / Stucco Facade
        stucco_noise = generate_perlin_noise_2d(width, height, octaves=4, persistence=0.5, seed=403)
        stucco_val = 205.0 + 20.0 * (stucco_noise - 0.5)
        stucco_rgb = np.stack([stucco_val * 1.0, stucco_val * 0.99, stucco_val * 0.97], axis=-1)
        stucco_rgb = np.clip(stucco_rgb, 0, 255).astype(np.uint8)
        img_stucco = Image.fromarray(stucco_rgb, mode='RGB').convert('RGBA')
        draw_s = ImageDraw.Draw(img_stucco)

        for wy in range(30, height - 50, 90):
            for wx in range(25, width - 35, 80):
                draw_s.rectangle([wx, wy, wx + 50, wy + 60], fill=(50, 65, 80, 255), outline=(60, 60, 65, 255), width=2)

        self._save_dds_and_png(img_stucco, "bldg_facade_modern", 'DXT1')

    # =========================================================================
    # 5. Roof, Metal, and Industrial Textures
    # =========================================================================
    def build_roof_and_metal(self, width=512, height=512):
        # Roof gravel
        noise = generate_perlin_noise_2d(width, height, octaves=5, persistence=0.6, seed=501)
        roof_val = 72.0 + 24.0 * (noise - 0.5)
        roof_rgb = np.stack([roof_val * 1.0, roof_val * 0.98, roof_val * 0.95], axis=-1)
        roof_rgb = np.clip(roof_rgb, 0, 255).astype(np.uint8)
        img_roof = Image.fromarray(roof_rgb, mode='RGB').convert('RGBA')

        normal_roof = generate_sobel_normal_map(noise, strength=2.4)
        img_roof_norm = Image.fromarray(normal_roof, mode='RGBA')

        self._save_dds_and_png(img_roof, "roof_gravel_albedo", 'DXT1')
        self._save_dds_and_png(img_roof_norm, "roof_gravel_normal", 'DXT1')

        # Corrugated Industrial Metal
        x_coords = np.linspace(0, 1, width)[None, :]
        sine_waves = (np.sin(x_coords * np.pi * 32.0) * 0.5 + 0.5).astype(np.float32)
        metal_noise = generate_perlin_noise_2d(width, height, octaves=3, persistence=0.4, seed=502)
        metal_val = 140.0 + 35.0 * sine_waves + 15.0 * (metal_noise - 0.5)
        metal_rgb = np.stack([metal_val * 0.98, metal_val * 1.0, metal_val * 1.02], axis=-1)
        metal_rgb = np.clip(metal_rgb, 0, 255).astype(np.uint8)
        img_metal = Image.fromarray(metal_rgb, mode='RGB').convert('RGBA')

        self._save_dds_and_png(img_metal, "metal_industrial_albedo", 'DXT1')

    # =========================================================================
    # 6. Vegetation & Landscape (Grass, Palm, Leaves)
    # =========================================================================
    def build_nature_textures(self, width=512, height=512):
        # Landscape Grass
        noise = generate_perlin_noise_2d(width, height, octaves=5, persistence=0.55, seed=601)
        g_val = 65.0 + 25.0 * (noise - 0.5)
        grass_rgb = np.zeros((height, width, 3), dtype=np.float32)
        grass_rgb[..., 0] = g_val * 0.65  # R
        grass_rgb[..., 1] = g_val * 1.15  # G lush green
        grass_rgb[..., 2] = g_val * 0.45  # B
        grass_rgb = np.clip(grass_rgb, 0, 255).astype(np.uint8)
        img_grass = Image.fromarray(grass_rgb, mode='RGB').convert('RGBA')

        norm_grass = generate_sobel_normal_map(noise, strength=2.6)
        img_grass_norm = Image.fromarray(norm_grass, mode='RGBA')

        self._save_dds_and_png(img_grass, "grass_albedo", 'DXT1')
        self._save_dds_and_png(img_grass_norm, "grass_normal", 'DXT1')

        # Palm Frond Billboard with alpha transparency
        img_palm = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw_p = ImageDraw.Draw(img_palm)
        # Draw central spine
        spine_color = (135, 150, 70, 255)
        draw_p.line([(width // 2, height - 20), (width // 2, 40)], fill=spine_color, width=8)
        # Draw leafy fronds
        np.random.seed(602)
        for y in range(50, height - 30, 6):
            frond_len = int(np.sin((y - 40) / float(height - 60) * np.pi) * (width * 0.42))
            tilt = int((y - height // 2) * 0.15)
            leaf_color = (int(50 + np.random.randint(0, 30)), int(115 + np.random.randint(0, 35)), 40, 255)
            # Left leaf
            draw_p.line([(width // 2, y), (width // 2 - frond_len, y + tilt + 15)], fill=leaf_color, width=4)
            # Right leaf
            draw_p.line([(width // 2, y), (width // 2 + frond_len, y + tilt + 15)], fill=leaf_color, width=4)

        self._save_dds_and_png(img_palm, "palm_frond_albedo", 'DXT5')

        # Oak / Deciduous Foliage Cluster
        img_oak = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw_o = ImageDraw.Draw(img_oak)
        np.random.seed(603)
        center = (width // 2, height // 2)
        for _ in range(1200):
            rad = np.random.rand() ** 0.5 * (width * 0.42)
            angle = np.random.rand() * 2 * np.pi
            px = int(center[0] + rad * np.cos(angle))
            py = int(center[1] + rad * np.sin(angle))
            leaf_sz = np.random.randint(8, 20)
            c = (int(45 + np.random.randint(0, 25)), int(105 + np.random.randint(0, 35)), int(35 + np.random.randint(0, 20)), 240)
            draw_o.ellipse([px - leaf_sz, py - leaf_sz, px + leaf_sz, py + leaf_sz], fill=c)

        self._save_dds_and_png(img_oak, "oak_leaves_albedo", 'DXT5')

    # =========================================================================
    # 7. American Signage & Props Textures
    # =========================================================================
    def build_american_signage(self, width=512, height=512):
        # Atlas of American traffic signs
        img_signs = Image.new('RGBA', (width, height), (30, 30, 30, 255))
        draw = ImageDraw.Draw(img_signs)

        # Quadrant 1: Red Octagonal STOP sign
        cx, cy, r = 128, 128, 90
        pts = [
            (int(cx + r * np.cos(a)), int(cy + r * np.sin(a)))
            for a in np.linspace(np.pi / 8, 2 * np.pi + np.pi / 8, 8, endpoint=False)
        ]
        draw.polygon(pts, fill=(210, 30, 30, 255), outline=(255, 255, 255, 255))
        # Inner text line
        draw.text((cx - 40, cy - 14), "STOP", fill=(255, 255, 255, 255), font_size=28)

        # Quadrant 2: US Interstate Highway Green Guide Sign
        draw.rectangle([266, 38, 490, 218], fill=(15, 115, 60, 255), outline=(255, 255, 255, 255), width=4)
        draw.text((280, 60), "INTERSTATE", fill=(255, 255, 255, 255), font_size=18)
        draw.text((340, 95), "95", fill=(255, 255, 255, 255), font_size=38)
        draw.text((280, 160), "DOWNTOWN  EXIT 1A", fill=(255, 255, 255, 255), font_size=16)

        # Quadrant 3: Yellow Diamond Warning Sign
        pts_d = [(128, 266), (228, 366), (128, 466), (28, 366)]
        draw.polygon(pts_d, fill=(245, 195, 30, 255), outline=(20, 20, 20, 255))
        draw.text((70, 350), "SIGNAL AHEAD", fill=(20, 20, 20, 255), font_size=15)

        # Quadrant 4: Speed Limit 45 Sign
        draw.rectangle([286, 266, 470, 466], fill=(245, 245, 245, 255), outline=(20, 20, 20, 255), width=6)
        draw.text((310, 285), "SPEED", fill=(20, 20, 20, 255), font_size=24)
        draw.text((315, 325), "LIMIT", fill=(20, 20, 20, 255), font_size=24)
        draw.text((330, 375), "45", fill=(20, 20, 20, 255), font_size=55)

        self._save_dds_and_png(img_signs, "signs_atlas_albedo", 'DXT1')

    # =========================================================================
    # 8. Animated Water Ripple Normal Map
    # =========================================================================
    def build_water_normal(self, width=512, height=512):
        noise1 = generate_perlin_noise_2d(width, height, octaves=4, persistence=0.5, seed=701)
        noise2 = generate_perlin_noise_2d(width, height, octaves=5, persistence=0.6, seed=702)
        wave_height = (noise1 * 0.65 + noise2 * 0.35).astype(np.float32)

        normal_water = generate_sobel_normal_map(wave_height, strength=3.0)
        img_water_norm = Image.fromarray(normal_water, mode='RGBA')
        self._save_dds_and_png(img_water_norm, "water_normal", 'DXT1')

    def generate_all(self):
        """Synthesizes the entire photorealistic texture suite."""
        print("Synthesizing PBR texture suite...")
        self.build_road_asphalt()
        self.build_highway_asphalt()
        self.build_concrete_and_sidewalk()
        self.build_facade_textures()
        self.build_roof_and_metal()
        self.build_nature_textures()
        self.build_american_signage()
        self.build_water_normal()
        print("All textures synthesized and saved to DDS successfully.")
