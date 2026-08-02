import json
from datetime import datetime
from pathlib import Path

from edi_test_runner.core.models import Execucao
from edi_test_runner.reporting.dashboard_publisher import publicar_execucoes_para_dashboard
from edi_test_runner.reporting.json_writer import salvar_execucao


def _execucao_exemplo(execucao_id: str) -> Execucao:
    return Execucao(
        id=execucao_id,
        cliente="CLIENTE_FICTICIO",
        ambiente="HOMOLOGACAO",
        data_inicio=datetime(2026, 8, 2, 10, 0, 0),
        data_fim=datetime(2026, 8, 2, 10, 0, 5),
        duracao_segundos=5,
        status="SUCESSO",
        nome_regra="REGRA_UPLOAD_SFTP_01",
        tipo_teste="SFTP_UPLOAD",
        etapas=[],
    )


def test_publicar_gera_array_json_com_todas_as_execucoes(tmp_path: Path) -> None:
    diretorio_execucoes = tmp_path / "execucoes"
    diretorio_dashboard = tmp_path / "dashboard_assets"

    salvar_execucao(_execucao_exemplo("id-1"), diretorio=diretorio_execucoes)
    salvar_execucao(_execucao_exemplo("id-2"), diretorio=diretorio_execucoes)

    resultado = publicar_execucoes_para_dashboard(
        diretorio_dashboard_assets=diretorio_dashboard,
        diretorio_execucoes=diretorio_execucoes,
    )

    assert resultado.caminho == diretorio_dashboard / "execucoes.json"
    assert resultado.total_execucoes == 2

    dados = json.loads(resultado.caminho.read_text(encoding="utf-8"))
    assert isinstance(dados, list)
    assert len(dados) == 2
    assert {item["id"] for item in dados} == {"id-1", "id-2"}


def test_publicar_usa_camel_case_compativel_com_angular(tmp_path: Path) -> None:
    diretorio_execucoes = tmp_path / "execucoes"
    diretorio_dashboard = tmp_path / "dashboard_assets"
    salvar_execucao(_execucao_exemplo("id-1"), diretorio=diretorio_execucoes)

    resultado = publicar_execucoes_para_dashboard(
        diretorio_dashboard_assets=diretorio_dashboard,
        diretorio_execucoes=diretorio_execucoes,
    )

    dados = json.loads(resultado.caminho.read_text(encoding="utf-8"))
    execucao = dados[0]

    assert execucao["nomeRegra"] == "REGRA_UPLOAD_SFTP_01"
    assert execucao["tipoTeste"] == "SFTP_UPLOAD"
    assert execucao["duracaoSegundos"] == 5
    assert execucao["totalEtapas"] == 0
    assert execucao["etapasComSucesso"] == 0


def test_publicar_com_diretorio_execucoes_vazio_gera_array_vazio(tmp_path: Path) -> None:
    diretorio_execucoes = tmp_path / "execucoes-vazio"
    diretorio_dashboard = tmp_path / "dashboard_assets"

    resultado = publicar_execucoes_para_dashboard(
        diretorio_dashboard_assets=diretorio_dashboard,
        diretorio_execucoes=diretorio_execucoes,
    )

    assert resultado.total_execucoes == 0
    assert json.loads(resultado.caminho.read_text(encoding="utf-8")) == []


def test_publicar_cria_diretorio_dashboard_se_nao_existir(tmp_path: Path) -> None:
    diretorio_dashboard = tmp_path / "nao-existe-ainda" / "assets"

    resultado = publicar_execucoes_para_dashboard(
        diretorio_dashboard_assets=diretorio_dashboard,
        diretorio_execucoes=tmp_path / "execucoes-vazio",
    )

    assert diretorio_dashboard.exists()
    assert resultado.caminho.exists()
