from playwright.sync_api import Page

from edi_test_runner.automation.health_check import (
    HealthCheckReport,
    ResultadoCheck,
    executar_health_check,
    verificar_diretorios,
    verificar_servidor_acessivel,
    verificar_servidor_ftp,
)
from tests.conftest import Credenciais


def test_health_check_completo_com_ambiente_saudavel(
    page: Page, edi_mock_url: str, credenciais_validas: Credenciais
) -> None:
    relatorio = executar_health_check(
        page,
        base_url=edi_mock_url,
        usuario=credenciais_validas.usuario,
        senha=credenciais_validas.senha,
    )

    nomes_e_status = {check.nome: check.status for check in relatorio.checks}
    assert nomes_e_status["servidor_acessivel"] == "OK"
    assert nomes_e_status["login_valido"] == "OK"
    assert nomes_e_status["servidor_ftp"] == "PULADO"
    assert nomes_e_status["diretorios"] == "PULADO"

    assert relatorio.status_geral == "DEGRADADO"
    assert relatorio.pode_executar_testes() is True


def test_health_check_aborta_com_servidor_inacessivel(
    page: Page, edi_url_indisponivel: str, credenciais_validas: Credenciais
) -> None:
    relatorio = executar_health_check(
        page,
        base_url=edi_url_indisponivel,
        usuario=credenciais_validas.usuario,
        senha=credenciais_validas.senha,
    )

    check_servidor = next(c for c in relatorio.checks if c.nome == "servidor_acessivel")
    check_login = next(c for c in relatorio.checks if c.nome == "login_valido")

    assert check_servidor.status == "FALHA"
    assert check_login.status == "PULADO"
    assert check_login.mensagem == "Pulado — servidor EDI inacessível"

    assert relatorio.status_geral == "FALHA"
    assert relatorio.pode_executar_testes() is False


def test_health_check_com_credencial_invalida_reporta_erro_distinto_de_infra(
    page: Page, edi_mock_url: str, credenciais_invalidas: Credenciais
) -> None:
    relatorio = executar_health_check(
        page,
        base_url=edi_mock_url,
        usuario=credenciais_invalidas.usuario,
        senha=credenciais_invalidas.senha,
    )

    check_servidor = next(c for c in relatorio.checks if c.nome == "servidor_acessivel")
    check_login = next(c for c in relatorio.checks if c.nome == "login_valido")

    assert check_servidor.status == "OK"
    assert check_login.status == "FALHA"
    assert check_login.mensagem == "Usuário ou senha inválidos."

    assert relatorio.status_geral == "FALHA"
    assert relatorio.pode_executar_testes() is False


def test_servidor_acessivel_reporta_falha_em_status_inesperado(
    page: Page, edi_mock_url_sem_login_html: str
) -> None:
    resultado = verificar_servidor_acessivel(page, base_url=edi_mock_url_sem_login_html)

    assert resultado.status == "FALHA"
    assert resultado.mensagem is not None
    assert "404" in resultado.mensagem


def test_stub_servidor_ftp_retorna_pulado() -> None:
    resultado = verificar_servidor_ftp(diretorio_destino="/qualquer")

    assert resultado.status == "PULADO"
    assert resultado.mensagem is not None


def test_stub_diretorios_retorna_pulado() -> None:
    resultado = verificar_diretorios(caminhos=["/qualquer"])

    assert resultado.status == "PULADO"
    assert resultado.mensagem is not None


def test_status_geral_saudavel_quando_todos_os_checks_passam() -> None:
    relatorio = HealthCheckReport(
        checks=[
            ResultadoCheck(nome="servidor_acessivel", status="OK"),
            ResultadoCheck(nome="login_valido", status="OK"),
            ResultadoCheck(nome="servidor_ftp", status="OK"),
            ResultadoCheck(nome="diretorios", status="OK"),
        ]
    )

    assert relatorio.status_geral == "SAUDAVEL"
    assert relatorio.pode_executar_testes() is True


def test_status_geral_pulado_quando_nenhum_check_executou() -> None:
    relatorio = HealthCheckReport(
        checks=[
            ResultadoCheck(nome="servidor_ftp", status="PULADO"),
            ResultadoCheck(nome="diretorios", status="PULADO"),
        ]
    )

    assert relatorio.status_geral == "PULADO"
    assert relatorio.pode_executar_testes() is False
