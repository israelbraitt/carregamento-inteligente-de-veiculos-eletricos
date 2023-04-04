from paho.mqtt import client as mqtt
import time

BROKER_ADDR = "broker.hivemq.com"
BROKER_PORT = 1883
CENTRAL_ADDR = "public.mqtthq.com"
CENTRAL_PORT = BROKER_PORT

STATION_TOPIC = "station"
CAR_BATTERY_TOPIC = "car/battery"
CAR_PATH_TOPIC = "car/path"
CENTRAL_TOPIC = "central/paths"

broker = mqtt.Client()
central = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print("Connection with " + str(client._client_id) + ": " + str(rc))

def on_message(client, userdata, message):
    print("Message received on topic "+message.topic+" with QoS "+str(message.qos)+" and payload "+str(message.payload))
    if int(message.payload) == 2:
        print("2")
        central.publish(CENTRAL_TOPIC, message.payload)


broker.on_message = on_message
broker.on_connect = on_connect
broker.connect(BROKER_ADDR, BROKER_PORT)
broker.loop_start()
broker.subscribe(STATION_TOPIC)
broker.subscribe(CAR_BATTERY_TOPIC)


central.on_connect = on_connect
central.connect(CENTRAL_ADDR, CENTRAL_PORT)
central.loop_start()
central.subscribe(CENTRAL_TOPIC)


print("STARTING LOCAL BROKER...")
while True:
    time.sleep(1)
