from station import Station

class DAO:
    """
    Data Acess Object para acessar e manipular a base de dados
    """
    def __init__(self):
        pass

    @staticmethod
    def getStationList():
        """
        Carrega a lista de postos de carregamento cadastrados

            Parâmetros:
            
            Retornos:
                Lista com objetos do tipo station com as informações dos postos de carregamento cadastrados
        """
        station_list = []

        file = open("database/station_list.txt")
        lines = file.readlines()

        for line in lines:
            code = line.split(";")[0]
            location = line.split(";")[1]
            queue = line.split(";")[2]
            station_obj = Station(location, code, queue)
            station_list.append(station_obj)
        
        file.close()
        
        return station_list
