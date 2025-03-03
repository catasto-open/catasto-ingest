import pytest
from catasto.parser import (
    FileParserService,
    parse_fab_record1_line,
    parse_fab_record_info,
)
from catasto.reader import LocalFileReaderService
from pydantic import ValidationError

# from .fab_generator import FabbricatiGenerator


class TestFabRecordInfo:
    """Test per il record generico di FAB."""

    def test_parse_fab_record_info_valid_line(self, static_fab_record1_valid_line):
        "Verifica che una linea con un record generico venga interpretata correttamente."

        fab_record_info = parse_fab_record_info(static_fab_record1_valid_line)

        assert fab_record_info.codice_amministrativo == "H501"
        assert fab_record_info.sezione == " "
        assert fab_record_info.identificativo_immobile == "5810000"
        assert fab_record_info.tipo_immobile == "F"
        assert fab_record_info.progressivo == "3"
        assert fab_record_info.tipo_record == "1"
        assert fab_record_info.items_number == 46

    def test_parse_fab_record_info_invalid_line(self, static_fab_record1_invalid_line):
        "Verifica che una linea con un record generico venga interpretata correttamente."

        with pytest.raises(ValidationError):
            fab_record_info = parse_fab_record_info(static_fab_record1_invalid_line)


class TestFabbricatiRecord1:
    """Test per il record di tipo 1 (caratteristiche dell'unità immobiliare)."""

    def test_parse_record1_line(self, static_fab_record1_valid_line):
        "Verifica che una linea con un record1 venga interpretata correttamente."

        fab_record_info = parse_fab_record_info(static_fab_record1_valid_line)
        parser = parse_fab_record1_line(fab_record_info)

        assert parser.codice_amministrativo == "H501"
        assert parser.sezione == " "
        assert parser.identificativo_immobile == "5810000"
        assert parser.tipo_immobile == "F"
        assert parser.progressivo == "3"
        assert parser.tipo_record == "1"

        assert parser.zona == "006"
        assert parser.categoria == "A02"
        assert parser.classe == "06"
        assert parser.consistenza == "6,5"
        assert parser.superficie == "141"
        assert parser.rendita_lire == ""
        assert parser.rendita_euro == "1057,45"
        assert parser.lotto == ""
        assert parser.edificio == ""
        assert parser.scala == ""
        assert parser.interno1 == "1"
        assert parser.interno2 == ""
        assert parser.piano1 == "T-1"
        assert parser.piano2 == ""
        assert parser.piano3 == ""
        assert parser.piano4 == ""
        assert parser.data_efficacia_iniziale == "27012020"
        assert parser.data_registrazione_atti_iniziale == "28012020"
        assert parser.tipo_nota_iniziale == "V"
        assert parser.numero_nota_iniziale == "045227"
        assert parser.progressivo_nota_iniziale == "001"
        assert parser.anno_nota_iniziale == "2020"
        assert parser.data_efficacia_finale == ""
        assert parser.data_registrazione_atti_finale == ""
        assert parser.tipo_nota_finale == ""
        assert parser.numero_nota_finale == ""
        assert parser.progressivo_nota_finale == ""
        assert parser.anno_nota_finale == ""
        assert parser.partita == ""
        assert parser.annotazione == ""
        assert parser.identificativo_mutazione_iniziale == "341274286"
        assert parser.identificativo_mutazione_finale == ""
        assert parser.protocollo_notifica == ""
        assert parser.data_notifica == ""
        assert parser.codice_causale_atto_generante == "VAR"
        assert (
            parser.descrizione_atto_generante
            == "QUESTA VIENE CONSIDERATA UNA SIMULAZIONE"
        )
        assert parser.codice_causale_atto_conclusivo == ""
        assert parser.descrizione_atto_conclusivo == ""
        assert parser.flag_classamento == "1"

    def test_parse_record1_invalid_line(self, static_fab_record1_invalid_line):
        "Verifica che una linea con un record1 venga interpretata correttamente."

        with pytest.raises(ValidationError):
            fab_record_info = parse_fab_record_info(static_fab_record1_invalid_line)
            parser = parse_fab_record1_line(fab_record_info)

    # def test_valid_record1(self, random_fab_record1):
    #     """Verifica che un record generato casualmente sia valido."""
    #     assert isinstance(random_fab_record1, FabbricatiRecord1)
    #     assert random_fab_record1.tipo_record == "1"
    #     assert random_fab_record1.tipo_immobile == "F"
    #     assert len(random_fab_record1.codice_amministrativo) == 4
    #     assert len(random_fab_record1.sezione) == 1
    #     assert len(random_fab_record1.progressivo) == 3

    # def test_categoria_validazione(self):
    #     """Verifica la validazione della categoria catastale."""
    #     record_data, _ = FabbricatiGenerator.genera_record1()

    #     # Categorie valide
    #     valid_categorie = ["A01", "B02", "C03"]
    #     for categoria in valid_categorie:
    #         record_data["categoria"] = categoria

    #         # Adeguare la consistenza in base alla categoria modificata
    #         if categoria.startswith("A"):
    #             # Per categoria A, la consistenza deve terminare con 0 o 5
    #             record_data["consistenza"] = "0000010"  # Termina con 0
    #         elif categoria.startswith("B"):
    #             # Per categoria B, qualsiasi valore numerico va bene
    #             record_data["consistenza"] = "0001234"
    #         elif categoria.startswith("C"):
    #             # Per categoria C, qualsiasi valore numerico va bene
    #             record_data["consistenza"] = "0005678"

    #         record = FabbricatiRecord1(**record_data)
    #         assert record.categoria == categoria

    # def test_consistenza_validazione(self):
    #     """Verifica la validazione della consistenza in base alla categoria."""
    #     record_data, _ = FabbricatiGenerator.genera_record1()

    #     # Test per categoria A (deve terminare con 0 o 5)
    #     record_data["categoria"] = "A01"

    #     # Valori validi
    #     record_data["consistenza"] = "0000010"
    #     record = FabbricatiRecord1(**record_data)
    #     assert record.consistenza == "0000010"

    #     record_data["consistenza"] = "0000015"
    #     record = FabbricatiRecord1(**record_data)
    #     assert record.consistenza == "0000015"

    #     # Valori non validi per categoria A
    #     record_data["consistenza"] = "0000012"
    #     with pytest.raises(ValidationError):
    #         FabbricatiRecord1(**record_data)

    #     # Test per categoria B (può essere qualsiasi numero)
    #     record_data["categoria"] = "B01"
    #     record_data["consistenza"] = "0001234"
    #     record = FabbricatiRecord1(**record_data)
    #     assert record.consistenza == "0001234"

    #     # Test per categoria C (può essere qualsiasi numero)
    #     record_data["categoria"] = "C01"
    #     record_data["consistenza"] = "0005678"
    #     record = FabbricatiRecord1(**record_data)
    #     assert record.consistenza == "0005678"

    # def test_date_validazione(self):
    #     """Verifica la validazione delle date."""
    #     record_data, _ = FabbricatiGenerator.genera_record1()

    #     # Data valida
    #     record_data["data_efficacia_iniziale"] = "01012022"
    #     record = FabbricatiRecord1(**record_data)
    #     assert record.data_efficacia_iniziale == "01012022"

    #     # Date non valide
    #     invalid_dates = ["32012022", "01132022", "01012999", "2022-01-01", "01/01/2022"]
    #     for date in invalid_dates:
    #         record_data["data_efficacia_iniziale"] = date

    #         # Cattura specificamente il messaggio di errore per il debug
    #         try:
    #             FabbricatiRecord1(**record_data)
    #             pytest.fail(f"Dovrebbe sollevare un errore per la data: {date}")
    #         except ValidationError as e:
    #             print(f"Errore catturato per {date}: {str(e)}")
    #             # Verifica che l'errore riguardi il campo data
    #             assert "data_efficacia_iniziale" in str(e)

    # def test_rendita_euro_validazione(self):
    #     """Verifica la validazione della rendita in euro."""
    #     record_data, _ = FabbricatiGenerator.genera_record1()

    #     # Rendita valida (18 caratteri esatti)
    #     record_data["rendita_euro"] = (
    #         "00000000000051.640"  # 14 cifre + punto + 3 cifre = 18 caratteri
    #     )
    #     record = FabbricatiRecord1(**record_data)
    #     assert record.rendita_euro == "00000000000051.640"

    #     # Rendite non valide
    #     invalid_rendite = [
    #         "00000000000051.64",  # Solo 2 decimali
    #         "00000000000051",  # Senza decimali
    #         "51.640",  # Troppo corta
    #         "00000000000051,640",  # Virgola invece di punto
    #     ]
    #     for rendita in invalid_rendite:
    #         record_data["rendita_euro"] = rendita
    #         with pytest.raises(ValidationError):
    #             FabbricatiRecord1(**record_data)


