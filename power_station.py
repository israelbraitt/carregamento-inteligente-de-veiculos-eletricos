from paho.mqtt import client as mqtt_client
from random import randint
from time import sleep
import json

class PowerStation:
    """
    Fornece funcionalidades de conexão e comunicação MQTT para divulgação
    das vagas de um posto de carregamento de carros elétricos

        Atributos:
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
        self.client_id = f'station-mqtt-{randint(0, 1000)}'

        self.limite_vagas = 25
        self.vagas_disp = 25

    def on_connect(self, client: mqtt_client, userdata, flags, rc):
        """
        Retorna o status da conexão (callback) de acordo com a resposta do servidor

            Parâmetros:
                client (mqtt_client): cliente MQTT
                userdata ():
                flags ():
                rc (int): determina se o cliente está conectado com sucesso
        """
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
            # Renova a assinatura caso a conexão tenha sido perdida
            client.subscribe(self.queue_update)
            client.subscribe(self.car_entrance)

    def connect_mqtt(self):
        """
        Conecta o cliente MQTT ao broker
        """
        # Define id do cliente conectado
        client = mqtt_client.Client()
        client.on_connect = self.on_connect
        client.connect(self.broker_addr, self.broker_port)
        return client

    def on_message(self, client: mqtt_client, userdata, message):
        """
        Recebe e trata as mensagens dos tópicos

            Parâmetros:
                client (mqtt_client): cliente MQTT
                userdata ():
                message (str): mensagem recebida
        """
        print(f"Mensagem " + {message.payload.decode("utf-8")} + " recebido do tópico " + {message.topic})

        message_dict = json.load(message.payload)
        # Atualiza as vagas do posto de carregamento
        match message.topic:
            case "REDESP2IG/station/traffic":
                self.updateVagas(message_dict)

        return_message = self.messageTreatment(message.payload.decode("utf-8"))

    def subscribe(self, client: mqtt_client, topic):
        """
        Increve os cliente nos tópicos do broker

            Parâmetros:
                client (mqtt_client): cliente MQTT
                topic (str): tópico do broker
        """
        client.subscribe(self.queue_update)
        client.subscribe(self.car_entrance)
        client.on_message = self.on_message

    def updateVagas(self, payload):
        if payload.get("station") == self.client_id:
            if payload.get("operation") == "entrance":
                self.vagas_disp = max(0, self.vagas_disp - 1)
            elif payload.get("operation") == "exit":
                self.vagas_disp = min(self.limite_vagas, self.vagas_disp + 1)

    def publishVagas(self, client: mqtt_client):
        publication = "{\"station\": \"" + self.client_id + "\", \"queue\": \"" + str(self.vagas_disp) + "\"}"
        publication = json.dumps(publication)

        self.publish(client, self.queue_update, publication)
        
    def publish(self, client: mqtt_client, topic, message):
        """
        Publica mensagens nos tópicos do broker

            Parâmetros:
                client (mqtt_client): cliente MQTT
                topic (str): tópico do broker
                message (str): mensagem a ser publicada
        """
        while True:
            sleep(1)
            result = client.publish(topic, message)
            # result: [0, 1]
            status = result[0]
            if status == 0:
                print(f"Enviando `{message}` para o tópico `{topic}`")
            else:
                print(f"Falha ao enviar mensagem para o tópico {topic}")

    def messageTreatment(self, payload):
        if (payload == ""):
            pass

    def main(self):
        client_mqtt = self.connect_mqtt()
        print(type(client_mqtt))

        client_mqtt.loop_forever()


post_inst = PowerStation()
post_inst.main()
