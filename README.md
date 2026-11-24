# LEGALAIR — Legal Document Intelligence

LEGALAIR is an experimental document-processing platform focused on extracting, classifying and organizing information from legal and administrative files. The repository combines a Python API, a web interface and local/LLM-assisted analysis components.

## Intended workflow
1. Ingest supported documents.
2. Extract text using parsing and OCR where available.
3. Classify document types and identify relevant entities.
4. Produce structured summaries and issue lists.
5. Route uncertain or consequential outputs for human review.

## Architecture
The current repository includes API, web, document-processing and deployment components. Treat the technology list and workflow above as the intended product shape; verify exact capabilities against the current source and tests before relying on them.

## Critical limitations
- AI output is not legal advice and must not be represented as a lawyer's opinion.
- Extraction errors, missing pages, OCR mistakes and hallucinated interpretations are possible.
- Human review is mandatory before any filing, deadline calculation, client communication or legal decision.
- Do not upload confidential client material to external model providers without a lawful basis, client authorization and appropriate data-processing controls.

## Status
Pre-release engineering project. The README's former version and deployment badges referenced placeholder organization paths; they have been removed rather than implying external CI or production status. No production readiness or legal accuracy guarantee is claimed.

## Development
Inspect the API and web package manifests for the current supported commands. Keep secrets in environment variables, use synthetic documents in tests and verify authentication, retention, access control and audit logging before deployment.

## License
See LICENSE.
