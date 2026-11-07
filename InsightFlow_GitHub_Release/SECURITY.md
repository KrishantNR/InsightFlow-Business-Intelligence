# Security Policy

## Supported version

Security and dependency fixes are made against the latest version on the `main` branch.

## Reporting a vulnerability

Do not publish API keys, private datasets or exploitable details in a public issue. Contact the repository owner privately through the contact method listed on their GitHub profile and include a concise reproduction. This is an academic prototype; there is no guaranteed response SLA.

## Credential handling

- Never commit `OPENAI_API_KEY`, `.env` files or `.streamlit/secrets.toml`.
- Use environment variables or a hosting provider's secret store.
- If a credential is exposed, revoke it immediately and issue a replacement.
- Use a dedicated API project/key with appropriate permissions, usage budgets and rotation.

## Data handling

LLM mode sends the question, recent messages, field metadata and calculated tool outputs to OpenAI after explicit consent. Responses API calls set `store=False` to disable application-state storage for those response objects; this is not a Zero Data Retention guarantee and does not remove other provider retention such as abuse monitoring. Review the provider's current [data controls](https://developers.openai.com/api/docs/guides/your-data). Raw DataFrame rows are not sent through the registered analytical tools. Aggregated values may still be sensitive. Do not upload confidential, personal or regulated data without authorization and a data-protection review.

Sensitive-dimension checks are heuristic and are not a substitute for data classification, authentication, access control or governance. This project does not provide production multi-tenant isolation.
