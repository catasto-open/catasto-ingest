import pytest
from catasto.parser import parse_sog_record_info, parse_sog_record_p_line
from pydantic import ValidationError


class TestSogRecordInfo:
    """Test per il record generico di SOG."""

    def test_parse_sog_record_info_valid_line(
        self, static_sog_private_person_record_valid_line
    ):
        "Verifica che una linea con un record generico venga interpretata correttamente."

        sog_record_info = parse_sog_record_info(
            static_sog_private_person_record_valid_line
        )

        assert sog_record_info.codice_amministrativo == "H501"
        assert sog_record_info.sezione == " "
        assert sog_record_info.identificativo_soggetto == "7125464"
        assert sog_record_info.tipo_soggetto == "P"
        assert sog_record_info.items_number == 12

    def test_parse_sog_record_info_invalid_line(
        self, static_sog_private_person_record_invalid_line
    ):
        "Verifica che una linea con un record generico venga interpretata correttamente."

        with pytest.raises(ValidationError):
            sog_record_info = parse_sog_record_info(
                static_sog_private_person_record_invalid_line
            )


class TestSoggetiRecordPrivatePerson:
    """Test per il record di tipo P (soggetti persone private dell'unità immobiliare)."""

    def test_parse_record_p_line(self, static_sog_private_person_record_valid_line):
        "Verifica che una linea con un record P venga interpretata correttamente."

        sog_record_info = parse_sog_record_info(
            static_sog_private_person_record_valid_line
        )
        parser = parse_sog_record_p_line(sog_record_info)

        assert parser.codice_amministrativo == "H501"
        assert parser.sezione == " "
        assert parser.identificativo_soggetto == "7125464"
        assert parser.tipo_soggetto == "P"

        assert parser.cognome == "ROSSI"
        assert parser.nome == "MARIO"
        assert parser.sesso == "1"
        assert parser.data_di_nascita == "01091973"
        assert parser.luogo_di_nascita == "H501"
        assert parser.codice_fiscale == "MRIRSS73P01LH501"

    def test_parse_record_p_invalid_line(
        self, static_sog_private_person_record_invalid_line
    ):
        "Verifica che una linea con un record P venga interpretata correttamente."

        with pytest.raises(ValidationError):
            sog_record_info = parse_sog_record_info(
                static_sog_private_person_record_invalid_line
            )
            parser = parse_sog_record_p_line(sog_record_info)
