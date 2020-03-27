from datetime import datetime

from app.models.domain.rwmodel import convert_datetime_to_realworld


def test_api_datetime_is_in_realworld_format() -> None:
    dt = datetime.fromisoformat("2019-10-27T02:21:42.844640")
    assert convert_datetime_to_realworld(dt) == "2019-10-27T02:21:42.844640Z"
