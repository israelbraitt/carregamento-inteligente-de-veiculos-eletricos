from paho.mqtt import client as mqtt_client
from random import randint
from time import sleep
import threading
import socket
import json


class Car:
    """
    Fornece funcionalidades de conexão e comunicação MQTT para um carro elétrico
    encontrar postos de carregamento
        Atributos:
            battery (int): nível da bateria do carro
            mode (int): modo de uso do carro (1 -> eco, 2 -> standard, 3 -> sport)
            current_localization (str): localização atual do carro
            broker_addr (str): endereço do broker
            broker_port (int): porta de conexão do broker
            car_battery_topic (str): tópico MQTT para solicitar vaga em um posto
            car_path_topic (str): tópico MQTT para enviar a localização atual do carro
            client_id (str): id do cliente
            tcp_host (str): endereço de acesso do sistema de informações do carro
            tcp_port (int): porta de acesso do socket TCP
    """

    def __init__(self):
        self.battery = 100
        self.mode = randint(1, 3) # 1 = economico, 2 = regular, 3 = sport, 4 = recarregando
        self.location = randint(1, 20)
        self.str_format = 'utf-8'
        self.broker_addr = '127.0.0.1'
        self.broker_port = 1915
        self.car_battery_topic = "REDESP2IG/car/battery"
        self.car_path_topic = "REDESP2IG/car/path"
        self.test_channel = "REDESP2IG/car/test"
        self.client_id = f'Carro {randint(0, 1000)}'

        self.tcp_host = '127.0.0.1'
        self.tcp_port = 1159

    def manageBattery(self, client):
        """
        Decrementa a bateria de acordo com o modo de uso do carro
        """
        while True:
            print("Bateria: " + str(self.battery))
            if self.mode > 3:
                self.battery = min(100, self.battery + 5)
            else:
                self.battery = max(0, self.battery - self.mode * 2)
                if self.battery < 40:
                    p_id = "{\"car\": \"" + self.client_id + "\", "
                    p_location = "\"location\": \"" + str(self.location) + "\", "
                    p_battery = "\"battery\": \"" + str(self.battery) + "\"}"
                    publication = p_id + p_location + p_battery
                    print("==ENVIANDO MENSAGEM==")
                    print(publication)
                    self.publish(client, self.car_battery_topic, publication)
            sleep(2)

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
            client.subscribe(self.car_path_topic)
            client.subscribe(self.car_battery_topic)
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

    def on_message(self, client: mqtt_client, userdata, message):
        """
        Exibe as mensagens exibidas dos tópicos
            Parâmetros:
                client (mqtt_client): cliente MQTT
                userdata ():
                message (str): mensagem recebida
        """
        print(f"Mensagem `{message.payload.decode(self.str_format)}` recebido do tópico `{message.topic}`")

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
                sleep(1)
                print(f"Falha ao enviar mensagem para o tópico {topic}")

    def conexaoTCP(self, socket_tcp):
        """
        Faz conexão com clientes TCP e executa uma thread para receber as mensagens
            Parâmetros:
                socket_tcp (socket): socket para conexão TCP
        """

        try:
            # Fornece o endereço e as portas para "escutar" as conexões
            # com os sockets dos clientes
            socket_tcp.bind((self.tcp_host, self.tcp_port))
            socket_tcp.listen()
        except:
            return print("Não foi possível iniciar o sistema de informações")

        while True:
            # Aceita a conexão com os sockets dos clientes
            conn_client_tcp, addr_client_tcp = socket_tcp.accept()
            print("Conectado com um cliente TCP em: ", addr_client_tcp)

            # Recebe mensagens dos clientes através da conexão TCP
            thread_tcp = threading.Thread(target=self.tratarRequests, args=[conn_client_tcp])
            thread_tcp.start()

    def tratarRequests(self, client):
        """
        Faz o tratamento dos "requests" dos clientes
            Parâmetros:
                client (socket): cliente conectado
        """
        while True:
            try:
                message = client.recv(1024)
                data = self.getMessageData(message.decode('utf-8'))
                print("Mensagem recebida:", message)

                if (data["method"] == "GET"):
                    # Retorna o nível de bateria do carro
                    if (data["url_content"] == "/nivel-bateria"):
                        response = self.assembleResponse("200", "OK",
                                                         json.dumps("Nível da bateria: " + self.battery + "%"))
                        self.sendTCPMessage(client, response)

                elif (data["method"] == "POST"):
                    # Altera a localização atual do carro
                    if (data["url_content"] == "/enviar-localizacao"):
                        current_localization = data["body_content"]["current_localization"]

                        self.setLocalization(current_localization)

                    # Altera o modo de autonomia do carro
                    elif (data["url_content"] == "/alterar-modo-carro"):
                        car_mode = data["body_content"]["car_mode"]

                        self.setModes(car_mode)

                elif (data["method"] == "PUT"):
                    pass

            except:
                break

    def getMessageData(self, mensagem):
        """
        Obtém os dados de uma "request"
            Parâmetros:
                mensagem (str): mensagem recebida de um cliente ("request")

            Retornos:
                um dicionário com o "method", o "url_content" e o "body_content" da "request"
        """
        method = mensagem.split(" ")[0]
        url_content = mensagem.split(" ")[1]

        try:
            # Prepara as mensagens no padrão JSON
            mensagem = mensagem.replace("{", "{dir")
            mensagem = mensagem.replace("}", "esq}")
            mensagem = mensagem.split("{")[1].split("}")[0]
            mensagem = mensagem.replace("dir", "{")
            mensagem = mensagem.replace("esq", "}")

            body_content = json.loads(mensagem)

        except:
            body_content = "{}"

        return {
            "method": method,
            "url_content": url_content,
            "body_content": body_content
        }

    def sendTCPMessage(self, client, message):
        """
        Envia mensagens para o usuário do carro através da conexão TCP
            Parâmetros:
                mensagem (str): mensagem a ser enviada ("response")
                client (socket): cliente conectado
        """
        try:
            client.send(message.encode('utf-8'))
        except:
            pass

    def assembleResponse(self, status_code, status_message, body):
        """
        Monta a "response" a ser enviada
            Parâmetros:
                status_code (str): código de status da resposta HTTP do servidor
                status_message (str): mensagem de status da resposta do servidor
                body (str): corpo da mensagem de retorno

            Retornos:
                response (str): resposta HTTP do servidor
        """
        http_version = "HTTP/1.1"
        HOST = "127.0.0.1:50000"
        user_agent = "server-conces-energia"
        content_type = "text/html"
        content_length = len(body)

        response = "{0} {1} {2}\nHOST: {3}\nUser-Agent: {4}\nContent-Type: {5}\nContent-Length: {6}\n\n{7}".format(
            http_version,
            status_code,
            status_message,
            HOST,
            user_agent,
            content_type,
            content_length,
            body)

        return response

    def main(self):
        # Cria um socket com conexão TCP
        socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_thread = threading.Thread(target=self.conexaoTCP, args=[socket_tcp])
        tcp_thread.start()

        client_mqtt = self.connect_mqtt()

        battery_thread = threading.Thread(target=self.manageBattery, args=[client_mqtt])
        battery_thread.start()

        client_mqtt.loop_forever()

carro_inst = Car()
carro_inst.main()
