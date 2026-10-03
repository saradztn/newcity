# New American City — Graphics Engine & Procedural Asset Pipeline for MTA:SA

## Overview
**New American City** is an end-to-end procedural city generator and DirectX 9 mini-graphics engine built entirely from scratch for **Multi Theft Auto: San Andreas (MTA:SA)**.

The project does not rely on pre-made map mods, ReShade presets, color filters, or modified stock Los Santos geometry. Instead, it generates a complete standalone American metropolis procedurally in Python, writes authentic binary RenderWare (DFF, TXD), GTA collision (COL3), and DirectDraw Surface (DDS) assets, and mounts them inside an optimized, runnable MTA:SA resource equipped with dynamic PBR approximations, atmospheric scattering, solar lighting, screen-space reflections (SSR), and dynamic weather.

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
│       ├── materials.py            # PBR material library (18 material types)
│       ├── textures.py             # Photorealistic procedural texture synthesizer
│       ├── weather_assets.py       # Cloud layers, rain streaks, lens droplets
│       ├── lighting_assets.py      # Sun disc, light cone, sodium/LED halos
│       ├── terrain.py              # Heightmap, coastline, plains, hills, valleys
│       ├── roads.py                # Road network graph, splines, cross-sections
│       ├── intersections.py        # 4-way signalized junctions, roundabouts
│       ├── highways.py             # Elevated overpasses, Jersey barriers, ramps
│       ├── bridges.py              # Concrete viaducts, water piers, railings
│       ├── tunnels.py              # Mountain portal arches, retaining walls
│       ├── districts.py            # Zoning plan: Downtown, Commercial, etc.
│       ├── buildings.py            # 23 American building archetypes
│       ├── props.py                # Street furniture, traffic signs, hydrants
│       ├── vegetation.py           # Palms, oaks, pines, shrubs
│       ├── infrastructure.py       # Streetlights, high-voltage transmission towers
│       ├── registry.py             # Model ID allocation & spatial database
│       ├── export.py               # Resource packager & meta.xml generator
│       ├── city.py                 # Master orchestrator
│       └── validator.py            # Automated QA validator (DFF/TXD/COL/LUA/FX)
└── resource/                       # Standalone Runnable MTA:SA Resource
    ├── meta.xml                    # Resource manifest (243 files declared)
    ├── client/
    │   ├── config.lua              # Quality presets: LOW, MEDIUM, HIGH, ULTRA
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
    │   ├── sun_shafts.fx           # Radial blur God Rays with dithered sampling
    │   ├── sky_atmosphere.fx       # Rayleigh/Mie scattering & dynamic sun disc
    │   ├── ssr_reflection.fx       # Screen-space reflections for wet surfaces
    │   ├── water_surface.fx        # Animated wave normals, Fresnel, depth color
    │   ├── street_light.fx         # Volumetric light cone & halo shader
    │   └── rain_screen.fx          # Camera rain droplet distortion
    ├── textures/                   # Synthesized DDS textures & TXD dictionaries
    ├── models/                     # Generated DFF models and LOD DFF models
    ├── collisions/                 # Generated COL3 collision models
    └── data/
        └── city_layout.json        # Spatial instance database & light positions
