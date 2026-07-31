from dataclasses import dataclass

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


@dataclass(frozen=True)
class ResultadoLogin:
    sucesso: bool
    mensagem: str | None = None


def login(page: Page, base_url: str, usuario: str, senha: str) -> ResultadoLogin:
    page.goto(f"{base_url}/login.html")
    page.fill("#usuario", usuario)
    page.fill("#senha", senha)
    page.click("#entrar")

    try:
        page.wait_for_url(f"{base_url}/dashboard.html", timeout=3000)
        return ResultadoLogin(sucesso=True)
    except PlaywrightTimeoutError:
        mensagem = page.locator("#erro-login").inner_text()
        return ResultadoLogin(sucesso=False, mensagem=mensagem)
