"""
Hotel Aggregation Service — Multi-platform hotel comparison.
Restructures existing hotel data into per-platform price comparisons,
adds coordinates, and computes best deals. Ready for real API swap.
"""

import logging
from typing import Dict, List, Optional
import random

logger = logging.getLogger(__name__)

# Hotel coordinates for major cities (real approximate coordinates)
HOTEL_COORDINATES: Dict[str, Dict[str, Dict[str, float]]] = {
    "delhi": {
        "The Imperial New Delhi": {"lat": 28.6268, "lng": 77.2189},
        "The Lalit New Delhi": {"lat": 28.6310, "lng": 77.2276},
        "Bloomrooms @ New Delhi Railway Station": {"lat": 28.6414, "lng": 77.2138},
        "FabHotel Prime Castle": {"lat": 28.6519, "lng": 77.1907},
        "Zostel Delhi": {"lat": 28.6432, "lng": 77.2155},
        "Moustache Hostel Delhi": {"lat": 28.6398, "lng": 77.2185},
    },
    "mumbai": {
        "The Taj Mahal Palace": {"lat": 18.9217, "lng": 72.8332},
        "Trident Nariman Point": {"lat": 18.9256, "lng": 72.8200},
        "Hotel Residency Fort": {"lat": 18.9340, "lng": 72.8370},
        "FabHotel Ascot International": {"lat": 19.1197, "lng": 72.8464},
        "Zostel Mumbai": {"lat": 18.9232, "lng": 72.8320},
    },
    "jaipur": {
        "Rambagh Palace": {"lat": 26.8984, "lng": 75.8065},
        "ITC Rajputana": {"lat": 26.9118, "lng": 75.7912},
        "Hotel Pearl Palace": {"lat": 26.9082, "lng": 75.8005},
        "Zostel Jaipur": {"lat": 26.9245, "lng": 75.8260},
    },
    "goa": {
        "Taj Exotica Resort & Spa": {"lat": 15.2613, "lng": 73.9217},
        "Alila Diwa Goa": {"lat": 15.2849, "lng": 73.9252},
        "Acron Waterfront Resort": {"lat": 15.5540, "lng": 73.7536},
        "Zostel Goa Anjuna": {"lat": 15.5737, "lng": 73.7415},
    },
    "bangalore": {
        "The Leela Palace Bangalore": {"lat": 12.9610, "lng": 77.6470},
        "Taj MG Road Bangalore": {"lat": 12.9748, "lng": 77.6066},
        "Treebo Trend Dee Empresa": {"lat": 12.9784, "lng": 77.6408},
        "Zostel Bangalore": {"lat": 12.9352, "lng": 77.6245},
    },
    "kolkata": {
        "The Oberoi Grand": {"lat": 22.5672, "lng": 88.3527},
        "The Park Kolkata": {"lat": 22.5540, "lng": 88.3540},
        "Zostel Kolkata": {"lat": 22.5570, "lng": 88.3495},
    },
    "hyderabad": {
        "Taj Falaknuma Palace": {"lat": 17.3316, "lng": 78.4671},
        "Novotel Hyderabad Convention Centre": {"lat": 17.4583, "lng": 78.3765},
        "Treebo Trend Aditya Hometel": {"lat": 17.4375, "lng": 78.4483},
    },
    "agra": {
        "The Oberoi Amarvilas": {"lat": 27.1697, "lng": 78.0438},
        "Crystal Sarovar Premiere": {"lat": 27.1612, "lng": 78.0283},
        "Zostel Agra": {"lat": 27.1730, "lng": 78.0455},
    },
    "varanasi": {
        "Taj Nadesar Palace": {"lat": 25.3314, "lng": 83.0128},
        "Hotel Surya Kaiser Palace": {"lat": 25.3270, "lng": 82.9890},
        "Zostel Varanasi": {"lat": 25.2853, "lng": 83.0048},
    },
    "kerala": {
        "Kumarakom Lake Resort": {"lat": 9.6175, "lng": 76.4301},
        "Fragrant Nature Munnar": {"lat": 10.0889, "lng": 77.0595},
        "Zostel Alleppey": {"lat": 9.4895, "lng": 76.3268},
    },
    "udaipur": {
        "Taj Lake Palace": {"lat": 24.5741, "lng": 73.6810},
        "Hotel Lakend": {"lat": 24.5945, "lng": 73.6790},
        "Zostel Udaipur": {"lat": 24.5768, "lng": 73.6878},
    },
    "shimla": {
        "Wildflower Hall, Shimla": {"lat": 31.1478, "lng": 77.2173},
        "Hotel Willow Banks": {"lat": 31.1045, "lng": 77.1695},
        "Zostel Shimla": {"lat": 31.1050, "lng": 77.1720},
    },
    "manali": {
        "The Himalayan": {"lat": 32.2420, "lng": 77.1770},
        "Hotel Manu Allaya": {"lat": 32.2388, "lng": 77.1885},
        "Zostel Manali": {"lat": 32.2510, "lng": 77.1880},
    },
    "rishikesh": {
        "Aloha on the Ganges": {"lat": 30.1288, "lng": 78.3202},
        "The Hosteller Rishikesh": {"lat": 30.1256, "lng": 78.3215},
        "Zostel Rishikesh": {"lat": 30.1302, "lng": 78.3195},
    },
    "pune": {
        "Conrad Pune": {"lat": 18.5365, "lng": 73.8948},
        "Lemon Tree Premier": {"lat": 18.5901, "lng": 73.7388},
        "Zostel Pune": {"lat": 18.5362, "lng": 73.8935},
    },
    "mysore": {
        "Radisson Blu Plaza Hotel Mysore": {"lat": 12.3065, "lng": 76.6600},
        "Hotel Pai Vista": {"lat": 12.3048, "lng": 76.6575},
        "Sonder Hostel Mysore": {"lat": 12.3158, "lng": 76.6530},
    },
    "chandigarh": {
        "The Lalit Chandigarh": {"lat": 30.7153, "lng": 76.8027},
        "Hotel Mountview": {"lat": 30.7479, "lng": 76.7872},
        "Zostel Chandigarh": {"lat": 30.7365, "lng": 76.7742},
    },
    "ooty": {
        "Savoy - IHCL SeleQtions": {"lat": 11.4125, "lng": 76.7005},
        "Hotel Lakeview": {"lat": 11.4048, "lng": 76.6978},
        "Zostel Ooty": {"lat": 11.4110, "lng": 76.6965},
    },
    "darjeeling": {
        "Mayfair Darjeeling": {"lat": 27.0430, "lng": 88.2647},
        "Hotel Sinclairs Darjeeling": {"lat": 27.0455, "lng": 88.2615},
        "Zostel Darjeeling": {"lat": 27.0395, "lng": 88.2620},
    },
    "rajasthan": {
        "Umaid Bhawan Palace Jodhpur": {"lat": 26.2840, "lng": 73.0483},
        "Hotel Raas Jodhpur": {"lat": 26.2972, "lng": 73.0205},
        "Zostel Jodhpur": {"lat": 26.2978, "lng": 73.0180},
    },
}

