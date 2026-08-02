import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

from edi_test_runner.core.models import Ambiente

load_dotenv()


class ConfiguracaoEdi(BaseModel):
    base_url: str
    usuario: str
    senha: str
    cliente: str
    ambiente: Ambiente


def carregar_configuracao_edi() -> ConfiguracaoEdi:
    return ConfiguracaoEdi(
        base_url=os.environ["EDI_BASE_URL"],
        usuario=os.environ["EDI_USUARIO"],
        senha=os.environ["EDI_SENHA"],
        cliente=os.environ["EDI_CLIENTE"],
        ambiente=os.environ["EDI_AMBIENTE"],
    )


def obter_dashboard_assets_dir() -> Path | None:
    # Opcional (ao contrário de ConfiguracaoEdi): publicar para o dashboard
    # é um passo explícito e independente do fluxo principal do TestRunner,
    # que precisa continuar rodando sem essa variável configurada.
    valor = os.environ.get("DASHBOARD_ASSETS_DIR")
    return Path(valor) if valor else None
