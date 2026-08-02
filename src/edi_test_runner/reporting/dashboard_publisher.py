import json
from dataclasses import dataclass
from pathlib import Path

from edi_test_runner.reporting.json_writer import EXECUCOES_DIR, listar_execucoes


@dataclass(frozen=True)
class ResultadoPublicacao:
    caminho: Path
    total_execucoes: int


def publicar_execucoes_para_dashboard(
    diretorio_dashboard_assets: Path, diretorio_execucoes: Path = EXECUCOES_DIR
) -> ResultadoPublicacao:
    execucoes = listar_execucoes(diretorio=diretorio_execucoes)
    dados = [execucao.model_dump(mode="json", by_alias=True) for execucao in execucoes]

    diretorio_dashboard_assets.mkdir(parents=True, exist_ok=True)
    caminho = diretorio_dashboard_assets / "execucoes.json"
    caminho.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")

    return ResultadoPublicacao(caminho=caminho, total_execucoes=len(execucoes))
