import functools
import http.server
import socket
import threading
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pytest
from playwright.sync_api import Browser, Page, sync_playwright

MOCKS_EDI_DIR = Path(__file__).resolve().parent / "mocks" / "edi"


@dataclass(frozen=True)
class Credenciais:
    usuario: str
    senha: str


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser: Browser) -> Iterator[Page]:
    page = browser.new_page()
    yield page
    page.close()


def _servir_diretorio(diretorio: Path) -> Iterator[str]:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(diretorio))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    # server_address é tipado genericamente pelo stdlib (pode ser IPv4/IPv6/unix
    # socket); como o bind acima é sempre IPv4, o cast documenta essa garantia.
    host, port = cast(tuple[str, int], server.server_address)
    yield f"http://{host}:{port}"

    server.shutdown()
    server.server_close()
    thread.join()


@pytest.fixture(scope="session")
def edi_mock_url() -> Iterator[str]:
    yield from _servir_diretorio(MOCKS_EDI_DIR)


@pytest.fixture(scope="session")
def edi_mock_url_sem_login_html() -> Iterator[str]:
    yield from _servir_diretorio(MOCKS_EDI_DIR.parent)


@pytest.fixture
def credenciais_validas() -> Iterator[Credenciais]:
    yield Credenciais(usuario="tester.edi", senha="Senha123!")


@pytest.fixture
def credenciais_invalidas() -> Iterator[Credenciais]:
    yield Credenciais(usuario="tester.edi", senha="senha-errada")


@pytest.fixture
def edi_url_indisponivel() -> Iterator[str]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    porta_livre = sock.getsockname()[1]
    sock.close()

    yield f"http://127.0.0.1:{porta_livre}"
