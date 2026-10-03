"""
city_plan.py - Master Urban Plan, District Zoning, and Instance Placer
Synthesizes a cohesive American metropolis centered exactly at:
X = -4076.83813, Y = 492.02350, Z = 161.42682
Arranges Financial Core, Commercial Corridor, Residential Uptown, Industrial Zone,
Central Park, Elevated Expressway, Cable-Stayed Bridge, Mountain Tunnel, and Street Furniture.
"""

CITY_ORIGIN_X = -4076.83813
CITY_ORIGIN_Y = 492.02350
CITY_ORIGIN_Z = 161.42682


class CityPlanner:
    def __init__(self, origin=(CITY_ORIGIN_X, CITY_ORIGIN_Y, CITY_ORIGIN_Z)):
        self.ox, self.oy, self.oz = origin
        self.instances = []
        self.streetlights = []
        self.pois = {}

    def plan_metropolis(self):
        """Generates spatial layout of blocks, buildings, infrastructure, and props."""
        self.instances = []
        self.streetlights = []

        # 1. Base Ground Blocks Grid (5x5 Grid spanning -160 to +160)
        grid_coords = [-160, -80, 0, 80, 160]
        for gx in grid_coords:
            for gy in grid_coords:
                # Determine block type
                if gx == 0 and gy == 0:
                    block_type = "block_plaza"
                elif gx == -80 and gy == 160:
                    block_type = "block_park"
                elif gx >= 80 and gy <= -80:
                    block_type = "block_industrial"
                else:
                    block_type = "block_downtown"

                self.add_instance(block_type, gx, gy, 0)

        # 2. Architectural Buildings Placements on Blocks
        # A. Financial Core (Center)
        self.add_instance("bldg_glass_skyscraper", 0, 80, 0.16)
        self.add_instance("bldg_art_deco_tower", 80, 0, 0.16)
        self.add_instance("bldg_corporate_hq", -80, 0, 0.16)
        self.add_instance("bldg_luxury_hotel", 0, -80, 0.16)

        # B. Commercial & Entertainment Corridor (East / North-East)
        self.add_instance("bldg_commercial_strip", 80, 80, 0.16)
        self.add_instance("bldg_american_diner", 160, 80, 0.16)
        self.add_instance("bldg_parking_garage", 80, 160, 0.16)
        self.add_instance("bldg_gas_station", 160, 160, 0.16)

        # C. Uptown Residential & Civic (West / North-West)
        self.add_instance("bldg_brownstone_block", -80, 80, 0.16)
        self.add_instance("bldg_residential_tower", -160, 80, 0.16)
        self.add_instance("bldg_city_hall", -160, 160, 0.16)
        self.add_instance("bldg_police_station", -160, 0, 0.16)
        self.add_instance("bldg_fire_station", -160, -80, 0.16)
        self.add_instance("bldg_hospital", -80, -160, 0.16)

        # D. Industrial & Maritime Logistics (South-East)
        self.add_instance("bldg_logistics_warehouse", 80, -80, 0.0)
        self.add_instance("bldg_factory_plant", 160, -80, 0.0)
        self.add_instance("bldg_power_substation", 80, -160, 0.0)

        # 3. Major Infrastructure: Elevated Expressway, Bridge, and Tunnel
        # Elevated Expressway Viaduct running North-South at X = 200
        for vy in [-120, -40, 40, 120]:
            self.add_instance("highway_viaduct", 200, vy, 0)
        # Expressway On-Ramp connecting surface street (at 160, 0) to viaduct (at 200, 0)
        self.add_instance("highway_ramp", 180, 0, 0, rot=(0, 0, 90))

        # Cable-Stayed Suspension Bridge spanning river channel to the North
        self.add_instance("cable_bridge", 0, 240, 0)

        # Mountain Highway Tunnel Portal to the South
        self.add_instance("tunnel_portal", 0, -220, 0)

        # 4. Street Lighting Network (Cobra-head lights with dynamic light metadata)
        street_light_positions = [
            (-35, -40), (35, -40), (-35, 40), (35, 40),
            (-115, -40), (115, -40), (-115, 40), (115, 40),
            (-40, -115), (40, -115), (-40, 115), (40, 115),
            (-115, -115), (115, -115), (-115, 115), (115, 115)
        ]
        for lx, ly in street_light_positions:
            self.add_instance("prop_streetlight_cobra", lx, ly, 0.16)
            self.streetlights.append({
                'pos': [self.ox + lx, self.oy + ly + 2.5, self.oz + 8.1],
                'color': [255, 195, 115],  # Warm sodium orange
                'radius': 22.0,
                'intensity': 1.2
            })

        # 5. Traffic Signals at Major Intersections
        signal_positions = [(-40, -40), (40, -40), (-40, 40), (40, 40)]
        for sx, sy in signal_positions:
            self.add_instance("prop_traffic_signal", sx, sy, 0.16)

        # 6. Street Furniture (Hydrants, Mailboxes, Bus Shelters, Dumpsters, Benches)
        self.add_instance("prop_fire_hydrant", -36, -32, 0.16)
        self.add_instance("prop_fire_hydrant", 36, 32, 0.16)
        self.add_instance("prop_usps_mailbox", -32, -36, 0.16)
        self.add_instance("prop_usps_mailbox", 32, 36, 0.16)
        self.add_instance("prop_bus_shelter", -32, 45, 0.16)
        self.add_instance("prop_bus_shelter", 32, -45, 0.16)
        self.add_instance("prop_dumpster", 85, -65, 0.0)
        self.add_instance("prop_dumpster", 165, -65, 0.0)

        # Park Benches inside Central Park
        park_cx, park_cy = -80, 160
        self.add_instance("prop_park_bench", park_cx - 10, park_cy - 4, 0.17)
        self.add_instance("prop_park_bench", park_cx + 10, park_cy - 4, 0.17)
        self.add_instance("prop_park_bench", park_cx - 10, park_cy + 4, 0.17)
        self.add_instance("prop_park_bench", park_cx + 10, park_cy + 4, 0.17)

        # 7. Botanical Trees (Palms and Oaks)
        # Boulevard Fan Palms along Central Plaza
        for py in [-25, -12, 12, 25]:
            self.add_instance("veg_fan_palm", -32, py, 0.16)
            self.add_instance("veg_fan_palm", 32, py, 0.16)

        # Oak Trees inside Central Park
        for ox_tree, oy_tree in [(-92, 148), (-68, 148), (-92, 172), (-68, 172)]:
            self.add_instance("veg_oak_tree", ox_tree, oy_tree, 0.17)

        # 8. Define Points of Interest (POIs) for Teleportation
        self.pois = {
            'center':      [self.ox, self.oy, self.oz + 1.2],
            'spawn':       [self.ox, self.oy, self.oz + 1.2],
            'plaza':       [self.ox, self.oy, self.oz + 1.2],
            'downtown':    [self.ox, self.oy + 80, self.oz + 1.2],
            'hotel':       [self.ox, self.oy - 80, self.oz + 1.2],
            'waterfront':  [self.ox, self.oy + 180, self.oz + 1.2],
            'bridge':      [self.ox, self.oy + 240, self.oz + 15.2],
            'expressway':  [self.ox + 200, self.oy, self.oz + 13.2],
            'tunnel':      [self.ox, self.oy - 200, self.oz + 1.2],
            'industrial':  [self.ox + 120, self.oy - 120, self.oz + 1.2],
            'park':        [self.ox - 80, self.oy + 160, self.oz + 1.2],
            'cityhall':    [self.ox - 160, self.oy + 160, self.oz + 1.2],
        }

        return self.instances, self.streetlights, self.pois

    def add_instance(self, model_name, rel_x, rel_y, rel_z, rot=(0, 0, 0), scale=1.0):
        """Adds a placed object instance with world coordinates."""
        world_x = round(self.ox + rel_x, 3)
        world_y = round(self.oy + rel_y, 3)
        world_z = round(self.oz + rel_z, 3)
        self.instances.append({
            'model': model_name,
            'pos': [world_x, world_y, world_z],
            'rot': list(rot),
            'scale': scale
        })
