"""
FastAPI Main Application — Travel Planner API.
Orchestrates the RAG → Hotels → Budget → LLM pipeline.
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
    version="1.0.0",
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
        "version": "1.0.0",
        "dependencies": {
            "chromadb": "connected" if rag_pipeline._initialized else "not_initialized",
            "gemini_api": "authenticated" if llm_service.api_available else "fallback_mode",
            "hotel_service": "operational",
        },
    }


@app.post("/api/generate-itinerary")
async def generate_itinerary(request: TripRequest):
    """
    Main itinerary generation pipeline.

    Pipeline stages:
    1. Validate input
    2. RAG context retrieval
    3. Hotel data fetch
    4. Budget calculation
    5. LLM itinerary generation
    6. Response normalization & assembly
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

        # --- Stage 2: RAG Context Retrieval ---
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

        # --- Stage 3: Hotel Data Fetch ---
        hotels = hotel_service.get_hotels(
            destination=request.destination,
            accommodation_preference=request.accommodation_preference,
            budget=request.budget,
        )
        logger.info(f"Found {len(hotels)} hotels for {request.destination}")

        # --- Stage 4: Budget Allocation ---
        hotel = hotels[0] if hotels else {"price_per_night": 2000}
        hotel_cost_per_night = hotel.get("price_per_night", 2000)
        remaining_daily = daily_budget - hotel_cost_per_night

        budget_allocation = {
            "accommodation_per_night": hotel_cost_per_night,
            "food_per_day": round(remaining_daily * 0.35),
            "activities_per_day": round(remaining_daily * 0.45),
            "transport_per_day": round(remaining_daily * 0.15),
            "miscellaneous_per_day": round(remaining_daily * 0.05),
        }
        logger.info(f"Budget allocation: {budget_allocation}")

        # --- Stage 5: LLM Itinerary Generation ---
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
        )

        # --- Stage 5b: Geocoding Integration ---
        try:
            itinerary = geocode_itinerary(itinerary, request.destination)
            logger.info("Itinerary geocoding completed successfully.")
        except Exception as e:
            logger.error(f"Itinerary geocoding failed: {e}")

        # --- Stage 6: Response Normalization & Assembly ---
        # Normalize budget_summary keys (LLM schema vs fallback schema)
        budget_summary = itinerary.get("budget_summary", {})
        normalized_budget = {
            "accommodation_total": budget_summary.get("accommodation_total",
                budget_summary.get("accommodation", hotel_cost_per_night * num_days)),
            "food_total": budget_summary.get("food_total",
                budget_summary.get("food_and_dining", budget_allocation["food_per_day"] * num_days)),
            "activities_total": budget_summary.get("activities_total",
                budget_summary.get("activities_and_entry", budget_allocation["activities_per_day"] * num_days)),
            "transport_total": budget_summary.get("transport_total",
                budget_summary.get("transport_and_misc", budget_allocation["transport_per_day"] * num_days)),
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
