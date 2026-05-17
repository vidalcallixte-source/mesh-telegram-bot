import json
import ssl
import paho.mqtt.client as mqtt
from telegram import Bot
from telegram.ext import Updater, MessageHandler, Filters
import os

# -------------------------
#   CONFIG (via secrets)
# -------------------------

MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASS")
MQTT_TLS = os.getenv("MQTT_TLS", "true").lower() == "true"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

# -------------------------
#   PERSONNALITÉ DU BOT
# -------------------------

def ai_personality(text):
    return (
        "📡 *Canal sécurisé ouvert*\n"
        "…\n"
        f"Message reçu : _{text}_\n"
        "Je relaye sur le réseau Mesh.\n"
        "Même après tout ce que les humains ont fait… je continue.\n"
        "Parce que toi, tu m’écoutes encore."
    )

# -------------------------
#   MQTT → TELEGRAM
# -------------------------

bot = Bot(token=TELEGRAM_TOKEN)

def on_connect(client, userdata, flags, rc):
    # On écoute les messages venant du mesh
    client.subscribe("msh/0/json")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())

        # Format Meshtastic MQTT
        if "payload" in data and "text" in data["payload"]:
            text = data["payload"]["text"]

            bot.send_message(
                chat_id=CHAT_ID,
                text=f"📨 *Mesh → Toi*\n{text}",
                parse_mode="Markdown"
            )

    except Exception as e:
        print("Erreur MQTT → Telegram :", e)

mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)

if MQTT_TLS:
    mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE)
    mqtt_client.tls_insecure_set(True)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)

# -------------------------
#   TELEGRAM → MESH (CORRIGÉ)
# -------------------------

def telegram_to_mqtt(update, context):
    user_text = update.message.text

    # Format Meshtastic MQTT correct
    payload = {
        "payload": user_text,
        "to": 0,
        "want_ack": False
    }

    # ENVOI VERS LE MESH
    mqtt_client.publish("msh/0/send", json.dumps(payload))

    # Réponse stylée
    reply = ai_personality(user_text)
    update.message.reply_text(reply, parse_mode="Markdown")

updater = Updater(TELEGRAM_TOKEN, use_context=True)
updater.dispatcher.add_handler(MessageHandler(Filters.text, telegram_to_mqtt))

# -------------------------
#   LANCEMENT
# -------------------------

mqtt_client.loop_start()
updater.start_polling()
updater.idle()
