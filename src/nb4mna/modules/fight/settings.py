from pydantic import BaseModel


class TatsumakiSettings(BaseModel):
    api_key: str
    guild_id: int
