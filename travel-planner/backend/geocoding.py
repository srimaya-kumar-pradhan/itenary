"""
Geocoding utility for Indian travel destinations and landmarks.
Uses a static coordinate database — zero external API dependencies.
Coordinates are WGS84 (lat, lng).
"""

from typing import Dict, Optional, Tuple

# ─── Destination City Coordinates ───
CITY_COORDS: Dict[str, Tuple[float, float]] = {
    "delhi": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777),
    "jaipur": (26.9124, 75.7873),
    "goa": (15.2993, 74.1240),
    "bangalore": (12.9716, 77.5946),
    "kolkata": (22.5726, 88.3639),
    "hyderabad": (17.3850, 78.4867),
    "agra": (27.1767, 78.0081),
    "varanasi": (25.3176, 83.0064),
    "kerala": (10.8505, 76.2711),
    "udaipur": (24.5854, 73.7125),
    "shimla": (31.1048, 77.1734),
    "manali": (32.2396, 77.1887),
    "rishikesh": (30.0869, 78.2676),
    "pune": (18.5204, 73.8567),
    "mysore": (12.2958, 76.6394),
    "ooty": (11.4102, 76.6950),
    "darjeeling": (27.0360, 88.2627),
    "chandigarh": (30.7333, 76.7794),
    "rajasthan": (26.9124, 75.7873),  # Default to Jaipur
}

