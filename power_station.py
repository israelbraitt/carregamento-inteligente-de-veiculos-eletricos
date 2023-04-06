from paho.mqtt import client as mqtt_client
from random import randint
from time import sleep


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
        self.broker_addr = 'broker.emqx.io'
        self.broker_port = 4000
        self.mqtt_topic = "python/mqtt"
        self.client_id = f'power-station-mqtt-{randint(0, 1000)}'

        self.limite_vagas = 25
        self.vagas_disp = 25

    def addVagas(self, operacao):
        """
        Adiciona uma vaga da quantidade de vagas disponíveis

            Parâmetros:
                operacao (int): se for 1 incrementa a quantidade de vagas em 1 unidade,
                                se for 2 decrementa a quantidade de vagas em 1 unidade
        """
        if (operacao == 1):
            if (self.vagas_disp < self.limite_vagas):
                self.vagas_disp += 1
        elif (operacao == 2):
            if (self.vagas_disp > 0):
                self.vagas_disp -= 1
            else:
                print("O posto não possui mais vagas disponíveis")

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
        client.on_connect = self.on_connect
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
        client.on_message = self.on_message

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


post_inst = PowerStation()
post_inst.main()
