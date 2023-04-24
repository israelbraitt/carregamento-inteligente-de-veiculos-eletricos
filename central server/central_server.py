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
            socket_tcp (socket): inicialização do socket TCP para comunicação com o servidor central
            station_dict (dict): lista de postos de carregamento associados ao serviço
            format (str): formato da codificação de caracteres
    """

    def __init__(self):
        """
        Método construtor da classe
        """
        self.cloud_host = socket.gethostbyname(socket.gethostname())
        self.cloud_port = 1917

        self.socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.station_dict = {}

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
            print(self.cloud_host)
            self.socket_tcp.bind((self.cloud_host, self.cloud_port))
            self.socket_tcp.listen()
        except:
            return print("Não foi possível iniciar o sistema de informações")

        while True:
            # Aceita a conexão com os sockets dos clientes
            conn_client_tcp, addr_client_tcp = self.socket_tcp.accept()
            print("Conectado com um cliente TCP em: ", addr_client_tcp)

            # Recebe mensagens dos clientes através da conexão TCP
            thread_tcp = threading.Thread(target=self.tratarServer, args=(conn_client_tcp, addr_client_tcp))
            thread_tcp.start()

    def tratarServer(self, client, addr):
        """
        Trata mensagens recebidas pelo servidor

            Parâmetros:
                client (): cliente TCP
                addr (str): endereço para envio da resposta
        """
        connected = True
        print(f"\n===CONEXÃO COM {addr} ESTABELECIDA.===\n")
        try:
            while connected:
                msg = client.recv(1024).decode(self.format)
                msg = str(msg)
                msg = json.loads(msg)
                print("===MENSAGEM RECEBIDA===")
                print(msg)
                response = None

                if msg.get("time_left"):
                    response = self.chooseBestStation(msg)
                elif msg.get("queue"):
                    response = self.updateStation(msg)

                if response:
                    print(f"\n===ENVIANDO RESPOSTA:=== \n{response}")
                    client.send(response.encode(self.format))

        except Exception as e:
            print(f"\n===OCORREU UM ERRO NA COMUNICAÇÃO COM {addr}.===")
            print(e)

    def updateStation(self, station_info):
        """
        Atualiza informações de um posto de carregamento

            Parâmetros:
                station_info (dict): informações de um posto de carregamento
        """
        print(self.station_dict)

        new_location = station_info.get("location")
        new_code = station_info.get("code")
        new_queue = station_info.get("queue")
        new_station = Station(new_location, new_code, new_queue)
        self.station_dict[new_code] = new_station
        print(self.station_dict)

        response = "{\"result\": \"1\"}"
        return response

    def chooseBestStation(self, car_info):
        """
        Escolhe o melhor posto entre as opções disponíveis para o carro recarregar

            Parâmetros:
                car_info (): informações do carro (bateria e modo de autonomia)
        """
        best_queue = 25
        best_station = None

        for station in self.station_dict.values():
            if station.location != car_info.get("location"):
                current_distance = station.distance(int(car_info.get("location")))
                current_time = current_distance * 10
                if int(car_info.get("time_left")) > current_time:
                    if int(station.queue) < best_queue:
                        best_queue = station.queue
                        best_station = station
        if best_station:
            return best_station.getJson()
        else:
            return "{\"result\": \"posto não encontrado\"}"

    def main(self):
        # Cria um socket com conexão TCP
        self.conexaoTCP()

central = CentralServer()
central.main()
