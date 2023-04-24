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
            broker_port (int): porta de conexão do broker
            cloud_host (str): endereço de conexão do socket TCP do servidor central
            cloud_port (int): porta de conexão do socket TCP do servidor central
            CAR_BATTERY_TOPIC (str): tópico para indicar o nível de bateria baixa dos carros
            STATION_UPDATE_TOPIC (str): tópico para atualização das filas dos postos
            STATION_REGISTER_TOPIC (str): tópico de registro da estação no servidor local
            CAR_PATH_TOPIC (str): tópico para indicar a localização dos carros
            location (str): localização ao qual o servidor processa as requisições
            cloud_socket (socket): inicialização do socket TCP para comunicação com o servidor central
            station_dict (dict): lista de postos da localidade
            format (str): formato da codificação de caracteres
    """

    def __init__(self, location):
        """
        Método construtor da classe

            Parâmetros:
                location (str): localização do posto
        """
        self.broker_addr = "127.0.0.1"
        self.broker_port = 1915

        self.cloud_host = "192.168.1.3"
        self.cloud_port = 1917

        self.CAR_BATTERY_TOPIC = "REDESP2IG/car/battery"
        self.STATION_UPDATE_TOPIC = "REDESP2IG/station/queue"
        self.STATION_REGISTER_TOPIC = "REDESP2IG/station/register"
        self.CAR_PATH_TOPIC = "REDESP2IG/car/path"

        self.location = location
        self.station_dict = {}
        self.cloud_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.format = 'utf-8'

    def on_connect(self, client: mqtt_client, userdata, flags, rc):
        """
        Retorna o status da conexão (callback) de acordo com a resposta do servidor

            Parâmetros:
                client (mqtt_client): cliente MQTT
                userdata (): dados definidos pelo usuário
                flags (): especifica o comportamento da conexão MQTT
                rc (int): determina se o cliente está conectado com sucesso
        """
        if rc == 0:
            print("Connected to MQTT Broker!")
            client.subscribe(self.CAR_BATTERY_TOPIC)
            client.subscribe(self.STATION_UPDATE_TOPIC)
            client.subscribe(self.STATION_REGISTER_TOPIC)
        else:
            print("Failed to connect, return code %d\n", rc)

    def on_message(self, client: mqtt_client, userdata, message):
        """
        Exibe as mensagens exibidas dos tópicos

            Parâmetros:
                client (mqtt_client): cliente MQTT
                message (str): mensagem recebida
        """
        decoded = message.payload.decode(self.format)
        print("Message received on topic " + message.topic + " with QoS " + str(message.qos) + " and payload " + str(
            decoded))

        match message.topic:
            case "REDESP2IG/car/battery":
                path = self.getPath(decoded)
                self.publishPath(client, path)
            case "REDESP2IG/station/queue":
                self.updateQueue(decoded)
            case "REDESP2IG/station/register":
                self.registerStation(decoded)

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

    def updateQueue(self, station_info):
        """
        Atualiza a fila de um posto de carregamento

            Parâmetros:
                station_info (dict): informações de um posto de carregamento
        """
        print(self.station_dict)
        station_info = json.loads(station_info)
        station_find = self.station_dict.get(station_info.get("code"))
        if station_find:
            station_find.queue = station_info.get("queue")
        self.communeWithCloud(station_find.getJson())
        print(self.station_dict)

    def registerStation(self, station_info):
        """
        Registra o posto de carregamento no servidor central

            Parâmetros:
                station_info (dict): informações de um posto de carregamento
        """
        print(self.station_dict)
        station_info = json.loads(station_info)
        new_station = Station(self.location, station_info.get("code"), station_info.get("queue"))
        self.station_dict[station_info.get("code")] = new_station
        self.communeWithCloud(new_station.getJson())
        print(self.station_dict)

    def getPath(self, car_info):
        """
        Determina o melhor posto da localidade para o carro recarregar a bateria

            Parâmetros:
                car_info (): informações do carro (bateria e modo de autonomia)
        """
        best_queue = 25
        best_station = None
        for station in self.station_dict.values():
            if int(station.queue) < best_queue:
                best_station = station
                best_queue = int(station.queue)
        if best_station:
            print(best_station)
            return best_station.getJson()
        else:
            car_info = json.loads(car_info)

            remaining_time = int(car_info.get("battery")) // max(1, int(car_info.get("mode")))

            message_location = "{\"location\": \"" + self.location + "\", "
            message_battery = "\"battery\": \"" + car_info.get("battery") + "\", "
            message_mode = "\"mode\": \"" + car_info.get("mode") + "\", "
            message_time = "\"time left\": \"" + str(remaining_time) + "\"}"

            message = message_location + message_battery + message_mode + message_time
            response = self.communeWithCloud(message)
            response = json.loads(response)
            return response

    def publishPath(self, client: mqtt_client, station_info):
        if station_info:
            self.publish(client, self.CAR_PATH_TOPIC, station_info)
        else:
            self.publish(client, self.CAR_PATH_TOPIC, "{\"result\": \"posto não encontrado\"}")

    def communeWithCloud(self, message):
        """
        Envia dados sobre a localização e o tempo de bateria restante para o servidor central

            Parâmetros:
                message (str): mensagem a ser enviada para o servidor central
        """
        self.cloud_socket.send(message.encode(self.format))
        response = self.cloud_socket.recv(1024)
        response = response.decode(self.format)
        response = str(response)
        print(response)
        return response

    def publish(self, client: mqtt_client, topic, message):
        """
        Publica mensagens nos tópicos do broker
        
            Parâmetros:
                client (mqtt_client): cliente MQTT
                topic (str): tópico do broker
                message (str): mensagem a ser publicada
        """
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
        self.tcpStart()
        broker = self.mqttStart()
        broker.loop_forever()


server = LocalServer(1)
server.main()
