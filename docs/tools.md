# Catálogo de tools — brasil-mcp-essentials v0.1.0

Cada tool é exposta tanto via MCP (nome `snake_case`) quanto via CLI (kebab-case). Os schemas abaixo refletem o input/output efetivo. Erros sempre seguem `{ code, message_pt, message_en, suggestion?: str }`.

**Códigos de erro possíveis (genéricos):**

| Code | Quando |
|---|---|
| `EMPTY_INPUT` | input vazio ou só whitespace |
| `INVALID_CHARACTER` | input contém caracteres não permitidos |
| `INVALID_LENGTH` | tamanho incorreto após normalização |
| `INVALID_FORMAT` | shape geral inválido |
| `INVALID_CHECKSUM` | dígitos verificadores não conferem |
| `REPEATED_DIGITS` | todos os dígitos iguais (rejeitado para CPF, CNPJ, PIS, CNH) |
| `UNSUPPORTED_FORMAT` | input identificado mas não suportado |
| `MISSING_REQUIRED_FIELD` | argumento obrigatório ausente (geradores) |

---

## Validators

### `validate_cpf`

Valida CPF brasileiro (11 dígitos). Módulo 11. Rejeita sequências repetidas como `00000000000`, `11111111111`, etc.

**Input:** `{ "value": "12345678909" | "123.456.789-09" }`
**Output:**
```json
{
  "valid": true,
  "formatted": "529.982.247-25",
  "raw": "52998224725",
  "error": null
}
```

**CLI:** `brasil-mcp validate-cpf 52998224725`

---

### `validate_cnpj`

Valida CNPJ brasileiro. **Auto-detecta** formato legacy (14 dígitos) ou alfanumérico novo (Receita Federal NT COCAD/SUARA nº 49/2024 — vigente a partir de julho/2026).

Algoritmo alfanumérico: cada caractere mapeado por `ord(c) - 48` (digits 0-9 → 0-9, letras A-Z → 17-42), módulo 11 com pesos padrão. DVs sempre numéricos.

**Input:** `{ "value": "11.222.333/0001-81" | "12ABC34501DE35" }`
**Output:**
```json
{
  "valid": true,
  "formatted": "11.222.333/0001-81",
  "raw": "11222333000181",
  "format": "legacy",
  "error": null
}
```

`format` é `"legacy"` ou `"alphanumeric"`.

**CLI:** `brasil-mcp validate-cnpj 11222333000181`

---

### `validate_pis`

Valida PIS/PASEP/NIT (11 dígitos). Módulo 11 com pesos `[3,2,9,8,7,6,5,4,3,2]`.

**Input:** `{ "value": "120.6789.012-5" }`
**Output:** shape padrão (`valid`, `formatted`, `raw`, `error`).

**CLI:** `brasil-mcp validate-pis 12067890125`

---

### `validate_renavam`

Valida RENAVAM (9-11 dígitos, padded para 11). Algoritmo: inverte os 10 primeiros dígitos, pesos `[2,3,4,5,6,7,8,9,2,3]`, `DV = (sum * 10) % 11` (0 se mod=10).

**Input:** `{ "value": "12345678900" }`
**Output:** shape padrão.

**CLI:** `brasil-mcp validate-renavam 12345678900`

---

### `validate_cnh`

Valida CNH brasileira (11 dígitos). Dois DVs com weights decrescentes/crescentes e regra de discount.

**CLI:** `brasil-mcp validate-cnh 12345678901`

---

### `validate_titulo_eleitor`

Valida título de eleitor (12 dígitos). Inclui detecção de UF embutida.

**Output (extras):** `{ "uf": "SP" }` ou `"Exterior"` para código 28.

**CLI:** `brasil-mcp validate-titulo-eleitor 123456789012`

---

### `validate_credit_card`

Valida cartão de crédito via Luhn (12-19 dígitos). Detecta bandeira por BIN: **Visa, Mastercard, Elo (BR), Hipercard (BR), Amex, Diners, JCB, Discover.**

**Output (extras):** `{ "brand": "visa" | "mastercard" | "elo" | "hipercard" | "amex" | "diners" | "jcb" | "discover" | null }`.

**CLI:** `brasil-mcp validate-credit-card "4111 1111 1111 1111"`

---

## Boleto

### `parse_boleto`

Faz parse de boleto brasileiro a partir de:
- **Linha digitável bancária** (47 dígitos)
- **Código de barras bancário** (44 dígitos)
- **Linha digitável de arrecadação** (48 dígitos, começando com `8`)

Auto-detecta tipo bancário vs arrecadação pelo primeiro dígito.

**Input:** `{ "value": "34191790010104351004791020150008291070026000" }`

