"""
districts.py - City Zoning & Spatial District Allocation System
Defines the urban layout, district zones, parcel bounding footprints,
setbacks, density tiers, and building archetype placements.
"""

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class DistrictZone:
    name: str
    zone_type: str        # 'downtown', 'commercial', 'residential', 'industrial', 'coastal', 'hills', 'park', 'civic'
    bounds: Tuple[float, float, float, float]  # (min_x, min_y, max_x, max_y)
    allowed_archetypes: List[str]
    max_height: float
    target_density: float # 0.0 to 1.0


class CityZoningPlan:
    def __init__(self, origin_x=0.0, origin_y=0.0):
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.zones = []
        self._init_districts()

    def _init_districts(self):
        ox, oy = self.origin_x, self.origin_y

        # 1. Downtown Core: High-density skyscrapers, modern glass towers, corporate office towers
        self.zones.append(DistrictZone(
            name="Downtown Core",
            zone_type="downtown",
            bounds=(ox - 80.0, oy - 80.0, ox + 180.0, oy + 180.0),
            allowed_archetypes=["Modern Tower", "Glass Tower", "Office Tower", "Parking Garage", "Hotel"],
            max_height=140.0,
            target_density=0.90
        ))

        # 2. Commercial District: Shopping centers, strip malls, diners, restaurants, banks
        self.zones.append(DistrictZone(
            name="Midtown Commercial",
            zone_type="commercial",
            bounds=(ox - 80.0, oy + 180.0, ox + 180.0, oy + 360.0),
            allowed_archetypes=["Shopping Center", "Strip Mall", "Restaurant", "Diner", "Motel", "Small Commercial Building", "Gas Station"],
            max_height=35.0,
            target_density=0.75
        ))

        # 3. Suburbs & Residential: Single-family homes, townhouses, luxury apartments
        self.zones.append(DistrictZone(
            name="Sunset Suburbs",
            zone_type="residential",
            bounds=(ox + 180.0, oy - 120.0, ox + 420.0, oy + 240.0),
            allowed_archetypes=["Suburban House", "Townhouse", "Luxury Apartment", "Residential Tower"],
            max_height=45.0,
            target_density=0.60
        ))

        # 4. Industrial District: Warehouses, factories, industrial yards
        self.zones.append(DistrictZone(
            name="Bayside Industrial",
            zone_type="industrial",
            bounds=(ox - 80.0, oy - 320.0, ox + 180.0, oy - 80.0),
            allowed_archetypes=["Warehouse", "Factory", "Industrial Building"],
            max_height=25.0,
            target_density=0.65
        ))

        # 5. Coastal District: Marina, oceanfront promenade, resort hotels
        self.zones.append(DistrictZone(
            name="Pacific Promenade",
            zone_type="coastal",
            bounds=(ox - 320.0, oy - 200.0, ox - 80.0, oy + 240.0),
            allowed_archetypes=["Hotel", "Restaurant", "Small Commercial Building", "Luxury Apartment"],
            max_height=50.0,
            target_density=0.55
        ))

        # 6. Hills District: Winding hilltop estates
        self.zones.append(DistrictZone(
            name="Eastern Heights",
            zone_type="hills",
            bounds=(ox + 420.0, oy - 120.0, ox + 600.0, oy + 280.0),
            allowed_archetypes=["Suburban House", "Luxury Apartment"],
            max_height=22.0,
            target_density=0.35
        ))

        # 7. Civic & Public Services: Hospital, police, fire, school, gas station
        self.zones.append(DistrictZone(
            name="Civic Plaza",
            zone_type="civic",
            bounds=(ox + 180.0, oy + 240.0, ox + 360.0, oy + 420.0),
            allowed_archetypes=["Hospital", "Police Station", "Fire Station", "School", "Gas Station"],
            max_height=30.0,
            target_density=0.70
        ))

    def get_zone_at(self, x, y):
        """Returns the district zone enclosing (x, y)."""
        for zone in self.zones:
            min_x, min_y, max_x, max_y = zone.bounds
            if min_x <= x <= max_x and min_y <= y <= max_y:
                return zone
        return self.zones[1]  # Default to commercial
