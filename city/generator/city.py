"""
city.py - Master Procedural City Generation Orchestrator
Coordinates texture synthesis, D3D9 TXD dictionary packaging, 3D RenderWare DFF clumps,
COL3 collision geometry, LOD proxies, spatial layout generation, and MTA:SA packaging.
Target origin: (-4076.83813, 492.02350, 161.42682).
"""

import os
import shutil
import json
from .textures import TextureSynthesizer
from .rw_txd import TXDBuilder
from .lod import generate_lod_mesh
from .ground import GroundCellFactory
from .buildings import BuildingFactory
from .infrastructure import InfrastructureFactory
from .props import PropFactory
from .vegetation import VegetationFactory
from .city_plan import CityPlanner, CITY_ORIGIN_X, CITY_ORIGIN_Y, CITY_ORIGIN_Z


class CityOrchestrator:
    def __init__(self, resource_dir="resource", seed=42, is_vertical_slice=False):
        self.resource_dir = resource_dir
        self.seed = seed
        self.is_vertical_slice = is_vertical_slice

        self.models_dir = os.path.join(resource_dir, "models")
        self.collisions_dir = os.path.join(resource_dir, "collisions")
        self.textures_dir = os.path.join(resource_dir, "textures")
        self.data_dir = os.path.join(resource_dir, "data")

        self.registered_models = {}

    def clean(self):
        """Removes previous build artifacts to guarantee reproducibility."""
        for d in [self.models_dir, self.collisions_dir, self.textures_dir, self.data_dir]:
            if os.path.exists(d):
                shutil.rmtree(d)
        for d in [self.models_dir, self.collisions_dir, self.textures_dir, self.data_dir]:
            os.makedirs(d, exist_ok=True)

    def generate_all(self):
        """Executes full end-to-end procedural generation pipeline."""
        print("==================================================")
        print("🚀 Starting Procedural American City Generation Pipeline")
        print(f"   Origin: ({CITY_ORIGIN_X:.3f}, {CITY_ORIGIN_Y:.3f}, {CITY_ORIGIN_Z:.3f})")
        print(f"   Seed:   {self.seed}")
        print("==================================================")

        # 1. Synthesize Procedural Textures (DDS + PNG)
        tex_synth = TextureSynthesizer(output_dir=self.textures_dir)
        generated_textures = tex_synth.generate_all()

        # 2. Package RenderWare 3.6 Direct3D 9 TXD (Master & Modular dictionaries)
        print("Packaging RenderWare Texture Dictionaries (city_textures.txd, city_ground.txd, city_bld.txd, city_infra.txd)...")
        ground_names = {'asphalt_road', 'asphalt_hwy', 'crosswalk', 'sidewalk_paver', 'curb_stone', 'grass_paver', 'concrete_wall', 'water_normal'}
        bld_names = {'glass_curtain_a', 'glass_curtain_b', 'bldg_brick', 'bldg_stone', 'roof_gravel', 'concrete_wall', 'metal_corrugated', 'storefront_atlas', 'neon_signs_atlas'}
        infra_names = {'asphalt_road', 'asphalt_hwy', 'concrete_wall', 'metal_corrugated', 'signs_atlas', 'tunnel_tiles', 'oak_leaves', 'palm_frond'}

        txd_master = TXDBuilder()
        txd_ground = TXDBuilder()
        txd_bld = TXDBuilder()
        txd_infra = TXDBuilder()

        for tex_name, pil_img in generated_textures.items():
            clean_name = tex_name.split('.')[0][:23]
            has_alpha = ("leaves" in tex_name or "frond" in tex_name)
            # Universal DXT1 format strictly conforming to GTA SA Direct3D 9 specifications
            fmt = "DXT1"

            txd_master.add_texture(clean_name, pil_img, fmt=fmt, has_alpha=has_alpha)
            if clean_name in ground_names:
                txd_ground.add_texture(clean_name, pil_img, fmt=fmt, has_alpha=has_alpha)
            if clean_name in bld_names:
                txd_bld.add_texture(clean_name, pil_img, fmt=fmt, has_alpha=has_alpha)
            if clean_name in infra_names:
                txd_infra.add_texture(clean_name, pil_img, fmt=fmt, has_alpha=has_alpha)

        txd_master.save(os.path.join(self.textures_dir, "city_textures.txd"))
        txd_ground.save(os.path.join(self.textures_dir, "city_ground.txd"))
        txd_bld.save(os.path.join(self.textures_dir, "city_bld.txd"))
        txd_infra.save(os.path.join(self.textures_dir, "city_infra.txd"))
        print(f"Native TXDs created successfully: master ({len(generated_textures)} textures), ground, buildings, infrastructure.")

        # 3. Generate All 3D Geometry (DFF + LOD + COL)
        print("Generating 3D ground cells, buildings, infrastructure, props, and vegetation...")
        self._generate_model_assets()

        # 4. Plan City Spatial Layout
        print("Synthesizing master urban layout and spatial database...")
        planner = CityPlanner(origin=(CITY_ORIGIN_X, CITY_ORIGIN_Y, CITY_ORIGIN_Z))
        instances, streetlights, pois = planner.plan_metropolis()

        # Save JSON Database
        layout_data = {
            'origin': [CITY_ORIGIN_X, CITY_ORIGIN_Y, CITY_ORIGIN_Z],
            'models': self.registered_models,
            'instances': instances,
            'streetlights': streetlights,
            'pois': pois
        }
        json_path = os.path.join(self.data_dir, "city_layout.json")
        with open(json_path, 'w') as f:
            json.dump(layout_data, f, indent=2)

        # 5. Export Lua Data Modules
        self._export_lua_data(layout_data)

        # 6. Build meta.xml
        self._build_meta_xml()

        print("==================================================")
        print(f"✨ Generation Complete!")
        print(f"   Registered Unique Models: {len(self.registered_models)}")
        print(f"   Placed World Instances:   {len(instances)}")
        print(f"   Dynamic Street Lights:    {len(streetlights)}")
        print(f"   Origin Coordinates:       ({CITY_ORIGIN_X:.3f}, {CITY_ORIGIN_Y:.3f}, {CITY_ORIGIN_Z:.3f})")
        print("==================================================")

    def _generate_model_assets(self):
        """Generates all unique models, saves DFF, LOD DFF, and COL3 files."""
        model_generators = [
            # Ground Blocks
            ("block_downtown", lambda: GroundCellFactory.create("block_downtown"), 350.0, 1800.0),
            ("block_plaza", lambda: GroundCellFactory.create("block_plaza"), 350.0, 1800.0),
            ("block_park", lambda: GroundCellFactory.create("block_park"), 350.0, 1800.0),
            ("block_industrial", lambda: GroundCellFactory.create("block_industrial"), 350.0, 1800.0),
            ("road_intersection", lambda: GroundCellFactory.create("road_intersection"), 300.0, 1500.0),
            ("road_straight", lambda: GroundCellFactory.create("road_straight"), 300.0, 1500.0),

            # Buildings
            ("bldg_glass_skyscraper", lambda: BuildingFactory.create("bldg_glass_skyscraper"), 450.0, 2400.0),
            ("bldg_art_deco_tower", lambda: BuildingFactory.create("bldg_art_deco_tower"), 450.0, 2200.0),
            ("bldg_corporate_hq", lambda: BuildingFactory.create("bldg_corporate_hq"), 400.0, 2000.0),
            ("bldg_luxury_hotel", lambda: BuildingFactory.create("bldg_luxury_hotel"), 380.0, 1800.0),
            ("bldg_residential_tower", lambda: BuildingFactory.create("bldg_residential_tower"), 380.0, 1800.0),
            ("bldg_brownstone_block", lambda: BuildingFactory.create("bldg_brownstone_block"), 300.0, 1400.0),
            ("bldg_commercial_strip", lambda: BuildingFactory.create("bldg_commercial_strip"), 280.0, 1400.0),
            ("bldg_american_diner", lambda: BuildingFactory.create("bldg_american_diner"), 260.0, 1200.0),
            ("bldg_parking_garage", lambda: BuildingFactory.create("bldg_parking_garage"), 320.0, 1600.0),
            ("bldg_logistics_warehouse", lambda: BuildingFactory.create("bldg_logistics_warehouse"), 350.0, 1600.0),
            ("bldg_factory_plant", lambda: BuildingFactory.create("bldg_factory_plant"), 380.0, 1800.0),
            ("bldg_power_substation", lambda: BuildingFactory.create("bldg_power_substation"), 280.0, 1400.0),
            ("bldg_city_hall", lambda: BuildingFactory.create("bldg_city_hall"), 380.0, 1800.0),
            ("bldg_police_station", lambda: BuildingFactory.create("bldg_police_station"), 280.0, 1400.0),
            ("bldg_fire_station", lambda: BuildingFactory.create("bldg_fire_station"), 280.0, 1400.0),
            ("bldg_hospital", lambda: BuildingFactory.create("bldg_hospital"), 380.0, 1800.0),
            ("bldg_gas_station", lambda: BuildingFactory.create("bldg_gas_station"), 280.0, 1400.0),

            # Civil Infrastructure
            ("highway_viaduct", lambda: InfrastructureFactory.create("highway_viaduct"), 400.0, 2000.0),
            ("highway_ramp", lambda: InfrastructureFactory.create("highway_ramp"), 350.0, 1800.0),
            ("cable_bridge", lambda: InfrastructureFactory.create("cable_bridge"), 600.0, 3000.0),
            ("tunnel_portal", lambda: InfrastructureFactory.create("tunnel_portal"), 400.0, 2000.0),

            # Props
            ("prop_streetlight_cobra", lambda: PropFactory.create("prop_streetlight_cobra"), 180.0, 600.0),
            ("prop_traffic_signal", lambda: PropFactory.create("prop_traffic_signal"), 180.0, 600.0),
            ("prop_fire_hydrant", lambda: PropFactory.create("prop_fire_hydrant"), 120.0, 400.0),
            ("prop_usps_mailbox", lambda: PropFactory.create("prop_usps_mailbox"), 120.0, 400.0),
            ("prop_bus_shelter", lambda: PropFactory.create("prop_bus_shelter"), 180.0, 600.0),
            ("prop_dumpster", lambda: PropFactory.create("prop_dumpster"), 150.0, 500.0),
            ("prop_park_bench", lambda: PropFactory.create("prop_park_bench"), 140.0, 450.0),
            ("prop_highway_sign", lambda: PropFactory.create("prop_highway_sign"), 250.0, 1000.0),

            # Botanical Vegetation
            ("veg_fan_palm", lambda: VegetationFactory.create("veg_fan_palm"), 220.0, 800.0),
            ("veg_oak_tree", lambda: VegetationFactory.create("veg_oak_tree"), 220.0, 800.0),
        ]

        for name, gen_fn, near_dist, far_dist in model_generators:
            mesh, col = gen_fn()

            dff_path = os.path.join(self.models_dir, f"{name}.dff")
            lod_dff_path = os.path.join(self.models_dir, f"{name}_lod.dff")
            col_path = os.path.join(self.collisions_dir, f"{name}.col")

            # 1. Save Primary DFF
            mesh.save(dff_path)

            # 2. Save LOD DFF
            lod_mesh = generate_lod_mesh(mesh)
            lod_mesh.save(lod_dff_path)

            # 3. Save COL3
            col.save(col_path)

            # Register
            self.registered_models[name] = {
                'dff': f"models/{name}.dff",
                'lod_dff': f"models/{name}_lod.dff",
                'col': f"collisions/{name}.col",
                'lod_distance': near_dist,
                'far_lod_distance': far_dist,
            }

    def _export_lua_data(self, layout_data):
        """Generates Lua layout and models files for fast client-side initialization."""
        models_lua = ["-- models.lua - Auto-generated Model Registry\nModelsRegistry = {\n"]
        for m_name, m_info in layout_data['models'].items():
            models_lua.append(f"    [\"{m_name}\"] = {{\n")
            models_lua.append(f"        dff = \"{m_info['dff']}\",\n")
            models_lua.append(f"        lod_dff = \"{m_info['lod_dff']}\",\n")
            models_lua.append(f"        col = \"{m_info['col']}\",\n")
            models_lua.append(f"        lod_distance = {m_info['lod_distance']},\n")
            models_lua.append(f"        far_lod_distance = {m_info['far_lod_distance']}\n")
            models_lua.append("    },\n")
        models_lua.append("}\n")

        with open(os.path.join(self.resource_dir, "client", "models.lua"), "w") as f:
            f.write("".join(models_lua))

        # layout.lua
        layout_lua = ["-- layout.lua - Auto-generated World Placements & POIs\nWorldLayout = {\n"]
        layout_lua.append(f"    origin = {{{layout_data['origin'][0]}, {layout_data['origin'][1]}, {layout_data['origin'][2]}}},\n")
        layout_lua.append("    pois = {\n")
        for p_name, p_pos in layout_data['pois'].items():
            layout_lua.append(f"        [\"{p_name}\"] = {{{p_pos[0]}, {p_pos[1]}, {p_pos[2]}}},\n")
        layout_lua.append("    },\n")
        layout_lua.append("    streetlights = {\n")
        for sl in layout_data['streetlights']:
            layout_lua.append(f"        {{ pos = {{{sl['pos'][0]}, {sl['pos'][1]}, {sl['pos'][2]}}}, color = {{{sl['color'][0]}, {sl['color'][1]}, {sl['color'][2]}}}, radius = {sl['radius']}, intensity = {sl['intensity']} }},\n")
        layout_lua.append("    }\n")
        layout_lua.append("}\n")

        with open(os.path.join(self.resource_dir, "client", "layout.lua"), "w") as f:
            f.write("".join(layout_lua))

    def _build_meta_xml(self):
        """Constructs valid MTA:SA resource manifest (meta.xml)."""
        lines = [
            '<meta>',
            '    <info author="Procedural City Engine" name="NewAmericanCity" type="script" version="2.0.0" />',
            '',
            '    <!-- Scripts -->',
            '    <script src="client/config.lua" type="client" />',
            '    <script src="client/models.lua" type="client" />',
            '    <script src="client/layout.lua" type="client" />',
            '    <script src="client/streaming.lua" type="client" />',
            '    <script src="client/renderer.lua" type="client" />',
            '    <script src="client/lighting.lua" type="client" />',
            '    <script src="client/environment.lua" type="client" />',
            '    <script src="client/weather.lua" type="client" />',
            '    <script src="client/puddle_system.lua" type="client" />',
            '    <script src="client/debug_ui.lua" type="client" />',
            '    <script src="client/main.lua" type="client" />',
            '    <script src="server/main.lua" type="server" />',
            '',
            '    <!-- Shaders -->',
        ]

        shaders_dir = os.path.join(self.resource_dir, "shaders")
        if os.path.exists(shaders_dir):
            for s_file in sorted(os.listdir(shaders_dir)):
                if s_file.endswith(".fx"):
                    lines.append(f'    <file src="shaders/{s_file}" />')

        lines.append('')
        lines.append('    <!-- Models (DFF) -->')
        if os.path.exists(self.models_dir):
            for m_file in sorted(os.listdir(self.models_dir)):
                if m_file.endswith(".dff"):
                    lines.append(f'    <file src="models/{m_file}" />')

        lines.append('')
        lines.append('    <!-- Collisions (COL) -->')
        if os.path.exists(self.collisions_dir):
            for c_file in sorted(os.listdir(self.collisions_dir)):
                if c_file.endswith(".col"):
                    lines.append(f'    <file src="collisions/{c_file}" />')

        lines.append('')
        lines.append('    <!-- Textures (TXD, DDS, PNG) -->')
        if os.path.exists(self.textures_dir):
            for t_file in sorted(os.listdir(self.textures_dir)):
                if t_file.endswith(".txd") or t_file.endswith(".dds") or t_file.endswith(".png"):
                    lines.append(f'    <file src="textures/{t_file}" />')

        lines.append('')
        lines.append('    <!-- Data -->')
        lines.append('    <file src="data/city_layout.json" />')
        lines.append('</meta>')

        meta_path = os.path.join(self.resource_dir, "meta.xml")
        with open(meta_path, 'w') as f:
            f.write("\n".join(lines) + "\n")
