from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
import os
import random
import shutil
import json
from datetime import datetime
import jdatetime

app = FastAPI()


SEASONS = {
    "spring": [1, 2, 3],
    "summer": [4, 5, 6],
    "fall":   [7, 8, 9],
    "winter": [10, 11, 12]
}

TRACKER_FILE = "seasons_tracker.json"
OUTPUT_FILE = "output.jpg"
IMAGE_FOLDER = "./"
MESSAGES_FILE = "messages.json"
STATE_FILE = "state.json"



def get_jalali_season():
    month = jdatetime.date.today().month
    for season, months in SEASONS.items():
        if month in months:
            return season
    return "unknown"

def load_tracker():
    if not os.path.exists(TRACKER_FILE):
        return {s: {"used": [], "last_reset": None} for s in SEASONS}
    with open(TRACKER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_tracker(tracker):
    with open(TRACKER_FILE, "w", encoding="utf-8") as f:
        json.dump(tracker, f)

def needs_reset(season, tracker, all_images):
    used = tracker[season]["used"]
    last_reset = tracker[season]["last_reset"]
    if len(used) >= len(all_images):
        if not last_reset:
            return True
        try:
            last_dt = datetime.strptime(last_reset, "%Y-%m-%d")
            return (datetime.today() - last_dt).days >= 45
        except Exception:
            return True
    return False

def select_image(season, tracker):
    folder_path = os.path.join(IMAGE_FOLDER, season)
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Season folder not found: {folder_path}")

    all_images = sorted([
        f for f in os.listdir(folder_path)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ])
    if not all_images:
        raise FileNotFoundError(f"No image files in: {folder_path}")

    if needs_reset(season, tracker, all_images):
        tracker[season]["used"] = []
        tracker[season]["last_reset"] = datetime.today().strftime("%Y-%m-%d")

    used = tracker[season]["used"]
    available = list(set(all_images) - set(used))
    if not available:
        tracker[season]["used"] = []
        available = all_images

    selected = random.choice(available)
    tracker[season]["used"].append(selected)
    return os.path.join(folder_path, selected)

def load_messages():
    with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
        return list(json.load(f).values())

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"index": 0}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)

def get_daily_message():
    messages = load_messages()
    state = load_state()
    index = state["index"]
    message = messages[index]
    index = (index + 1) % len(messages)
    save_state({"index": index})
    return message


# API Routes 
@app.get("/get-image")
def api_get_image():
    try:
        season = get_jalali_season()
        if season == "unknown":
            return JSONResponse(status_code=400, content={"error": "Unknown Jalali season."})

        tracker = load_tracker()
        selected_path = select_image(season, tracker)
        shutil.copyfile(selected_path, OUTPUT_FILE)
        save_tracker(tracker)

        return FileResponse(OUTPUT_FILE, media_type="image/jpeg", filename="output.jpg")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/get-message")
def api_get_message():
    try:
        message = get_daily_message()
        return JSONResponse(content={"message": message})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/greeting")
def api_get_greeting():
    try:
        # Get message
        message = get_daily_message()

        # Get image
        season = get_jalali_season()
        if season == "unknown":
            return JSONResponse(status_code=400, content={"error": "Unknown Jalali season."})
        tracker = load_tracker()
        selected_path = select_image(season, tracker)
        shutil.copyfile(selected_path, OUTPUT_FILE)
        save_tracker(tracker)

        return JSONResponse(content={
            "caption": message,
            "image_url": "/get-image"
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
