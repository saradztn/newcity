"""
export.py - Resource Packaging & MTA:SA Deployment Pipeline
Generates meta.xml, exports textures, models, collisions, and layout data
into a self-contained, fully runnable MTA:SA resource package.
"""

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom


class ResourceExporter:
    def __init__(self, resource_root):
        self.resource_root = resource_root
        os.makedirs(os.path.join(resource_root, "models"), exist_ok=True)
        os.makedirs(os.path.join(resource_root, "collisions"), exist_ok=True)
        os.makedirs(os.path.join(resource_root, "textures"), exist_ok=True)
        os.makedirs(os.path.join(resource_root, "shaders"), exist_ok=True)
        os.makedirs(os.path.join(resource_root, "client"), exist_ok=True)
        os.makedirs(os.path.join(resource_root, "server"), exist_ok=True)
        os.makedirs(os.path.join(resource_root, "data"), exist_ok=True)

    def generate_meta_xml(self, registry):
        """Builds clean, valid meta.xml containing all scripts, shaders, models, textures."""
        root = ET.Element("meta")

        # Resource Info
        info = ET.SubElement(root, "info")
        info.set("author", "MTA Technical Artist / Graphics Pipeline")
        info.set("name", "NewAmericanCity")
        info.set("description", "Next-Gen Procedural American City & Dynamic Environment Graphics Engine")
        info.set("version", "2.0.0")
        info.set("type", "script")

        # Server Scripts
        s_main = ET.SubElement(root, "script")
        s_main.set("src", "server/main.lua")
        s_main.set("type", "server")

        # Client Scripts (in load dependency order)
        client_scripts = [
            "client/config.lua",
            "client/environment.lua",
            "client/weather.lua",
            "client/puddle_system.lua",
            "client/renderer.lua",
            "client/streaming.lua",
            "client/lighting.lua",
            "client/debug_ui.lua",
            "client/main.lua",
        ]
        for cs in client_scripts:
            s_elem = ET.SubElement(root, "script")
            s_elem.set("src", cs)
            s_elem.set("type", "client")

        # Data files
        f_data = ET.SubElement(root, "file")
        f_data.set("src", "data/city_layout.json")

        # Shaders
        shader_files = [
            "shaders/road_pbr.fx",
            "shaders/building_facade.fx",
            "shaders/sun_shafts.fx",
            "shaders/sky_atmosphere.fx",
            "shaders/ssr_reflection.fx",
            "shaders/water_surface.fx",
            "shaders/street_light.fx",
            "shaders/rain_screen.fx",
        ]
        for sh in shader_files:
            f_elem = ET.SubElement(root, "file")
            f_elem.set("src", sh)

        # Textures (scan resource/textures)
        tex_dir = os.path.join(self.resource_root, "textures")
        if os.path.exists(tex_dir):
            for t_file in sorted(os.listdir(tex_dir)):
                if t_file.endswith(('.dds', '.png', '.txd')):
                    f_elem = ET.SubElement(root, "file")
                    f_elem.set("src", f"textures/{t_file}")

        # Models & Collisions (from registry)
        for name, info in sorted(registry.models.items()):
            f_dff = ET.SubElement(root, "file")
            f_dff.set("src", info['dff'])

            f_lod = ET.SubElement(root, "file")
            f_lod.set("src", info['lod_dff'])

            f_col = ET.SubElement(root, "file")
            f_col.set("src", info['col'])

        # Pretty print XML
        raw_xml = ET.tostring(root, encoding="utf-8")
        parsed = minidom.parseString(raw_xml)
        pretty_xml = parsed.toprettyxml(indent="    ")

        meta_path = os.path.join(self.resource_root, "meta.xml")
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(pretty_xml)

        return meta_path
