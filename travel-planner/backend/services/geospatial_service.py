"""
Geospatial Service — Distance calculations, travel time estimation, and route optimization.
Uses Haversine formula for distance and speed-based heuristics for travel time.
Integrates with the existing static coordinate database in geocoding.py.
"""

import math
import logging
from typing import Dict, Tuple, List, Optional

logger = logging.getLogger(__name__)

# Average speeds (km/h) for travel time estimation by mode
AVERAGE_SPEEDS = {
    "car": 25,       # Indian city traffic average
    "auto": 20,      # Auto-rickshaw in city
    "metro": 35,     # Metro rail average including stops
    "bus": 18,       # City bus
    "walking": 4.5,  # Walking speed
    "bike": 15,      # Bicycle
}

# Buffer minutes added to every leg (boarding, waiting, etc.)
BUFFER_MINUTES = {
    "car": 5,
    "auto": 8,
    "metro": 12,   # Includes walking to station + waiting
    "bus": 15,
    "walking": 0,
    "bike": 3,
}


class GeospatialService:
    """Handle all geographic calculations for itinerary planning."""

    def __init__(self):
        self._distance_cache: Dict[Tuple, float] = {}

    def calculate_distance_km(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """
        Calculate straight-line distance using Haversine formula.

        Args:
            lat1, lon1: Starting coordinates
            lat2, lon2: Ending coordinates

        Returns:
            Distance in kilometers
        """
        cache_key = (round(lat1, 6), round(lon1, 6), round(lat2, 6), round(lon2, 6))
        if cache_key in self._distance_cache:
            return self._distance_cache[cache_key]

        R = 6371  # Earth's radius in km

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )

        c = 2 * math.asin(math.sqrt(a))
        distance = R * c

        self._distance_cache[cache_key] = round(distance, 2)
        return self._distance_cache[cache_key]

    def estimate_travel_time_minutes(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
        transport_type: str = "car",
    ) -> int:
        """
        Estimate travel time based on distance and average city speed.

        Uses a road-distance multiplier (1.4x straight-line) to approximate
        actual driving distance in Indian cities.

        Args:
            lat1, lon1: Starting coordinates
            lat2, lon2: Destination coordinates
            transport_type: "car", "auto", "metro", "bus", "walking", "bike"

        Returns:
            Estimated travel time in minutes
        """
        straight_distance = self.calculate_distance_km(lat1, lon1, lat2, lon2)

        # Road distance is typically 1.3-1.5x straight-line in cities
        road_multiplier = 1.0 if transport_type == "walking" else 1.4
        road_distance = straight_distance * road_multiplier

        speed = AVERAGE_SPEEDS.get(transport_type, 25)
        buffer = BUFFER_MINUTES.get(transport_type, 5)

        travel_minutes = (road_distance / speed) * 60 + buffer

        return max(int(round(travel_minutes)), 1)

    def validate_activity_sequence(
        self,
        activities: List[Dict],
        time_available_minutes: int,
    ) -> Tuple[bool, List[str], int]:
        """
        Validate if a sequence of activities is feasible within the time window.

        Args:
            activities: List of dicts with 'coordinates' (lat/lng dict) and
                        'duration_minutes' keys
            time_available_minutes: Total minutes available

        Returns:
            (is_feasible, warning_messages, total_time_needed)
        """
        warnings: List[str] = []
        total_time_needed = 0

        for i, activity in enumerate(activities):
            # Activity duration
            total_time_needed += activity.get("duration_minutes", 60)

            # Travel time to next activity
            if i < len(activities) - 1:
                current_coords = activity.get("coordinates", {})
                next_coords = activities[i + 1].get("coordinates", {})

                if current_coords and next_coords:
                    travel_time = self.estimate_travel_time_minutes(
                        current_coords.get("lat", 0),
                        current_coords.get("lng", 0),
                        next_coords.get("lat", 0),
                        next_coords.get("lng", 0),
                        transport_type="auto",
                    )
                    total_time_needed += travel_time
                else:
                    # Default 20 min travel if coordinates missing
                    total_time_needed += 20

        is_feasible = total_time_needed <= time_available_minutes

        if not is_feasible:
            variance = total_time_needed - time_available_minutes
            warnings.append(
                f"Activities require {total_time_needed}min but only "
                f"{time_available_minutes}min available. "
                f"Need {variance}min more or reduce activities."
            )

        return is_feasible, warnings, total_time_needed

    def optimize_route_order(
        self,
        locations: List[Dict],
        start_location: Dict,
    ) -> List[Dict]:
        """
        Reorder locations using nearest-neighbor heuristic to minimize travel.

        Args:
            locations: List of dicts with 'coordinates' key (lat/lng dict)
            start_location: Dict with 'coordinates' key (hotel or starting point)

        Returns:
            Reordered list of locations
        """
        if len(locations) <= 1:
            return locations

        unvisited = locations.copy()
        current_coords = start_location.get("coordinates", {})
        optimized: List[Dict] = []

        while unvisited:
            nearest = None
            min_distance = float("inf")

            for loc in unvisited:
                loc_coords = loc.get("coordinates", {})
                if not loc_coords or not current_coords:
                    continue

                distance = self.calculate_distance_km(
                    current_coords.get("lat", 0),
                    current_coords.get("lng", 0),
                    loc_coords.get("lat", 0),
                    loc_coords.get("lng", 0),
                )

                if distance < min_distance:
                    min_distance = distance
                    nearest = loc

            if nearest:
                optimized.append(nearest)
                unvisited.remove(nearest)
                current_coords = nearest.get("coordinates", {})
            else:
                # Append remaining without optimization
                optimized.extend(unvisited)
                break

        return optimized

    def check_location_diversity(
        self,
        locations: List[Dict],
        min_distance_km: float = 0.5,
    ) -> Tuple[float, List[str]]:
        """
        Score how geographically diverse a set of locations is.

        Args:
            locations: List of dicts with 'coordinates' and 'name' keys
            min_distance_km: Minimum desired distance between any two locations

        Returns:
            (diversity_score 0-1, warnings)
        """
        if len(locations) <= 1:
            return 1.0, []

        warnings: List[str] = []
        too_close_count = 0
        total_pairs = 0

        for i in range(len(locations)):
            for j in range(i + 1, len(locations)):
                coords_i = locations[i].get("coordinates", {})
                coords_j = locations[j].get("coordinates", {})

                if not coords_i or not coords_j:
                    continue

                total_pairs += 1
                distance = self.calculate_distance_km(
                    coords_i.get("lat", 0),
                    coords_i.get("lng", 0),
                    coords_j.get("lat", 0),
                    coords_j.get("lng", 0),
                )

                if distance < min_distance_km:
                    too_close_count += 1
                    name_i = locations[i].get("name", f"Location {i+1}")
                    name_j = locations[j].get("name", f"Location {j+1}")
                    warnings.append(
                        f"{name_i} and {name_j} are only {distance:.1f}km apart"
                    )

        if total_pairs == 0:
            return 1.0, []

        diversity_score = 1.0 - (too_close_count / total_pairs)
        return round(diversity_score, 2), warnings

    def calculate_distances_from_hotel(
        self,
        hotel_coords: Dict,
        activity_coords_list: List[Dict],
    ) -> List[float]:
        """
        Calculate distance from hotel to each activity.

        Args:
            hotel_coords: Dict with 'lat' and 'lng'
            activity_coords_list: List of dicts with 'lat' and 'lng'

        Returns:
            List of distances in km
        """
        distances = []
        for coords in activity_coords_list:
            if hotel_coords and coords:
                d = self.calculate_distance_km(
                    hotel_coords.get("lat", 0),
                    hotel_coords.get("lng", 0),
                    coords.get("lat", 0),
                    coords.get("lng", 0),
                )
                distances.append(round(d, 2))
            else:
                distances.append(0.0)
        return distances


# Singleton instance
geospatial_service = GeospatialService()