# ─── Landmark Coordinates ───
# Popular tourist spots in Indian cities — used to geocode activities
LANDMARK_COORDS: Dict[str, Tuple[float, float]] = {
    # Delhi
    "red fort": (28.6562, 77.2410),
    "india gate": (28.6129, 77.2295),
    "qutub minar": (28.5245, 77.1855),
    "humayun's tomb": (28.5933, 77.2507),
    "humayuns tomb": (28.5933, 77.2507),
    "lotus temple": (28.5535, 77.2588),
    "jama masjid": (28.6507, 77.2334),
    "karim's": (28.6502, 77.2337),
    "karims": (28.6502, 77.2337),
    "chandni chowk": (28.6506, 77.2303),
    "connaught place": (28.6315, 77.2167),
    "akshardham": (28.6127, 77.2773),
    "agrasen ki baoli": (28.6264, 77.2245),
    "paranthe wali gali": (28.6555, 77.2302),
    "sunder nursery": (28.5936, 77.2470),
    "mehrauli archaeological park": (28.5207, 77.1822),
    "rajpath": (28.6129, 77.2295),
    "jantar mantar delhi": (28.6271, 77.2166),
    "rashtrapati bhavan": (28.6143, 77.1994),

    # Mumbai
    "gateway of india": (18.9220, 72.8347),
    "marine drive": (18.9432, 72.8235),
    "elephanta caves": (18.9633, 72.9315),
    "chhatrapati shivaji terminus": (18.9398, 72.8355),
    "bandra worli sea link": (19.0379, 72.8183),
    "haji ali dargah": (18.9827, 72.8089),
    "juhu beach": (19.0883, 72.8264),
    "colaba causeway": (18.9217, 72.8318),
    "sanjay gandhi national park": (19.2147, 72.9107),
    "siddhivinayak temple": (19.0168, 72.8302),

    # Jaipur
    "hawa mahal": (26.9239, 75.8267),
    "amber fort": (26.9855, 75.8513),
    "city palace jaipur": (26.9258, 75.8237),
    "jantar mantar jaipur": (26.9249, 75.8243),
    "nahargarh fort": (26.9373, 75.8154),
    "jal mahal": (26.9535, 75.8460),
    "albert hall museum": (26.9116, 75.8194),

    # Goa
    "baga beach": (15.5525, 73.7517),
    "calangute beach": (15.5434, 73.7554),
    "anjuna beach": (15.5726, 73.7423),
    "basilica of bom jesus": (15.5009, 73.9116),
    "se cathedral": (15.5039, 73.9122),
    "fort aguada": (15.4923, 73.7736),
    "dudhsagar falls": (15.3144, 74.3144),
    "palolem beach": (15.0100, 74.0230),

    # Bangalore
    "lalbagh botanical garden": (12.9507, 77.5848),
    "cubbon park": (12.9763, 77.5929),
    "bangalore palace": (12.9988, 77.5921),
    "tipu sultan's palace": (12.9591, 77.5737),
    "iskon temple bangalore": (12.9716, 77.5511),
    "vidhana soudha": (12.9791, 77.5913),
    "nandi hills": (13.3702, 77.6835),

    # Kolkata
    "victoria memorial": (22.5448, 88.3426),
    "howrah bridge": (22.5851, 88.3468),
    "indian museum": (22.5580, 88.3510),
    "dakshineswar kali temple": (22.6553, 88.3577),
    "park street": (22.5512, 88.3570),
    "science city kolkata": (22.5399, 88.3961),
    "mother house": (22.5444, 88.3612),

    # Hyderabad
    "charminar": (17.3616, 78.4747),
    "golconda fort": (17.3833, 78.4011),
    "hussain sagar lake": (17.4239, 78.4738),
    "ramoji film city": (17.2543, 78.6808),
    "birla mandir hyderabad": (17.4062, 78.4691),
    "salar jung museum": (17.3714, 78.4804),

    # Agra
    "taj mahal": (27.1751, 78.0421),
    "agra fort": (27.1795, 78.0211),
    "fatehpur sikri": (27.0945, 77.6679),
    "mehtab bagh": (27.1800, 78.0466),
    "itimad-ud-daulah": (27.1924, 78.0308),

    # Varanasi
    "dashashwamedh ghat": (25.3046, 83.0108),
    "kashi vishwanath temple": (25.3109, 83.0107),
    "assi ghat": (25.2844, 83.0044),
    "sarnath": (25.3814, 83.0227),
    "manikarnika ghat": (25.3128, 83.0113),
    "ramnagar fort": (25.2872, 83.0280),

    # Kerala
    "alleppey backwaters": (9.4981, 76.3388),
    "munnar": (10.0889, 77.0595),
    "kumarakom": (9.6175, 76.4301),
    "fort kochi": (9.9658, 76.2421),
    "periyar wildlife sanctuary": (9.4624, 77.1640),
    "kovalam beach": (8.3959, 76.9787),
    "varkala beach": (8.7330, 76.7157),
    "athirapally falls": (10.2855, 76.5698),

    # Udaipur
    "city palace udaipur": (24.5764, 73.6908),
    "lake pichola": (24.5711, 73.6807),
    "jag mandir": (24.5668, 73.6830),
    "sajjangarh palace": (24.5756, 73.6513),
    "fateh sagar lake": (24.5978, 73.6795),
    "jagdish temple": (24.5770, 73.6909),

    # Shimla
    "the ridge shimla": (31.1044, 77.1717),
    "mall road shimla": (31.1045, 77.1695),
    "jakhu temple": (31.1084, 77.1802),
    "kufri": (31.0971, 77.2663),
    "christ church shimla": (31.1049, 77.1718),

    # Manali
    "hadimba temple": (32.2431, 77.1892),
    "solang valley": (32.3178, 77.1571),
    "rohtang pass": (32.3725, 77.2478),
    "old manali": (32.2510, 77.1880),
    "vashisht hot springs": (32.2549, 77.1812),
    "mall road manali": (32.2417, 77.1893),

    # Rishikesh
    "laxman jhula": (30.1256, 78.3215),
    "ram jhula": (30.1145, 78.3133),
    "triveni ghat": (30.1035, 78.2948),
    "beatles ashram": (30.1153, 78.3125),
    "parmarth niketan": (30.1186, 78.3155),
    "neer garh waterfall": (30.1215, 78.3385),

    # Pune
    "shaniwar wada": (18.5196, 73.8553),
    "aga khan palace": (18.5525, 73.9015),
    "sinhagad fort": (18.3663, 73.7557),
    "dagdusheth halwai ganpati temple": (18.5166, 73.8560),
    "osho ashram": (18.5319, 73.8933),

    # Mysore
    "mysore palace": (12.3052, 76.6552),
    "chamundi hills": (12.2723, 76.6703),
    "brindavan gardens": (12.4213, 76.5729),
    "st philomena's church": (12.3181, 76.6564),
    "mysore zoo": (12.3009, 76.6630),

    # Ooty
    "ooty botanical gardens": (11.4152, 76.7095),
    "ooty lake": (11.4040, 76.6998),
    "doddabetta peak": (11.4019, 76.7355),
    "nilgiri mountain railway": (11.4100, 76.6950),
    "rose garden ooty": (11.4210, 76.7068),

    # Darjeeling
    "tiger hill": (26.9949, 88.2670),
    "batasia loop": (27.0243, 88.2582),
    "peace pagoda darjeeling": (27.0382, 88.2526),
    "darjeeling himalayan railway": (27.0430, 88.2627),
    "happy valley tea estate": (27.0343, 88.2528),

    # Chandigarh
    "rock garden chandigarh": (30.7525, 76.8097),
    "sukhna lake": (30.7421, 76.8184),
    "rose garden chandigarh": (30.7480, 76.7838),
    "capitol complex": (30.7612, 76.8046),
}


