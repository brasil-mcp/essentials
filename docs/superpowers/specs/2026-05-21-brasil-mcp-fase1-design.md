# Brasil MCP — Fase 1 (Essentials) — Spec de Design

**Data:** 2026-05-21
**Status:** Aprovado para implementação
**Escopo:** v0.1.0 — núcleo offline, Python, MCP stdio + CLI

---

## 1. Visão geral

`brasil-mcp-essentials` é um MCP server (stdio) + CLI Python que oferece **14 tools utilitárias offline** para desenvolvimento brasileiro: validators de documentos, parsers/geradores de boleto e PIX, e operações de calendário. Posicionamento de marca: **privacy-first, zero rede para a operação core, CNPJ alfanumérico-ready** (Receita Federal NT COCAD/SUARA nº 49/2024).

**Não inclui na v0.1.0** (entra em sprints subsequentes):
- Lookups via API externa (CEP/ViaCEP, FEBRABAN/BrasilAPI online, cotações BCB)
- Transport SSE
- REST API + OpenAPI
- Pacote npm
- Submissão a registries (Smithery, glama.ai, mcp.so, Anthropic Directory)

---

## 2. Arquitetura

Pattern: **core puro + adapters finos**.

- `core/` — funções puras, dataclasses tipadas. Zero conhecimento de MCP/CLI/HTTP. Testável isoladamente.
- `adapters/mcp/` — registra cada função do core como uma MCP tool. Apenas serialização de I/O + JSON Schema.
- `adapters/cli/` — Typer app expondo cada função como subcomando.
- Adapters futuros (`adapters/sse/`, `adapters/rest/`) entrarão sem mexer no core.

### 2.1. Stack

| Componente | Escolha | Justificativa |
|---|---|---|
| Python | ≥ 3.11 | match/case, async maduro, tipos modernos |
| Build/install | `uv` + `hatchling` (build backend) | rápido, padrão pyproject.toml, OIDC publishing |
| Lint/format | `ruff` | tudo num só |
| Type check | `pyright` strict | catches mais que mypy em alguns casos |
| Test | `pytest` + `pytest-cov` | default |
| CLI | `typer` | melhor DX, ecosistema FastAPI |
| MCP SDK | `mcp` (oficial Anthropic) | suportado, mantido |
| QR PIX | `segno` | pure Python, PNG + SVG, sem Pillow |
| Feriados | `python-holidays` | BR nacional + UFs + alguns municípios |
| Telemetria (opt-in) | `posthog` (lazy import) | stack já em uso |
| Licença | MIT | per spec |

### 2.2. Repo

`github.com/brasil-mcp/essentials` — org dedicada `brasil-mcp/`. Casa com npm scope `@brasil-mcp/`. Phase 2/3 vão como `brasil-mcp/match`, `brasil-mcp/compliance`.

### 2.3. Layout

```
brasil-mcp-essentials/
├── pyproject.toml
├── README.md                       # PT-BR primário, EN secundário
├── LICENSE                         # MIT
├── CHANGELOG.md
├── .github/workflows/
│   ├── ci.yml
│   └── release.yml
├── src/brasil_mcp/
│   ├── __init__.py                 # __version__
│   ├── core/
│   │   ├── validators/
│   │   │   ├── cpf.py
│   │   │   ├── cnpj.py             # legacy + alfanumérico
│   │   │   ├── pis.py
│   │   │   ├── renavam.py
│   │   │   ├── cnh.py
│   │   │   ├── titulo_eleitor.py
│   │   │   └── credit_card.py
│   │   ├── boleto/
│   │   │   ├── linha_digitavel.py
│   │   │   ├── codigo_barras.py
│   │   │   ├── parser.py           # despacha bancário vs arrecadação
│   │   │   └── febraban_codes.json # bundled
│   │   ├── pix/
│   │   │   ├── brcode.py
│   │   │   ├── crc16.py
│   │   │   └── qr.py
│   │   ├── calendar/
│   │   │   └── feriados.py
│   │   ├── errors.py               # códigos, ErrorObj
│   │   ├── models.py               # dataclasses de output
│   │   └── telemetry.py            # opt-in posthog
│   ├── adapters/
│   │   ├── mcp/
│   │   │   ├── server.py           # entry: brasil-mcp-server
│   │   │   └── tools.py            # @tool registrations
│   │   └── cli/
│   │       └── app.py              # typer; entry: brasil-mcp
│   └── __main__.py                 # python -m brasil_mcp
├── tests/
│   ├── core/                       # espelha src/
│   ├── adapters/
│   ├── fixtures/                   # vetores oficiais
│   └── conftest.py
└── docs/
    ├── README.pt-BR.md
    └── tools.md                    # catálogo de tools referência
```

