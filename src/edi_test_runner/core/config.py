import os

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
