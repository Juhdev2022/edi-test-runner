from collections.abc import Iterator
from dataclasses import dataclass

import pytest
from playwright.sync_api import Page

from edi_test_runner.automation.login import login


@dataclass(frozen=True)
class Credenciais:
    usuario: str
    senha: str


@pytest.fixture
def credenciais_validas() -> Iterator[Credenciais]:
    yield Credenciais(usuario="tester.edi", senha="Senha123!")


@pytest.fixture
def credenciais_invalidas() -> Iterator[Credenciais]:
    yield Credenciais(usuario="tester.edi", senha="senha-errada")


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