### 2.4. Entry points

```toml
# pyproject.toml [project.scripts]
brasil-mcp = "brasil_mcp.adapters.cli.app:app"
brasil-mcp-server = "brasil_mcp.adapters.mcp.server:main"
```

- `brasil-mcp` — CLI Typer com 14 subcomandos + `serve` (que sobe stdio).
- `brasil-mcp-server` — entry direto. É **este** que `claude_desktop_config.json` referencia:
  ```json
  { "mcpServers": { "brasil-essentials": { "command": "brasil-mcp-server" } } }
  ```

---

## 3. Catálogo de tools

### Convenções globais

**Input:**
- Strings de documento aceitam com OU sem máscara — normalização interna.
- Datas em ISO 8601 (`YYYY-MM-DD`).
- Valores monetários em **centavos (int)** — nunca float.

**Output:**
- Validators/parsers retornam `{ valid: bool, ..., raw: str, error: ErrorObj | null }`.
- Erros **nunca** levantam exceção pra input inválido — viram `valid: false` com `error` populado.
- Exceções apenas pra bugs/misuse de API.

### 3.1. Validators (7)

| # | Tool | Descrição (vai pro JSON Schema MCP) |
|---|---|---|
| 1 | `validate_cpf` | Valida CPF brasileiro (11 dígitos). Módulo 11. Rejeita sequências repetidas. |
| 2 | `validate_cnpj` | Valida CNPJ brasileiro — formato legacy (14 dígitos) E novo alfanumérico (NT COCAD/SUARA 49/2024). Auto-detecta. |
| 3 | `validate_pis` | Valida PIS/PASEP/NIT (11 dígitos). |
| 4 | `validate_renavam` | Valida RENAVAM (11 dígitos). |
| 5 | `validate_cnh` | Valida CNH brasileira (11 dígitos). |
| 6 | `validate_titulo_eleitor` | Valida título de eleitor (12 dígitos). |
| 7 | `validate_credit_card` | Valida cartão via Luhn + detecta bandeira (Visa, Mastercard, Elo, Hipercard, Amex, Diners, JCB, Discover). |

**Schema padrão de output:**
```json
{
  "valid": true,
  "formatted": "123.456.789-09",
  "raw": "12345678909",
  "error": null
}
```

**Extensões:**
- `validate_cnpj`: `+ "format": "legacy" | "alphanumeric"`
- `validate_credit_card`: `+ "brand": "visa" | "mastercard" | "elo" | "hipercard" | "amex" | "diners" | "jcb" | "discover" | null`
- `validate_titulo_eleitor`: `+ "uf": "SP" | ...`

**Algoritmo CNPJ alfanumérico:**
1. Converter cada char: `ord(c) - 48` (digits 0-9 → 0-9, letras A-Z → 17-42)
2. Aplicar módulo 11 com pesos padrão (5,4,3,2,9,8,7,6,5,4,3,2 para DV1; 6,5,4,3,2,9,8,7,6,5,4,3,2 para DV2)
3. DVs sempre numéricos
4. Formato canônico legacy: 14 dígitos. Formato alfanumérico: 12 chars alfanum + 2 dígitos. Tamanho total sempre 14.

### 3.2. Boleto (1)

`parse_boleto` — Aceita linha digitável (47 dígitos) OU código de barras (44 dígitos). Detecta tipo bancário vs arrecadação.

