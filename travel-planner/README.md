# 🌏 AI Travel Planner — RAG + Gemini AI

An intelligent travel planning application for Indian destinations that uses **Retrieval-Augmented Generation (RAG)** with ChromaDB and **Google Gemini AI** to generate personalized itineraries.

## Features

- 🏛️ **20 Indian Destinations** — Delhi, Mumbai, Jaipur, Goa, Kerala, and more
- 🤖 **AI-Powered Itineraries** — Google Gemini generates personalized day-by-day plans
- 🔍 **RAG Pipeline** — Semantic search over 50+ curated travel documents
- 💰 **Budget Optimization** — Smart allocation across accommodation, food, activities
- 🏨 **Hotel Recommendations** — 3 tiers (budget, mid-range, luxury) per city
- 💎 **Hidden Gems** — Off-the-beaten-path recommendations
- 📱 **Responsive UI** — Premium dark theme with glassmorphism

## Quick Start

### 1. Setup
```bash
cd travel-planner/backend
python -m venv venv
venv\Scripts\activate         # Windows
# source venv/bin/activate    # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure API Key
Edit `backend/.env` and set your Gemini API key:
```
GEMINI_API_KEY=your_actual_key_here
```
Get one at: https://aistudio.google.com/

### 3. Start Backend
```bash
cd backend
python main.py
```
Backend runs at http://localhost:8000

### 4. Serve Frontend
```bash
cd frontend
python -m http.server 8001
```
Open http://localhost:8001 in your browser.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/generate-itinerary` | Generate trip itinerary |

### Sample Request
```json
{
  "destination": "delhi",
  "start_date": "2026-07-01",
  "end_date": "2026-07-04",
  "budget": 15000,
  "travelers": 1,
  "preferences": ["Historical", "Budget"],
  "accommodation_preference": "mid-range"
}
```

## Tech Stack

- **Backend**: FastAPI + Uvicorn
- **Vector DB**: ChromaDB (persistent)
- **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2)
- **LLM**: Google Gemini 2.0 Flash
- **Frontend**: Vanilla HTML/CSS/JS

## Project Structure

```
travel-planner/
├── frontend/           # Web UI
│   ├── index.html
│   ├── css/style.css
│   └── js/script.js
├── backend/            # FastAPI server
│   ├── main.py         # API endpoints
│   ├── config.py       # Settings
│   ├── models.py       # Pydantic schemas
│   ├── rag.py          # RAG pipeline
│   ├── llm.py          # Gemini integration
│   ├── hotel_api.py    # Hotel service
│   ├── data_loader.py  # Vector DB seeding
│   └── .env            # API keys
├── vector_db/          # ChromaDB storage
└── README.md
```
