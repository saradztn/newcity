# New American City — Deep Technical Architecture Manual

## Overview
**New American City** is an end-to-end procedural city generator and DirectX 9 mini-graphics engine built entirely from scratch for **Multi Theft Auto: San Andreas (MTA:SA)**.

The city is situated at target coordinates:
- **X = -4076.83813**
- **Y = 492.02350**
- **Z = 161.42682**

It generates a complete standalone American metropolis procedurally in Python, writes authentic binary RenderWare (DFF, TXD), GTA collision (COL3), and DirectDraw Surface (DDS) assets, and mounts them inside an optimized, runnable MTA:SA resource equipped with dynamic PBR approximations, atmospheric scattering, solar lighting, screen-space reflections (SSR), and dynamic weather.

---

## 1. Directory Structure

```text
newcity/
├── run_pipeline.py                 # Top-level build & validation runner
├── README.md                       # Project documentation & usage
├── ARCHITECTURE.md                 # Deep technical architecture manual
├── city/
│   └── generator/                  # Python Procedural Generation Engine
│       ├── __init__.py
│       ├── dds.py                  # DirectDraw Surface (BC1/BC3) with mipmaps
│       ├── rw_dff.py               # RenderWare 3.6 DFF Clump binary encoder
│       ├── rw_txd.py               # RenderWare 3.6 TXD texture dictionary encoder
│       ├── collision.py            # GTA:SA COL3 binary collision generator
│       ├── lod.py                  # Level of Detail (LOD) generator
│       ├── bake.py                 # Prelit vertex lighting baker (sky glow + point lights)
│       ├── bldkit.py               # Floor- and bay-aligned architectural mapping
│       ├── textures.py             # Photorealistic procedural texture synthesizer
│       ├── ground.py               # Modular ground cells, avenues, curbs, sidewalks
│       ├── buildings.py            # 17 American architectural building archetypes
│       ├── infrastructure.py       # Elevated viaducts, ramps, cable bridge, tunnel
│       ├── props.py                # Street furniture, traffic signals, hydrants
│       ├── vegetation.py           # California fan palms, American broadleaf oaks
│       ├── city_plan.py            # Master urban plan and spatial layout database
│       ├── city.py                 # Master orchestrator & pipeline builder
│       └── validator.py            # Automated QA validator (DFF/TXD/COL/LUA/FX)
└── resource/                       # Standalone Runnable MTA:SA Resource
    ├── meta.xml                    # Resource manifest
    ├── client/
    │   ├── config.lua              # Quality presets: LOW, MEDIUM, HIGH, ULTRA
    │   ├── models.lua              # Auto-generated model registry & draw distances
    │   ├── layout.lua              # Auto-generated world placements & POIs
    │   ├── environment.lua         # Solar math, day/night keyframes, atmosphere
    │   ├── weather.lua             # Weather director (CLEAR, RAIN, STORM, etc.)
    │   ├── puddle_system.lua       # Dynamic surface wetness & drying engine
    │   ├── renderer.lua            # Mini-graphics renderer, shaders & post-fx
    │   ├── streaming.lua           # Cell-based asset & LOD object streamer
    │   ├── lighting.lua            # Dynamic street lighting & window states
    │   ├── debug_ui.lua            # In-game telemetry HUD (F7 toggle)
    │   └── main.lua                # Client lifecycle initialization
    ├── server/
    │   └── main.lua                # Server setup, /citytp, /citytime, /cityweather
    ├── shaders/
    │   ├── road_pbr.fx             # Asphalt PBR: micro-cracks, wetness, sun glint
    │   ├── building_facade.fx      # Facade glass reflection, night window lights
    │   ├── sun_shafts.fx           # Screen-space God Rays with dithered sampling
    │   ├── sky_atmosphere.fx       # Rayleigh/Mie atmospheric scattering & sun disc
    │   ├── ssr_reflection.fx       # Screen-space reflections for wet roads & glass
    │   ├── water_surface.fx        # River water ripples, Fresnel, depth absorption
    │   ├── street_light.fx         # Volumetric light cones & sodium/LED halos
    │   ├── rain_screen.fx          # Camera lens refraction droplets
    │   └── tex_diffuse.fx          # Universal fallback hardware texture mapper
    ├── models/                     # High-detail DFF and low-poly LOD DFF files
    ├── collisions/                 # Validated GTA:SA COL3 files
    ├── textures/                   # Native TXD, DDS, and fallback PNG textures
    └── data/
        └── city_layout.json        # Spatial instance database and dynamic streetlights
```

---

## 2. Resolution of the White City Rendering Issue

In GTA SA and MTA:SA, custom models often render as pure white cardboard blocks due to four distinct failure points. This project resolves all four:

