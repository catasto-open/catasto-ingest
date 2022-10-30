from .common import CommonBase, CommonBaseFiscalSubject


class SoggettiModel(CommonBase, CommonBaseFiscalSubject):
    cognome: str = None
    nome: str = None
    sesso: str = None
    data_di_nascita: str = None # TBD to_date
    luogo_di_nascita: str = None
    info_suppl: str = None
    denominazione: str = None
    sede: str = None
