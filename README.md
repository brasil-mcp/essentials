# brasil-mcp-essentials

[![PyPI version](https://img.shields.io/pypi/v/brasil-mcp-essentials.svg)](https://pypi.org/project/brasil-mcp-essentials/)
[![Python versions](https://img.shields.io/pypi/pyversions/brasil-mcp-essentials.svg)](https://pypi.org/project/brasil-mcp-essentials/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/brasil-mcp/essentials/actions/workflows/ci.yml/badge.svg)](https://github.com/brasil-mcp/essentials/actions/workflows/ci.yml)

> **MCP server brasileiro — privacy-first, CNPJ alfanumérico-ready.**
> 14 utilities offline para devs BR: validação de documentos, parse de boleto, PIX BR Code, calendário de feriados.

Sem rede, sem PII coletada, sem dependência de API externa. Tudo roda local — perfeito para agentes (Claude Desktop, Cursor, ChatGPT, etc.) que precisam tratar dados brasileiros com privacidade.

---

## Por que esse MCP existe

- **CNPJ alfanumérico ready.** A Receita Federal vai começar a emitir CNPJs alfanuméricos em julho/2026 (NT COCAD/SUARA nº 49/2024). Este pacote valida os dois formatos — legacy 14 dígitos **e** novo alfanumérico — auto-detectando. Seu agente não quebra quando o RF flipar a chave.
- **Privacy-first.** Validação e parse rodam 100% offline. Nada de chamada a API externa, nada de telemetria embutida por padrão. Opt-in opcional pra ajudar o projeto com metadata anônima.
- **MCP-nativo.** Cada tool é uma MCP tool com schema, descrição e ergonomia que o LLM realmente consegue selecionar bem.
- **CLI bonus.** Tudo que serve como MCP tool serve também como subcomando shell, para devs que ainda não usam um MCP client.

---

## Instalação

```bash
# Via uv (recomendado)
uv tool install brasil-mcp-essentials

# Via pipx
pipx install brasil-mcp-essentials

# Via pip
pip install brasil-mcp-essentials
```

---

## Configurar Claude Desktop / Cursor / outros MCP clients

Adicione ao `claude_desktop_config.json` (Claude Desktop) ou equivalente:

```json
{
  "mcpServers": {
    "brasil-essentials": {
      "command": "brasil-mcp-server"
    }
  }
}
```

Reinicie o cliente. As 14 tools aparecem automaticamente.

---

## Quick start no terminal

```bash
# Validar CPF
$ brasil-mcp validate-cpf 52998224725
{
  "valid": true,
  "formatted": "529.982.247-25",
  "raw": "52998224725",
  "error": null
}

# Validar CNPJ (legacy ou alfanumérico — auto-detecta)
$ brasil-mcp validate-cnpj 11.222.333/0001-81
{
  "valid": true,
  "formatted": "11.222.333/0001-81",
  "raw": "11.222.333/0001-81",
  "error": null,
  "format": "legacy"
}

# Parse de boleto bancário
$ brasil-mcp parse-boleto "34191790010104351004791020150008291070026000"
# (...detecta tipo, banco, valor, vencimento)

# Gerar BR Code PIX estático
$ brasil-mcp generate-pix-brcode \
    --chave joao@example.com \
    --nome "Joao da Silva" \
    --cidade "Sao Paulo" \
    --valor 12345
{
  "brcode": "00020126...6304ABCD",
  ...
}

# Próximo dia útil (pula fins de semana + feriados)
$ brasil-mcp proximo-dia-util 2026-09-04
{ "date": "2026-09-08", "dias_pulados": 3 }
```

Liste todos os comandos: `brasil-mcp --help`.

---

## Catálogo de 14 tools

### Validators (7)

| Tool | Descrição |
|---|---|
| `validate_cpf` | CPF (11 dígitos), módulo 11, rejeita sequências repetidas |
| `validate_cnpj` | CNPJ **legacy** (14 dígitos) **OU alfanumérico** (RF NT 49/2024). Auto-detecta. |
| `validate_pis` | PIS/PASEP/NIT (11 dígitos) |
| `validate_renavam` | RENAVAM (9/10/11 dígitos, padded para 11) |
| `validate_cnh` | CNH brasileira (11 dígitos) |
| `validate_titulo_eleitor` | Título de eleitor (12 dígitos), retorna UF |
| `validate_credit_card` | Luhn + detecção de bandeira (Visa, Mastercard, **Elo**, **Hipercard**, Amex, Diners, JCB, Discover) |

### Boleto (1)

| Tool | Descrição |
|---|---|
| `parse_boleto` | Linha digitável (47) / código de barras (44) bancário, ou arrecadação (48). Detecta tipo, banco (12+ bancos FEBRABAN), valor, vencimento, nosso número, segmento de arrecadação. |

### PIX (2)

| Tool | Descrição |
|---|---|
| `parse_pix_brcode` | Decoda BR Code PIX (EMV TLV). Retorna chave, tipo de chave, beneficiário, cidade, valor, txid, descrição, detecção estático/dinâmico. |
| `generate_pix_brcode` | Gera BR Code PIX estático. Opcional: QR code em PNG base64 e/ou SVG. |

### Calendar (4)

| Tool | Descrição |
|---|---|
| `is_feriado_nacional` | Verifica se uma data é feriado brasileiro (nacional + opcional UF) |
| `proximo_dia_util` | Próximo dia útil após uma data (pula fim de semana + feriados) |
| `contar_dias_uteis` | Conta dias úteis entre duas datas |
| `listar_feriados` | Lista feriados brasileiros de um ano (nacional + opcional estadual) |

Detalhes completos de cada tool em [`docs/tools.md`](docs/tools.md).

---

## Convenções globais

- **Input:** strings de documento aceitam com ou sem máscara (normalização interna). Datas em ISO 8601 (`YYYY-MM-DD`).
- **Output:** validadores retornam `{ valid, formatted, raw, error }`. Valores monetários sempre em **centavos (int)** — nunca float.
- **Erros:** estruturados `{ code, message_pt, message_en, suggestion? }`. Códigos: `INVALID_FORMAT`, `INVALID_LENGTH`, `INVALID_CHECKSUM`, `EMPTY_INPUT`, `REPEATED_DIGITS`, etc. Inputs inválidos viram `valid: false` — nunca exceções não-tratadas.

---

## Privacidade & telemetria

**Default: nenhuma telemetria.** Para opt-in (metadata anônima — nome da tool, sucesso/falha, latência, versão; nunca os inputs/outputs):

```bash
export BRASIL_MCP_TELEMETRY=1
```

Um ID anônimo é gerado no primeiro run e armazenado em `$XDG_DATA_HOME/brasil-mcp/installation_id`. Para desabilitar de novo, basta `unset` da variável.

Detalhes completos em [`docs/tools.md#telemetria`](docs/tools.md).

---

## Roadmap

Este é o **Brasil Essentials MCP (Fase 1)**. Próximos sprints:

- **v0.2** — Lookups com API externa: CEP via ViaCEP, FEBRABAN online, cotações BCB.
- **v0.3** — Transport SSE + REST API com OpenAPI.
- **v0.4** — Pacote npm gêmeo (`@brasil-mcp/essentials`).
- **v0.5** — Submissão a registries: Smithery, glama.ai, mcp.so, Anthropic Directory.

Fases futuras (produtos separados):

- **Brasil Match MCP (Fase 2)** — Match contra base Receita Federal sem expor dado pessoal. KYC, anti-fraude, onboarding B2B.
- **Brasil Compliance MCP (Fase 3)** — Due diligence + KYC pago: sanções (CEIS/CNEP), processos (CNJ), IP (INPI), ambiental (IBAMA), trabalho (MTE), PEP screening.

---

## Licença

MIT — veja [LICENSE](LICENSE).

---

## Contribuindo

Issues e PRs bem-vindos em [github.com/brasil-mcp/essentials](https://github.com/brasil-mcp/essentials/issues).

---

<details>
<summary><h2 style="display:inline">English (summary)</h2></summary>

`brasil-mcp-essentials` is a Brazilian-focused MCP server + CLI providing 14 offline utilities for developers working with Brazilian data: document validators (CPF, CNPJ, PIS, RENAVAM, CNH, Voter ID, Credit Card), boleto parser, PIX BR Code parser/generator with QR codes, and Brazilian calendar tools (holidays, business days).

**Headline feature:** validates both legacy 14-digit CNPJs AND the new alphanumeric CNPJs that Brazil's Receita Federal will start issuing in July 2026 (NT COCAD/SUARA 49/2024). Future-proof your agent today.

**Privacy-first.** Everything runs offline. No external API calls. No telemetry by default — opt-in only, anonymous metadata.

Install:
```bash
uv tool install brasil-mcp-essentials
```

MCP config (Claude Desktop):
```json
{ "mcpServers": { "brasil-essentials": { "command": "brasil-mcp-server" } } }
```

CLI:
```bash
brasil-mcp validate-cpf 52998224725
brasil-mcp parse-boleto "<47-digit string>"
brasil-mcp generate-pix-brcode --chave you@example.com --nome "Your Name" --cidade "Sao Paulo"
```

See the [tool catalog](docs/tools.md) for full schema documentation.

License: MIT.

</details>