1. **Direct3D 9 TXD Binary Conformance**:
   - In standard GTA SA PC, the Texture Dictionary struct requires `deviceId = 9` (Direct3D 9). Passing `1` (D3D8 generic) causes GTA SA's RenderWare driver to reject the TXD.
   - The native texture struct conforms to `RpRasterPC_Header` (88 bytes):
     - `platformId`: `9` (Direct3D 9).
     - `filter_and_addressing`: `0x1106` (linear-mip-linear filtering `0x06`, wrapU `0x01`, wrapV `0x01`).
     - `rasterFormat`: `0x0280` (`rwRASTERFORMAT565 | rwRASTERFORMATMIPMAP`) for DXT1, and `0x0480` (`rwRASTERFORMAT4444 | rwRASTERFORMATMIPMAP`) for DXT5. Writing unaligned values like `0x8200` causes Direct3D texture creation to fail.
     - `numLevels`: Complete 10-level mipmap pyramid down to 1x1.

2. **RenderWare 3.6 DFF Clump Conformance**:
   - `flags` packed as `(1 << 16) | FLAG_POSITIONS | FLAG_TEXTURED | FLAG_PRELIT | FLAG_NORMALS | FLAG_MODULATE`.
   - Bit 16 indicates 1 set of UV coordinates. If omitted, RenderWare skips texture sampling entirely.
   - Triangle winding packed as `(v1, v0, mat_id, v2)` for GTA SA Direct3D CCW orientation.
   - Texture chunk header formatted as `b'\x06\x11\x00\x00'`.
   - BinMesh PLG chunk (`0x050E`) groups indices cleanly by material ID.

3. **Prelit Vertex Lighting Bake (`bake.py`)**:
   - Unbaked RenderWare models with pure white vertex colors `(255, 255, 255, 255)` wash out textures or render flat.
   - `VertexBaker` calculates:
     - Hemispherical skylight ambient: upward faces receive cool sky ambient `(145, 155, 185)`.
     - Street canyon height falloff: narrow street levels are shaded smoothly (`0.82x`), while tower tops catch full skylight (`1.15x`).
     - Local point light baking: streetlamps (sodium orange `(255, 195, 115)`) cast quadratic light pools directly onto road and sidewalk vertices.
     - Emissive surface overrides: windows, neon signs, and LED lines are set to full brightness in the vertex color stream.

4. **Dual Texture Delivery & Universal Fallback**:
   - Both `.dds` and lossless `.png` textures are generated in `resource/textures/`.
   - In `streaming.lua`, `engineImportTXD(txd, modelId)` and `engineImportTXD(txd, lodModelId)` are called **prior** to model replacement.
   - In `renderer.lua`, a universal direct texture mapper (`tex_diffuse.fx`) binds every world texture name (`asphalt_road`, `sidewalk_paver`, `glass_curtain_a`, etc.) directly via hardware samplers, guaranteeing that no model can ever be drawn white.

---

## 3. Shader Model 2.0 Instruction Slot Compliance

DirectX 9 Shader Model 2.0 (`ps_2_0`) enforces a strict hard limit of 64 arithmetic instruction slots and 32 texture instruction slots. Complex loops or excessive texture samples trigger compile errors (e.g., X5608 / X5609).

Every shader in this engine implements dual techniques:
1. **SM 3.0 Technique (`ps_3_0`)**: High-fidelity pass with full physical parameters, 16-sample radial light integration, multiple normal map layers, and dynamic loops.
2. **SM 2.0 Technique (`ps_2_0`)**: Compact fallback pass containing under 35 arithmetic instructions, unrolled single-tap lookups, and branch-free formulas.

Example (`sun_shafts.fx` SM 2.0 Fallback):
```hlsl
float4 PixelShaderFunction_SM2(PS_INPUT input) : COLOR0
{
    float4 originalColor = tex2D(ScreenSampler, input.TexCoord);
    if (gSunVisibility <= 0.001 || gShaftIntensity <= 0.001) return originalColor;

    float2 delta = (input.TexCoord - gSunScreenPos) * (0.25 * gDensity);
    float2 curCoord = input.TexCoord;
    float3 shafts = float3(0.0, 0.0, 0.0);

    curCoord -= delta; shafts += tex2D(ScreenSampler, saturate(curCoord)).rgb * 0.40;
    curCoord -= delta; shafts += tex2D(ScreenSampler, saturate(curCoord)).rgb * 0.30;
    curCoord -= delta; shafts += tex2D(ScreenSampler, saturate(curCoord)).rgb * 0.20;
    curCoord -= delta; shafts += tex2D(ScreenSampler, saturate(curCoord)).rgb * 0.10;

    return float4(originalColor.rgb + shafts * gSunShaftColor * gShaftIntensity * gSunVisibility, originalColor.a);
}
```

---

## 4. Architectural Building Engine

To prevent sliced windows and distorted textures, `bldkit.py` calculates floor- and bay-aligned UV coordinates:
$$\text{nb} = \max\left(1, \text{round}\left(\frac{L}{\text{bay\_w}}\right)\right), \quad \text{nf} = \max\left(1, \text{round}\left(\frac{z_{\text{top}} - z_{\text{bottom}}}{\text{floor\_h}}\right)\right)$$

Every building archetype features:
- Ground-floor podium with retail storefronts, entrance canopies, or loading docks.
- Stepped setbacks at higher elevations.
- Parapet walls, belt cornices, and roof drainage grates.
- Rooftop mechanical clutter: elevator penthouses, HVAC cooling chillers, wooden/steel water tanks, and aviation beacon spires.
