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

        Argumentos:
            broker (str): endereço do broker
            mqtt_port (int): porta de conexão do broker
            topic (str): tópico envio/recebimento de mensagens no broker
            client_id (str): id do cliente
            tcp_host (str): endereço de acesso do sistema de informações do carro
            tcp_port (int): porta de acesso do socket TCP
    """

    def __init__(self):
        self.battery = 100
        self.mode = 2

        self.broker_addr = 'broker.emqx.io'
        self.broker_port = 4000
        self.nearby_power_stations_topic = "python/mqtt"
        self.client_id = f'car-mqtt-{randint(0, 1000)}'

        self.tcp_host = '127.0.0.1'
        self.tcp_port = 50000

    def setModes(self, mode):
        """
        Altera o modo de uso, que define a autonomia do carro

            Argumentos:
                mode (str): modo de uso do carro
        """
        if (mode == "eco"):
            self.mode = 1
        elif (mode == "standard"):
            self.mode = 2
        elif (mode == "sport"):
            self.mode = 3

    def decreaseBattery(self):
        """
        Decrementa a bateria de acordo com o modo de uso do carro

        """
        while True:
            if self.battery != 0:
                self.battery -= self.mode*2
                sleep(2)
                print("Bateria: ", self.battery)
    
    def batteryAlert(self, client):
        """
        Emite um alerta de recarga para os postos próximos

            Argumentos:
                client (): client MQTT
        """
        message = str("O carro " + self.client_id + " precisa de recarga.")
        while True:
            if (self.battery <= 30):
                self.publish(client, self.nearby_power_stations_topic, message)

    def recharge(self):
        """
        Recarrega a bateria do carro
        """
        while(True):
            if self.battery != 100:
                self.battery += 1
                sleep(1)
            else:
                print("Bateria completamente carregada")

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
        client.on_connect = self.on_connect
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

    def conexaoTCP(self, socket_tcp):
        """
        Faz conexão com clientes TCP e executa uma thread para receber as mensagens

            Parâmetros:
                socket_tcp (socket): socket para conexão TCP
        """
        while True:
            # Aceita a conexão com os sockets dos clientes
            conn_client_tcp, addr_client_tcp = socket_tcp.accept()
            print("Conectado com um cliente TCP em: ", addr_client_tcp)
            self.clients.append(conn_client_tcp)
            
            # Recebe mensagens dos clientes através da conexão TCP
            thread_tcp = threading.Thread(target=self.tratarRequests, args=[conn_client_tcp])
            thread_tcp.start()

    def tratarRequests(self, client):
        """
        Faz o tratamento dos "requests" dos clientes

            Parâmetros:
                client (socket): cliente conectado
            
            Retornos:

        """
        while True:
            try:
                message = client.recv(self.BUFFER_SIZE)
                data = self.getMessageData(message.decode('utf-8'))
                print("Mensagem recebida:", message)
                
                if (data["method"] == "GET"):
                    if (data["url_content"] == "/nivel-bateria"):
                        username = data["body_content"]["current_localization"]
                        
                        response = self.assembleResponse("200", "OK", json.dumps("Nível da bateria: " + self.battery + "%"))
                        self.sendMessage(client, response)

                elif (data["method"] == "POST"):
                    if (data["url_content"] == "/alterar-localizacao"):
                        current_localization = data["body_content"]["current_localization"]
                    
                    elif (data["url_content"] == "/entrar-no-posto"):
                        id_power_station = data["body_content"]["id_power_station"]

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
            mensagem = mensagem.replace("{","{dir") 
            mensagem = mensagem.replace("}","esq}")
            mensagem = mensagem.split("{")[1].split("}")[0]
            mensagem = mensagem.replace("dir","{")
            mensagem = mensagem.replace("esq","}")

            body_content = json.loads(mensagem)

        except:
            body_content = "{}"

        return {
            "method": method,
            "url_content": url_content,
            "body_content": body_content
    }

    def sendMessage(self, client, message):
        """
        Envia mensagens para o usuário do carro através da conexão TCP

            Parâmetros:
                mensagem (str): mensagem a ser enviada ("response")
                client (socket): cliente conectado
            
            Retornos:

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

        response = "{0} {1} {2}\nHOST: {3}\nUser-Agent: {4}\nContent-Type: {5}\nContent-Length: {6}\n\n{7}" .format(http_version, 
                                                                                                                    status_code, 
                                                                                                                    status_message, 
                                                                                                                    HOST, 
                                                                                                                    user_agent, 
                                                                                                                    content_type, 
                                                                                                                    content_length,
                                                                                                                    body)
        
        return response

    def main(self):
        # Conecta o clietne MQTT com algum broker
        client_mqtt = self.connect_mqtt()
        client_mqtt.loop_forever()
        
        # Cria um socket com conexão TCP
        socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            # Fornece o endereço e as portas para "escutar" as conexões
            # com os sockets dos clientes
            socket_tcp.bind((self.HOST, self.TCP_PORT))
            socket_tcp.listen()
        except:
            return print("Não foi possível iniciar o sistema de informações")

        self.publish(client_mqtt, self.nearby_power_stations_topic, "oi")

        # Decrementa a bateria do carro de acordo com o modo e uso
        thread1 = threading.Thread(target=self.decreaseBattery)
        thread1.start()

        # Emite um alerta para os postos próximos caso o nível da bateria esteja baixo
        thread2 = threading.Thread(target=self.batteryAlert(client_mqtt))
        thread2.start()


carro_inst = Car()
carro_inst.main()
