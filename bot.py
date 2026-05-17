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
CHAT_ID = 8950301568

mqtt_client = None  # global

# -----------------------------
# TELEGRAM → MQTT
# -----------------------------
def handle_telegram(update, context):
    text = update.message.text

    payload = {
        "cmd": "sendtext",
        "text": text,
        "to": 0
    }

    mqtt_client.publish(TOPIC_CMD, json.dumps(payload))
    print(f"[BOT] Message envoyé au mesh : {text}")

# -----------------------------
# MQTT → TELEGRAM
# -----------------------------
def on_mqtt_message(client, userdata, msg):
    bot = userdata["bot"]

    try:
        data = json.loads(msg.payload.decode())
    except:
        return

    if "decoded" in data and "text" in data["decoded"]:
        text = data["decoded"]["text"]
        bot.send_message(chat_id=CHAT_ID, text=f"[Mesh] {text}")
        print(f"[MQTT] Reçu du mesh : {text}")

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

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
