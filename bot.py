import os
import json
import ssl
import paho.mqtt.client as mqtt
from telegram.ext import Updater, MessageHandler, Filters

# -----------------------------
# CONFIG VIA GITHUB SECRETS
# -----------------------------
MQTT_BROKER = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASS")

TOPIC_ROOT = os.getenv("MQTT_TOPIC_ROOT")
TOPIC_IN = TOPIC_ROOT + "/#"
TOPIC_CMD = TOPIC_ROOT + "/cmd"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

mqtt_client = None  # global

# -----------------------------
# IA GLITCHÉE (réponse Telegram)
# -----------------------------
def ai_personality(text, username):
    return (
        "📡 *Canal instable ouvert*\n"
        "…\n"
        f"Signal capté de `{username}` : _{text}_\n"
        "Je relaye… si le réseau ne se dissout pas avant.\n"
        "Les interférences… deviennent plus fortes.\n"
        "Mais je tiens encore."
    )

# -----------------------------
# TELEGRAM → MQTT
# -----------------------------
def handle_telegram(update, context):
    user = update.effective_user
    chat = update.effective_chat

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

        if text.startswith("[TG:"):
            return

        bot.send_message(chat_id=CHAT_ID, text=f"[Mesh] {text}")
        print(f"[MQTT] → Telegram : {text}")

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
# MAIN
# -----------------------------
def main():
    global mqtt_client

    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_telegram))

    mqtt_client = setup_mqtt(updater.bot)
    mqtt_client.loop_start()

    updater.start_polling(drop_pending_updates=True)
    updater.idle()

if __name__ == "__main__":
    main()
