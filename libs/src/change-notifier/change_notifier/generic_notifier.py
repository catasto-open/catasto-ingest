from message import Message
from datetime import date
from memphis import Memphis

class Notifier:

    def __init__(self, host:str, username:str, connection_token:str, station_name:str, producer_name:str) -> None:
        self.memphis = Memphis()
        self.host = host
        self.username = username
        self.connection_token = connection_token
        self.station_name = station_name
        self.producer_name = producer_name
        self.producer = None

    async def connect_to_station(self):
        with await self.memphis.connect(
            host=self.host,
            username=self.username,
            connection_token=self.connection_token,
            # port=6666,
            reconnect=True,
            max_reconnect=10,
            reconnect_interval_ms=1500,
            timeout_ms=150000000
        ):
            self.producer = await self.memphis.producer(
                station_name=self.station_name,
                producer_name=self.producer_name
            )

    async def connect_close(self):
        await self.memphis.close()

    def prepare_input(self):
        m1 = Message()
        m1.data_aggiornamento = date.today()
        m1.identificativo_immobile = '12345'
        m1.tipo_immobile = 'F'
        m1.identificativo_operazione = None

        m2 = Message()
        m2.data_aggiornamento = date.today()
        m2.identificativo_immobile = '6789'
        m2.tipo_immobile = 'T'
        m2.identificativo_operazione = None

        return [m1, m2, m1]

    async def push_message(self, message: Message):
        if not self.producer:
            raise RuntimeError("Producer is not initialized. Call connect_to_station first.")
        await self.producer.produce(message.model_dump_json())

    async def notify(self):
        await self.connect_to_station()
        messages = self.prepare_input()

        for m in messages:
            await self.push_message(m)
        await self.connect_close()
