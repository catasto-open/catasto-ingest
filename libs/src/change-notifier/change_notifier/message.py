from pydantic import BaseModel
from datetime import date

class Message(BaseModel):
    data_aggiornamento: date
    identificativo_immobile: str
    tipo_immobile: int
    identificativo_operazione: str
