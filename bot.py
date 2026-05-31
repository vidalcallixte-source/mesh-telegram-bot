import json
import ssl
import paho.mqtt.client as mqtt
from telegram.ext import Updater, MessageHandler, Filters

# -----------------------------
# CONFIG
# -----------------------------
MQTT_BROKER = "18841154e5a04ceab0311bb42ad58777.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "Esk8_63"
MQTT_PASS = "Esk8_63000"

TOPIC_IN = "MshNdEsk8t/2/json/#"
TOPIC_CMD = "MshNdEsk8t/2/cmd"

TELEGRAM_TOKEN = "8871950569:AAE9N6SJcmJ9nlL9yztebszlE7nvZTMIym0"
CHAT_ID = 8950301568   # ton chat privé, mais le bot fonctionnera aussi en groupe

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

    # Sécurité : ignorer les bots, messages vides, messages système
    if user is None or user.is_bot:
        return
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    username = user.username or user.first_name or "???"

    # Message envoyé au mesh avec tag Telegram
    mesh_text = f"[TG:{username}] {text}"

    payload = {
        "cmd": "sendtext",
        "text": mesh_text,
        "to": 0
    }

    mqtt_client.publish(TOPIC_CMD, json.dumps(payload))
    print(f"[BOT] → Mesh : {mesh_text}")

    # Réponse Telegram stylée
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

    # Meshtastic v2.x : texte dans data["payload"]["text"]
    if "payload" in data and "text" in data["payload"]:
        text = data["payload"]["text"]

        # Anti-boucle : si le message vient déjà de Telegram, on ne renvoie pas
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
