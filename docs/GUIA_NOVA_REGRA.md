# Como adicionar uma nova regra

**Contra um sistema EDI real, você não precisa fazer nada disto.** `descobrir_regras()` mapeia automaticamente qualquer regra cadastrada — é o diferencial que este projeto herdou da ferramenta anterior. Este guia é só para estender o **ambiente de teste sintético** (`tests/mocks/edi/`), quando você quer cobrir um tipo de regra que os cenários atuais ainda não representam.

## Onde mexer

Uma regra sintética existe em três lugares, que precisam ficar consistentes entre si:

### 1. `tests/mocks/edi/regras.html` — aparece na listagem

Adicione uma linha na tabela:

```html
<tr class="linha-regra">
  <td class="regra-nome">REGRA_NOVO_TIPO_09</td>
  <td class="regra-tipo">NOVO_TIPO</td>
  <td class="regra-status">ATIVA</td>
  <td class="regra-ultima-execucao">2026-08-01T10:00:00</td>
</tr>
```

`regra-status` pode ser `ATIVA` ou `INATIVA` (a bateria completa só executa `ATIVA`). Deixe `regra-ultima-execucao` vazio (`<td class="regra-ultima-execucao"></td>`) se quiser testar o caminho de "regra nunca executada".

### 2. `tests/mocks/edi/regra_detalhe.html` — a "aplicação" da regra

Adicione uma entrada no objeto `REGRAS`, com o mesmo nome usado no passo 1, listando as etapas e o status de cada uma:

```js
REGRA_NOVO_TIPO_09: [
  { nome: "Preparar arquivo local", status: "SUCESSO", mensagem: null },
  { nome: "Conectar servidor", status: "SUCESSO", mensagem: null },
  { nome: "Enviar arquivo", status: "SUCESSO", mensagem: null },
  { nome: "Validar recebimento no destino", status: "SUCESSO", mensagem: null },
],
```

Para uma regra que deve falhar, marque a etapa correspondente `FALHA` com uma `mensagem` realista, e as etapas seguintes `PULADA` (cascata — nunca `FALHA` depois da primeira).

### 3. `tests/mocks/edi/execucao_log.html` — a fonte que o executor realmente lê

O executor não confia no que `regra_detalhe.html` renderizou visualmente — ele navega para esta segunda página e lê `window.__logExecucao`. Adicione a mesma regra aqui, agora com `duracaoSegundos` por etapa:

```js
REGRA_NOVO_TIPO_09: {
  resultado: "SUCESSO",
  etapas: [
    { nome: "Preparar arquivo local", status: "SUCESSO", mensagem: null, duracaoSegundos: 1 },
    { nome: "Conectar servidor", status: "SUCESSO", mensagem: null, duracaoSegundos: 2 },
    { nome: "Enviar arquivo", status: "SUCESSO", mensagem: null, duracaoSegundos: 2 },
    { nome: "Validar recebimento no destino", status: "SUCESSO", mensagem: null, duracaoSegundos: 1 },
  ],
},
```

As etapas 2 e 3 (`_tabela_etapas`) devem bater exatamente entre `regra_detalhe.html` e `execucao_log.html` — nome, status e mensagem. Só a duração vive exclusivamente no segundo arquivo (é o único lugar que o executor usa para isso).

Se a regra for de **download** (não upload), troque o nome da terceira etapa para `"Baixar arquivo"` nos dois arquivos — é a única diferença de nomenclatura entre os dois fluxos hoje.

## Checklist antes de commitar

- [ ] Nome da regra idêntico nos três arquivos (`regras.html`, `regra_detalhe.html`, `execucao_log.html`)
- [ ] Etapas idênticas (nome, status, mensagem) entre `regra_detalhe.html` e `execucao_log.html`
- [ ] Se a regra ficou `ATIVA`: **`tests/test_batch_runner.py::test_bateria_completa_via_descoberta_real` provavelmente precisa de ajuste** — esse teste verifica contagens exatas (`total_regras`, `total_sucesso`, `total_falha`) contra as 8 regras atuais do mock. Adicionar uma 9ª regra ativa muda esses números.
- [ ] `uv run pytest -v` continua 100% verde

## Exemplo real para referência

As 8 regras já existentes (`REGRA_UPLOAD_SFTP_01` até `REGRA_VALIDACAO_ASSINATURA_08`) cobrem a variação que este guia descreve: sucesso completo, falha na primeira etapa, falha no meio (cascata parcial), falha na última etapa (sem cascata), regra inativa, e regra sem última execução registrada. Comparar uma regra nova com a mais parecida dessas costuma ser mais rápido do que começar do zero.
