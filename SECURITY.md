# Security Policy

## Overview

The Student Location Tracker application takes security seriously. This document outlines our security practices, supported versions, and how to report security vulnerabilities.

## Supported Versions

We actively maintain and provide security updates for the following versions:

| Version | Supported          | Notes                    |
| ------- | ------------------ | ------------------------ |
| 1.x.x   | :white_check_mark: | Current stable release   |
| 0.9.x   | :white_check_mark: | Legacy support until EOL |
| < 0.9   | :x:                | No longer supported      |

## Security Features

### Authentication & Authorization
- **Multi-factor Authentication**: OAuth 2.0 integration with Google
- **Session Management**: Secure session handling with Flask-Session
- **Role-based Access Control**: Separate student and professor access levels
- **Password Security**: Bcrypt hashing for traditional login credentials
- **CAPTCHA Protection**: Impossible CAPTCHA system to encourage OAuth usage

### Data Protection
- **Location Privacy**: GPS coordinates are processed server-side only
- **Data Encryption**: Sensitive data encrypted at rest and in transit
- **Database Security**: Parameterized queries to prevent SQL injection
- **Input Validation**: All user inputs are sanitized and validated
- **CSRF Protection**: Cross-Site Request Forgery tokens on all forms

### Infrastructure Security
- **HTTPS Enforcement**: All communications encrypted with TLS 1.2+
- **Secure Headers**: Content Security Policy, HSTS, and other security headers
- **Rate Limiting**: API endpoints protected against abuse
- **Error Handling**: No sensitive information exposed in error messages

### Privacy Controls
- **Location Sharing**: Opt-in location sharing with granular controls
- **Data Retention**: Automatic cleanup of old notifications and location data
- **User Consent**: Clear privacy policies and consent mechanisms
- **Data Minimization**: Only collect necessary data for functionality

## Reporting a Vulnerability

### How to Report

If you discover a security vulnerability, please report it responsibly:

1. **Email**: Send details to your security contact email
2. **Subject Line**: "Security Vulnerability Report - [Brief Description]"
3. **Include**:
   - Detailed description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact assessment
   - Suggested remediation (if any)
   - Your contact information

### What to Expect

- **Acknowledgment**: We will acknowledge receipt within 24 hours
- **Initial Assessment**: Preliminary assessment within 72 hours
- **Regular Updates**: Status updates every 7 days until resolution
- **Resolution Timeline**: Critical issues resolved within 7 days, others within 30 days
- **Credit**: Security researchers will be credited (with permission) in our security advisories

### Vulnerability Severity Levels

| Severity | Description | Response Time |
|----------|-------------|---------------|
| **Critical** | Remote code execution, data breach | 24 hours |
| **High** | Authentication bypass, privilege escalation | 72 hours |
| **Medium** | Information disclosure, CSRF | 7 days |
| **Low** | Minor information leaks, UI issues | 30 days |

## Security Best Practices for Users

### For Students
- Use strong, unique passwords for traditional login
- Prefer OAuth login when available
- Review location sharing permissions regularly
- Log out from shared devices
- Report suspicious activity immediately

### For Professors
- Enable two-factor authentication if available
- Use secure networks when accessing the system
- Regularly review class enrollment and permissions
- Follow data protection guidelines for student information
- Report any unauthorized access attempts

### For Administrators
- Keep the application updated to the latest version
- Monitor system logs for suspicious activity
- Implement proper backup and recovery procedures
- Use environment variables for sensitive configuration
- Regularly audit user permissions and access logs

## Security Configuration

### Required Environment Variables
```bash
# Security Configuration
SECRET_KEY=your-secret-key-here
OAUTH_CLIENT_ID=your-oauth-client-id
OAUTH_CLIENT_SECRET=your-oauth-client-secret
DATABASE_URL=your-secure-database-url

# Optional Security Settings
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

### Recommended Deployment Settings
- Use HTTPS in production
- Set secure cookie flags
- Configure proper CORS policies
- Enable security headers
- Use a reverse proxy (nginx/Apache)
- Implement rate limiting
- Set up monitoring and alerting

## Compliance

### Data Protection Regulations
- **FERPA**: Educational records protection compliance
- **GDPR**: European data protection regulation compliance
- **CCPA**: California consumer privacy act compliance
- **COPPA**: Children's online privacy protection (if applicable)

### Security Standards
- **OWASP Top 10**: Protection against common web vulnerabilities
- **NIST Cybersecurity Framework**: Following established security practices
- **ISO 27001**: Information security management principles

## Security Changelog

### Version 1.0.0 (Current)
- Implemented OAuth 2.0 authentication
- Added CAPTCHA protection system
- Enhanced location privacy controls
- Implemented notification cleanup system
- Added comprehensive input validation

## Contact Information

For security-related inquiries, please use the appropriate contact method based on the severity of the issue.

## Acknowledgments

We thank the security research community for their responsible disclosure of vulnerabilities and contributions to improving the security of our application.

---

*This security policy is reviewed and updated regularly. Last updated: November 2025*
