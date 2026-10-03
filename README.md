# New American City — Graphics Engine & Procedural Asset Pipeline for MTA:SA

An authentic, fully procedural American metropolis generation system and DirectX 9 mini-graphics engine built entirely from scratch for **Multi Theft Auto: San Andreas (MTA:SA)**.

---

## 📍 Geographic Location & In-Game Origin

The procedural metropolis is centered at:
- **X = -4076.83813**
- **Y = 492.02350**
- **Z = 161.42682**

Use `/citytp` in-game to teleport directly to the city center.

---

## 🌟 Key Features

- **Procedural City Architecture**:
  - **Ground Blocks & Road Network**: Seamless 80m x 80m ground cells with 4-lane asphalt avenues, painted zebra crosswalks, stop bars, 0.16m raised concrete curbs with chamfered corner ramps, and sidewalk paving slabs.
  - **17 Architectural Archetypes**:
    - **Downtown Financial District**: 120m Modern Glass Skyscraper (3 setbacks, helipad, antenna mast), 95m Art Deco Tower (stepped crown, limestone facade, copper spire), 85m Corporate HQ, 65m Luxury Hotel (grand canopy, neon marquee).
    - **Midtown Commercial Corridor**: 2-story Retail Shopping Strip (Deli, Coffee Shop, Diner, Pharmacy), 1950s American Retro Diner, 4-level Concrete Parking Garage, Roadside Gas Station with 8-pump canopy.
    - **Uptown Residential & Civic**: 4-story Classic Brick Brownstones with front stoops, 75m Residential Apartment High-Rise with balconies, Neoclassical City Hall with columned portico and clock tower, Municipal Police Station, 2-bay Fire Station, 6-story Hospital Center with ambulance bay and helipad.
    - **Industrial & Power District**: Logistics Warehouse with 6 freight loading docks, Factory Plant with dual tall smokestacks, High-Voltage Electrical Substation.
  - **Major Civil Infrastructure**:
    - 4-Lane Elevated Expressway Viaduct (Z=12m) with Jersey crash barriers and heavy concrete pier bents.
    - 80m Curved Highway Interchange Ramp connecting surface street to elevated viaduct.
    - 120m Cable-Stayed Suspension Bridge with 55m concrete A-frame pylon towers and illuminated stay cables.
    - Mountain Cut-and-Cover Tunnel Portal with ceramic-tiled interior tube.
  - **Street Furniture & Botanical Foliage**:
    - Cobra-head streetlights with realistic color temperatures (sodium amber and cool LED).
    - Traffic signal gantries with 3-aspect signal heads.
    - Cast iron fire hydrants, USPS blue mailboxes, transit bus shelters, waste dumpsters, and park benches.
    - California fan palms (*Washingtonia robusta*) and American broadleaf oak trees with alpha canopy.

- **Flawless Texture & Rendering Pipeline (Eliminating White Models)**:
  - **Direct3D 9 TXD Binary Conformance**:
    - `deviceId = 9` (D3D9 PC).
    - Exact 88-byte `RpRasterPC_Header`: `rasterFormat = 0x8200` (`RASTER_565 | RASTER_MIPMAP`) for DXT1, `0x8100` (`RASTER_1555 | RASTER_MIPMAP`) for 1-bit alpha punchthrough.
    - `filter_and_addressing = 0x1106` (linear-mip-linear with wrap/wrap).
    - Full 10-level mipmap chains down to 1x1 with exact D3D sub-4px block sizing (8 bytes for 2x2 and 1x1).
    - Texture names strictly <= 23 characters (padded with null bytes to 32 bytes).
    - Modular TXD dictionaries (`city_ground.txd`, `city_bld.txd`, `city_infra.txd`) alongside master `city_textures.txd` to prevent single-dictionary memory allocation caps.
  - **RenderWare 3.6 DFF Binary Conformance**:
    - `flags = (1 << 16) | FLAG_POSITIONS | FLAG_TEXTURED | FLAG_PRELIT | FLAG_NORMALS | FLAG_MODULATE`.
    - CCW triangle winding: `(v1, v0, mat_id, v2)`.
    - Texture chunk filter and wrap header: `b'\x06\x11\x00\x00'`.
    - BinMesh PLG chunk `0x050E` properly grouping triangles by material.
  - **Baked Prelit Vertex Lighting (`bake.py`)**:
    - Computes cool skylight ambient, street canyon height falloff, emissive window/sign surfaces, and local point light falloffs from streetlamps onto street/curb/sidewalk vertices.
  - **Dual Texture Delivery in Resource**:
    - Both `.dds` and `.png` textures are packaged in `resource/textures/`.
    - Paired Vertex & Pixel Shaders in `tex_diffuse.fx` guarantee immediate texture projection via `engineApplyShaderToWorldTexture`.

