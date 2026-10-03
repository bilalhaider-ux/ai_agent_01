# Security Policy

## Supported Versions

Security fixes target the current `main` branch. This project is not a hosted security service and does not promise long-term support for old revisions.

## Reporting a Vulnerability

Do not publish API keys, private datasets, stack traces containing secrets, or working exploit details in a public issue. Contact the repository owner privately through the GitHub repository's available private channel and include a minimal reproduction, affected component, impact, and suggested mitigation.

## Secret Handling

- Store provider keys in local `.env` files or Heroku Config Vars.
- Never commit `backend/.env`, API keys, tokens, or credentials.
- Rotate a key immediately if it appears in a terminal log, chat, issue, commit, or pull request.
- Keep API keys in backend configuration; never send them to the frontend.

## Runtime Boundaries

Generated analysis code runs in a child subprocess with a timeout and temporary directory. This reduces accidental impact on the API process but is not equivalent to a hardened sandbox or container. Do not expose this workflow to hostile untrusted tenants without stronger OS/container isolation, resource limits, and a review of allowed imports and filesystem access.

Uploads are restricted by extension, filename, and size. Reports currently live in process memory and uploaded files are temporary; do not treat this implementation as durable storage for sensitive records.
