from paho.mqtt import client as mqtt_client
from random import randint
from time import sleep
import json


class PowerStation:
    """
    Fornece funcionalidades de conexão e comunicação MQTT para divulgação
    das vagas de um posto de carregamento de carros elétricos
        Atributos:
            broker_addr (str): endereço do broker
            broker_port (int): porta de conexão do broker
            queue_update (str): tópico para atualização da fila do posto
            car_entrance (str): tópico para sinalizar entrada de um carro em um posto
            station_code (int): código do posto
            client_id (str): id do cliente
            location (int): código da localização do posto
            limite_vagas (int): limite de vagas no posto
            vagas_disp (int): quantidade de vagas disponíveis no posto
            format (str): formato da codificação de caracteres
    """

    def __init__(self, location=randint(1, 10)):
        """
        Método construtor da classe
        """
        self.BROKER_ADDR = '127.0.0.1'
        self.CENTRAL_ADDR = '127.0.0.1'
        self.BROKER_PORT = 1915
        self.CENTRAL_PORT = 1917

        self.REGISTER_TOPIC = "REDESP2IG/station/register"
        self.UPDATE_TOPIC = "REDESP2IG/station/queue"
        self.CAR_TOPIC = "REDESP2IG/station/traffic"
        self.TEST_TOPIC = "REDESP2IG/station/test"

        self.station_code = randint(1, 100)
        self.client_id = f'Station {self.station_code}'
        self.location = location

        self.limite_vagas = 25
        self.vagas_disp = 25

        self.format = 'utf-8'

    def on_connect(self, client: mqtt_client, userdata, flags, rc):
        """
        Retorna o status da conexão (callback) de acordo com a resposta do servidor
            Argumentos:
                client (mqtt_client): cliente MQTT
                rc (int): determina se o cliente está conectado com sucesso
        """
        if rc == 0:
            print("Connected to MQTT Broker!")
            client.subscribe(self.CAR_TOPIC)
            client.subscribe(self.TEST_TOPIC)
        else:
            print("Failed to connect, return code %d\n", rc)

    def connect_mqtt(self):
        """
        Conecta o cliente MQTT ao broker
        """
        client = mqtt_client.Client()
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.connect(self.BROKER_ADDR, self.BROKER_PORT)
        return client

    def on_message(self, client: mqtt_client, userdata, message):
        """
        Exibe as mensagens exibidas dos tópicos
            Argumentos:
                client (mqtt_client): cliente MQTT
                message (str): mensagem recebida
        """
        decoded = message.payload.decode(self.format)
        print("Message received on topic " + message.topic + " with QoS " + str(message.qos) + " and payload " + str(
            decoded))

        message_dict = json.loads(decoded)
        match message.topic:
            case "REDESP2IG/station/traffic":
                self.updateVagas(client, message_dict)

        return_message = self.messageTreatment(message.payload.decode("utf-8"))

    def subscribe(self, client: mqtt_client, topic):
        """
        Increve os cliente nos tópicos do broker

            Argumentos:
                client (mqtt_client): cliente MQTT
                topic (str): tópico do broker
        """
        client.subscribe(topic)
        client.on_message = self.on_message

    def register(self, client):
        pub_code = "{\"code\": \"" + str(self.station_code) + "\", "
        pub_queue = "\"queue\": \"" + str(self.limite_vagas - self.vagas_disp) + "\"}"
        publication = pub_code + pub_queue
        self.publish(client, self.REGISTER_TOPIC, publication)

    def updateVagas(self, client, payload):
        if payload.get("station") == self.client_id:
            if payload.get("operation") == "entrance":
                self.vagas_disp = max(0, self.vagas_disp - 1)
                self.publishVagas(client)
            elif payload.get("operation") == "exit":
                self.vagas_disp = min(self.limite_vagas, self.vagas_disp + 1)
                self.publishVagas(client)

    def publishVagas(self, client: mqtt_client):
        """
        Publica as vagas disponíveis no posto
            Argumentos:
                client (mqtt_client): cliente MQTT
        """
        pub_code = "{\"station\": \"" + str(self.station_code) + "\","
        pub_location = "\"district\": \"" + str(self.location) + "\","
        pub_queue = "\"queue\": \"" + str(self.limite_vagas - self.vagas_disp) + "\"}"
        publication = pub_code + pub_location + pub_queue
        self.publish(client, self.UPDATE_TOPIC, publication)

    def publish(self, client: mqtt_client, topic, message):
        """
        Publica mensagens nos tópicos do broker
            Argumentos:
                client (mqtt_client): cliente MQTT
                topic (str): tópico do broker
                message (str): mensagem a ser publicada
        """
        while True:
            result = client.publish(topic, message)
            # result: [0, 1]
            status = result[0]
            if status == 0:
                print(f"Enviou `{message}` para o tópico `{topic}`")
                break
            else:
                print(f"Falha ao enviar mensagem para o tópico {topic}")
                sleep(1)

    def messageTreatment(self, payload):
        if (payload == ""):
            pass

    def main(self):
        client = self.connect_mqtt()
        self.register(client)
        client.loop_forever()


post_inst = PowerStation(1)
post_inst.main()