**Output:**
```json
{
  "valid": true,
  "tipo": "bancario",
  "linha_digitavel": "...",
  "codigo_barras": "...",
  "banco": {
    "codigo_febraban": "341",
    "ispb": "60701190",
    "nome": "Itaú Unibanco S.A."
  },
  "moeda": "BRL",
  "valor": 12345,
  "vencimento": "2026-06-15",
  "fator_vencimento": 9876,
  "nosso_numero": "12345678901",
  "segmento_arrecadacao": null,
  "raw": "...",
  "error": null
}
```

Para `tipo: "arrecadacao"`:
- `banco: null` (em geral)
- `segmento_arrecadacao`: enum `"tributo_federal" | "tributo_estadual" | "tributo_municipal" | "concessionaria_eletrica" | "concessionaria_gas" | "concessionaria_telefonia" | "concessionaria_agua_saneamento" | "carnes_assemelhados" | "multas_transito" | "outros"`
- `nosso_numero: null`

Fator de vencimento: base 1997-10-07 (dia 1000). Em 22/02/2025 o fator atingiu 9999 e foi reiniciado em 1000 (circular FEBRABAN). O parser usa heurística: se o fator decoded com base 1997 cair antes de 2025-02-22, usa essa data; senão, usa base 2025-02-22.

### 3.3. PIX (2)

#### `parse_pix_brcode`

Faz parse de BR Code PIX (string EMV-compliant). Suporta estático e dinâmico.

**Output:**
```json
{
  "valid": true,
  "chave": "joao@example.com",
  "tipo_chave": "email",
  "beneficiario": "Joao da Silva",
  "cidade": "Sao Paulo",
  "valor": 12345,
  "moeda": "BRL",
  "txid": "PEDIDO12345",
  "descricao": "Pagamento NF 1234",
  "dinamico": false,
  "url_provedor": null,
  "raw": "00020126...",
  "error": null
}
```

`tipo_chave` ∈ `cpf | cnpj | telefone | email | aleatoria`. Detecção: heurística + tamanho + caracteres.

#### `generate_pix_brcode`

**Input:**
```json
{
  "chave": "joao@example.com",
  "nome_beneficiario": "Joao da Silva",
  "cidade": "Sao Paulo",
  "valor": 12345,
  "txid": "PEDIDO12345",
  "descricao": "Pagamento NF 1234",
  "qr_format": "none"
}
```

Constraints (padrão PIX):
- `nome_beneficiario`: max 25 chars, ASCII (acentos removidos)
- `cidade`: max 15 chars, ASCII
- `txid`: max 25 chars, `[A-Za-z0-9]`
- `qr_format`: `"none" | "png" | "svg" | "both"` (default `"none"`)

**Output:**
```json
{
  "brcode": "00020126360014BR.GOV.BCB.PIX...6304ABCD",
  "qr_png_base64": "iVBORw0KGgo...",
  "qr_svg": "<svg>...</svg>",
  "error": null
}
```

CRC16-CCITT-FALSE puro Python (poly 0x1021, init 0xFFFF).

### 3.4. Calendar (4)

| Tool | Input | Output |
|---|---|---|
| `is_feriado_nacional` | `{ date, uf?, municipio? }` | `{ is_feriado, nome, esfera, raw_date }` |
| `proximo_dia_util` | `{ date, uf?, include_today? }` | `{ date, dias_pulados }` |
| `contar_dias_uteis` | `{ start_date, end_date, uf?, inclusive_end? }` (default `inclusive_end=false`) | `{ count, total_dias, feriados_no_periodo }` |
| `listar_feriados` | `{ year, uf? }` | `{ ano, uf, feriados: [{date, nome, esfera}] }` |

`esfera` ∈ `nacional | estadual | municipal`. Backend: `python-holidays.Brazil(state=uf)`.

---

## 4. Modelo de erros

```python
# core/errors.py
class ErrorCode(StrEnum):
    INVALID_FORMAT = "INVALID_FORMAT"
    INVALID_LENGTH = "INVALID_LENGTH"
    INVALID_CHECKSUM = "INVALID_CHECKSUM"
    EMPTY_INPUT = "EMPTY_INPUT"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    VALUE_TOO_LONG = "VALUE_TOO_LONG"
    INVALID_CHARACTER = "INVALID_CHARACTER"
    INVALID_DATE = "INVALID_DATE"
    REPEATED_DIGITS = "REPEATED_DIGITS"

@dataclass(frozen=True, slots=True)
class ErrorObj:
    code: ErrorCode
    message_pt: str
    message_en: str
    suggestion: str | None = None
```

