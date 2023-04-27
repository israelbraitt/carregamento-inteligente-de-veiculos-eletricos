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
            mode (int): modo de uso do carro (1 -> economico, 2 -> regular, 3 -> sport, 4 -> recaregando)
            localization (str): localização atual do carro
            best_station (str): melhor posto de carregamento
            servers (list): endereço dos brokers dos servidores locais
            server_port (int): porta de conexão dos brokers dos servidores locais
            BATTERY_TOPIC (str): tópico MQTT para solicitar vaga em um posto
            PATH_TOPIC (str): tópico MQTT para enviar a localização atual do carro
            TEST_TOPIC (str):
            client_id (str): id do cliente
            tcp_host (str): endereço de acesso do sistema de informações do carro
            tcp_port (int): porta de acesso do socket TCP
            format (str): formato da codificação de caracteres
    """

    def __init__(self, location=randint(1, 2)):
        """
        Método construtor da classe
        """
        self.battery = 50
        self.mode = 2  # 1 = economico, 2 = regular, 3 = sport, 4 = recarregando
        self.location = location
        self.station = 0
        self.servers = {1: '172.16.103.1', 2: '172.16.103.3'}
        self.server_port = 1883

        self.BATTERY_TOPIC = "REDESP2IG/car/battery"
        self.PATH_TOPIC = "REDESP2IG/car/path"
        self.UPDATE_TOPIC = "REDESP2IG/station/traffic"
        self.TEST_TOPIC = "REDESP2IG/car/test"
        self.client_id = f'Carro {randint(0, 1000)}'

        self.tcp_host = socket.gethostbyname(socket.gethostname())
        self.tcp_port = 1159

        self.format = 'utf-8'

    def manageBattery(self, client: mqtt_client):
        """
        Gerencia a bateria do carro

            Parâmetros:
                client (mqtt_client): cliente MQTT
        """
        while True:
            print("Bateria: " + str(self.battery))
            if self.mode > 3:
                self.battery = min(100, self.battery + 5)
            else:
                self.battery = max(0, self.battery - self.mode * 2)
                if self.battery < 25:
                    p_id = "{\"car\": \"" + self.client_id + "\", "
                    p_location = "\"location\": \"" + str(self.location) + "\", "
                    p_mode = "\"mode\": \"" + str(self.mode) + "\", "
                    p_battery = "\"battery\": \"" + str(self.battery) + "\"}"
                    publication = p_id + p_location + p_mode + p_battery
                    print("==ENVIANDO MENSAGEM==")
                    print(publication)
                    self.publish(client, self.BATTERY_TOPIC, publication)
            sleep(2)

    def setLocation(self, client, current_location, station=0):
        """
        Altera a localização atual do carro
            Parâmetros:
                current_location (str): localização atual do carro
        """

        self.location = current_location
        self.station = station
        p_operation = "\"operation\": \"none\", "

        if station:
            self.mode = 4
            p_operation = "\"operation\": \"entrance\", "
        else:
            self.mode = 2
            p_operation = "\"operation\": \"exit\", "


        p_id = "{\"car\": \"" + self.client_id + "\", "
        p_location = "\"location\": \"" + str(self.location) + "\", "
        p_station = "\"station\": \"" + str(self.station) + "\", "
        p_battery = "\"battery\": \"" + str(self.battery) + "\"}"

        publication = p_id + p_location + p_station + p_operation + p_battery

        print("==ENVIANDO MENSAGEM==")
        print(publication)
        self.publish(client, self.UPDATE_TOPIC, publication)

    def setMode(self, car_mode):
        """
        Altera o modo de autonomia do carro
            Parâmetros:
                car_mode (int):  modo de autonomia
        """
        self.mode = car_mode

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
            client.subscribe(self.PATH_TOPIC)
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
        if self.location > 2:
            server_addr = self.servers.get(1)
        else:
            server_addr = self.servers.get(self.location)
        client.connect(server_addr, self.server_port)
        return client

    def on_message(self, client: mqtt_client, userdata, message):
        """
        Exibe as mensagens exibidas dos tópicos

            Parâmetros:
                client (mqtt_client): cliente MQTT
                userdata (): dados definidos pelo usuário
                message (str): mensagem recebida
        """
        print(f"Mensagem `{message.payload.decode(self.format)}` recebido do tópico `{message.topic}`")
        decoded = message.payload.decode(self.format)
        match decoded:
            case "REDESP2IG/car/path":
                if decoded.get("car"):
                    if decoded.get("car") == self.client_id:
                        print("Mensagem é pra este carro.")
                        self.best_station = int(decoded.get("code"))

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
                        response = self.assembleResponse("200", "OK", json.dumps("Nível da bateria: " + self.battery + "%"))
                        self.sendTCPMessage(client, response)
                        print("Nível da bateria do carro: " + self.battery)

                    # Retorna o modo de autonomia atual do carro
                    elif (data["url_content"] == "/modo"):
                        response = self.assembleResponse("200", "OK", json.dumps("Modo de autonomia: " + self.mode + "%"))
                        self.sendTCPMessage(client, response)
                        print("Modo de autonomia do carro: " + self.mode)

                elif (data["method"] == "POST"):
                    # Altera a localização atual do carro
                    if (data["url_content"] == "/mudar-localizacao"):

                        current_location = data["body_content"]["current_location"]
                        current_station = data["body_content"]["current_station"]

                        self.setLocation(client, current_location, current_station)
                        print("Localização alterada para: " + self.location)

                    # Altera o modo de autonomia do carro
                    elif (data["url_content"] == "/alterar-modo-carro"):
                        car_mode = data["body_content"]["car_mode"]
                        self.setMode(car_mode)
                        print("Modo alterado para: " + self.mode)

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
        # Socket com conexão TCP
        socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_thread = threading.Thread(target=self.conexaoTCP, args=[socket_tcp])
        tcp_thread.start()

        client_mqtt = self.connect_mqtt()

        # Thread para gerenciar a bateria do carro
        battery_thread = threading.Thread(target=self.manageBattery, args=[client_mqtt])
        battery_thread.start()

        client_mqtt.loop_forever()


carro_inst = Car()
carro_inst.main()
