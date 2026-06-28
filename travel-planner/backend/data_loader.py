"""
Data Loader — populates the ChromaDB vector database with travel data.
Uses hardcoded curated data for monuments, restaurants, and activities.
Kaggle integration is optional (requires ~/.kaggle/kaggle.json).
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def load_all_data(rag_pipeline) -> int:
    """
    Load all travel data into the RAG vector database.

    Args:
        rag_pipeline: Initialized RAGPipeline instance

    Returns:
        Total number of documents loaded
    """
    total = 0

    monuments = load_monuments()
    rag_pipeline.ingest_documents("monuments", monuments)
    total += len(monuments)
    logger.info(f"Loaded {len(monuments)} monument documents")

    restaurants = load_restaurants()
    rag_pipeline.ingest_documents("restaurants", restaurants)
    total += len(restaurants)
    logger.info(f"Loaded {len(restaurants)} restaurant documents")

    activities = load_activities()
    rag_pipeline.ingest_documents("activities", activities)
    total += len(activities)
    logger.info(f"Loaded {len(activities)} activity documents")

    logger.info(f"Data loading completed — {total} total documents ingested")
    return total


def load_monuments() -> List[Dict]:
    """Load monument and attraction data for Indian cities."""
    monuments = [
        # Delhi
        {"id": "delhi_red_fort", "text": "Red Fort (Lal Qila) in Delhi is a UNESCO World Heritage Site built in 1638 by Mughal Emperor Shah Jahan. Entry fee: ₹35 for Indians, ₹500 for foreigners. Open 9:30 AM - 4:30 PM. The fort features beautiful Mughal architecture with the Diwan-i-Aam, Diwan-i-Khas, and Rang Mahal. Sound and light show in evenings. Located in Old Delhi near Chandni Chowk metro station.", "metadata": {"city": "delhi", "type": "Historical", "cost": 35, "timing": "09:30-16:30"}},
        {"id": "delhi_qutub_minar", "text": "Qutub Minar in Delhi is a 73-meter tall UNESCO World Heritage Site, the tallest brick minaret in the world. Built in 1193 by Qutb-ud-din Aibak. Entry: ₹35 Indians, ₹550 foreigners. Features intricate carvings, the Iron Pillar, and Alai Darwaza. Located in Mehrauli, accessible via Qutub Minar metro. Best visited in morning for photography.", "metadata": {"city": "delhi", "type": "Historical", "cost": 35, "timing": "07:00-17:00"}},
        {"id": "delhi_india_gate", "text": "India Gate is a 42-meter war memorial in New Delhi, designed by Edwin Lutyens. No entry fee. Open 24/7. The surrounding Rajpath area features beautiful lawns, the Amar Jawan Jyoti, and is perfect for evening strolls. Ice cream vendors and boating available nearby. Metro: Central Secretariat.", "metadata": {"city": "delhi", "type": "Historical", "cost": 0, "timing": "24/7"}},
        {"id": "delhi_humayun_tomb", "text": "Humayun's Tomb in Delhi is a UNESCO World Heritage Site and the first garden-tomb in the Indian subcontinent, built in 1570. Entry: ₹35 Indians, ₹550 foreigners. The tomb inspired the Taj Mahal and features stunning Mughal architecture with a Persian-style garden. Located in Nizamuddin, near Hazrat Nizamuddin station.", "metadata": {"city": "delhi", "type": "Historical", "cost": 35, "timing": "06:00-18:00"}},
        {"id": "delhi_lotus_temple", "text": "Lotus Temple (Bahá'í House of Worship) in Delhi is a stunning lotus-shaped marble structure. Free entry. Open 9 AM - 5 PM (closed Mondays). Known for its remarkable architecture with 27 marble petals. Silent meditation hall inside. Surrounded by beautiful gardens. Metro: Kalkaji Mandir.", "metadata": {"city": "delhi", "type": "Spiritual", "cost": 0, "timing": "09:00-17:00"}},
        {"id": "delhi_akshardham", "text": "Akshardham Temple in Delhi is a stunning Hindu temple complex opened in 2005. Free entry (exhibitions extra ₹170-₹220). Features 234 ornately carved pillars, 9 domes, and a Musical Fountain show. The temple holds a Guinness World Record for being the world's largest comprehensive Hindu temple. Metro: Akshardham.", "metadata": {"city": "delhi", "type": "Spiritual", "cost": 0, "timing": "09:30-18:30"}},
        {"id": "delhi_jama_masjid", "text": "Jama Masjid in Old Delhi is one of India's largest mosques, built by Shah Jahan in 1656. Free entry (camera ₹300). Can hold 25,000 worshippers. Climb the minaret for panoramic views of Old Delhi (₹100). Located in the heart of Old Delhi near Chawri Bazaar metro, surrounded by famous food streets.", "metadata": {"city": "delhi", "type": "Historical", "cost": 0, "timing": "07:00-12:00, 13:30-18:30"}},
        {"id": "delhi_lodhi_gardens", "text": "Lodhi Gardens in Delhi is a beautiful 90-acre park with 15th-century tombs of Sayyid and Lodhi dynasties. Free entry. Open 6 AM - 8 PM. Features Mohammed Shah's Tomb, Sikandar Lodi's Tomb, Bara Gumbad, and Sheesh Gumbad. Popular for morning jogs and photography. Near Khan Market metro.", "metadata": {"city": "delhi", "type": "Historical", "cost": 0, "timing": "06:00-20:00"}},
        {"id": "delhi_chandni_chowk", "text": "Chandni Chowk is Delhi's oldest and busiest market, established in the 17th century by Shah Jahan's daughter. A paradise for street food: Paranthe Wali Gali, Natraj Dahi Bhalle, Kuremal Kulfi, and Old Famous Jalebi Wala. Also famous for wedding shopping, electronics, and spices. Metro: Chandni Chowk.", "metadata": {"city": "delhi", "type": "Cultural", "cost": 0, "timing": "09:00-21:00"}},
        {"id": "delhi_hauz_khas", "text": "Hauz Khas Village in Delhi is a trendy urban village with medieval ruins, art galleries, boutiques, and rooftop cafes. Free to explore. The Hauz Khas Complex features a 13th-century water tank, madrasa, and tomb of Feroz Shah Tughlaq. Adjacent deer park is great for relaxation. Metro: Hauz Khas.", "metadata": {"city": "delhi", "type": "Cultural", "cost": 0, "timing": "24/7"}},

        # Mumbai
        {"id": "mumbai_gateway", "text": "Gateway of India in Mumbai is an iconic arch-monument built in 1924 to commemorate King George V's visit. Free entry. Located at Apollo Bunder, Colaba, overlooking the Arabian Sea. Start point for Elephanta Caves ferry. Surrounded by the Taj Mahal Palace Hotel and street vendors. Best at sunrise or sunset.", "metadata": {"city": "mumbai", "type": "Historical", "cost": 0, "timing": "24/7"}},
        {"id": "mumbai_marine_drive", "text": "Marine Drive (Queen's Necklace) in Mumbai is a 3.6-km art deco promenade along the coast. Free. The curved road from Nariman Point to Malabar Hill lights up at night like a string of pearls. Perfect for sunset watching and evening walks. Chowpatty Beach at the northern end is famous for bhel puri.", "metadata": {"city": "mumbai", "type": "Cultural", "cost": 0, "timing": "24/7"}},
        {"id": "mumbai_elephanta", "text": "Elephanta Caves in Mumbai are UNESCO World Heritage rock-cut caves dating to 5th-8th century. Entry: ₹40 Indians, ₹600 foreigners. Ferry from Gateway of India (₹200 round trip, 1 hour). Features stunning sculptures of Lord Shiva, including the famous Trimurti. Best visited on weekdays. Closed Mondays.", "metadata": {"city": "mumbai", "type": "Historical", "cost": 240, "timing": "09:30-17:30"}},
        {"id": "mumbai_cst", "text": "Chhatrapati Shivaji Maharaj Terminus (CST) in Mumbai is a UNESCO World Heritage Victorian Gothic railway station built in 1887. Free to view exterior. Features turrets, pointed arches, stained glass, and ornate stone carvings. Still serves as an active railway station. Best photographed from across the road.", "metadata": {"city": "mumbai", "type": "Historical", "cost": 0, "timing": "24/7"}},
        {"id": "mumbai_haji_ali", "text": "Haji Ali Dargah in Mumbai is a stunning mosque and tomb on an islet 500m into the Arabian Sea, connected by a causeway accessible only at low tide. Free entry. Built in 1431. Features Indo-Islamic architecture with marble walls and mirror work. Beautiful at sunset. Near Mahalaxmi station.", "metadata": {"city": "mumbai", "type": "Spiritual", "cost": 0, "timing": "05:30-22:00"}},

        # Jaipur
        {"id": "jaipur_amber_fort", "text": "Amber Fort (Amer Fort) in Jaipur is a magnificent Rajput fort built in 1592 by Raja Man Singh. Entry: ₹100 Indians, ₹500 foreigners. Features the Sheesh Mahal (Mirror Palace), Diwan-i-Aam, and stunning views. Elephant rides available (₹1100). Located 11 km from Jaipur. Light and sound show in evenings.", "metadata": {"city": "jaipur", "type": "Historical", "cost": 100, "timing": "08:00-17:30"}},
        {"id": "jaipur_hawa_mahal", "text": "Hawa Mahal (Palace of Winds) in Jaipur is an iconic pink sandstone structure with 953 small windows (jharokhas). Built in 1799 by Maharaja Sawai Pratap Singh. Entry: ₹50 Indians, ₹200 foreigners. The honeycomb facade was designed for royal women to observe street festivals. Best photographed from across the street.", "metadata": {"city": "jaipur", "type": "Historical", "cost": 50, "timing": "09:00-16:30"}},
        {"id": "jaipur_city_palace", "text": "City Palace in Jaipur is a blend of Rajput, Mughal and European architecture. Entry: ₹200 Indians, ₹700 foreigners. Features the Chandra Mahal, Mubarak Mahal, and the world's largest silver vessels (Guinness Record). Part of the palace is still a royal residence. Located in the heart of the Pink City.", "metadata": {"city": "jaipur", "type": "Historical", "cost": 200, "timing": "09:00-17:00"}},
        {"id": "jaipur_nahargarh", "text": "Nahargarh Fort in Jaipur stands on the edge of the Aravalli Hills, offering breathtaking views of the city. Entry: ₹50 Indians, ₹200 foreigners. Built in 1734. Features the Madhavendra Bhawan with connected suites. Famous sunset point. Houses a wax museum and sculpture park. Great for evening visits.", "metadata": {"city": "jaipur", "type": "Historical", "cost": 50, "timing": "10:00-17:30"}},

        # Goa
        {"id": "goa_basilica", "text": "Basilica of Bom Jesus in Old Goa is a UNESCO World Heritage Church built in 1605. Free entry. Houses the mortal remains of St. Francis Xavier. Features Baroque architecture and gilded altars. One of the oldest churches in India. Located in Old Goa, 10 km from Panaji.", "metadata": {"city": "goa", "type": "Historical", "cost": 0, "timing": "09:00-18:30"}},
        {"id": "goa_aguada_fort", "text": "Aguada Fort in Goa is a well-preserved 17th-century Portuguese fort. Free entry. Features a 4-story lighthouse (oldest of its kind in Asia), freshwater spring, and panoramic sea views. Located on Sinquerim Beach, North Goa. Great for sunset photography and history walks.", "metadata": {"city": "goa", "type": "Historical", "cost": 0, "timing": "09:30-18:00"}},
        {"id": "goa_dudhsagar", "text": "Dudhsagar Falls in Goa is a stunning 4-tiered waterfall (310m) on the Mandovi River. One of India's tallest waterfalls. Entry via jeep safari from Collem (₹400-600). Best during monsoon (June-Sept). Swimming in the pool below is possible. Located on the Goa-Karnataka border, 60 km from Panaji.", "metadata": {"city": "goa", "type": "Adventure", "cost": 600, "timing": "07:00-16:00"}},
        {"id": "goa_baga_beach", "text": "Baga Beach in North Goa is famous for nightlife, water sports, and beach shacks. Free entry. Offers parasailing (₹500-800), jet skiing (₹400-600), and banana boat rides. Famous Tito's Lane nightclub nearby. Great for sunset parties. Crowded during peak season (Nov-Feb).", "metadata": {"city": "goa", "type": "Beach", "cost": 0, "timing": "24/7"}},
        {"id": "goa_palolem", "text": "Palolem Beach in South Goa is a crescent-shaped paradise known for its calm waters and laid-back vibe. Free entry. Offers kayaking, dolphin spotting trips (₹400), and silent disco parties. Beach huts available from ₹800/night. Less crowded than North Goa. Perfect for relaxation and swimming.", "metadata": {"city": "goa", "type": "Beach", "cost": 0, "timing": "24/7"}},

        # Kolkata
        {"id": "kolkata_victoria", "text": "Victoria Memorial in Kolkata is a magnificent white marble building built in 1921 dedicated to Queen Victoria. Entry: ₹30 Indians, ₹500 foreigners (museum). Surrounding gardens free (₹10). Features a museum with 28,394 artifacts, paintings, and historical documents. Sound and light show in evenings. Metro: Maidan.", "metadata": {"city": "kolkata", "type": "Historical", "cost": 30, "timing": "10:00-17:00"}},
        {"id": "kolkata_howrah_bridge", "text": "Howrah Bridge (Rabindra Setu) in Kolkata is an iconic cantilever bridge over the Hooghly River, built in 1943. Free. The sixth-longest bridge of its type. Best views from Mallick Ghat flower market at dawn or from Princep Ghat at sunset. A symbol of Kolkata and an engineering marvel.", "metadata": {"city": "kolkata", "type": "Historical", "cost": 0, "timing": "24/7"}},

        # Hyderabad
        {"id": "hyd_charminar", "text": "Charminar in Hyderabad is an iconic monument and mosque built in 1591 by Muhammad Quli Qutb Shah. Entry: ₹25 Indians, ₹300 foreigners. Features 4 grand arches with minarets. Climb for panoramic city views. Surrounded by Laad Bazaar (famous for bangles) and street food. Located in Old City.", "metadata": {"city": "hyderabad", "type": "Historical", "cost": 25, "timing": "09:30-17:30"}},
        {"id": "hyd_golconda", "text": "Golconda Fort in Hyderabad is a 13th-century fortified citadel famous for its acoustic architecture — a handclap at the entrance gate can be heard at the top. Entry: ₹25 Indians, ₹200 foreigners. Sound and light show in evenings (₹130). Features royal palaces, temples, and the famous Diamond Vault.", "metadata": {"city": "hyderabad", "type": "Historical", "cost": 25, "timing": "09:00-17:30"}},

        # Agra
        {"id": "agra_taj_mahal", "text": "Taj Mahal in Agra is one of the Seven Wonders of the World, a UNESCO World Heritage Site built by Shah Jahan in memory of Mumtaz Mahal (1632-1653). Entry: ₹50 Indians, ₹1100 foreigners. Open sunrise to sunset, closed Fridays. Features white marble inlaid with precious stones. Best visited at sunrise for photography and fewer crowds.", "metadata": {"city": "agra", "type": "Historical", "cost": 50, "timing": "06:00-18:30"}},
        {"id": "agra_fort", "text": "Agra Fort is a UNESCO World Heritage Site and massive red sandstone fortress built by Akbar in 1565. Entry: ₹50 Indians, ₹550 foreigners. Features the Diwan-i-Aam, Diwan-i-Khas, Jahangir's Palace, and Khas Mahal. Shah Jahan spent his final years here, gazing at the Taj Mahal. 2.5 km from Taj Mahal.", "metadata": {"city": "agra", "type": "Historical", "cost": 50, "timing": "06:00-18:00"}},

        # Varanasi
        {"id": "varanasi_ghats", "text": "Varanasi Ghats along the River Ganges are the spiritual heart of India. Over 80 ghats stretch along 7 km. Dashashwamedh Ghat hosts the famous Ganga Aarti ceremony every evening at 7 PM. Boat rides (₹100-300 per person) at dawn offer views of sunrise over the ghats. Manikarnika Ghat is the primary cremation ghat.", "metadata": {"city": "varanasi", "type": "Spiritual", "cost": 0, "timing": "24/7"}},
        {"id": "varanasi_kashi_vishwanath", "text": "Kashi Vishwanath Temple in Varanasi is one of the most famous Hindu temples, dedicated to Lord Shiva. Free entry. Recently renovated with the Kashi Vishwanath Corridor. Located in Varanasi's narrow lanes. Photography restrictions inside. Security check required. Early morning darshan recommended to avoid long queues.", "metadata": {"city": "varanasi", "type": "Spiritual", "cost": 0, "timing": "03:00-23:00"}},

        # Kerala
        {"id": "kerala_backwaters", "text": "Kerala Backwaters (Alleppey/Kumarakom) are a network of interconnected canals, rivers, and lakes. Houseboat cruise: ₹6000-15000 per night. Day cruise: ₹400-1000. Features lush paddy fields, coconut groves, and village life. Best during Oct-March. Alleppey is the 'Venice of the East'. Shikara rides also available.", "metadata": {"city": "kerala", "type": "Adventure", "cost": 1000, "timing": "06:00-18:00"}},
        {"id": "kerala_munnar", "text": "Munnar in Kerala is a picturesque hill station at 1,600m altitude, famous for tea plantations. Tata Tea Museum entry: ₹125. Visit Eravikulam National Park (₹125) to see the endangered Nilgiri Tahr. Mattupetty Dam, Echo Point, and Top Station offer stunning views. Best visited Sept-May. Cool climate year-round.", "metadata": {"city": "kerala", "type": "Adventure", "cost": 125, "timing": "09:00-16:00"}},

        # Bangalore
        {"id": "bangalore_palace", "text": "Bangalore Palace is a Tudor-style palace built in 1887, inspired by Windsor Castle. Entry: ₹230 Indians, ₹460 foreigners. Features fortified towers, Gothic windows, and sprawling gardens over 454 acres. Houses a collection of paintings and artifacts from the Wodeyar dynasty. Located in central Bangalore.", "metadata": {"city": "bangalore", "type": "Historical", "cost": 230, "timing": "10:00-17:30"}},
        {"id": "bangalore_lalbagh", "text": "Lalbagh Botanical Garden in Bangalore spans 240 acres, originally designed by Hyder Ali in 1760. Entry: ₹25. Features one of the largest collections of tropical plants, a Glass House (modeled on London's Crystal Palace), and a 3000-million-year-old rock formation. Flower shows held on Republic and Independence Days.", "metadata": {"city": "bangalore", "type": "Cultural", "cost": 25, "timing": "06:00-19:00"}},
    ]

    return monuments


def load_restaurants() -> List[Dict]:
    """Load restaurant and food data for Indian cities."""
    restaurants = [
        # Delhi
        {"id": "delhi_karims", "text": "Karim's near Jama Masjid in Old Delhi is a legendary Mughlai restaurant since 1913. Famous for Mutton Burra (₹400), Chicken Jahangiri (₹350), and Seekh Kebabs (₹250). Average meal: ₹500-800 per person. No reservations. Extremely crowded during lunch. Located in narrow lanes of Old Delhi.", "metadata": {"city": "delhi", "type": "restaurant", "cuisine": "Mughlai", "avg_cost": 600}},
        {"id": "delhi_paranthe", "text": "Paranthe Wali Gali in Chandni Chowk, Delhi has been serving stuffed paranthas since the 1870s. Try at Pt. Gaya Prasad Shiv Charan (oldest shop). Famous paranthas: aloo, paneer, mixed, rabri. Cost: ₹50-150 per parantha. A must-visit for food lovers exploring Old Delhi. Open 9 AM - 10 PM.", "metadata": {"city": "delhi", "type": "restaurant", "cuisine": "Street Food", "avg_cost": 200}},
        {"id": "delhi_indian_accent", "text": "Indian Accent in The Lodhi, Delhi is ranked among Asia's 50 Best Restaurants. Features modern Indian cuisine by Chef Manish Mehrotra. Signature dishes: Daulat ki Chaat, Pork Ribs Vindaloo. Tasting menu: ₹5500+. Reservations essential. Perfect for a luxury dining experience.", "metadata": {"city": "delhi", "type": "restaurant", "cuisine": "Modern Indian", "avg_cost": 5500}},
        {"id": "delhi_saravana", "text": "Saravana Bhavan at Connaught Place, Delhi is a legendary South Indian vegetarian chain. Famous for crispy dosas (₹120-200), idli-sambhar (₹100), and filter coffee (₹60). Average meal: ₹200-350 per person. Always busy. Multiple floors. Great for budget-friendly authentic South Indian food.", "metadata": {"city": "delhi", "type": "restaurant", "cuisine": "South Indian", "avg_cost": 250}},

        # Mumbai
        {"id": "mumbai_leopold", "text": "Leopold Cafe in Colaba, Mumbai is an iconic cafe since 1871, featured in 'Shantaram'. Serves multi-cuisine food and drinks. Beer from ₹300, meals from ₹400-700. Always buzzing with tourists and locals. Open 7:30 AM - 1:30 AM. A must-visit for atmosphere and history.", "metadata": {"city": "mumbai", "type": "restaurant", "cuisine": "Multi-cuisine", "avg_cost": 600}},
        {"id": "mumbai_britannia", "text": "Britannia & Co. in Fort, Mumbai is a legendary Parsi restaurant since 1923. Famous for Berry Pulao (₹600), Dhansak (₹350), and Caramel Custard (₹100). Run by 96-year-old Boman Kohinoor. Average meal: ₹500-700. Closed Sundays. A Mumbai institution.", "metadata": {"city": "mumbai", "type": "restaurant", "cuisine": "Parsi", "avg_cost": 550}},
        {"id": "mumbai_street_food", "text": "Mumbai Street Food Guide: Vada Pav at Ashok Vada Pav (₹20), Pav Bhaji at Sardar (₹120) at Tardeo, Bhel Puri at Chowpatty (₹50-80), Sandwich at Bombay Sandwich (₹60), Falooda at Badshah (₹100) at Crawford Market. Budget: ₹200-400 for a full street food crawl.", "metadata": {"city": "mumbai", "type": "restaurant", "cuisine": "Street Food", "avg_cost": 300}},

        # Jaipur
        {"id": "jaipur_lmb", "text": "LMB (Laxmi Mishthan Bhandar) on Johari Bazaar, Jaipur is famous since 1727. Known for Ghevar (₹200-500/kg), Rajasthani Thali (₹450), and sweets. The restaurant also serves full meals with Dal Baati Churma (₹350). Average meal: ₹400-600. A Jaipur food institution.", "metadata": {"city": "jaipur", "type": "restaurant", "cuisine": "Rajasthani", "avg_cost": 450}},
        {"id": "jaipur_1135ad", "text": "1135 AD at Amber Fort, Jaipur offers fine dining in a 1135-year-old setting. Serves Rajasthani and Indian cuisine with fort views. Signature: Laal Maas (₹750), Safed Maas (₹700). Average meal: ₹1500-2500 per person. Reservations recommended. One of India's most unique dining locations.", "metadata": {"city": "jaipur", "type": "restaurant", "cuisine": "Rajasthani Fine Dining", "avg_cost": 2000}},

        # Goa
        {"id": "goa_fishermans", "text": "Fisherman's Wharf in Goa serves Goan and seafood cuisine by the Sal River. Famous for Goan Fish Curry Rice (₹400), Prawn Balchao (₹500), and Bebinca (₹200). Average meal: ₹600-900 per person. Multiple locations across Goa. Great ambiance with live music.", "metadata": {"city": "goa", "type": "restaurant", "cuisine": "Goan Seafood", "avg_cost": 750}},
        {"id": "goa_thalassa", "text": "Thalassa in Vagator, Goa is a cliffside Greek restaurant with stunning sea views. Famous for Greek Salad (₹450), Moussaka (₹550), and sunset cocktails (₹400). Average meal: ₹1000-1500. Reservations essential for sunset tables. One of Goa's most popular restaurants.", "metadata": {"city": "goa", "type": "restaurant", "cuisine": "Greek-Goan", "avg_cost": 1200}},

        # Kolkata
        {"id": "kolkata_peter_cat", "text": "Peter Cat on Park Street, Kolkata is legendary for its Chelo Kebab (₹500) — a mountain of rice with mutton kebabs and an egg. Queue starts before opening. Also try the Prawn Cocktail. Average meal: ₹500-700. A Kolkata institution since 1960s.", "metadata": {"city": "kolkata", "type": "restaurant", "cuisine": "Continental-Indian", "avg_cost": 600}},

        # Hyderabad
        {"id": "hyd_paradise", "text": "Paradise Biryani in Hyderabad is the most famous biryani restaurant chain. The Hyderabadi Dum Biryani (₹280-400) is legendary. Also try Haleem during Ramadan (₹200). Multiple branches. The original at MG Road is most authentic. Average meal: ₹350-500 per person.", "metadata": {"city": "hyderabad", "type": "restaurant", "cuisine": "Hyderabadi", "avg_cost": 400}},

        # Varanasi
        {"id": "varanasi_blue_lassi", "text": "Blue Lassi Shop in Varanasi's narrow lanes near Manikarnika Ghat has been serving thick, creamy lassi since 1925. Famous fruit lassi (₹60-100) in clay cups. Try the saffron and rose variants. No seating except a small bench. Open 7 AM - 10 PM. A Varanasi institution.", "metadata": {"city": "varanasi", "type": "restaurant", "cuisine": "Beverages", "avg_cost": 80}},

        # Agra
        {"id": "agra_pindi", "text": "Pind Balluchi near Taj Mahal, Agra serves North Indian cuisine with Mughlai specialties. Try Tandoori Chicken (₹350), Butter Naan (₹60), and Mughlai Biryani (₹300). Average meal: ₹400-600. Rooftop restaurants near Taj offer views with meals — try Oberoi's Bellevue for luxury.", "metadata": {"city": "agra", "type": "restaurant", "cuisine": "Mughlai", "avg_cost": 500}},
    ]

    return restaurants


def load_activities() -> List[Dict]:
    """Load activities and experiences data."""
    activities = [
        # Delhi Activities
        {"id": "delhi_food_walk", "text": "Old Delhi Food Walk: A 3-hour guided walk through Chandni Chowk covering 10+ food stops. Cost: ₹1500-2500 for guided tour, ₹500 self-guided. Includes Paranthe Wali Gali, Karim's, Natraj Dahi Bhalle, Old Famous Jalebi Wala, and Kuremal Kulfi. Best started at 10 AM. Highly recommended for food lovers.", "metadata": {"city": "delhi", "type": "Cultural", "cost": 1500, "duration_hours": 3}},
        {"id": "delhi_metro_heritage", "text": "Delhi Metro Heritage Ride: Use the metro to visit heritage sites — Yellow Line from HUDA City Centre to Chandni Chowk covers most tourist spots. Day pass: ₹200. Efficient, air-conditioned, and avoids Delhi traffic. Download DMRC app for navigation. Runs 5 AM - 11 PM.", "metadata": {"city": "delhi", "type": "Budget", "cost": 200, "duration_hours": 8}},
        {"id": "delhi_cycle_tour", "text": "Delhi Cycle Tour through Old Delhi: 3-hour early morning cycling experience through heritage lanes. Cost: ₹2000-3500 with guide. Covers Jama Masjid, Chandni Chowk, Kinari Bazaar, and hidden havelis. Best at 6:30 AM before crowds. Multiple operators available. Includes chai stops.", "metadata": {"city": "delhi", "type": "Adventure", "cost": 2500, "duration_hours": 3}},

        # Mumbai Activities
        {"id": "mumbai_dharavi_tour", "text": "Dharavi Walking Tour in Mumbai: 2.5-hour tour of Asia's largest slum turned micro-economy. Cost: ₹600-1000 per person. See pottery, leather, recycling, and bakery workshops. 80% of profits go to community NGOs. Photography may be restricted in residential areas. Book with Reality Tours.", "metadata": {"city": "mumbai", "type": "Cultural", "cost": 800, "duration_hours": 2.5}},
        {"id": "mumbai_bollywood_tour", "text": "Bollywood Studio Tour in Mumbai: Visit Film City in Goregaon for a behind-the-scenes look at Bollywood. Cost: ₹500-1500. See active sets, green screens, and sometimes live shooting. Half-day tour. Book via authorized operators. Also visit RK Studios heritage.", "metadata": {"city": "mumbai", "type": "Cultural", "cost": 1000, "duration_hours": 4}},

        # Jaipur Activities
        {"id": "jaipur_elephant_village", "text": "Elefantastic Elephant Village near Jaipur: Ethical elephant interaction experience. Cost: ₹3000-5000 per person. Includes feeding, bathing, and painting with elephants. No riding. 3-hour experience. Located in Kukas, 20 km from Jaipur. Highly rated on TripAdvisor for ethical practices.", "metadata": {"city": "jaipur", "type": "Adventure", "cost": 3500, "duration_hours": 3}},
        {"id": "jaipur_block_printing", "text": "Block Printing Workshop in Jaipur: Learn traditional Rajasthani block printing at Anokhi Museum or local artisan workshops. Cost: ₹500-1500 per person. 2-3 hour session. Create your own fabric souvenirs. Located in Amber area. Great for cultural immersion and unique souvenirs.", "metadata": {"city": "jaipur", "type": "Cultural", "cost": 800, "duration_hours": 2.5}},

        # Goa Activities
        {"id": "goa_water_sports", "text": "Water Sports in Goa at Baga/Calangute Beach: Parasailing (₹500-800), Jet Skiing (₹400-600), Banana Ride (₹300), Bumper Ride (₹400), Kayaking (₹500). Package deals available (₹1500-2500 for 4 activities). Operators at all major North Goa beaches. Best during Oct-May.", "metadata": {"city": "goa", "type": "Adventure", "cost": 1500, "duration_hours": 3}},
        {"id": "goa_spice_plantation", "text": "Spice Plantation Tour in Goa: Visit Sahakari Spice Farm or Tropical Spice Plantation. Cost: ₹400-600 per person includes buffet lunch. See cardamom, pepper, vanilla, cinnamon growing. Elephant bathing sometimes available. 3-hour experience. Located 25-30 km from Panaji.", "metadata": {"city": "goa", "type": "Cultural", "cost": 500, "duration_hours": 3}},
        {"id": "goa_dolphin_trip", "text": "Dolphin Spotting Trip in Goa: Boat trip from Sinquerim/Palolem to spot Indo-Pacific Humpback Dolphins. Cost: ₹400-800 per person. 1-2 hour trip. Best time: early morning (7-9 AM). Also visit Grand Island for snorkeling (₹1500-2500 full day). Seasonal: Oct-May.", "metadata": {"city": "goa", "type": "Adventure", "cost": 600, "duration_hours": 2}},

        # Kerala Activities
        {"id": "kerala_ayurveda", "text": "Ayurveda Spa Experience in Kerala: Traditional Ayurvedic massage and treatment. Cost: ₹1500-5000 for 1-2 hours. Popular treatments: Abhyangam (₹1500), Shirodhara (₹2500), Pizhichil (₹3500). Best centers in Kumarakom, Kovalam, and Varkala. Book at certified centers.", "metadata": {"city": "kerala", "type": "Cultural", "cost": 2500, "duration_hours": 2}},
        {"id": "kerala_kathakali", "text": "Kathakali Dance Performance in Kerala: Traditional dance-drama with elaborate costumes and makeup. Cost: ₹200-500 at cultural centers. See makeup process starting 1 hour before show. Best venues: Kerala Kathakali Centre (Kochi), Greenix Village. Shows usually at 6:30 PM, makeup from 5 PM.", "metadata": {"city": "kerala", "type": "Cultural", "cost": 350, "duration_hours": 2}},

        # Varanasi Activities
        {"id": "varanasi_ganga_aarti", "text": "Ganga Aarti Ceremony at Dashashwamedh Ghat, Varanasi: A mesmerizing fire ritual performed every evening at 7 PM. Free to watch from the ghat steps. Boat viewing: ₹100-300 per person (better views). Arrive by 6 PM for good spots. Features synchronized chanting, fire lamps, and conch shells.", "metadata": {"city": "varanasi", "type": "Spiritual", "cost": 0, "duration_hours": 1}},
        {"id": "varanasi_boat_ride", "text": "Sunrise Boat Ride on the Ganges in Varanasi: Essential Varanasi experience. Cost: ₹100-300 per person (shared), ₹500-1000 (private). Duration: 1-2 hours starting at 5:30 AM. See sunrise over the ghats, morning rituals, yoga practitioners, and cremation ghats from a respectful distance.", "metadata": {"city": "varanasi", "type": "Spiritual", "cost": 300, "duration_hours": 1.5}},

        # Hyderabad Activities
        {"id": "hyd_food_trail", "text": "Hyderabad Food Trail: Famous for biryani, haleem, and Irani chai. Start at Paradise for Biryani (₹280), Shah Ghouse for Kebabs (₹200), Nimrah Cafe for Irani Chai & Osmania Biscuits (₹50), and Pista House for Haleem (₹200). Total food tour budget: ₹700-1000. Best self-guided through Old City.", "metadata": {"city": "hyderabad", "type": "Cultural", "cost": 800, "duration_hours": 4}},
    ]

    return activities


if __name__ == "__main__":
    """Test data loading standalone."""
    logging.basicConfig(level=logging.INFO)
    print(f"Monuments: {len(load_monuments())}")
    print(f"Restaurants: {len(load_restaurants())}")
    print(f"Activities: {len(load_activities())}")
    total = len(load_monuments()) + len(load_restaurants()) + len(load_activities())
    print(f"Total documents: {total}")
