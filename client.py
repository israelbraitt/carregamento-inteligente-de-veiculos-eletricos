from paho.mqtt import client as mqtt_client
from random import randint
from time import sleep

class client:
    """
    Fornece funcionalidades de conexão e comunicação MQTT

        Argumentos:
            broker (str): endereço do broker
            port (int): porta de conexão do broker
            topic1 (str): tópico envio/recebimento de mensagens no broker
            client_id (str): id do cliente
            username (str): nome de usuário
            password (str): senha para conexão
    """
    def __init__(self):
        self.broker = 'broker.emqx.io'
        self.port = 1883
        self.topic1 = "python/mqtt"
        self.client_id = f'mqtt-{randint(0, 1000)}'
        self.username = 'emqx'
        self.password = 'public'
    
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
        else:
            print("Failed to connect, return code %d\n", rc)
            # Renova a assinatura caso a conexão tenha sido perdida
            client.subscribe("$SYS/#")

    def connect_mqtt(self):
        """
        Conecta o cliente MQTT ao broker
        """
        # Define id do cliente conectado
        client = mqtt_client.Client()
        client.username_pw_set(self.username, self.password)
        client.on_connect = self.on_connect()
        client.connect(self.broker, self.port)
        return client
    
    def on_message(self, client, userdata, message):
        """
        Exibe as mensagens exibidas dos tópicos

            Argumentos:
                client (): cliente MQTT
                userdata ():
                message (str): mensagem recebida
        """
        print(f"Mensagem `{message.payload.decode()}` recebido do tópico `{message.topic}`")
    
    def subscribe(self, client: mqtt_client, topic):
        """
        Increve os cliente nos tópicos do broker

            Argumentos:
                client (): cliente MQTT
                topic (str): tópico do broker
        """
        client.subscribe(topic)
        client.on_message = self.on_message()

    def publish(self, client, topic, message):
        """
        Publica mensagens nos tópicos do broker
            
            Argumentos:
                client (): cliente MQTT
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
    
    def main(self):
        client = self.connect_mqtt()

        client.loop_forever()
        self.publish(client, self.topic1, "oi")

client_inst = client()
client.main()