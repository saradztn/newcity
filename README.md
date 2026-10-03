# New American City — Graphics Engine & Procedural Asset Pipeline for MTA:SA

An authentic, fully procedural American city generation system and DirectX 9 mini-graphics engine built entirely from scratch for **Multi Theft Auto: San Andreas (MTA:SA)**.

---

## 🌟 Key Features

- **Procedural City Generator in Python**:
  - Generates realistic roads, highways, bridges, tunnels, intersections, roundabouts, and multi-elevation terrain.
  - Generates **23 American building archetypes** (Modern Tower, Glass Tower, Office Tower, Suburban House, Townhouse, Diner, Gas Station, Hospital, Fire Station, etc.).
  - Generates authentic street props (traffic lights, hydrants, USPS mailboxes, utility poles, dumpsters, benches, bus shelters, guardrails).
  - Generates California fan palms, American oaks, pines, and shrubs.
- **Native Binary Encoders**:
  - **RenderWare 3.6 DFF** Clump binary encoder with BinMesh optimization, materials, and vertex normals.
  - **RenderWare 3.6 TXD** Texture Dictionary encoder.
  - **GTA:SA COL3** Collision binary generator with exact bounding boxes, bounding spheres, and material surfaces.
  - **LOD Generation**: Simplified envelope models with automatic pairing via `setLowLODElement`.
  - **DDS Compression**: Vectorized DXT1 (BC1) and DXT5 (BC3) block compressor with full mipmap pyramids.
- **DirectX 9 Graphics Engine (HLSL Shaders)**:
  - `road_pbr.fx`: Dynamic asphalt darkening, puddle accumulation, micro-cracks, tire wear, and sun specular glints.
  - `building_facade.fx`: Architectural glass reflections and deterministic night window illumination.
  - `sun_shafts.fx`: Screen-space God Rays / Light Shafts with dithered sampling.
  - `sky_atmosphere.fx`: Rayleigh/Mie atmospheric scattering, dynamic sun disc with limb darkening, and scrolling cloud decks.
  - `ssr_reflection.fx`: Screen-space reflections for wet roads, puddles, and glass.
  - `water_surface.fx`: Dual-scrolling wave ripples, Fresnel reflection, and depth color absorption.
  - `street_light.fx`: Volumetric light cones and color-temperature halos (sodium amber, halogen, cool LED).
  - `rain_screen.fx`: Refractive camera lens water droplets.
- **Dynamic Environment & Weather**:
  - 24-hour Day/Night cycle (Dawn, Sunrise, Morning, Midday, Afternoon, Golden Hour, Sunset, Blue Hour, Night).
  - Weather Director: `CLEAR`, `PARTLY_CLOUDY`, `OVERCAST`, `LIGHT_RAIN`, `HEAVY_RAIN`, `STORM`, `FOG`, `MIST`, `POST_RAIN`.
  - Dynamic Drying System: surfaces stay soaked after rain stops, then evaporate gradually under sunlight.
  - Rare lightning events with distant thunder in storms.
- **Quality Presets**: `LOW`, `MEDIUM`, `HIGH`, `ULTRA` scalable for all hardware.
- **Automated Validation Suite**: Deep structural checks on DFF, TXD, COL, DDS, Lua, Shaders, and `meta.xml`.

---

## 🚀 Quick Start & Building

### 1. Run the Entire Pipeline
To generate all textures, models, collisions, and package the complete MTA:SA resource:

```bash
python3 run_pipeline.py --clean
```

### 2. Run Validation Suite Separately
To verify integrity of all 243 assets and scripts:

```bash
python3 -m city.generator.validator
```

### 3. Deploying to MTA:SA
Copy the `resource/` directory to your MTA:SA server's `server/mods/deathmatch/resources/` directory (e.g. rename to `newcity`) and run `start newcity` in server console.

---

## 🎮 In-Game Commands

- `/citytp`: Teleports you directly to Grand Boulevard in the Downtown Core.
- `/cityweather <type>`: Changes dynamic weather (e.g. `/cityweather storm`, `/cityweather post_rain`).
- `/citytime <hour> [minute]`: Sets synchronized server time (e.g. `/citytime 18 30` for Sunset).
- `/cityquality <preset>`: Toggles performance preset (`low`, `med`, `high`, `ultra`).
- `/citydebug` or **F7**: Toggles the real-time engine telemetry HUD.

---

## 📊 Technical Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for full format specifications, shader mathematics, and procedural algorithms.
