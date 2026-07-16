# Security policy

Report suspected vulnerabilities privately to the repository owner; do not include sensitive source text in a public issue.

TextSignal reads CSV, XLSX, JSON, and TXT up to 50 MB, applies row/column limits, never executes workbook macros, and
neutralizes spreadsheet-formula prefixes in exports. Aggregate evidence excludes raw text and row assignments.

These controls do not create a hardened multi-tenant service. Internet hosting requires authentication, TLS, authorization,
rate limiting, secure headers, isolated storage, dependency monitoring, appropriate logging, deletion controls, and a
threat model for the deployment and data classification.
