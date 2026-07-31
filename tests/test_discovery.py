from datetime import datetime

from playwright.sync_api import Page

from edi_test_runner.automation.discovery import descobrir_regras


def test_descobre_todas_as_regras_cadastradas(page: Page, edi_mock_url: str) -> None:
    regras = descobrir_regras(page, base_url=edi_mock_url)

    assert len(regras) == 8
    assert [regra.nome for regra in regras] == [
        "REGRA_UPLOAD_SFTP_01",
        "REGRA_DOWNLOAD_FTPS_02",
        "REGRA_VALIDACAO_LAYOUT_03",
        "REGRA_UPLOAD_FTP_04",
        "REGRA_DOWNLOAD_SFTP_05",
        "REGRA_NOTIFICACAO_EMAIL_06",
        "REGRA_ARQUIVAMENTO_07",
        "REGRA_VALIDACAO_ASSINATURA_08",
    ]


def test_descobre_tipo_e_status_de_cada_regra(page: Page, edi_mock_url: str) -> None:
    regras = descobrir_regras(page, base_url=edi_mock_url)

    primeira_regra = regras[0]
    assert primeira_regra.tipo == "SFTP_UPLOAD"
    assert primeira_regra.status == "ATIVA"
    assert primeira_regra.ultima_execucao == datetime(2026, 7, 28, 9, 12, 0)


def test_filtra_regras_por_status(page: Page, edi_mock_url: str) -> None:
    regras = descobrir_regras(page, base_url=edi_mock_url)

    ativas = [regra for regra in regras if regra.status == "ATIVA"]
    inativas = [regra for regra in regras if regra.status == "INATIVA"]

    assert len(ativas) == 5
    assert len(inativas) == 3


def test_regra_sem_ultima_execucao_fica_none(page: Page, edi_mock_url: str) -> None:
    regras = descobrir_regras(page, base_url=edi_mock_url)

    regra_nunca_executada = next(
        regra for regra in regras if regra.nome == "REGRA_VALIDACAO_ASSINATURA_08"
    )

    assert regra_nunca_executada.ultima_execucao is None