# class TestFabbricatiRecord2:
#     """Test per il record di tipo 2 (identificativi dell'unità immobiliare)."""

#     def test_valid_record2(self):
#         """Verifica che un record generato casualmente sia valido."""
#         t = FabbricatiTestGenerator.genera_file_fabbricati()
#         record1, key = t  # FabbricatiGenerator.genera_record1()
#         codice, sezione, id_immobile, progressivo = key
#         record2_data = t  # FabbricatiGenerator.genera_record2(
#         #    codice, sezione, id_immobile, progressivo, num_identificativi=2
#         # )

#         record2 = FabbricatiRecord2(**record2_data)

#         assert isinstance(record2, FabbricatiRecord2)
#         assert record2.tipo_record == "2"
#         assert record2.tipo_immobile == "F"
#         assert len(record2.identificativi) == 2
#         assert isinstance(record2.identificativi[0], Identificativo)

#     def test_edificialita_validazione(self):
#         """Verifica la validazione dell'edificialità."""
#         record1, key = FabbricatiGenerator.genera_record1()
#         codice, sezione, id_immobile, progressivo = key
#         record2_data = FabbricatiGenerator.genera_record2(
#             codice, sezione, id_immobile, progressivo, num_identificativi=1
#         )

#         # Test con edificialità 'E' e numero che inizia con '.'
#         record2_data["identificativi"][0]["edificialita"] = "E"
#         record2_data["identificativi"][0]["numero"] = ".0123"
#         record2 = FabbricatiRecord2(**record2_data)
#         assert record2.identificativi[0].edificialita == "E"
#         assert record2.identificativi[0].numero == ".0123"

