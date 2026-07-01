"""
LLM Service — Google Gemini integration with enhanced prompt engineering.
Generates structured JSON itineraries with location diversity, meal planning,
transport recommendations, and accurate budget arithmetic.
Includes a comprehensive fallback generator if the LLM call fails.
"""

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import google.generativeai as genai

from config import settings
from prompt_templates import SYSTEM_ROLE_PROMPT, generate_production_prompt

logger = logging.getLogger(__name__)


class LLMService:
    """LLM-powered itinerary generation with Gemini."""

    def __init__(self):
        """Configure Gemini API."""
        self.model = None
        self.api_available = False

        if settings.gemini_api_key and settings.gemini_api_key != "your_gemini_api_key_here":
            try:
                genai.configure(api_key=settings.gemini_api_key)
                self.model = genai.GenerativeModel("gemini-2.0-flash")
                self.api_available = True
                logger.info("Gemini LLM service initialized successfully")
            except Exception as e:
                logger.warning(f"Gemini initialization failed: {e}. Using fallback.")
        else:
            logger.warning("No valid Gemini API key — using fallback itinerary generator")

    def _build_production_prompt(
        self,
        destination: str,
        start_date: str,
        end_date: str,
        budget: float,
        travelers: int,
        preferences: List[str],
        accommodation_preference: str,
        context: str,
        hotels: List[Dict],
        daily_budget: float,
        num_days: int,
        budget_allocation: Optional[Dict] = None,
        transport_info: str = "",
        meal_budget_info: str = "",
    ) -> str:
        """
        Build production prompt using prompt_templates module.

        Assembles user_request, rag_results, hotel_data, budget_allocation,
        transport info, and meal budgets into the structured template.
        """
        # Assemble user request dict for the template
        user_request = {
            "destination": destination,
            "start_date": start_date,
            "end_date": end_date,
            "budget": budget,
            "travelers": travelers,
            "preferences": preferences,
            "accommodation_preference": accommodation_preference,
            "duration_days": num_days,
        }

        # Format hotel data for prompt injection (with coordinates if available)
        hotel_lines = []
        for h in hotels[:3]:
            coords_str = ""
            if h.get("coordinates"):
                coords_str = (
                    f", Coords: ({h['coordinates'].get('lat', 'N/A')}, "
                    f"{h['coordinates'].get('lng', 'N/A')})"
                )
            hotel_lines.append(
                f"  - {h['name']}: ₹{h['price_per_night']}/night, "
                f"Rating: {h.get('rating', 'N/A')}, "
                f"Location: {h.get('location', 'N/A')}, "
                f"Amenities: {', '.join(h.get('amenities', []))}"
                f"{coords_str}"
            )
        hotel_data = "\n".join(hotel_lines) if hotel_lines else "No live hotel data available."

        # Use smart budget allocation if provided, otherwise compute basic one
        if budget_allocation:
            prompt_budget = budget_allocation
        else:
            hotel_cost = hotels[0].get("price_per_night", 2000) if hotels else 2000
            accommodation_total = hotel_cost * num_days
            remaining = budget - accommodation_total
            prompt_budget = {
                "accommodation": round(accommodation_total),
                "food_and_dining": round(remaining * 0.35),
                "activities_and_entry": round(remaining * 0.40),
                "transport_and_misc": round(remaining * 0.25),
            }

        # Truncate RAG context to fit token limits
        rag_results = context[:6000] if context else "No RAG context available."

        return generate_production_prompt(
            user_request=user_request,
            rag_results=rag_results,
            hotel_data=hotel_data,
            budget_allocation=prompt_budget,
            transport_info=transport_info,
            meal_budget_info=meal_budget_info,
        )

    def generate_itinerary(
        self,
        destination: str,
        start_date: str,
        end_date: str,
        budget: float,
        travelers: int,
        preferences: List[str],
        accommodation_preference: str,
        context: str,
        hotels: List[Dict],
        budget_allocation: Optional[Dict] = None,
        transport_info: str = "",
        meal_budget_info: str = "",
    ) -> Dict:
        """
        Generate a complete itinerary using Gemini LLM.
        Falls back to rule-based generator if LLM fails.
        """
        # Calculate trip parameters
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        num_days = (end - start).days
        if num_days <= 0:
            num_days = 1
        daily_budget = budget / num_days

        # Try LLM generation
        if self.api_available and self.model:
            try:
                prompt = self._build_production_prompt(
                    destination, start_date, end_date, budget,
                    travelers, preferences, accommodation_preference,
                    context, hotels, daily_budget, num_days,
                    budget_allocation=budget_allocation,
                    transport_info=transport_info,
                    meal_budget_info=meal_budget_info,
                )

                response = self.model.generate_content(
                    [SYSTEM_ROLE_PROMPT, prompt],
                    generation_config=genai.types.GenerationConfig(
                        temperature=settings.temperature,
                        max_output_tokens=settings.max_tokens,
                    ),
                )

                raw_text = response.text.strip()

                # Clean markdown code fences if present
                if raw_text.startswith("```"):
                    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                    raw_text = re.sub(r"\s*```$", "", raw_text)

                itinerary = json.loads(raw_text)

                # Validate required fields
                if "daily_plans" in itinerary and len(itinerary["daily_plans"]) > 0:
                    # Post-generation validation: check location diversity
                    itinerary = self._validate_location_diversity(itinerary)
                    logger.info("LLM itinerary generated successfully")
                    return itinerary
                else:
                    logger.warning("LLM returned incomplete itinerary, using fallback")

            except json.JSONDecodeError as e:
                logger.error(f"LLM returned invalid JSON: {e}")
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")

        # Fallback to rule-based generator
        logger.info("Using fallback itinerary generator")
        return self._generate_fallback_itinerary(
            destination, start_date, end_date, budget,
            travelers, preferences, accommodation_preference, hotels,
        )

    def _validate_location_diversity(self, itinerary: Dict) -> Dict:
        """
        Post-generation check: warn if same location appears
        in morning and evening of the same day.
        """
        for day in itinerary.get("daily_plans", []):
            morning_activities = day.get("morning", {}).get("activities", [])
            evening_activities = day.get("evening", {}).get("activities", [])

            morning_text = " ".join(morning_activities).lower() if morning_activities else ""
            evening_text = " ".join(evening_activities).lower() if evening_activities else ""

            # Check for overlap in keywords
            morning_words = set(w for w in morning_text.split() if len(w) > 4)
            evening_words = set(w for w in evening_text.split() if len(w) > 4)
            overlap = morning_words & evening_words

            if len(overlap) > 2:  # More than 2 significant words overlap
                if "warnings" not in day:
                    day["warnings"] = []
                day["warnings"].append(
                    f"Location diversity warning: morning and evening may feature similar locations"
                )

        return itinerary

    def _generate_fallback_itinerary(
        self,
        destination: str,
        start_date: str,
        end_date: str,
        budget: float,
        travelers: int,
        preferences: List[str],
        accommodation_preference: str,
        hotels: List[Dict],
    ) -> Dict:
        """
        Enhanced rule-based fallback itinerary generator.
        Produces a valid, structured itinerary with meals, transport,
        and diverse locations — without LLM.
        """
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        num_days = max((end - start).days, 1)
        daily_budget = budget / num_days

        # City-specific attractions
        city_data = self._get_city_data(destination)

        # Pick hotel
        hotel = hotels[0] if hotels else {
            "name": f"Hotel {destination.title()} Stay",
            "price_per_night": 2000,
            "rating": 3.5,
            "location": f"Central {destination.title()}",
        }
        hotel_cost = hotel.get("price_per_night", 2000)

        # Calculate remaining daily budget
        remaining_daily = daily_budget - hotel_cost
        food_daily = remaining_daily * 0.30
        activity_daily = remaining_daily * 0.45
        transport_daily = remaining_daily * 0.15
        misc_daily = remaining_daily * 0.10

        # Meal breakdown
        breakfast_cost = round(food_daily * 0.25)
        lunch_cost = round(food_daily * 0.40)
        dinner_cost = round(food_daily * 0.35)

        daily_plans = []
        used_attractions = set()  # Track used attractions for diversity

        for day_num in range(1, num_days + 1):
            current_date = start + timedelta(days=day_num - 1)
            attractions = city_data["attractions"]
            restaurants = city_data["restaurants"]

            # Pick 3 DIFFERENT attractions for morning, afternoon, evening
            morning_idx = (day_num * 3 - 3) % len(attractions)
            afternoon_idx = (day_num * 3 - 2) % len(attractions)
            evening_idx = (day_num * 3 - 1) % len(attractions)

            # Ensure they're all different
            if afternoon_idx == morning_idx:
                afternoon_idx = (afternoon_idx + 1) % len(attractions)
            if evening_idx == morning_idx or evening_idx == afternoon_idx:
                evening_idx = (evening_idx + 2) % len(attractions)

            morning_attraction = attractions[morning_idx]
            afternoon_attraction = attractions[afternoon_idx]
            evening_attraction = attractions[evening_idx]

            rest_idx = (day_num - 1) % len(restaurants)

            morning_cost = round(activity_daily * 0.4)
            afternoon_cost = round(activity_daily * 0.35)
            evening_cost = round(activity_daily * 0.25)

            transport_leg_cost = round(transport_daily / 3)

            day_meals_cost = breakfast_cost + lunch_cost + dinner_cost
            day_transport_cost = transport_leg_cost * 3
            day_activities_cost = morning_cost + afternoon_cost + evening_cost
            day_total = day_activities_cost + day_meals_cost + day_transport_cost + hotel_cost

            day_plan = {
                "day": day_num,
                "date": current_date.strftime("%Y-%m-%d"),
                "theme": city_data["themes"][day_num % len(city_data["themes"]) - 1],
                "morning": {
                    "activity": f"Visit {morning_attraction}",
                    "time": "09:00 - 12:00",
                    "cost": morning_cost,
                    "description": (
                        f"Explore {morning_attraction}, one of {destination.title()}'s "
                        f"most iconic landmarks. Perfect for photography and cultural immersion."
                    ),
                },
                "afternoon": {
                    "activity": f"Lunch at {restaurants[rest_idx]} & visit {afternoon_attraction}",
                    "time": "12:30 - 17:00",
                    "cost": afternoon_cost,
                    "description": (
                        f"Enjoy authentic local cuisine at {restaurants[rest_idx]}, "
                        f"followed by exploring {afternoon_attraction}."
                    ),
                },
                "evening": {
                    "activity": f"Evening at {evening_attraction}",
                    "time": "17:30 - 21:00",
                    "cost": evening_cost,
                    "description": (
                        f"Experience the evening ambiance at {evening_attraction}. "
                        f"End the day with local street food and cultural performances."
                    ),
                },
                "meals": [
                    {
                        "type": "breakfast",
                        "restaurant": hotel.get("name", "Hotel restaurant"),
                        "cuisine": "Continental/Indian",
                        "estimated_cost": breakfast_cost,
                    },
                    {
                        "type": "lunch",
                        "restaurant": restaurants[rest_idx],
                        "cuisine": "Local cuisine",
                        "estimated_cost": lunch_cost,
                    },
                    {
                        "type": "dinner",
                        "restaurant": restaurants[(rest_idx + 1) % len(restaurants)],
                        "cuisine": "Local cuisine",
                        "estimated_cost": dinner_cost,
                    },
                ],
                "transport": [
                    {
                        "from": hotel.get("name", "Hotel"),
                        "to": morning_attraction,
                        "mode": "auto",
                        "cost": transport_leg_cost,
                        "time_minutes": 20,
                    },
                    {
                        "from": morning_attraction,
                        "to": afternoon_attraction,
                        "mode": "auto",
                        "cost": transport_leg_cost,
                        "time_minutes": 25,
                    },
                    {
                        "from": afternoon_attraction,
                        "to": evening_attraction,
                        "mode": "auto",
                        "cost": transport_leg_cost,
                        "time_minutes": 20,
                    },
                ],
                "activities_cost": day_activities_cost,
                "meals_cost": day_meals_cost,
                "transport_cost": day_transport_cost,
                "hotel_cost": hotel_cost,
                "day_total": day_total,
            }
            daily_plans.append(day_plan)

        # Budget summary — accurate arithmetic
        total_activities = sum(d["activities_cost"] for d in daily_plans)
        total_meals = sum(d["meals_cost"] for d in daily_plans)
        total_transport = sum(d["transport_cost"] for d in daily_plans)
        accommodation_total = hotel_cost * num_days
        total_estimated = total_activities + total_meals + total_transport + accommodation_total

        return {
            "destination": destination.title(),
            "daily_plans": daily_plans,
            "budget_summary": {
                "accommodation_total": accommodation_total,
                "accommodation": accommodation_total,
                "food_total": total_meals,
                "food_and_dining": total_meals,
                "activities_total": total_activities,
                "activities_and_entry": total_activities,
                "transport_total": total_transport,
                "transport_and_misc": total_transport,
                "miscellaneous": round(misc_daily * num_days),
                "total_estimated": total_estimated,
            },
            "cost_verification": {
                "daily_sum": total_estimated,
                "allocated_budget": budget,
                "variance_percentage": round(
                    ((total_estimated - budget) / budget) * 100, 1
                ),
                "status": (
                    "WITHIN_BUDGET" if total_estimated <= budget * 1.05
                    else "OVER_BUDGET"
                ),
            },
            "travel_tips": city_data["tips"],
            "hidden_gems": city_data["hidden_gems"],
            "emergency_contacts": {
                "police": "100",
                "ambulance": "102",
                "tourist_helpline": "1363",
                "women_helpline": "1091",
                "fire": "101",
            },
        }

    def _get_city_data(self, destination: str) -> Dict:
        """Get curated city-specific travel data for fallback generation."""
        city_database = {
            "delhi": {
                "attractions": [
                    "Red Fort", "Qutub Minar", "India Gate", "Humayun's Tomb",
                    "Lotus Temple", "Akshardham Temple", "Jama Masjid",
                    "Chandni Chowk", "Lodhi Gardens", "Hauz Khas Village",
                ],
                "restaurants": [
                    "Karim's (Jama Masjid)", "Paranthe Wali Gali",
                    "Indian Accent", "Bukhara (ITC Maurya)",
                    "Saravana Bhavan (Connaught Place)", "Al Jawahar",
                    "Gulati Restaurant", "Moti Mahal",
                ],
                "themes": [
                    "Mughal Heritage Trail", "Modern Delhi & Culture",
                    "Old Delhi Food Walk", "Spiritual & Sacred Sites",
                    "Art & Architecture", "Markets & Shopping",
                ],
                "tips": [
                    "Use Delhi Metro for efficient travel — it covers most tourist spots",
                    "Visit Red Fort early morning (9 AM) to avoid crowds and heat",
                    "Carry a water bottle and sunscreen — Delhi summers exceed 40°C",
                    "Try street food at Chandni Chowk but stick to busy stalls for hygiene",
                    "Book an auto-rickshaw via Uber/Ola to avoid price negotiations",
                ],
                "hidden_gems": [
                    {"name": "Agrasen ki Baoli", "description": "A stunning 14th-century stepwell hidden in the heart of central Delhi, offering a surreal photo opportunity", "cost": 0},
                    {"name": "Mehrauli Archaeological Park", "description": "Sprawling ruins park near Qutub Minar with Balban's Tomb and Jamali Kamali Mosque — rarely visited by tourists", "cost": 0},
                    {"name": "Sunder Nursery", "description": "Beautifully restored Mughal-era garden complex with heritage monuments, now a public park", "cost": 50},
                ],
            },
            "mumbai": {
                "attractions": [
                    "Gateway of India", "Marine Drive", "Elephanta Caves",
                    "Chhatrapati Shivaji Terminus", "Haji Ali Dargah",
                    "Siddhivinayak Temple", "Bandra-Worli Sea Link",
                    "Colaba Causeway", "Juhu Beach", "Dharavi",
                ],
                "restaurants": [
                    "Leopold Cafe", "Britannia & Co.", "Trishna",
                    "Bademiya (Colaba)", "Cafe Mondegar",
                    "Swati Snacks", "Bastian", "Peshawri (ITC Maratha)",
                ],
                "themes": [
                    "Colonial Heritage Walk", "Coastal Mumbai",
                    "Bollywood & Entertainment", "Street Food Trail",
                    "Art & Culture", "Island Exploration",
                ],
                "tips": [
                    "Take the local train during non-peak hours for an authentic Mumbai experience",
                    "Visit Marine Drive at sunset — it's called the Queen's Necklace for a reason",
                    "Ferry to Elephanta Caves departs from Gateway of India — book early",
                    "Mumbai's street food (vada pav, pav bhaji) is legendary — try stalls near Chowpatty",
                    "Monsoon season (June-Sept) brings heavy rains — carry an umbrella always",
                ],
                "hidden_gems": [
                    {"name": "Banganga Tank", "description": "An ancient water tank in Malabar Hill dating to the Silhara dynasty, surrounded by temples", "cost": 0},
                    {"name": "Khotachiwadi Heritage Village", "description": "A cluster of Portuguese-style bungalows in Girgaon — one of Mumbai's last East Indian villages", "cost": 0},
                ],
            },
            "jaipur": {
                "attractions": [
                    "Amber Fort", "Hawa Mahal", "City Palace",
                    "Jantar Mantar", "Nahargarh Fort", "Jal Mahal",
                    "Albert Hall Museum", "Birla Mandir", "Johari Bazaar",
                ],
                "restaurants": [
                    "LMB (Laxmi Mishthan Bhandar)", "Tapri Central",
                    "Bar Palladio", "1135 AD (Amber Fort)", "Rawat Mishthan Bhandar",
                    "Niros", "Suvarna Mahal (Rambagh Palace)",
                ],
                "themes": [
                    "Royal Rajputana Heritage", "Forts & Palaces Trail",
                    "Pink City Food Walk", "Art & Crafts Discovery",
                    "Sunset Points & Photography", "Bazaar Shopping Spree",
                ],
                "tips": [
                    "Buy a composite ticket for Amber Fort, Jantar Mantar, Hawa Mahal, and Nahargarh Fort",
                    "Visit Amber Fort by 9 AM and consider the elephant ride (book ethically)",
                    "Jaipur is best explored Oct-March; summers reach 45°C",
                    "Bargain at Johari Bazaar — start at 40% of the quoted price",
                    "Watch the sunset from Nahargarh Fort for panoramic city views",
                ],
                "hidden_gems": [
                    {"name": "Panna Meena ka Kund", "description": "A stunning geometric stepwell near Amber Fort — Instagram-famous but still uncrowded", "cost": 0},
                    {"name": "Chand Baori (Abhaneri)", "description": "One of India's deepest stepwells, 3,500 steps in a mesmerizing geometric pattern (2 hr drive)", "cost": 100},
                ],
            },
            "goa": {
                "attractions": [
                    "Basilica of Bom Jesus", "Aguada Fort", "Dudhsagar Falls",
                    "Anjuna Flea Market", "Baga Beach", "Palolem Beach",
                    "Old Goa Churches", "Chapora Fort", "Spice Plantations",
                ],
                "restaurants": [
                    "Fisherman's Wharf", "Gunpowder", "Thalassa",
                    "Martin's Corner", "Vinayak Family Restaurant",
                    "Cafe Bodega", "Bomra's",
                ],
                "themes": [
                    "Beach & Chill Day", "Heritage Portuguese Trail",
                    "Adventure & Water Sports", "South Goa Serenity",
                    "Nightlife & Culture", "Nature & Spice Trail",
                ],
                "tips": [
                    "Rent a scooter (₹300-500/day) — it's the best way to explore Goa",
                    "Visit Dudhsagar Falls during monsoon (July-Sept) for full water flow",
                    "South Goa beaches (Palolem, Agonda) are calmer than North Goa",
                    "Attend the Saturday Night Market at Arpora for food, music, and shopping",
                    "Carry cash — many beach shacks and local shops don't accept cards",
                ],
                "hidden_gems": [
                    {"name": "Divar Island", "description": "A peaceful island accessible by free ferry — Portuguese churches, paddy fields, and zero tourists", "cost": 0},
                    {"name": "Butterfly Beach", "description": "Accessible only by boat from Palolem — a secluded paradise for snorkeling", "cost": 500},
                ],
            },
        }

        # Default data for cities not in the detailed database
        default_data = {
            "attractions": [
                f"Main Temple of {destination.title()}",
                f"{destination.title()} Fort",
                f"Central Market of {destination.title()}",
                f"{destination.title()} Museum",
                f"Lake / Garden in {destination.title()}",
                f"Old Town of {destination.title()}",
            ],
            "restaurants": [
                f"Local Thali House",
                f"{destination.title()} Bhavan",
                f"Street Food Market",
                f"Heritage Restaurant",
                f"Rooftop Cafe",
            ],
            "themes": [
                "Heritage & History Exploration",
                "Local Culture Immersion",
                "Nature & Scenic Beauty",
                "Food & Market Discovery",
            ],
            "tips": [
                f"Best time to visit {destination.title()} is October to March",
                "Carry comfortable walking shoes for exploration",
                "Download offline maps as network coverage can be patchy",
                "Try local cuisine at small family-run restaurants for authentic flavors",
                "Respect local customs and dress modestly when visiting religious sites",
            ],
            "hidden_gems": [
                {"name": f"Old Quarter of {destination.title()}", "description": "Walk through centuries-old lanes with traditional architecture", "cost": 0},
                {"name": f"Sunrise Point near {destination.title()}", "description": "A local favorite for stunning morning views", "cost": 0},
            ],
        }

        return city_database.get(destination.lower(), default_data)


# Singleton instance
llm_service = LLMService()
