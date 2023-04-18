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
        json_result = "{\"result\": \"posto encontrado\", "
        json_code = "\"code\": \"" + str(self.code) + "\", "
        json_location = "\"location\": \"" + str(self.location) + "\", "
        json_queue = "\"queue\":" + str(self.queue) + "\"}"
        return json_result + json_code + json_location + json_queue

class LocalServer:

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
        self.station_dict = {}
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
                path = self.getPath(decoded)
                self.publishPath(client, path)
            case "REDESP2IG/station/queue":
                self.updateQueue(decoded)
            case "REDESP2IG/station/register":
                self.registerStation(decoded)

    def tcpStart(self):
        self.cloud_socket.connect((self.CLOUD_HOST, self.CLOUD_PORT))
        print("Connected to cloud.")

    def mqttStart(self):
        client = mqtt_client.Client()
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.connect(self.BROKER_ADDR, self.BROKER_PORT)
        return client

    def updateQueue(self, station_info):
        station_info = json.loads(station_info)
        station_find = self.station_dict.get(station_info.get("code"))
        if station_find:
            station_find.queue = station_info.get("queue")

    def registerStation(self, station_info):
        station_info = json.loads(station_info)
        new_station = Station(self.location, station_info.get("code"), station_info.get("queue"))
        self.station_dict[station_info.get("code")] = new_station

    def getPath(self, car_info):
        best_queue = 25
        best_station = None
        for station in self.station_dict.values():
            if station.queue < best_queue:
                best_station = station
        if best_station:
            return best_station.getJson()
        else:
            car_info = json.loads(car_info)
            remaining_time = int(car_info.get("battery"))//max(1, int(car_info.get("mode")))

            message_location = "{\"location\": \"" + str(self.location) + "\", "
            message_time = "\"time left\": \"" + str(remaining_time) + "\"}"

            message = message_location + message_time
            response = self.communeWithCloud(message)
            response = json.loads(response)
            return response

    def publishPath(self, client: mqtt_client, station):
        if station:
            self.publish(client, self.CAR_PATH_TOPIC, station.getJson())
        else:
            self.publish(client, self.CAR_PATH_TOPIC, "{\"resultado\": \"posto não encontrado\"}")

    def communeWithCloud(self, message):
        self.cloud_socket.send(message.encode(self.FORMAT))
        response = self.cloud_socket.recv(1024)
        return response.decode(self.FORMAT)

    def publish(self, client: mqtt_client, topic, message):
        while True:
            result = client.publish(topic, message)
            # result: [0, 1]
            status = result[0]
            if status == 0:
                print(f"Enviando `{message}` para o tópico `{topic}`")
                break
            else:
                print(f"Falha ao enviar mensagem para o tópico {topic}")
                sleep(1)

    def main(self):
        pass
