from collections.abc import Callable, Iterator
from contextlib import contextmanager

import streamlit as st
from playwright.sync_api import Page, sync_playwright

from edi_test_runner.automation.batch_runner import ResultadoBateria, executar_bateria
from edi_test_runner.automation.discovery import Regra, descobrir_regras
from edi_test_runner.automation.health_check import HealthCheckReport, executar_health_check
from edi_test_runner.core.config import ConfiguracaoEdi, carregar_configuracao_edi
from edi_test_runner.core.models import Execucao
from edi_test_runner.reporting.json_writer import listar_execucoes, salvar_resultado_bateria
from edi_test_runner.reporting.report_builder import (
    gerar_card_bug,
    montar_log_completo,
    salvar_card_bug,
)

_NOMES_AMIGAVEIS_CHECK = {
    "servidor_acessivel": "servidor EDI",
    "login_valido": "login",
    "servidor_ftp": "FTP/SFTP",
    "diretorios": "diretórios",
}

_COR_STATUS_ETAPA = {"SUCESSO": "green", "FALHA": "red", "PULADA": "gray"}
_COR_STATUS_EXECUCAO = {"SUCESSO": "green", "FALHA": "red", "PARCIAL": "orange"}


@contextmanager
def _sessao_playwright(headless: bool) -> Iterator[Page]:
    # Não cacheado entre reruns: a API síncrona do Playwright prende a conexão
    # à thread que a criou, e o Streamlit reexecuta cada interação em threads
    # diferentes (confirmado rodando o app de verdade — greenlet.error:
    # "Cannot switch to a different thread" ao tentar reusar uma Page
    # cacheada). Abrir e fechar tudo dentro da mesma execução de script evita
    # o problema por completo, ao custo de alguns segundos de start-up do
    # navegador por ação.
    with sync_playwright() as playwright:
        # slow_mo só quando o navegador é visível: dá pra acompanhar os
        # cliques a olho nu. Headless continua na velocidade máxima.
        slow_mo = 500 if not headless else None
        browser = playwright.chromium.launch(headless=headless, slow_mo=slow_mo)
        try:
            yield browser.new_page()
        finally:
            browser.close()


def _inicializar_estado() -> None:
    valores_padrao: dict[str, object] = {
        "regras_descobertas": [],
        "ultimo_resultado": None,
        "ultimo_health_check": None,
        "mostrar_navegador": False,
        "solicitar_execucao": False,
        "regras_para_rodar": [],
    }
    for chave, valor in valores_padrao.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor


def _renderizar_sidebar(config: ConfiguracaoEdi) -> None:
    st.sidebar.header("EDI Test Runner")
    st.sidebar.markdown(f"**Cliente:** {config.cliente}")
    st.sidebar.markdown(f"**Ambiente:** {config.ambiente}")

    st.sidebar.checkbox("Mostrar navegador durante execução", key="mostrar_navegador")

    st.sidebar.divider()

    if st.sidebar.button("Verificar conexão"):
        with _sessao_playwright(not st.session_state.mostrar_navegador) as pagina:
            st.session_state.ultimo_health_check = executar_health_check(
                pagina, config.base_url, config.usuario, config.senha
            )

    _renderizar_status_conexao(st.session_state.ultimo_health_check)

    st.sidebar.divider()

    if st.sidebar.button("Descobrir regras"):
        with _sessao_playwright(not st.session_state.mostrar_navegador) as pagina:
            st.session_state.regras_descobertas = descobrir_regras(pagina, config.base_url)

    regras = st.session_state.regras_descobertas
    if regras:
        nomes_ativos = [regra.nome for regra in regras if regra.status == "ATIVA"]
        selecionadas = st.sidebar.multiselect(
            "Regras a executar",
            options=[regra.nome for regra in regras],
            default=nomes_ativos,
        )

        if st.sidebar.button("Executar bateria", type="primary"):
            st.session_state.regras_para_rodar = [
                regra for regra in regras if regra.nome in selecionadas
            ]
            st.session_state.solicitar_execucao = True
            st.rerun()


def _renderizar_status_conexao(relatorio: HealthCheckReport | None) -> None:
    if relatorio is None:
        st.sidebar.info("Conexão ainda não verificada.")
        return

    if relatorio.pode_executar_testes():
        st.sidebar.success(f"Status: {relatorio.status_geral}")
    else:
        st.sidebar.error(f"Status: {relatorio.status_geral}")

    if relatorio.status_geral == "DEGRADADO":
        st.sidebar.info(_explicar_degradado(relatorio))


def _explicar_degradado(relatorio: HealthCheckReport) -> str:
    ok = [_NOMES_AMIGAVEIS_CHECK[c.nome] for c in relatorio.checks if c.status == "OK"]
    pendentes = [_NOMES_AMIGAVEIS_CHECK[c.nome] for c in relatorio.checks if c.status != "OK"]

    partes = []
    if ok:
        partes.append(f"{' e '.join(ok)} OK")
    if pendentes:
        partes.append(f"checks de {' e '.join(pendentes)} pulados (aguardam ambiente real)")

    return "DEGRADADO — " + "; ".join(partes) + "."