- **DirectX 9 Graphics Engine (HLSL Shaders)**:
  - Compact SM 2.0 fallback passes (< 35 instructions) and full SM 3.0 passes to prevent instruction slot limit errors (`ps_2_0` max 64 instructions).
  - `road_pbr.fx`: Dynamic asphalt darkening, puddle accumulation, tire wear, and sun specular glints.
  - `building_facade.fx`: Architectural glass reflections and deterministic night window illumination.
  - `sun_shafts.fx`: Screen-space God Rays / Light Shafts with dithered sampling.
  - `sky_atmosphere.fx`: Rayleigh/Mie atmospheric scattering, dynamic sun disc, and scrolling clouds.
  - `ssr_reflection.fx`: Screen-space reflections for wet roads, puddles, and glass.
  - `water_surface.fx`: Dual-scrolling wave ripples, Fresnel reflection, and depth absorption.
  - `street_light.fx`: Volumetric light cones and color-temperature halos.
  - `rain_screen.fx`: Refractive camera lens water droplets.

- **Dynamic Environment & Weather**:
  - 24-hour astronomical Day/Night cycle.
  - Dynamic Weather States: `CLEAR`, `PARTLY_CLOUDY`, `OVERCAST`, `LIGHT_RAIN`, `HEAVY_RAIN`, `STORM`, `FOG`, `MIST`, `POST_RAIN`.
  - Dynamic Drying System: surfaces stay soaked after rain stops, then evaporate gradually under sunlight.
  - Rare lightning events with distant thunder in storms.

---

## 🚀 Quick Start & Building

### 1. Run the Entire Pipeline
To generate all textures, models, collisions, and package the complete MTA:SA resource:

```bash
python3 run_pipeline.py --clean
```

### 2. Run Validation Suite Separately
To verify integrity of all generated assets and scripts:

```bash
python3 -m city.generator.validator
```

### 3. Deploying to MTA:SA
Copy the `resource/` directory to your MTA:SA server's `server/mods/deathmatch/resources/` directory (e.g. rename to `newcity`) and run `start newcity` in server console.

---

## 🎮 In-Game Commands

- `/citytp [location]`: Teleports you directly to any city location:
  - `center` or `spawn` or `plaza`: Downtown Central Plaza `(-4076.838, 492.024, 162.6)`
  - `downtown`: Financial District Skyscraper `(-4076.838, 572.024, 162.6)`
  - `hotel`: Luxury Hotel Corridor `(-4076.838, 412.024, 162.6)`
  - `waterfront`: Waterfront Promenade `(-4076.838, 672.024, 162.6)`
  - `bridge`: Cable-Stayed Suspension Bridge Deck `(-4076.838, 732.024, 176.6)`
  - `expressway`: Elevated Expressway Viaduct `(-3876.838, 492.024, 174.6)`
  - `tunnel`: Mountain Tunnel Portal Entrance `(-4076.838, 292.024, 162.6)`
  - `industrial`: Maritime Logistics & Factory Yard `(-3956.838, 372.024, 162.6)`
  - `park`: Central Park Walkways & Trees `(-4156.838, 652.024, 162.6)`
  - `cityhall`: Civic Center & Municipal Hall `(-4236.838, 652.024, 162.6)`
- `/cityweather <type>`: Changes dynamic weather (e.g. `/cityweather storm`, `/cityweather post_rain`).
- `/citytime <hour> [minute]`: Sets synchronized server time (e.g. `/citytime 18 30` for Sunset).
- `/cityquality <preset>`: Toggles performance preset (`low`, `med`, `high`, `ultra`).
- `/citydebug` or **F7**: Toggles the real-time engine telemetry HUD.
