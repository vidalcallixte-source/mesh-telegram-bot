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

# Topics Meshtastic 2.7.x
TOPIC_IN = "MshNdEsk8t/2/json/#"     # uplink mesh → MQTT
TOPIC_CMD = "MshNdEsk8t/2/cmd"       # downlink MQTT → mesh

TELEGRAM_TOKEN = "TON_TOKEN_TELEGRAM_ICI"
CHAT_ID = TON_CHAT_ID_ICI  # ex: 123456789

# -----------------------------
# TELEGRAM → MQTT (send to mesh)
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
# MQTT → TELEGRAM (uplink)
# -----------------------------
def on_mqtt_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
    except:
        return

    # On ne prend que les messages texte
    if "decoded" in data and "text" in data["decoded"]:
        text = data["decoded"]["text"]
        context = userdata["tg_context"]
        context.bot.send_message(chat_id=CHAT_ID, text=f"[Mesh] {text}")
        print(f"[MQTT] Reçu du mesh : {text}")

# -----------------------------
# MQTT SETUP
# -----------------------------
def setup_mqtt(tg_context):
    client = mqtt.Client(userdata={"tg_context": tg_context})

    client.username_pw_set(MQTT_USER, MQTT_PASS)

    client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)
    client.tls_insecure_set(False)

    client.on_message = on_mqtt_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(TOPIC_IN)

    return client

# -----------------------------
# MAIN
# -----------------------------
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_telegram))

    mqtt_client = setup_mqtt(updater.bot)
    mqtt_client.loop_start()

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
