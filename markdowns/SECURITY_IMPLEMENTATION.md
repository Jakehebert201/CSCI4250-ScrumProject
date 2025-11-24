# Security Implementation Guide

This document describes the security features implemented in the Student Location Tracker application.

## Security Features Implemented

### 1. CSRF Protection (Flask-WTF)
- **Status**: ✅ Implemented
- **Description**: Cross-Site Request Forgery protection on all forms
- **Configuration**: Automatic CSRF tokens on all POST requests
- **Usage**: CSRF tokens are automatically added to forms by Flask-WTF

### 2. Rate Limiting (Flask-Limiter)
- **Status**: ✅ Implemented
- **Description**: Prevents brute force attacks and API abuse
- **Limits**:
  - Login endpoints: 5 attempts per minute
  - Registration endpoints: 10 attempts per hour
  - Global default: 200 requests per day, 50 per hour
- **Storage**: In-memory (consider Redis for production)

### 3. Security Headers (Flask-Talisman)
- **Status**: ✅ Implemented (Production only)
- **Features**:
  - HTTPS enforcement
  - Strict-Transport-Security (HSTS)
  - Content-Security-Policy (CSP)
  - X-Frame-Options
  - X-Content-Type-Options
- **Note**: Only enabled when `FLASK_ENV=production`

### 4. Input Validation & Sanitization
- **Status**: ✅ Implemented
- **Module**: `studenttracker/validators.py`
- **Features**:
  - HTML/JavaScript sanitization using bleach
  - Email validation
  - Password strength requirements (8+ chars, uppercase, lowercase, number)
  - Username validation (alphanumeric + underscores)
  - Student/Employee ID validation
  - Name validation
  - GPS coordinate validation

### 5. Secure Session Configuration
- **Status**: ✅ Implemented
- **Features**:
  - `SESSION_COOKIE_SECURE`: True in production (HTTPS only)
  - `SESSION_COOKIE_HTTPONLY`: True (prevents JavaScript access)
  - `SESSION_COOKIE_SAMESITE`: 'Lax' (CSRF protection)
  - `PERMANENT_SESSION_LIFETIME`: 24 hours

### 6. Password Security
- **Status**: ✅ Implemented
- **Features**:
  - Bcrypt hashing (via Werkzeug)
  - Password strength validation
  - Minimum 8 characters
  - Requires uppercase, lowercase, and number

### 7. Debug Mode Control
- **Status**: ✅ Implemented
- **Configuration**: Debug mode only enabled via `FLASK_DEBUG=true` environment variable
- **Default**: Debug disabled in production

### 8. SQL Injection Protection
- **Status**: ✅ Implemented
- **Method**: SQLAlchemy ORM with parameterized queries
- **Note**: Avoid raw SQL queries

## Installation

Install security dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

### Development Environment

```bash
# .env file
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_SECRET=your-dev-secret-key
```

### Production Environment

```bash
# .env file
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_SECRET=your-strong-random-secret-key-at-least-32-characters

# Additional production settings
SESSION_COOKIE_SECURE=True
```

## Password Requirements

When users register, passwords must meet these requirements:
- Minimum 8 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one number (0-9)

## Rate Limiting Details

### Login Endpoints
- **Limit**: 5 attempts per minute per IP
- **Endpoints**: `/login/student`, `/login/professor`
- **Purpose**: Prevent brute force attacks

### Registration Endpoints
- **Limit**: 10 attempts per hour per IP
- **Endpoints**: `/register/student`, `/register/professor`
- **Purpose**: Prevent spam registrations

### Global Limits
- **Daily**: 200 requests per IP
- **Hourly**: 50 requests per IP
- **Purpose**: General API protection

## Security Headers (Production)

