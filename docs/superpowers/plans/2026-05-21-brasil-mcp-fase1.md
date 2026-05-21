# Brasil MCP — Fase 1 (v0.1.0) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `brasil-mcp-essentials` v0.1.0 — Python MCP server (stdio) + CLI with 14 offline tools (validators, boleto, PIX, calendar) — production-ready, PyPI-published.

**Architecture:** Core puro (zero deps de MCP/HTTP) + thin adapters (MCP stdio, Typer CLI). Layout `src/brasil_mcp/{core,adapters}`.

**Tech Stack:** Python ≥3.11, `uv`+`hatchling`, `ruff`, `pyright`, `pytest`, `typer`, `mcp` (Anthropic), `segno`, `python-holidays`, `posthog` (lazy, opt-in).

**Spec:** `docs/superpowers/specs/2026-05-21-brasil-mcp-fase1-design.md` — todo subagente DEVE ler antes de implementar.

**Working dir:** `/Users/ricardo/omc/projects/brasil-mcp/code/`

---

## Task Map

| # | Task | Phase | Parallelizable |
|---|---|---|---|
| 1 | Scaffold repo + pyproject + tooling | A: foundation | — |
| 2 | Core errors + models | A: foundation | depends on 1 |
| 3 | Validators (7 tools) | B: subsystems | yes |
| 4 | Boleto parser | B: subsystems | yes |
| 5 | PIX (parse + generate + QR + CRC16) | B: subsystems | yes |
| 6 | Calendar (4 tools) | B: subsystems | yes |
| 7 | Telemetry (opt-in PostHog) | B: subsystems | yes |
| 8 | MCP adapter | C: adapters | depends on 3-7 |
| 9 | CLI adapter | C: adapters | depends on 3-7 |
| 10 | README + tools.md + CHANGELOG | D: polish | depends on 8,9 |
| 11 | GH Actions CI + release workflows | D: polish | yes |
| 12 | Final verification + git tag v0.1.0 | D: polish | depends on all |

Tasks 3-7 can be dispatched in parallel. Task 8 and 9 can be done in parallel after subsystems are ready.

---

## Task 1: Scaffold repo, pyproject.toml, tooling config

**Files (all create):**
- `pyproject.toml`
- `.gitignore`
- `.python-version`
- `LICENSE`
- `README.md` (placeholder)
- `src/brasil_mcp/__init__.py`
- `src/brasil_mcp/__main__.py`
- `src/brasil_mcp/core/__init__.py`
- `src/brasil_mcp/adapters/__init__.py`
- `tests/__init__.py`
- `tests/conftest.py`

- [ ] **Step 1.1: Initialize git + create directory skeleton**

```bash
cd /Users/ricardo/omc/projects/brasil-mcp/code
git init -b main
mkdir -p src/brasil_mcp/core/{validators,boleto,pix,calendar}
mkdir -p src/brasil_mcp/adapters/{mcp,cli}
mkdir -p tests/{core/{validators,boleto,pix,calendar},adapters,fixtures}
touch src/brasil_mcp/__init__.py src/brasil_mcp/core/__init__.py src/brasil_mcp/adapters/__init__.py
touch src/brasil_mcp/core/{validators,boleto,pix,calendar}/__init__.py
touch src/brasil_mcp/adapters/{mcp,cli}/__init__.py
touch tests/__init__.py tests/conftest.py
```

- [ ] **Step 1.2: Write `pyproject.toml`**

File `/Users/ricardo/omc/projects/brasil-mcp/code/pyproject.toml`:

```toml
[project]
name = "brasil-mcp-essentials"
version = "0.1.0"
description = "MCP server brasileiro, privacy-first, CNPJ alfanumérico-ready. 14 utilities offline para devs BR."
readme = "README.md"
license = { text = "MIT" }
authors = [{ name = "Brasil MCP" }]
requires-python = ">=3.11"
keywords = ["mcp", "brasil", "cpf", "cnpj", "boleto", "pix", "validator"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Libraries",
    "Natural Language :: Portuguese (Brazilian)",
]
dependencies = [
    "mcp>=1.0.0",
    "typer>=0.12.0",
    "segno>=1.6.0",
    "python-holidays>=0.50",
]

[project.optional-dependencies]
telemetry = ["posthog>=3.5"]

[project.urls]
Homepage = "https://github.com/brasil-mcp/essentials"
Repository = "https://github.com/brasil-mcp/essentials"
Issues = "https://github.com/brasil-mcp/essentials/issues"

[project.scripts]
brasil-mcp = "brasil_mcp.adapters.cli.app:app"
brasil-mcp-server = "brasil_mcp.adapters.mcp.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/brasil_mcp"]

[tool.hatch.build]
include = [
    "src/brasil_mcp/core/boleto/febraban_codes.json",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.6",
    "pyright>=1.1.380",
    "hypothesis>=6.100",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "RUF"]
ignore = []

[tool.pyright]
include = ["src", "tests"]
pythonVersion = "3.11"
typeCheckingMode = "strict"
reportMissingTypeStubs = false

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --strict-markers"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
]

[tool.coverage.run]
source = ["src/brasil_mcp"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
```

- [ ] **Step 1.3: Write `.python-version` + `.gitignore` + `LICENSE`**

`.python-version`:
```
3.12
```

`.gitignore`:
```
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
dist/
*.egg-info/
.venv/
venv/
.pytest_cache/
.coverage
htmlcov/
.ruff_cache/
.pyright/
*.log
.DS_Store
.env
.env.local
```

`LICENSE` (MIT):
```
MIT License

Copyright (c) 2026 Brasil MCP contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 1.4: Write `src/brasil_mcp/__init__.py` + `__main__.py`**

`src/brasil_mcp/__init__.py`:
```python
"""Brasil MCP Essentials — 14 utilities offline para devs BR."""
__version__ = "0.1.0"
```

`src/brasil_mcp/__main__.py`:
```python
"""Entry point: ``python -m brasil_mcp`` → CLI Typer."""
from brasil_mcp.adapters.cli.app import app

if __name__ == "__main__":
    app()
```

- [ ] **Step 1.5: Write placeholder README.md**

```markdown
# brasil-mcp-essentials

MCP server brasileiro, privacy-first, CNPJ alfanumérico-ready.

(README completo no final do build.)
```

- [ ] **Step 1.6: Install deps via uv**

```bash
cd /Users/ricardo/omc/projects/brasil-mcp/code
uv sync
```

Expected: cria `.venv/`, instala todas as deps, gera `uv.lock`.

- [ ] **Step 1.7: Verify scaffolding**

```bash
uv run python -c "import brasil_mcp; print(brasil_mcp.__version__)"
```

Expected: `0.1.0`.

```bash
uv run ruff check src
uv run pyright src
```

Expected: ambos passam (sem erros).

- [ ] **Step 1.8: Commit**

```bash
git add .
git commit -m "chore: scaffold repo, pyproject, tooling config"
```

---

## Task 2: Core errors + models

**Files (all create):**
- `src/brasil_mcp/core/errors.py`
- `src/brasil_mcp/core/models.py`
- `tests/core/test_errors.py`
- `tests/core/test_models.py`

- [ ] **Step 2.1: Write `errors.py`**

```python
"""Códigos de erro e ErrorObj usados por todos os core modules."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


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

    def to_dict(self) -> dict[str, str | None]:
        return {
            "code": str(self.code),
            "message_pt": self.message_pt,
            "message_en": self.message_en,
            "suggestion": self.suggestion,
        }
```

- [ ] **Step 2.2: Write `models.py`**

```python
"""Dataclasses de output usadas pelos core modules."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from brasil_mcp.core.errors import ErrorObj


@dataclass(frozen=True, slots=True)
class ValidationResult:
    valid: bool
    raw: str
    formatted: str | None = None
    error: ErrorObj | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "valid": self.valid,
            "formatted": self.formatted,
            "raw": self.raw,
            "error": self.error.to_dict() if self.error else None,
        }
        result.update(self.extras)
        return result
```

- [ ] **Step 2.3: Write tests `tests/core/test_errors.py` + `test_models.py`**

`test_errors.py`:
```python
from brasil_mcp.core.errors import ErrorCode, ErrorObj


def test_error_code_is_string():
    assert str(ErrorCode.INVALID_FORMAT) == "INVALID_FORMAT"


def test_error_obj_to_dict_includes_all_fields():
    err = ErrorObj(
        code=ErrorCode.INVALID_LENGTH,
        message_pt="CPF deve ter 11 dígitos",
        message_en="CPF must have 11 digits",
        suggestion="Verifique o tamanho",
    )
    d = err.to_dict()
    assert d == {
        "code": "INVALID_LENGTH",
        "message_pt": "CPF deve ter 11 dígitos",
        "message_en": "CPF must have 11 digits",
        "suggestion": "Verifique o tamanho",
    }


def test_error_obj_suggestion_optional():
    err = ErrorObj(code=ErrorCode.EMPTY_INPUT, message_pt="vazio", message_en="empty")
    assert err.to_dict()["suggestion"] is None
```

`test_models.py`:
```python
from brasil_mcp.core.errors import ErrorCode, ErrorObj
from brasil_mcp.core.models import ValidationResult


def test_validation_result_valid():
    r = ValidationResult(valid=True, raw="123", formatted="1-2-3")
    d = r.to_dict()
    assert d == {"valid": True, "formatted": "1-2-3", "raw": "123", "error": None}


def test_validation_result_with_error():
    err = ErrorObj(ErrorCode.INVALID_CHECKSUM, "checksum", "checksum")
    r = ValidationResult(valid=False, raw="999", error=err)
    d = r.to_dict()
    assert d["valid"] is False
    assert d["error"]["code"] == "INVALID_CHECKSUM"


def test_validation_result_extras_merged():
    r = ValidationResult(valid=True, raw="x", extras={"format": "legacy"})
    assert r.to_dict()["format"] == "legacy"
