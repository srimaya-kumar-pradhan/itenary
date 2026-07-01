"""
Pydantic data models for request/response validation.
Defines the complete schema for trip requests and itinerary responses.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict
from datetime import date


class TranslationRequest(BaseModel):
    """Batch translation request for Bhashini / i18n proxy."""
    texts: List[str] = Field(..., min_length=1, max_length=100)
    source_lang: str = Field(default="en", max_length=5)
    target_lang: str = Field(..., max_length=5)


class TranslationResponse(BaseModel):
    """Batch translation response."""
    translations: List[str]
    source_lang: str
    target_lang: str


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


class Coordinates(BaseModel):
    """Geographic coordinates (WGS84)."""
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class TransportOption(BaseModel):
    """Transportation between locations."""
    mode: str  # metro, auto, taxi, bus, walking
    cost: float = 0
    estimated_time_minutes: int = 0
    distance_km: float = 0


class MealPlan(BaseModel):
    """Meal plan for a time slot."""
    type: str  # breakfast, lunch, dinner, snacks
    restaurant: Optional[str] = None
    cuisine: Optional[str] = None
    estimated_cost: float = 0
    coordinates: Optional[Dict[str, float]] = None


class PriceComparison(BaseModel):
    """Multi-platform price comparison entry."""
    platform: str  # booking, agoda, makemytrip
    price_per_night: float
    total_price: float = 0
    currency: str = "INR"
    taxes_included: bool = True
    url: Optional[str] = None
    availability: bool = True


class HotelOption(BaseModel):
    """Hotel recommendation data model — enhanced with geo and pricing."""

    name: str
    rating: float = Field(ge=0, le=5)
    price_per_night: float = Field(ge=0)
    location: str
    amenities: List[str] = []
    booking_link: Optional[str] = None
    # Enhanced fields (all optional for backward compatibility)
    coordinates: Optional[Dict[str, float]] = None
    price_comparisons: Optional[List[Dict]] = None
    best_price: Optional[float] = None
    best_platform: Optional[str] = None
    average_price: Optional[float] = None
    savings: Optional[float] = None
    savings_percentage: Optional[float] = None
    booking_links: Optional[Dict[str, str]] = None
    tier: Optional[str] = None


class ActivityRecommendation(BaseModel):
    """Activity/attraction data model."""

    name: str
    type: str
    duration_hours: float = Field(ge=0)
    estimated_cost: float = Field(ge=0)
    description: str
    coordinates: Optional[Dict[str, float]] = None


class DayPlan(BaseModel):
    """Single day itinerary plan — enhanced with meals, transport."""

    day: int
    date: str
    theme: str = ""
    morning: Dict = {}
    afternoon: Dict = {}
    evening: Dict = {}
    hotel: Optional[Dict] = None
    day_total: float = 0
    # Enhanced fields
    meals: Optional[List[Dict]] = None
    transport: Optional[List[Dict]] = None
    activities_cost: Optional[float] = None
    meals_cost: Optional[float] = None
    transport_cost: Optional[float] = None
    hotel_cost: Optional[float] = None
    warnings: Optional[List[str]] = None


class ItineraryResponse(BaseModel):
    """Complete itinerary response — enhanced with all 11-issue fixes."""

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
    # Enhanced fields
    budget_detailed: Optional[Dict] = None
    budget_status: Optional[str] = None
    budget_variance_percentage: Optional[float] = None
    transport_summary: Optional[Dict] = None
    hotel_comparison: Optional[List[Dict]] = None
