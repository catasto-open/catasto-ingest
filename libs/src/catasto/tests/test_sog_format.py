import pytest
from catasto.parser import parse_sog_record_info
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
