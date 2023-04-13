from paho.mqtt import client as mqtt_client
from random import randint
from time import sleep
import threading
import socket
import json

class Station:
    def __init__(self, location, code, queue):
        self.location = location
        self.code = code
        self.queue = queue

    def getJson(self):
        json_code = "{\"code\": \"" + str(self.code) + "\", "
        json_location = "\"location\": \"" + str(self.location) + "\", "
        json_queue = "\"queue\":" + str(queue) + "\"}"
        return json_code + json_location + json_queue

class Server:

    def __init__(self, location):
        self.BROKER_ADDR = "127.0.0.1"
        self.BROKER_PORT = 1915

        self.CLOUD_HOST = "192.168.1.6"
        self.CLOUD_PORT = 1917

        self.FORMAT = 'utf-8'

        self.CAR_BATTERY_TOPIC = "REDESP2IG/car/battery"
        self.STATION_TOPIC = "REDESP2IG/station/queue"
        self.CAR_PATH_TOPIC = "REDESP2IG/car/path"

        self.location = location
        self.station_list = []
        self.cloud_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)



    def on_connect(self, client: mqtt_client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
            client.subscribe(self.CAR_BATTERY_TOPIC)
            client.subscribe(self.STATION_TOPIC)
        else:
            print("Failed to connect, return code %d\n", rc)

    def on_message(self, client: mqtt_client, userdata, message):

        decoded = message.payload.decode(self.FORMAT)
        print("Message received on topic "+message.topic+" with QoS "+str(message.qos)+" and payload " + str(decoded))

        match message.topic:
            case "REDESP2IG/car/battery":
                print("sneed")
            case "REDESP2IG/station/queue":
                print("chuck")

    def tcpStart(self):
        self.cloud_socket.connect((self.CLOUD_HOST, self.CLOUD_PORT))
        print("Connected to cloud.")

    def mqttStart(self):
        client = mqtt_client.Client()
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.connect(self.BROKER_ADDR, self.BROKER_PORT)
        return client

    def getPath(self, car_info):
        best_queue = 25
        best_station = None
        for station in self.station_list:
            if station.queue < best_queue:
                best_station = station
        if best_station:
            return best_station
        else:
            remaining_time = int(car_info.get("battery"))//max(1, int(car_info.get("mode")))

            message_location = "{\"location\": \"" + str(self.location) + "\", "
            message_time = "\"time left\": \"" + str(remaining_time) + "\"}"

            message = message_location + message_time
            response = self.communeWithCloud(message)
            response = json.loads(response)
            if response.get("result") == "posto encontrado":
                best_station = Station(self.location, response.get("code"), int(response.get("queue")))

    def publishPath(self, station_info):
        pass

    def communeWithCloud(self, message):
        self.cloud_socket.send(message.encode(self.FORMAT))
        response = self.cloud_socket.recv(1024)
        return response.decode(self.FORMAT)

    def publish(self, client: mqtt_client, payload):
        pass

    def main(self):
        pass
