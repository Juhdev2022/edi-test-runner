from datetime import datetime

import pytest
from playwright.sync_api import Page

from edi_test_runner.automation.batch_runner import ResultadoBateria, executar_bateria
from edi_test_runner.automation.discovery import Regra, descobrir_regras
from edi_test_runner.automation.executor import RegraNaoEncontradaError
from edi_test_runner.core.models import Execucao, StatusExecucao


def _execucao_exemplo(status: StatusExecucao) -> Execucao:
    return Execucao(
        id="1",
        cliente="CLIENTE_FICTICIO",
        ambiente="HOMOLOGACAO",
        data_inicio=datetime(2026, 7, 31, 10, 0, 0),
        data_fim=datetime(2026, 7, 31, 10, 0, 5),
        duracao_segundos=5,
        status=status,
        nome_regra="REGRA_UPLOAD_SFTP_01",
        tipo_teste="SFTP_UPLOAD",
        etapas=[],
    )


def test_bateria_completa_via_descoberta_real(page: Page, edi_mock_url: str) -> None:
    regras = descobrir_regras(page, base_url=edi_mock_url)

    resultado = executar_bateria(
        page,
        base_url=edi_mock_url,
        cliente="CLIENTE_FICTICIO",
        ambiente="HOMOLOGACAO",
        regras=regras,
    )

    # Só as 5 regras ATIVA de regras.html rodam; as 3 INATIVA são puladas.
    assert resultado.total_regras == 5
    assert resultado.total_sucesso == 3
    assert resultado.total_falha == 2
    assert resultado.status_geral == "PARCIAL"


def test_bateria_continua_apos_falha_de_regra(page: Page, edi_mock_url: str) -> None:
    regras = [
        Regra(nome="REGRA_UPLOAD_SFTP_01", tipo="SFTP_UPLOAD", status="ATIVA"),
        Regra(nome="REGRA_DOWNLOAD_FTPS_02", tipo="FTPS_DOWNLOAD", status="ATIVA"),
        Regra(nome="REGRA_UPLOAD_FTP_04", tipo="FTP_UPLOAD", status="ATIVA"),
    ]

    resultado = executar_bateria(
        page,
        base_url=edi_mock_url,
        cliente="CLIENTE_FICTICIO",
        ambiente="HOMOLOGACAO",
        regras=regras,
    )

    assert resultado.total_regras == 3
    assert [execucao.status for execucao in resultado.execucoes] == [
        "SUCESSO",
        "FALHA",
        "SUCESSO",
    ]


def test_executar_bateria_chama_on_progresso_para_cada_regra_ativa(
    page: Page, edi_mock_url: str
) -> None:
    regras = [
        Regra(nome="REGRA_UPLOAD_SFTP_01", tipo="SFTP_UPLOAD", status="ATIVA"),
        Regra(nome="REGRA_UPLOAD_FTP_04", tipo="FTP_UPLOAD", status="ATIVA"),
    ]
    chamadas: list[tuple[int, int, str]] = []

    def registrar(indice: int, total: int, regra: Regra) -> None:
        chamadas.append((indice, total, regra.nome))

    executar_bateria(
        page,
        base_url=edi_mock_url,
        cliente="CLIENTE_FICTICIO",
        ambiente="HOMOLOGACAO",
        regras=regras,
        on_progresso=registrar,
    )

    assert chamadas == [
        (1, 2, "REGRA_UPLOAD_SFTP_01"),
        (2, 2, "REGRA_UPLOAD_FTP_04"),
    ]


def test_bateria_pula_regras_inativas(page: Page, edi_mock_url: str) -> None:
    regras = [
        Regra(nome="REGRA_UPLOAD_SFTP_01", tipo="SFTP_UPLOAD", status="ATIVA"),
        Regra(nome="REGRA_VALIDACAO_LAYOUT_03", tipo="VALIDACAO_LAYOUT", status="INATIVA"),
    ]

    resultado = executar_bateria(
        page,
        base_url=edi_mock_url,
        cliente="CLIENTE_FICTICIO",
        ambiente="HOMOLOGACAO",
        regras=regras,
    )

    assert resultado.total_regras == 1


def test_bateria_reseta_para_tela_de_regras_entre_execucoes(page: Page, edi_mock_url: str) -> None:
    regras = [Regra(nome="REGRA_UPLOAD_SFTP_01", tipo="SFTP_UPLOAD", status="ATIVA")]

    executar_bateria(
        page,
        base_url=edi_mock_url,
        cliente="CLIENTE_FICTICIO",
        ambiente="HOMOLOGACAO",
        regras=regras,
    )

    assert page.url == f"{edi_mock_url}/regras.html"


def test_bateria_com_regra_inexistente_propaga_erro(page: Page, edi_mock_url: str) -> None:
    regras = [Regra(nome="REGRA_FANTASMA", tipo="SFTP_UPLOAD", status="ATIVA")]

    with pytest.raises(RegraNaoEncontradaError):
        executar_bateria(
            page,
            base_url=edi_mock_url,
            cliente="CLIENTE_FICTICIO",
            ambiente="HOMOLOGACAO",
            regras=regras,
        )


def test_status_geral_sucesso_quando_todas_as_execucoes_sao_sucesso() -> None:
    resultado = ResultadoBateria(execucoes=[_execucao_exemplo("SUCESSO")])

    assert resultado.status_geral == "SUCESSO"


def test_status_geral_falha_quando_todas_as_execucoes_sao_falha() -> None:
    resultado = ResultadoBateria(execucoes=[_execucao_exemplo("FALHA")])

    assert resultado.status_geral == "FALHA"


def test_status_geral_parcial_quando_mix_de_sucesso_e_falha() -> None:
    resultado = ResultadoBateria(
        execucoes=[_execucao_exemplo("SUCESSO"), _execucao_exemplo("FALHA")]
    )

    assert resultado.status_geral == "PARCIAL"


def test_duracao_segundos_e_calculada_a_partir_de_data_inicio_e_fim() -> None:
    resultado = ResultadoBateria(
        execucoes=[],
        data_inicio=datetime(2026, 7, 31, 10, 0, 0),
        data_fim=datetime(2026, 7, 31, 10, 0, 42),
    )

    assert resultado.duracao_segundos == 42


def test_status_geral_parcial_quando_lote_vazio() -> None:
    resultado = ResultadoBateria(execucoes=[])

    assert resultado.total_regras == 0
    assert resultado.status_geral == "PARCIAL"
