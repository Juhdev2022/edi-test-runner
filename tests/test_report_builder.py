from datetime import datetime
from pathlib import Path

import pytest

from edi_test_runner.automation.batch_runner import ResultadoBateria
from edi_test_runner.core.models import EtapaExecucao, Execucao
from edi_test_runner.reporting.report_builder import (
    CardBugNaoAplicavelError,
    gerar_card_bug,
    gerar_report_bateria,
    montar_log_completo,
    salvar_card_bug,
    salvar_report_bateria,
)


def _execucao_sucesso() -> Execucao:
    return Execucao(
        id="id-sucesso",
        cliente="CLIENTE_FICTICIO",
        ambiente="HOMOLOGACAO",
        data_inicio=datetime(2026, 8, 1, 10, 0, 0),
        data_fim=datetime(2026, 8, 1, 10, 0, 5),
        duracao_segundos=5,
        status="SUCESSO",
        nome_regra="REGRA_UPLOAD_SFTP_01",
        tipo_teste="SFTP_UPLOAD",
        etapas=[
            EtapaExecucao(
                ordem=1, nome="Preparar arquivo local", status="SUCESSO", duracao_segundos=1
            ),
            EtapaExecucao(ordem=2, nome="Conectar servidor", status="SUCESSO", duracao_segundos=2),
        ],
    )


def _execucao_falha() -> Execucao:
    return Execucao(
        id="id-falha",
        cliente="CLIENTE_FICTICIO",
        ambiente="HOMOLOGACAO",
        data_inicio=datetime(2026, 8, 1, 11, 0, 0),
        data_fim=datetime(2026, 8, 1, 11, 0, 30),
        duracao_segundos=30,
        status="FALHA",
        nome_regra="REGRA_DOWNLOAD_FTPS_02",
        tipo_teste="FTPS_DOWNLOAD",
        etapas=[
            EtapaExecucao(
                ordem=1, nome="Preparar arquivo local", status="SUCESSO", duracao_segundos=5
            ),
            EtapaExecucao(
                ordem=2,
                nome="Conectar servidor",
                status="FALHA",
                duracao_segundos=25,
                mensagem="Certificado FTPS expirado",
            ),
            EtapaExecucao(ordem=3, nome="Baixar arquivo", status="PULADA", duracao_segundos=0),
        ],
        observacoes="Falha na etapa 'Conectar servidor': Certificado FTPS expirado",
    )


def _execucao_falha_so_com_puladas() -> Execucao:
    # Cenário defensivo: status FALHA sem nenhuma etapa marcada FALHA
    # explicitamente (não deveria acontecer com o executor atual, mas
    # gerar_card_bug precisa lidar com isso sem quebrar).
    return Execucao(
        id="id-falha-pulada",
        cliente="CLIENTE_FICTICIO",
        ambiente="HOMOLOGACAO",
        data_inicio=datetime(2026, 8, 1, 12, 0, 0),
        data_fim=datetime(2026, 8, 1, 12, 0, 10),
        duracao_segundos=10,
        status="FALHA",
        nome_regra="REGRA_TESTE_DEFENSIVO",
        tipo_teste="SFTP_UPLOAD",
        etapas=[
            EtapaExecucao(
                ordem=1, nome="Preparar arquivo local", status="PULADA", duracao_segundos=0
            ),
        ],
    )


def test_gerar_card_bug_monta_titulo_correto() -> None:
    card = gerar_card_bug(_execucao_falha())

    assert (
        "Nome: [BUG] [PREENCHER TÍTULO] — Regra REGRA_DOWNLOAD_FTPS_02 "
        "falhou na etapa Conectar servidor" in card
    )


