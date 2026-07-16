# Privacy

TextSignal is local-first. It includes no account system, telemetry SDK, advertising, remote database, external AI call, or
required API connection. Browser input is processed by the local Streamlit process unless the user hosts or moves it.

Open text can contain names, contacts, health details, complaints, confidential plans, or unique stories. Remove direct and
indirect identifiers and irrelevant sensitive data before upload. The on-screen masker recognizes common email, phone, and
URL patterns only; it is not anonymization and can miss or over-mask content.

Evidence packs exclude source text, masked snippets, document IDs, and document-level topic assignments. Aggregate terms,
counts, group contrasts, topic terms, source fingerprints, and human notes can still be confidential. Review every export.

A hosted operator is responsible for TLS, authentication, authorization, logs, backups, retention, deletion, incident
response, data-processing roles, and applicable law. Local-first defaults do not make an internet deployment private.
