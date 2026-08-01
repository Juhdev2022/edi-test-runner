import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from edi_test_runner.automation.batch_runner import ResultadoBateria
from edi_test_runner.core.models import Execucao

# Assume que o processo roda a partir da raiz do projeto (mesmo padrão de
# `uv run pytest` / `uv run streamlit run ...` já usado neste projeto).
EXECUCOES_DIR = Path("data/execucoes")

# Execucao serializa esses computed_field na saída (model_dump_json), mas
# extra="forbid" os rejeita na entrada (não são campos settáveis de verdade -
# ver test_computed_fields_nao_aceitam_valor_na_construcao do M2). Precisam
# ser descartados antes de reler um JSON que nós mesmos produzimos.
_CAMPOS_COMPUTADOS = ("totalEtapas", "etapasComSucesso")


def _slug_timestamp(momento: datetime) -> str:
    return momento.strftime("%Y%m%dT%H%M%S")


def salvar_execucao(execucao: Execucao, diretorio: Path = EXECUCOES_DIR) -> Path:
    diretorio.mkdir(parents=True, exist_ok=True)

    nome_arquivo = f"execucao_{_slug_timestamp(execucao.data_inicio)}_{execucao.id}.json"
    caminho = diretorio / nome_arquivo
    caminho.write_text(execucao.model_dump_json(by_alias=True, indent=2), encoding="utf-8")
    return caminho


def salvar_resultado_bateria(resultado: ResultadoBateria, diretorio: Path = EXECUCOES_DIR) -> Path:
    diretorio.mkdir(parents=True, exist_ok=True)

    for execucao in resultado.execucoes:
        salvar_execucao(execucao, diretorio=diretorio)

    resumo = {
        "dataInicio": resultado.data_inicio.isoformat(),
        "dataFim": resultado.data_fim.isoformat(),
        "statusGeral": resultado.status_geral,
        "totalRegras": resultado.total_regras,
        "totalSucesso": resultado.total_sucesso,
        "totalFalha": resultado.total_falha,
        "duracaoSegundos": resultado.duracao_segundos,
        "execucaoIds": [execucao.id for execucao in resultado.execucoes],
    }

    nome_arquivo = f"bateria_{_slug_timestamp(resultado.data_inicio)}_{uuid4()}.json"
    caminho = diretorio / nome_arquivo
    caminho.write_text(json.dumps(resumo, indent=2, ensure_ascii=False), encoding="utf-8")
    return caminho


def listar_execucoes(diretorio: Path = EXECUCOES_DIR) -> list[Execucao]:
    if not diretorio.exists():
        return []

    arquivos = sorted(diretorio.glob("execucao_*.json"), reverse=True)

    execucoes = []
    for arquivo in arquivos:
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
        for campo in _CAMPOS_COMPUTADOS:
            dados.pop(campo, None)
        execucoes.append(Execucao.model_validate(dados))

    return execucoes
