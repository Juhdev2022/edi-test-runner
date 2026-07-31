import pytest

from edi_test_runner.core.config import carregar_configuracao_edi


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
