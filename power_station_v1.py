from paho.mqtt import client as mqtt_client
from random import randint
from time import sleep
import json


class PowerStation:
    """
    Fornece funcionalidades de conexão e comunicação MQTT para divulgação
    das vagas de um posto de carregamento de carros elétricos
        Argumentos:
            broker (str): endereço do broker
            port (int): porta de conexão do broker
            topic1 (str): tópico envio/recebimento de mensagens no broker
            client_id (str): id do cliente
            limite_vagas (int): limite de vagas no posto
            vagas_disp (int): quantidade de vagas disponíveis no posto
    """

    def __init__(self):
        self.broker_addr = '127.0.0.1'
        self.broker_port = 1915
        self.queue_update = "REDESP2IG/station/queue"
        self.car_entrance = "REDESP2IG/station/traffic"
        self.test_channel = "REDESP2IG/station/test"

        self.client_id = f'Station {randint(1, 100)}'
        self.location = f'District {randint(1, 20)}'

        self.limite_vagas = 25
        self.vagas_disp = 25


    def on_connect(self, client, userdata, flags, rc):
        """
        Retorna o status da conexão (callback) de acordo com a resposta do servidor
            Argumentos:
                client (): cliente MQTT
                userdata ():
                flags ():
                rc (): determina se o cliente está conectado com sucesso
        """
        if rc == 0:
            print("Connected to MQTT Broker!")
            client.subscribe(self.queue_update)
            client.subscribe(self.car_entrance)
            client.subscribe(self.test_channel)
        else:
            print("Failed to connect, return code %d\n", rc)
            # Renova a assinatura caso a conexão tenha sido perdida

    def connect_mqtt(self):
        """
        Conecta o cliente MQTT ao broker
        """
        # Define id do cliente conectado
        client = mqtt_client.Client()
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.connect(self.broker_addr, self.broker_port)
        return client

    def on_message(self, client, userdata, message):
        """
        Exibe as mensagens exibidas dos tópicos
            Argumentos:
                client (): cliente MQTT
                userdata ():
                message (str): mensagem recebida
        """
        print("Message received on topic "+message.topic+" with QoS "+str(message.qos)+" and payload "+str(message.payload))

        message_dict = json.load(message.payload)
        match message.topic:
            case "REDESP2IG/station/traffic":
                self.updateVagas(client, message_dict)

        return_message = self.messageTreatment(message.payload.decode("utf-8"))

    def subscribe(self, client: mqtt_client, topic):
        """
        Increve os cliente nos tópicos do broker
            Argumentos:
                client (): cliente MQTT
                topic (str): tópico do broker
        """
        client.subscribe(topic)
        client.on_message = self.on_message

    def updateVagas(self, client, payload):
        if payload.get("station") == self.client_id:
            if payload.get("operation") == "entrance":
                self.vagas_disp = max(0, self.vagas_disp - 1)
                self.publishVagas(client)
            elif payload.get("operation") == "exit":
                self.vagas_disp = min(self.limite_vagas, self.vagas_disp + 1)
                self.publishVagas(client)

    def publishVagas(self, client):
        publication = "{\"station\": \"" + self.client_id + "\", \"queue\": \"" + str(self.vagas_disp) + "\"}"
        self.publish(client, self.queue_update, publication)

    def publish(self, client, topic, message):
        """
        Publica mensagens nos tópicos do broker
            Argumentos:
                client (): cliente MQTT
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

    def messageTreatment(self, payload):
        if (payload == ""):
            pass

    def main(self):
        client = self.connect_mqtt()

        self.publish(client, self.test_channel, "oi")
        client.loop_forever()

post_inst = PowerStation()
post_inst.main()
