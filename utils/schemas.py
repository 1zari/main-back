from pydantic import BaseModel, ConfigDict

MY_CONFIG = ConfigDict(
        from_attributes=True,
        extra='ignore'
    )

class CustomBaseModel(BaseModel):
    model_config = MY_CONFIG
