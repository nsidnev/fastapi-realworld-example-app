from datetime import datetime, timezone

from pydantic import BaseConfig


class ISODatetimeConfig(BaseConfig):
    json_encoders = {
        datetime: lambda dt: dt.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    }
