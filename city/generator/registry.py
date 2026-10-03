"""
registry.py - Master Asset Registry, Model ID Allocation & Spatial Database
Maintains all procedural asset metadata, DFF/TXD/COL/LOD relationships,
streaming cell bounds, and instance placement records.
"""

import json
import os


class AssetRegistry:
    def __init__(self, start_model_id=1337):
        self.next_model_id = start_model_id
        self.models = {}         # name -> model_info
        self.instances = []      # list of placed instances
        self.streetlights = []   # list of dynamic light sources

    def register_model(self, name, category="building", lod_distance=220.0, far_lod_distance=1500.0):
        """Allocates a unique Model ID and registers file paths."""
        if name in self.models:
            return self.models[name]

        model_id = self.next_model_id
        self.next_model_id += 1

        info = {
            'id': model_id,
            'name': name,
            'category': category,
            'dff': f"models/{name}.dff",
            'lod_dff': f"models/{name}_lod.dff",
            'col': f"collisions/{name}.col",
            'lod_distance': lod_distance,
            'far_lod_distance': far_lod_distance,
        }
        self.models[name] = info
        return info

    def add_instance(self, model_name, x, y, z, rx=0.0, ry=0.0, rz=0.0, scale=1.0, district="commercial"):
        """Places an instance of a registered model in world space."""
        self.instances.append({
            'model': model_name,
            'pos': [round(float(x), 3), round(float(y), 3), round(float(z), 3)],
            'rot': [round(float(rx), 1), round(float(ry), 1), round(float(rz), 1)],
            'scale': round(float(scale), 3),
            'district': district
        })

    def add_streetlight(self, x, y, z, light_type="sodium", intensity=1.0, radius=18.0):
        """Registers a dynamic streetlight for the lighting system."""
        self.streetlights.append({
            'pos': [round(float(x), 3), round(float(y), 3), round(float(z), 3)],
            'type': light_type,  # 'sodium', 'halogen', 'led'
            'intensity': round(float(intensity), 2),
            'radius': round(float(radius), 1)
        })

    def export_layout_json(self, filepath):
        """Exports full city spatial database for the MTA:SA streaming engine."""
        data = {
            'models': self.models,
            'instances': self.instances,
            'streetlights': self.streetlights,
            'meta': {
                'total_models': len(self.models),
                'total_instances': len(self.instances),
                'total_lights': len(self.streetlights),
            }
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return len(self.instances)
