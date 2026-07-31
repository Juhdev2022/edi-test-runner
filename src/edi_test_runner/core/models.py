from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, computed_field
from pydantic.alias_generators import to_camel

Ambiente = Literal["PRODUCAO", "HOMOLOGACAO", "DESENVOLVIMENTO"]
StatusExecucao = Literal["SUCESSO", "FALHA", "PARCIAL", "EM_EXECUCAO"]
StatusEtapa = Literal["SUCESSO", "FALHA", "PULADA"]


class EdiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )


class EtapaExecucao(EdiModel):
    ordem: int
    nome: str
    status: StatusEtapa
    duracao_segundos: int
    mensagem: str | None = None


class Execucao(EdiModel):
    id: str
    cliente: str
    ambiente: Ambiente
    data_inicio: datetime
    data_fim: datetime
    duracao_segundos: int
    status: StatusExecucao
    tipo_teste: str
    etapas: list[EtapaExecucao]
    observacoes: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_etapas(self) -> int:
        return len(self.etapas)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def etapas_com_sucesso(self) -> int:
        return sum(1 for etapa in self.etapas if etapa.status == "SUCESSO")
