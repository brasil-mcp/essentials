# Changelog

Todas as mudanças importantes deste projeto serão documentadas aqui.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o
projeto segue [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [0.3.0] - 2026-05-22

### Adicionado

- **`lookup_endereco_cep(uf, cidade, logradouro)`** — busca reversa de CEP via ViaCEP. Aceita match parcial (fuzzy lado servidor). Retorna lista de matches com cep, logradouro, complemento, unidade, bairro, cidade, uf, ibge, ddd. Cacheado 30 dias.
- **`validate_telefone(value)`** — valida e normaliza telefone brasileiro. Reconhece celular (11 dígitos com `9` após DDD) e fixo (10 dígitos com 2-5 após DDD). Aceita com/sem `+55`, qualquer máscara. Outputs: `formatted` (`(11) 98765-4321`), `formatted_international` (`+55 11 98765-4321`), `e164` (`+5511987654321`), `ddd`, `tipo` (celular/fixo). Lista oficial Anatel de DDDs válidos.
- **`generate_whatsapp_qr(telefone, mensagem?, qr_format?)`** — gera link wa.me (deeplink universal WhatsApp) + QR opcional (PNG base64 e/ou SVG). Aproveita `validate_telefone` pra normalizar o número. Útil pra cartões de visita, email signature, atendimento.

### Modificado

- Total de **22 MCP tools** registradas (era 19 na 0.2.x).
- 729 testes (era 677), 100% coverage de linhas + branches mantida.

[0.3.0]: https://github.com/brasil-mcp/essentials/releases/tag/v0.3.0
## [0.2.1] - 2026-05-22

### Corrigido

- `lookup_cotacao_brl`: bug crítico que retornava `NETWORK_ERROR` em todas as chamadas devido a 3 erros na URL/params do BCB Olinda:
  - parâmetro era `dataInicial` mas o endpoint `CotacaoMoedaPeriodoFechamento` exige `dataInicialCotacao`;
  - `$orderby=dataHoraCotacao desc` não é permitido pelo BCB — agora ordenação é client-side;
  - `$top=10` causava HTTP 500 — removido.
- Smoke-testado contra BCB live: USD R$5,03, EUR R$5,84 em 2026-05-20.

### Modificado

- `SUPPORTED_MOEDAS`: lista corrigida pelas 10 moedas que o BCB PTAX **de fato** publica vs BRL (descobertas via endpoint `/Moedas` do Olinda):
  - **Adicionadas:** DKK, NOK, SEK (Coroas dinamarquesa, norueguesa, sueca — type A direct).
  - **Removida:** ARS (BCB não publica peso argentino diretamente vs BRL — vira NOT_FOUND em qualquer data).
  - Mantidas: USD, EUR, GBP, JPY, CHF, CAD, AUD.

## [0.2.0] - 2026-05-22

### Adicionado

- **5 lookup tools online** (cobrindo a spec original da Fase 1 que ficou pendente em 0.1.x):
  - `lookup_cep` — endereço por CEP via ViaCEP. Retorna `{ logradouro, complemento, bairro, cidade, uf, ibge, ddd }`.
  - `lookup_banco_febraban` — banco por código FEBRABAN via BrasilAPI (cobre 200+ bancos vs 12 bundled).
  - `lookup_ddd` — UF e municípios por DDD via BrasilAPI.
  - `lookup_ibge_municipio` — código IBGE de município por nome (acento-insensível, UF opcional).
  - `lookup_cotacao_brl` — cotação PTAX BRL via Banco Central. USD, EUR, GBP, JPY, ARS, CHF, CAD, AUD. Suporta data histórica.
- **Camada de cache local** (`core.cache.local`) com TTL configurável. Cache fica em `$XDG_CACHE_HOME/brasil-mcp/lookups/`. TTLs específicos por endpoint (30 dias pra CEP/IBGE, 90 dias pra DDD, 7 dias pra banco, 1 ano pra cotação histórica, 1h pra cotação intraday).
- **Camada HTTP compartilhada** (`core.lookups.http_client`) com retry exponential backoff, timeout configurável e errors estruturados (`NotFoundError`, `NetworkError`, `UpstreamError`).
- 3 códigos de erro novos: `NETWORK_ERROR`, `UPSTREAM_ERROR`, `NOT_FOUND`.
- 5 subcomandos CLI correspondentes (`lookup-cep`, `lookup-banco-febraban`, `lookup-ddd`, `lookup-ibge-municipio`, `lookup-cotacao-brl`).

### Modificado

- Total de **19 MCP tools** registradas (14 offline + 5 online). MCP server stdio expõe todas via mesmo entry point — agente decide qual chamar.
- Pitch atualizado: **"core offline + lookups online opcionais"**. As 14 tools offline da v0.1.x continuam sem rede.
- 676 testes (era 602), 100% coverage de linhas + branches mantida.
- Nova dependência runtime: `httpx>=0.27`.

### Notas

- Lookups são tools separadas — agente decide quando usar. Validações offline (CPF, CNPJ, etc.) NUNCA fazem call HTTP.
- Cache desativável via `cache.clear("namespace")` ou `cache.clear()` em código; via CLI ainda não exposto (TODO v0.2.1).
- MCP SSE transport + REST API ficaram pra v0.3.0.

## [0.1.2] - 2026-05-22

### Modificado

- `generate_pix_brcode`: `nome_beneficiario` e `cidade` agora são opcionais. Quando omitidos, usa defaults `"PAGAMENTO PIX"` e `"BRASIL"`.
- `generate_pix_brcode`: chave normalizada — CPF/CNPJ legacy/CNPJ alfanumérico têm máscaras stripped antes de irem pro BR Code.

## [0.1.1] - 2026-05-22

### Adicionado

- Novo entry point `brasil-mcp-essentials` apontando direto para o MCP server stdio.

## [0.1.0] - 2026-05-21

### Adicionado

- Primeiro release público.
- 14 tools offline em uma única instalação:
  - Validators (7): `validate_cpf`, `validate_cnpj` (legacy + alfanumérico RF NT COCAD/SUARA 49/2024), `validate_pis`, `validate_renavam`, `validate_cnh`, `validate_titulo_eleitor`, `validate_credit_card`.
  - Boleto (1): `parse_boleto`.
  - PIX (2): `parse_pix_brcode` e `generate_pix_brcode`.
  - Calendar (4): `is_feriado_nacional`, `proximo_dia_util`, `contar_dias_uteis`, `listar_feriados`.
- MCP server stdio (`brasil-mcp-server`).
- CLI Typer (`brasil-mcp`).
- Telemetria opt-in via PostHog.

[0.2.1]: https://github.com/brasil-mcp/essentials/releases/tag/v0.2.1
[0.2.0]: https://github.com/brasil-mcp/essentials/releases/tag/v0.2.0
[0.1.2]: https://github.com/brasil-mcp/essentials/releases/tag/v0.1.2
[0.1.1]: https://github.com/brasil-mcp/essentials/releases/tag/v0.1.1
[0.1.0]: https://github.com/brasil-mcp/essentials/releases/tag/v0.1.0
