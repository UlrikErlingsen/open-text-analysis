# Security policy

Report suspected vulnerabilities privately to the repository owner; do not include sensitive source text in a public issue.

Run locally, Text Signal has no built-in size limit on CSV, XLSX, JSON, and TXT (Streamlit's upload cap is
`TEXTSIGNAL_MAX_UPLOAD_MB`, or `STREAMLIT_SERVER_MAX_UPLOAD_SIZE` in Docker, default 10,000 MB); any shared or public deployment
should set `SIGNAL_PUBLIC=1`, which applies upload, row and column caps. It never executes workbook macros, and
neutralizes spreadsheet-formula prefixes in exports. Aggregate evidence excludes raw text and row assignments.

These controls do not create a hardened multi-tenant service. Internet hosting requires authentication, TLS, authorization,
rate limiting, secure headers, isolated storage, dependency monitoring, appropriate logging, deletion controls, and a
threat model for the deployment and data classification.
