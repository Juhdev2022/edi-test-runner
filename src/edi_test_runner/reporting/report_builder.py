from datetime import datetime
from pathlib import Path
from uuid import uuid4

from edi_test_runner.automation.batch_runner import ResultadoBateria
from edi_test_runner.core.models import EtapaExecucao, Execucao

REPORTS_DIR = Path("data/reports")


class CardBugNaoAplicavelError(Exception):
    pass


def _slug_timestamp(momento: datetime) -> str:
    return momento.strftime("%Y%m%dT%H%M%S")


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


def _etapa_referencia_da_falha(etapas: list[EtapaExecucao]) -> EtapaExecucao:
    etapa_falha = next((etapa for etapa in etapas if etapa.status == "FALHA"), None)
    if etapa_falha is not None:
        return etapa_falha

    # Defensivo: cascata de PULADA sem nenhuma etapa FALHA explícita não
    # deveria acontecer com o executor atual (PULADA só existe como
    # consequência de uma FALHA anterior), mas evita presumir e quebrar
    # silenciosamente se algum dia esse invariante mudar.
    etapa_pulada = next((etapa for etapa in etapas if etapa.status == "PULADA"), None)
    if etapa_pulada is not None:
        return etapa_pulada

    raise CardBugNaoAplicavelError("Não foi possível identificar a etapa que causou a falha.")


def gerar_card_bug(execucao: Execucao) -> str:
    if execucao.status != "FALHA":
        raise CardBugNaoAplicavelError("Card de bug só se aplica a execuções com falha.")

    etapa_referencia = _etapa_referencia_da_falha(execucao.etapas)
    mensagem_erro = etapa_referencia.mensagem or "(sem mensagem registrada)"
    data_formatada = execucao.data_inicio.strftime("%d/%m/%Y %H:%M:%S")
    duracao_ate_falha = sum(
        etapa.duracao_segundos for etapa in execucao.etapas if etapa.ordem <= etapa_referencia.ordem
    )

    return (
        f"Nome: [BUG] [PREENCHER TÍTULO] — Regra {execucao.nome_regra} "
        f"falhou na etapa {etapa_referencia.nome}\n\n"
        f"Resumo do problema:\n"
        f"[PREENCHER RESUMO EM 1-2 FRASES]\n\n"
        f"Comportamento atual:\n"
        f"Execução da regra {execucao.nome_regra} (tipo {execucao.tipo_teste}) falhou na "
        f'etapa "{etapa_referencia.nome}" com a mensagem: "{mensagem_erro}".\n'
        f"Ambiente: {execucao.ambiente}\n"
        f"Cliente: {execucao.cliente}\n"
        f"Data/hora: {data_formatada}\n\n"
        f"Comportamento esperado:\n"
        f"[PREENCHER O QUE DEVERIA ACONTECER]\n\n"
        f"Passos para reproduzir:\n"
        f"1. Configurar regra {execucao.nome_regra} (tipo {execucao.tipo_teste}) "
        f"no ambiente {execucao.ambiente}\n"
        f"2. Executar a regra\n"
        f'3. Verificar que falha na etapa "{etapa_referencia.nome}"\n\n'
        f"Evidências:\n"
        f"{montar_log_completo(execucao)}\n\n"
        f"Data/hora da execução: {data_formatada}\n"
        f"Duração até a falha: {duracao_ate_falha}s\n\n"
        f"Criticidade: [PREENCHER]\n"
    )


def gerar_report_bateria(resultado: ResultadoBateria) -> str:
    cabecalho = (
        f"# Resumo da bateria — {resultado.status_geral}\n\n"
        f"**Início:** {resultado.data_inicio.isoformat()}\n"
        f"**Fim:** {resultado.data_fim.isoformat()}\n"
        f"**Duração total:** {resultado.duracao_segundos}s\n"
        f"**Total de regras:** {resultado.total_regras} "
        f"(sucesso: {resultado.total_sucesso}, falha: {resultado.total_falha})\n\n"
        f"---\n"
    )
    cards = [
        gerar_card_bug(execucao) for execucao in resultado.execucoes if execucao.status == "FALHA"
    ]
    if not cards:
        return cabecalho + "\nNenhuma falha nesta bateria — sem cards de bug a gerar.\n"

    return cabecalho + "\n---\n".join(cards)


def salvar_report(conteudo: str, nome_arquivo: str, diretorio: Path = REPORTS_DIR) -> Path:
    diretorio.mkdir(parents=True, exist_ok=True)
    caminho = diretorio / nome_arquivo
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho


def salvar_card_bug(execucao: Execucao, diretorio: Path = REPORTS_DIR) -> Path:
    nome_arquivo = f"card_bug_{_slug_timestamp(execucao.data_inicio)}_{execucao.id}.md"
    return salvar_report(gerar_card_bug(execucao), nome_arquivo, diretorio)


def salvar_report_bateria(resultado: ResultadoBateria, diretorio: Path = REPORTS_DIR) -> Path:
    nome_arquivo = f"resumo_bateria_{_slug_timestamp(resultado.data_inicio)}_{uuid4()}.md"
    return salvar_report(gerar_report_bateria(resultado), nome_arquivo, diretorio)