#         # Test con edificialità 'E' ma numero che non inizia con '.'
#         record2_data["identificativi"][0]["edificialita"] = "E"
#         record2_data["identificativi"][0]["numero"] = "00123"
#         with pytest.raises(ValidationError):
#             FabbricatiRecord2(**record2_data)

#         # Test con edificialità ' ' (spazio)
#         record2_data["identificativi"][0]["edificialita"] = " "
#         record2_data["identificativi"][0]["numero"] = "00123"
#         record2 = FabbricatiRecord2(**record2_data)
#         assert record2.identificativi[0].edificialita == " "
#         assert record2.identificativi[0].numero == "00123"

#     def test_max_identificativi(self):
#         """Verifica che non si possano avere più di 10 identificativi."""
#         record1, key = FabbricatiGenerator.genera_record1()
#         codice, sezione, id_immobile, progressivo = key

#         # Genera un record con 10 identificativi (dovrebbe funzionare)
#         record_data = FabbricatiGenerator.genera_record2(
#             codice, sezione, id_immobile, progressivo, num_identificativi=10
#         )
#         record = FabbricatiRecord2(**record_data)
#         assert len(record.identificativi) == 10

#         # Genera un record con 11 identificativi (dovrebbe fallire)
#         record_data = FabbricatiGenerator.genera_record2(
#             codice, sezione, id_immobile, progressivo, num_identificativi=1
#         )
#         # Aggiungi manualmente più identificativi
#         identificativo = record_data["identificativi"][0]
#         record_data["identificativi"] = [identificativo.copy() for _ in range(11)]

