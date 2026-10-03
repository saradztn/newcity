"""
materials.py - Comprehensive PBR Material Definitions and DX9 Approximations
Defines physical material properties: Albedo, Normal, Specular, Roughness,
Height/Parallax, Emissive, and Wetness responses for DirectX 9 / MTA:SA shaders.
"""


class MaterialDef:
    def __init__(self, name, albedo_rgb, roughness, specular_intensity,
                 normal_strength=1.0, is_transparent=False, is_emissive=False,
                 emissive_color=(0, 0, 0), wetness_darkening=0.35, puddle_receptive=True):
        self.name = name
        self.albedo_rgb = albedo_rgb          # (r, g, b) base color in [0..255]
        self.roughness = roughness            # [0.0 = mirror, 1.0 = full diffuse]
        self.specular_intensity = specular_intensity # [0.0..1.0]
        self.normal_strength = normal_strength# height / normal map depth multiplier
        self.is_transparent = is_transparent
        self.is_emissive = is_emissive
        self.emissive_color = emissive_color
        self.wetness_darkening = wetness_darkening  # How much albedo drops when wet
        self.puddle_receptive = puddle_receptive    # Whether puddles form on this material

    def to_shader_params(self, wetness_factor=0.0):
        """Calculates dynamic uniforms passed to HLSL DX9 shaders."""
        darkening = 1.0 - (self.wetness_darkening * wetness_factor)
        r = (self.albedo_rgb[0] / 255.0) * darkening
        g = (self.albedo_rgb[1] / 255.0) * darkening
        b = (self.albedo_rgb[2] / 255.0) * darkening

        # Roughness decreases with water saturation
        dyn_roughness = max(0.04, self.roughness * (1.0 - 0.75 * wetness_factor))
        # Specular increases with water surface reflection
        dyn_specular = min(1.0, self.specular_intensity + (0.85 - self.specular_intensity) * wetness_factor)

        return {
            'albedo': (r, g, b),
            'roughness': dyn_roughness,
            'specular': dyn_specular,
            'normal_strength': self.normal_strength,
        }


