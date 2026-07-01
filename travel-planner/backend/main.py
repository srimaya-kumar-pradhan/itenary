"""
FastAPI Main Application — Travel Planner API.
Orchestrates the RAG → Hotels → Budget → Transport → LLM pipeline.
Enhanced with geospatial validation, smart budgeting, and transport integration.
"""

import logging
import sys
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from models import TripRequest, TranslationRequest, TranslationResponse
from bhashini import bhashini_service
from rag import rag_pipeline
from llm import llm_service
from hotel_api import hotel_service
from data_loader import load_all_data
from geocoding import geocode_itinerary
from services.budget_calculator import budget_calculator
from services.transport_service import transport_service
from services.hotel_aggregation_service import hotel_aggregation_service
from services.geospatial_service import geospatial_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle events."""
    # Startup
    logger.info("Starting Travel Planner API...")
    try:
        rag_pipeline.initialize()
        total_docs = load_all_data(rag_pipeline)
        logger.info(f"RAG system ready with {total_docs} documents")
    except Exception as e:
        logger.error(f"Startup initialization failed: {e}")
        logger.warning("API will run with limited functionality")

    yield

    # Shutdown
    logger.info("Shutting down Travel Planner API...")


app = FastAPI(
    title="Intelligent Travel Planner API",
    description="RAG-powered travel itinerary generator for Indian destinations",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — permit cross-origin requests from frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    """Health check endpoint with dependency status."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "dependencies": {
            "chromadb": "connected" if rag_pipeline._initialized else "not_initialized",
            "gemini_api": "authenticated" if llm_service.api_available else "fallback_mode",
            "hotel_service": "operational",
            "geospatial_service": "operational",
            "transport_service": "operational",
            "budget_calculator": "operational",
        },
    }