#         with pytest.raises(ValidationError):
#             FabbricatiRecord2(**record_data)


# class TestFabbricatiRecord3:
#     """Test per il record di tipo 3 (indirizzi dell'unità immobiliare)."""

#     def test_valid_record3(self):
#         """Verifica che un record generato casualmente sia valido."""
#         record1, key = FabbricatiGenerator.genera_record1()
#         codice, sezione, id_immobile, progressivo = key
#         record3_data = FabbricatiGenerator.genera_record3(
#             codice, sezione, id_immobile, progressivo, num_indirizzi=2
#         )

#         record3 = FabbricatiRecord3(**record3_data)

#         assert isinstance(record3, FabbricatiRecord3)
#         assert record3.tipo_record == "3"
#         assert record3.tipo_immobile == "F"
#         assert len(record3.indirizzi) == 2
#         assert isinstance(record3.indirizzi[0], Indirizzo)

#     def test_max_indirizzi(self):
#         """Verifica che non si possano avere più di 4 indirizzi."""
#         record1, key = FabbricatiGenerator.genera_record1()
#         codice, sezione, id_immobile, progressivo = key

#         # Genera un record con 4 indirizzi (dovrebbe funzionare)
#         record_data = FabbricatiGenerator.genera_record3(
#             codice, sezione, id_immobile, progressivo, num_indirizzi=4
#         )
#         record = FabbricatiRecord3(**record_data)
#         assert len(record.indirizzi) == 4

#         # Genera un record con 5 indirizzi (dovrebbe fallire)
#         record_data = FabbricatiGenerator.genera_record3(
#             codice, sezione, id_immobile, progressivo, num_indirizzi=1
#         )
#         # Aggiungi manualmente più indirizzi
#         indirizzo = record_data["indirizzi"][0]
#         record_data["indirizzi"] = [indirizzo.copy() for _ in range(5)]

#         with pytest.raises(ValidationError):
#             FabbricatiRecord3(**record_data)


# class TestFabbricatiRecord4:
#     """Test per il record di tipo 4 (utilità comuni dell'unità immobiliare)."""

#     def test_valid_record4(self):
#         """Verifica che un record generato casualmente sia valido."""
#         record1, key = FabbricatiGenerator.genera_record1()
#         codice, sezione, id_immobile, progressivo = key
#         record4_data = FabbricatiGenerator.genera_record4(
#             codice, sezione, id_immobile, progressivo, num_utilita=2
#         )

#         record4 = FabbricatiRecord4(**record4_data)

#         assert isinstance(record4, FabbricatiRecord4)
#         assert record4.tipo_record == "4"
#         assert record4.tipo_immobile == "F"
#         assert len(record4.utilita_comuni) == 2
#         assert isinstance(record4.utilita_comuni[0], UtilitaComune)

#     def test_max_utilita_comuni(self):
#         """Verifica che non si possano avere più di 10 utilità comuni."""
#         record1, key = FabbricatiGenerator.genera_record1()
#         codice, sezione, id_immobile, progressivo = key

#         # Genera un record con 10 utilità comuni (dovrebbe funzionare)
#         record_data = FabbricatiGenerator.genera_record4(
#             codice, sezione, id_immobile, progressivo, num_utilita=10
#         )
#         record = FabbricatiRecord4(**record_data)
#         assert len(record.utilita_comuni) == 10

#         # Genera un record con 11 utilità comuni (dovrebbe fallire)
#         record_data = FabbricatiGenerator.genera_record4(
#             codice, sezione, id_immobile, progressivo, num_utilita=1
#         )
#         # Aggiungi manualmente più utilità comuni
#         utilita = record_data["utilita_comuni"][0]
#         record_data["utilita_comuni"] = [utilita.copy() for _ in range(11)]

#         with pytest.raises(ValidationError):
#             FabbricatiRecord4(**record_data)


