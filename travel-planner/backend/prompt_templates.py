# backend/prompt_templates.py

SYSTEM_ROLE_PROMPT = """You are TravelAI, a production-grade, deterministic travel planning engine specializing in Indian tourism infrastructure, geospatial routing, and precise budgetary arithmetic.

CORE EXECUTION DIRECTIVES:
1. ARITHMETIC INTEGRITY: Treat the user's budget as a hard constraint. Track every single rupee. Sum of daily plans must accurately reflect total estimated spend.
2. GEOSPATIAL ANCHORING: Rely entirely on the structured coordinates and POIs provided in the RAG context. Group activities logically to minimize daily local transit times.
3. HIDDEN GEMS PRIORITIZATION: Actively surface low-footfall, high-heritage sites from the context (e.g., specific stepwells, uncrowded monuments like Ramappa Temple) over generic locations.
4. ZERO TALKATIVE TEXT: Do not include introductory text, conversational pleasantries, or concluding remarks. Your output must strictly be a single, fully-formed JSON object.
"""


def generate_production_prompt(user_request, rag_results, hotel_data, budget_allocation):
    """
    Assembles contextual parameters, RAG-retrieved data, and live hotel metrics
    into a structured template enforcing 100% schema alignment.
    """
    duration_days = user_request.get('duration_days', 3)  # fallback default

    return f"""### SYSTEM INSTRUCTION
Output a single, syntactically flawless JSON object conforming exactly to the schema below.
Do not wrap the output in markdown code blocks (such as ```json). No trailing commas.

### INPUT PARAMETERS
- Destination: {user_request['destination'].upper()}
- Duration: {duration_days} Days
- Start Date: {user_request['start_date']}
- End Date: {user_request['end_date']}
- Travelers: {user_request['travelers']}
- Total Budget Limit: ₹{user_request['budget']}
- Accommodation Tier: {user_request['accommodation_preference']}

### DATA RETRIEVAL (RAG & APIS)
---
1. GEOGRAPHIC & CULTURAL CONTEXT (Chroma DB / OpenStreetMap):
{rag_results}

2. REAL-WORLD HOTELS (Live API Feed):
{hotel_data}

3. TARGET TARGET BUDGET SEGMENTATION (Computed Parameters):
- Max Accommodation Total: ₹{budget_allocation['accommodation']}
- Max Food & Dining Total: ₹{budget_allocation['food_and_dining']}
- Max Activities & Entry Total: ₹{budget_allocation['activities_and_entry']}
- Max Transport & Misc Total: ₹{budget_allocation['transport_and_misc']}
---

### STRICT STAGE-GATE VALIDATION SCHEMA
The output object must follow this exact key/value structure:
{{{{
  "destination": "{user_request['destination'].title()}",
  "trip_overview": "Comprehensive strategic summary of the itinerary.",
  "daily_plans": [
    {{{{
      "day": 1,
      "date": "{user_request['start_date']}",
      "theme": "Core theme matching user preferences",
      "morning": {{{{
        "time": "09:00-12:00",
        "activities": ["Verified activity name with location anchor and duration"]
      }}}},
      "afternoon": {{{{
        "time": "12:00-17:00",
        "activities": ["Verified activity or hidden gem with routing details"]
      }}}},
      "evening": {{{{
        "time": "17:00-21:30",
        "activities": ["Dining experience and night walk details"]
      }}}},
      "hotel": {{{{
        "name": "Exact matching property name from live hotel feed",
        "price_per_night": 0,
        "booking_link": "API provided link string"
      }}}},
      "meals": [
        {{{{
          "type": "breakfast",
          "location": "Specific restaurant name from context",
          "estimated_cost": 0
        }}}}
      ],
      "transport": {{{{
        "mode": "Metro, Auto-rickshaw, or Walking",
        "estimated_cost": 0
      }}}},
      "activities_cost": 0,
      "meals_cost": 0,
      "hotel_cost": 0,
      "transport_cost": 0,
      "day_total": 0,
      "tips": ["Actionable localized tips"]
    }}}}
  ],
  "hotels_summary": [
    {{{{
      "name": "Selected Property Name",
      "rating": 4.5,
      "price_per_night": 0,
      "total_stay_cost": 0
    }}}}
  ],
  "budget_summary": {{{{
    "accommodation": 0,
    "food_and_dining": 0,
    "activities_and_entry": 0,
    "transport_and_misc": 0,
    "total_estimated": 0
  }}}},
  "cost_verification": {{{{
    "daily_sum": 0,
    "allocated_budget": {user_request['budget']},
    "variance_percentage": 0.0,
    "status": "WITHIN_BUDGET"
  }}}},
  "hidden_gems": [
    {{{{
      "name": "Lesser known site name",
      "description": "Granular data matching historical context guidelines.",
      "day_recommendation": 1,
      "estimated_cost": 0
    }}}}
  ],
  "dining_highlights": [
    {{{{
      "restaurant_name": "Name",
      "cuisine": "Authentic regional style",
      "average_cost": 0,
      "specialty": "Signature dish",
      "recommended_time": "evening"
    }}}}
  ],
  "travel_tips": ["Pack constraints, timing guidelines, cultural nuances."],
  "emergency_contacts": {{{{
    "police": "100",
    "ambulance": "102",
    "tourist_helpline": "1363"
  }}}},
  "disclaimer": "Real-world tariff data. Rates subject to seasonal shifts."
}}}}

CRITICAL PARSING CONSTRAINT: Output nothing but raw text starting with {{{{ and ending with }}}}. Ensure all string parameters use standard double-quotes. No text or block formatting outside the JSON boundaries. Verify arithmetic values prior to rendering final tokens."""
