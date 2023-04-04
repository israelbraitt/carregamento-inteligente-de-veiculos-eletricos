from paho.mqtt import client as mqtt
import time

ADDR = "public.mqtthq.com"
PORT = 1883
CAR_TOPIC = "car/paths"

broker = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print("Connection with " + str(client._client_id) + ": " + str(rc))

def on_message(client, userdata, message):
    print("Message received on topic "+message.topic+" with QoS "+str(message.qos)+" and payload "+str(message.payload))



broker.on_message = on_message
broker.on_connect = on_connect

broker.connect(ADDR, PORT)
broker.loop_start()
broker.subscribe("central/paths")


print("STARTING CENTRAL BROKER...")
while True:
    time.sleep(1)
