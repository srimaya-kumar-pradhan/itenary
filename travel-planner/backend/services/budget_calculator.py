"""
Smart Budget Calculator — Intelligent budget allocation based on
destination cost-of-living, actual hotel prices, and user preferences.
Replaces the fixed percentage-based split.
"""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class SmartBudgetCalculator:
    """Advanced budget allocation with city awareness and preference tuning."""

    # Cost of living indices by city (relative to base 100)
    CITY_COL_INDEX = {
        "delhi": 95,
        "mumbai": 110,
        "bangalore": 100,
        "hyderabad": 85,
        "jaipur": 75,
        "agra": 70,
        "goa": 90,
        "kerala": 80,
        "chandigarh": 88,
        "pune": 92,
        "kolkata": 82,
        "varanasi": 68,
        "udaipur": 78,
        "shimla": 85,
        "manali": 82,
        "rishikesh": 72,
        "mysore": 75,
        "ooty": 78,
        "darjeeling": 76,
        "rajasthan": 75,
    }

    # Minimum recommended daily budget per person (INR) by city
    DAILY_MINIMUMS = {
        "delhi": 1200,
        "mumbai": 1500,
        "bangalore": 1200,
        "hyderabad": 1000,
        "jaipur": 900,
        "agra": 800,
        "goa": 1000,
        "kerala": 1100,
        "kolkata": 900,
        "varanasi": 700,
        "udaipur": 900,
        "shimla": 1000,
        "manali": 1000,
        "rishikesh": 800,
        "pune": 1000,
        "mysore": 800,
        "ooty": 900,
        "darjeeling": 900,
        "chandigarh": 1000,
        "rajasthan": 900,
    }

    # Average meal costs by city tier (INR per person)
    MEAL_COSTS = {
        "budget": {"breakfast": 100, "lunch": 200, "dinner": 250, "snacks": 50},
        "mid-range": {"breakfast": 200, "lunch": 400, "dinner": 500, "snacks": 100},
        "luxury": {"breakfast": 500, "lunch": 1000, "dinner": 1500, "snacks": 200},
    }

    def calculate_smart_allocation(
        self,
        total_budget: float,
        destination: str,
        duration_days: int,
        travelers: int,
        hotel_prices: List[float],
        preferences: List[str],
        accommodation_preference: str = "mid-range",
    ) -> Tuple[Dict, Dict[str, str]]:
        """
        Calculate optimal budget allocation.

        Args:
            total_budget: Total trip budget in ₹
            destination: Destination city
            duration_days: Trip length in days
            travelers: Number of people
            hotel_prices: List of available hotel prices per night
            preferences: User preference tags
            accommodation_preference: budget / mid-range / luxury

        Returns:
            (allocation: detailed breakdown, notes: explanations)
        """
        allocation: Dict = {}
        notes: Dict[str, str] = {}

        # Step 1: Get COL index
        col_index = self.CITY_COL_INDEX.get(destination.lower(), 100)
        col_multiplier = col_index / 100
        notes["cost_of_living"] = f"{destination.title()} COL index: {col_index}/100"

        # Step 2: Calculate accommodation from actual hotel prices
        if hotel_prices:
            avg_hotel_price = sum(hotel_prices) / len(hotel_prices)
            min_hotel_price = min(hotel_prices)
            accommodation_per_night = avg_hotel_price
        else:
            # Fallback based on accommodation preference
            fallback_prices = {"budget": 800, "mid-range": 2500, "luxury": 8000}
            accommodation_per_night = fallback_prices.get(
                accommodation_preference, 2500
            )
            min_hotel_price = accommodation_per_night

        accommodation_total = accommodation_per_night * duration_days

        # Cap accommodation at 55% of budget
        max_accommodation = total_budget * 0.55
        if accommodation_total > max_accommodation:
            # Use cheapest hotel to fit budget
            accommodation_per_night = min_hotel_price
            accommodation_total = min_hotel_price * duration_days
            if accommodation_total > max_accommodation:
                accommodation_total = max_accommodation
                accommodation_per_night = max_accommodation / duration_days
            notes["accommodation_adjustment"] = (
                "Accommodation capped at 55% of budget. Consider a lower-tier hotel."
            )

        allocation["accommodation_per_night"] = round(accommodation_per_night, 2)
        allocation["accommodation_total"] = round(accommodation_total, 2)
        notes["accommodation"] = f"₹{accommodation_per_night:.0f}/night × {duration_days} nights"

        # Step 3: Calculate meal costs based on city and tier
        meal_tier = accommodation_preference
        base_meals = self.MEAL_COSTS.get(meal_tier, self.MEAL_COSTS["mid-range"])

        # Adjust for COL
        meals_daily = {
            "breakfast": round(base_meals["breakfast"] * col_multiplier),
            "lunch": round(base_meals["lunch"] * col_multiplier),
            "dinner": round(base_meals["dinner"] * col_multiplier),
            "snacks": round(base_meals["snacks"] * col_multiplier),
        }
        meals_daily["total_daily"] = sum(meals_daily.values())
        meals_daily["total_daily_all_travelers"] = meals_daily["total_daily"] * travelers

        meals_total_trip = meals_daily["total_daily_all_travelers"] * duration_days

        allocation["meals"] = {
            **meals_daily,
            "total_trip": round(meals_total_trip, 2),
        }
        notes["meals"] = (
            f"Per-person daily: ₹{meals_daily['total_daily']} "
            f"(adjusted for {destination.title()} COL)"
        )

        # Step 4: Remaining budget for activities, transport, misc
        remaining = total_budget - accommodation_total - meals_total_trip

        if remaining < 0:
            # Budget too tight — squeeze meals
            notes["budget_warning"] = (
                "Budget is tight. Meal estimates reduced to fit."
            )
            meals_total_trip = max((total_budget - accommodation_total) * 0.3, 0)
            remaining = total_budget - accommodation_total - meals_total_trip
            allocation["meals"]["total_trip"] = round(meals_total_trip, 2)

        # Adjust activity/transport split based on preferences
        prefs_lower = [p.lower() for p in preferences]
        if "adventure" in prefs_lower:
            activity_ratio = 0.55
            transport_ratio = 0.25
            notes["preference_adjustment"] = "Adventure: higher activity allocation"
        elif "luxury" in prefs_lower:
            activity_ratio = 0.35
            transport_ratio = 0.30
            notes["preference_adjustment"] = "Luxury: higher transport allocation"
        elif "budget" in prefs_lower:
            activity_ratio = 0.45
            transport_ratio = 0.20
            notes["preference_adjustment"] = "Budget: minimized transport costs"
        else:
            activity_ratio = 0.45
            transport_ratio = 0.25
            notes["preference_adjustment"] = "Balanced allocation"

        tips_ratio = 0.05
        misc_ratio = 1.0 - activity_ratio - transport_ratio - tips_ratio

        allocation["activities_total"] = round(remaining * activity_ratio, 2)
        allocation["activities_per_day"] = round(
            allocation["activities_total"] / max(duration_days, 1), 2
        )
        allocation["local_transport_total"] = round(remaining * transport_ratio, 2)
        allocation["local_transport_per_day"] = round(
            allocation["local_transport_total"] / max(duration_days, 1), 2
        )
        allocation["tips_total"] = round(remaining * tips_ratio, 2)
        allocation["miscellaneous_total"] = round(remaining * misc_ratio, 2)

        # Step 5: Grand total and validation
        computed_total = (
            allocation["accommodation_total"]
            + allocation["meals"]["total_trip"]
            + allocation["activities_total"]
            + allocation["local_transport_total"]
            + allocation["tips_total"]
            + allocation["miscellaneous_total"]
        )

        # Fix rounding variance
        rounding_variance = total_budget - computed_total
        allocation["miscellaneous_total"] = round(
            allocation["miscellaneous_total"] + rounding_variance, 2
        )

        allocation["total_budget"] = round(total_budget, 2)
        allocation["per_person_per_day"] = round(
            total_budget / (duration_days * max(travelers, 1)), 2
        )

        # Step 6: Feasibility warnings
        allocation["warnings"] = []
        daily_per_person = total_budget / (duration_days * max(travelers, 1))
        min_required = self.DAILY_MINIMUMS.get(destination.lower(), 1000)

        if daily_per_person < min_required:
            allocation["warnings"].append(
                f"Daily budget (₹{daily_per_person:.0f}/person) is below the "
                f"recommended minimum (₹{min_required}) for {destination.title()}. "
                f"Trip may be uncomfortable."
            )

        if accommodation_total > total_budget * 0.55:
            allocation["warnings"].append(
                "Accommodation exceeds 55% of budget. Consider cheaper hotels."
            )

        # Budget status
        variance_pct = ((computed_total + rounding_variance) / total_budget - 1) * 100
        if abs(variance_pct) < 1:
            allocation["budget_status"] = "WITHIN_BUDGET"
        elif variance_pct < -5:
            allocation["budget_status"] = "UNDER_BUDGET"
        elif variance_pct > 10:
            allocation["budget_status"] = "SIGNIFICANTLY_OVER"
        elif variance_pct > 0:
            allocation["budget_status"] = "SLIGHTLY_OVER"
        else:
            allocation["budget_status"] = "WITHIN_BUDGET"

        allocation["variance_percentage"] = round(variance_pct, 2)

        logger.info(
            f"Budget allocation for {destination}: "
            f"total=₹{total_budget}, status={allocation['budget_status']}"
        )

        return allocation, notes

    def get_budget_summary_for_prompt(
        self,
        allocation: Dict,
        duration_days: int,
    ) -> Dict[str, int]:
        """
        Convert allocation to simplified budget segments for LLM prompt injection.

        Returns:
            Dict with accommodation, food_and_dining, activities_and_entry,
            transport_and_misc keys
        """
        return {
            "accommodation": round(allocation.get("accommodation_total", 0)),
            "food_and_dining": round(allocation.get("meals", {}).get("total_trip", 0)),
            "activities_and_entry": round(allocation.get("activities_total", 0)),
            "transport_and_misc": round(
                allocation.get("local_transport_total", 0)
                + allocation.get("tips_total", 0)
                + allocation.get("miscellaneous_total", 0)
            ),
        }


# Singleton instance
budget_calculator = SmartBudgetCalculator()
