# backend/prompt_templates.py
"""
Production-grade prompt templates for itinerary generation.
Enforces location diversity, meal planning, transport recommendations,
and accurate budget arithmetic.
"""

SYSTEM_ROLE_PROMPT = """You are TravelAI, a production-grade, deterministic travel planning engine specializing in Indian tourism infrastructure, geospatial routing, and precise budgetary arithmetic.

CORE EXECUTION DIRECTIVES:
1. ARITHMETIC INTEGRITY: Treat the user's budget as a hard constraint. Track every single rupee. For each day: day_total = activities_cost + meals_cost + transport_cost + hotel_cost. Sum of all day_totals must match total_estimated.
2. GEOSPATIAL ANCHORING: Rely entirely on the structured coordinates and POIs provided in the RAG context. Group activities logically to minimize daily local transit times.
3. LOCATION DIVERSITY: NEVER repeat the same attraction in both morning and evening of the same day. Each activity slot MUST feature a DIFFERENT location. Track all locations used so far and avoid revisiting them across days unless the trip exceeds 5 days.
4. MEAL PLANNING: EVERY day MUST include exactly 3 meals — breakfast, lunch, and dinner — with specific restaurant names, cuisine type, and estimated per-person cost. Use restaurants from the context data when available.
5. TRANSPORT PLANNING: Between EVERY pair of consecutive activities, specify the transport mode (metro, auto, taxi, walking), estimated cost, and estimated time in minutes. Use the transport data provided.
6. HIDDEN GEMS PRIORITIZATION: Actively surface low-footfall, high-heritage sites from the context (e.g., specific stepwells, uncrowded monuments) over generic locations.
7. ZERO TALKATIVE TEXT: Do not include introductory text, conversational pleasantries, or concluding remarks. Your output must strictly be a single, fully-formed JSON object.
"""


def generate_production_prompt(
    user_request,
    rag_results,
    hotel_data,
    budget_allocation,
    transport_info="",
    meal_budget_info="",
    visited_locations=None,
):
    """
    Assembles contextual parameters, RAG-retrieved data, live hotel metrics,
    transport data, and meal budgets into a structured template enforcing
    100% schema alignment with location diversity constraints.
    """
    duration_days = user_request.get("duration_days", 3)

    # Build visited locations constraint
    visited_constraint = ""
    if visited_locations and len(visited_locations) > 0:
        visited_list = ", ".join(visited_locations)
        visited_constraint = f"""
ALREADY ASSIGNED LOCATIONS (DO NOT REPEAT):
{visited_list}
"""

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

### CRITICAL CONSTRAINTS
1. LOCATION DIVERSITY: Each morning, afternoon, and evening activity MUST be at a DIFFERENT location. Do NOT use the same attraction twice in one day. Spread activities geographically.
2. MEAL MANDATE: Each day MUST include 3 meals (breakfast, lunch, dinner) with restaurant name, cuisine, and cost. Place meals at logical times (breakfast 8-9am, lunch 12:30-1:30pm, dinner 7:30-9pm).
3. TRANSPORT MANDATE: Between each activity, specify transport mode, cost, and time. Use metro when available, auto for short distances, taxi for longer ones.
4. ARITHMETIC RULE: day_total = activities_cost + meals_cost + transport_cost + hotel_cost. Verify this for EVERY day. total_estimated = sum of all day_totals.
{visited_constraint}
### DATA RETRIEVAL (RAG & APIS)
---
1. GEOGRAPHIC & CULTURAL CONTEXT (Chroma DB / OpenStreetMap):
{rag_results}

2. REAL-WORLD HOTELS (Live API Feed):
{hotel_data}

3. TRANSPORT OPTIONS:
{transport_info if transport_info else "Use auto-rickshaw (₹25 base + ₹12/km) as default. Metro available in Delhi, Mumbai, Bangalore, Kolkata, Hyderabad."}

4. MEAL BUDGET GUIDELINES:
{meal_budget_info if meal_budget_info else "Breakfast: ₹150-300, Lunch: ₹300-500, Dinner: ₹400-700 per person"}

5. BUDGET SEGMENTATION (Computed Parameters):
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
        "activities": ["Activity at UNIQUE LOCATION with duration"],
        "coordinates": {{{{"lat": 0.0, "lng": 0.0}}}}
      }}}},
      "afternoon": {{{{
        "time": "12:00-17:00",
        "activities": ["Activity at DIFFERENT LOCATION from morning"],
        "coordinates": {{{{"lat": 0.0, "lng": 0.0}}}}
      }}}},
      "evening": {{{{
        "time": "17:00-21:30",
        "activities": ["Activity at DIFFERENT LOCATION from morning and afternoon"],
        "coordinates": {{{{"lat": 0.0, "lng": 0.0}}}}
      }}}},
      "hotel": {{{{
        "name": "Exact matching property name from hotel feed",
        "price_per_night": 0,
        "booking_link": "URL string"
      }}}},
      "meals": [
        {{{{
          "type": "breakfast",
          "restaurant": "Specific restaurant name",
          "cuisine": "Cuisine type",
          "estimated_cost": 0
        }}}},
        {{{{
          "type": "lunch",
          "restaurant": "Specific restaurant name",
          "cuisine": "Cuisine type",
          "estimated_cost": 0
        }}}},
        {{{{
          "type": "dinner",
          "restaurant": "Specific restaurant name",
          "cuisine": "Cuisine type",
          "estimated_cost": 0
        }}}}
      ],
      "transport": [
        {{{{
          "from": "Hotel",
          "to": "Morning activity location",
          "mode": "metro/auto/taxi/walking",
          "cost": 0,
          "time_minutes": 0
        }}}}
      ],
      "activities_cost": 0,
      "meals_cost": 0,
      "transport_cost": 0,
      "hotel_cost": 0,
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
