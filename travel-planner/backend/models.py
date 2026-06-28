"""
Pydantic data models for request/response validation.
Defines the complete schema for trip requests and itinerary responses.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict
from datetime import date


class TripRequest(BaseModel):
    """Validated trip request input from the user."""

    destination: str = Field(..., min_length=2, max_length=100)
    start_date: date
    end_date: date
    budget: float = Field(..., gt=0)
    travelers: int = Field(default=1, ge=1, le=20)
    preferences: List[str] = Field(
        default=["Historical", "Budget"],
        description="Historical, Adventure, Beach, Budget, Luxury, Cultural",
    )
    accommodation_preference: str = Field(
        default="mid-range",
        description="budget, mid-range, luxury",
    )
    special_requirements: Optional[str] = None

    @field_validator("destination")
    @classmethod
    def validate_destination(cls, v: str) -> str:
        """Ensure destination is a supported Indian city."""
        valid_cities = {
            "delhi", "mumbai", "bangalore", "hyderabad", "jaipur",
            "kolkata", "pune", "chandigarh", "kerala", "goa",
            "rajasthan", "agra", "varanasi", "udaipur", "shimla",
            "manali", "rishikesh", "mysore", "ooty", "darjeeling",
        }
        if v.lower().strip() not in valid_cities:
            raise ValueError(
                f"Destination '{v}' is not supported. "
                f"Choose from: {', '.join(sorted(valid_cities))}"
            )
        return v.lower().strip()

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v: date, info) -> date:
        """Ensure end_date is after start_date."""
        start = info.data.get("start_date")
        if start and v <= start:
            raise ValueError("end_date must be after start_date")
        if start and (v - start).days > 14:
            raise ValueError("Trip duration cannot exceed 14 days")
        return v


class HotelOption(BaseModel):
    """Hotel recommendation data model."""

    name: str
    rating: float = Field(ge=0, le=5)
    price_per_night: float = Field(ge=0)
    location: str
    amenities: List[str] = []
    booking_link: Optional[str] = None


class ActivityRecommendation(BaseModel):
    """Activity/attraction data model."""

    name: str
    type: str
    duration_hours: float = Field(ge=0)
    estimated_cost: float = Field(ge=0)
    description: str
    coordinates: Optional[Dict[str, float]] = None


class DayPlan(BaseModel):
    """Single day itinerary plan."""

    day: int
    date: str
    theme: str = ""
    morning: Dict = {}
    afternoon: Dict = {}
    evening: Dict = {}
    hotel: Optional[Dict] = None
    day_total: float = 0


class ItineraryResponse(BaseModel):
    """Complete itinerary response."""

    destination: str
    duration_days: int
    total_budget: float
    total_cost_estimated: float
    daily_plans: List[DayPlan] = []
    hotels: List[HotelOption] = []
    budget_breakdown: Dict[str, float] = {}
    travel_tips: List[str] = []
    emergency_contacts: Dict[str, str] = {}
    hidden_gems: List[Dict] = []
    disclaimer: str = "Costs are estimated and may vary based on season and availability."
