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
        self.broker_addr = 'broker.emqx.io'
        self.broker_port = 4000
        self.mqtt_topic = "python/mqtt"
        self.client_id = f'car-mqtt-{randint(0, 1000)}'

        self.tcp_host = '127.0.0.1'
        self.tcp_port = 50000

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
                mensagem = client.recv(self.BUFFER_SIZE)
                dados = self.obterDadosMensagem(mensagem.decode('utf-8'))
                print("Mensagem recebida:", mensagem)
                
                if (dados["method"] == "GET"):
                    pass

                elif (dados["method"] == "POST"):
                    if (dados["url_content"] == "/validacao-usuario"):
                        username = dados["body_content"]["username"]
                        matricula = dados["body_content"]["matricula"]
                        
                        # Consulta se o cliente está registrado na base de dados
                        dao_inst = DAO()
                        validacao_client = dao_inst.getClient(username, matricula)

                        if (validacao_client == True):
                            request = self.montarResponse("200", "OK", json.dumps("Usuário cadastrado"))
                            self.enviarMensagem(client, request)

                        elif (validacao_client == False):
                            request = self.montarResponse("404", "Not Found", json.dumps("Usuário não cadastrado"))
                            self.enviarMensagem(client, request)
                            self.detelarClient(client)
                    
                    elif (dados["url_content"] == "/medicoes/ultima-medicao"):
                        matricula = dados["body_content"]["matricula"]

                        # Consulta a última medição associada a determinado número de matrícula
                        dao_inst = DAO()
                        ultima_medicao = dao_inst.getUltimaMedicao(matricula)

                        if (ultima_medicao != (0, 0)):
                            # Retorna a data, a hora e o consumo registrado na última medição
                            data_hora = ultima_medicao[0]
                            consumo = ultima_medicao[1]
                            dic_ultima_medicao = { "data_hora" : data_hora, "consumo" : consumo}
                            
                            request = self.montarResponse("200", "OK", json.dumps(dic_ultima_medicao))
                            self.enviarMensagem(client, request)
                        else:
                            request = self.montarResponse("404", "Not Found", json.dumps(""))
                            self.enviarMensagem(client, request)

                    elif (dados["url_content"] == "/gerar-fatura"):
                        matricula = dados["body_content"]["matricula"]

                        # Consulta as 2 últimas medições associadas a determinado número de matrícula
                        dao_inst = DAO()
                        ultimas_2_medicoes = dao_inst.get2UltimasMedicoes(matricula)
                        
                        if (ultimas_2_medicoes[0] != ('0', '0') and ultimas_2_medicoes[1] != ('0', '0')):
                            data, consumo_final= ultimas_2_medicoes[0]
                            data, consumo_inicial = ultimas_2_medicoes[1]
                            consumo_total = int(consumo_final) - int(consumo_inicial)
                            
                            # Multiplica o total de consumo do último período registrado
                            # pelo valor da taxa de consumo
                            valor_pagamento = consumo_total * self.TAXA_CONSUMO
                            
                            dic_fatura = { "consumo" : consumo_total , "valor_pagamento" : valor_pagamento}
                            
                            request = self.montarResponse("200", "OK", json.dumps(dic_fatura))
                            self.enviarMensagem(client, request)
                        else:
                            request = self.montarResponse("404", "Not Found", json.dumps(""))
                            self.enviarMensagem(client, request)

                    elif (dados["url_content"] == "/alerta-consumo"):
                        matricula = dados["body_content"]["matricula"]
                        
                        # Consulta as 5 últimas medições associadas a determinado número de matrícula
                        dao_inst = DAO()
                        ultimas_5_medicoes = dao_inst.get5UltimasMedicoes(matricula)
                        
                        if (ultimas_5_medicoes):
                            lista_variacao_consumo = []
                            
                            i = 4
                            while i > 0:
                                data, consumo_final = ultimas_5_medicoes[i-1]
                                data, consumo_inicial = ultimas_5_medicoes[i]
                                consumo_total = int(consumo_final) - int(consumo_inicial)
                                # Calcula e salva a variação de consumo dos último 4 períodos
                                lista_variacao_consumo.append(consumo_total)
                                i -= 1
                            
                            # Calcula a média de consumo dos últimos 3 períodos anteriores
                            media = (lista_variacao_consumo[0] + 
                                    lista_variacao_consumo[1] +
                                    lista_variacao_consumo[2])/3
                            
                            # Caso o consumo do último período seja maior que a média
                            # de consumo dos últimos 3 períodos vezes 1,5
                            if (lista_variacao_consumo[3] >= (media*1.5)):
                                # Calcula a diferença de consumo do último período em relação
                                # à média de consumo dos últimos 3 períodos anteriores
                                excesso_consumo = lista_variacao_consumo[3] - media
                                dic_exc_consumo = { "excesso_consumo" : excesso_consumo }

                                request = self.montarResponse("200", "OK", json.dumps(dic_exc_consumo))
                                self.enviarMensagem(client, request)
                            
                            # Caso não seja identificado consumo excessivo em relação à
                            # média dos períodos anteriores
                            else:
                                request = self.montarResponse("200", "OK", json.dumps("Sem consumo excessivo"))
                                self.enviarMensagem(client, request)
                        
                        else:
                            request = self.montarResponse("404", "Not Found", "")
                            self.enviarMensagem(client, request)

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

        self.publish(client_mqtt, self.topic1, "oi")


carro_inst = Car()
carro_inst.main()
