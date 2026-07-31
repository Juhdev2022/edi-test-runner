import pytest
from playwright.sync_api import Page

from edi_test_runner.automation.discovery import Regra
from edi_test_runner.automation.executor import (
    RegraNaoEncontradaError,
    _montar_observacoes,
    executar_regra,
)
from edi_test_runner.core.models import EtapaExecucao


def test_executa_regra_com_sucesso_completo(page: Page, edi_mock_url: str) -> None:
    regra = Regra(nome="REGRA_UPLOAD_SFTP_01", tipo="SFTP_UPLOAD", status="ATIVA")

    execucao = executar_regra(
        page,
        base_url=edi_mock_url,
        cliente="CLIENTE_FICTICIO",
        ambiente="HOMOLOGACAO",
        regra=regra,
    )

    assert execucao.status == "SUCESSO"
    assert execucao.cliente == "CLIENTE_FICTICIO"
    assert execucao.ambiente == "HOMOLOGACAO"
    assert execucao.tipo_teste == "SFTP_UPLOAD"
    assert execucao.observacoes is None
    assert len(execucao.etapas) == 4
    assert all(etapa.status == "SUCESSO" for etapa in execucao.etapas)
    assert execucao.data_fim >= execucao.data_inicio
    assert execucao.duracao_segundos >= 0


def test_executa_regra_com_falha_e_cascata_de_puladas(page: Page, edi_mock_url: str) -> None:
    regra = Regra(nome="REGRA_UPLOAD_SFTP_02", tipo="SFTP_UPLOAD", status="ATIVA")

    execucao = executar_regra(
        page,
        base_url=edi_mock_url,
        cliente="CLIENTE_FICTICIO",
        ambiente="HOMOLOGACAO",
        regra=regra,
    )

    assert execucao.status == "FALHA"
    assert [etapa.status for etapa in execucao.etapas] == [
        "SUCESSO",
        "FALHA",
        "PULADA",
        "PULADA",
    ]

    etapa_falha = execucao.etapas[1]
    assert etapa_falha.nome == "Conectar SFTP"
    assert etapa_falha.mensagem == "Certificado FTPS expirado"

    assert execucao.observacoes == "Falha na etapa 'Conectar SFTP': Certificado FTPS expirado"


def test_observacoes_none_quando_status_falha_sem_etapa_com_falha_explicita() -> None:
    etapas = [
        EtapaExecucao(ordem=1, nome="Preparar arquivo local", status="PULADA", duracao_segundos=0)
    ]

    assert _montar_observacoes(etapas, "FALHA") is None


def test_regra_inexistente_levanta_erro_claro(page: Page, edi_mock_url: str) -> None:
    regra = Regra(nome="REGRA_INEXISTENTE", tipo="SFTP_UPLOAD", status="ATIVA")

    with pytest.raises(RegraNaoEncontradaError):
        executar_regra(
            page,
            base_url=edi_mock_url,
            cliente="CLIENTE_FICTICIO",
            ambiente="HOMOLOGACAO",
            regra=regra,
        )
