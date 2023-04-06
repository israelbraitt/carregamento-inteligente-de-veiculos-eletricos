import logging
import asyncio
from hbmqtt.broker import Broker as mqtt_broker
from paho.mqtt import client as mqtt_client

class MiddleServer:
    def __init__(self):

        self.logger = logging.getLogger(__name__)

        config = {
            'listeners': {
                'default': {
                    'type': 'tcp',
                    'bind': 'localhost:4000'
                }
            },
            'sys_interval': 10,
            'topic-check': {
                'enabled': False
            }
        }

        self.broker = mqtt_broker.Broker(config)

        self.broker_addr = "broker.hivemq.com"
        self.broker_port = 4000
        self.locality = "bairro_x"

        self.client = mqtt_client.Client()

        self.central_broker_addr = "public.mqtthq.com"
        self.central_broker_port = 1883

        self.power_station_topic = "power_station"
        self.car_batery_topic = "car/battery"
        self.central_topic = "central/paths"

    @asyncio.coroutine
    def startBroker(self):
        yield from self.broker.start()

    def on_connect(self, client, userdata, flags, rc):
        print("Conectado com " + str(client._client_id) + ": " + str(rc))

    def on_message(self, client, userdata, message):
        print("Mensagem recebida no tópico " + message.topic + " com QoS " + str(message.qos) + " and payload " + str(message.payload))
        if int(message.payload) == 2:
            print("2")
            self.central_broker.publish(self.central_topic, message.payload)

    def main(self):
        self.broker.on_message = self.on_message
        self.broker.on_connect = self.on_connect
        self.broker.connect(self.broker_addr, self.broker_port)
        self.broker.loop_start()
        self.broker.subscribe(self.station_topic)
        self.broker.subscribe(self.car_batery_topic)

        self.client.on_connect = self.on_connect
        self.client.connect(self.central_broker_addr, self.central_broker_port)
        self.client.loop_start()
        self.client.subscribe(self.central_topic)

        if __name__ == "__main__":
            formatter  = "[%(asctime)s] :: %(levelname)s :: %(name)s :: %(message)s"
            logging.basicConfig(level=logging.INFO, format=formatter)
            asyncio.get_event_loop().run_until_complete(self.startBroker())
            asyncio.get_event_loop().run_forever()

        print("INICIANDO BROKER LOCAL...")
