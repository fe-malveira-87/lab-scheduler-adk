from pydantic import BaseModel, computed_field


class PIIEntity(BaseModel):
    tipo: str
    valor_original: str
    valor_mascarado: str
    posicao_inicio: int
    posicao_fim: int


class PIIResult(BaseModel):
    texto_original: str
    texto_anonimizado: str
    entidades: list[PIIEntity] = []

    @computed_field
    @property
    def total_entidades(self) -> int:
        return len(self.entidades)

    @computed_field
    @property
    def tem_pii(self) -> bool:
        return len(self.entidades) > 0
