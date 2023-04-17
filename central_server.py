from paho.mqtt import client as mqtt_client
import threading
import socket
import json
from station import Station

class CentralServer:
    """
    Servidor que processa as requisições dos servidores locais

        Atributos:
            cloud_host (str): endereço de conexão do socket TCP
            cloud_port (int): porta de conexão do socket TCP
            cloud_socket (socket): inicialização do socket TCP para comunicação com o servidor central

            station_list (list): lista de postos de carregamento associados ao serviço

            format (str): formato da codificação de caracteres
    """
    def __init__(self):
        """
        Método construtor da classe
        """
        self.cloud_host = '127.0.0.1'
        self.cloud_port = 1917
        self.socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.station_list = []

        self.format = 'utf-8'

    def conexaoTCP(self):
        """
        Faz conexão com clientes TCP e executa uma thread para receber as mensagens
            Parâmetros:
                socket_tcp (socket): socket para conexão TCP
        """

        try:
            # Fornece o endereço e as portas para "escutar" as conexões
            # com os sockets dos clientes
            self.socket_tcp.bind((self.tcp_host, self.tcp_port))
            self.socket_tcp.listen()
        except:
            return print("Não foi possível iniciar o sistema de informações")

        while True:
            # Aceita a conexão com os sockets dos clientes
            conn_client_tcp, addr_client_tcp = self.socket_tcp.accept()
            print("Conectado com um cliente TCP em: ", addr_client_tcp)
            new_station = Station()

            # Recebe mensagens dos clientes através da conexão TCP
            thread_tcp = threading.Thread(target=self.tratarRequests, args=[conn_client_tcp])
            thread_tcp.start()

    def recvMessage(self):
        """
        Recebe mensagens via TCP dos servidores locais
        """
        power_station_data = self.socket_tcp.recv(1024)

    def chooseBestStation(self, car_info):
        """
        Escolhe o melhor posto entre as opções disponíveis para o carro recarregar
        
            Argumentos:
                car_info (): informações do carro (bateria e modo de autonomia)
        """
        best_queue = 25
        best_station = None
        
        for station in self.station_list:
            time_to_station = 0
            if car_info["time left"] ==  time_to_station:
                if station.queue < best_queue:
                    best_station = station
        
        if best_station:
            return best_station
        else:
            pass

    def main(self):
        # Cria um socket com conexão TCP
        tcp_thread = threading.Thread(target=self.conexaoTCP, args=[])
        tcp_thread.start()
