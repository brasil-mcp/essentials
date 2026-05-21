# Changelog

Todas as mudanças importantes deste projeto serão documentadas aqui.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o
projeto segue [Semantic Versioning](https://semver.org/lang/pt-BR/).

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

[0.1.0]: https://github.com/brasil-mcp/essentials/releases/tag/v0.1.0