def test_gerar_card_bug_preenche_campos_com_dados_reais() -> None:
    card = gerar_card_bug(_execucao_falha())

    assert "Execução da regra REGRA_DOWNLOAD_FTPS_02 (tipo FTPS_DOWNLOAD) falhou" in card
    assert 'etapa "Conectar servidor" com a mensagem: "Certificado FTPS expirado"' in card
    assert "Ambiente: HOMOLOGACAO" in card
    assert "Cliente: CLIENTE_FICTICIO" in card
    assert "Data/hora: 01/08/2026 11:00:00" in card
    assert montar_log_completo(_execucao_falha()) in card


def test_gerar_card_bug_tem_campos_para_preencher_manualmente() -> None:
    card = gerar_card_bug(_execucao_falha())

    assert "[PREENCHER TÍTULO]" in card
    assert "[PREENCHER RESUMO EM 1-2 FRASES]" in card
    assert "[PREENCHER O QUE DEVERIA ACONTECER]" in card
    assert "Criticidade: [PREENCHER]" in card


def test_gerar_card_bug_duracao_ate_falha_nao_inclui_puladas_depois() -> None:
    card = gerar_card_bug(_execucao_falha())

    # Etapa 1 (5s) + etapa 2 (25s) = 30s; a etapa 3 (PULADA, 0s) vem DEPOIS
    # da falha e não deveria ser somada de qualquer forma (soma até a
    # etapa de referência, inclusive).
    assert "Duração até a falha: 30s" in card


def test_gerar_card_bug_com_status_sucesso_levanta_erro_claro() -> None:
    with pytest.raises(CardBugNaoAplicavelError, match="só se aplica a execuções com falha"):
        gerar_card_bug(_execucao_sucesso())


def test_gerar_card_bug_usa_primeira_pulada_quando_sem_etapa_falha_explicita() -> None:
    card = gerar_card_bug(_execucao_falha_so_com_puladas())

    assert "falhou na etapa Preparar arquivo local" in card
    assert "(sem mensagem registrada)" in card


def test_gerar_card_bug_sem_etapa_falha_ou_pulada_levanta_erro() -> None:
    execucao = _execucao_falha_so_com_puladas()
    execucao.etapas = []

    with pytest.raises(CardBugNaoAplicavelError, match="identificar a etapa"):
        gerar_card_bug(execucao)


def test_salvar_card_bug_grava_arquivo_md(tmp_path: Path) -> None:
    caminho = salvar_card_bug(_execucao_falha(), diretorio=tmp_path)

    assert caminho.exists()
    assert caminho.name.startswith("card_bug_")
    assert "id-falha" in caminho.name
    assert "[BUG]" in caminho.read_text(encoding="utf-8")


def test_gerar_report_bateria_inclui_so_cards_de_falha() -> None:
    resultado = ResultadoBateria(
        execucoes=[_execucao_sucesso(), _execucao_falha()],
        data_inicio=datetime(2026, 8, 1, 10, 0, 0),
        data_fim=datetime(2026, 8, 1, 11, 0, 30),
    )

    report = gerar_report_bateria(resultado)

    assert "REGRA_DOWNLOAD_FTPS_02" in report
    assert "REGRA_UPLOAD_SFTP_01" not in report


def test_gerar_report_bateria_sem_falhas_avisa_que_nao_ha_cards() -> None:
    resultado = ResultadoBateria(
        execucoes=[_execucao_sucesso()],
        data_inicio=datetime(2026, 8, 1, 10, 0, 0),
        data_fim=datetime(2026, 8, 1, 10, 0, 5),
    )

    report = gerar_report_bateria(resultado)

    assert "Nenhuma falha nesta bateria" in report


def test_salvar_report_bateria_grava_arquivo_md(tmp_path: Path) -> None:
    resultado = ResultadoBateria(
        execucoes=[_execucao_falha()],
        data_inicio=datetime(2026, 8, 1, 10, 0, 0),
        data_fim=datetime(2026, 8, 1, 11, 0, 30),
    )

    caminho = salvar_report_bateria(resultado, diretorio=tmp_path)

    assert caminho.exists()
    assert caminho.name.startswith("resumo_bateria_")
