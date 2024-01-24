from message import Message
from datetime import date
from generic_notifier import Notifier

class ReftreeNotifier(Notifier):

    def __init__(self, host, username, connection_token, station_name, producer_name) -> None:
        super().__init__(host, username, connection_token, station_name, producer_name)

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