def _rodar_bateria_com_progresso(config: ConfiguracaoEdi, regras: list[Regra]) -> None:
    barra = st.progress(0.0)
    status_texto = st.empty()

    def _atualizar_progresso(indice: int, total: int, regra: Regra) -> None:
        barra.progress(indice / total)
        status_texto.text(f"Executando {indice}/{total}: {regra.nome}")

    with _sessao_playwright(not st.session_state.mostrar_navegador) as pagina:
        resultado = executar_bateria(
            pagina,
            base_url=config.base_url,
            cliente=config.cliente,
            ambiente=config.ambiente,
            regras=regras,
            on_progresso=_atualizar_progresso,
        )

    salvar_resultado_bateria(resultado)
    st.session_state.ultimo_resultado = resultado

    status_texto.text("Bateria concluída.")


def _renderizar_aba_execucao(config: ConfiguracaoEdi) -> None:
    if st.session_state.solicitar_execucao:
        st.session_state.solicitar_execucao = False
        _rodar_bateria_com_progresso(config, st.session_state.regras_para_rodar)

    resultado: ResultadoBateria | None = st.session_state.ultimo_resultado

    if resultado is None:
        st.info("Nenhuma bateria executada ainda.")
        st.caption("Configure detalhes na barra lateral →")

        if st.button("Executar bateria completa agora", type="primary"):
            regras = st.session_state.regras_descobertas
            if not regras:
                with _sessao_playwright(not st.session_state.mostrar_navegador) as pagina:
                    regras = descobrir_regras(pagina, config.base_url)
                st.session_state.regras_descobertas = regras

            st.session_state.regras_para_rodar = [
                regra for regra in regras if regra.status == "ATIVA"
            ]
            st.session_state.solicitar_execucao = True
            st.rerun()
        return

    _renderizar_resultado_bateria(resultado)


def _renderizar_resultado_bateria(resultado: ResultadoBateria) -> None:
    coluna_total, coluna_sucesso, coluna_falha = st.columns(3)
    coluna_total.metric("Total de regras", resultado.total_regras)
    coluna_sucesso.metric("Sucesso", resultado.total_sucesso)
    coluna_falha.metric("Falha", resultado.total_falha)

    cor_geral = _COR_STATUS_EXECUCAO.get(resultado.status_geral, "gray")
    st.markdown(f"**Status geral:** :{cor_geral}[{resultado.status_geral}]")

    for execucao in resultado.execucoes:
        with st.expander(f"{execucao.nome_regra} — {execucao.status}"):
            if execucao.observacoes:
                st.write(execucao.observacoes)

            for etapa in execucao.etapas:
                cor = _COR_STATUS_ETAPA.get(etapa.status, "gray")
                linha = f"{etapa.ordem}. {etapa.nome} — :{cor}[{etapa.status}]"
                if etapa.status == "FALHA" and etapa.mensagem:
                    linha += f" — {etapa.mensagem}"
                st.markdown(linha)

            with st.expander("Log completo"):
                st.code(montar_log_completo(execucao), language="text")

            if execucao.status == "FALHA":
                st.download_button(
                    "Baixar card de bug",
                    data=gerar_card_bug(execucao),
                    file_name=f"card_bug_{execucao.id}.md",
                    mime="text/markdown",
                    key=f"download_card_bug_{execucao.id}",
                    on_click=_criar_callback_salvar_card_bug(execucao),
                )


def _criar_callback_salvar_card_bug(execucao: Execucao) -> Callable[[], None]:
    # Vínculo explícito do valor de `execucao` no momento da criação do
    # callback — sem isso, todo botão do loop apontaria para a última
    # execução da lista (closure sobre a variável do loop, não sobre o
    # valor de cada iteração).
    def _salvar() -> None:
        salvar_card_bug(execucao)

    return _salvar


def _renderizar_aba_regras() -> None:
    regras = st.session_state.regras_descobertas
    if not regras:
        st.info('Nenhuma regra descoberta ainda — clique em "Descobrir regras" na barra lateral.')
        return

    st.dataframe(
        [
            {
                "Nome": regra.nome,
                "Tipo": regra.tipo,
                "Status": regra.status,
                "Última execução": regra.ultima_execucao,
            }
            for regra in regras
        ],
        width="stretch",
    )


def _renderizar_aba_historico() -> None:
    execucoes = listar_execucoes()
    if not execucoes:
        st.info("Nenhuma execução registrada ainda.")
        return

    st.dataframe(
        [
            {
                "Data início": execucao.data_inicio,
                "Cliente": execucao.cliente,
                "Regra": execucao.nome_regra,
                "Tipo": execucao.tipo_teste,
                "Status": execucao.status,
                "Duração (s)": execucao.duracao_segundos,
            }
            for execucao in execucoes
        ],
        width="stretch",
    )


def main() -> None:
    st.set_page_config(page_title="EDI Test Runner", page_icon="🧪", layout="wide")
    _inicializar_estado()

    config = carregar_configuracao_edi()
    _renderizar_sidebar(config)

    aba_execucao, aba_regras, aba_historico = st.tabs(["Execução", "Regras", "Histórico"])

    with aba_execucao:
        _renderizar_aba_execucao(config)

    with aba_regras:
        _renderizar_aba_regras()

    with aba_historico:
        _renderizar_aba_historico()


main()
