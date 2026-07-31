from datetime import datetime
from typing import Literal

from playwright.sync_api import Page
from pydantic import BaseModel

StatusRegra = Literal["ATIVA", "INATIVA"]


class Regra(BaseModel):
    nome: str
    tipo: str
    status: StatusRegra
    ultima_execucao: datetime | None = None


def descobrir_regras(page: Page, base_url: str) -> list[Regra]:
    page.goto(f"{base_url}/regras.html")

    linhas = page.locator(".linha-regra")
    total_linhas = linhas.count()

    regras: list[Regra] = []
    for indice in range(total_linhas):
        linha = linhas.nth(indice)
        ultima_execucao_texto = linha.locator(".regra-ultima-execucao").inner_text()

        regras.append(
            Regra(
                nome=linha.locator(".regra-nome").inner_text(),
                tipo=linha.locator(".regra-tipo").inner_text(),
                status=linha.locator(".regra-status").inner_text(),
                ultima_execucao=ultima_execucao_texto or None,
            )
        )

    return regras