Cada validator/parser instancia `ErrorObj` com mensagens contextuais. Exemplo:
```python
ErrorObj(
    code=ErrorCode.INVALID_LENGTH,
    message_pt="CPF deve ter 11 dígitos; recebido 10.",
    message_en="CPF must have 11 digits; received 10.",
    suggestion="Verifique se o número não está truncado.",
)
```

---

## 5. Telemetria

**Opt-in.** Default OFF.

- Ativação: `BRASIL_MCP_TELEMETRY=1` no environment.
- Anonymous installation ID: UUID4 gerado no primeiro run com telemetria ativa; armazenado em `$XDG_DATA_HOME/brasil-mcp/installation_id` (fallback `~/.brasil-mcp/installation_id`).
- Backend: PostHog (lazy import — `posthog` só é importado se telemetria ativa).
- Evento único: `tool_called` com:
  ```json
  {
    "tool": "validate_cpf",
    "success": true,
    "latency_ms": 0.3,
    "error_code": null,
    "brasil_mcp_version": "0.1.0",
    "python_version": "3.12",
    "platform": "darwin"
  }
  ```
- **Nunca** logado: inputs, outputs, valores de documento, datas específicas, etc.
- Disclosure prominente no README (seção "Telemetria") e no help do CLI (`brasil-mcp telemetry --status`).
- First-run notice: ao executar `brasil-mcp serve` ou qualquer subcomando pela primeira vez SEM env var setada, exibe uma única linha em stderr:
  ```
  ℹ Brasil MCP não coleta telemetria. Para opt-in (anonymous metadata only):
    export BRASIL_MCP_TELEMETRY=1
  ```
  Após mostrar, cria flag de "seen" em `$XDG_DATA_HOME/brasil-mcp/notice_seen` pra não repetir.

---

## 6. Testes

### Cobertura

- Target: ≥90% no `core/`. ≥70% em `adapters/`.
- Ferramenta: `pytest-cov`. Threshold enforçado em CI.

### Estratégia por subsistema

**Validators:**
- Vetores golden por tipo (em `tests/fixtures/validators/<tipo>.json`):
  - Mínimo 5 válidos conhecidos publicamente.
  - 10-20 inválidos cobrindo:
    - Comprimento errado
    - Caracteres inválidos
    - Checksum errado
    - Sequências repetidas (`00000000000`, etc.)
    - Inputs vazios / None
- Smoke test "validate-then-format-then-revalidate" — idempotência.

**CNPJ alfanumérico — caso especial:**
- Vetores válidos com letras nas 12 primeiras posições, incluindo edge cases: todos zeros, todos A's, mistura digits+letters.
- Vetores de teste oficiais da RF quando disponíveis.
- Test que valida que `12345678000195` (legacy válido conhecido) é reconhecido como `format: legacy`.
- Test que valida que um CNPJ alfanumérico com checksum correto é reconhecido como `format: alphanumeric`.

**Boleto:**
- Vetores reais (com PII redacted) de boletos bancários (Itaú, Bradesco, Santander, BB, Caixa) e de arrecadação (concessionária, tributo).
- Test: linha digitável ↔ código de barras conversion é reversível.
- Test: vencimento decode com fator base 1997-10-07.

**PIX:**
- Vetores oficiais do Manual BR Code do Banco Central.
- Test: `generate -> parse` round-trip preserva todos os campos.
- Test: CRC16 contra vetores conhecidos.
- Test: QR PNG gerado é decodável (com `pyzbar` em test-only).

**Calendar:**
- Test: feriados nacionais 2026, 2027 contra calendário oficial.
- Test: feriados estaduais SP, RJ, MG conhecidos.
- Test: `proximo_dia_util` em sexta-feira retorna segunda; em véspera de feriado pula corretamente.

