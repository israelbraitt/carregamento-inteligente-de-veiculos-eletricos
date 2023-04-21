class Station:
    """
    Guarda informações dos postos de carregamento nos servidores

        Atributos:
            location (str): localização do posto
            code (int): código do posto
            queue (int): tamanho da fila de carros do posto
    """
    def __init__(self, location, code, queue):
        """
        Método construtor da classe

            Argumentos:
                location (str): localização do posto
                code (int): código do posto
                queue (int): tamanho da fila de carros do posto
        """
        self.location = location
        self.code = code
        self.queue = queue

    def getJson(self):
        """
        Retorna as informações do posto como um dicionário
        """
        json_code = "{\"code\": \"" + str(self.code) + "\", "
        json_location = "\"location\": \"" + str(self.location) + "\", "
        json_queue = "\"queue\":" + str(self.queue) + "\"}"
        return json_code + json_location + json_queue
