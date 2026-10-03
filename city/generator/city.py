"""
city.py - Master Procedural City Generator & Pipeline Orchestrator
Coordinates terrain, roads, intersections, highways, bridges, tunnels,
districts, buildings, props, vegetation, materials, textures, collisions,
LODs, and packages the complete MTA:SA resource.
"""

import os
import sys
import shutil
import argparse
import numpy as np
from PIL import Image

from .textures import TextureSynthesizer
from .weather_assets import WeatherAssetGenerator
from .lighting_assets import LightingAssetGenerator
from .terrain import TerrainGenerator
from .roads import RoadNetworkGraph, RoadGeometryBuilder
from .intersections import IntersectionBuilder
from .highways import HighwayBuilder
from .bridges import BridgeBuilder
from .tunnels import TunnelBuilder
from .districts import CityZoningPlan
from .buildings import BuildingGenerator
from .props import PropsBuilder
from .vegetation import VegetationBuilder
from .infrastructure import InfrastructureBuilder
from .registry import AssetRegistry
from .export import ResourceExporter
from .rw_txd import TXDBuilder


class CityOrchestrator:
    def __init__(self, resource_dir="resource", seed=42, is_vertical_slice=True):
        self.resource_dir = resource_dir
        self.seed = seed
        self.is_vertical_slice = is_vertical_slice
        self.registry = AssetRegistry(start_model_id=1337)
        self.exporter = ResourceExporter(resource_dir)

    def clean(self):
        """Removes previously generated assets to ensure clean build."""
        for sub in ["models", "collisions", "textures", "data"]:
            p = os.path.join(self.resource_dir, sub)
            if os.path.exists(p):
                shutil.rmtree(p)
                os.makedirs(p, exist_ok=True)

    def generate_all(self):
        print("==================================================")
        print("🚀 Starting Procedural American City Generation Pipeline")
        print(f"   Target: {'Vertical Slice Test District' if self.is_vertical_slice else 'Full Metropolis'}")
        print(f"   Seed: {self.seed}")
        print("==================================================")

        np.random.seed(self.seed)

        # 1. Synthesize PBR textures and DDS files
        tex_dir = os.path.join(self.resource_dir, "textures")
        tex_synth = TextureSynthesizer(tex_dir)
        tex_synth.generate_all()

        weather_gen = WeatherAssetGenerator(tex_dir)
        weather_gen.generate_all()

        lighting_gen = LightingAssetGenerator(tex_dir)
        lighting_gen.generate_all()

        # Build unified TXD package for RenderWare
        print("Packaging RenderWare Texture Dictionaries (TXD)...")
        txd_builder = TXDBuilder()
        for t_file in os.listdir(tex_dir):
            if t_file.endswith('.png'):
                t_name = os.path.splitext(t_file)[0]
                t_img = Image.open(os.path.join(tex_dir, t_file))
                fmt = 'DXT5' if t_img.mode == 'RGBA' and 'frond' in t_name or 'leaves' in t_name or 'droplets' in t_name else 'DXT1'
                txd_builder.add_texture(t_name, t_img, fmt)
        txd_builder.save(os.path.join(tex_dir, "city_textures.txd"))

        # 2. Build Terrain Chunks
        print("Generating 3D terrain and topography...")
        terrain_gen = TerrainGenerator(origin_x=0.0, origin_y=0.0)
        # 4 quadrant chunks around urban center
        chunks = [
            ("terrain_sw", -300.0, -300.0, 0.0, 0.0),
            ("terrain_se", 0.0, -300.0, 300.0, 0.0),
            ("terrain_nw", -300.0, 0.0, 0.0, 300.0),
            ("terrain_ne", 0.0, 0.0, 300.0, 300.0),
        ]
        for c_name, min_x, min_y, max_x, max_y in chunks:
            mesh, col, lod = terrain_gen.generate_chunk_mesh(min_x, min_y, max_x, max_y, grid_res=12)
            self._save_asset(c_name, mesh, col, lod, category="terrain", lod_dist=300.0, far_lod=2500.0)
            self.registry.add_instance(c_name, 0.0, 0.0, 0.0, district="terrain")

        # 3. Build Road Network Graph & Geometry
        print("Synthesizing Road Network Graph & road corridors...")
        road_graph = RoadNetworkGraph()
        # Key Nodes
        road_graph.add_node("n_downtown_center", (0.0, 0.0, 4.5), "intersection")
        road_graph.add_node("n_downtown_north", (0.0, 160.0, 5.0), "intersection")
        road_graph.add_node("n_downtown_south", (0.0, -160.0, 4.2), "intersection")
        road_graph.add_node("n_commercial_east", (160.0, 0.0, 6.0), "intersection")
        road_graph.add_node("n_coastal_west", (-180.0, 0.0, 2.5), "intersection")
        road_graph.add_node("n_suburbs_roundabout", (260.0, 140.0, 12.0), "roundabout")

        # Road Segments
        # Downtown Grand Boulevard (North-South, 4 lanes with median, wide sidewalks)
        seg_bvd_s = road_graph.add_segment("rd_downtown_bvd_s", "n_downtown_south", "n_downtown_center",
                                           road_class="boulevard", lanes=4, width=18.0, speed_class=35)
        seg_bvd_n = road_graph.add_segment("rd_downtown_bvd_n", "n_downtown_center", "n_downtown_north",
                                           road_class="boulevard", lanes=4, width=18.0, speed_class=35)

        # Commercial Avenue (East-West)
        seg_comm = road_graph.add_segment("rd_commercial_ave", "n_downtown_center", "n_commercial_east",
                                          road_class="arterial_downtown", lanes=4, width=16.0, speed_class=35)

        # Coastal Scenic Drive (curving gently down to coast)
        seg_coast = road_graph.add_segment("rd_coastal_drive", "n_coastal_west", "n_downtown_center",
                                           road_class="coastal", lanes=2, width=12.0, speed_class=30,
                                           control_points=[(-90.0, -35.0, 3.2)])

        # Suburbs Climbing Road (curving up into eastern hills)
        seg_suburbs = road_graph.add_segment("rd_suburbs_climb", "n_commercial_east", "n_suburbs_roundabout",
                                             road_class="residential", lanes=2, width=10.0, speed_class=25,
                                             control_points=[(210.0, 50.0, 8.5)])

        for seg in [seg_bvd_s, seg_bvd_n, seg_comm, seg_coast, seg_suburbs]:
            mesh, col, lod = RoadGeometryBuilder.build_segment_geometry(seg, sample_res=16)
            self._save_asset(seg.id, mesh, col, lod, category="road", lod_dist=250.0, far_lod=1800.0)
            self.registry.add_instance(seg.id, 0.0, 0.0, 0.0, district="road")

        # 4. Intersections & Roundabouts
        print("Generating signalized intersections & roundabouts...")
        mesh_4w, col_4w, lod_4w = IntersectionBuilder.build_4way_intersection("int_downtown_main", (0.0, 0.0, 4.5), road_width=18.0)
        self._save_asset("int_downtown_main", mesh_4w, col_4w, lod_4w, category="intersection")
        self.registry.add_instance("int_downtown_main", 0.0, 0.0, 0.0, district="downtown")

        mesh_rb, col_rb, lod_rb = IntersectionBuilder.build_roundabout("roundabout_suburbs", (260.0, 140.0, 12.0), inner_radius=8.0, roadway_width=9.0)
        self._save_asset("roundabout_suburbs", mesh_rb, col_rb, lod_rb, category="intersection")
        self.registry.add_instance("roundabout_suburbs", 0.0, 0.0, 0.0, district="residential")

        # 5. Elevated Highway & Ramps
        print("Generating elevated highway overpass & interchange ramps...")
        mesh_hw, col_hw, lod_hw = HighwayBuilder.build_elevated_span(
            "hw_elevated_span",
            start_pos=(-120.0, -220.0, 12.5),
            end_pos=(180.0, -220.0, 12.5),
            width=24.0, height_clearance=8.0
        )
        self._save_asset("hw_elevated_span", mesh_hw, col_hw, lod_hw, category="highway", lod_dist=280.0, far_lod=2000.0)
        self.registry.add_instance("hw_elevated_span", 0.0, 0.0, 0.0, district="highway")

        # Highway off-ramp connecting to surface street
        mesh_ramp, col_ramp, lod_ramp = HighwayBuilder.build_ramp(
            "hw_exit_ramp",
            start_ground=(0.0, -160.0, 4.2),
            end_elevated=(60.0, -220.0, 12.5),
            width=7.5,
            control_pt=(25.0, -200.0, 7.5)
        )
        self._save_asset("hw_exit_ramp", mesh_ramp, col_ramp, lod_ramp, category="highway", lod_dist=250.0, far_lod=1800.0)
        self.registry.add_instance("hw_exit_ramp", 0.0, 0.0, 0.0, district="highway")

        # 6. Viaduct Bridge & Tunnel Portal
        print("Generating water viaduct bridge & mountain tunnel portal...")
        mesh_br, col_br, lod_br = BridgeBuilder.build_viaduct_bridge(
            "bridge_bayside_viaduct",
            start_pos=(-180.0, 0.0, 2.5),
            end_pos=(-290.0, -80.0, 2.5),
            width=18.0, pier_depth=10.0
        )
        self._save_asset("bridge_bayside_viaduct", mesh_br, col_br, lod_br, category="bridge", lod_dist=300.0, far_lod=2200.0)
        self.registry.add_instance("bridge_bayside_viaduct", 0.0, 0.0, 0.0, district="coastal")

        mesh_tun, col_tun, lod_tun = TunnelBuilder.build_tunnel_portal(
            "tunnel_heights_portal",
            position=(260.0, 140.0, 12.0),
            direction_angle=np.pi * 0.25,
            road_width=12.0, height=6.5
        )
        self._save_asset("tunnel_heights_portal", mesh_tun, col_tun, lod_tun, category="tunnel")
        self.registry.add_instance("tunnel_heights_portal", 0.0, 0.0, 0.0, district="hills")

        # 7. Generate and Place Buildings across All Districts
        print("Generating all 23 building archetypes and urban districts...")
        all_archetypes = [
            "Modern Tower", "Glass Tower", "Office Tower", "Residential Tower",
            "Luxury Apartment", "Suburban House", "Townhouse", "Motel", "Hotel",
            "Shopping Center", "Strip Mall", "Restaurant", "Diner", "Gas Station",
            "Warehouse", "Factory", "Hospital", "School", "Police Station",
            "Fire Station", "Parking Garage", "Industrial Building", "Small Commercial Building"
        ]

        # Generate each unique archetype asset
        for arch in all_archetypes:
            clean_name = "bldg_" + arch.lower().replace(" ", "_")
            mesh_b, col_b, lod_b = BuildingGenerator.generate(arch, seed=hash(arch) % 1000)
            self._save_asset(clean_name, mesh_b, col_b, lod_b, category="building", lod_dist=200.0, far_lod=1600.0)

        # Place Downtown Towers
        self.registry.add_instance("bldg_modern_tower", 45.0, 45.0, 4.6, rz=0.0, district="downtown")
        self.registry.add_instance("bldg_glass_tower", -45.0, 45.0, 4.6, rz=90.0, district="downtown")
        self.registry.add_instance("bldg_office_tower", 45.0, -45.0, 4.5, rz=180.0, district="downtown")
        self.registry.add_instance("bldg_hotel", -45.0, -45.0, 4.4, rz=270.0, district="downtown")
        self.registry.add_instance("bldg_parking_garage", 95.0, 45.0, 5.0, rz=0.0, district="downtown")

        # Place Commercial District Buildings
        self.registry.add_instance("bldg_shopping_center", 45.0, 110.0, 5.0, rz=0.0, district="commercial")
        self.registry.add_instance("bldg_strip_mall", -45.0, 110.0, 4.9, rz=0.0, district="commercial")
        self.registry.add_instance("bldg_restaurant", 95.0, 110.0, 5.2, rz=90.0, district="commercial")
        self.registry.add_instance("bldg_diner", -95.0, 110.0, 4.7, rz=270.0, district="commercial")
        self.registry.add_instance("bldg_motel", 135.0, 110.0, 5.4, rz=0.0, district="commercial")
        self.registry.add_instance("bldg_small_commercial_building", -135.0, 110.0, 4.5, rz=0.0, district="commercial")
        self.registry.add_instance("bldg_gas_station", 0.0, 125.0, 5.0, rz=0.0, district="commercial")

        # Place Residential & Suburbs
        self.registry.add_instance("bldg_residential_tower", 140.0, -45.0, 5.5, rz=0.0, district="residential")
        self.registry.add_instance("bldg_luxury_apartment", 185.0, -45.0, 6.0, rz=0.0, district="residential")
        self.registry.add_instance("bldg_townhouse", 185.0, 0.0, 6.2, rz=90.0, district="residential")
        self.registry.add_instance("bldg_suburban_house", 220.0, 80.0, 9.5, rz=45.0, district="residential")
        self.registry.add_instance("bldg_suburban_house", 250.0, 95.0, 11.0, rz=30.0, district="residential")

        # Place Industrial District
        self.registry.add_instance("bldg_warehouse", -45.0, -110.0, 4.0, rz=0.0, district="industrial")
        self.registry.add_instance("bldg_factory", 45.0, -110.0, 4.1, rz=0.0, district="industrial")
        self.registry.add_instance("bldg_industrial_building", -95.0, -110.0, 3.8, rz=90.0, district="industrial")

        # Place Civic District
        self.registry.add_instance("bldg_hospital", 140.0, 180.0, 6.5, rz=0.0, district="civic")
        self.registry.add_instance("bldg_police_station", 185.0, 180.0, 7.0, rz=0.0, district="civic")
        self.registry.add_instance("bldg_fire_station", 225.0, 180.0, 7.5, rz=0.0, district="civic")
        self.registry.add_instance("bldg_school", 140.0, 230.0, 7.2, rz=0.0, district="civic")

        # 8. American Props & Street Infrastructure
        print("Generating street furniture, signs, traffic lights, and utility poles...")
        props = [
            ("prop_hydrant", PropsBuilder.build_fire_hydrant()),
            ("prop_mailbox", PropsBuilder.build_mailbox()),
            ("prop_utility_pole", PropsBuilder.build_utility_pole()),
            ("prop_traffic_signal", PropsBuilder.build_traffic_signal()),
            ("prop_dumpster", PropsBuilder.build_dumpster()),
            ("prop_bench", PropsBuilder.build_street_bench()),
            ("prop_bus_shelter", PropsBuilder.build_bus_shelter()),
            ("prop_traffic_sign", PropsBuilder.build_traffic_sign()),
            ("prop_guardrail", PropsBuilder.build_guardrail_segment()),
        ]
        for p_name, (mesh_p, col_p, lod_p) in props:
            self._save_asset(p_name, mesh_p, col_p, lod_p, category="prop", lod_dist=120.0, far_lod=800.0)

        # Place props along downtown intersections and sidewalks
        self.registry.add_instance("prop_traffic_signal", 10.0, 10.0, 4.68, rz=0.0, district="downtown")
        self.registry.add_instance("prop_traffic_signal", -10.0, -10.0, 4.68, rz=180.0, district="downtown")
        self.registry.add_instance("prop_hydrant", 9.5, 14.0, 4.68, district="downtown")
        self.registry.add_instance("prop_mailbox", -9.5, 14.0, 4.68, district="downtown")
        self.registry.add_instance("prop_bench", 10.0, 25.0, 4.68, rz=90.0, district="downtown")
        self.registry.add_instance("prop_bus_shelter", -10.0, 35.0, 4.68, rz=270.0, district="downtown")
        self.registry.add_instance("prop_traffic_sign", 9.5, -14.0, 4.68, district="downtown")
        self.registry.add_instance("prop_dumpster", 30.0, -35.0, 4.5, district="downtown")
        self.registry.add_instance("prop_guardrail", 12.0, -210.0, 4.2, rz=0.0, district="highway")

        # 9. Vegetation (Palms, Oaks, Pines, Shrubs)
        print("Generating botanical models & urban green spaces...")
        veg = [
            ("veg_palm_tree", VegetationBuilder.build_palm_tree()),
            ("veg_oak_tree", VegetationBuilder.build_oak_tree()),
            ("veg_pine_tree", VegetationBuilder.build_pine_tree()),
            ("veg_shrub", VegetationBuilder.build_shrub()),
        ]
        for v_name, (mesh_v, col_v, lod_v) in veg:
            self._save_asset(v_name, mesh_v, col_v, lod_v, category="vegetation", lod_dist=150.0, far_lod=1000.0)

        # Place palm trees along Grand Boulevard sidewalk
        for y_pos in [-120.0, -80.0, -40.0, 40.0, 80.0, 120.0]:
            self.registry.add_instance("veg_palm_tree", -10.5, y_pos, 4.7, rz=float(hash(y_pos) % 360), district="downtown")
            self.registry.add_instance("veg_palm_tree", 10.5, y_pos, 4.7, rz=float(hash(y_pos + 1) % 360), district="downtown")

        # Place oaks in suburbs
        self.registry.add_instance("veg_oak_tree", 205.0, 75.0, 9.2, district="residential")
        self.registry.add_instance("veg_oak_tree", 235.0, 90.0, 10.5, district="residential")
        self.registry.add_instance("veg_pine_tree", 270.0, 120.0, 12.2, district="hills")
        self.registry.add_instance("veg_shrub", 10.0, 20.0, 4.68, district="downtown")

        # 10. Infrastructure & Street Lights
        print("Generating street lighting network & power infrastructure...")
        infra = [
            ("infra_streetlight_cobra", InfrastructureBuilder.build_cobra_streetlight()),
            ("infra_power_tower", InfrastructureBuilder.build_power_tower()),
        ]
        for inf_name, (mesh_i, col_i, lod_i) in infra:
            self._save_asset(inf_name, mesh_i, col_i, lod_i, category="infrastructure", lod_dist=180.0, far_lod=1200.0)

        # Place streetlights along the boulevard and register dynamic lights
        for y_pos in [-140.0, -100.0, -60.0, -20.0, 20.0, 60.0, 100.0, 140.0]:
            # West side streetlight (cool LED)
            self.registry.add_instance("infra_streetlight_cobra", -10.2, y_pos, 4.68, rz=90.0, district="downtown")
            self.registry.add_streetlight(-7.4, y_pos, 4.68 + 9.5, light_type="led", intensity=1.0, radius=22.0)

            # East side streetlight (warm sodium)
            self.registry.add_instance("infra_streetlight_cobra", 10.2, y_pos, 4.68, rz=270.0, district="downtown")
            self.registry.add_streetlight(7.4, y_pos, 4.68 + 9.5, light_type="sodium", intensity=1.0, radius=22.0)

        # Power towers
        self.registry.add_instance("infra_power_tower", -150.0, -280.0, 3.5, district="industrial")
        self.registry.add_instance("infra_power_tower", 150.0, -280.0, 3.8, district="industrial")

        # 11. Export Layout Database and meta.xml
        print("Exporting spatial layout JSON database...")
        layout_path = os.path.join(self.resource_dir, "data", "city_layout.json")
        total_inst = self.registry.export_layout_json(layout_path)

        print("Building MTA:SA resource manifest (meta.xml)...")
        meta_path = self.exporter.generate_meta_xml(self.registry)

        print("==================================================")
        print("✨ Generation Complete!")
        print(f"   Registered Unique Models: {len(self.registry.models)}")
        print(f"   Placed World Instances:   {total_inst}")
        print(f"   Dynamic Street Lights:    {len(self.registry.streetlights)}")
        print(f"   Manifest:                 {meta_path}")
        print("==================================================")

    def _save_asset(self, name, mesh, col, lod, category="general", lod_dist=200.0, far_lod=1500.0):
        """Saves DFF, LOD DFF, and COL files and registers them."""
        dff_path = os.path.join(self.resource_dir, "models", f"{name}.dff")
        lod_path = os.path.join(self.resource_dir, "models", f"{name}_lod.dff")
        col_path = os.path.join(self.resource_dir, "collisions", f"{name}.col")

        mesh.save(dff_path)
        lod.save(lod_path)
        col.save(col_path)

        self.registry.register_model(name, category, lod_distance=lod_dist, far_lod_distance=far_lod)


def main():
    parser = argparse.ArgumentParser(description="Procedural American City Generator for MTA:SA")
    parser.add_argument("--vertical-slice", action="store_true", default=True, help="Build complete vertical slice test area")
    parser.add_argument("--full-city", action="store_true", help="Expand procedural generation to full city")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed")
    parser.add_argument("--output", type=str, default="resource", help="Output MTA:SA resource directory")
    parser.add_argument("--clean", action="store_true", help="Clean output folders before generation")
    args = parser.parse_args()

    orchestrator = CityOrchestrator(
        resource_dir=args.output,
        seed=args.seed,
        is_vertical_slice=not args.full_city
    )

    if args.clean:
        orchestrator.clean()

    orchestrator.generate_all()


if __name__ == "__main__":
    main()
