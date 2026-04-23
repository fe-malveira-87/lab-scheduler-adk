from pydantic import BaseModel, computed_field


class PIIEntity(BaseModel):
    type: str
    original: str
    masked: str
    start: int
    end: int


class PIIResult(BaseModel):
    original_text: str
    masked_text: str
    entities: list[PIIEntity] = []

    @computed_field
    @property
    def total_entities(self) -> int:
        return len(self.entities)

    @computed_field
    @property
    def has_pii(self) -> bool:
        return len(self.entities) > 0
