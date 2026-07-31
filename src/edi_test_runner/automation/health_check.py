from dataclasses import dataclass, field
from typing import Literal

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

from edi_test_runner.automation.login import login

StatusCheck = Literal["OK", "FALHA", "PULADO"]
StatusGeral = Literal["SAUDAVEL", "DEGRADADO", "FALHA", "PULADO"]

CHECKS_CRITICOS = frozenset({"servidor_acessivel", "login_valido"})


@dataclass(frozen=True)
class ResultadoCheck:
    nome: str
    status: StatusCheck
    mensagem: str | None = None


@dataclass(frozen=True)
class HealthCheckReport:
    checks: list[ResultadoCheck] = field(default_factory=list)

    @property
    def status_geral(self) -> StatusGeral:
        criticos = [check for check in self.checks if check.nome in CHECKS_CRITICOS]

        if any(check.status == "FALHA" for check in criticos):
            return "FALHA"
        if all(check.status == "PULADO" for check in self.checks):
            return "PULADO"
        if all(check.status == "OK" for check in self.checks):
            return "SAUDAVEL"
        return "DEGRADADO"

    def pode_executar_testes(self) -> bool:
        return self.status_geral in ("SAUDAVEL", "DEGRADADO")


def verificar_servidor_acessivel(page: Page, base_url: str) -> ResultadoCheck:
    try:
        resposta = page.goto(f"{base_url}/login.html", timeout=5000)
    except PlaywrightError as erro:
        return ResultadoCheck(
            nome="servidor_acessivel",
            status="FALHA",
            mensagem=f"Servidor EDI inacessível: {erro}",
        )

    if resposta is not None and resposta.ok:
        return ResultadoCheck(nome="servidor_acessivel", status="OK")

    status_code = resposta.status if resposta is not None else "sem resposta"
    return ResultadoCheck(
        nome="servidor_acessivel",
        status="FALHA",
        mensagem=f"Servidor EDI retornou status inesperado: {status_code}",
    )


def verificar_login_valido(page: Page, base_url: str, usuario: str, senha: str) -> ResultadoCheck:
    resultado_login = login(page, base_url=base_url, usuario=usuario, senha=senha)

    if resultado_login.sucesso:
        return ResultadoCheck(nome="login_valido", status="OK")

    return ResultadoCheck(
        nome="login_valido",
        status="FALHA",
        mensagem=resultado_login.mensagem or "Falha de login não especificada",
    )


def verificar_servidor_ftp(diretorio_destino: str) -> ResultadoCheck:
    """Stub — TODO(M6+): conectar de verdade contra o servidor FTP/SFTP real.

    Implementação futura:
      - FTP: socket.create_connection() ou ftplib.FTP().connect()
      - SFTP: paramiko.SSHClient().connect()
    """
    return ResultadoCheck(
        nome="servidor_ftp",
        status="PULADO",
        mensagem="Stub — ambiente real não disponível",
    )


def verificar_diretorios(caminhos: list[str]) -> ResultadoCheck:
    """Stub — TODO(M6+): usar pathlib.Path.exists() contra o ambiente real."""
    return ResultadoCheck(
        nome="diretorios",
        status="PULADO",
        mensagem="Stub — ambiente real não disponível",
    )


def executar_health_check(page: Page, base_url: str, usuario: str, senha: str) -> HealthCheckReport:
    checks: list[ResultadoCheck] = []

    check_servidor = verificar_servidor_acessivel(page, base_url)
    checks.append(check_servidor)

    if check_servidor.status == "OK":
        checks.append(verificar_login_valido(page, base_url, usuario, senha))
    else:
        checks.append(
            ResultadoCheck(
                nome="login_valido",
                status="PULADO",
                mensagem="Pulado — servidor EDI inacessível",
            )
        )

    checks.append(verificar_servidor_ftp(diretorio_destino="n/a em ambiente mock"))
    checks.append(verificar_diretorios(caminhos=["n/a em ambiente mock"]))

    return HealthCheckReport(checks=checks)
