from fastapi import FastAPI, Depends, HTTPException



from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session

import models, schemas
from database import engine, SessionLocal

import random


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables in database
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_fake_weather():
    weather_conditions = ["Hot", "Cold", "Moderate", "Humid", "Rainy"]
    return random.choice(weather_conditions)

@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):

    # Check if user already exists
    existing_user = db.query(models.User).filter(models.User.username == user.username).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = models.User(
        username=user.username,
        password=user.password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@app.post("/login", response_model=schemas.UserResponse)
def login(user: schemas.UserCreate, db: Session = Depends(get_db)):

    db_user = db.query(models.User).filter(models.User.username == user.username).first()

    if not db_user or db_user.password != user.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return db_user



@app.post("/appliance/add/{username}", response_model=schemas.ApplianceResponse)
def add_appliance(username: str, appliance: schemas.ApplianceCreate, db: Session = Depends(get_db)):

    # Find user
    user = db.query(models.User).filter(models.User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Energy calculation
    energy = (appliance.power * appliance.hours_per_day) / 1000

    new_appliance = models.Appliance(
        name=appliance.name,
        power=appliance.power,
        hours_per_day=appliance.hours_per_day,
        daily_energy=energy,
        user_id=user.id
    )

    db.add(new_appliance)
    db.commit()
    db.refresh(new_appliance)

    return new_appliance

@app.get("/appliance/all/{username}", response_model=list[schemas.ApplianceResponse])
def get_appliances(username: str, db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user.appliances


@app.get("/energy/daily/{username}")
def get_daily_energy(username: str, db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    total = sum(a.daily_energy for a in user.appliances)

    return {"daily_energy_kwh": total}


@app.get("/energy/monthly/{username}")
def get_monthly_energy(username: str, db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    total_daily = sum(a.daily_energy for a in user.appliances)
    monthly = total_daily * 30

    return {"monthly_energy_kwh": monthly}


@app.get("/recommend/{username}")
def get_recommendations(username: str, db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    appliances = user.appliances

    if not appliances:
        return {"tips": ["No appliances found. Add appliances first."]}

    tips = []
    total_energy = 0

    cost_per_unit = 8

    # Analyze appliances
    for a in appliances:
        total_energy += a.daily_energy
        name = a.name.lower()

        # 🔹 AC
        if name == "ac":
            if a.hours_per_day > 5:
                tips.append("❄️ Your AC usage is high. Use sleep mode to save up to 20% electricity.")

            tips.append("🌡️ Set AC temperature to 24°C. Each degree increase saves ~6% energy (₹150–₹300/month).")
            tips.append("🧹 Clean AC filters monthly to avoid 5–15% extra energy consumption.")

        # 🔹 FAN
        if name == "fan":
            if a.hours_per_day > 10:
                tips.append("🌀 Fan running too long. Turn off when not needed.")

        # 🔹 FRIDGE
        if name == "fridge":
            tips.append("🧊 Avoid frequent fridge door opening.")
            tips.append("🔌 Keep fridge away from heat sources.")

        # 🔹 LIGHTS
        if name in ["light", "bulb"]:
            tips.append("💡 Switch to LED bulbs to save up to 80% electricity.")

        # 🔹 TV
        if name == "tv":
            tips.append("📺 Turn off TV completely instead of standby mode.")

        # 🔹 HIGH POWER DEVICE
        if a.power > 2000:
            saving = int((a.power / 1000) * 30 * cost_per_unit)
            tips.append(f"⚡ {a.name} is high power. Reducing 1 hour usage can save ~₹{saving}/month.")

        # 🔹 HIGH DAILY ENERGY
        if a.daily_energy > 5:
            tips.append(f"⚠️ {a.name} consumes high daily energy.")

    #  Total energy analysis
    monthly_bill = total_energy * 30 * cost_per_unit

    if total_energy < 5:
        tips.append("✅ Your energy usage is efficient.")
    elif total_energy <= 15:
        tips.append("⚠️ Moderate energy usage. Try optimizing.")
    else:
        tips.append(f"❌ High energy usage! You could save ₹{int(monthly_bill*0.2)} by reducing consumption.")

    # 🔥 Highest consuming appliance
    max_appliance = max(appliances, key=lambda x: x.daily_energy)
    tips.append(f"🔝 {max_appliance.name} is your highest energy consuming appliance.")

    # 🔥 Remove duplicate tips
    tips = list(set(tips))

    return {
        "total_daily_energy": round(total_energy, 2),
        "monthly_bill_estimate": round(monthly_bill, 2),
        "tips": tips
    }

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.post("/chatbot")
def chatbot(message: dict):

    user_msg = message["message"].lower()

    weather = get_fake_weather()

    # 🔥 RULE-BASED RESPONSE
    if "ac" in user_msg or "cool" in user_msg:
        advice = "Use AC at 24°C and clean filters for efficiency."

    elif "bill" in user_msg or "save" in user_msg:
        advice = "Turn off unused appliances and switch to LED bulbs."

    elif "fan" in user_msg:
        advice = "Use fan instead of AC when possible to save energy."

    elif "fridge" in user_msg:
        advice = "Avoid opening fridge frequently and keep it away from heat."

    else:
        advice = "Use appliances efficiently to reduce electricity usage."

    # 🔥 WEATHER BASED INTELLIGENCE
    if weather == "Hot":
        advice += " It is hot today, so reduce AC usage time and maintain 24°C."

    elif weather == "Cold":
        advice += " It is cold today, avoid unnecessary heaters."

    elif weather == "Rainy":
        advice += " It is rainy, ensure proper insulation and avoid moisture damage."

    elif weather == "Humid":
        advice += " It is humid, use ventilation instead of AC when possible."

    return {
        "weather": weather,
        "reply": advice
    }