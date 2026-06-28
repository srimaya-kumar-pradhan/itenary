"""
Hotel API Service — provides hotel recommendations by city and tier.
Uses curated mock data for MVP with integration points for real APIs.
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class HotelService:
    """Hotel data service with mock data for Indian cities."""

    def __init__(self):
        """Initialize with curated hotel data."""
        self.hotels: Dict[str, List[Dict]] = {}
        self._load_mock_hotels()
        logger.info(f"Hotel service initialized with {len(self.hotels)} cities")

    def _load_mock_hotels(self):
        """Load curated hotel data for major Indian cities."""
        self.hotels = {
            "delhi": [
                {
                    "name": "The Imperial New Delhi",
                    "rating": 4.8,
                    "price_per_night": 12000,
                    "location": "Janpath, Connaught Place",
                    "amenities": ["Pool", "Spa", "Fine Dining", "Heritage"],
                    "tier": "luxury",
                },
                {
                    "name": "The Lalit New Delhi",
                    "rating": 4.5,
                    "price_per_night": 7500,
                    "location": "Barakhamba Road",
                    "amenities": ["Pool", "Restaurant", "Fitness Center"],
                    "tier": "luxury",
                },
                {
                    "name": "Bloomrooms @ New Delhi Railway Station",
                    "rating": 4.0,
                    "price_per_night": 3500,
                    "location": "Paharganj",
                    "amenities": ["Wi-Fi", "AC", "Restaurant"],
                    "tier": "mid-range",
                },
                {
                    "name": "FabHotel Prime Castle",
                    "rating": 3.8,
                    "price_per_night": 2500,
                    "location": "Karol Bagh",
                    "amenities": ["Wi-Fi", "AC", "Breakfast"],
                    "tier": "mid-range",
                },
                {
                    "name": "Zostel Delhi",
                    "rating": 3.5,
                    "price_per_night": 800,
                    "location": "Paharganj",
                    "amenities": ["Wi-Fi", "Common Area", "Lockers"],
                    "tier": "budget",
                },
                {
                    "name": "Moustache Hostel Delhi",
                    "rating": 3.6,
                    "price_per_night": 600,
                    "location": "New Delhi Station Area",
                    "amenities": ["Wi-Fi", "Breakfast", "Tours"],
                    "tier": "budget",
                },
            ],
            "mumbai": [
                {
                    "name": "The Taj Mahal Palace",
                    "rating": 4.9,
                    "price_per_night": 18000,
                    "location": "Colaba, Gateway of India",
                    "amenities": ["Pool", "Spa", "Sea View", "Heritage"],
                    "tier": "luxury",
                },
                {
                    "name": "Trident Nariman Point",
                    "rating": 4.6,
                    "price_per_night": 9000,
                    "location": "Nariman Point",
                    "amenities": ["Pool", "Sea View", "Restaurant"],
                    "tier": "luxury",
                },
                {
                    "name": "Hotel Residency Fort",
                    "rating": 3.9,
                    "price_per_night": 3000,
                    "location": "Fort Area",
                    "amenities": ["Wi-Fi", "AC", "Restaurant"],
                    "tier": "mid-range",
                },
                {
                    "name": "FabHotel Ascot International",
                    "rating": 3.7,
                    "price_per_night": 2800,
                    "location": "Andheri",
                    "amenities": ["Wi-Fi", "AC", "Breakfast"],
                    "tier": "mid-range",
                },
                {
                    "name": "Zostel Mumbai",
                    "rating": 3.5,
                    "price_per_night": 900,
                    "location": "Colaba",
                    "amenities": ["Wi-Fi", "Common Area", "City Tours"],
                    "tier": "budget",
                },
            ],
            "jaipur": [
                {
                    "name": "Rambagh Palace",
                    "rating": 4.9,
                    "price_per_night": 25000,
                    "location": "Bhawani Singh Road",
                    "amenities": ["Pool", "Spa", "Palace Heritage", "Gardens"],
                    "tier": "luxury",
                },
                {
                    "name": "ITC Rajputana",
                    "rating": 4.5,
                    "price_per_night": 6500,
                    "location": "MI Road",
                    "amenities": ["Pool", "Restaurant", "Spa"],
                    "tier": "luxury",
                },
                {
                    "name": "Hotel Pearl Palace",
                    "rating": 4.2,
                    "price_per_night": 2000,
                    "location": "Hathroi Fort",
                    "amenities": ["Rooftop Restaurant", "Wi-Fi", "AC"],
                    "tier": "mid-range",
                },
                {
                    "name": "Zostel Jaipur",
                    "rating": 3.8,
                    "price_per_night": 700,
                    "location": "Near Hawa Mahal",
                    "amenities": ["Wi-Fi", "Common Area", "Breakfast"],
                    "tier": "budget",
                },
            ],
            "goa": [
                {
                    "name": "Taj Exotica Resort & Spa",
                    "rating": 4.8,
                    "price_per_night": 15000,
                    "location": "Benaulim, South Goa",
                    "amenities": ["Private Beach", "Pool", "Spa", "Golf"],
                    "tier": "luxury",
                },
                {
                    "name": "Alila Diwa Goa",
                    "rating": 4.5,
                    "price_per_night": 8000,
                    "location": "Majorda, South Goa",
                    "amenities": ["Pool", "Spa", "Restaurant"],
                    "tier": "luxury",
                },
                {
                    "name": "Acron Waterfront Resort",
                    "rating": 3.9,
                    "price_per_night": 3500,
                    "location": "Baga, North Goa",
                    "amenities": ["Pool", "Restaurant", "Beach Access"],
                    "tier": "mid-range",
                },
                {
                    "name": "Zostel Goa Anjuna",
                    "rating": 3.7,
                    "price_per_night": 800,
                    "location": "Anjuna",
                    "amenities": ["Wi-Fi", "Pool", "Common Area"],
                    "tier": "budget",
                },
            ],
            "bangalore": [
                {
                    "name": "The Leela Palace Bangalore",
                    "rating": 4.8,
                    "price_per_night": 14000,
                    "location": "HAL Airport Road",
                    "amenities": ["Pool", "Spa", "Fine Dining", "Gardens"],
                    "tier": "luxury",
                },
                {
                    "name": "Taj MG Road Bangalore",
                    "rating": 4.4,
                    "price_per_night": 6000,
                    "location": "MG Road",
                    "amenities": ["Pool", "Restaurant", "Bar"],
                    "tier": "mid-range",
                },
                {
                    "name": "Treebo Trend Dee Empresa",
                    "rating": 3.6,
                    "price_per_night": 2200,
                    "location": "Indiranagar",
                    "amenities": ["Wi-Fi", "AC", "Breakfast"],
                    "tier": "mid-range",
                },
                {
                    "name": "Zostel Bangalore",
                    "rating": 3.5,
                    "price_per_night": 700,
                    "location": "Koramangala",
                    "amenities": ["Wi-Fi", "Common Area", "Events"],
                    "tier": "budget",
                },
            ],
            "kolkata": [
                {
                    "name": "The Oberoi Grand",
                    "rating": 4.7,
                    "price_per_night": 10000,
                    "location": "Chowringhee Road",
                    "amenities": ["Pool", "Spa", "Heritage", "Fine Dining"],
                    "tier": "luxury",
                },
                {
                    "name": "The Park Kolkata",
                    "rating": 4.2,
                    "price_per_night": 5000,
                    "location": "Park Street",
                    "amenities": ["Pool", "Nightclub", "Restaurant"],
                    "tier": "mid-range",
                },
                {
                    "name": "Zostel Kolkata",
                    "rating": 3.5,
                    "price_per_night": 600,
                    "location": "Sudder Street",
                    "amenities": ["Wi-Fi", "Common Area"],
                    "tier": "budget",
                },
            ],
            "hyderabad": [
                {
                    "name": "Taj Falaknuma Palace",
                    "rating": 4.9,
                    "price_per_night": 30000,
                    "location": "Falaknuma",
                    "amenities": ["Palace Heritage", "Pool", "Fine Dining"],
                    "tier": "luxury",
                },
                {
                    "name": "Novotel Hyderabad Convention Centre",
                    "rating": 4.3,
                    "price_per_night": 5500,
                    "location": "HICC Complex",
                    "amenities": ["Pool", "Restaurant", "Fitness"],
                    "tier": "mid-range",
                },
                {
                    "name": "Treebo Trend Aditya Hometel",
                    "rating": 3.6,
                    "price_per_night": 1800,
                    "location": "Ameerpet",
                    "amenities": ["Wi-Fi", "AC", "Breakfast"],
                    "tier": "budget",
                },
            ],
            "agra": [
                {
                    "name": "The Oberoi Amarvilas",
                    "rating": 4.9,
                    "price_per_night": 35000,
                    "location": "Taj East Gate Road",
                    "amenities": ["Taj Mahal View", "Pool", "Spa"],
                    "tier": "luxury",
                },
                {
                    "name": "Crystal Sarovar Premiere",
                    "rating": 4.1,
                    "price_per_night": 4000,
                    "location": "Fatehabad Road",
                    "amenities": ["Pool", "Restaurant", "Wi-Fi"],
                    "tier": "mid-range",
                },
                {
                    "name": "Zostel Agra",
                    "rating": 3.6,
                    "price_per_night": 600,
                    "location": "Near Taj Mahal",
                    "amenities": ["Rooftop", "Wi-Fi", "Breakfast"],
                    "tier": "budget",
                },
            ],
            "varanasi": [
                {
                    "name": "Taj Nadesar Palace",
                    "rating": 4.7,
                    "price_per_night": 20000,
                    "location": "Nadesar Palace Grounds",
                    "amenities": ["Heritage", "Pool", "Gardens"],
                    "tier": "luxury",
                },
                {
                    "name": "Hotel Surya Kaiser Palace",
                    "rating": 3.8,
                    "price_per_night": 2500,
                    "location": "The Mall, Cantonment",
                    "amenities": ["Restaurant", "Wi-Fi", "AC"],
                    "tier": "mid-range",
                },
                {
                    "name": "Zostel Varanasi",
                    "rating": 3.7,
                    "price_per_night": 500,
                    "location": "Assi Ghat",
                    "amenities": ["Ghat View", "Wi-Fi", "Café"],
                    "tier": "budget",
                },
            ],
            "kerala": [
                {
                    "name": "Kumarakom Lake Resort",
                    "rating": 4.8,
                    "price_per_night": 18000,
                    "location": "Kumarakom, Kottayam",
                    "amenities": ["Lake View", "Ayurveda Spa", "Pool"],
                    "tier": "luxury",
                },
                {
                    "name": "Fragrant Nature Munnar",
                    "rating": 4.2,
                    "price_per_night": 4500,
                    "location": "Munnar",
                    "amenities": ["Mountain View", "Restaurant", "Spa"],
                    "tier": "mid-range",
                },
                {
                    "name": "Zostel Alleppey",
                    "rating": 3.6,
                    "price_per_night": 800,
                    "location": "Alleppey Beach",
                    "amenities": ["Beach Access", "Wi-Fi", "Kayaking"],
                    "tier": "budget",
                },
            ],
            "udaipur": [
                {
                    "name": "Taj Lake Palace",
                    "rating": 4.9,
                    "price_per_night": 40000,
                    "location": "Pichola Lake",
                    "amenities": ["Lake Palace", "Pool", "Heritage"],
                    "tier": "luxury",
                },
                {
                    "name": "Hotel Lakend",
                    "rating": 4.0,
                    "price_per_night": 3500,
                    "location": "Fateh Sagar Lake",
                    "amenities": ["Lake View", "Restaurant", "Pool"],
                    "tier": "mid-range",
                },
                {
                    "name": "Zostel Udaipur",
                    "rating": 3.7,
                    "price_per_night": 600,
                    "location": "Lal Ghat",
                    "amenities": ["Rooftop", "Wi-Fi", "Lake View"],
                    "tier": "budget",
                },
            ],
            "shimla": [
                {
                    "name": "Wildflower Hall, Shimla",
                    "rating": 4.8,
                    "price_per_night": 22000,
                    "location": "Mashobra",
                    "amenities": ["Spa", "Pool", "Mountain View"],
                    "tier": "luxury",
                },
                {
                    "name": "Hotel Willow Banks",
                    "rating": 3.9,
                    "price_per_night": 3000,
                    "location": "The Mall Road",
                    "amenities": ["Restaurant", "Wi-Fi", "Valley View"],
                    "tier": "mid-range",
                },
                {
                    "name": "Zostel Shimla",
                    "rating": 3.5,
                    "price_per_night": 700,
                    "location": "Near Christ Church",
                    "amenities": ["Wi-Fi", "Common Area", "Café"],
                    "tier": "budget",
                },
            ],
            "manali": [
                {
                    "name": "The Himalayan",
                    "rating": 4.5,
                    "price_per_night": 12000,
                    "location": "Log Huts Area",
                    "amenities": ["Spa", "Restaurant", "Mountain View"],
                    "tier": "luxury",
                },
                {
                    "name": "Hotel Manu Allaya",
                    "rating": 4.0,
                    "price_per_night": 4000,
                    "location": "Circuit House Road",
                    "amenities": ["Spa", "Restaurant", "Wi-Fi"],
                    "tier": "mid-range",
                },
                {
                    "name": "Zostel Manali",
                    "rating": 3.8,
                    "price_per_night": 700,
                    "location": "Old Manali",
                    "amenities": ["Wi-Fi", "Café", "Mountain View"],
                    "tier": "budget",
                },
            ],
            "rishikesh": [
                {
                    "name": "Aloha on the Ganges",
                    "rating": 4.4,
                    "price_per_night": 8000,
                    "location": "Tapovan",
                    "amenities": ["River View", "Pool", "Yoga"],
                    "tier": "luxury",
                },
                {
                    "name": "The Hosteller Rishikesh",
                    "rating": 4.0,
                    "price_per_night": 2000,
                    "location": "Laxman Jhula",
                    "amenities": ["Wi-Fi", "Café", "River View"],
                    "tier": "mid-range",
                },
                {
                    "name": "Zostel Rishikesh",
                    "rating": 3.7,
                    "price_per_night": 600,
                    "location": "Tapovan",
                    "amenities": ["Wi-Fi", "Yoga", "Rafting"],
                    "tier": "budget",
                },
            ],
            "pune": [
                {
                    "name": "Conrad Pune",
                    "rating": 4.6,
                    "price_per_night": 9000,
                    "location": "Koregaon Park",
                    "amenities": ["Pool", "Spa", "Fine Dining"],
                    "tier": "luxury",
                },
                {
                    "name": "Lemon Tree Premier",
                    "rating": 4.0,
                    "price_per_night": 4000,
                    "location": "Hinjewadi",
                    "amenities": ["Pool", "Restaurant", "Fitness"],
                    "tier": "mid-range",
                },
                {
                    "name": "Zostel Pune",
                    "rating": 3.5,
                    "price_per_night": 700,
                    "location": "Koregaon Park",
                    "amenities": ["Wi-Fi", "Common Area"],
                    "tier": "budget",
                },
            ],
            "mysore": [
                {
                    "name": "Radisson Blu Plaza Hotel Mysore",
                    "rating": 4.3,
                    "price_per_night": 5500,
                    "location": "Nazarbad",
                    "amenities": ["Pool", "Spa", "Restaurant"],
                    "tier": "luxury",
                },
                {
                    "name": "Hotel Pai Vista",
                    "rating": 3.8,
                    "price_per_night": 2500,
                    "location": "Nazarbad Main Road",
                    "amenities": ["Restaurant", "Wi-Fi", "AC"],
                    "tier": "mid-range",
                },
                {
                    "name": "Sonder Hostel Mysore",
                    "rating": 3.5,
                    "price_per_night": 500,
                    "location": "Gokulam",
                    "amenities": ["Wi-Fi", "Common Area"],
                    "tier": "budget",
                },
            ],
            "chandigarh": [
                {
                    "name": "The Lalit Chandigarh",
                    "rating": 4.4,
                    "price_per_night": 7000,
                    "location": "IT Park",
                    "amenities": ["Pool", "Spa", "Restaurant"],
                    "tier": "luxury",
                },
                {
                    "name": "Hotel Mountview",
                    "rating": 3.9,
                    "price_per_night": 3500,
                    "location": "Sector 10",
                    "amenities": ["Restaurant", "Wi-Fi", "Garden"],
                    "tier": "mid-range",
                },
                {
                    "name": "Zostel Chandigarh",
                    "rating": 3.5,
                    "price_per_night": 600,
                    "location": "Sector 22",
                    "amenities": ["Wi-Fi", "Common Area"],
                    "tier": "budget",
                },
            ],
            "rajasthan": [
                {
                    "name": "Umaid Bhawan Palace Jodhpur",
                    "rating": 4.9,
                    "price_per_night": 45000,
                    "location": "Jodhpur",
                    "amenities": ["Palace Heritage", "Pool", "Spa"],
                    "tier": "luxury",
                },
                {
                    "name": "Hotel Raas Jodhpur",
                    "rating": 4.4,
                    "price_per_night": 8000,
                    "location": "Tunwarji Ka Jhalra, Jodhpur",
                    "amenities": ["Pool", "Restaurant", "Fort View"],
                    "tier": "mid-range",
                },
                {
                    "name": "Zostel Jodhpur",
                    "rating": 3.7,
                    "price_per_night": 600,
                    "location": "Near Clock Tower, Jodhpur",
                    "amenities": ["Wi-Fi", "Rooftop", "Fort View"],
                    "tier": "budget",
                },
            ],
            "ooty": [
                {
                    "name": "Savoy - IHCL SeleQtions",
                    "rating": 4.5,
                    "price_per_night": 10000,
                    "location": "Sylks Road",
                    "amenities": ["Heritage", "Restaurant", "Garden"],
                    "tier": "luxury",
                },
                {
                    "name": "Hotel Lakeview",
                    "rating": 3.8,
                    "price_per_night": 2500,
                    "location": "West Lake Road",
                    "amenities": ["Lake View", "Restaurant", "Wi-Fi"],
                    "tier": "mid-range",
                },
                {
                    "name": "Zostel Ooty",
                    "rating": 3.5,
                    "price_per_night": 600,
                    "location": "Charring Cross",
                    "amenities": ["Wi-Fi", "Common Area"],
                    "tier": "budget",
                },
            ],
            "darjeeling": [
                {
                    "name": "Mayfair Darjeeling",
                    "rating": 4.5,
                    "price_per_night": 9000,
                    "location": "The Mall",
                    "amenities": ["Spa", "Restaurant", "Mountain View"],
                    "tier": "luxury",
                },
                {
                    "name": "Hotel Sinclairs Darjeeling",
                    "rating": 3.9,
                    "price_per_night": 3500,
                    "location": "Chauk Bazaar",
                    "amenities": ["Restaurant", "Wi-Fi", "Valley View"],
                    "tier": "mid-range",
                },
                {
                    "name": "Zostel Darjeeling",
                    "rating": 3.6,
                    "price_per_night": 600,
                    "location": "Dr. Zakir Hussain Road",
                    "amenities": ["Wi-Fi", "Common Area", "Mountain View"],
                    "tier": "budget",
                },
            ],
        }

    def get_hotels(
        self,
        destination: str,
        accommodation_preference: Optional[str] = None,
        budget: Optional[float] = None,
    ) -> List[Dict]:
        """
        Get hotel recommendations for a destination.

        Args:
            destination: City name (lowercase)
            accommodation_preference: 'budget', 'mid-range', or 'luxury'
            budget: Total trip budget (used to filter)

        Returns:
            List of matching hotel dictionaries
        """
        city_hotels = self.hotels.get(destination.lower(), [])

        if not city_hotels:
            # Fallback: return generic budget options
            logger.warning(f"No hotels found for '{destination}', using fallback")
            return [
                {
                    "name": f"Hotel {destination.title()} Inn",
                    "rating": 3.5,
                    "price_per_night": 2000,
                    "location": f"Central {destination.title()}",
                    "amenities": ["Wi-Fi", "AC", "Restaurant"],
                    "tier": "mid-range",
                }
            ]

        if accommodation_preference:
            tier_map = {
                "budget": "budget",
                "mid-range": "mid-range",
                "luxury": "luxury",
            }
            tier = tier_map.get(accommodation_preference, "mid-range")
            filtered = [h for h in city_hotels if h.get("tier") == tier]
            if filtered:
                return filtered

        return city_hotels


# Singleton instance
hotel_service = HotelService()