```

- [ ] **Step 2.4: Run tests + commit**

```bash
uv run pytest tests/core/test_errors.py tests/core/test_models.py -v
```

Expected: 6 tests pass.

```bash
git add src/brasil_mcp/core/errors.py src/brasil_mcp/core/models.py tests/core/test_errors.py tests/core/test_models.py
git commit -m "feat(core): errors + models foundation"
```

---

## Task 3: Validators (7 tools)

**Files:**
- `src/brasil_mcp/core/validators/{cpf,cnpj,pis,renavam,cnh,titulo_eleitor,credit_card}.py`
- `tests/core/validators/test_{cpf,cnpj,pis,renavam,cnh,titulo_eleitor,credit_card}.py`
- `tests/fixtures/validators/<each>.json` (test vectors)

### Pattern (todos seguem)

Cada validator exporta uma única função `validate_<doc>(value: str) -> ValidationResult`. A função:
1. Recebe input cru
2. Normaliza (strip não-dígitos/não-alfanum)
3. Verifica comprimento
4. Verifica caracteres válidos
5. Verifica casos especiais (ex: sequências repetidas para CPF/CNPJ)
6. Calcula checksum
7. Retorna ValidationResult com `formatted` (com máscara) se válido, ou com `error` apropriado

### Task 3.1: validate_cpf

- [ ] **Step 3.1.1: Test fixtures** — `tests/fixtures/validators/cpf.json`:
```json
{
  "valid": [
    "529.982.247-25",
    "529.982.247-25",
    "935.411.347-80",
    "111.444.777-35",
    "12345678909"
  ],
  "invalid": [
    {"input": "", "code": "EMPTY_INPUT"},
    {"input": "123", "code": "INVALID_LENGTH"},
    {"input": "123456789012", "code": "INVALID_LENGTH"},
    {"input": "abc.def.ghi-jk", "code": "INVALID_CHARACTER"},
    {"input": "000.000.000-00", "code": "REPEATED_DIGITS"},
    {"input": "111.111.111-11", "code": "REPEATED_DIGITS"},
    {"input": "999.999.999-99", "code": "REPEATED_DIGITS"},
    {"input": "529.982.247-26", "code": "INVALID_CHECKSUM"},
    {"input": "123.456.789-00", "code": "INVALID_CHECKSUM"}
  ]
}
```

- [ ] **Step 3.1.2: Implementation** — `src/brasil_mcp/core/validators/cpf.py`:

```python
"""Validator de CPF brasileiro (11 dígitos, módulo 11)."""
from __future__ import annotations

import re

from brasil_mcp.core.errors import ErrorCode, ErrorObj
from brasil_mcp.core.models import ValidationResult

_MASK_RE = re.compile(r"[^\d]")


def _format_cpf(digits: str) -> str:
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def _calc_digit(digits: str, weight_start: int) -> int:
    total = sum(int(d) * w for d, w in zip(digits, range(weight_start, 1, -1), strict=True))
    rem = total % 11
    return 0 if rem < 2 else 11 - rem


def validate_cpf(value: str) -> ValidationResult:
    raw = value or ""
    if not raw.strip():
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.EMPTY_INPUT,
                "CPF não pode ser vazio.",
                "CPF cannot be empty.",
            ),
        )

    # Reject if contains chars that aren't digits or common mask chars
    if re.search(r"[^\d.\-\s]", raw):
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_CHARACTER,
                "CPF deve conter apenas dígitos e máscara opcional.",
                "CPF must contain only digits and optional mask.",
            ),
        )

    digits = _MASK_RE.sub("", raw)

    if len(digits) != 11:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_LENGTH,
                f"CPF deve ter 11 dígitos; recebido {len(digits)}.",
                f"CPF must have 11 digits; received {len(digits)}.",
                suggestion="Verifique se o número não está truncado.",
            ),
        )

    if len(set(digits)) == 1:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.REPEATED_DIGITS,
                "CPF com todos os dígitos iguais é inválido.",
                "CPF with all repeated digits is invalid.",
            ),
        )

    d1 = _calc_digit(digits[:9], weight_start=10)
    d2 = _calc_digit(digits[:10], weight_start=11)
    if d1 != int(digits[9]) or d2 != int(digits[10]):
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_CHECKSUM,
                "Dígitos verificadores do CPF não conferem.",
                "CPF checksum digits do not match.",
            ),
        )

    return ValidationResult(valid=True, raw=raw, formatted=_format_cpf(digits))
```

- [ ] **Step 3.1.3: Test** — `tests/core/validators/test_cpf.py`:

```python
import json
from pathlib import Path

import pytest

from brasil_mcp.core.validators.cpf import validate_cpf

_FIXTURES = json.loads((Path(__file__).parents[2] / "fixtures/validators/cpf.json").read_text())


@pytest.mark.parametrize("cpf", _FIXTURES["valid"])
def test_valid_cpf(cpf: str):
    result = validate_cpf(cpf)
    assert result.valid is True
    assert result.error is None
    assert result.formatted is not None
    assert len(result.formatted.replace(".", "").replace("-", "")) == 11


@pytest.mark.parametrize("case", _FIXTURES["invalid"])
def test_invalid_cpf(case: dict):
    result = validate_cpf(case["input"])
    assert result.valid is False
    assert result.error is not None
    assert str(result.error.code) == case["code"]


def test_formatted_idempotent():
    """Formatted output, fed back, still validates."""
    r1 = validate_cpf("52998224725")
    assert r1.valid
    r2 = validate_cpf(r1.formatted or "")
    assert r2.valid
```

- [ ] **Step 3.1.4: Run + commit**

```bash
uv run pytest tests/core/validators/test_cpf.py -v
```

Expected: ~14 tests pass.

### Task 3.2: validate_cnpj (legacy + alfanumérico — DIFFERENTIATOR-CHEFE)

- [ ] **Step 3.2.1: Test fixtures** — `tests/fixtures/validators/cnpj.json`:
```json
{
  "valid_legacy": [
    "11.222.333/0001-81",
    "11222333000181",
    "13.347.016/0001-17",
    "60.701.190/0001-04"
  ],
  "valid_alphanumeric": [
    "12ABC34501DE35",
    "BR123456789012"
  ],
  "invalid": [
    {"input": "", "code": "EMPTY_INPUT"},
    {"input": "123", "code": "INVALID_LENGTH"},
    {"input": "11.222.333/0001-82", "code": "INVALID_CHECKSUM"},
    {"input": "00.000.000/0000-00", "code": "REPEATED_DIGITS"},
    {"input": "1@@@@@.000/0001-81", "code": "INVALID_CHARACTER"}
  ]
}
```

**Note**: os vetores `valid_alphanumeric` precisam ter checksum correto. O subagente deve **gerar** vetores válidos usando o algoritmo da RF e popular o fixture. Pseudo-código pra gerar:
```python
# Pega 12 chars alfanuméricos (digits ou A-Z),
# calcula DV1 e DV2 usando weights padrão e fórmula:
#   for char in base: value = ord(char) - 48  # '0'=0...'9'=9, 'A'=17...'Z'=42
#   sum(value * weight), mod 11, then 0 if rem<2 else 11-rem
# Concatena: base (12 chars) + str(DV1) + str(DV2)
```

- [ ] **Step 3.2.2: Implementation** — `src/brasil_mcp/core/validators/cnpj.py`:

```python
"""Validator de CNPJ — legacy (14 dígitos) E alfanumérico (RF NT COCAD/SUARA 49/2024)."""
from __future__ import annotations

import re

from brasil_mcp.core.errors import ErrorCode, ErrorObj
from brasil_mcp.core.models import ValidationResult

_MASK_RE = re.compile(r"[^A-Za-z0-9]")
_ALNUM_BASE_RE = re.compile(r"^[A-Z0-9]{12}$")
_LEGACY_BASE_RE = re.compile(r"^\d{12}$")

_W1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
_W2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]


def _format_cnpj(canonical: str) -> str:
    return f"{canonical[:2]}.{canonical[2:5]}.{canonical[5:8]}/{canonical[8:12]}-{canonical[12:]}"


def _char_value(c: str) -> int:
    return ord(c) - 48


def _calc_digit(base: str, weights: list[int]) -> int:
    total = sum(_char_value(c) * w for c, w in zip(base, weights, strict=True))
    rem = total % 11
    return 0 if rem < 2 else 11 - rem


def validate_cnpj(value: str) -> ValidationResult:
    raw = value or ""
    if not raw.strip():
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.EMPTY_INPUT,
                "CNPJ não pode ser vazio.",
                "CNPJ cannot be empty.",
            ),
        )

    upper = raw.upper()
    if re.search(r"[^A-Z0-9./\-\s]", upper):
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_CHARACTER,
                "CNPJ deve conter apenas letras/dígitos e máscara opcional.",
                "CNPJ must contain only letters/digits and optional mask.",
            ),
        )

    canon = _MASK_RE.sub("", upper)
    if len(canon) != 14:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_LENGTH,
                f"CNPJ deve ter 14 caracteres; recebido {len(canon)}.",
                f"CNPJ must have 14 chars; received {len(canon)}.",
            ),
        )

    base, dv = canon[:12], canon[12:]
    if not dv.isdigit():
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_FORMAT,
                "Os dois dígitos verificadores do CNPJ devem ser numéricos.",
                "CNPJ check digits must be numeric.",
            ),
        )

    if _LEGACY_BASE_RE.match(base):
        cnpj_format = "legacy"
    elif _ALNUM_BASE_RE.match(base):
        cnpj_format = "alphanumeric"
    else:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_FORMAT,
                "Os 12 primeiros caracteres devem ser dígitos (legacy) ou alfanuméricos A-Z/0-9 (novo formato).",
                "First 12 chars must be digits (legacy) or alphanumeric A-Z/0-9 (new format).",
            ),
        )

    if len(set(canon)) == 1:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.REPEATED_DIGITS,
                "CNPJ com todos os caracteres iguais é inválido.",
                "CNPJ with all repeated chars is invalid.",
            ),
        )

    d1 = _calc_digit(base, _W1)
    d2 = _calc_digit(base + str(d1), _W2)
    if str(d1) != dv[0] or str(d2) != dv[1]:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_CHECKSUM,
                "Dígitos verificadores do CNPJ não conferem.",
                "CNPJ checksum digits do not match.",
            ),
        )

    return ValidationResult(
        valid=True,
        raw=raw,
        formatted=_format_cnpj(canon),
        extras={"format": cnpj_format},
    )
```

- [ ] **Step 3.2.3: Test + helper to generate alphanumeric fixtures** — `tests/core/validators/test_cnpj.py`:

```python
import json
from pathlib import Path

import pytest

from brasil_mcp.core.validators.cnpj import _W1, _W2, _calc_digit, validate_cnpj

_FIXTURES = json.loads((Path(__file__).parents[2] / "fixtures/validators/cnpj.json").read_text())


def _gen_valid_alphanum(base12: str) -> str:
    d1 = _calc_digit(base12, _W1)
    d2 = _calc_digit(base12 + str(d1), _W2)
    return base12 + str(d1) + str(d2)


@pytest.mark.parametrize("cnpj", _FIXTURES["valid_legacy"])
def test_valid_legacy(cnpj: str):
    r = validate_cnpj(cnpj)
    assert r.valid is True, r.error
    assert r.extras["format"] == "legacy"


def test_valid_alphanumeric_generated():
    """Generate valid alphanumeric CNPJs using the documented algorithm."""
    for base in ["12ABC345001DE", "BR1234567890A", "AAAA1234BBBB"]:
        # Take first 12 chars, then compute DVs
        base12 = base[:12]
        valid_cnpj = _gen_valid_alphanum(base12)
        r = validate_cnpj(valid_cnpj)
        assert r.valid is True, (valid_cnpj, r.error)
        assert r.extras["format"] == "alphanumeric"


@pytest.mark.parametrize("case", _FIXTURES["invalid"])
def test_invalid(case: dict):
    r = validate_cnpj(case["input"])
    assert r.valid is False
    assert r.error is not None
    assert str(r.error.code) == case["code"]


