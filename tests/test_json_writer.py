import json
from datetime import datetime
from pathlib import Path

from edi_test_runner.automation.batch_runner import ResultadoBateria
from edi_test_runner.core.models import Execucao
from edi_test_runner.reporting.json_writer import (
    listar_execucoes,
    salvar_execucao,
    salvar_resultado_bateria,
)


def _execucao_exemplo(execucao_id: str, data_inicio: datetime) -> Execucao:
    return Execucao(
        id=execucao_id,
        cliente="CLIENTE_FICTICIO",
        ambiente="HOMOLOGACAO",
        data_inicio=data_inicio,
        data_fim=data_inicio,
        duracao_segundos=5,
        status="SUCESSO",
        nome_regra="REGRA_UPLOAD_SFTP_01",
        tipo_teste="SFTP_UPLOAD",
        etapas=[],
    )


def test_salvar_execucao_grava_arquivo_e_retorna_caminho(tmp_path: Path) -> None:
    execucao = _execucao_exemplo("abc-123", datetime(2026, 8, 1, 10, 0, 0))

    caminho = salvar_execucao(execucao, diretorio=tmp_path)

    assert caminho.exists()
    assert caminho.name == "execucao_20260801T100000_abc-123.json"


def test_salvar_execucao_grava_json_valido_em_camel_case(tmp_path: Path) -> None:
    execucao = _execucao_exemplo("abc-123", datetime(2026, 8, 1, 10, 0, 0))

    caminho = salvar_execucao(execucao, diretorio=tmp_path)
    conteudo = json.loads(caminho.read_text(encoding="utf-8"))

    assert conteudo["tipoTeste"] == "SFTP_UPLOAD"
    assert conteudo["duracaoSegundos"] == 5


def test_listar_execucoes_retorna_mais_recente_primeiro(tmp_path: Path) -> None:
    salvar_execucao(_execucao_exemplo("mais-antiga", datetime(2026, 8, 1, 9, 0, 0)), tmp_path)
    salvar_execucao(_execucao_exemplo("mais-recente", datetime(2026, 8, 1, 11, 0, 0)), tmp_path)

    execucoes = listar_execucoes(diretorio=tmp_path)

    assert [execucao.id for execucao in execucoes] == ["mais-recente", "mais-antiga"]


def test_listar_execucoes_diretorio_inexistente_retorna_lista_vazia(tmp_path: Path) -> None:
    diretorio_inexistente = tmp_path / "nao-existe"

    assert listar_execucoes(diretorio=diretorio_inexistente) == []


def test_salvar_resultado_bateria_grava_execucoes_e_resumo(tmp_path: Path) -> None:
    execucao_1 = _execucao_exemplo("id-1", datetime(2026, 8, 1, 10, 0, 0))
    execucao_2 = _execucao_exemplo("id-2", datetime(2026, 8, 1, 10, 5, 0))
    resultado = ResultadoBateria(
        execucoes=[execucao_1, execucao_2],
        data_inicio=datetime(2026, 8, 1, 10, 0, 0),
        data_fim=datetime(2026, 8, 1, 10, 10, 0),
    )

    caminho_resumo = salvar_resultado_bateria(resultado, diretorio=tmp_path)
    resumo = json.loads(caminho_resumo.read_text(encoding="utf-8"))

    assert resumo["statusGeral"] == "SUCESSO"
    assert resumo["totalRegras"] == 2
    assert resumo["execucaoIds"] == ["id-1", "id-2"]
    assert len(listar_execucoes(diretorio=tmp_path)) == 2
