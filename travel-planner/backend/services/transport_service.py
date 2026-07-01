"""
Transport Service — City-specific transport recommendations, cost estimation,
and mode selection based on distance between locations.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# Transport cost per km by mode and city tier
# city_tier: "metro_city" (Delhi, Mumbai, Bangalore, Kolkata, Hyderabad)
#            "tier2" (Jaipur, Pune, Chandigarh)
#            "tourist" (Goa, Kerala, Agra, Varanasi, etc.)
TRANSPORT_COSTS = {
    "metro_city": {
        "metro": {"base_fare": 10, "per_km": 2.5, "available": True},
        "auto": {"base_fare": 25, "per_km": 12, "available": True},
        "taxi": {"base_fare": 50, "per_km": 15, "available": True},
        "bus": {"base_fare": 10, "per_km": 1.5, "available": True},
        "walking": {"base_fare": 0, "per_km": 0, "available": True},
    },
    "tier2": {
        "metro": {"base_fare": 0, "per_km": 0, "available": False},
        "auto": {"base_fare": 20, "per_km": 10, "available": True},
        "taxi": {"base_fare": 40, "per_km": 12, "available": True},
        "bus": {"base_fare": 10, "per_km": 1.5, "available": True},
        "walking": {"base_fare": 0, "per_km": 0, "available": True},
    },
    "tourist": {
        "metro": {"base_fare": 0, "per_km": 0, "available": False},
        "auto": {"base_fare": 30, "per_km": 15, "available": True},
        "taxi": {"base_fare": 50, "per_km": 14, "available": True},
        "bus": {"base_fare": 15, "per_km": 2, "available": True},
        "walking": {"base_fare": 0, "per_km": 0, "available": True},
    },
}

# City to tier mapping
CITY_TIERS = {
    "delhi": "metro_city",
    "mumbai": "metro_city",
    "bangalore": "metro_city",
    "kolkata": "metro_city",
    "hyderabad": "metro_city",
    "jaipur": "tier2",
    "pune": "tier2",
    "chandigarh": "tier2",
    "goa": "tourist",
    "kerala": "tourist",
    "agra": "tourist",
    "varanasi": "tourist",
    "udaipur": "tourist",
    "shimla": "tourist",
    "manali": "tourist",
    "rishikesh": "tourist",
    "mysore": "tourist",
    "ooty": "tourist",
    "darjeeling": "tourist",
    "rajasthan": "tier2",
}

# Metro line info for metro cities
METRO_INFO = {
    "delhi": {
        "name": "Delhi Metro (DMRC)",
        "lines": 12,
        "stations": 286,
        "hours": "05:00-23:30",
        "day_pass": 200,
        "app": "DMRC app / Google Maps",
        "key_tourist_stations": [
            "Chandni Chowk (Yellow Line) — Red Fort, Jama Masjid",
            "Rajiv Chowk (Yellow/Blue) — Connaught Place",
            "Central Secretariat (Yellow/Violet) — India Gate",
            "Qutub Minar (Yellow Line) — Qutub Minar Complex",
            "Akshardham (Blue Line) — Akshardham Temple",
            "Jama Masjid (Violet Line) — Jama Masjid, Karim's",
            "Hauz Khas (Yellow/Magenta) — Hauz Khas Village",
            "Kalkaji Mandir (Violet/Magenta) — Lotus Temple",
        ],
    },
    "mumbai": {
        "name": "Mumbai Metro + Local Trains",
        "lines": 3,
        "stations": 67,
        "hours": "05:00-23:00",
        "day_pass": 150,
        "app": "m-Indicator app",
        "key_tourist_stations": [
            "CSMT (Central/Harbour) — CST, Fort Area",
            "Churchgate (Western) — Marine Drive, Nariman Point",
            "Andheri (Western/Metro) — Juhu Beach connection",
            "Bandra (Western) — Bandra-Worli Sea Link",
        ],
    },
    "bangalore": {
        "name": "Namma Metro (BMRCL)",
        "lines": 2,
        "stations": 62,
        "hours": "05:00-23:00",
        "day_pass": 120,
        "app": "Namma Metro app",
        "key_tourist_stations": [
            "Cubbon Park (Purple Line) — Cubbon Park, Vidhana Soudha",
            "MG Road (Purple Line) — MG Road, shopping",
            "Majestic (Purple/Green) — Bangalore Palace connection",
            "Lalbagh (Green Line) — Lalbagh Botanical Garden",
        ],
    },
    "kolkata": {
        "name": "Kolkata Metro",
        "lines": 2,
        "stations": 32,
        "hours": "06:45-21:45",
        "day_pass": 100,
        "app": "Kolkata Metro Rail app",
        "key_tourist_stations": [
            "Park Street (Blue Line) — Park Street restaurants",
            "Maidan (Blue Line) — Victoria Memorial",
            "Central (Blue Line) — New Market shopping",
            "Esplanade (Blue/Green) — BBD Bagh, GPO",
        ],
    },
    "hyderabad": {
        "name": "Hyderabad Metro (L&T)",
        "lines": 3,
        "stations": 57,
        "hours": "06:00-22:00",
        "day_pass": 100,
        "app": "T-Savari app",
        "key_tourist_stations": [
            "MGBS (Red/Green) — Charminar connection",
            "Nampally (Blue Line) — Salar Jung Museum",
            "Ameerpet (Red/Blue) — Central hub",
        ],
    },
}


class TransportService:
    """Transport recommendations and cost estimation for Indian cities."""

    def recommend_transport(
        self,
        city: str,
        distance_km: float,
        budget_preference: str = "mid-range",
    ) -> Dict:
        """
        Recommend best transport mode for a given distance in a city.

        Args:
            city: Destination city name
            distance_km: Distance in kilometers
            budget_preference: "budget", "mid-range", "luxury"

        Returns:
            Dict with mode, cost, time_minutes, and alternative options
        """
        tier = CITY_TIERS.get(city.lower(), "tourist")
        costs = TRANSPORT_COSTS.get(tier, TRANSPORT_COSTS["tourist"])

        options: List[Dict] = []

        for mode, config in costs.items():
            if not config["available"]:
                continue

            # Calculate cost for this mode
            if mode == "walking" and distance_km > 2.5:
                continue  # Don't suggest walking for long distances
            if mode == "walking" and distance_km > 1.5 and budget_preference != "budget":
                continue

            cost = config["base_fare"] + (config["per_km"] * distance_km)
            cost = round(max(cost, config["base_fare"]), 0)

            # Estimate time
            speeds = {"metro": 35, "auto": 20, "taxi": 25, "bus": 18, "walking": 4.5}
            time_minutes = round((distance_km / speeds.get(mode, 20)) * 60)

            # Add boarding/waiting buffer
            buffers = {"metro": 12, "auto": 5, "taxi": 3, "bus": 15, "walking": 0}
            time_minutes += buffers.get(mode, 5)

            options.append({
                "mode": mode,
                "cost": cost,
                "estimated_time_minutes": max(time_minutes, 1),
                "distance_km": round(distance_km, 1),
            })

        if not options:
            return {
                "recommended": {
                    "mode": "auto",
                    "cost": round(30 + 12 * distance_km),
                    "estimated_time_minutes": round(distance_km * 3) + 5,
                    "distance_km": round(distance_km, 1),
                },
                "alternatives": [],
            }

        # Sort by preference: budget=cheapest, luxury=fastest, mid-range=balanced
        if budget_preference == "budget":
            options.sort(key=lambda x: x["cost"])
        elif budget_preference == "luxury":
            options.sort(key=lambda x: x["estimated_time_minutes"])
        else:
            # Balance: score = cost * 0.4 + time * 0.6
            options.sort(
                key=lambda x: x["cost"] * 0.4 + x["estimated_time_minutes"] * 10 * 0.6
            )

        return {
            "recommended": options[0],
            "alternatives": options[1:3],  # Top 2 alternatives
        }

    def get_metro_info(self, city: str) -> Optional[Dict]:
        """
        Get metro system information for a city.

        Returns:
            Metro info dict or None if city has no metro
        """
        return METRO_INFO.get(city.lower())

    def estimate_daily_transport_cost(
        self,
        city: str,
        num_legs: int = 4,
        avg_distance_km: float = 5.0,
        budget_preference: str = "mid-range",
    ) -> Dict:
        """
        Estimate total daily transport cost.

        Args:
            city: City name
            num_legs: Number of trips per day (hotel→A, A→B, B→C, C→hotel)
            avg_distance_km: Average distance per leg
            budget_preference: "budget", "mid-range", "luxury"

        Returns:
            Dict with total_cost, per_leg_cost, recommended_mode
        """
        recommendation = self.recommend_transport(
            city, avg_distance_km, budget_preference
        )

        per_leg = recommendation["recommended"]["cost"]
        total = per_leg * num_legs

        return {
            "total_daily_cost": round(total),
            "per_leg_cost": round(per_leg),
            "recommended_mode": recommendation["recommended"]["mode"],
            "num_legs": num_legs,
            "avg_distance_km": avg_distance_km,
        }

    def get_transport_summary_for_prompt(self, city: str) -> str:
        """
        Generate a transport context string for LLM prompt injection.

        Args:
            city: City name

        Returns:
            Formatted string with transport info for the city
        """
        tier = CITY_TIERS.get(city.lower(), "tourist")
        metro = self.get_metro_info(city)
        costs = TRANSPORT_COSTS.get(tier, TRANSPORT_COSTS["tourist"])

        lines = [f"TRANSPORT OPTIONS IN {city.upper()}:"]

        if metro:
            lines.append(f"- {metro['name']}: {metro['stations']} stations, "
                         f"operates {metro['hours']}, day pass ₹{metro['day_pass']}")
            lines.append(f"  Key tourist stations: {'; '.join(metro['key_tourist_stations'][:4])}")

        for mode, config in costs.items():
            if config["available"] and mode != "walking":
                lines.append(
                    f"- {mode.title()}: Base ₹{config['base_fare']}, "
                    f"₹{config['per_km']}/km"
                )

        lines.append("- Walking: Free, recommended for distances under 1.5km")

        return "\n".join(lines)


# Singleton instance
transport_service = TransportService()
