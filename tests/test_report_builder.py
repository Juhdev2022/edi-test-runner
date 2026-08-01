from datetime import datetime
from pathlib import Path

from edi_test_runner.automation.batch_runner import ResultadoBateria
from edi_test_runner.core.models import EtapaExecucao, Execucao
from edi_test_runner.reporting.report_builder import (
    gerar_report_bateria,
    gerar_report_execucao,
    montar_log_completo,
    salvar_report_bateria,
    salvar_report_execucao,
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


def test_montar_log_completo_tem_inicio_etapas_e_fim() -> None:
    log = montar_log_completo(_execucao_sucesso())

    linhas = log.splitlines()
    assert linhas[0].startswith("[2026-08-01T10:00:00] Início — SFTP_UPLOAD")
    assert "1. Preparar arquivo local — SUCESSO (1s)" in linhas[1]
    assert linhas[-1] == "[2026-08-01T10:00:05] Fim — status: SUCESSO"


def test_montar_log_completo_inclui_mensagem_da_etapa_com_falha() -> None:
    log = montar_log_completo(_execucao_falha())

    assert "Certificado FTPS expirado" in log


def test_gerar_report_execucao_inclui_contexto_e_status() -> None:
    report = gerar_report_execucao(_execucao_sucesso())

    assert "# Report de execução — SFTP_UPLOAD" in report
    assert "**Status:** SUCESSO" in report
    assert "**Cliente:** CLIENTE_FICTICIO" in report
    assert "**Ambiente:** HOMOLOGACAO" in report
    assert "**ID da execução:** id-sucesso" in report


def test_gerar_report_execucao_sucesso_usa_mensagem_padrao_sem_observacoes() -> None:
    report = gerar_report_execucao(_execucao_sucesso())

    assert "Execução concluída com sucesso." in report


def test_gerar_report_execucao_com_falha_mostra_observacoes_e_tabela() -> None:
    report = gerar_report_execucao(_execucao_falha())

    assert "Falha na etapa 'Conectar servidor': Certificado FTPS expirado" in report
    assert "| 2 | Conectar servidor | FALHA | 25 | Certificado FTPS expirado |" in report
    assert "| 3 | Baixar arquivo | PULADA | 0 | — |" in report


def test_tabela_etapas_escapa_pipe_na_mensagem() -> None:
    execucao = _execucao_falha()
    execucao.etapas[1].mensagem = "Erro: campo A | campo B inconsistente"

    report = gerar_report_execucao(execucao)

    assert "campo A \\| campo B" in report


def test_gerar_report_bateria_inclui_todas_as_execucoes() -> None:
    resultado = ResultadoBateria(
        execucoes=[_execucao_sucesso(), _execucao_falha()],
        data_inicio=datetime(2026, 8, 1, 10, 0, 0),
        data_fim=datetime(2026, 8, 1, 11, 0, 30),
    )

    report = gerar_report_bateria(resultado)

    assert "# Report de bateria — PARCIAL" in report
    assert "Report de execução — SFTP_UPLOAD" in report
    assert "Report de execução — FTPS_DOWNLOAD" in report
    assert "Total de regras:** 2" in report


def test_salvar_report_execucao_grava_arquivo_md(tmp_path: Path) -> None:
    caminho = salvar_report_execucao(_execucao_sucesso(), diretorio=tmp_path)

    assert caminho.exists()
    assert caminho.suffix == ".md"
    assert "id-sucesso" in caminho.name
    assert "# Report de execução" in caminho.read_text(encoding="utf-8")


def test_salvar_report_bateria_grava_arquivo_md(tmp_path: Path) -> None:
    resultado = ResultadoBateria(
        execucoes=[_execucao_sucesso()],
        data_inicio=datetime(2026, 8, 1, 10, 0, 0),
        data_fim=datetime(2026, 8, 1, 10, 0, 5),
    )

    caminho = salvar_report_bateria(resultado, diretorio=tmp_path)

    assert caminho.exists()
    assert caminho.name.startswith("report_bateria_")
    assert "# Report de bateria" in caminho.read_text(encoding="utf-8")