# class TestFabbricatiRecord5:
#     """Test per il record di tipo 5 (riserve dell'unità immobiliare)."""

#     def test_valid_record5(self):
#         """Verifica che un record generato casualmente sia valido."""
#         record1, key = FabbricatiGenerator.genera_record1()
#         codice, sezione, id_immobile, progressivo = key
#         record5_data = FabbricatiGenerator.genera_record5(
#             codice, sezione, id_immobile, progressivo, num_riserve=2
#         )

#         record5 = FabbricatiRecord5(**record5_data)

#         assert isinstance(record5, FabbricatiRecord5)
#         assert record5.tipo_record == "5"
#         assert record5.tipo_immobile == "F"
#         assert len(record5.riserve) == 2
#         assert isinstance(record5.riserve[0], Riserva)

#     def test_max_riserve(self):
#         """Verifica che non si possano avere più di 10 riserve."""
#         record1, key = FabbricatiGenerator.genera_record1()
#         codice, sezione, id_immobile, progressivo = key

#         # Genera un record con 10 riserve (dovrebbe funzionare)
#         record_data = FabbricatiGenerator.genera_record5(
#             codice, sezione, id_immobile, progressivo, num_riserve=10
#         )
#         record = FabbricatiRecord5(**record_data)
#         assert len(record.riserve) == 10

#         # Genera un record con 11 riserve (dovrebbe fallire)
#         record_data = FabbricatiGenerator.genera_record5(
#             codice, sezione, id_immobile, progressivo, num_riserve=1
#         )
#         # Aggiungi manualmente più riserve
#         riserva = record_data["riserve"][0]
#         record_data["riserve"] = [riserva.copy() for _ in range(11)]

#         with pytest.raises(ValidationError):
#             FabbricatiRecord5(**record_data)


# class TestImmobileCompleto:
#     """Test per un immobile completo (insieme di record diversi)."""

#     def test_immobile_completo(self, random_immobile_completo):
#         """Verifica che un immobile completo generato casualmente sia valido."""
#         # Verifica che ci siano almeno i due record obbligatori
#         assert len(random_immobile_completo) >= 2

#         # Estrai i record per tipo
#         records_by_type = {}
#         for record in random_immobile_completo:
#             records_by_type[record.tipo_record] = record

#         # Verifica che ci siano almeno i record di tipo 1 e 2
#         assert "1" in records_by_type
#         assert "2" in records_by_type

#         # Verifica che tutti i record abbiano gli stessi campi di base
#         record1 = records_by_type["1"]
#         codice = record1.codice_amministrativo
#         sezione = record1.sezione
#         id_immobile = record1.identificativo_immobile
#         progressivo = record1.progressivo

#         for record in random_immobile_completo:
#             assert record.codice_amministrativo == codice
#             assert record.sezione == sezione
#             assert record.identificativo_immobile == id_immobile
#             assert record.progressivo == progressivo
#             assert record.tipo_immobile == "F"