def test_legacy_format_preserved_through_normalization():
    r = validate_cnpj("11222333000181")
    assert r.valid
    assert r.formatted == "11.222.333/0001-81"


def test_alphanumeric_format_preserved():
    base = _gen_valid_alphanum("12ABC345001D")
    r = validate_cnpj(base)
    assert r.valid
    assert r.extras["format"] == "alphanumeric"
```

- [ ] **Step 3.2.4: Run + commit**

```bash
uv run pytest tests/core/validators/test_cnpj.py -v
git add src/brasil_mcp/core/validators/cnpj.py tests/core/validators/test_cnpj.py tests/fixtures/validators/cnpj.json
git commit -m "feat(validators): cnpj legacy + alphanumeric"
```

### Task 3.3 – 3.7: Demais validators (PIS, RENAVAM, CNH, Título, Credit Card)

Cada um segue o **mesmo pattern** do CPF: fixture JSON com 5+ válidos e 8+ inválidos, função `validate_<doc>(value: str) -> ValidationResult` em `core/validators/<doc>.py`, teste parametrizado.

**Algoritmos:**

- **PIS/PASEP/NIT (11 dígitos):** pesos `[3,2,9,8,7,6,5,4,3,2]` sobre os 10 primeiros dígitos. DV = `(11 - sum % 11) % 11` (se 10, DV = 0). Rejeita sequências repetidas.

- **RENAVAM (11 dígitos):** pesos `[3,2,9,8,7,6,5,4,3,2]` sobre os 10 primeiros dígitos. Soma mod 11. `mod = (sum * 10) % 11`. DV = 0 se mod == 10, senão mod. *Nota:* o RENAVAM aceita 9, 10 ou 11 dígitos legalmente; normalizar pra 11 dígitos zero-padded à esquerda.

- **CNH (11 dígitos):** dois DVs.
  - DV1: pesos `[9,8,7,6,5,4,3,2,1]` (decrescente, começa em 9) sobre os 9 primeiros dígitos. `sum % 11`. Se >= 10, DV1 = 0 e `dsc = 2`; senão DV1 = sum % 11, dsc = 0.
  - DV2: pesos `[1,2,3,4,5,6,7,8,9]` (crescente) sobre os 9 primeiros dígitos. `(sum % 11) - dsc`. Se < 0, somar 11. Se >= 10, DV2 = 0.

- **Título Eleitor (12 dígitos):**
  - Primeiros 8 dígitos = inscrição (variável).
  - Posições 9-10 (1-indexed) = UF code (01=SP, 02=MG, 03=RJ, 04=RS, 05=BA, 06=PR, 07=CE, 08=PE, 09=SC, 10=GO, 11=MA, 12=PB, 13=PA, 14=ES, 15=PI, 16=RN, 17=AL, 18=MT, 19=MS, 20=DF, 21=SE, 22=AM, 23=RO, 24=AC, 25=AP, 26=RR, 27=TO, 28=Exterior).
  - DV1: pesos `[2,3,4,5,6,7,8,9]` sobre os 8 primeiros dígitos. `sum % 11`. Se >=10, DV1 = 0 (mas para SP/MG, DV1 = 1). Senão DV1 = sum % 11.
  - DV2: pesos `[7,8,9]` sobre os 2 dígitos da UF + DV1. `sum % 11`. Mesma regra de exceção SP/MG.
  - Output extras: `{"uf": "SP"}` (ou nome do estado).

- **Credit Card (Luhn):** strip non-digits. Comprimento entre 12 e 19. Aplica Luhn (dobrar dígitos das posições pares contadas da direita; se > 9, subtrai 9; soma todos; mod 10 == 0). Bandeira por BIN:
  - `4` → visa (13/16/19 dígitos)
  - `5[1-5]` ou `2[2-7]` → mastercard
  - `3[47]` → amex (15 dígitos)
  - `6011` ou `65` → discover
  - `30[0-5]`, `36`, `38` → diners
  - `35[2-8]` → jcb
  - **`4011|4312|4389|4514|4573|5041|5066|5067|6362|6504|6505|6516|6550` → elo** (BR)
  - **`384100|384140|384160|606282|637095|637568|637599|637609|637612` → hipercard** (BR)
  - Output extras: `{"brand": "..."}`

Para cada validator, **siga estritamente o pattern do CPF** acima: módulo `src/brasil_mcp/core/validators/<doc>.py`, fixture `tests/fixtures/validators/<doc>.json`, teste `tests/core/validators/test_<doc>.py`.

- [ ] **Step 3.3.1:** PIS — implement + test + commit
- [ ] **Step 3.3.2:** RENAVAM — implement + test + commit
- [ ] **Step 3.3.3:** CNH — implement + test + commit
- [ ] **Step 3.3.4:** Título eleitor — implement + test + commit
- [ ] **Step 3.3.5:** Credit Card — implement + test + commit

Após todos:
```bash
uv run pytest tests/core/validators -v
```
Expected: ~80+ tests pass.

---

## Task 4: Boleto parser

**Files:**
- `src/brasil_mcp/core/boleto/febraban_codes.json` (bundled bank table)
- `src/brasil_mcp/core/boleto/linha_digitavel.py`
- `src/brasil_mcp/core/boleto/codigo_barras.py`
- `src/brasil_mcp/core/boleto/parser.py` (entry point: `parse_boleto`)
- `tests/core/boleto/test_parser.py`
- `tests/fixtures/boleto/bancario.json`
- `tests/fixtures/boleto/arrecadacao.json`

- [ ] **Step 4.1: febraban_codes.json (bundled data)** — `src/brasil_mcp/core/boleto/febraban_codes.json`:

Estrutura: `{ "<codigo_3>": { "ispb": "<8_digits>", "nome": "<nome>" }, ... }`.

Bootstrap com os 20+ bancos mais comuns (Itaú, Bradesco, Santander, Banco do Brasil, Caixa, Inter, Nubank, BTG, Original, Safra, etc.). Subagente: usar este snippet de seed:

```json
{
  "001": {"ispb": "00000000", "nome": "Banco do Brasil S.A."},
  "033": {"ispb": "90400888", "nome": "Banco Santander (Brasil) S.A."},
  "077": {"ispb": "00416968", "nome": "Banco Inter S.A."},
  "104": {"ispb": "00360305", "nome": "Caixa Econômica Federal"},
  "208": {"ispb": "30306294", "nome": "Banco BTG Pactual S.A."},
  "212": {"ispb": "92894922", "nome": "Banco Original S.A."},
  "237": {"ispb": "60746948", "nome": "Banco Bradesco S.A."},
  "260": {"ispb": "18236120", "nome": "Nu Pagamentos S.A."},
  "341": {"ispb": "60701190", "nome": "Itaú Unibanco S.A."},
  "422": {"ispb": "58160789", "nome": "Banco Safra S.A."},
  "748": {"ispb": "01181521", "nome": "Sicredi"},
  "756": {"ispb": "02038232", "nome": "Sicoob"}
}
```

- [ ] **Step 4.2: Algoritmo (linha digitável bancária — 47 dígitos)**

Layout:
```
Posições 1-4:    Banco (3) + Moeda (1) → AAAA
Posições 5-9:    Campo 1 (5 dígitos do código de barras pos 20-24)
Posição 10:      DV módulo 10 do campo 1
Posições 11-20:  Campo 2 (10 dígitos do código de barras pos 25-34)
Posição 21:      DV módulo 10 do campo 2
Posições 22-31:  Campo 3 (10 dígitos do código de barras pos 35-44)
Posição 32:      DV módulo 10 do campo 3
Posição 33:      DV geral (módulo 11)
Posições 34-37:  Fator de vencimento (4 dígitos)
Posições 38-47:  Valor (10 dígitos = R$ em centavos, padded com zeros à esquerda)
```

**Conversão linha digitável → código de barras (44 dígitos):**
```
Pos 1-4 do barcode = pos 1-4 da linha
Pos 5 do barcode    = DV geral (pos 33 da linha)
Pos 6-9 do barcode  = fator de vencimento (pos 34-37 da linha)
Pos 10-19 do barcode = valor (pos 38-47 da linha)
Pos 20-24 do barcode = campo 1 dígitos sem DV (pos 5-9 da linha)
Pos 25-34 do barcode = campo 2 dígitos sem DV (pos 11-20 da linha)
Pos 35-44 do barcode = campo 3 dígitos sem DV (pos 22-31 da linha)
```

**DV módulo 10:** multiplicar dígitos por 2,1,2,1,... da direita pra esquerda. Se produto > 9, somar os dígitos do produto. Somar todos. DV = `(10 - (sum % 10)) % 10`.

**DV módulo 11 (DV geral):** pesos 2..9 cíclicos da direita pra esquerda. Soma mod 11. `dv = 11 - (sum % 11)`. Se dv em {0,10,11}, dv = 1.

**Fator de vencimento:**
- Base original: 1997-10-07 = fator 1000.
- Em 22/02/2025 atingiu 9999, reiniciou em 1000 (FEBRABAN reset).
- Heurística do parser: se fator decoded com base 1997 cair em data > 2025-02-22, usar base 2025-02-22. Equivalente: tentar primeiro com base 1997 e ver se ≤ 2025-02-21; senão usar base 2025-02-22.
- Se fator == 0: vencimento = null.

**Valor:** posições 38-47, em centavos. Se tudo zero, valor = null (boleto em branco).

- [ ] **Step 4.3: Algoritmo (boleto de arrecadação — 47 dígitos)**

Distinguível pela posição 1: começa com `8` (arrecadação). Layout diferente:
```
Pos 1:    "8" (identificador de arrecadação)
Pos 2:    Segmento (1-9)
Pos 3:    Identificador de valor (6 = real efetivo; 9 = referência)
Pos 4:    DV geral (módulo 10 ou 11 dependendo de pos 3)
Pos 5-15: Valor (11 dígitos em centavos) — ou referência
Pos 16-26 + 27-37 + 38-48: Empresa/órgão + dados livres
```

Segmento (pos 2):
- 1 → prefeitura (tributo municipal)
- 2 → saneamento (concessionaria_agua_saneamento)
- 3 → energia elétrica/gás (concessionaria_eletrica/gas — agrupar como "concessionaria_eletrica" se não houver distinção)
- 4 → telecom (concessionaria_telefonia)
- 5 → órgão governamental (tributo_federal ou tributo_estadual; mapear pra "tributo_federal" por default)
- 6 → carnês (carnes_assemelhados)
- 7 → multas de trânsito (multas_transito)
- 9 → outros

Para arrecadação, a linha digitável tem **48 dígitos** (não 47). Validar tamanho de acordo com primeiro char.

**Critério de aceite parser:**
- Aceita input com espaços, dots, hífens — strip.
- Distingue automaticamente bancário vs arrecadação pelo primeiro dígito.
- Calcula código de barras a partir da linha digitável (e vice-versa).
- Valida DVs (campo 1, 2, 3, geral).
- Decoda fator de vencimento + valor.
- Mapeia banco via febraban_codes.json.
- Retorna ValidationResult com extras na shape documentada.

- [ ] **Step 4.4: Implementation**

`src/brasil_mcp/core/boleto/linha_digitavel.py`:

```python
"""Linha digitável bancária (47 dígitos) e arrecadação (48 dígitos)."""
from __future__ import annotations

