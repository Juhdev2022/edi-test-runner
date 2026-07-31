from playwright.sync_api import Page

from edi_test_runner.automation.login import login
from tests.conftest import Credenciais


def test_login_com_credenciais_validas_redireciona_para_dashboard(
    page: Page, edi_mock_url: str, credenciais_validas: Credenciais
) -> None:
    resultado = login(
        page,
        base_url=edi_mock_url,
        usuario=credenciais_validas.usuario,
        senha=credenciais_validas.senha,
    )

    assert resultado.sucesso is True
    assert resultado.mensagem is None
    assert page.url == f"{edi_mock_url}/dashboard.html"


def test_login_com_credenciais_invalidas_retorna_erro(
    page: Page, edi_mock_url: str, credenciais_invalidas: Credenciais
) -> None:
    resultado = login(
        page,
        base_url=edi_mock_url,
        usuario=credenciais_invalidas.usuario,
        senha=credenciais_invalidas.senha,
    )

    assert resultado.sucesso is False
    assert resultado.mensagem == "Usuário ou senha inválidos."
