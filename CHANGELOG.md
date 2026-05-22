# Changelog

Todas as mudanças importantes deste projeto serão documentadas aqui.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o
projeto segue [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [0.1.2] - 2026-05-22

### Modificado

- `generate_pix_brcode`: `nome_beneficiario` e `cidade` agora são opcionais. Quando omitidos (None ou string vazia), usa defaults `"PAGAMENTO PIX"` e `"BRASIL"` respectivamente. O BR Code spec exige esses campos mas nenhum banco brasileiro valida o conteúdo contra o titular real da chave PIX — o app sobrescreve com o nome do recebedor cadastrado no Banco Central. Defaults são seguros e tornam a API mais ergonômica para callers que não precisam customizar.
- `generate_pix_brcode`: a chave agora é normalizada antes de ir pro BR Code. CPF mascarado (`123.456.789-09`) vira `12345678909`; CNPJ legacy (`33.000.167/0001-01`) vira `33000167000101`; CNPJ alfanumérico (`12.abc.345/01de-35`) vira `12ABC34501DE35`. Email, telefone (com `+`), e chave aleatória (UUID) são preservados como digitados. Garante que o BR Code emitido seja consistente independente de o caller passar a chave com ou sem máscara.

### Adicionado

- `brasil_mcp.core.pix.parser.DEFAULT_NOME_BENEFICIARIO` e `DEFAULT_CIDADE` exportados.
- `brasil_mcp.core.pix.parser._normalize_chave` (pública para inspeção, prefixada com `_` por convenção).
- 11 testes novos cobrindo defaults + normalização.

## [0.1.1] - 2026-05-22

### Adicionado

- Novo entry point `brasil-mcp-essentials` apontando direto para o MCP server stdio. Permite invocar via `uvx brasil-mcp-essentials` sem precisar de `--from`. Atalho ergonômico para MCP clients (Claude Desktop, Cursor, etc.) — os entry points existentes (`brasil-mcp`, `brasil-mcp-server`) continuam funcionando exatamente igual.

## [0.1.0] - 2026-05-21

### Adicionado

- Primeiro release público.
- **14 tools offline em uma única instalação:**
  - **Validators (7):** `validate_cpf`, `validate_cnpj` (legacy + alfanumérico RF NT COCAD/SUARA 49/2024), `validate_pis`, `validate_renavam`, `validate_cnh`, `validate_titulo_eleitor`, `validate_credit_card` (com detecção de Elo + Hipercard brasileiros).
  - **Boleto (1):** `parse_boleto` para linha digitável bancária (47 dígitos), código de barras (44), e arrecadação (48). Inclui tabela bundled com 12 bancos FEBRABAN principais.
  - **PIX (2):** `parse_pix_brcode` e `generate_pix_brcode` com QR Code opcional em PNG base64 e/ou SVG.
  - **Calendar (4):** `is_feriado_nacional`, `proximo_dia_util`, `contar_dias_uteis`, `listar_feriados` (com suporte a feriados estaduais por UF).
- **MCP server stdio** (`brasil-mcp-server`) compatível com Claude Desktop, Cursor, e outros MCP clients.
- **CLI Typer** (`brasil-mcp`) com todos os 14 tools como subcomandos + `serve` + `version`.
- Errors estruturados bilíngue (PT + EN) com códigos enumerados.
- Telemetria opt-in via PostHog — anonymous metadata only, default OFF.
- Suíte de 266 testes unitários cobrindo casos extremos.

[0.1.2]: https://github.com/brasil-mcp/essentials/releases/tag/v0.1.2
[0.1.1]: https://github.com/brasil-mcp/essentials/releases/tag/v0.1.1
[0.1.0]: https://github.com/brasil-mcp/essentials/releases/tag/v0.1.0