# Comprehensive Material Library
MATERIAL_LIBRARY = {
    # 1. Road Asphalt
    'asphalt': MaterialDef(
        name='asphalt',
        albedo_rgb=(58, 60, 62),
        roughness=0.82,
        specular_intensity=0.18,
        normal_strength=1.2,
        wetness_darkening=0.45,
        puddle_receptive=True
    ),
    # 2. Wet Asphalt
    'wet_asphalt': MaterialDef(
        name='wet_asphalt',
        albedo_rgb=(32, 33, 35),
        roughness=0.15,
        specular_intensity=0.92,
        normal_strength=0.6,
        wetness_darkening=0.0,
        puddle_receptive=True
    ),
    # 3. Structural Concrete
    'concrete': MaterialDef(
        name='concrete',
        albedo_rgb=(175, 172, 168),
        roughness=0.72,
        specular_intensity=0.22,
        normal_strength=0.8,
        wetness_darkening=0.30,
        puddle_receptive=True
    ),
    # 4. Sidewalk Pavement
    'sidewalk': MaterialDef(
        name='sidewalk',
        albedo_rgb=(190, 188, 182),
        roughness=0.78,
        specular_intensity=0.15,
        normal_strength=1.0,
        wetness_darkening=0.35,
        puddle_receptive=True
    ),
    # 5. Red Architectural Brick
    'brick': MaterialDef(
        name='brick',
        albedo_rgb=(152, 72, 58),
        roughness=0.88,
        specular_intensity=0.12,
        normal_strength=1.4,
        wetness_darkening=0.25,
        puddle_receptive=False
    ),
    # 6. Painted Concrete
    'painted_concrete': MaterialDef(
        name='painted_concrete',
        albedo_rgb=(210, 212, 215),
        roughness=0.65,
        specular_intensity=0.28,
        normal_strength=0.5,
        wetness_darkening=0.20,
        puddle_receptive=False
    ),
    # 7. Glass (Architectural Curtain Wall)
    'glass': MaterialDef(
        name='glass',
        albedo_rgb=(75, 115, 135),
        roughness=0.04,
        specular_intensity=0.98,
        normal_strength=0.1,
        is_transparent=True,
        wetness_darkening=0.05,
        puddle_receptive=False
    ),
    # 8. Structural Metal
    'metal': MaterialDef(
        name='metal',
        albedo_rgb=(160, 165, 172),
        roughness=0.35,
        specular_intensity=0.85,
        normal_strength=0.4,
        wetness_darkening=0.15,
        puddle_receptive=False
    ),
    # 9. Painted Metal (Barriers, Poles)
    'painted_metal': MaterialDef(
        name='painted_metal',
        albedo_rgb=(190, 195, 200),
        roughness=0.45,
        specular_intensity=0.55,
        normal_strength=0.3,
        wetness_darkening=0.15,
        puddle_receptive=False
    ),
    # 10. Commercial Roof Gravel/Tar
    'roof': MaterialDef(
        name='roof',
        albedo_rgb=(70, 72, 75),
        roughness=0.90,
        specular_intensity=0.10,
        normal_strength=1.3,
        wetness_darkening=0.30,
        puddle_receptive=True
    ),
    # 11. Landscape Grass
    'grass': MaterialDef(
        name='grass',
        albedo_rgb=(62, 108, 48),
        roughness=0.92,
        specular_intensity=0.08,
        normal_strength=1.5,
        wetness_darkening=0.30,
        puddle_receptive=False
    ),
    # 12. Soil / Dirt
    'soil': MaterialDef(
        name='soil',
        albedo_rgb=(104, 82, 60),
        roughness=0.95,
        specular_intensity=0.05,
        normal_strength=1.6,
        wetness_darkening=0.40,
        puddle_receptive=True
    ),
    # 13. Coastal Sand
    'sand': MaterialDef(
        name='sand',
        albedo_rgb=(215, 198, 155),
        roughness=0.92,
        specular_intensity=0.08,
        normal_strength=1.1,
        wetness_darkening=0.45,
        puddle_receptive=False
    ),
    # 14. Water Surface
    'water': MaterialDef(
        name='water',
        albedo_rgb=(28, 65, 88),
        roughness=0.02,
        specular_intensity=0.99,
        normal_strength=1.8,
        is_transparent=True,
        wetness_darkening=0.0,
        puddle_receptive=False
    ),
    # 15. Road Marking Paint
    'road_marking': MaterialDef(
        name='road_marking',
        albedo_rgb=(240, 240, 235),
        roughness=0.45,
        specular_intensity=0.65,
        normal_strength=0.7,
        wetness_darkening=0.20,
        puddle_receptive=True
    ),
    # 16. Road Yellow Marking
    'road_yellow': MaterialDef(
        name='road_yellow',
        albedo_rgb=(225, 175, 30),
        roughness=0.45,
        specular_intensity=0.65,
        normal_strength=0.7,
        wetness_darkening=0.20,
        puddle_receptive=True
    ),
    # 17. Wood
    'wood': MaterialDef(
        name='wood',
        albedo_rgb=(145, 108, 72),
        roughness=0.75,
        specular_intensity=0.20,
        normal_strength=0.9,
        wetness_darkening=0.35,
        puddle_receptive=False
    ),
    # 18. Natural Stone / Rock
    'stone': MaterialDef(
        name='stone',
        albedo_rgb=(130, 128, 125),
        roughness=0.85,
        specular_intensity=0.14,
        normal_strength=1.5,
        wetness_darkening=0.35,
        puddle_receptive=False
    ),
}


def get_material(name):
    return MATERIAL_LIBRARY.get(name, MATERIAL_LIBRARY['concrete'])
