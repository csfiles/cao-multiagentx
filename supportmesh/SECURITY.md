# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ Active  |

## Reporting a Vulnerability

**Do not open public GitHub issues for security vulnerabilities.**

Email: security@supportmesh.dev

Please include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested mitigations

We aim to acknowledge reports within 48 hours and provide a fix timeline within 7 days for critical issues.

## Security Defaults

SupportMesh is designed to be **safe by default**:

### Mutation Safety

The `SUPPORTMESH_ALLOW_MUTATIONS` environment variable defaults to `false`. When false:

- `create_refund_request` **never writes** to any storage
- All mutating operations return dry-run proposals
- No irreversible actions are taken automatically

Only set `SUPPORTMESH_ALLOW_MUTATIONS=true` in controlled environments after explicit review.

### AWS Credentials

- **Never commit** AWS credentials, API keys, or `.env` files to source control
- Use IAM roles or AWS profiles instead of static credentials
- Follow the principle of least privilege for any IAM policies
- The `.gitignore` excludes `.env` and credential files by default

### Agent Safety

- Agents are instructed never to invent order, refund, or policy information
- The `refund_specialist` agent requires explicit confirmation before proposing refunds
- The `communication_agent` is instructed to state uncertainty rather than fabricate

### MCP Server

- The MCP server binds to `127.0.0.1` (localhost) by default
- Do not expose the MCP server port publicly without authentication
- In production, place the MCP server behind a private VPC endpoint

### Dependency Security

- Dependencies are pinned to minimum versions; review changelogs before updating
- Run `pip audit` or `uv pip audit` periodically to check for known CVEs

## Do Not Report

The following are known limitations, not security vulnerabilities:
- Local demo mode does not authenticate API callers (by design for development)
- The MCP server has no built-in authentication (use network controls in production)
