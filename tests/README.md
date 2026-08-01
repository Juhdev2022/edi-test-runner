# Testes — guia rápido

60 testes, 100% de cobertura em `src/edi_test_runner/` exceto `ui/` (ver seção final). Threshold mínimo configurado em `pyproject.toml`: `--cov-fail-under` de 95% (via `[tool.coverage.report] fail_under`), aplicado automaticamente por `pytest-cov` sem precisar de flag na linha de comando.

```bash
uv run pytest -v          # roda tudo, com relatório de cobertura
uv run pytest tests/test_executor.py -v   # só um arquivo
```

## Padrão de fixtures (`tests/conftest.py`)

Todo o suite roda contra mocks HTML estáticos em `tests/mocks/edi/`, nunca contra o EDI Enterprise real (fase 1 do projeto — ver `CONTEXTO_PROJETO_TESTRUNNER_PYTHON.md`). O padrão se repete em praticamente todo teste de automação:

**`browser` (session) → `page` (por teste).** Um único Chromium fica de pé pra sessão inteira de testes (caro de subir); cada teste recebe sua própria aba (`page`), fechada ao final. Exemplo mínimo: `test_login.py`.

**`edi_mock_url` (session).** Sobe um `http.server.ThreadingHTTPServer` servindo `tests/mocks/edi/` numa **porta dinâmica** (`("127.0.0.1", 0)` — o SO escolhe uma livre), pra nunca colidir com algo já rodando na sua máquina. A fixture devolve a URL base (`http://127.0.0.1:PORTA`); os testes montam a URL completa (`f"{edi_mock_url}/regras.html"`).

**Variações do servidor mock, quando o teste precisa simular infraestrutura quebrada:**
- `edi_mock_url_sem_login_html` — serve o diretório *pai* de `mocks/edi/`, então `/login.html` dá 404 de verdade. Usado em `test_health_check.py` pra testar o branch de "servidor responde, mas com status inesperado" sem inventar um mock só pra isso.
- `edi_url_indisponivel` — abre e fecha um socket na hora pra garantir uma porta livre onde **nada** está escutando, simulando conexão recusada/timeout de verdade (não um mock, uma porta genuinamente fechada). Usado no mesmo arquivo pra testar "servidor inacessível".

**`credenciais_validas` / `credenciais_invalidas`.** Par usuário/senha sintético que bate com o que `login.html` espera (`tester.edi` / `Senha123!`). Nunca são dados reais de cliente.

## Como adicionar um novo mock HTML

Exemplo de referência: `tests/mocks/edi/regra_detalhe.html` e `execucao_log.html` (ambos parametrizados por query string `?id=`, com um "banco de dados" JS pequeno mapeando nome de regra → comportamento esperado — ver seção 4.4 do `CONTEXTO_PROJETO_TESTRUNNER_PYTHON.md` pra decisão de design). Regra geral: um HTML por *tipo de tela* do EDI (não um por regra cadastrada), lendo o identificador da URL.

## Por que `ui/streamlit_app.py` fica de fora da cobertura

Decisão consciente desde o M8, não lacuna: **UI do Streamlit é validada manualmente, rodando o app de verdade — não por `pytest`.** Motivos:
- Testes automatizados de widget do Streamlit testariam re-execução de script, não comportamento visual (layout, cor, clareza de mensagem) — que é justamente o que mais importa numa UI.
- `pytest-cov` conta `ui/streamlit_app.py` como 0% se não excluído, o que tornaria qualquer threshold de cobertura inútil (por isso o `omit` em `[tool.coverage.run]` no `pyproject.toml`).

**Como a UI é validada na prática (padrão usado do M8 ao M9.1):**
1. Sobe um servidor mock standalone: `uv run python -m http.server 8900 --directory tests/mocks/edi` (fora do `pytest`, que sobe/derruba o dele sozinho a cada rodada).
2. Cria um `.env` na raiz apontando pra essa porta (ver `.env.example`).
3. Roda o app: `uv run streamlit run src/edi_test_runner/ui/streamlit_app.py`.
4. Clica pelo fluxo real (ou, pra verificação automatizada de regressão visual/funcional pontual, usa um script Playwright avulso apontando pro app rodando — foi assim que os bugs do M8 (`greenlet` + cache) e do M9.1 (JSON legado) foram pegos antes de chegar até você).

Toda lógica que a UI *usa* (descoberta, execução, bateria, health check, persistência JSON, geração de card de bug) já é 100% coberta pelos módulos abaixo de `ui/` — a UI em si é só orquestração fina desses módulos.
