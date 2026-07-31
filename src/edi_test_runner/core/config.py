import os

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class ConfiguracaoEdi(BaseModel):
    base_url: str
    usuario: str
    senha: str


def carregar_configuracao_edi() -> ConfiguracaoEdi:
    return ConfiguracaoEdi(
        base_url=os.environ["EDI_BASE_URL"],
        usuario=os.environ["EDI_USUARIO"],
        senha=os.environ["EDI_SENHA"],
    )