**Output (bancário):**
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
  "fator_vencimento": 10500,
  "nosso_numero": "...",
  "segmento_arrecadacao": null,
  "raw": "...",
  "error": null
}
```

**Output (arrecadação):** `tipo: "arrecadacao"`, `banco: null`, `segmento_arrecadacao: "tributo_estadual" | ...`.

Segmentos suportados: `tributo_municipal`, `concessionaria_agua_saneamento`, `concessionaria_eletrica`, `concessionaria_telefonia`, `tributo_federal`, `carnes_assemelhados`, `multas_transito`, `tributo_estadual`, `outros`.

**Fator de vencimento:** base 1997-10-07 = fator 1000. Em 2025-02-22 FEBRABAN reiniciou em 1000 (heurística automática no parser).

**CLI:** `brasil-mcp parse-boleto "34191790010104351004791020150008291070026000"`

---

## PIX

### `parse_pix_brcode`

Decoda BR Code PIX (string EMV TLV). Suporta estático e dinâmico.

**Input:** `{ "value": "00020126360014BR.GOV.BCB.PIX..." }`

**Output:**
```json
{
  "valid": true,
  "chave": "joao@example.com",
  "tipo_chave": "email",
  "beneficiario": "JOAO DA SILVA",
  "cidade": "SAO PAULO",
  "valor": 12345,
  "moeda": "BRL",
  "txid": "PEDIDO12345",
  "descricao": "Pagamento NF",
  "dinamico": false,
  "url_provedor": null,
  "raw": "...",
  "error": null
}
```

`tipo_chave`: `cpf | cnpj | telefone | email | aleatoria`.

**CLI:** `brasil-mcp parse-pix-brcode "00020126..."`

---

### `generate_pix_brcode`

Gera BR Code PIX estático.

**Input:**
```json
{
  "chave": "joao@example.com",
  "nome_beneficiario": "Joao da Silva",
  "cidade": "Sao Paulo",
  "valor": 12345,
  "txid": "PEDIDO12345",
  "descricao": "Pagamento NF",
  "qr_format": "none"
}
```

Constraints:
- `nome_beneficiario`: max 25 chars (acentos removidos, uppercase)
- `cidade`: max 15 chars (idem)
- `txid`: max 25 chars
- `descricao`: max 72 chars
- `qr_format`: `"none" | "png" | "svg" | "both"`

**Output:**
```json
{
  "brcode": "00020126360014BR.GOV.BCB.PIX...6304ABCD",
  "qr_png_base64": "iVBORw0KGgo...",
  "qr_svg": "<svg>...</svg>",
  "error": null
}
```

`qr_png_base64` é populado se `qr_format ∈ {png, both}`. `qr_svg` se `qr_format ∈ {svg, both}`.

**CLI:**
```bash
brasil-mcp generate-pix-brcode \
  --chave joao@example.com \
  --nome "Joao da Silva" \
  --cidade "Sao Paulo" \
  --valor 12345 \
  --qr both
```

---

## Calendar

### `is_feriado_nacional`

Verifica se uma data é feriado brasileiro.

**Input:** `{ "date": "2026-09-07", "uf": "SP" }` (uf opcional)
**Output:**
```json
{ "is_feriado": true, "nome": "Independência do Brasil", "esfera": "nacional", "raw_date": "2026-09-07" }
```

`esfera`: `"nacional"` ou `"estadual"` (quando uf fornecido e a data é feriado estadual).

**CLI:** `brasil-mcp is-feriado 2026-09-07 --uf SP`

---

### `proximo_dia_util`

Retorna o próximo dia útil após uma data (pula fins de semana + feriados).

**Input:** `{ "date": "2026-05-22", "uf": "SP", "include_today": false }`
**Output:** `{ "date": "2026-05-25", "dias_pulados": 2 }`

`include_today`: se `true`, retorna a própria data se já for dia útil.

**CLI:** `brasil-mcp proximo-dia-util 2026-05-22`

---

### `contar_dias_uteis`

Conta dias úteis entre duas datas.

**Input:** `{ "start_date": "2026-09-01", "end_date": "2026-09-30", "uf": "SP", "inclusive_end": false }`
**Output:**
```json
{
  "count": 21,
  "total_dias": 29,
  "feriados_no_periodo": [{"date": "2026-09-07", "nome": "Independência do Brasil"}]
}
```

`inclusive_end`: se `true`, inclui `end_date` na contagem.

**CLI:** `brasil-mcp contar-dias-uteis 2026-09-01 2026-09-30`

---

### `listar_feriados`

Lista feriados brasileiros de um ano.

**Input:** `{ "year": 2026, "uf": "SP" }`
**Output:**
```json
{
  "ano": 2026,
  "uf": "SP",
  "feriados": [
    {"date": "2026-01-01", "nome": "Confraternização Universal", "esfera": "nacional"},
    {"date": "2026-04-21", "nome": "Tiradentes", "esfera": "nacional"},
    {"date": "2026-07-09", "nome": "Revolução Constitucionalista", "esfera": "estadual"}
  ]
}
```

**CLI:** `brasil-mcp listar-feriados 2026 --uf SP`

---

## Telemetria

Default **OFF**. Para opt-in:

```bash
export BRASIL_MCP_TELEMETRY=1
```

Quando ativa, cada chamada de tool envia um evento `tool_called` com:

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

**Nunca** logado: o input (CPF, CNPJ, valores, etc.), o output, ou qualquer dado PII.

ID anônimo gerado uma vez e armazenado em `$XDG_DATA_HOME/brasil-mcp/installation_id` (fallback `~/.local/share/brasil-mcp/installation_id`).

Backend: PostHog. Configurável via `BRASIL_MCP_POSTHOG_KEY` se quiser apontar para sua própria instância.
