import json
from datetime import datetime

import pytest
from pydantic import ValidationError

from edi_test_runner.core.models import EtapaExecucao, Execucao


def _etapas_exemplo() -> list[EtapaExecucao]:
    return [
        EtapaExecucao(ordem=1, nome="Gerar arquivo", status="SUCESSO", duracao_segundos=2),
        EtapaExecucao(
            ordem=2,
            nome="Aplicar regra",
            status="FALHA",
            duracao_segundos=5,
            mensagem="timeout no SFTP",
        ),
        EtapaExecucao(ordem=3, nome="Consultar log", status="PULADA", duracao_segundos=0),
    ]


def _execucao_exemplo() -> Execucao:
    return Execucao(
        id="0d3f2b1a-0000-4000-8000-000000000001",
        cliente="CLIENTE_FICTICIO",
        ambiente="HOMOLOGACAO",
        data_inicio=datetime(2026, 7, 30, 10, 0, 0),
        data_fim=datetime(2026, 7, 30, 10, 0, 7),
        duracao_segundos=7,
        status="PARCIAL",
        nome_regra="REGRA_UPLOAD_SFTP_01",
        tipo_teste="SFTP_UPLOAD",
        etapas=_etapas_exemplo(),
    )


def test_total_etapas_e_derivado_da_lista_etapas() -> None:
    execucao = _execucao_exemplo()

    assert execucao.total_etapas == 3
    assert execucao.etapas_com_sucesso == 1


def test_computed_fields_nao_aceitam_valor_na_construcao() -> None:
    with pytest.raises(ValidationError):
        Execucao(
            id="x",
            cliente="CLIENTE_FICTICIO",
            ambiente="HOMOLOGACAO",
            data_inicio=datetime(2026, 7, 30, 10, 0, 0),
            data_fim=datetime(2026, 7, 30, 10, 0, 7),
            duracao_segundos=7,
            status="SUCESSO",
            nome_regra="REGRA_UPLOAD_SFTP_01",
            tipo_teste="SFTP_UPLOAD",
            etapas=[],
            total_etapas=999,  # type: ignore[call-arg]
        )


def test_serializacao_json_usa_camel_case_compativel_com_angular() -> None:
    execucao = _execucao_exemplo()

    payload = json.loads(execucao.model_dump_json(by_alias=True))

    assert payload["dataInicio"] == "2026-07-30T10:00:00"
    assert payload["duracaoSegundos"] == 7
    assert payload["nomeRegra"] == "REGRA_UPLOAD_SFTP_01"
    assert payload["tipoTeste"] == "SFTP_UPLOAD"
    assert payload["totalEtapas"] == 3
    assert payload["etapasComSucesso"] == 1
    assert payload["etapas"][1]["duracaoSegundos"] == 5
    assert payload["etapas"][1]["mensagem"] == "timeout no SFTP"


def test_validacao_aceita_entrada_em_camel_case() -> None:
    execucao = Execucao.model_validate(
        {
            "id": "abc",
            "cliente": "CLIENTE_FICTICIO",
            "ambiente": "PRODUCAO",
            "dataInicio": "2026-07-30T10:00:00",
            "dataFim": "2026-07-30T10:00:07",
            "duracaoSegundos": 7,
            "status": "SUCESSO",
            "nomeRegra": "REGRA_DOWNLOAD_FTP_04",
            "tipoTeste": "FTP_DOWNLOAD",
            "etapas": [],
        }
    )

    assert execucao.data_inicio == datetime(2026, 7, 30, 10, 0, 0)
    assert execucao.tipo_teste == "FTP_DOWNLOAD"


def test_status_invalido_e_rejeitado() -> None:
    with pytest.raises(ValidationError):
        EtapaExecucao(ordem=1, nome="Etapa", status="EM_ANDAMENTO", duracao_segundos=1)


def test_cliente_e_tipo_teste_aceitam_qualquer_string() -> None:
    execucao = _execucao_exemplo()

    assert execucao.cliente == "CLIENTE_FICTICIO"
    assert execucao.tipo_teste == "SFTP_UPLOAD"


def test_campos_opcionais_tem_default_none() -> None:
    etapa = EtapaExecucao(ordem=1, nome="Gerar arquivo", status="SUCESSO", duracao_segundos=2)

    assert etapa.mensagem is None