@app.post("/api/generate-itinerary")
async def generate_itinerary(request: TripRequest):
    """
    Main itinerary generation pipeline.

    Enhanced Pipeline stages:
    1. Validate input & calculate parameters
    2. RAG context retrieval (city-scoped)
    3. Hotel data fetch + multi-platform enrichment
    4. Smart budget calculation (city-aware)
    5. Transport context assembly
    6. LLM itinerary generation (with diversity + meals + transport)
    7. Geocoding integration
    8. Post-generation validation
    9. Response normalization & assembly
    """
    logger.info(
        f"Generating itinerary: {request.destination}, "
        f"budget=₹{request.budget}, "
        f"dates={request.start_date} to {request.end_date}"
    )

    try:
        # --- Stage 1: Calculate trip parameters ---
        num_days = (request.end_date - request.start_date).days
        if num_days <= 0:
            raise HTTPException(status_code=400, detail="Invalid date range")

        daily_budget = request.budget / num_days

        # --- Stage 2: RAG Context Retrieval (city-scoped) ---
        context = ""
        try:
            context = rag_pipeline.build_context(
                destination=request.destination,
                preferences=request.preferences,
                budget=request.budget,
            )
            logger.info(f"RAG context built: {len(context)} chars")
        except Exception as e:
            logger.warning(f"RAG retrieval failed (continuing without context): {e}")

        # --- Stage 3: Hotel Data Fetch + Multi-Platform Enrichment ---
        hotels = hotel_service.get_hotels(
            destination=request.destination,
            accommodation_preference=request.accommodation_preference,
            budget=request.budget,
        )
        logger.info(f"Found {len(hotels)} hotels for {request.destination}")

        # Enrich with coordinates and price comparisons
        try:
            hotels = hotel_aggregation_service.enrich_hotels_with_comparison(
                hotels=hotels,
                destination=request.destination,
                duration_days=num_days,
            )
            logger.info(f"Enriched {len(hotels)} hotels with multi-platform pricing")
        except Exception as e:
            logger.warning(f"Hotel enrichment failed (continuing with basic data): {e}")

        # --- Stage 4: Smart Budget Calculation ---
        hotel = hotels[0] if hotels else {"price_per_night": 2000}
        hotel_cost_per_night = hotel.get("best_price", hotel.get("price_per_night", 2000))
        hotel_prices = [h.get("best_price", h.get("price_per_night", 2000)) for h in hotels]

        try:
            smart_allocation, budget_notes = budget_calculator.calculate_smart_allocation(
                total_budget=request.budget,
                destination=request.destination,
                duration_days=num_days,
                travelers=request.travelers,
                hotel_prices=hotel_prices,
                preferences=request.preferences,
                accommodation_preference=request.accommodation_preference,
            )
            budget_for_prompt = budget_calculator.get_budget_summary_for_prompt(
                smart_allocation, num_days
            )
            logger.info(f"Smart budget: {smart_allocation.get('budget_status', 'N/A')}")
        except Exception as e:
            logger.warning(f"Smart budget failed, using basic allocation: {e}")
            remaining_daily = daily_budget - hotel_cost_per_night
            smart_allocation = {
                "accommodation_per_night": hotel_cost_per_night,
                "accommodation_total": hotel_cost_per_night * num_days,
                "meals": {"total_trip": round(remaining_daily * 0.35 * num_days)},
                "activities_total": round(remaining_daily * 0.45 * num_days),
                "local_transport_total": round(remaining_daily * 0.15 * num_days),
                "tips_total": round(remaining_daily * 0.02 * num_days),
                "miscellaneous_total": round(remaining_daily * 0.03 * num_days),
                "total_budget": request.budget,
                "budget_status": "WITHIN_BUDGET",
                "warnings": [],
            }
            budget_for_prompt = {
                "accommodation": round(hotel_cost_per_night * num_days),
                "food_and_dining": round(remaining_daily * 0.35 * num_days),
                "activities_and_entry": round(remaining_daily * 0.40 * num_days),
                "transport_and_misc": round(remaining_daily * 0.25 * num_days),
            }
            budget_notes = {}

        # --- Stage 5: Transport Context Assembly ---
        transport_info = ""
        try:
            transport_info = transport_service.get_transport_summary_for_prompt(
                request.destination
            )
            logger.info(f"Transport context assembled for {request.destination}")
        except Exception as e:
            logger.warning(f"Transport context assembly failed: {e}")

        # Meal budget info for prompt
        meals_data = smart_allocation.get("meals", {})
        meal_budget_info = (
            f"Breakfast: ₹{meals_data.get('breakfast', 200)}/person, "
            f"Lunch: ₹{meals_data.get('lunch', 400)}/person, "
            f"Dinner: ₹{meals_data.get('dinner', 500)}/person"
        )

        # Hotel comparison summary for prompt
        hotel_comparison_summary = ""
        try:
            hotel_comparison_summary = hotel_aggregation_service.get_price_comparison_summary(
                hotels
            )
        except Exception:
            pass

        # --- Stage 6: LLM Itinerary Generation ---
        itinerary = llm_service.generate_itinerary(
            destination=request.destination,
            start_date=str(request.start_date),
            end_date=str(request.end_date),
            budget=request.budget,
            travelers=request.travelers,
            preferences=request.preferences,
            accommodation_preference=request.accommodation_preference,
            context=context,
            hotels=hotels,
            budget_allocation=budget_for_prompt,
            transport_info=transport_info,
            meal_budget_info=meal_budget_info,
        )

        # --- Stage 7: Geocoding Integration ---
        try:
            itinerary = geocode_itinerary(itinerary, request.destination)
            logger.info("Itinerary geocoding completed successfully.")
        except Exception as e:
            logger.error(f"Itinerary geocoding failed: {e}")

        # --- Stage 8: Post-Generation Validation ---
        validation_warnings = []
        try:
            # Check feasibility of daily plans using geospatial service
            for day in itinerary.get("daily_plans", []):
                activities = []
                for period in ["morning", "afternoon", "evening"]:
                    slot = day.get(period, {})
                    if slot and slot.get("coordinates"):
                        activities.append({
                            "coordinates": slot["coordinates"],
                            "duration_minutes": 120,  # 2 hours per slot
                        })

                if len(activities) >= 2:
                    is_feasible, warnings, _ = geospatial_service.validate_activity_sequence(
                        activities, time_available_minutes=720  # 12 hours
                    )
                    if not is_feasible:
                        validation_warnings.extend(warnings)
                        if "warnings" not in day:
                            day["warnings"] = []
                        day["warnings"].extend(warnings)
        except Exception as e:
            logger.warning(f"Post-generation validation failed: {e}")

        # --- Stage 9: Response Normalization & Assembly ---
        budget_summary = itinerary.get("budget_summary", {})
        normalized_budget = {
            "accommodation_total": budget_summary.get("accommodation_total",
                budget_summary.get("accommodation", hotel_cost_per_night * num_days)),
            "food_total": budget_summary.get("food_total",
                budget_summary.get("food_and_dining",
                    smart_allocation.get("meals", {}).get("total_trip",
                        daily_budget * 0.35 * num_days))),
            "activities_total": budget_summary.get("activities_total",
                budget_summary.get("activities_and_entry",
                    smart_allocation.get("activities_total", daily_budget * 0.40 * num_days))),
            "transport_total": budget_summary.get("transport_total",
                budget_summary.get("transport_and_misc",
                    smart_allocation.get("local_transport_total", daily_budget * 0.15 * num_days))),
            "miscellaneous": budget_summary.get("miscellaneous",
                round(request.budget * 0.05)),
            "total_estimated": budget_summary.get("total_estimated",
                request.budget),
        }
        itinerary["budget_summary"] = normalized_budget

        if "travel_tips" not in itinerary or not itinerary["travel_tips"]:
            itinerary["travel_tips"] = [
                f"Best time to visit {request.destination.title()} is October to March",
                "Carry a reusable water bottle and stay hydrated",
                "Download offline maps for navigation without internet",
                "Keep a photocopy of your ID separately from the original",
                "Try local cuisine at family-run restaurants for authentic flavors",
            ]

        if "emergency_contacts" not in itinerary:
            itinerary["emergency_contacts"] = {
                "police": "100",
                "ambulance": "102",
                "tourist_helpline": "1363",
                "women_helpline": "1091",
                "fire": "101",
            }

        # Build transport summary
        transport_summary = None
        try:
            metro_info = transport_service.get_metro_info(request.destination)
            daily_transport = transport_service.estimate_daily_transport_cost(
                city=request.destination,
                budget_preference=request.accommodation_preference,
            )
            transport_summary = {
                "has_metro": metro_info is not None,
                "metro_info": metro_info,
                "daily_estimate": daily_transport,
            }
        except Exception:
            pass

        response = {
            "success": True,
            "data": itinerary,
            "summary": {
                "destination": request.destination.title(),
                "duration_days": num_days,
                "total_budget": request.budget,
                "total_estimated_cost": normalized_budget.get("total_estimated", request.budget),
                "travelers": request.travelers,
                "accommodation_type": request.accommodation_preference,
                "hotel_recommended": hotels[0]["name"] if hotels else "N/A",
                "hotel_cost_per_night": hotel_cost_per_night,
            },
            # Enhanced response fields
            "budget_detailed": smart_allocation,
            "budget_notes": budget_notes,
            "hotel_comparison": [
                {
                    "name": h.get("name"),
                    "rating": h.get("rating"),
                    "location": h.get("location"),
                    "coordinates": h.get("coordinates"),
                    "amenities": h.get("amenities", []),
                    "price_comparisons": h.get("price_comparisons", []),
                    "best_price": h.get("best_price"),
                    "best_platform": h.get("best_platform"),
                    "savings": h.get("savings", 0),
                    "savings_percentage": h.get("savings_percentage", 0),
                    "booking_links": h.get("booking_links", {}),
                    "tier": h.get("tier"),
                }
                for h in hotels[:5]
            ],
            "transport_summary": transport_summary,
            "validation_warnings": validation_warnings,
        }

        logger.info(
            f"Itinerary generated successfully for {request.destination.title()}"
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Itinerary generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate itinerary: {str(e)}",
        )


@app.post("/api/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """
    Batch translation endpoint.
    Proxies to Bhashini ULCA API for Indian languages.
    Returns original text for unsupported languages.
    """
    logger.info(
        f"Translation requested: {request.source_lang} → {request.target_lang}, "
        f"{len(request.texts)} texts"
    )

    try:
        translated = bhashini_service.translate_batch(
            texts=request.texts,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
        )

        return TranslationResponse(
            translations=translated,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
        )
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return TranslationResponse(
            translations=request.texts,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
    )
