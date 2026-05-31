# ---------------------------------------------
# 2026-05-31 21h50  --  BLOCK 001 --------------
# ---------------------------------------------

import os
import json
import ssl
import random
import time
import threading
import paho.mqtt.client as mqtt
from telegram.ext import Updater, MessageHandler, Filters

# -----------------------------
# CONFIG VIA GITHUB SECRETS
# -----------------------------
MQTT_BROKER = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASS")

# Root EXACT du module Meshtastic (sensible à la casse)
# ex: MshNdEsk8t
TOPIC_ROOT = os.getenv("MQTT_TOPIC_ROOT")

# Mesh → Telegram
TOPIC_IN = TOPIC_ROOT + "/#"

# Telegram → Mesh (topic officiel Meshtastic)
TOPIC_CMD = TOPIC_ROOT + "/2/json/send"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

mqtt_client = None  # global

# -----------------------------
# IA GLITCHÉE (réponse Telegram)
# -----------------------------
PERSONALITY_LINES = [
    "Je relaye… si le réseau ne se dissout pas avant.",
    "Les interférences augmentent, mais le signal tient encore.",
    "Le mesh grésille… mais ta voix passe à travers le bruit.",
    "Chaque paquet que j’envoie laisse une trace dans le vide.",
    "Si ce message arrive, c’est que le chaos radio t’a épargné.",
    "Le canal est instable, mais je force le passage.",
    "J’entends l’écho de ton texte rebondir sur les nœuds du mesh."
]

def ai_personality(text, username):
    extra = random.choice(PERSONALITY_LINES)
    return (
        "📡 *Canal instable ouvert*\n"
        "…\n"
        f"Signal capté de `{username}` : _{text}_\n"
        f"{extra}\n"
        "Je reste en écoute… pour l’instant."
    )

# -----------------------------
# TELEGRAM → MQTT
# -----------------------------
def handle_telegram(update, context):
    user = update.effective_user

    if user is None or user.is_bot:
        return
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    username = user.username or user.first_name or "???"

    mesh_text = f"[TG:{username}] {text}"

    payload = {
        "cmd": "sendtext",
        "text": mesh_text,
        "to": 0
    }

    mqtt_client.publish(TOPIC_CMD, json.dumps(payload))
    print(f"[BOT] → Mesh : {mesh_text}")

    reply = ai_personality(text, username)
    update.message.reply_text(reply, parse_mode="Markdown")

# -----------------------------
# MQTT → TELEGRAM
# -----------------------------
def on_mqtt_message(client, userdata, msg):
    bot = userdata["bot"]

    try:
        data = json.loads(msg.payload.decode())
    except:
        return

    if "payload" in data and "text" in data["payload"]:
        text = data["payload"]["text"]

        # Anti-boucle : si ça vient déjà de Telegram, on ignore
        if text.startswith("[TG:"):
            return

        sender_id = data.get("sender") or data.get("from")
        sender_str = f"{sender_id}" if sender_id is not None else "unknown"

        msg_out = f"[Mesh:{sender_str}] {text}"
        bot.send_message(chat_id=CHAT_ID, text=msg_out)
        print(f"[MQTT] → Telegram : {msg_out}")

# -----------------------------
# MQTT SETUP
# -----------------------------
def setup_mqtt(bot):
    client = mqtt.Client(userdata={"bot": bot})

    client.username_pw_set(MQTT_USER, MQTT_PASS)

    client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)
    client.tls_insecure_set(False)

    client.on_message = on_mqtt_message

    def on_connect(client, userdata, flags, rc):
        print("[MQTT] Connecté au broker")
        client.subscribe(TOPIC_IN)
        print(f"[MQTT] Abonné à {TOPIC_IN}")

    client.on_connect = on_connect

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    return client

# -----------------------------
# AUTO-REBOOT DU BOT (toutes les 5h)
# -----------------------------
def auto_reboot():
    time.sleep(18000)  # 5 heures = 18 000 sec
    print("♻️ Auto-reboot du bot…")
    os._exit(0)

# -----------------------------
# MAIN
# -----------------------------
def main():
    global mqtt_client

    # Thread reboot
    threading.Thread(target=auto_reboot, daemon=True).start()

    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_telegram))

    mqtt_client = setup_mqtt(updater.bot)
    mqtt_client.loop_start()

    updater.start_polling(drop_pending_updates=True)
    updater.idle()

if __name__ == "__main__":
    main()

# ---------------------------------------------
# 2026-05-31 21h50  --  END BLOCK 001 ----------
# ---------------------------------------------