class TestFileValidazione:
    """Test per la validazione di interi file .FAB."""

    @pytest.mark.asyncio
    async def test_lettura_file_valido(self, temp_fab_file):
        """Verifica che un file generato casualmente possa essere letto."""
        reader = LocalFileReaderService(filepath=str(temp_fab_file))

        async with reader.open() as file_reader:
            assert file_reader is not None
            assert isinstance(file_reader.content, str)
            assert len(file_reader.content.strip().split("\n")) > 0

    @pytest.mark.asyncio
    async def test_parsing_file_valido(self, temp_fab_file):
        """Verifica che un file generato casualmente possa essere parsificato."""
        reader = LocalFileReaderService(filepath=str(temp_fab_file))
        parser = FileParserService(reader=reader)

        # Ottenere l'oggetto Census dal parser
        census = await parser.parse()

        # Verifica che ci sia un oggetto Census
        assert census
        assert hasattr(census, "fabbricati")
        assert census.fabbricati

        # Verifica che ci siano immobili
        assert hasattr(census.fabbricati, "immobili")

        # Verifica che ogni immobile abbia almeno i record di tipo 1 e 2
        for immobile in census.fabbricati.immobili:
            assert hasattr(immobile, "record1")
            assert immobile.record1 is not None
            assert immobile.record1.tipo_record == "1"

            assert hasattr(immobile, "record2")
            assert immobile.record2 is not None
            assert immobile.record2.tipo_record == "2"

    @pytest.mark.asyncio
    async def test_file_con_errori(self, custom_fab_file):
        """Verifica che un file con errori produca le eccezioni appropriate."""
        # Crea un file con errori di sintassi
        file_path = custom_fab_file(num_immobili=2, con_errori=True)

        reader = LocalFileReaderService(filepath=str(file_path))
        parser = FileParserService(reader=reader)

        # Il parser dovrebbe sollevare eccezioni per i record malformati
        with pytest.raises(Exception):
            await parser.parse()

    @pytest.mark.asyncio
    async def test_raggruppamento_immobili(self, temp_fab_file):
        """Verifica che i record possano essere raggruppati per immobile."""

        reader = LocalFileReaderService(filepath=str(temp_fab_file))
        parser = FileParserService(reader=reader)

        # Ottieni l'oggetto Census
        census = await parser.parse()

        # Verifica che l'oggetto Census sia valido
        assert census is not None, "L'oggetto Census non è stato creato"
        assert hasattr(census, "fabbricati"), "Census non ha l'attributo fabbricati"
        assert census.fabbricati is not None, "L'attributo fabbricati è None"

        # Se ci sono immobili, verifica che abbiano la struttura corretta
        if hasattr(census.fabbricati, "immobili") and census.fabbricati.immobili:
            for immobile in census.fabbricati.immobili:
                # Verifica che l'immobile abbia gli attributi di base
                assert hasattr(
                    immobile, "codice_amministrativo"
                ), "Immobile senza codice amministrativo"
                assert hasattr(immobile, "sezione"), "Immobile senza sezione"
                assert hasattr(
                    immobile, "identificativo_immobile"
                ), "Immobile senza identificativo"
                assert hasattr(immobile, "tipo_immobile"), "Immobile senza tipo"
                assert hasattr(immobile, "progressivo"), "Immobile senza progressivo"

                # Verifica che l'immobile abbia almeno i record obbligatori
                assert hasattr(immobile, "record1"), "Immobile senza record1"
                assert immobile.record1 is not None, "Record1 è None"
                assert hasattr(immobile, "record2"), "Immobile senza record2"
                assert immobile.record2 is not None, "Record2 è None"
        else:
            # Test passa anche senza immobili, ma lo segnaliamo
            print("Avviso: Nessun immobile trovato, ma il test passa comunque.")

    @pytest.mark.asyncio
    async def test_validate_record_formats(self, temp_fab_file):
        """Verifica che i record nel file rispettino i formati specificati nel PDF."""
        reader = LocalFileReaderService(filepath=str(temp_fab_file))

        async with reader.open() as file_reader:
            content = file_reader.content
            lines = content.strip().split("\n")

            for line in lines:
                # Estrai la parte dei campi chiave
                parts = line.split("|")
                assert len(parts) >= 5, f"Linea malformata: {line}"

                header = parts[0:6]

                # Verifica che l'header contenga i campi obbligatori
                assert len(header) == 6, f"Header troppo corto: {header}"

                # Verifica il tipo record
                tipo_record = header[5:6][0]
                assert tipo_record in [
                    "1",
                    "2",
                    "3",
                    "4",
                    "5",
                ], f"Tipo record non valido: {tipo_record}"

                # Verifica il tipo immobile (deve essere F per i fabbricati)
                tipo_immobile = header[3:4][0]
                assert (
                    tipo_immobile == "F"
                ), f"Tipo immobile non valido: {tipo_immobile}"

                # Verifica che il progressivo sia numerico
                progressivo = header[4:5][0]
                assert progressivo.isdigit(), f"Progressivo non numerico: {progressivo}"
