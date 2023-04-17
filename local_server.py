from paho.mqtt import client as mqtt_client
from random import randint
from time import sleep
import threading
import socket
import json
from station import Station

class LocalServer:
    """
    Servidor que processa as requisições de carregamento dos carros e solicitações
    de vagas nos postos em determinada localidade

        Atributos:
            broker_addr (str): endereço do broker
            broker_port (str): porta de conexão do broker
            car_battery_topic (str): tópico para indicar o nível de bateria baixa dos carros
            station_topic (str): tópico para atualização das filas dos postos
            car_path_topic (str): tópico para indicar a localização dos carros

            cloud_host (str): endereço de conexão do socket TCP do servidor central
            cloud_port (int): porta de conexão do socket TCP do servidor central
            cloud_socket (socket): inicialização do socket TCP para comunicação com o servidor central

            location (str): localização ao qual o servidor processa as requisições
            station_list (list): lista de postos da localidade

            format (str): formato da codificação de caracteres
    """
    def __init__(self, location):
        """
        Método construtor da classe

            Argumentos:
                location (str): localização do posto
        """
        self.broker_addr = "127.0.0.1"
        self.broker_port = 1915
        self.car_battery_topic = "REDESP2IG/car/battery"
        self.station_topic = "REDESP2IG/station/queue"
        self.car_path_topic = "REDESP2IG/car/path"

        self.cloud_host = "192.168.1.6"
        self.cloud_port = 1917
        self.cloud_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.location = location
        self.station_list = []

        self.format = 'utf-8'

    def on_connect(self, client: mqtt_client, userdata, flags, rc):
        """
        Retorna o status da conexão (callback) de acordo com a resposta do servidor

            Argumentos:
                client (mqtt_client): cliente MQTT
                userdata (): dados definidos pelo usuário
                flags (): especifica o comportamento da conexão MQTT
                rc (int): determina se o cliente está conectado com sucesso
        """
        if rc == 0:
            print("Connected to MQTT Broker!")
            client.subscribe(self.car_battery_topic)
            client.subscribe(self.station_topic)
        else:
            print("Failed to connect, return code %d\n", rc)

    def on_message(self, client: mqtt_client, message):
        """
        Exibe as mensagens exibidas dos tópicos
            Argumentos:
                client (mqtt_client): cliente MQTT
                message (str): mensagem recebida
        """
        decoded = message.payload.decode(self.FORMAT)
        print("Message received on topic "+message.topic+" with QoS "+str(message.qos)+" and payload " + str(decoded))

        match message.topic:
            case "REDESP2IG/car/battery":
                print("sneed")
            case "REDESP2IG/station/queue":
                print("chuck")

    def tcpStart(self):
        """
        Inicializa o socket TCP
        """
        self.cloud_socket.connect((self.cloud_host, self.cloud_port))
        print("Connected to cloud.")

    def mqttStart(self):
        """
        Inicializa o cliente MQTT
        """
        client = mqtt_client.Client()
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.connect(self.broker_addr, self.broker_port)
        return client

    def getPath(self, car_info):
        """
        Determina o melhor posto da localidade para o carro recarregar a bateria

            Argumentos:
                car_info (): informações do carro (bateria e modo de autonomia)
        """
        best_queue = 25
        best_station = None
        
        for station in self.station_list:
            if station.queue < best_queue:
                best_station = station
        
        if best_station:
            return best_station
        else:
            # calcula o tempo restante da bateria
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
        """
        Envia dados sobre a localização e o tempo de bateria restante para o servidor central

            Argumentos:
                message (str): mensagem a ser enviada para o servidor central
        """
        self.cloud_socket.send(message.encode(self.FORMAT))
        response = self.cloud_socket.recv(1024)
        return response.decode(self.FORMAT)

    def publish(self, client: mqtt_client, payload):
        pass

    def main(self):
        pass