# Platform price multipliers (simulates different pricing across platforms)
PLATFORM_MULTIPLIERS = {
    "booking": 1.0,       # Base price
    "agoda": 0.95,        # Typically 5% cheaper
    "makemytrip": 0.97,   # Typically 3% cheaper
}

PLATFORM_URLS = {
    "booking": "https://www.booking.com/searchresults.html?ss=",
    "agoda": "https://www.agoda.com/search?city=",
    "makemytrip": "https://www.makemytrip.com/hotels/hotel-listing?city=",
}


class HotelAggregationService:
    """Aggregate hotel data with multi-platform price comparisons."""

    def enrich_hotels_with_comparison(
        self,
        hotels: List[Dict],
        destination: str,
        duration_days: int = 1,
    ) -> List[Dict]:
        """
        Enrich hotel list with coordinates and multi-platform price comparisons.

        Args:
            hotels: List of hotel dicts from hotel_api.py
            destination: City name
            duration_days: Stay duration for total price calculation

        Returns:
            Enriched hotel list with coordinates, price comparisons, and best deal
        """
        city_coords = HOTEL_COORDINATES.get(destination.lower(), {})
        enriched_hotels: List[Dict] = []

        for hotel in hotels:
            name = hotel.get("name", "")
            base_price = hotel.get("price_per_night", 2000)

            # Add coordinates
            coords = city_coords.get(name)
            if coords:
                hotel["coordinates"] = coords
            else:
                # Generate approximate coordinates near city center
                hotel["coordinates"] = self._approximate_coordinates(destination)

            # Generate multi-platform price comparisons
            price_comparisons = []
            for platform, multiplier in PLATFORM_MULTIPLIERS.items():
                # Add small random variation (±3%) for realism
                variation = 1.0 + random.uniform(-0.03, 0.03)
                platform_price = round(base_price * multiplier * variation)

                price_comparisons.append({
                    "platform": platform,
                    "price_per_night": platform_price,
                    "total_price": platform_price * duration_days,
                    "currency": "INR",
                    "taxes_included": platform != "booking",  # Booking often shows pre-tax
                    "url": f"{PLATFORM_URLS[platform]}{destination}",
                    "availability": True,
                })

            hotel["price_comparisons"] = price_comparisons

            # Find best deal
            best = min(price_comparisons, key=lambda x: x["price_per_night"])
            hotel["best_price"] = best["price_per_night"]
            hotel["best_platform"] = best["platform"]
            hotel["average_price"] = round(
                sum(p["price_per_night"] for p in price_comparisons) / len(price_comparisons)
            )

            # Savings info
            max_price = max(p["price_per_night"] for p in price_comparisons)
            if max_price > best["price_per_night"]:
                hotel["savings"] = max_price - best["price_per_night"]
                hotel["savings_percentage"] = round(
                    (hotel["savings"] / max_price) * 100, 1
                )
            else:
                hotel["savings"] = 0
                hotel["savings_percentage"] = 0

            # Add booking links
            hotel["booking_links"] = {
                p["platform"]: p["url"] for p in price_comparisons
            }

            enriched_hotels.append(hotel)

        # Sort by best price
        enriched_hotels.sort(key=lambda x: x.get("best_price", float("inf")))

        logger.info(
            f"Enriched {len(enriched_hotels)} hotels for {destination} "
            f"with multi-platform pricing"
        )

        return enriched_hotels

    def _approximate_coordinates(self, destination: str) -> Dict[str, float]:
        """Generate approximate coordinates near the city center."""
        from geocoding import CITY_COORDS

        city_center = CITY_COORDS.get(destination.lower(), (28.6139, 77.2090))
        return {
            "lat": city_center[0] + random.uniform(-0.015, 0.015),
            "lng": city_center[1] + random.uniform(-0.015, 0.015),
        }

    def get_price_comparison_summary(
        self, hotels: List[Dict]
    ) -> str:
        """
        Generate a price comparison summary string for LLM prompt.

        Args:
            hotels: Enriched hotel list

        Returns:
            Formatted comparison string
        """
        lines = ["HOTEL PRICE COMPARISON:"]

        for hotel in hotels[:3]:  # Top 3
            name = hotel.get("name", "Unknown")
            lines.append(f"\n  {name} (★{hotel.get('rating', 'N/A')}):")
            lines.append(f"    Location: {hotel.get('location', 'N/A')}")
            lines.append(f"    Coordinates: ({hotel['coordinates']['lat']:.4f}, "
                         f"{hotel['coordinates']['lng']:.4f})")

            for pc in hotel.get("price_comparisons", []):
                tax_note = "(incl. tax)" if pc["taxes_included"] else "(+ tax)"
                lines.append(
                    f"    {pc['platform'].title()}: ₹{pc['price_per_night']}/night {tax_note}"
                )

            best = hotel.get("best_platform", "")
            lines.append(f"    ✅ Best Deal: {best.title()} at ₹{hotel.get('best_price', 0)}/night")

            if hotel.get("savings", 0) > 0:
                lines.append(f"    💰 Save ₹{hotel['savings']} ({hotel['savings_percentage']}%)")

        return "\n".join(lines)


# Singleton instance
hotel_aggregation_service = HotelAggregationService()
