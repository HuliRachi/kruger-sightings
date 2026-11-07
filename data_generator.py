import json
import os
import random
from datetime import datetime, timedelta

run_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")

OUTPUT_DIR = "batch_01"
TARGET_FOLDER = os.path.join(OUTPUT_DIR, "filtered_youtube")
os.makedirs(TARGET_FOLDER, exist_ok=True)

print("Simulating realistic YouTube API tracking records for Kruger Latest Sightings...")

TOTAL_RECORDS = 15  

ANIMALS_CARNIVORES = ["Leopard", "Lion Pack", "Hyena Pack", "Crocodile", "Python", "Cheetah"]
ANIMALS_HERBIVORES = ["Warthog", "Porcupine", "Buffalo Herd", "Elephant", "Baboon", "Impala"]
ACTIONS = [
    "Ambushes", "Steals Meal From", "Turns Tables On", "Smashes Into Vehicle To Escape",
    "Learns Painful Lesson From", "Fights off", "Chases Down", "Lets Out Crazy Call Near"
]
LOCATIONS = ["at the Crocodile River", "near Skukuza", "at Satara Waterhole", "in Lower Sabie"]

def generate_random_title():
    if random.random() > 0.15:
        c = random.choice(ANIMALS_CARNIVORES)
        h = random.choice(ANIMALS_HERBIVORES)
        a = random.choice(ACTIONS)
        return f"{c} {a} {h}" if random.random() > 0.5 else f"{h} Escapes As {c} {a.lower()}"
    else:
        return f"Live from the {random.choice(['Crocodile River', 'Sabie River', 'Olifants Viewpoint'])} at the Kruger National Park"

clickstream_file = os.path.join(TARGET_FOLDER, f"youtube_sightings_{run_suffix}.json")

with open(clickstream_file, "w", encoding="utf-8") as f:
    for _ in range(TOTAL_RECORDS):
        title = generate_random_title()
        
        is_live = "Live from" in title
        live_status = "live" if is_live else "none"
        
        views = random.randint(100, 500) if is_live else random.randint(15000, 1500000)
        comments = 0 if is_live or views < 5000 else int(views * random.uniform(0.001, 0.004))
        likes = random.randint(5, 50) if is_live else int(views * random.uniform(0.008, 0.015))
        
        days_back = random.randint(0, 30)
        hours_back = random.randint(0, 23)
        timestamp = (datetime.now() - timedelta(days=days_back, hours=hours_back)).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        char_pool = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        video_id = "".join(random.choice(char_pool) for _ in range(11))
        
        sighting_record = {
            "title": title,
            "id": video_id,
            "published_at": timestamp,
            "live_broadcast_content": live_status,
            "view_count": str(views),
            "comment_count": str(comments),
            "favorite_count": "0",  
            "like_count": str(likes)
        }
        
        f.write(json.dumps(sighting_record) + "\n")

print(f"Generated JSON Lines File: {clickstream_file} ({TOTAL_RECORDS} rows)")
print(f"Successfully staged to your ingestion target directory layout: './{TARGET_FOLDER}/'")
