import requests
from datetime import datetime, timedelta
import random
import json
from faker import Faker
from config.settings import API_BASE_URL, build_headers
from services.ia import get_description
from services.images import get_profile_image
from generators.posts import create_post_and_publish

faker = Faker('es_ES')
user_tokens = {}

def generate_post_schedule():
    start_hour = 6
    end_hour = 22
    now = datetime.now()
    today = now.date()

    times = []
    while len(times) < 10:
        random_hour = random.randint(start_hour, end_hour - 1)
        random_minute = random.randint(0, 59)
        scheduled_time = datetime.combine(today, datetime.min.time()) + timedelta(hours=random_hour, minutes=random_minute)

        if scheduled_time > now:
            times.append(scheduled_time.isoformat())

    times.sort()
    return times


def create_user():
    sex = random.choice(["female", "male"])
    name = faker.first_name_male() if sex == "male" else faker.first_name_female()
    last_name = faker.last_name()
    email = faker.email()
    
    payload = {
        "name": name,
        "last_name": last_name,
        "email": email,
        "password": "password",
    }
    
    response = requests.post(f"{API_BASE_URL}/register", json=payload, headers=build_headers())
    
    if response.status_code == 201:
        print("✅ Usurio creado con éxito")
    else:
        print("❌ Error al crear el usuario")
        return

    user_tokens[email] = {
        "id": response.json()["user"]["id"],
        "token": response.json()["token"],
    }

    bio = get_description(name, sex)
    image = get_profile_image(user_tokens[email]["token"], sex)
    
    update_profile(user_tokens[email]["token"], user_tokens[email]["id"], name, last_name, email, bio, image)
    
    post_schedule = generate_post_schedule()

    with open(f"post_schedule_{email}.json", "w") as f:
        json.dump(post_schedule, f)

    return {
        "id": user_tokens[email]["id"],
        "token": user_tokens[email]["token"],
        "name": name,
        "last_name": last_name,
        "email": email,
        "bio": bio,
        "image": image
    }


    
    
def update_profile(token, id, name, last_name, email, bio, image):
    payload = {
        "name": name,
        "last_name": last_name,
        "email": email,
        "bio": bio,
        "profile_image": image,
    }
        
    response = requests.put(f"{API_BASE_URL}/users/{id}/profile", json=payload, headers=build_headers(token))
    if response.status_code == 200:
        print("✅ Perfil actualizado con éxito")
    else:
        print("❌ Error al actualizar el perfil")