from pathlib import Path

import pytest
from pydantic import ValidationError

from edi_test_runner.core.config import carregar_configuracao_edi, obter_dashboard_assets_dir


def test_carrega_configuracao_das_variaveis_de_ambiente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EDI_BASE_URL", "http://localhost:8000")
    monkeypatch.setenv("EDI_USUARIO", "usuario_ficticio")
    monkeypatch.setenv("EDI_SENHA", "senha_ficticia")
    monkeypatch.setenv("EDI_CLIENTE", "CLIENTE_FICTICIO")
    monkeypatch.setenv("EDI_AMBIENTE", "HOMOLOGACAO")

    configuracao = carregar_configuracao_edi()

    assert configuracao.base_url == "http://localhost:8000"
    assert configuracao.usuario == "usuario_ficticio"
    assert configuracao.senha == "senha_ficticia"
    assert configuracao.cliente == "CLIENTE_FICTICIO"
    assert configuracao.ambiente == "HOMOLOGACAO"


def test_variavel_de_ambiente_faltando_lanca_key_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EDI_BASE_URL", raising=False)
    monkeypatch.delenv("EDI_USUARIO", raising=False)
    monkeypatch.delenv("EDI_SENHA", raising=False)
    monkeypatch.delenv("EDI_CLIENTE", raising=False)
    monkeypatch.delenv("EDI_AMBIENTE", raising=False)

    with pytest.raises(KeyError):
        carregar_configuracao_edi()


def test_ambiente_invalido_lanca_validation_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EDI_BASE_URL", "http://localhost:8000")
    monkeypatch.setenv("EDI_USUARIO", "usuario_ficticio")
    monkeypatch.setenv("EDI_SENHA", "senha_ficticia")
    monkeypatch.setenv("EDI_CLIENTE", "CLIENTE_FICTICIO")
    monkeypatch.setenv("EDI_AMBIENTE", "AMBIENTE_QUE_NAO_EXISTE")

    with pytest.raises(ValidationError):
        carregar_configuracao_edi()


def test_obter_dashboard_assets_dir_retorna_none_quando_nao_configurado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DASHBOARD_ASSETS_DIR", raising=False)

    assert obter_dashboard_assets_dir() is None


def test_obter_dashboard_assets_dir_retorna_path_quando_configurado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DASHBOARD_ASSETS_DIR", "/tmp/algum-lugar")

    assert obter_dashboard_assets_dir() == Path("/tmp/algum-lugar")