**Adapters:**
- MCP: smoke test que `Server.list_tools()` retorna 14 entries; smoke test que invocar `validate_cpf` via MCP retorna o mesmo que invocar a core fn direto.
- CLI: smoke test cada subcomando com input válido + inválido (via `typer.testing.CliRunner`).

### Tempo

Suíte completa deve rodar em < 5 s em hardware moderno. Tests lentos (geração QR + decode com pyzbar) marcados `@pytest.mark.slow` — rodados em CI mas não localmente por default.

---

## 7. CI/CD

### `.github/workflows/ci.yml`

Triggers: push + pull_request em qualquer branch.

Matrix: Python 3.11, 3.12, 3.13.

Steps:
1. `uv sync --frozen`
2. `uv run ruff check`
3. `uv run ruff format --check`
4. `uv run pyright`
5. `uv run pytest --cov=brasil_mcp --cov-report=xml --cov-fail-under=85`

### `.github/workflows/release.yml`

Trigger: push de tag `v*`.

Steps:
1. `uv sync --frozen`
2. `uv run pytest` (sanity)
3. `uv build`
4. Publish PyPI via **trusted publishing (OIDC)** — `pypa/gh-action-pypi-publish@release/v1`. Sem API key armazenada no repo.
5. Create GitHub Release com changelog extraído de `CHANGELOG.md` (seção `[0.1.0]`).

PyPI trusted publisher precisa ser configurado no PyPI dashboard antes do primeiro release.

---

## 8. README & docs

### README.md (raiz, PT-BR primário)

Estrutura:
1. Hero: nome, badges (PyPI, Python, MIT, CI, downloads), tagline ("MCP server brasileiro, privacy-first, CNPJ alfanumérico-ready").
2. Instalação:
   ```bash
   uv tool install brasil-mcp-essentials
   # ou
   pipx install brasil-mcp-essentials
   ```
3. Quick start CLI: 3 exemplos (`brasil-mcp validate-cpf`, `brasil-mcp parse-boleto`, `brasil-mcp generate-pix-brcode`).
4. Configurar Claude Desktop:
   ```json
   {
     "mcpServers": {
       "brasil-essentials": { "command": "brasil-mcp-server" }
     }
   }
   ```
5. Catálogo de tools (tabela enxuta, links pra `docs/tools.md`).
6. Privacidade & telemetria.
7. Roadmap (Phase 1 expansion → Phase 2 → Phase 3).
8. License: MIT.
9. Seção "English" abaixo de tudo, com mesmos pontos resumidos.

### `docs/tools.md`

Referência completa por tool: nome, descrição, input schema, output shape, erros possíveis, exemplo.

### `CHANGELOG.md`

Keep a Changelog format. Seção `[0.1.0] - 2026-05-21`.

---

## 9. Critérios de aceite (Definition of Done para v0.1.0)

- [ ] Repo `github.com/brasil-mcp/essentials` público, MIT, com tag `v0.1.0`.
- [ ] PyPI: `pip install brasil-mcp-essentials` funciona, retorna versão 0.1.0.
- [ ] `brasil-mcp-server` inicia stdio MCP e expõe 14 tools.
- [ ] `brasil-mcp --help` mostra 14 subcomandos + `serve`.
- [ ] Cada uma das 14 tools tem teste unitário (core) + smoke test (adapter MCP) + smoke test (CLI).
- [ ] CI verde em 3.11, 3.12, 3.13.
- [ ] Coverage ≥85% global.
- [ ] README PT-BR + EN com quick start, badges, e seção de telemetria.
- [ ] CNPJ alfanumérico funcionando com vetores de teste documentados.

---

## 10. Fora de escopo (explicitamente)

Confirmados como **fora da v0.1.0**:
- Lookups com API externa (CEP, FEBRABAN online, cotações, IBGE)
- Transport SSE
- REST API + OpenAPI
- Pacote npm
- Submissão a registries (Smithery, glama.ai, mcp.so, Anthropic Directory)
- DDD / IBGE municipalidade / FEBRABAN como tools standalone

Cada um destes entra em sua própria sprint subsequente desta semana, reusando o `core/` sem refactor.