When `FLASK_ENV=production`, the following headers are automatically added:

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' https://maps.googleapis.com https://accounts.google.com; ...
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
```

## Input Validation

All user inputs are validated and sanitized:

### Sanitization
- Removes HTML tags
- Strips JavaScript
- Prevents XSS attacks

### Validation
- Email format validation
- Username format (alphanumeric + underscores)
- Student/Employee ID format
- Name format (letters, spaces, hyphens, apostrophes)
- Coordinate ranges (lat: -90 to 90, lng: -180 to 180)

## Best Practices

### For Developers

1. **Never commit `.env` files** - They contain secrets
2. **Use environment variables** for all sensitive configuration
3. **Always validate user input** before processing
4. **Use parameterized queries** - Never concatenate SQL
5. **Keep dependencies updated** - Run `pip list --outdated` regularly
6. **Review security logs** - Monitor for suspicious activity

### For Deployment

1. **Use HTTPS** - Always in production
2. **Set strong SECRET_KEY** - At least 32 random characters
3. **Disable debug mode** - Set `FLASK_DEBUG=False`
4. **Use production WSGI server** - Gunicorn or uWSGI, not Flask dev server
5. **Configure firewall** - Limit access to necessary ports
6. **Regular backups** - Backup database regularly
7. **Monitor logs** - Set up logging and monitoring
8. **Use Redis for rate limiting** - In production, use Redis instead of memory

### For Users

1. **Use strong passwords** - Follow password requirements
2. **Prefer OAuth login** - More secure than password
3. **Log out on shared devices** - Always log out
4. **Report suspicious activity** - Contact administrators

## Security Checklist

- [x] CSRF protection enabled
- [x] Rate limiting on authentication endpoints
- [x] Security headers (production)
- [x] Input validation and sanitization
- [x] Secure session configuration
- [x] Password strength requirements
- [x] Debug mode controlled by environment
- [x] SQL injection protection (ORM)
- [x] .env file in .gitignore
- [ ] Location data encryption at rest (future enhancement)
- [ ] Two-factor authentication (future enhancement)
- [ ] Security audit logging (future enhancement)

## Testing Security Features

### Test Rate Limiting

```bash
# Try to login more than 5 times in a minute
for i in {1..6}; do
  curl -X POST http://localhost:5000/app/login/student \
    -d "username=test&password=wrong"
done
# 6th request should be rate limited
```

### Test Password Validation

Try registering with weak passwords:
- "short" - Should fail (too short)
- "alllowercase" - Should fail (no uppercase)
- "ALLUPPERCASE" - Should fail (no lowercase)
- "NoNumbers" - Should fail (no numbers)
- "ValidPass123" - Should succeed

### Test Input Sanitization

Try registering with malicious input:
- Username: `<script>alert('xss')</script>`
- Should be sanitized to: `scriptalertxssscript`

## Troubleshooting

### Rate Limit Errors

If you're getting rate limited during development:
1. Restart the Flask application (clears in-memory limits)
2. Or temporarily increase limits in `extensions.py`

### CSRF Token Errors

If you get CSRF errors:
1. Ensure forms include `{{ csrf_token() }}` in templates
2. Check that CSRF is initialized in `__init__.py`
3. Verify cookies are enabled in browser

### Security Headers Not Applied

Security headers are only applied in production:
1. Set `FLASK_ENV=production` in `.env`
2. Restart the application
3. Check headers with browser dev tools

## Future Enhancements

1. **Location Data Encryption**: Encrypt GPS coordinates at rest
2. **Two-Factor Authentication**: Add 2FA for enhanced security
3. **Security Audit Logging**: Log all security-relevant events
4. **Redis for Rate Limiting**: Use Redis in production for distributed rate limiting
5. **API Key Authentication**: For programmatic access
6. **IP Whitelisting**: For administrative functions
7. **Automated Security Scanning**: Integrate security scanning tools

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/latest/security/)
- [Flask-WTF Documentation](https://flask-wtf.readthedocs.io/)
- [Flask-Limiter Documentation](https://flask-limiter.readthedocs.io/)
- [Flask-Talisman Documentation](https://github.com/GoogleCloudPlatform/flask-talisman)

## Contact

For security concerns, please refer to [SECURITY.md](SECURITY.md) for reporting procedures.

---

*Last Updated: November 2025*
