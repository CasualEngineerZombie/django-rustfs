# Security Policy

## Supported Versions

The following versions of django-rustfs are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in django-rustfs, please report it responsibly.

**Do NOT open a public issue for security vulnerabilities.**

Instead, please report security issues via:

- Email: rian@pythonist.dev
- GitHub Security Advisories: https://github.com/CasualEngineerZombie/django-rustfs/security/advisories

Please include:
- A description of the vulnerability
- Steps to reproduce (if applicable)
- Potential impact assessment
- Any suggested fixes or mitigations

## Response Timeline

- **Acknowledgment**: Within 48 hours of receiving your report
- **Initial Assessment**: Within 7 days
- **Fix Timeline**: Based on severity, typically within 30 days
- **Disclosure**: Coordinated disclosure after fix is released

## Security Best Practices

When using django-rustfs in production:

- Use HTTPS endpoints for RustFS connections
- Keep your RustFS access keys secure and rotate them regularly
- Use dedicated buckets with appropriate ACLs
- Enable SSL verification in production environments
- Monitor access logs on your RustFS server

## Acknowledgments

We appreciate responsible disclosure and will acknowledge reporters in our release notes (with their permission).
