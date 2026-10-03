# Contributing

Thank you for improving AI Agent 01. Contributions should preserve the analytics pipeline and keep decision outputs traceable to computed evidence.

## Before Opening a Change

- Read the product behavior and limitations in [README.md](README.md).
- Do not commit `.env` files, API keys, uploaded datasets containing sensitive information, generated reports, or sandbox output.
- Keep provider credentials backend-only.
- Preserve the six workflow stages and existing report formats unless the change explicitly updates the contract.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v
```

Use `LLM_PROVIDER=mock` for tests. Network calls and real provider keys must not be required by the test suite.

## Pull Requests

Describe the user-facing behavior, affected API contract, data-quality implications, security impact, and test evidence. Add focused tests for provider behavior, upload validation, report output, or metric validation when relevant. Keep commits small and explain migrations or breaking changes.

## Reporting Security Issues

Do not open a public issue containing a secret or exploit details. Follow [SECURITY.md](SECURITY.md).