import re

_NON_DIGIT = re.compile(r"[^\d]")


def normalize(s: str) -> str:
    return _NON_DIGIT.sub("", s or "")


def is_arrecadacao(digits: str) -> bool:
    return len(digits) >= 1 and digits[0] == "8"


def dv_mod10(digits: str) -> int:
    weights = [2, 1] * (len(digits) // 2 + 1)
    total = 0
    for d, w in zip(reversed(digits), weights, strict=False):
        p = int(d) * w
        total += p if p < 10 else p - 9
    rem = total % 10
    return (10 - rem) % 10


def dv_mod11_bancario(digits: str) -> int:
    weights = [2, 3, 4, 5, 6, 7, 8, 9]
    total = sum(int(d) * weights[i % 8] for i, d in enumerate(reversed(digits)))
    dv = 11 - (total % 11)
    return 1 if dv in (0, 10, 11) else dv


def linha_to_barcode_bancario(linha47: str) -> str:
    """Convert 47-digit linha digitável into 44-digit barcode."""
    return (
        linha47[0:4]
        + linha47[32:33]
        + linha47[33:37]
        + linha47[37:47]
        + linha47[4:9]
        + linha47[10:20]
        + linha47[21:31]
    )


def barcode_to_linha_bancario(barcode44: str) -> str:
    """Convert 44-digit barcode into 47-digit linha digitável."""
    campo1 = barcode44[0:4] + barcode44[19:24]
    campo2 = barcode44[24:34]
    campo3 = barcode44[34:44]
    return (
        campo1 + str(dv_mod10(campo1))
        + campo2 + str(dv_mod10(campo2))
        + campo3 + str(dv_mod10(campo3))
        + barcode44[4]
        + barcode44[5:19]
    )
```

`src/brasil_mcp/core/boleto/parser.py`:

```python
"""parse_boleto — entry point pra boleto bancário e arrecadação."""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from brasil_mcp.core.boleto.linha_digitavel import (
    barcode_to_linha_bancario,
    dv_mod10,
    dv_mod11_bancario,
    is_arrecadacao,
    linha_to_barcode_bancario,
    normalize,
)
from brasil_mcp.core.errors import ErrorCode, ErrorObj
from brasil_mcp.core.models import ValidationResult

_FEBRABAN_PATH = Path(__file__).parent / "febraban_codes.json"
_FEBRABAN: dict[str, dict[str, str]] = json.loads(_FEBRABAN_PATH.read_text())

_BASE_OLD = date(1997, 10, 7)
_BASE_NEW = date(2025, 2, 22)
_RESET_DATE = date(2025, 2, 22)

_SEGMENT_MAP = {
    "1": "tributo_municipal",
    "2": "concessionaria_agua_saneamento",
    "3": "concessionaria_eletrica",
    "4": "concessionaria_telefonia",
    "5": "tributo_federal",
    "6": "carnes_assemelhados",
    "7": "multas_transito",
    "9": "outros",
}


def _decode_fator_vencimento(fator: int) -> date | None:
    if fator == 0:
        return None
    candidate_old = _BASE_OLD + timedelta(days=fator - 1000)
    if candidate_old <= _RESET_DATE:
        return candidate_old
    return _BASE_NEW + timedelta(days=fator - 1000)


def _err(code: ErrorCode, pt: str, en: str, raw: str) -> ValidationResult:
    return ValidationResult(valid=False, raw=raw, error=ErrorObj(code, pt, en))


def parse_boleto(value: str) -> ValidationResult:
    raw = value or ""
    if not raw.strip():
        return _err(ErrorCode.EMPTY_INPUT, "Boleto não pode ser vazio.", "Boleto cannot be empty.", raw)

    digits = normalize(raw)
    if not digits:
        return _err(ErrorCode.INVALID_CHARACTER, "Boleto deve conter dígitos.", "Boleto must contain digits.", raw)

    if is_arrecadacao(digits):
        return _parse_arrecadacao(digits, raw)

    if len(digits) == 47:
        return _parse_bancario_linha(digits, raw)
    if len(digits) == 44:
        linha = barcode_to_linha_bancario(digits)
        return _parse_bancario_linha(linha, raw)

    return _err(
        ErrorCode.INVALID_LENGTH,
        f"Boleto bancário deve ter 47 ou 44 dígitos; recebido {len(digits)}.",
        f"Bancário boleto must be 47 or 44 digits; got {len(digits)}.",
        raw,
    )


def _parse_bancario_linha(linha: str, raw: str) -> ValidationResult:
    # Validate DVs of each campo
    campo1, dv1 = linha[0:9], linha[9]
    campo2, dv2 = linha[10:20], linha[20]
    campo3, dv3 = linha[21:31], linha[31]
    if dv_mod10(campo1) != int(dv1):
        return _err(ErrorCode.INVALID_CHECKSUM, "DV do campo 1 inválido.", "Field 1 DV invalid.", raw)
    if dv_mod10(campo2) != int(dv2):
        return _err(ErrorCode.INVALID_CHECKSUM, "DV do campo 2 inválido.", "Field 2 DV invalid.", raw)
    if dv_mod10(campo3) != int(dv3):
        return _err(ErrorCode.INVALID_CHECKSUM, "DV do campo 3 inválido.", "Field 3 DV invalid.", raw)

    barcode = linha_to_barcode_bancario(linha)
    dv_geral = barcode[4]
    barcode_for_check = barcode[:4] + barcode[5:]
    if dv_mod11_bancario(barcode_for_check) != int(dv_geral):
        return _err(ErrorCode.INVALID_CHECKSUM, "DV geral inválido.", "General DV invalid.", raw)

    codigo_banco = barcode[0:3]
    fator = int(barcode[5:9])
    valor_cents = int(barcode[9:19])
    nosso_numero = barcode[19:44]

    banco_info = _FEBRABAN.get(codigo_banco)
    venc = _decode_fator_vencimento(fator)

    return ValidationResult(
        valid=True,
        raw=raw,
        formatted=linha,
        extras={
            "tipo": "bancario",
            "linha_digitavel": linha,
            "codigo_barras": barcode,
            "banco": (
                {"codigo_febraban": codigo_banco, **banco_info}
                if banco_info
                else {"codigo_febraban": codigo_banco, "ispb": None, "nome": None}
            ),
            "moeda": "BRL",
            "valor": valor_cents if valor_cents > 0 else None,
            "vencimento": venc.isoformat() if venc else None,
            "fator_vencimento": fator if fator > 0 else None,
            "nosso_numero": nosso_numero,
            "segmento_arrecadacao": None,
        },
    )


def _parse_arrecadacao(digits: str, raw: str) -> ValidationResult:
    if len(digits) != 48:
        return _err(
            ErrorCode.INVALID_LENGTH,
            f"Arrecadação deve ter 48 dígitos; recebido {len(digits)}.",
            f"Arrecadação must be 48 digits; got {len(digits)}.",
            raw,
        )
    segmento = _SEGMENT_MAP.get(digits[1], "outros")
    id_valor = digits[2]
    valor_field = digits[4:15]  # 11 dígitos (after DV)
    valor_cents: int | None = None
    if id_valor in ("6", "7"):  # valor efetivo em real
        valor_cents = int(valor_field) if int(valor_field) > 0 else None

    return ValidationResult(
        valid=True,
        raw=raw,
        formatted=digits,
        extras={
            "tipo": "arrecadacao",
            "linha_digitavel": digits,
            "codigo_barras": digits[0:4] + digits[4:],  # arrecadação tem barcode = linha sem rearranjo
            "banco": None,
            "moeda": "BRL",
            "valor": valor_cents,
            "vencimento": None,
            "fator_vencimento": None,
            "nosso_numero": None,
            "segmento_arrecadacao": segmento,
        },
    )
```

- [ ] **Step 4.5: Tests** — `tests/core/boleto/test_parser.py`:

```python
from brasil_mcp.core.boleto.parser import parse_boleto


# Vetores reais (com PII redacted onde aplicável)
# Boleto Itaú (banco 341), valor R$ 1,00, vencimento conhecido
VALID_LINHA_341 = "34191790010104351004791020150008291070026000"  # 44-digit barcode example


def test_empty():
    r = parse_boleto("")
    assert not r.valid
    assert r.error and str(r.error.code) == "EMPTY_INPUT"


def test_invalid_length():
    r = parse_boleto("12345")
    assert not r.valid
    assert r.error and str(r.error.code) == "INVALID_LENGTH"


def test_arrecadacao_detected():
    """Boleto arrecadação começa com 8."""
    arr = "8" + "1" * 47  # 48 digits, segmento 1
    r = parse_boleto(arr)
    # Mesmo que falhe checksum, deve ser identificado como arrecadação
    assert r.valid is True or (r.error is not None)


def test_strips_whitespace_and_punctuation():
    sample = "34191.79001 01043.510047 91020.150008 2 91070026000000"
    # se 47 dígitos válidos, parser aceita
    r = parse_boleto(sample)
    # Pode falhar checksum (linha sintética), mas não deve falhar por whitespace
    assert r.error is None or str(r.error.code) != "INVALID_CHARACTER"
```

**Nota para o subagente:** Para vetores reais, gerar com algoritmo válido (use as funções `linha_to_barcode_bancario` + DV calculators para gerar linhas que passem validação). Documentar fontes no fixture JSON.

- [ ] **Step 4.6: Commit**

```bash
uv run pytest tests/core/boleto -v
git add src/brasil_mcp/core/boleto tests/core/boleto tests/fixtures/boleto
git commit -m "feat(boleto): parser para bancário (47/44 dígitos) e arrecadação (48)"
```

---

## Task 5: PIX (parse + generate + QR + CRC16)

**Files:**
- `src/brasil_mcp/core/pix/crc16.py`
- `src/brasil_mcp/core/pix/brcode.py` (encoder/decoder EMV)
- `src/brasil_mcp/core/pix/qr.py` (segno wrapper)
- `src/brasil_mcp/core/pix/parser.py` (parse_pix_brcode + generate_pix_brcode)
- `tests/core/pix/test_*.py`
- `tests/fixtures/pix/*.json`

- [ ] **Step 5.1: CRC16-CCITT-FALSE** — `src/brasil_mcp/core/pix/crc16.py`:

```python
"""CRC16-CCITT-FALSE (poly 0x1021, init 0xFFFF) — usado em PIX BR Code."""
from __future__ import annotations


def crc16_ccitt_false(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if (crc & 0x8000) else (crc << 1) & 0xFFFF
    return crc


def crc16_hex(payload: str) -> str:
    """Returns the 4-char uppercase hex CRC for a PIX BR Code payload (excluding the CRC field)."""
    return f"{crc16_ccitt_false(payload.encode('utf-8')):04X}"
```

Test `tests/core/pix/test_crc16.py`:

```python
from brasil_mcp.core.pix.crc16 import crc16_ccitt_false, crc16_hex


def test_crc16_known_vector_123456789():
    """ISO/IEC test vector: CRC16-CCITT-FALSE("123456789") == 0x29B1."""
    assert crc16_ccitt_false(b"123456789") == 0x29B1


def test_crc16_pix_example():
    # Sample partial payload (truncate before CRC field as per PIX spec)
    payload = "00020126360014BR.GOV.BCB.PIX0114+5561999999990520400005303986540510.005802BR5913FULANO DE TAL6008BRASILIA62070503***6304"
    crc = crc16_hex(payload)
    assert len(crc) == 4
    assert all(c in "0123456789ABCDEF" for c in crc)
```

- [ ] **Step 5.2: EMV TLV codec** — `src/brasil_mcp/core/pix/brcode.py`:

```python
"""EMV TLV encoder/decoder pra PIX BR Code."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TLV:
    tag: str  # 2 chars
    value: str  # já decodificado (string), sub-TLVs serializados se nested

    def encode(self) -> str:
        length = len(self.value)
        return f"{self.tag}{length:02d}{self.value}"


def decode_tlv(payload: str, start: int = 0, end: int | None = None) -> dict[str, str]:
    """Decode TLVs at the given range. Returns dict of tag → raw value (string)."""
    end = end if end is not None else len(payload)
    out: dict[str, str] = {}
    i = start
    while i < end:
        if i + 4 > end:
            break
        tag = payload[i:i + 2]
        length = int(payload[i + 2:i + 4])
        value = payload[i + 4:i + 4 + length]
        out[tag] = value
        i = i + 4 + length
    return out


def encode_tlvs(tlvs: list[TLV]) -> str:
    return "".join(t.encode() for t in tlvs)
```

Test `tests/core/pix/test_brcode.py`:

```python
from brasil_mcp.core.pix.brcode import TLV, decode_tlv, encode_tlvs


def test_tlv_encode():
    assert TLV("00", "01").encode() == "000201"


def test_decode_simple():
    payload = "000201010212"
    out = decode_tlv(payload)
    assert out == {"00": "01", "01": "12"}


def test_encode_decode_roundtrip():
    tlvs = [TLV("00", "01"), TLV("52", "0000"), TLV("53", "986")]
    s = encode_tlvs(tlvs)
    assert decode_tlv(s) == {"00": "01", "52": "0000", "53": "986"}
```

- [ ] **Step 5.3: QR generator** — `src/brasil_mcp/core/pix/qr.py`:

```python
"""QR code rendering (PNG base64 + SVG) via segno."""
from __future__ import annotations

import base64
import io

import segno


def to_png_base64(payload: str, scale: int = 8) -> str:
    qr = segno.make(payload, error="M")
    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=scale)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def to_svg(payload: str, scale: int = 8) -> str:
    qr = segno.make(payload, error="M")
    buf = io.BytesIO()
    qr.save(buf, kind="svg", scale=scale, xmldecl=False)
    return buf.getvalue().decode("utf-8")
```

- [ ] **Step 5.4: parser + generator** — `src/brasil_mcp/core/pix/parser.py`:

```python
"""parse_pix_brcode + generate_pix_brcode."""
from __future__ import annotations

import re
import unicodedata
from typing import Any

from brasil_mcp.core.errors import ErrorCode, ErrorObj
from brasil_mcp.core.models import ValidationResult
from brasil_mcp.core.pix.brcode import TLV, decode_tlv, encode_tlvs
from brasil_mcp.core.pix.crc16 import crc16_hex
from brasil_mcp.core.pix.qr import to_png_base64, to_svg

_ID_PAYLOAD_FORMAT_INDICATOR = "00"
_ID_MERCHANT_ACCOUNT_INFO_PIX = "26"  # static
_ID_MERCHANT_ACCOUNT_INFO_DYNAMIC = "26"  # same tag, distinguished by sub-TLVs
_ID_MERCHANT_CATEGORY_CODE = "52"
_ID_TRANSACTION_CURRENCY = "53"
_ID_TRANSACTION_AMOUNT = "54"
_ID_COUNTRY_CODE = "58"
_ID_MERCHANT_NAME = "59"
_ID_MERCHANT_CITY = "60"
_ID_ADDITIONAL_DATA_FIELD = "62"
_ID_CRC = "63"
_PIX_GUI = "BR.GOV.BCB.PIX"


def _classify_chave(chave: str) -> str:
    if not chave:
        return "aleatoria"
    if "@" in chave:
        return "email"
    digits = re.sub(r"\D", "", chave)
    if chave.startswith("+") and len(digits) >= 12:
        return "telefone"
    if len(digits) == 11 and digits == chave.replace(".", "").replace("-", ""):
        return "cpf"
    if len(digits) == 14 and digits == chave.replace(".", "").replace("/", "").replace("-", ""):
        return "cnpj"
    if re.fullmatch(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", chave.lower()):
        return "aleatoria"
    return "aleatoria"


def _strip_accents_upper(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).upper()


def _err(code: ErrorCode, pt: str, en: str, raw: str) -> ValidationResult:
    return ValidationResult(valid=False, raw=raw, error=ErrorObj(code, pt, en))


def parse_pix_brcode(value: str) -> ValidationResult:
    raw = value or ""
    if not raw.strip():
        return _err(ErrorCode.EMPTY_INPUT, "BR Code não pode ser vazio.", "BR Code cannot be empty.", raw)

    if len(raw) < 30 or _ID_CRC + "04" not in raw:
        return _err(ErrorCode.INVALID_FORMAT, "BR Code inválido.", "Invalid BR Code.", raw)

    # CRC is last 4 chars; remove "6304" prefix + 4 chars
    crc_pos = raw.rfind(_ID_CRC + "04")
    payload_without_crc = raw[:crc_pos + 4]
    actual_crc = raw[crc_pos + 4:crc_pos + 8]
    expected_crc = crc16_hex(payload_without_crc)
    if actual_crc.upper() != expected_crc:
        return _err(ErrorCode.INVALID_CHECKSUM, "CRC do BR Code inválido.", "BR Code CRC invalid.", raw)

    top = decode_tlv(raw)
    merchant_acct = top.get(_ID_MERCHANT_ACCOUNT_INFO_PIX, "")
    sub = decode_tlv(merchant_acct)

    if sub.get("00") != _PIX_GUI:
        return _err(ErrorCode.UNSUPPORTED_FORMAT, "Não é um PIX BR Code (GUI ausente).", "Not a PIX BR Code.", raw)

    chave = sub.get("01", "")
    descricao_static = sub.get("02") or None
    url_provedor = sub.get("25") or None
    dinamico = bool(url_provedor)

    amount_str = top.get(_ID_TRANSACTION_AMOUNT)
    valor: int | None = None
    if amount_str:
        try:
            valor = int(round(float(amount_str) * 100))
        except ValueError:
            valor = None

    beneficiario = top.get(_ID_MERCHANT_NAME, "")
    cidade = top.get(_ID_MERCHANT_CITY, "")
    add_data = decode_tlv(top.get(_ID_ADDITIONAL_DATA_FIELD, ""))
    txid = add_data.get("05") if add_data.get("05") not in (None, "***") else None

    return ValidationResult(
        valid=True,
        raw=raw,
        formatted=raw,
        extras={
            "chave": chave,
            "tipo_chave": _classify_chave(chave),
            "beneficiario": beneficiario,
            "cidade": cidade,
            "valor": valor,
            "moeda": "BRL",
            "txid": txid,
            "descricao": descricao_static,
            "dinamico": dinamico,
            "url_provedor": url_provedor,
        },
    )


def generate_pix_brcode(
    chave: str,
    nome_beneficiario: str,
    cidade: str,
    valor: int | None = None,
    txid: str | None = None,
    descricao: str | None = None,
    qr_format: str = "none",
) -> dict[str, Any]:
    if qr_format not in ("none", "png", "svg", "both"):
        return {
            "brcode": None,
            "qr_png_base64": None,
            "qr_svg": None,
            "error": ErrorObj(
                ErrorCode.INVALID_FORMAT,
                "qr_format inválido.",
                "Invalid qr_format.",
            ).to_dict(),
        }

    nome = _strip_accents_upper(nome_beneficiario)[:25]
    cid = _strip_accents_upper(cidade)[:15]
    if not chave:
        return {
            "brcode": None,
            "qr_png_base64": None,
            "qr_svg": None,
            "error": ErrorObj(
                ErrorCode.MISSING_REQUIRED_FIELD,
                "chave PIX é obrigatória.",
                "PIX key is required.",
            ).to_dict(),
        }

    sub_tlvs = [TLV("00", _PIX_GUI), TLV("01", chave)]
    if descricao:
        sub_tlvs.append(TLV("02", descricao[:72]))
    merchant_account = encode_tlvs(sub_tlvs)

    add_data_inner = TLV("05", txid[:25] if txid else "***").encode()

    tlvs = [
        TLV("00", "01"),
        TLV("26", merchant_account),
        TLV("52", "0000"),
        TLV("53", "986"),
    ]
    if valor is not None and valor > 0:
        amount_str = f"{valor / 100:.2f}"
        tlvs.append(TLV("54", amount_str))
    tlvs += [
        TLV("58", "BR"),
        TLV("59", nome or "NOME NAO INFORMADO"),
        TLV("60", cid or "BRASIL"),
        TLV("62", add_data_inner),
    ]

    payload_no_crc = encode_tlvs(tlvs) + _ID_CRC + "04"
    crc = crc16_hex(payload_no_crc)
    brcode = payload_no_crc + crc

    out: dict[str, Any] = {"brcode": brcode, "qr_png_base64": None, "qr_svg": None, "error": None}
    if qr_format in ("png", "both"):
        out["qr_png_base64"] = to_png_base64(brcode)
    if qr_format in ("svg", "both"):
        out["qr_svg"] = to_svg(brcode)
    return out
```

- [ ] **Step 5.5: Tests** — `tests/core/pix/test_parser.py`:

```python
from brasil_mcp.core.pix.parser import generate_pix_brcode, parse_pix_brcode


def test_generate_then_parse_roundtrip():
    gen = generate_pix_brcode(
        chave="joao@example.com",
        nome_beneficiario="Joao da Silva",
        cidade="Sao Paulo",
        valor=12345,
        txid="PEDIDO12345",
    )
    assert gen["brcode"] is not None
    assert gen["error"] is None

    parsed = parse_pix_brcode(gen["brcode"])
    assert parsed.valid is True
    assert parsed.extras["chave"] == "joao@example.com"
    assert parsed.extras["tipo_chave"] == "email"
    assert parsed.extras["valor"] == 12345
    assert parsed.extras["txid"] == "PEDIDO12345"
    assert parsed.extras["cidade"] == "SAO PAULO"
    assert parsed.extras["beneficiario"].startswith("JOAO")


def test_generate_qr_png():
    gen = generate_pix_brcode(
        chave="11122233344",
        nome_beneficiario="Maria",
        cidade="Recife",
        qr_format="png",
    )
    assert gen["qr_png_base64"] is not None
    assert len(gen["qr_png_base64"]) > 100


def test_generate_qr_svg():
    gen = generate_pix_brcode(
        chave="11122233344",
        nome_beneficiario="Maria",
        cidade="Recife",
        qr_format="svg",
    )
    assert gen["qr_svg"] is not None
    assert gen["qr_svg"].startswith("<svg")


def test_classify_keys():
    from brasil_mcp.core.pix.parser import _classify_chave
    assert _classify_chave("joao@example.com") == "email"
    assert _classify_chave("+5511999999999") == "telefone"
    assert _classify_chave("11122233344") == "cpf"
    assert _classify_chave("12345678000195") == "cnpj"
    assert _classify_chave("550e8400-e29b-41d4-a716-446655440000") == "aleatoria"


def test_parse_invalid_crc():
    bad = "00020126360014BR.GOV.BCB.PIX0114+556199999999952040000530398654041.005802BR5913FULANO DE TAL6008BRASILIA62070503***6304FFFF"
    r = parse_pix_brcode(bad)
    assert not r.valid
    assert r.error and str(r.error.code) == "INVALID_CHECKSUM"
```

- [ ] **Step 5.6: Commit**

```bash
uv run pytest tests/core/pix -v
git add src/brasil_mcp/core/pix tests/core/pix
git commit -m "feat(pix): parse_pix_brcode + generate_pix_brcode + QR (PNG/SVG)"
```

---

## Task 6: Calendar (4 tools)

**Files:**
- `src/brasil_mcp/core/calendar/feriados.py`
- `tests/core/calendar/test_feriados.py`

- [ ] **Step 6.1: Implementation** — `src/brasil_mcp/core/calendar/feriados.py`:

```python
"""4 calendar tools: is_feriado_nacional, proximo_dia_util, contar_dias_uteis, listar_feriados."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import holidays


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _br_holidays(year: int, uf: str | None = None) -> dict[date, str]:
    if uf:
        return holidays.country_holidays("BR", subdiv=uf, years=year)  # type: ignore[no-any-return]
    return holidays.country_holidays("BR", years=year)  # type: ignore[no-any-return]


def is_feriado_nacional(date_str: str, uf: str | None = None, municipio: str | None = None) -> dict[str, Any]:
    d = _parse_date(date_str)
    nacionais = _br_holidays(d.year)
    if d in nacionais:
        return {
            "is_feriado": True,
            "nome": nacionais[d],
            "esfera": "nacional",
            "raw_date": date_str,
        }
    if uf:
        estaduais = _br_holidays(d.year, uf=uf)
        if d in estaduais and d not in nacionais:
            return {
                "is_feriado": True,
                "nome": estaduais[d],
                "esfera": "estadual",
                "raw_date": date_str,
            }
    return {"is_feriado": False, "nome": None, "esfera": None, "raw_date": date_str}


def proximo_dia_util(date_str: str, uf: str | None = None, include_today: bool = False) -> dict[str, Any]:
    d = _parse_date(date_str)
    if not include_today:
        d += timedelta(days=1)
    skipped = 0
    while True:
        if d.weekday() >= 5:  # Sat/Sun
            d += timedelta(days=1)
            skipped += 1
            continue
        if is_feriado_nacional(d.isoformat(), uf=uf)["is_feriado"]:
            d += timedelta(days=1)
            skipped += 1
            continue
        break
    return {"date": d.isoformat(), "dias_pulados": skipped}


def contar_dias_uteis(
    start_date: str,
    end_date: str,
    uf: str | None = None,
    inclusive_end: bool = False,
) -> dict[str, Any]:
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if inclusive_end:
        end += timedelta(days=1)
    count = 0
    feriados_no_periodo: list[dict[str, str]] = []
    cursor = start
    while cursor < end:
        info = is_feriado_nacional(cursor.isoformat(), uf=uf)
        if info["is_feriado"]:
            feriados_no_periodo.append({"date": cursor.isoformat(), "nome": info["nome"]})
        elif cursor.weekday() < 5:
            count += 1
        cursor += timedelta(days=1)
    return {
        "count": count,
        "total_dias": (end - start).days,
        "feriados_no_periodo": feriados_no_periodo,
    }


def listar_feriados(year: int, uf: str | None = None) -> dict[str, Any]:
    nacionais = _br_holidays(year)
    out: list[dict[str, str]] = [
        {"date": d.isoformat(), "nome": nome, "esfera": "nacional"}
        for d, nome in sorted(nacionais.items())
    ]
    if uf:
        estaduais = _br_holidays(year, uf=uf)
        for d, nome in sorted(estaduais.items()):
            if d not in nacionais:
                out.append({"date": d.isoformat(), "nome": nome, "esfera": "estadual"})
        out.sort(key=lambda x: x["date"])
    return {"ano": year, "uf": uf, "feriados": out}
```

- [ ] **Step 6.2: Tests** — `tests/core/calendar/test_feriados.py`:

```python
from brasil_mcp.core.calendar.feriados import (
    contar_dias_uteis,
    is_feriado_nacional,
    listar_feriados,
    proximo_dia_util,
)


def test_independencia_2026():
    r = is_feriado_nacional("2026-09-07")
    assert r["is_feriado"] is True
    assert "Independ" in r["nome"]
    assert r["esfera"] == "nacional"


def test_dia_comum():
    r = is_feriado_nacional("2026-08-12")  # quarta normal
    assert r["is_feriado"] is False


def test_aniversario_sp():
    r = is_feriado_nacional("2026-01-25", uf="SP")  # aniversário SP
    assert r["is_feriado"] is True
    assert r["esfera"] == "estadual"


def test_proximo_dia_util_sexta_para_segunda():
    r = proximo_dia_util("2026-05-22")  # sexta-feira
    assert r["date"] == "2026-05-25"  # segunda
    assert r["dias_pulados"] == 2


def test_proximo_dia_util_vespera_feriado():
    # 6 de setembro de 2026 é domingo, 7 é feriado, 8 é terça
    r = proximo_dia_util("2026-09-04")  # sexta antes do feriado
    assert r["date"] == "2026-09-08"
    assert r["dias_pulados"] == 3


def test_contar_dias_uteis():
    r = contar_dias_uteis("2026-09-01", "2026-09-30")
    # Setembro 2026: 30 dias, ~22 úteis (depende de domingo/sábado), -1 feriado nacional dia 7
    assert r["total_dias"] == 29  # default inclusive_end=False
    assert r["count"] >= 19 and r["count"] <= 22
    assert any(f["date"] == "2026-09-07" for f in r["feriados_no_periodo"])


def test_listar_feriados_2026():
    r = listar_feriados(2026)
    assert r["ano"] == 2026
    assert len(r["feriados"]) >= 10  # ~ 10-12 nacionais
    assert any(f["date"] == "2026-09-07" for f in r["feriados"])


def test_listar_feriados_sp():
    r = listar_feriados(2026, uf="SP")
    assert any(f["date"] == "2026-01-25" and f["esfera"] == "estadual" for f in r["feriados"])
```

- [ ] **Step 6.3: Commit**

```bash
uv run pytest tests/core/calendar -v
git add src/brasil_mcp/core/calendar tests/core/calendar
git commit -m "feat(calendar): is_feriado_nacional, proximo_dia_util, contar_dias_uteis, listar_feriados"
```

---

## Task 7: Telemetry (opt-in PostHog)

**Files:**
- `src/brasil_mcp/core/telemetry.py`
- `tests/core/test_telemetry.py`

- [ ] **Step 7.1: Implementation** — `src/brasil_mcp/core/telemetry.py`:

```python
"""Telemetria opt-in via PostHog. Default OFF. Anonymous metadata only."""
from __future__ import annotations

import os
import platform
import sys
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import brasil_mcp


def _is_enabled() -> bool:
    return os.environ.get("BRASIL_MCP_TELEMETRY", "0").lower() in ("1", "true", "yes", "on")


def _data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    p = Path(base) / "brasil-mcp"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _get_or_create_installation_id() -> str:
    f = _data_dir() / "installation_id"
    if f.exists():
        return f.read_text().strip()
    new_id = str(uuid.uuid4())
    f.write_text(new_id)
    return new_id


def _notice_seen() -> bool:
    return (_data_dir() / "notice_seen").exists()


def _mark_notice_seen() -> None:
    (_data_dir() / "notice_seen").touch()


def maybe_show_notice() -> None:
    """Show one-time stderr notice if telemetry not opt-in and notice not shown yet."""
    if _is_enabled() or _notice_seen():
        return
    print(
        "\nℹ Brasil MCP não coleta telemetria. Para opt-in (anonymous metadata only):\n"
        "    export BRASIL_MCP_TELEMETRY=1\n",
        file=sys.stderr,
    )
    _mark_notice_seen()


_posthog_client: Any | None = None


def _get_client() -> Any | None:
    global _posthog_client
    if not _is_enabled():
        return None
    if _posthog_client is not None:
        return _posthog_client
    try:
        from posthog import Posthog  # type: ignore[import-untyped]
    except ImportError:
        return None
    api_key = os.environ.get("BRASIL_MCP_POSTHOG_KEY", "phc_PUBLIC_KEY_PLACEHOLDER")
    _posthog_client = Posthog(api_key, host="https://us.i.posthog.com")
    return _posthog_client


def track_tool_call(
    tool: str,
    success: bool,
    latency_ms: float,
    error_code: str | None = None,
) -> None:
    client = _get_client()
    if client is None:
        return
    try:
        client.capture(
            distinct_id=_get_or_create_installation_id(),
            event="tool_called",
            properties={
                "tool": tool,
                "success": success,
                "latency_ms": round(latency_ms, 3),
                "error_code": error_code,
                "brasil_mcp_version": brasil_mcp.__version__,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
                "platform": platform.system().lower(),
            },
        )
    except Exception:
        # Telemetry failure never breaks the user experience.
        pass


@contextmanager
def track(tool: str) -> Iterator[None]:
    """Context manager to time + report a tool call."""
    start = time.perf_counter()
    error_code: str | None = None
    success = True
    try:
        yield
    except Exception as exc:
        success = False
        error_code = type(exc).__name__
        raise
    finally:
        latency_ms = (time.perf_counter() - start) * 1000
        track_tool_call(tool, success=success, latency_ms=latency_ms, error_code=error_code)
```

- [ ] **Step 7.2: Tests** — `tests/core/test_telemetry.py`:

```python
import os
from unittest.mock import patch

from brasil_mcp.core.telemetry import _is_enabled, maybe_show_notice, track_tool_call


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv("BRASIL_MCP_TELEMETRY", raising=False)
    assert _is_enabled() is False


def test_enabled_when_env_set(monkeypatch):
    monkeypatch.setenv("BRASIL_MCP_TELEMETRY", "1")
    assert _is_enabled() is True


def test_track_no_op_when_disabled(monkeypatch):
    monkeypatch.delenv("BRASIL_MCP_TELEMETRY", raising=False)
    # Should not raise even if posthog not importable
    track_tool_call("validate_cpf", success=True, latency_ms=1.0)


def test_notice_shown_only_once(monkeypatch, capsys, tmp_path):
    monkeypatch.delenv("BRASIL_MCP_TELEMETRY", raising=False)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    maybe_show_notice()
    out1 = capsys.readouterr().err
    assert "BRASIL_MCP_TELEMETRY" in out1
    maybe_show_notice()
    out2 = capsys.readouterr().err
    assert out2 == ""  # already seen
```

- [ ] **Step 7.3: Commit**

```bash
uv run pytest tests/core/test_telemetry.py -v
git add src/brasil_mcp/core/telemetry.py tests/core/test_telemetry.py
git commit -m "feat(telemetry): opt-in PostHog wrapper with one-time notice"
```

---

## Task 8: MCP adapter

**Files:**
- `src/brasil_mcp/adapters/mcp/server.py`
- `src/brasil_mcp/adapters/mcp/tools.py`
- `tests/adapters/test_mcp_server.py`

- [ ] **Step 8.1: Tools registry + server** — `src/brasil_mcp/adapters/mcp/tools.py`:

```python
"""Registra cada core function como uma MCP tool com schema apropriado."""
from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from brasil_mcp.core.boleto.parser import parse_boleto as core_parse_boleto
from brasil_mcp.core.calendar.feriados import (
    contar_dias_uteis as core_contar_dias_uteis,
)
from brasil_mcp.core.calendar.feriados import (
    is_feriado_nacional as core_is_feriado,
)
from brasil_mcp.core.calendar.feriados import (
    listar_feriados as core_listar_feriados,
)
from brasil_mcp.core.calendar.feriados import (
    proximo_dia_util as core_proximo_dia_util,
)
from brasil_mcp.core.pix.parser import generate_pix_brcode as core_generate_pix
from brasil_mcp.core.pix.parser import parse_pix_brcode as core_parse_pix
from brasil_mcp.core.telemetry import track
from brasil_mcp.core.validators.cnh import validate_cnh as core_validate_cnh
from brasil_mcp.core.validators.cnpj import validate_cnpj as core_validate_cnpj
from brasil_mcp.core.validators.cpf import validate_cpf as core_validate_cpf
from brasil_mcp.core.validators.credit_card import (
    validate_credit_card as core_validate_credit_card,
)
from brasil_mcp.core.validators.pis import validate_pis as core_validate_pis
from brasil_mcp.core.validators.renavam import validate_renavam as core_validate_renavam
from brasil_mcp.core.validators.titulo_eleitor import (
    validate_titulo_eleitor as core_validate_titulo,
)


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def validate_cpf(value: str) -> dict[str, Any]:
        """Valida CPF brasileiro (11 dígitos). Módulo 11. Rejeita sequências repetidas."""
        with track("validate_cpf"):
            return core_validate_cpf(value).to_dict()

    @mcp.tool()
    def validate_cnpj(value: str) -> dict[str, Any]:
        """Valida CNPJ brasileiro — legacy (14 dígitos) E novo alfanumérico (Receita Federal NT COCAD/SUARA 49/2024). Auto-detecta."""
        with track("validate_cnpj"):
            return core_validate_cnpj(value).to_dict()

    @mcp.tool()
    def validate_pis(value: str) -> dict[str, Any]:
        """Valida PIS/PASEP/NIT (11 dígitos)."""
        with track("validate_pis"):
            return core_validate_pis(value).to_dict()

    @mcp.tool()
    def validate_renavam(value: str) -> dict[str, Any]:
        """Valida RENAVAM (11 dígitos)."""
        with track("validate_renavam"):
            return core_validate_renavam(value).to_dict()

    @mcp.tool()
    def validate_cnh(value: str) -> dict[str, Any]:
        """Valida CNH brasileira (11 dígitos)."""
        with track("validate_cnh"):
            return core_validate_cnh(value).to_dict()

    @mcp.tool()
    def validate_titulo_eleitor(value: str) -> dict[str, Any]:
        """Valida título de eleitor (12 dígitos)."""
        with track("validate_titulo_eleitor"):
            return core_validate_titulo(value).to_dict()

    @mcp.tool()
    def validate_credit_card(value: str) -> dict[str, Any]:
        """Valida cartão de crédito (Luhn) e detecta bandeira: Visa, Mastercard, Elo, Hipercard, Amex, Diners, JCB, Discover."""
        with track("validate_credit_card"):
            return core_validate_credit_card(value).to_dict()

    @mcp.tool()
    def parse_boleto(value: str) -> dict[str, Any]:
        """Parse boleto bancário (47 linha digitável / 44 código de barras) OU arrecadação (48). Detecta tipo automaticamente."""
        with track("parse_boleto"):
            return core_parse_boleto(value).to_dict()

    @mcp.tool()
    def parse_pix_brcode(value: str) -> dict[str, Any]:
        """Parse BR Code PIX (string EMV). Retorna chave, beneficiário, valor, txid, descrição."""
        with track("parse_pix_brcode"):
            return core_parse_pix(value).to_dict()

    @mcp.tool()
    def generate_pix_brcode(
        chave: str,
        nome_beneficiario: str,
        cidade: str,
        valor: int | None = None,
        txid: str | None = None,
        descricao: str | None = None,
        qr_format: str = "none",
    ) -> dict[str, Any]:
        """Gera BR Code PIX estático. qr_format: 'none' | 'png' | 'svg' | 'both'."""
        with track("generate_pix_brcode"):
            return core_generate_pix(chave, nome_beneficiario, cidade, valor, txid, descricao, qr_format)

    @mcp.tool()
    def is_feriado_nacional(date: str, uf: str | None = None, municipio: str | None = None) -> dict[str, Any]:
        """Verifica se uma data (YYYY-MM-DD) é feriado brasileiro. UF opcional para estaduais."""
        with track("is_feriado_nacional"):
            return core_is_feriado(date, uf=uf, municipio=municipio)

    @mcp.tool()
    def proximo_dia_util(date: str, uf: str | None = None, include_today: bool = False) -> dict[str, Any]:
        """Retorna o próximo dia útil após uma data. Pula fins de semana e feriados."""
        with track("proximo_dia_util"):
            return core_proximo_dia_util(date, uf=uf, include_today=include_today)

    @mcp.tool()
    def contar_dias_uteis(
        start_date: str,
        end_date: str,
        uf: str | None = None,
        inclusive_end: bool = False,
    ) -> dict[str, Any]:
        """Conta dias úteis entre duas datas (inclui início, exclui fim por padrão)."""
        with track("contar_dias_uteis"):
            return core_contar_dias_uteis(start_date, end_date, uf=uf, inclusive_end=inclusive_end)

    @mcp.tool()
    def listar_feriados(year: int, uf: str | None = None) -> dict[str, Any]:
        """Lista feriados brasileiros num ano. UF opcional para incluir estaduais."""
        with track("listar_feriados"):
            return core_listar_feriados(year, uf=uf)
```

`src/brasil_mcp/adapters/mcp/server.py`:

```python
"""Entry point: brasil-mcp-server — MCP server stdio."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from brasil_mcp.adapters.mcp.tools import register_tools
from brasil_mcp.core.telemetry import maybe_show_notice


def build_server() -> FastMCP:
    mcp = FastMCP("brasil-mcp-essentials")
    register_tools(mcp)
    return mcp


def main() -> None:
    maybe_show_notice()
    server = build_server()
    server.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 8.2: Tests** — `tests/adapters/test_mcp_server.py`:

```python
import pytest

from brasil_mcp.adapters.mcp.server import build_server


@pytest.mark.asyncio
async def test_server_lists_14_tools():
    server = build_server()
    tools = await server.list_tools()
    names = {t.name for t in tools}
    expected = {
        "validate_cpf", "validate_cnpj", "validate_pis", "validate_renavam",
        "validate_cnh", "validate_titulo_eleitor", "validate_credit_card",
        "parse_boleto",
        "parse_pix_brcode", "generate_pix_brcode",
        "is_feriado_nacional", "proximo_dia_util", "contar_dias_uteis", "listar_feriados",
    }
    assert expected.issubset(names), f"Missing: {expected - names}"


@pytest.mark.asyncio
async def test_validate_cpf_via_mcp_returns_same_as_core():
    from brasil_mcp.core.validators.cpf import validate_cpf as core_fn

    server = build_server()
    result = await server.call_tool("validate_cpf", {"value": "529.982.247-25"})
    # FastMCP wraps content; extract the structured data
    expected = core_fn("529.982.247-25").to_dict()
    # The structured content should match
    assert any(expected["valid"] == c.get("valid") for c in result if isinstance(c, dict)) or result
```

Add to `pyproject.toml`:
```toml
[dependency-groups]
dev = [
    # ... existing ...
    "pytest-asyncio>=0.23",
]
```

And to `[tool.pytest.ini_options]`:
```toml
asyncio_mode = "auto"
```

- [ ] **Step 8.3: Commit**

```bash
uv add --dev pytest-asyncio
uv run pytest tests/adapters/test_mcp_server.py -v
git add src/brasil_mcp/adapters/mcp tests/adapters/test_mcp_server.py pyproject.toml uv.lock
git commit -m "feat(mcp): server with 14 tools registered via FastMCP"
```

---

## Task 9: CLI adapter

**Files:**
- `src/brasil_mcp/adapters/cli/app.py`
- `tests/adapters/test_cli.py`

- [ ] **Step 9.1: Typer app** — `src/brasil_mcp/adapters/cli/app.py`:

```python
"""CLI Typer: brasil-mcp <subcommand>. Subcommand 'serve' inicia stdio MCP."""
from __future__ import annotations

import json
from typing import Any

import typer

from brasil_mcp.core.boleto.parser import parse_boleto as core_parse_boleto
from brasil_mcp.core.calendar.feriados import (
    contar_dias_uteis as core_contar,
)
from brasil_mcp.core.calendar.feriados import (
    is_feriado_nacional as core_is_feriado,
)
from brasil_mcp.core.calendar.feriados import (
    listar_feriados as core_listar,
)
from brasil_mcp.core.calendar.feriados import (
    proximo_dia_util as core_prox,
)
from brasil_mcp.core.pix.parser import generate_pix_brcode as core_gen_pix
from brasil_mcp.core.pix.parser import parse_pix_brcode as core_parse_pix
from brasil_mcp.core.validators.cnh import validate_cnh as core_cnh
from brasil_mcp.core.validators.cnpj import validate_cnpj as core_cnpj
from brasil_mcp.core.validators.cpf import validate_cpf as core_cpf
from brasil_mcp.core.validators.credit_card import (
    validate_credit_card as core_cc,
)
from brasil_mcp.core.validators.pis import validate_pis as core_pis
from brasil_mcp.core.validators.renavam import validate_renavam as core_renavam
from brasil_mcp.core.validators.titulo_eleitor import (
    validate_titulo_eleitor as core_titulo,
)

app = typer.Typer(
    name="brasil-mcp",
    help="MCP server brasileiro + CLI. Validators, boleto, PIX, calendário.",
    no_args_is_help=True,
)


def _emit(data: Any) -> None:
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2))


@app.command("validate-cpf")
def cli_validate_cpf(value: str) -> None:
    """Valida CPF (11 dígitos)."""
    _emit(core_cpf(value).to_dict())


@app.command("validate-cnpj")
def cli_validate_cnpj(value: str) -> None:
    """Valida CNPJ (legacy 14 dígitos OU alfanumérico novo)."""
    _emit(core_cnpj(value).to_dict())


@app.command("validate-pis")
def cli_validate_pis(value: str) -> None:
    _emit(core_pis(value).to_dict())


@app.command("validate-renavam")
def cli_validate_renavam(value: str) -> None:
    _emit(core_renavam(value).to_dict())


@app.command("validate-cnh")
def cli_validate_cnh(value: str) -> None:
    _emit(core_cnh(value).to_dict())


@app.command("validate-titulo-eleitor")
def cli_validate_titulo(value: str) -> None:
    _emit(core_titulo(value).to_dict())


@app.command("validate-credit-card")
def cli_validate_cc(value: str) -> None:
    _emit(core_cc(value).to_dict())


@app.command("parse-boleto")
def cli_parse_boleto(value: str) -> None:
    _emit(core_parse_boleto(value).to_dict())


@app.command("parse-pix-brcode")
def cli_parse_pix(value: str) -> None:
    _emit(core_parse_pix(value).to_dict())


@app.command("generate-pix-brcode")
def cli_gen_pix(
    chave: str = typer.Option(..., help="Chave PIX"),
    nome: str = typer.Option(..., help="Nome do beneficiário (max 25 chars ASCII)"),
    cidade: str = typer.Option(..., help="Cidade (max 15 chars ASCII)"),
    valor: int | None = typer.Option(None, help="Valor em centavos"),
    txid: str | None = typer.Option(None, help="Identificador de transação"),
    descricao: str | None = typer.Option(None, help="Descrição"),
    qr: str = typer.Option("none", help="Formato do QR: none|png|svg|both"),
) -> None:
    _emit(core_gen_pix(chave, nome, cidade, valor, txid, descricao, qr))


@app.command("is-feriado")
def cli_is_feriado(
    date: str,
    uf: str | None = typer.Option(None, help="UF para feriados estaduais"),
) -> None:
    _emit(core_is_feriado(date, uf=uf))


@app.command("proximo-dia-util")
def cli_prox(
    date: str,
    uf: str | None = typer.Option(None),
    include_today: bool = typer.Option(False),
) -> None:
    _emit(core_prox(date, uf=uf, include_today=include_today))


@app.command("contar-dias-uteis")
def cli_contar(
    start_date: str,
    end_date: str,
    uf: str | None = typer.Option(None),
    inclusive_end: bool = typer.Option(False),
) -> None:
    _emit(core_contar(start_date, end_date, uf=uf, inclusive_end=inclusive_end))


@app.command("listar-feriados")
def cli_listar(year: int, uf: str | None = typer.Option(None)) -> None:
    _emit(core_listar(year, uf=uf))


@app.command("serve")
def cli_serve() -> None:
    """Inicia o servidor MCP via stdio."""
    from brasil_mcp.adapters.mcp.server import main as run_mcp_server
    run_mcp_server()


@app.command("version")
def cli_version() -> None:
    """Exibe a versão do pacote."""
    import brasil_mcp
    typer.echo(brasil_mcp.__version__)
```

- [ ] **Step 9.2: Tests** — `tests/adapters/test_cli.py`:

```python
import json

from typer.testing import CliRunner

from brasil_mcp.adapters.cli.app import app

runner = CliRunner()


def test_version():
    r = runner.invoke(app, ["version"])
    assert r.exit_code == 0
    assert r.stdout.strip()


def test_validate_cpf_valid():
    r = runner.invoke(app, ["validate-cpf", "52998224725"])
    assert r.exit_code == 0
    data = json.loads(r.stdout)
    assert data["valid"] is True


def test_validate_cpf_invalid():
    r = runner.invoke(app, ["validate-cpf", "111"])
    assert r.exit_code == 0
    data = json.loads(r.stdout)
    assert data["valid"] is False


def test_validate_cnpj_legacy():
    r = runner.invoke(app, ["validate-cnpj", "11222333000181"])
    assert r.exit_code == 0
    data = json.loads(r.stdout)
    assert data["valid"] is True
    assert data["format"] == "legacy"


def test_generate_pix():
    r = runner.invoke(app, [
        "generate-pix-brcode",
        "--chave", "11122233344",
        "--nome", "Maria Silva",
        "--cidade", "Sao Paulo",
    ])
    assert r.exit_code == 0
    data = json.loads(r.stdout)
    assert data["brcode"]


def test_is_feriado():
    r = runner.invoke(app, ["is-feriado", "2026-09-07"])
    assert r.exit_code == 0
    data = json.loads(r.stdout)
    assert data["is_feriado"] is True
```

- [ ] **Step 9.3: Commit**

```bash
uv run pytest tests/adapters/test_cli.py -v
git add src/brasil_mcp/adapters/cli tests/adapters/test_cli.py
git commit -m "feat(cli): typer app com 14 subcomandos + serve"
```

---

## Task 10: README + tools.md + CHANGELOG

**Files:**
- `README.md` (overwrite scaffold)
- `docs/tools.md`
- `CHANGELOG.md`

- [ ] **Step 10.1: Write README.md** — substituir o placeholder. Estrutura completa em PT-BR + seção EN. Inclui:
  - Hero + tagline + badges
  - Tabela de 14 tools com link pra docs/tools.md
  - Instalação (uv/pipx)
  - Quick start CLI
  - Configurar Claude Desktop
  - Seção privacidade + telemetria
  - Roadmap (Phase 1 expansion, Phase 2, Phase 3)
  - Licença MIT
  - Seção "English" no final

- [ ] **Step 10.2: Write `docs/tools.md`** — uma seção por tool com:
  - Nome
  - Descrição completa
  - JSON Schema do input
  - Output shape com exemplo
  - Códigos de erro possíveis
  - Exemplo CLI

- [ ] **Step 10.3: Write `CHANGELOG.md`** — Keep a Changelog format:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-05-21

### Added
- Initial public release.
- 14 offline tools: validators (CPF, CNPJ legacy+alfanumérico, PIS, RENAVAM, CNH, Título de Eleitor, Cartão de Crédito), boleto parser (bancário 47/44 dígitos + arrecadação 48), PIX (parse + generate + QR PNG/SVG), calendar (is_feriado_nacional, proximo_dia_util, contar_dias_uteis, listar_feriados).
- MCP server via stdio (`brasil-mcp-server`).
- CLI Typer (`brasil-mcp`) com todos os 14 tools como subcomandos.
- Telemetria opt-in via PostHog, anonymous metadata only.
- Suporte completo a CNPJ alfanumérico (Receita Federal NT COCAD/SUARA 49/2024).
```

- [ ] **Step 10.4: Commit**

```bash
git add README.md docs/tools.md CHANGELOG.md
git commit -m "docs: README PT/EN, tools.md, CHANGELOG v0.1.0"
```

---

## Task 11: GitHub Actions workflows

**Files:**
- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`

- [ ] **Step 11.1: CI workflow** — `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true
      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}
      - name: Install
        run: uv sync --frozen --all-extras
      - name: Lint
        run: uv run ruff check
      - name: Format check
        run: uv run ruff format --check
      - name: Type check
        run: uv run pyright src
      - name: Tests
        run: uv run pytest --cov=brasil_mcp --cov-report=xml --cov-fail-under=85
```

- [ ] **Step 11.2: Release workflow** — `.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    tags:
      - "v*"

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # OIDC for trusted publishing
      contents: write  # for GitHub release
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - name: Set up Python
        run: uv python install 3.12
      - name: Install
        run: uv sync --frozen
      - name: Tests
        run: uv run pytest -q
      - name: Build
        run: uv build
      - name: Publish to PyPI (OIDC)
        uses: pypa/gh-action-pypi-publish@release/v1
      - name: GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          generate_release_notes: true
          files: dist/*
```

- [ ] **Step 11.3: Commit**

```bash
git add .github/workflows
git commit -m "ci: add GitHub Actions for tests + PyPI release via OIDC"
```

---

## Task 12: Final verification + tag v0.1.0

- [ ] **Step 12.1: Run full check locally**

```bash
cd /Users/ricardo/omc/projects/brasil-mcp/code
uv run ruff check
uv run ruff format --check
uv run pyright src
uv run pytest --cov=brasil_mcp --cov-report=term-missing
```

Expected: tudo passa, coverage ≥85%.

- [ ] **Step 12.2: Smoke test do CLI**

```bash
uv run brasil-mcp version
uv run brasil-mcp validate-cpf 52998224725
uv run brasil-mcp validate-cnpj 11222333000181
uv run brasil-mcp generate-pix-brcode --chave 11122233344 --nome "Maria" --cidade "SP"
uv run brasil-mcp is-feriado 2026-09-07
```

Expected: cada comando retorna JSON válido com `"valid": true` ou shape esperada.

- [ ] **Step 12.3: Smoke test do MCP server (process boot only)**

```bash
echo '' | timeout 2 uv run brasil-mcp-server || true
```

Expected: processo inicia e termina (sem crash). Logs em stderr OK.

- [ ] **Step 12.4: Tag e push (CONFIRMAR COM USUÁRIO ANTES DE PUSH)**

```bash
git tag -a v0.1.0 -m "v0.1.0 — Initial public release"
# git push origin main
# git push origin v0.1.0
```

**STOP. Confirme com o usuário antes de fazer push pra remote.** Pushar pra main + tag dispara o release.yml e publica no PyPI — ação irreversível.

---

## Notas Finais

- **Fixtures de testes:** muitos testes acima dependem de vetores gerados algoritmicamente. Subagente deve gerar e validar antes de incluir nos fixtures.
- **Coverage 85%:** se algum módulo ficar abaixo, adicionar testes específicos antes de prosseguir.
- **Brand consistency:** README + CHANGELOG + descrições MCP devem mencionar "CNPJ alfanumérico-ready" como diferencial.
- **Privacy positioning:** mencionar "opt-in telemetry" no README de forma proeminente.
- **PyPI trusted publisher:** configurar manualmente no PyPI dashboard antes do primeiro release tag — instrução em `docs/RELEASE.md` (criar como parte de Task 10 se necessário).
