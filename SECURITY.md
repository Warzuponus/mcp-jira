# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

Please report (suspected) security vulnerabilities to security@yourdomain.com. You will receive a response from us within 48 hours. If the issue is confirmed, we will release a patch as soon as possible depending on complexity but historically within a few days.

## Security Measures

1. **Authentication**: All JIRA API calls require proper authentication using API tokens
2. **Data Protection**: Sensitive data like API tokens should be provided via environment variables
3. **Input Validation**: All inputs are validated before being used in JIRA API calls
4. **Error Handling**: Errors are caught and handled appropriately without exposing sensitive information