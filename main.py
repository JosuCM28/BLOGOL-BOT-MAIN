# main.py
import os
import json
import glob
import requests
from datetime import datetime, timedelta

from services.api import get_categories
from services.ia import get_description
from services.images import get_profile_image, get_post_image
from generators.users import create_user
from generators.posts import create_post_and_publish
from utils.delta import convert_to_delta
from config.settings import TOKEN_TELEGRAM, CHAT_ID_TELEGRAM

LAST_RUN_FILE = "last_run.json"
TASK_NAME = "create_user"
INTERVAL = timedelta(hours=1)

def notify_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {
        "chat_id": CHAT_ID_TELEGRAM,
        "text": message
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("❌ Error al notificar por Telegram:", e)

def load_last_run():
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, "r") as f:
            return json.load(f)
    return {}

def save_last_run(data):
    with open(LAST_RUN_FILE, "w") as f:
        json.dump(data, f)

def should_run(last_time_str):
    if not last_time_str:
        return True
    last_time = datetime.fromisoformat(last_time_str)
    return datetime.now() - last_time >= INTERVAL

def run_scheduled_posts():
    schedule_files = glob.glob("post_schedule_*.json")
    posts_ejecutados = 0

    for file in schedule_files:
        with open(file, "r") as f:
            schedule = json.load(f)

        if not schedule:
            continue

        now = datetime.now()
        updated_schedule = []

        for iso_time in schedule:
            scheduled_time = datetime.fromisoformat(iso_time)

            print(f"📄 Evaluando: {iso_time}")
            print(f"🕑 Ahora: {now.isoformat()} | Programado: {scheduled_time.isoformat()}")

            if scheduled_time <= now:
                email = file.replace("post_schedule_", "").replace(".json", "")
                token_file = f"user_token_{email}.json"
                if os.path.exists(token_file):
                    with open(token_file, "r") as tf:
                        user = json.load(tf)
                        try:
                            create_post_and_publish(user)
                            notify_telegram(f"📝 Post creado para {user['name']} a las {scheduled_time.time()}")
                            posts_ejecutados += 1
                        except Exception as e:
                            print(f"⚠️ Error al crear post para {email}: {e}")
                            notify_telegram(f"⚠️ Error al crear post para {email}: {str(e)}")
            else:
                updated_schedule.append(iso_time)

        with open(file, "w") as f:
            json.dump(updated_schedule, f)

        if not updated_schedule:
            os.remove(file)
            print(f"🗑️ Archivo de horarios eliminado: {file}")

    return posts_ejecutados > 0

if __name__ == "__main__":
    last_run = load_last_run()
    last_time_str = last_run.get(TASK_NAME)

    if should_run(last_time_str):
        try:
            user = create_user()
            notify_telegram(
                f"✅ Bot ejecutado con éxito.\n"
                f"👤 USUARIO CREADO ✅\n"
                f"Nombre: {user['name']}\n"
                f"Apellido: {user['last_name']}\n"
                f"Email: {user['email']}\n"
            )
            with open(f"user_token_{user['email']}.json", "w") as f:
                json.dump(user, f)

            last_run[TASK_NAME] = datetime.now().isoformat()
            save_last_run(last_run)
        except Exception as e:
            notify_telegram(f"❌ Falló el bot: {str(e)}")
    else:
        print("⏳ No es momento aún.")
        notify_telegram("⏳ No es momento aún de crear un nuevo usuario")

    if run_scheduled_posts():
        print("✅ Posts programados ejecutados con éxito.")
        notify_telegram("✅ Posts programados ejecutados con éxito.")
    else:
        print("⏳ No hay publicaciones programadas para este momento.")
        notify_telegram("⏳ No hay publicaciones programadas para este momento.")
