from datetime import date

from pydantic import ConfigDict

MY_CONFIG = ConfigDict(
    from_attributes=True,
    extra="ignore",
    json_encoders={date: lambda v: v.strftime("%Y-%m-%d")},
    arbitrary_types_allowed=True,
)
