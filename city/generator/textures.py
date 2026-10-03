"""
textures.py - High-Resolution Procedural Texture Synthesizer for American Metropolises
Synthesizes photographic and architectural textures: Asphalt roadways with lane markings,
highways, crosswalks, concrete sidewalks with granite curbs, glass curtain walls with
illuminated office windows, brick masonry, limestone Art Deco facades, industrial siding,
commercial storefronts, neon signs, highway direction signs, tunnel tiles, and botanical foliage.
Outputs both DirectDraw Surface (.dds) with mipmaps and lossless PNG fallbacks.
"""

import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from .dds import save_image_to_dds


class TextureSynthesizer:
    def __init__(self, output_dir="resource/textures"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.generated_images = {}  # name -> PIL.Image

    def _save(self, name, img, fmt='DXT1'):
        """Saves image to both .dds (for TXD / MTA D3D9) and .png (for universal fallback)."""
        self.generated_images[name] = img
        dds_path = os.path.join(self.output_dir, f"{name}.dds")
        png_path = os.path.join(self.output_dir, f"{name}.png")

        # Save DDS
        save_image_to_dds(img, dds_path, format_type=fmt, generate_mips=True)
        # Save PNG
        img.save(png_path, "PNG", optimize=True)

    def generate_all(self):
        """Synthesizes all textures required by the procedural American city."""
        print("Synthesizing comprehensive urban texture suite...")

        self._gen_asphalt_road()
        self._gen_asphalt_highway()
        self._gen_crosswalk()
        self._gen_sidewalk_paver()
        self._gen_curb_stone()
        self._gen_concrete_wall()
        self._gen_glass_curtain_a()
        self._gen_glass_curtain_b()
        self._gen_bldg_brick()
        self._gen_bldg_stone()
        self._gen_roof_gravel()
        self._gen_metal_corrugated()
        self._gen_storefront_atlas()
        self._gen_neon_signs_atlas()
        self._gen_signs_atlas()
        self._gen_tunnel_tiles()
        self._gen_grass_paver()
        self._gen_oak_leaves()
        self._gen_palm_frond()
        self._gen_water_normal()
        self._gen_pbr_auxiliary_maps()

        print(f"Generated {len(self.generated_images)} procedural textures successfully.")
        return self.generated_images

    def _gen_asphalt_road(self):
        """Standard 2-lane American city street with yellow double centerline and white edge lines."""
        w, h = 512, 512
        # Base dark aggregate asphalt
        noise = np.random.normal(52, 6, (h, w)).clip(35, 75).astype(np.uint8)
        rgb = np.stack([noise, (noise * 0.98).astype(np.uint8), (noise * 0.95).astype(np.uint8)], axis=-1)
        img = Image.fromarray(rgb, 'RGB')
        draw = ImageDraw.Draw(img)

        # Center double solid yellow lines (American standard: MUTCD Section 3B.01)
        center_x = w // 2
        line_w = 6
        gap = 8
        draw.line([(center_x - gap // 2 - line_w, 0), (center_x - gap // 2 - line_w, h)], fill=(225, 175, 25), width=line_w)
        draw.line([(center_x + gap // 2 + line_w, 0), (center_x + gap // 2 + line_w, h)], fill=(225, 175, 25), width=line_w)

        # White outer edge lines (fog lines)
        draw.line([(24, 0), (24, h)], fill=(215, 215, 215), width=5)
        draw.line([(w - 24, 0), (w - 24, h)], fill=(215, 215, 215), width=5)

        # Subtle tire wear tracks
        wear = Image.new('L', (w, h), 0)
        wear_draw = ImageDraw.Draw(wear)
        wear_draw.rectangle([center_x - 140, 0, center_x - 70, h], fill=30)
        wear_draw.rectangle([center_x + 70, 0, center_x + 140, h], fill=30)
        wear = wear.filter(ImageFilter.GaussianBlur(15))
        img = Image.composite(Image.new('RGB', (w, h), (35, 36, 38)), img, wear)

        self._save("asphalt_road", img, 'DXT1')

    def _gen_asphalt_highway(self):
        """4-lane expressway asphalt with dashed white lane dividers and solid yellow shoulder line."""
        w, h = 512, 512
        noise = np.random.normal(48, 5, (h, w)).clip(30, 70).astype(np.uint8)
        rgb = np.stack([noise, noise, (noise * 1.02).astype(np.uint8)], axis=-1)
        img = Image.fromarray(rgb, 'RGB')
        draw = ImageDraw.Draw(img)

        # Left shoulder solid yellow line
        draw.line([(20, 0), (20, h)], fill=(230, 180, 20), width=7)

        # Center dashed white lane divider
        dash_len = 48
        gap_len = 32
        for y in range(0, h, dash_len + gap_len):
            draw.line([(w // 2, y), (w // 2, min(h, y + dash_len))], fill=(220, 220, 220), width=6)

        # Right shoulder solid white line
        draw.line([(w - 20, 0), (w - 20, h)], fill=(225, 225, 225), width=7)

        self._save("asphalt_hwy", img, 'DXT1')

    def _gen_crosswalk(self):
        """High-visibility American continental / zebra crosswalk stripes and thick stop bar."""
        w, h = 512, 512
        noise = np.random.normal(50, 5, (h, w)).clip(35, 70).astype(np.uint8)
        rgb = np.stack([noise, noise, noise], axis=-1)
        img = Image.fromarray(rgb, 'RGB')
        draw = ImageDraw.Draw(img)

        # Thick white stop bar at top
        draw.rectangle([0, 15, w, 55], fill=(230, 230, 230))

        # Wide zebra crossing stripes
        num_stripes = 8
        stripe_w = 40
        spacing = w / num_stripes
        for i in range(num_stripes):
            sx = int(i * spacing + (spacing - stripe_w) / 2)
            draw.rectangle([sx, 90, sx + stripe_w, h - 30], fill=(235, 235, 235))

        self._save("crosswalk", img, 'DXT1')

    def _gen_sidewalk_paver(self):
        """Square concrete sidewalk slabs (1.5m grid) with expansion joints, aggregate, and dirt."""
        w, h = 512, 512
        base = np.random.normal(185, 10, (h, w)).clip(140, 230).astype(np.uint8)
        r = base
        g = (base * 0.98).astype(np.uint8)
        b = (base * 0.94).astype(np.uint8)
        img = Image.fromarray(np.stack([r, g, b], axis=-1), 'RGB')
        draw = ImageDraw.Draw(img)

        # Concrete joint grid (256x256 tiles inside 512x512)
        grid_step = 128
        for x in range(0, w, grid_step):
            draw.line([(x, 0), (x, h)], fill=(90, 85, 80), width=2)
            draw.line([(x + 1, 0), (x + 1, h)], fill=(120, 115, 110), width=1)
        for y in range(0, h, grid_step):
            draw.line([(0, y), (w, y)], fill=(90, 85, 80), width=2)
            draw.line([(0, y + 1), (w, y + 1)], fill=(120, 115, 110), width=1)

        self._save("sidewalk_paver", img, 'DXT1')

    def _gen_curb_stone(self):
        """Cast concrete road curb with upper edge bevel and expansion seams."""
        w, h = 512, 512
        base = np.random.normal(160, 8, (h, w)).clip(130, 200).astype(np.uint8)
        img = Image.fromarray(np.stack([base, base, base], axis=-1), 'RGB')
        draw = ImageDraw.Draw(img)

        # Upper curb bevel highlight
        draw.rectangle([0, 0, w, 40], fill=(205, 205, 200))
        draw.line([(0, 40), (w, 40)], fill=(110, 110, 105), width=2)
        # Curb face shading
        draw.rectangle([0, 42, w, h], fill=(150, 148, 145))

        # Vertical expansion seams every 128px
        for x in range(0, w, 128):
            draw.line([(x, 0), (x, h)], fill=(80, 78, 75), width=2)

        self._save("curb_stone", img, 'DXT1')

    def _gen_concrete_wall(self):
        """Architectural cast concrete panels with tie-rod holes and formwork seams."""
        w, h = 512, 512
        noise = np.random.normal(165, 8, (h, w)).clip(135, 205).astype(np.uint8)
        img = Image.fromarray(np.stack([noise, noise, (noise * 0.98).astype(np.uint8)], axis=-1), 'RGB')
        draw = ImageDraw.Draw(img)

        # Horizontal panel seams
        draw.line([(0, 170), (w, 170)], fill=(95, 95, 90), width=2)
        draw.line([(0, 340), (w, 340)], fill=(95, 95, 90), width=2)

        # Tie rod circular holes
        holes = [(64, 85), (256, 85), (448, 85),
                 (64, 255), (256, 255), (448, 255),
                 (64, 425), (256, 425), (448, 425)]
        for hx, hy in holes:
            draw.ellipse([hx - 4, hy - 4, hx + 4, hy + 4], fill=(60, 60, 58), outline=(100, 100, 98))

        self._save("concrete_wall", img, 'DXT1')

    def _gen_glass_curtain_a(self):
        """Modern corporate skyscraper curtain wall: reflective cyan-tinted glass with illuminated warm offices."""
        w, h = 512, 512
        img = Image.new('RGB', (w, h), (25, 45, 60))
        draw = ImageDraw.Draw(img)

        # 4 bays x 4 floors
        bays, floors = 4, 4
        bw = w // bays
        fh = h // floors

        rng = np.random.RandomState(101)
        for r in range(floors):
            for c in range(bays):
                x0, y0 = c * bw, r * fh
                x1, y1 = x0 + bw, y0 + fh

                # Dark mullion border
                draw.rectangle([x0, y0, x1, y1], outline=(15, 22, 28), width=3)

                # Window glass interior
                is_lit = rng.rand() > 0.45
                if is_lit:
                    # Warm interior office glow (yellow/white)
                    lit_val = rng.randint(200, 255)
                    draw.rectangle([x0 + 4, y0 + 4, x1 - 4, y1 - 4], fill=(lit_val, int(lit_val * 0.92), int(lit_val * 0.70)))
                    # Horizontal blinds or partition
                    if rng.rand() > 0.5:
                        blind_y = rng.randint(y0 + 10, y1 - 20)
                        draw.rectangle([x0 + 4, y0 + 4, x1 - 4, blind_y], fill=(160, 150, 120))
                else:
                    # Reflective deep blue/cyan sky reflection
                    grad_b = rng.randint(60, 95)
                    draw.rectangle([x0 + 4, y0 + 4, x1 - 4, y1 - 4], fill=(20, int(grad_b * 0.75), grad_b))

        self._save("glass_curtain_a", img, 'DXT1')

    def _gen_glass_curtain_b(self):
        """High-rise residential glass tower: balcony railings, glass sliding doors, curtains."""
        w, h = 512, 512
        img = Image.new('RGB', (w, h), (40, 48, 55))
        draw = ImageDraw.Draw(img)

        bays, floors = 4, 4
        bw, fh = w // bays, h // floors
        rng = np.random.RandomState(202)

        for r in range(floors):
            # Concrete floor slab
            slab_y = r * fh
            draw.rectangle([0, slab_y, w, slab_y + 12], fill=(160, 160, 158))
            for c in range(bays):
                x0 = c * bw
                x1 = x0 + bw
                y0 = slab_y + 12
                y1 = slab_y + fh

                draw.rectangle([x0, y0, x1, y1], outline=(25, 30, 35), width=2)
                is_lit = rng.rand() > 0.5
                if is_lit:
                    draw.rectangle([x0 + 4, y0 + 4, x1 - 4, y1 - 24], fill=(240, 220, 180))
                else:
                    draw.rectangle([x0 + 4, y0 + 4, x1 - 4, y1 - 24], fill=(30, 42, 55))

                # Glass balcony railing at bottom
                draw.rectangle([x0 + 2, y1 - 22, x1 - 2, y1 - 2], fill=(60, 80, 95), outline=(130, 140, 150))

        self._save("glass_curtain_b", img, 'DXT1')

    def _gen_bldg_brick(self):
        """American classic running-bond red brick facade with mortar joints and weathered accents."""
        w, h = 512, 512
        mortar = (150, 145, 138)
        img = Image.new('RGB', (w, h), mortar)
        draw = ImageDraw.Draw(img)

        brick_h = 16
        brick_w = 40
        mortar_size = 2

        rng = np.random.RandomState(303)
        row = 0
        for y in range(0, h, brick_h + mortar_size):
            offset = (brick_w // 2) if (row % 2 == 1) else 0
            for x in range(-offset, w + brick_w, brick_w + mortar_size):
                # Red brick color variation
                r = rng.randint(145, 185)
                g = rng.randint(55, 78)
                b = rng.randint(45, 65)
                draw.rectangle([x, y, x + brick_w, y + brick_h], fill=(r, g, b))
            row += 1

        self._save("bldg_brick", img, 'DXT1')

    def _gen_bldg_stone(self):
        """Limestone / sandstone architectural facade with fluted channels and Art Deco spandrels."""
        w, h = 512, 512
        base = np.random.normal(195, 7, (h, w)).clip(160, 230).astype(np.uint8)
        r = base
        g = (base * 0.95).astype(np.uint8)
        b = (base * 0.88).astype(np.uint8)
        img = Image.fromarray(np.stack([r, g, b], axis=-1), 'RGB')
        draw = ImageDraw.Draw(img)

        # Architectural pilasters and spandrel recesses
        bays, floors = 4, 4
        bw, fh = w // bays, h // floors
        for r_idx in range(floors):
            for c_idx in range(bays):
                x0, y0 = c_idx * bw, r_idx * fh
                x1, y1 = x0 + bw, y0 + fh
                # Stone pilaster vertical borders
                draw.rectangle([x0, y0, x0 + 10, y1], fill=(170, 162, 150))
                draw.rectangle([x1 - 10, y0, x1, y1], fill=(170, 162, 150))
                # Window opening
                draw.rectangle([x0 + 14, y0 + 16, x1 - 14, y1 - 16], fill=(35, 45, 55), outline=(130, 125, 115))

        self._save("bldg_stone", img, 'DXT1')

    def _gen_roof_gravel(self):
        """Tar and aggregate pea-gravel flat commercial roof with circular drainage grates."""
        w, h = 512, 512
        noise = np.random.normal(110, 14, (h, w)).clip(65, 165).astype(np.uint8)
        img = Image.fromarray(np.stack([noise, noise, (noise * 0.96).astype(np.uint8)], axis=-1), 'RGB')
        draw = ImageDraw.Draw(img)

        # Cast iron roof drainage bowl and grate
        cx, cy = w // 2, h // 2
        draw.ellipse([cx - 36, cy - 36, cx + 36, cy + 36], fill=(45, 45, 48), outline=(25, 25, 28), width=3)
        for ang in range(0, 360, 30):
            rad = math.radians(ang)
            ex = cx + int(32 * math.cos(rad))
            ey = cy + int(32 * math.sin(rad))
            draw.line([(cx, cy), (ex, ey)], fill=(20, 20, 22), width=2)

        self._save("roof_gravel", img, 'DXT1')

    def _gen_metal_corrugated(self):
        """Industrial corrugated sheet metal with vertical fluting ribs and subtle rust."""
        w, h = 512, 512
        rib_w = 16
        rib = (np.sin(np.linspace(0, np.pi * 2 * (w / rib_w), w)) * 35 + 130).clip(70, 200).astype(np.uint8)
        base = np.tile(rib, (h, 1))

        # Add subtle rust streaks
        rust = np.random.normal(0, 10, (h, w)).clip(-20, 40)
        r = (base + np.maximum(0, rust * 1.5)).clip(0, 255).astype(np.uint8)
        g = (base + np.maximum(0, rust * 0.8)).clip(0, 255).astype(np.uint8)
        b = (base - np.maximum(0, rust * 0.5)).clip(0, 255).astype(np.uint8)
        img = Image.fromarray(np.stack([r, g, b], axis=-1), 'RGB')

        self._save("metal_corrugated", img, 'DXT1')

    def _gen_storefront_atlas(self):
        """Street-level commercial retail atlas: Diner, Deli, Coffee Shop, Pharmacy."""
        w, h = 512, 512
        img = Image.new('RGB', (w, h), (180, 175, 170))
        draw = ImageDraw.Draw(img)

        # 4 distinct storefronts arranged in a 2x2 grid
        shops = [
            ("METRO DELI & BAKERY", (180, 40, 30), 0, 0),
            ("ROAST COFFEE HOUSE", (45, 80, 50), 256, 0),
            ("EMPIRE RETRO DINER", (20, 70, 140), 0, 256),
            ("CITY RX PHARMACY", (30, 130, 120), 256, 256)
        ]

        for title, banner_col, ox, oy in shops:
            # Storefront fascia sign
            draw.rectangle([ox + 10, oy + 12, ox + 246, oy + 54], fill=banner_col, outline=(30, 30, 30))
            draw.text((ox + 24, oy + 24), title, fill=(255, 255, 255))

            # Large display windows
            draw.rectangle([ox + 16, oy + 70, ox + 150, oy + 220], fill=(210, 230, 245), outline=(40, 40, 40), width=3)
            # Shop entrance door
            draw.rectangle([ox + 165, oy + 70, ox + 236, oy + 236], fill=(190, 215, 235), outline=(40, 40, 40), width=3)
            # Door handle
            draw.line([(ox + 175, oy + 150), (ox + 175, oy + 175)], fill=(220, 190, 60), width=3)

        self._save("storefront_atlas", img, 'DXT1')

    def _gen_neon_signs_atlas(self):
        """Illuminated neon signs: HOTEL, BAR, 24H DINER, LOUNGE."""
        w, h = 512, 512
        img = Image.new('RGB', (w, h), (12, 12, 14))
        draw = ImageDraw.Draw(img)

        signs = [
            ("GRAND HOTEL", (255, 40, 80), 30, 40),
            ("BLUE BAR", (40, 180, 255), 280, 40),
            ("OPEN 24 HOURS", (80, 255, 100), 40, 160),
            ("CITY LOUNGE", (255, 200, 30), 270, 160),
            ("COCKTAILS", (255, 80, 220), 40, 280),
            ("MOTEL VACANCY", (255, 60, 40), 260, 280)
        ]

        for text, col, x, y in signs:
            # Glow backing box
            draw.rectangle([x - 10, y - 8, x + 210, y + 55], fill=(25, 25, 32), outline=(50, 50, 65))
            # Text neon core
            draw.text((x + 10, y + 12), text, fill=col)

        self._save("neon_signs_atlas", img, 'DXT1')

    def _gen_signs_atlas(self):
        """MUTCD standard green highway destination signs, Stop signs, and speed limits."""
        w, h = 512, 512
        img = Image.new('RGB', (w, h), (180, 180, 185))
        draw = ImageDraw.Draw(img)

        # 1. Highway Overhead Green Sign
        draw.rectangle([20, 20, 492, 160], fill=(0, 105, 60), outline=(255, 255, 255), width=5)
        draw.text((45, 45), "NORTH   EXPWY 101", fill=(255, 255, 255))
        draw.text((45, 80), "DOWNTOWN  /  WATERFRONT", fill=(255, 255, 255))
        draw.text((45, 115), "EXIT 4A   1/2 MILE  -->", fill=(255, 255, 255))

        # 2. Octagonal Red STOP Sign
        stop_cx, stop_cy, stop_r = 120, 260, 75
        pts = []
        for i in range(8):
            ang = math.radians(22.5 + i * 45)
            pts.append((stop_cx + int(stop_r * math.cos(ang)), stop_cy + int(stop_r * math.sin(ang))))
        draw.polygon(pts, fill=(200, 20, 20), outline=(255, 255, 255))
        draw.text((stop_cx - 32, stop_cy - 12), "STOP", fill=(255, 255, 255))

        # 3. White SPEED LIMIT 35 Sign
        draw.rectangle([280, 190, 460, 340], fill=(245, 245, 245), outline=(20, 20, 20), width=4)
        draw.text((305, 210), "SPEED", fill=(20, 20, 20))
        draw.text((305, 245), "LIMIT", fill=(20, 20, 20))
        draw.text((330, 280), "35", fill=(20, 20, 20))

        # 4. Green Street Name Sign ("MAIN ST / 5TH AVE")
        draw.rectangle([30, 380, 480, 470], fill=(0, 110, 65), outline=(255, 255, 255), width=4)
        draw.text((60, 410), "W BROADWAY / 5TH AVE", fill=(255, 255, 255))

        self._save("signs_atlas", img, 'DXT1')

    def _gen_tunnel_tiles(self):
        """Glazed ceramic subway/road tunnel tiles with reflection and yellow safety reflector stripe."""
        w, h = 512, 512
        img = Image.new('RGB', (w, h), (235, 238, 242))
        draw = ImageDraw.Draw(img)

        # 16x16 tile grid
        tile_w, tile_h = 32, 16
        for y in range(0, h, tile_h):
            draw.line([(0, y), (w, y)], fill=(155, 160, 168), width=1)
        for x in range(0, w, tile_w):
            draw.line([(x, 0), (x, h)], fill=(155, 160, 168), width=1)

        # Yellow reflective safety belt in the middle
        draw.rectangle([0, 230, w, 282], fill=(235, 195, 20))
        # Black chevron stripes on the reflector belt
        for x in range(0, w, 48):
            draw.polygon([(x, 230), (x + 24, 256), (x, 282), (x - 12, 282), (x + 12, 256), (x - 12, 230)], fill=(30, 30, 30))

        self._save("tunnel_tiles", img, 'DXT1')

    def _gen_grass_paver(self):
        """Lush green urban park grass with fine blade texture."""
        w, h = 512, 512
        noise = np.random.normal(85, 12, (h, w)).clip(40, 140).astype(np.uint8)
        r = (noise * 0.55).astype(np.uint8)
        g = (noise * 1.25).clip(0, 255).astype(np.uint8)
        b = (noise * 0.40).astype(np.uint8)
        img = Image.fromarray(np.stack([r, g, b], axis=-1), 'RGB')
        self._save("grass_paver", img, 'DXT1')

    def _gen_oak_leaves(self):
        """American Oak leaf canopy foliage with cut-out alpha transparency."""
        w, h = 512, 512
        img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        rng = np.random.RandomState(404)
        for _ in range(350):
            cx = rng.randint(20, w - 20)
            cy = rng.randint(20, h - 20)
            lw = rng.randint(22, 48)
            lh = rng.randint(16, 32)
            rot = rng.randint(0, 360)

            r = rng.randint(35, 65)
            g = rng.randint(110, 175)
            b = rng.randint(25, 55)

            leaf = Image.new('RGBA', (lw * 2, lh * 2), (0, 0, 0, 0))
            ld = ImageDraw.Draw(leaf)
            ld.ellipse([lw // 2, lh // 2, lw * 3 // 2, lh * 3 // 2], fill=(r, g, b, 255))
            leaf = leaf.rotate(rot, resample=Image.Resampling.BILINEAR)

            img.alpha_composite(leaf, (cx - lw, cy - lh))

        self._save("oak_leaves", img, 'DXT5')

    def _gen_palm_frond(self):
        """California fan palm frond with detailed leaflets and alpha cutout."""
        w, h = 512, 512
        img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Central palm stem
        draw.line([(w // 2, 480), (w // 2, 40)], fill=(90, 115, 60, 255), width=8)

        # Lateral leaflets
        for y in range(80, 440, 12):
            progress = (y - 80) / 360.0
            span = int(180 * math.sin(progress * math.pi))
            col = (int(50 + 20 * progress), int(135 + 30 * progress), 45, 255)
            draw.line([(w // 2, y), (w // 2 - span, y + 25)], fill=col, width=4)
            draw.line([(w // 2, y), (w // 2 + span, y + 25)], fill=col, width=4)

        self._save("palm_frond", img, 'DXT5')

    def _gen_water_normal(self):
        """Dynamic undulating river water normal map."""
        w, h = 512, 512
        x = np.linspace(0, 16 * np.pi, w)
        y = np.linspace(0, 16 * np.pi, h)
        xx, yy = np.meshgrid(x, y)

        wave = np.sin(xx + yy * 0.5) * 0.5 + np.sin(xx * 1.5 - yy * 0.8) * 0.3 + np.cos(xx * 0.8 + yy * 2.0) * 0.2
        dx, dy = np.gradient(wave)

        nx = (-dx * 4.0).clip(-1.0, 1.0)
        ny = (-dy * 4.0).clip(-1.0, 1.0)
        nz = np.sqrt(np.maximum(0.01, 1.0 - nx**2 - ny**2))

        # Pack into [0..255] tangent space normal
        r = ((nx * 0.5 + 0.5) * 255).astype(np.uint8)
        g = ((ny * 0.5 + 0.5) * 255).astype(np.uint8)
        b = ((nz * 0.5 + 0.5) * 255).astype(np.uint8)
        img = Image.fromarray(np.stack([r, g, b], axis=-1), 'RGB')

        self._save("water_normal", img, 'DXT1')

    def _gen_pbr_auxiliary_maps(self):
        """Auxiliary normal, puddle, and emissive maps for road and facade shaders."""
        w, h = 512, 512
        # 1. Asphalt Normal Map
        noise_x = np.random.normal(0, 0.08, (h, w)).clip(-0.5, 0.5)
        noise_y = np.random.normal(0, 0.08, (h, w)).clip(-0.5, 0.5)
        noise_z = np.sqrt(np.maximum(0.1, 1.0 - noise_x**2 - noise_y**2))
        r = ((noise_x * 0.5 + 0.5) * 255).astype(np.uint8)
        g = ((noise_y * 0.5 + 0.5) * 255).astype(np.uint8)
        b = ((noise_z * 0.5 + 0.5) * 255).astype(np.uint8)
        img_norm = Image.fromarray(np.stack([r, g, b], axis=-1), 'RGB')
        self._save("asphalt_normal", img_norm, 'DXT1')
        self._save("highway_normal", img_norm, 'DXT1')
        self._save("concrete_normal", img_norm, 'DXT1')
        self._save("sidewalk_normal", img_norm, 'DXT1')
        self._save("roof_gravel_normal", img_norm, 'DXT1')

        # 2. Road Puddle Mask
        puddle_arr = np.zeros((h, w), dtype=np.uint8)
        for _ in range(12):
            cx = np.random.randint(40, w - 40)
            cy = np.random.randint(40, h - 40)
            rx = np.random.randint(30, 80)
            ry = np.random.randint(20, 50)
            yy, xx = np.ogrid[:h, :w]
            dist = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
            puddle_arr[dist <= 1.0] = 255
        puddle_img = Image.fromarray(puddle_arr, 'L').filter(ImageFilter.GaussianBlur(8))
        self._save("asphalt_puddle", puddle_img.convert('RGB'), 'DXT1')

        # 3. Emissive Glass Map
        emissive_img = Image.new('RGB', (w, h), (0, 0, 0))
        e_draw = ImageDraw.Draw(emissive_img)
        rng = np.random.RandomState(505)
        for r_idx in range(4):
            for c_idx in range(4):
                if rng.rand() > 0.45:
                    x0, y0 = c_idx * 128 + 6, r_idx * 128 + 6
                    x1, y1 = x0 + 116, y0 + 116
                    e_draw.rectangle([x0, y0, x1, y1], fill=(255, 235, 175))
        self._save("glass_a_emiss", emissive_img, 'DXT1')