```

---

## 2. Low-Level Binary File Formats

### 2.1 DirectDraw Surface (`dds.py`)
- Compliant 128-byte DDS header: 4-byte magic `DDS `, `dwFlags`, dimensions, pitch/linear size, and `DDPIXELFORMAT`.
- Vectorized block compression in NumPy:
  - **DXT1 (BC1)**: 8 bytes per 4x4 block, 16-bit RGB565 endpoints with 4-color palette interpolation.
  - **DXT5 (BC3)**: 16 bytes per 4x4 block, 8-level alpha interpolation block + DXT1 color block.
- Automatic mipmap pyramid downsampled with Lanczos filtering down to 1x1.

### 2.2 RenderWare 3.6 DFF (`rw_dff.py`)
- RenderWare version code `0x1803FFFF` (GTA:SA 3.6.0.3 standard).
- Chunk tree hierarchy:
  - `Clump` (0x10)
    - `Struct` (0x01)
    - `FrameList` (0x0E): Frame hierarchy, 3x3 rotation matrices, positions
    - `GeometryList` (0x1A):
      - `Geometry` (0x0F): Vertex positions, normals, UV texture coordinates, prelit lighting colors, triangle array (`v2, v1, mat_id, v3`), morph targets, bounding sphere.
      - `MaterialList` (0x08): Material structs, textured materials with `Texture` (0x06) and 4-byte aligned `String` (0x02) chunks.
      - `BinMesh` (0x050E): Material splits with indexed triangle lists for hardware rendering efficiency.
    - `Atomic` (0x14): Links root frame to geometry with flags `rwATOMICRENDER | rwATOMICCOLLISION`.

### 2.3 RenderWare 3.6 TXD (`rw_txd.py`)
- Standard texture dictionary chunk `0x16` containing `NativeTexture` (0x15) chunks.
- Supports Direct3D 9 platform ID (9), D3DFMT_DXT1 (`0x31545844`), D3DFMT_DXT5 (`0x35545844`), and 32-bit RGBA.
- Writes full mipmap chains with per-level byte lengths.

### 2.4 GTA:SA Collision Format (`collision.py`)
- Standard **COL3** binary format:
  - Header: `COL3` FourCC, total size minus 8, 22-byte model name, model ID.
  - Bounding Box: 6 floats (`minX, minY, minZ, maxX, maxY, maxZ`).
  - Bounding Sphere: 4 floats (`centerX, centerY, centerZ, radius`).
  - Collision Boxes: Axis-aligned boxes with GTA SA surface material IDs (`TSurface`).
  - Collision Mesh: 16-bit fixed-point vertices (`int16(coord * 128.0)`) and indexed triangle faces with material types:
    - `COL_MAT_PAVEMENT` (5): Asphalt road surface.
    - `COL_MAT_CONCRETE` (1): Sidewalks, curbs, retaining walls, piers.
    - `COL_MAT_GRASS` (2): Lawns, medians, park terrain.
    - `COL_MAT_METAL` (6): Guardrails, light poles, dumpsters, towers.
    - `COL_MAT_WOOD` (20): Utility poles, porches, benches.

### 2.5 Automated LOD Chains (`lod.py`)
- Generates simplified low-poly bounding silhouette and envelope meshes (`_lod.dff`).
- Pairs primary objects with LOD objects in the streaming engine via `setLowLODElement(obj, lodObj)`.
- Near LOD distance: 120m – 300m; Far LOD distance: 800m – 2500m.

---

## 3. Procedural City Generation

### 3.1 Road Network Graph & Cross-Sections (`roads.py`, `intersections.py`)
- Directed road graph with explicit `RoadNode` and `RoadSegment` data structures.
- Spline curvature via cubic Bézier curves.
- Multi-lane cross-sections with raised concrete curbs (0.18m), gutters, and sidewalks.
- Diverse road classes:
  - **Grand Boulevard**: 4 lanes, grass/palm median, broad sidewalks.
  - **Downtown Arterial**: 4 lanes, parking lanes, high-density sidewalks.
  - **Commercial Avenue**: Multi-lane commercial street with turning bays.
  - **Residential Street**: Narrow 2-lane neighborhood street with curb ramps.
  - **Coastal Scenic Drive**: Curving coastal roadway descending to water level.
- 4-way signalized intersections with corner curb fillets and zebra pedestrian crosswalks.
- Circular roundabouts with landscaped central islands and circulating asphalt roadway.

### 3.2 Highways, Bridges & Tunnels (`highways.py`, `bridges.py`, `tunnels.py`)
- **Elevated Highways**: Concrete deck spans supported by heavy cylindrical pier bents and flanked by Jersey crash barriers.
- **Highway Ramps**: Curving, banked 1-2 lane connectors transitioning smoothly between ground-level arterials and elevated overpasses.
- **Bayside Viaduct Bridge**: Deep concrete water piers, structural deck, pedestrian walkway, and steel safety railings.
- **Mountain Tunnel Portal**: Massive concrete portal archway with wing retaining walls cut into hill terrain and an interior roadway tube.

### 3.3 23 American Building Archetypes (`buildings.py`)
Every archetype supports parametric dimensions, floors, facade styles, window grids, roof mechanicals, and deterministic variation:
1. `Modern Tower`: Tiered glass-and-steel skyscraper with spire.
2. `Glass Tower`: Reflective curtain-wall commercial skyscraper with entrance atrium.
3. `Office Tower`: Architectural stone and tinted glass corporate high-rise.
4. `Residential Tower`: High-rise condo tower with articulated balconies.
5. `Luxury Apartment`: 6-story mid-rise brick urban block with roof cornice.
6. `Suburban House`: American single-family home with pitched gable roof, porch, and attached garage.
7. `Townhouse`: 3-story urban rowhouse with entrance stoop.
8. `Motel`: 2-story American roadside motel with exterior catwalk corridors.
9. `Hotel`: 12-story urban hotel with portico entrance canopy.
10. `Shopping Center`: Retail complex with glass entrance atrium.
11. `Strip Mall`: Neighborhood retail strip with continuous pedestrian awning.
12. `Restaurant`: Freestanding fast-casual restaurant with drive-thru canopy.
13. `Diner`: American roadside diner with corrugated metal styling.
14. `Gas Station`: Multi-pump service canopy with convenience store.
15. `Warehouse`: Portal-frame logistics facility with loading docks.
16. `Factory`: Industrial manufacturing plant with twin smokestacks.
17. `Hospital`: Multi-wing medical center with ambulance bay canopy.
18. `School`: 2-story brick public school with entrance portico.
19. `Police Station`: Municipal law enforcement precinct with antenna mast.
20. `Fire Station`: Red brick firehouse with 3 apparatus bay doors and hose drying tower.
21. `Parking Garage`: 5-deck open-air concrete parking structure with stair core.
22. `Industrial Building`: Medium utilitarian workshop.
23. `Small Commercial Building`: Standalone retail shop / bank.

### 3.4 Props, Vegetation & Infrastructure (`props.py`, `vegetation.py`, `infrastructure.py`)
- **Props**: Fire hydrants, USPS blue mailboxes, wooden utility poles with crossarms and transformers, mast-arm traffic signals, commercial dumpsters, park benches, glass bus shelters, traffic signs (Stop, Interstate 95, Speed Limit 45), and W-beam guardrails.
- **Vegetation**: California fan palms, American broadleaf oaks, conical pines, manicured boxwood shrubs.
- **Infrastructure**: Cobra-head streetlights, high-voltage lattice steel power transmission towers.

---

## 4. Graphics Engine & Shader Pipeline (HLSL / DX9)

### 4.1 Advanced Road PBR (`road_pbr.fx`)
- Micro-surface roughness variation and normal perturbation.
- Dynamic wetness response:
  - Water saturation causes diffuse albedo darkening.
  - Surface roughness decreases from 0.82 (matte dry) to 0.15 (wet gloss).
  - Puddles pool based on puddle accumulation masks (`asphalt_puddle.dds`), creating mirror-like reflection pockets (roughness 0.02).
- Solar interaction:
  - Blinn-Phong specular glints from sun direction.
  - Fresnel reflection (Schlick approximation) reflecting sky ambient at grazing angles.
  - Golden hour warm highlights vs midday neutral glare.

### 4.2 Building Facades & Window Illumination (`building_facade.fx`)
- Glass reflections and specular highlights.
- Night window illumination modulated by `gNightFactor`:
  - Individual windows light up based on deterministic spatial hash.
  - Interior warm tungsten amber (~2800K) or cool office fluorescent (~4500K) illumination.

### 4.3 Screen-Space Sun Shafts / God Rays (`sun_shafts.fx`)
- Projects 3D solar position into normalized 2D screen coordinates.
- Samples screen buffer along 16 radial integration steps towards sun position.
- Blue noise dither map (`godray_dither.dds`) eliminates radial banding.
- Modulated by atmospheric fog, cloud coverage, and sun elevation.

### 4.4 Sky Atmosphere & Sun Disc (`sky_atmosphere.fx`)
- Realistic solar disc with core limb darkening (~0.5° angular diameter) and Mie scattering corona.
- Rayleigh scattering gradient: deep zenith blue transitioning to warm horizon scattering.
- Dual-layer scrolling cloud deck (`clouds_cumulus.dds`, `clouds_storm.dds`) illuminated by grazing golden sunlight at sunset.

### 4.5 Screen-Space Reflections (`ssr_reflection.fx`)
- Planar reflection approximation for wet asphalt, puddles, and glass.
- Roughness-dependent multi-tap blur.
- Screen edge fade prevents harsh boundary clipping.

### 4.6 Dynamic Drying System (`puddle_system.lua`)
- During rain: surface wetness accumulates rapidly, puddles pool progressively.
- When rain ceases (**POST_RAIN**):
  - Rain stops, but asphalt remains soaked.
  - Sunlight and wind drive evaporation: thin water film dries first, then deep puddles evaporate gradually.

---

## 5. In-Game Controls & Commands

| Command | Arguments | Description |
|---|---|---|
| `/citytp` | `[player]` | Teleports to Grand Boulevard in Downtown New American City `(0, 10, 5.5)` |
| `/cityweather` | `<clear\|partly_cloudy\|overcast\|light_rain\|heavy_rain\|storm\|fog\|post_rain>` | Triggers dynamic weather state transition |
| `/citytime` | `<hour> [minute]` | Sets synchronized in-game time (0–23) |
| `/cityquality` | `<low\|med\|high\|ultra>` | Toggles graphics presets and performance scaling |
| `/citydebug` | *(none)* | Toggles real-time engine telemetry HUD (or press **F7**) |

---

## 6. Build & Validation

The pipeline is 100% reproducible. To purge all generated assets, rebuild the city, and validate:

```bash
python3 run_pipeline.py --clean
```

The automated validator executes 81 structural tests across all assets:
- **[OK] META**: Validates XML structure and verifies all 243 files exist on disk.
- **[OK] LUA**: Parses all 10 Lua scripts using genuine LuaJIT syntax compiler.
- **[OK] HLSL**: Validates all 8 DirectX 9 shaders (techniques, passes, pixel/vertex shader entry points).
- **[OK] DDS**: Validates magic header, 124-byte header size, power-of-two dimensions, and DXT1/DXT5 FourCCs.
- **[OK] DFF**: Traverses RenderWare Clump hierarchy, verifies geometry, vertex/face counts, normals, UVs, and BinMesh plugins.
- **[OK] COL**: Validates COL3 FourCC, file size alignment, bounding volumes, and collision face indices.
