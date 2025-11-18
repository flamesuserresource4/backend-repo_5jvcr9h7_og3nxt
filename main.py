import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import Benefit, Inquiry

app = FastAPI(title="Benefits Finder API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Benefits Finder backend is running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# ---------- Benefits Endpoints ----------

class SeedResult(BaseModel):
    inserted: int

@app.post("/api/benefits/seed", response_model=SeedResult)
def seed_benefits():
    """Seed the database with a small catalog of benefits if empty"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    existing = db["benefit"].count_documents({})
    if existing > 0:
        return {"inserted": 0}

    seed_data = [
        Benefit(
            name="SNAP (Food Assistance)",
            agency="USDA",
            description="Monthly funds on an EBT card to help buy groceries.",
            category="food",
            url="https://www.fns.usda.gov/snap",
            eligibility_notes="Based on household size, income, and expenses.",
            max_income=30000,
            tags=["low-income", "household"]
        ),
        Benefit(
            name="Medicaid",
            agency="State Medicaid Agency",
            description="Free or low-cost health coverage for eligible individuals.",
            category="healthcare",
            url="https://www.medicaid.gov/",
            eligibility_notes="Based on income, disability, pregnancy, and other factors.",
            max_income=28000,
            tags=["health", "low-income"]
        ),
        Benefit(
            name="Pell Grant",
            agency="U.S. Department of Education",
            description="Grant to help pay for college, does not need to be repaid.",
            category="education",
            url="https://studentaid.gov/understand-aid/types/grants/pell",
            eligibility_notes="Undergraduate students with exceptional financial need.",
            max_income=60000,
            min_age=16,
            tags=["students", "education"]
        ),
        Benefit(
            name="Section 8 Housing Choice Voucher",
            agency="HUD",
            description="Rental assistance vouchers for low-income families.",
            category="housing",
            url="https://www.hud.gov/",
            eligibility_notes="Waitlists common; based on income and family size.",
            max_income=35000,
            requires_dependents=True,
            tags=["housing", "family"]
        ),
    ]

    inserted = 0
    for item in seed_data:
        create_document("benefit", item)
        inserted += 1

    return {"inserted": inserted}

@app.get("/api/benefits", response_model=List[Benefit])
def list_benefits(limit: Optional[int] = 50):
    docs = get_documents("benefit", {}, limit)
    # convert ObjectId to string-safe response
    cleaned = []
    for d in docs:
        d.pop("_id", None)
        cleaned.append(Benefit(**d))
    return cleaned

@app.post("/api/match", response_model=List[Benefit])
def match_benefits(profile: Inquiry):
    """Simple rule-based matching to surface likely benefits"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    # Fetch all benefits for now and filter in Python (small set). For scale, build Mongo queries
    benefits = list_benefits()
    matches: List[Benefit] = []

    for b in benefits:
        score = 0
        # Income threshold
        if profile.income is not None and b.max_income is not None:
            if profile.income <= b.max_income:
                score += 2
            else:
                continue  # ineligible by income
        # Age bounds
        if b.min_age is not None and profile.age is not None and profile.age < b.min_age:
            continue
        if b.max_age is not None and profile.age is not None and profile.age > b.max_age:
            continue
        # Location (if specified on benefit)
        if b.location and profile.location and b.location.lower() != profile.location.lower():
            continue
        # Flags
        if b.requires_disability and not profile.disability:
            continue
        if b.requires_veteran and not profile.veteran:
            continue
        if b.requires_dependents and (profile.dependents is None or profile.dependents == 0):
            continue

        # Soft tag match boosts
        if profile.tags and b.tags:
            shared = set([t.lower() for t in profile.tags]) & set([t.lower() for t in b.tags])
            if shared:
                score += 1

        if score >= 0:
            matches.append(b)

    return matches

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
