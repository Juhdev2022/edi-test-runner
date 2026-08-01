from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from playwright.sync_api import Page

from edi_test_runner.automation.discovery import Regra
from edi_test_runner.automation.executor import executar_regra
from edi_test_runner.core.models import Ambiente, Execucao, StatusExecucao


@dataclass(frozen=True)
class ResultadoBateria:
    execucoes: list[Execucao] = field(default_factory=list)
    data_inicio: datetime = field(default_factory=datetime.now)
    data_fim: datetime = field(default_factory=datetime.now)

    @property
    def total_regras(self) -> int:
        return len(self.execucoes)

    @property
    def total_sucesso(self) -> int:
        return sum(1 for execucao in self.execucoes if execucao.status == "SUCESSO")

    @property
    def total_falha(self) -> int:
        return sum(1 for execucao in self.execucoes if execucao.status == "FALHA")

    @property
    def duracao_segundos(self) -> int:
        return int((self.data_fim - self.data_inicio).total_seconds())

    @property
    def status_geral(self) -> StatusExecucao:
        # Nenhuma regra executada (lote vazio ou todas inativas): não há evidência
        # de sucesso, então não retorna SAUDAVEL — trata como PARCIAL (inconclusivo).
        if self.total_regras == 0:
            return "PARCIAL"
        if self.total_sucesso == self.total_regras:
            return "SUCESSO"
        if self.total_falha == self.total_regras:
            return "FALHA"
        return "PARCIAL"


def executar_bateria(
    page: Page,
    base_url: str,
    cliente: str,
    ambiente: Ambiente,
    regras: list[Regra],
    on_progresso: Callable[[int, int, Regra], None] | None = None,
) -> ResultadoBateria:
    data_inicio = datetime.now()

    regras_ativas = [regra for regra in regras if regra.status == "ATIVA"]
    total = len(regras_ativas)

    execucoes: list[Execucao] = []
    for indice, regra in enumerate(regras_ativas, start=1):
        execucao = executar_regra(page, base_url, cliente, ambiente, regra)
        execucoes.append(execucao)

        _resetar_para_tela_inicial(page, base_url)

        if on_progresso is not None:
            on_progresso(indice, total, regra)

    data_fim = datetime.now()

    return ResultadoBateria(execucoes=execucoes, data_inicio=data_inicio, data_fim=data_fim)


def _resetar_para_tela_inicial(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/regras.html")
