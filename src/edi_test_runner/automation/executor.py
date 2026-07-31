from datetime import datetime
from typing import TypedDict
from uuid import uuid4

from playwright.sync_api import Page

from edi_test_runner.automation.discovery import Regra
from edi_test_runner.core.models import (
    Ambiente,
    EtapaExecucao,
    Execucao,
    StatusEtapa,
    StatusExecucao,
)


class RegraNaoEncontradaError(Exception):
    pass


class _EtapaLog(TypedDict):
    nome: str
    status: StatusEtapa
    mensagem: str | None
    duracaoSegundos: int


class _LogExecucao(TypedDict):
    resultado: str
    etapas: list[_EtapaLog]


def executar_regra(
    page: Page,
    base_url: str,
    cliente: str,
    ambiente: Ambiente,
    regra: Regra,
) -> Execucao:
    data_inicio = datetime.now()

    page.goto(f"{base_url}/regra_detalhe.html?id={regra.nome}")

    if page.locator("#erro-regra").is_visible():
        raise RegraNaoEncontradaError(f"Regra '{regra.nome}' não encontrada no EDI.")

    page.click("#aplicar-regra")

    page.goto(f"{base_url}/execucao_log.html?id={regra.nome}")
    log_execucao: _LogExecucao = page.evaluate("window.__logExecucao")

    etapas = [
        EtapaExecucao(
            ordem=indice + 1,
            nome=etapa["nome"],
            status=etapa["status"],
            duracao_segundos=etapa["duracaoSegundos"],
            mensagem=etapa["mensagem"],
        )
        for indice, etapa in enumerate(log_execucao["etapas"])
    ]

    status_geral: StatusExecucao = (
        "SUCESSO" if all(etapa.status == "SUCESSO" for etapa in etapas) else "FALHA"
    )

    data_fim = datetime.now()

    return Execucao(
        id=str(uuid4()),
        cliente=cliente,
        ambiente=ambiente,
        data_inicio=data_inicio,
        data_fim=data_fim,
        duracao_segundos=int((data_fim - data_inicio).total_seconds()),
        status=status_geral,
        tipo_teste=regra.tipo,
        etapas=etapas,
        observacoes=_montar_observacoes(etapas, status_geral),
    )


def _montar_observacoes(etapas: list[EtapaExecucao], status_geral: StatusExecucao) -> str | None:
    if status_geral == "SUCESSO":
        return None

    etapa_com_falha = next((etapa for etapa in etapas if etapa.status == "FALHA"), None)
    if etapa_com_falha is None:
        return None

    return f"Falha na etapa '{etapa_com_falha.nome}': {etapa_com_falha.mensagem}"
