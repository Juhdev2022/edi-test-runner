from datetime import datetime
from pathlib import Path
from uuid import uuid4

from edi_test_runner.automation.batch_runner import ResultadoBateria
from edi_test_runner.core.models import EtapaExecucao, Execucao

REPORTS_DIR = Path("data/reports")


def _slug_timestamp(momento: datetime) -> str:
    return momento.strftime("%Y%m%dT%H%M%S")


def _escapar_celula(texto: str) -> str:
    return texto.replace("|", "\\|").replace("\n", " ")


def montar_log_completo(execucao: Execucao) -> str:
    linhas = [
        f"[{execucao.data_inicio.isoformat()}] Início — {execucao.tipo_teste} "
        f"({execucao.cliente} / {execucao.ambiente})"
    ]
    for etapa in execucao.etapas:
        detalhe = f": {etapa.mensagem}" if etapa.mensagem else ""
        linhas.append(
            f"  {etapa.ordem}. {etapa.nome} — {etapa.status} ({etapa.duracao_segundos}s){detalhe}"
        )
    linhas.append(f"[{execucao.data_fim.isoformat()}] Fim — status: {execucao.status}")
    return "\n".join(linhas)


def _tabela_etapas(etapas: list[EtapaExecucao]) -> str:
    linhas = ["| # | Etapa | Status | Duração (s) | Mensagem |", "|---|---|---|---|---|"]
    for etapa in etapas:
        mensagem = _escapar_celula(etapa.mensagem) if etapa.mensagem else "—"
        nome = _escapar_celula(etapa.nome)
        linhas.append(
            f"| {etapa.ordem} | {nome} | {etapa.status} | {etapa.duracao_segundos} | {mensagem} |"
        )
    return "\n".join(linhas)


def gerar_report_execucao(execucao: Execucao) -> str:
    resultado_texto = execucao.observacoes or "Execução concluída com sucesso."

    return (
        f"# Report de execução — {execucao.tipo_teste}\n\n"
        f"**Status:** {execucao.status}\n"
        f"**Cliente:** {execucao.cliente}\n"
        f"**Ambiente:** {execucao.ambiente}\n"
        f"**Início:** {execucao.data_inicio.isoformat()}\n"
        f"**Fim:** {execucao.data_fim.isoformat()}\n"
        f"**Duração:** {execucao.duracao_segundos}s\n"
        f"**ID da execução:** {execucao.id}\n\n"
        f"## Resultado\n\n"
        f"{resultado_texto}\n\n"
        f"## Etapas\n\n"
        f"{_tabela_etapas(execucao.etapas)}\n\n"
        f"## Log completo\n\n"
        f"```\n{montar_log_completo(execucao)}\n```\n"
    )


def gerar_report_bateria(resultado: ResultadoBateria) -> str:
    cabecalho = (
        f"# Report de bateria — {resultado.status_geral}\n\n"
        f"**Início:** {resultado.data_inicio.isoformat()}\n"
        f"**Fim:** {resultado.data_fim.isoformat()}\n"
        f"**Duração total:** {resultado.duracao_segundos}s\n"
        f"**Total de regras:** {resultado.total_regras} "
        f"(sucesso: {resultado.total_sucesso}, falha: {resultado.total_falha})\n\n"
        f"---\n"
    )
    secoes = [gerar_report_execucao(execucao) for execucao in resultado.execucoes]
    return cabecalho + "\n---\n".join(secoes)


def salvar_report(conteudo: str, nome_arquivo: str, diretorio: Path = REPORTS_DIR) -> Path:
    diretorio.mkdir(parents=True, exist_ok=True)
    caminho = diretorio / nome_arquivo
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho


def salvar_report_execucao(execucao: Execucao, diretorio: Path = REPORTS_DIR) -> Path:
    nome_arquivo = f"report_execucao_{_slug_timestamp(execucao.data_inicio)}_{execucao.id}.md"
    return salvar_report(gerar_report_execucao(execucao), nome_arquivo, diretorio)


def salvar_report_bateria(resultado: ResultadoBateria, diretorio: Path = REPORTS_DIR) -> Path:
    nome_arquivo = f"report_bateria_{_slug_timestamp(resultado.data_inicio)}_{uuid4()}.md"
    return salvar_report(gerar_report_bateria(resultado), nome_arquivo, diretorio)
