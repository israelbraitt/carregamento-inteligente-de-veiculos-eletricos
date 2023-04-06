import logging
import asyncio
from hbmqtt.broker import Broker as mqtt_broker
from paho.mqtt import client as mqtt_client

class CentralServer:
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

        self.client = mqtt_client.Client()

        self.middle_broker_addr_port = []
        self.middle_broker_topics = []

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

        for i in len(self.middle_broker_topics):
            self.broker.subscribe(self.middle_broker_topics[i])
            self.client.on_connect = self.on_connect
            mb_addr_port = self.middle_broker_addr_port[i]
            self.client.connect(mb_addr_port[0], mb_addr_port[1])
            self.client.loop_start()
            self.client.subscribe(self.middle_broker_topics)


        if __name__ == "__main__":
            formatter  = "[%(asctime)s] :: %(levelname)s :: %(name)s :: %(message)s"
            logging.basicConfig(level=logging.INFO, format=formatter)
            asyncio.get_event_loop().run_until_complete(self.startBroker())
            asyncio.get_event_loop().run_forever()

        print("INICIANDO BROKER LOCAL...")