def get_city_coordinates(destination: str) -> Optional[Dict[str, float]]:
    """Return {lat, lng} for a destination city, or None."""
    key = destination.lower().strip()
    coords = CITY_COORDS.get(key)
    if coords:
        return {"lat": coords[0], "lng": coords[1]}
    return None


def get_landmark_coordinates(activity_text: str) -> Optional[Dict[str, float]]:
    """
    Try to find coordinates for an activity description by matching
    against known landmarks. Uses fuzzy substring matching.
    """
    text = activity_text.lower().strip()

    # Direct match
    if text in LANDMARK_COORDS:
        coords = LANDMARK_COORDS[text]
        return {"lat": coords[0], "lng": coords[1]}

    # Substring match — check if any landmark name appears in the text
    for landmark, coords in LANDMARK_COORDS.items():
        if landmark in text:
            return {"lat": coords[0], "lng": coords[1]}

    return None


def geocode_itinerary(itinerary: dict, destination: str) -> dict:
    """
    Augment an itinerary dict with coordinates for the destination
    and each daily activity. Non-destructive — only adds `coordinates`
    fields to existing nodes.
    """
    # Add destination-level coordinates
    dest_coords = get_city_coordinates(destination)
    if dest_coords:
        itinerary["destination_coordinates"] = dest_coords

    # Add coordinates to daily plans
    daily_plans = itinerary.get("daily_plans", [])
    for day in daily_plans:
        for period in ["morning", "afternoon", "evening"]:
            slot = day.get(period)
            if not slot:
                continue

            # Try to geocode from activity text
            activity = slot.get("activity", "")
            if not activity:
                activities = slot.get("activities", [])
                activity = " ".join(activities) if activities else slot.get("name", "")

            coords = get_landmark_coordinates(activity)
            if coords:
                slot["coordinates"] = coords
            elif dest_coords:
                # Fallback: use city center with a small random offset
                import random
                slot["coordinates"] = {
                    "lat": dest_coords["lat"] + random.uniform(-0.02, 0.02),
                    "lng": dest_coords["lng"] + random.uniform(-0.02, 0.02),
                }

    # Add coordinates to hidden gems
    for gem in itinerary.get("hidden_gems", []):
        name = gem.get("name", "")
        coords = get_landmark_coordinates(name)
        if coords:
            gem["coordinates"] = coords

    return itinerary
