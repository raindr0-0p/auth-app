# Authentication Web Application

A complete, production-oriented authentication system built with React (frontend) and FastAPI (backend).

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Local Development](#local-development)
- [Environment Variables](#environment-variables)
- [Running Tests](#running-tests)
- [Production Considerations](#production-considerations)
- [API Documentation](#api-documentation)
- [How to Study This Project](#how-to-study-this-project)
- [End-to-End Request Walkthrough](#end-to-end-request-walkthrough)
- [What a Real Company Would Add Next](#what-a-real-company-would-add-next)

## Overview

This is a full-stack authentication application that implements secure user authentication with features like:
- User registration with email verification
- Secure login/logout
- Password reset and change functionality
- Session management
- Rate limiting
- CSRF protection
- Email verification workflows

The backend uses server-side sessions (not JWT tokens stored in localStorage) for enhanced security.

## Architecture

```
Browser
|
| HTTPS / REST API
v
FastAPI backend
|
+-------------------+
|                   |
v                   v
PostgreSQL               Redis
persistent data          temporary/high-speed state
```

- **PostgreSQL**: Source of truth for users, sessions, and token data
- **Redis**: Used for rate limiting and temporary state
- **FastAPI**: Backend API framework
- **React**: Frontend library

## Features

### Authentication
- ✅ User registration with email verification
- ✅ Secure login with password verification (Argon2id)
- ✅ Logout with session invalidation
- ✅ Email verification (with expiration and single-use tokens)
- ✅ Password reset (with expiration and single-use tokens)
- ✅ Password change (requires current password)
- ✅ Session management (list and revoke sessions)
- ✅ Remember me functionality (via persistent sessions)

### Security
- ✅ Argon2id for password hashing
- ✅ HttpOnly, Secure, SameSite cookies
- ✅ CSRF protection (double-submit cookie)
- ✅ Rate limiting (login, signup, forgot password, resend verification)
- ✅ Input validation with Pydantic
- ✅ No account enumeration (generic responses)
- ✅ Security headers (CSP, X-Content-Type-Options, etc.)
- ✅ Session token hashing (never store raw tokens)
- ✅ Proper CORS configuration

### Infrastructure
- ✅ Docker Compose for local development
- ✅ Environment-based configuration
- ✅ Alembic for database migrations
- ✅ Comprehensive test suite
- ✅ Development email service (logs to console)

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy 2.x ORM
- **Cache**: Redis
- **Authentication**: 
  - Password hashing: Argon2id (via passlib)
  - Sessions: Server-side with token hashing
  - CSRF: Double-submit cookie
- **Validation**: Pydantic
- **Migrations**: Alembic
- **Testing**: Pytest, pytest-asyncio
- **Dev Tools**: Python-dotenv for environment variables

### Frontend
- **Library**: React 18
- **Build Tool**: Vite
- **Language**: TypeScript
- **Routing**: React Router DOM
- **Styling**: Plain CSS
- **HTTP**: Fetch API with credentials: 'include'

### DevOps
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **CI/CD**: Ready for GitHub Actions, GitLab CI, etc.

## Local Development

### Prerequisites
- Docker and Docker Compose
- Git

### Setup

1. Clone the repository
```bash
git clone <repository-url>
cd auth
```

2. Create a `.env` file in the backend directory based on `.env.example`:
```bash
cd backend
cp .env.example .env
# Edit .env to set your SECRET_KEY and other values
```

3. Start the services:
```bash
cd ..
docker compose up --build
```

4. The application will be available at:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

5. Initialize the database (handled automatically on startup):
   ```bash
   # The docker-compose command runs migrations automatically
   # To run migrations manually:
   docker compose exec backend alembic upgrade head
   ```

### Development Mode Features
- Email verification links are logged to the backend console
- Rate limits are configured for development (adjust in .env)
- CORS is configured for localhost:5173
- Cookie security flags are relaxed for development (secure=false)

## Environment Variables

Create a `.env` file in the `backend/` directory with the following variables:

| Variable | Description | Example/Default |
|----------|-------------|-----------------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg2://postgres:postgres@localhost:5432/auth_db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `SECRET_KEY` | Secret key for cryptographic operations | Generate with: `openssl rand -hex 32` |
| `FRONTEND_URL` | Frontend URL for email links | `http://localhost:5173` |
| `SESSION_EXPIRE_MINUTES` | Session lifetime | `60` |
| `PASSWORD_RESET_EXPIRE_MINUTES` | Password reset token lifetime | `30` |
| `EMAIL_VERIFICATION_EXPIRE_MINUTES` | Email verification token lifetime | `60` |
| `LOGIN_RATE_LIMIT_PER_MINUTE` | Login attempts per minute | `5` |
| `SIGNUP_RATE_LIMIT_PER_MINUTE` | Signup attempts per minute | `3` |
| `FORGOT_PASSWORD_RATE_LIMIT_PER_HOUR` | Forgot password requests per hour | `3` |
| `RESEND_VERIFICATION_RATE_LIMIT_PER_HOUR` | Resend verification requests per hour | `3` |
| `ENVIRONMENT` | Application environment | `development` (or `production`, `testing`) |

### Generating Secrets
```bash
# For SECRET_KEY
openssl rand -hex 32

# For other secrets, use similar random generation
```

## Running Tests

### Backend Tests
```bash
# From the backend directory
cd backend
pip install -r requirements.txt  # if not already installed
pytest
```

### Frontend Tests
*(Frontend testing not implemented in this version but would use Jest/Vitest)*

## Production Considerations

Before deploying to production, you should:

1. **Change Environment Variables**:
   - Set `ENVIRONMENT=production`
   - Use strong, unique values for `SECRET_KEY`
   - Update `FRONTEND_URL` to your production domain
   - Configure proper email service (see below)

2. **Security Settings**:
   - Set `COOKIE_SECURE=true` in config.py
   - Consider using `COOKIE_SAMESITE="strict"` or `"lax"`
   - Ensure your deployment serves only over HTTPS
   - Use a proper secrets management system (AWS Secrets Manager, HashiCorp Vault, etc.)

3. **Email Service**:
   - Replace the `DevelopmentEmailService` with a real email provider
   - Configure SMTP settings or use a service like SendGrid, Mailgun, or Amazon SES
   - Update the `email_service.py` file to implement actual email sending

4. **Database**:
   - Use managed PostgreSQL service (AWS RDS, Google Cloud SQL, etc.)
   - Configure proper backups and monitoring
   - Set appropriate connection limits

5. **Redis**:
   - Use managed Redis service (AWS ElastiCache, Redis Cloud, etc.)
   - Configure persistence if needed for rate limiting data
   - Set appropriate memory policies

6. **Deployment**:
   - Use a reverse proxy (NGINX, Traefik) for SSL termination
   - Consider using a process manager like Gunicorn with Uvicorn workers
   - Implement proper logging and monitoring
   - Set up health checks for your orchestration platform (Kubernetes, Docker Swarm, etc.)

7. **Performance**:
   - Enable caching layers where appropriate
   - Use CDN for static frontend assets
   - Monitor database query performance
   - Consider read replicas for scaling reads

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

The API documentation includes:
- Detailed endpoint descriptions
- Request/response schemas
- Authentication requirements
- Example responses

## How to Study This Project

Follow this order to understand the codebase:

### 1. User Model (`backend/app/models/user.py`)
- **Problem**: Securely store user information
- **Why**: Central entity for authentication
- **Data enters**: Registration endpoint, direct database insertion
- **Data leaves**: User information (excluding sensitive fields)
- **Security threat**: Password exposure, unauthorized access
- **Interactions**: Sessions, email verification, password reset tokens

### 2. Password Hashing (`backend/app/security/password.py`)
- **Problem**: Securely store passwords
- **Why**: Prevent password leakage if database is compromised
- **Data enters**: Plain password during registration/password change
- **Data leaves**: Argon2id hash (one-way)
- **Security threat**: Password cracking, rainbow table attacks
- **Interactions**: User model, login, password change, reset password

### 3. Signup Route (`backend/app/routers/auth.py` -> `signup`)
- **Problem**: Create new user accounts securely
- **Why**: First step in user onboarding
- **Data enters**: Name, email, password
- **Data leaves**: Success message (generic to prevent enumeration)
- **Security threat**: Account enumeration, weak passwords
- **Interactions**: User model (creation), email service (verification), rate limiting

### 4. Database Transaction (Throughout services)
- **Problem**: Maintain data consistency
- **Why**: Prevent partial updates in case of failures
- **Data enters**: Service layer function calls
- **Data leaves**: Committed or rolled back database state
- **Security threat**: Inconsistent state, lost updates
- **Interactions**: All database operations use SQLAlchemy sessions

### 5. Login Route (`backend/app/routers/auth.py` -> `login`)
- **Problem**: Authenticate users and create sessions
- **Why**: Main authenticated entry point
- **Data enters**: Email, password
- **Data leaves**: User data, session cookie, CSRF cookie
- **Security threat**: Brute force, credential stuffing
- **Interactions**: User model (lookup), session creation, rate limiting

### 6. Session Generation (`backend/app/services/auth_service.py` -> `create_session`)
- **Problem**: Create secure, trackable user sessions
- **Why**: Maintain authenticated state without exposing secrets
- **Data enters**: User ID, optional user agent/IP
- **Data leaves**: Session token (to client), hash (stored in DB)
- **Security threat**: Session hijacking, fixation
- **Interactions**: Session model, cookie setting

### 7. Cookie Creation (`backend/app/security/cookies.py`)
- **Problem**: Securely store session identifier in browser
- **Why**: Maintain state across requests
- **Data enters**: Session token
- **Data leaves**: Set-Cookie header
- **Security theme**: XSS, CSRF, session theft
- **Interactions**: Login, logout, session validation

### 8. Authentication Dependency (`backend/app/dependencies/auth.py`)
- **Problem**: Verify user identity on protected routes
- **Why**: Centralized authentication logic
- **Data enters**: Session cookie from request
- **Data leaves**: User object or 401 error
- **Security threat**: Unauthorized access, session replay
- **Interactions**: Session model, token validation

### 9. `/me` Endpoint (`backend/app/routers/auth.py` -> `get_current_user_info`)
- **Problem**: Provide current user information
- **Why**: Frontend needs to know auth status
- **Data enters**: Validated session (via dependency)
- **Data leaves**: User public information
- **Security threat**: Information leakage
- **Interactions**: Authentication dependency, user model

### 10. Logout (`backend/app/routers/auth.py` -> `logout`)
- **Problem**: End user session securely
- **Why**: Allow users to terminate access
- **Data enters**: Session cookie
- **Data leaves**: Cleared cookies, revoked session
- **Security threat**: Session persistence after logout
- **Interactions**: Session model, cookie clearing

### 11. Redis Rate Limiting (`backend/app/security/rati_limit.py`)
- **Problem**: Prevent abuse of authentication endpoints
- **Why**: Protect against brute force and DoS
- **Data enters**: Request identifier (IP)
- **Data leaves**: Allow/deny decision
- **Security threat**: Credential stuffing, account lockout
- **Interactions**: Login, signup, forgot password, resend verification endpoints

### 12. CSRF Protection (`backend/app/security/csrf.py`)
- **Problem**: Prevent Cross-Site Request Forgery
- **Why**: Protect state-changing operations
- **Data enters**: CSRF token from cookie and header
- **Data leaves**: Allow/deny decision
- **Security threat**: CSRF attacks on login, password change, etc.
- **Interactions**: All state-changing endpoints (login, logout, password change, etc.)

### 13. Email Verification (`backend/app/services/auth_service.py` -> `verify_email_token`)
- **Problem**: Verify user email address
- **Why**: Ensure valid contact information
- **Data enters**: Verification token
- **Data leaves**: Success/failure, email_verified flag update
- **Security threat**: Fake account creation, email spraying
- **Interactions**: EmailVerificationToken model, User model

### 14. Password Reset (`backend/app/services/auth_service.py` -> `reset_password`)
- **Problem**: Allow users to regain access
- **Why**: Secure password recovery
- **Data enters**: Reset token, new password
- **Data leaves**: Success/failure, updated password, revoked sessions
- **Security threat**: Account takeover, token leakage
- **Interactions**: PasswordResetToken model, User model, session revocation

### 15. Session Management (`backend/app/services/session_service.py`)
- **Problem**: Allow users to view and control their sessions
- **Why**: Increase transparency and security control
- **Data enters**: User ID
- **Data leaves**: List of active sessions
- **Security threat**: Unauthorized session access
- **Interactions**: Session model, user model

### 16. Tests (`backend/tests/`)
- **Problem**: Ensure correctness and prevent regressions
- **Why**: Maintain reliability as code evolves
- **Data enters**: Test requests and assertions
- **Data leaves**: Pass/fail results
- **Security threat**: Undetected vulnerabilities
- **Interactions**: All components via test client

### 17. Docker (`backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`)
- **Problem**: Consistent, reproducible deployment
- **Why**: Eliminate "works on my machine" issues
- **Data enters**: Application code and dependencies
- **Data leaves**: Running containers
- **Security threat**: Inconsistent environments
- **Interactions**: All components via containerization

### 18. Deployment Architecture (Diagram in README)
Shows how components connect in production with reverse proxy, load balancer, etc.

## End-to-End Request Walkthrough

### A. New User Signup

1. **Browser**: User fills registration form and submits
2. **HTTP Request**: `POST /api/auth/signup` with JSON `{name, email, password}`
3. **FastAPI Route**: `signup` endpoint in `auth.py` router
4. **Validation**: Pydantic model validates input
5. **Rate Limiting**: Checks IP-based rate limit for signup
6. **Service Layer**: `create_user` in `auth_service.py`
   - Checks for existing email (returns generic message if exists)
   - Hashes password with Argon2id
   - Creates user record
   - Generates email verification token (hashed for storage)
   - Logs verification link to console (development)
7. **Database**: User and email_verification_token records created
8. **Response**: Generic success message to prevent email enumeration
9. **Browser**: Shows message and redirects to login after delay

### B. Login

1. **Browser**: User enters credentials and submits
2. **HTTP Request**: `POST /api/auth/login` with JSON `{email, password}`
3. **FastAPI Route**: `login` endpoint in `auth.py` router
4. **Validation**: Pydantic model validates input
5. **Rate Limiting**: Checks IP-based rate limit for login
6. **Service Layer**: `authenticate_user` in `auth_service.py`
   - Looks up user by email (normalized to lowercase)
   - Verifies password against Argon2id hash
   - Returns None on failure (generic error to prevent enumeration)
7. **Additional Checks**: Verifies email is confirmed
8. **Service Layer**: `create_session` in `auth_service.py`
   - Generates secure random session token
   - Hashes token for storage
   - Creates session record with expiration
   - Stores user agent and IP (optional)
9. **Middleware**: Sets session cookie (HttpOnly, Secure, SameSite)
   - Sets CSRF cookie (readable by JavaScript)
10. **Response**: User data (excluding sensitive fields)
11. **Browser**: Stores cookies, redirects to dashboard

### C. Authenticated `/me`

1. **Browser**: Makes request to `/api/auth/me` (on app load or navigation)
2. **HTTP Request**: `GET /api/auth/me` with credentials: 'include'
3. **FastAPI Route**: `get_current_user_info` endpoint
4. **Dependency**: `get_current_user` validates session
   - Extracts session token from cookie
   - Hashes token and looks up in sessions table
   - Checks for revocation and expiration
   - Updates last_used_at timestamp
   - Returns associated user
5. **Response**: User public information (id, email, name, email_verified, is_active, created_at)
6. **Browser**: Updates UI to show authenticated state

### D. Logout

1. **Browser**: User clicks logout button
2. **HTTP Request**: `POST /api/auth/logout` with credentials: 'include'
3. **FastAPI Route**: `logout` endpoint in `auth.py` router
4. **Dependency**: `get_current_user` validates session
5. **Service Layer**: `revoke_session` in `auth_service.py`
   - Extracts session token from cookie
   - Hashes token and finds session
   - Sets revoked_at timestamp
6. **Middleware**: Clears session and CSRF cookies
7. **Response**: Success message
8. **Browser**: Removes cookies, redirects to login

### E. Forgot Password

1. **Browser**: User enters email and submits
2. **HTTP Request**: `POST /api/auth/forgot-password` with JSON `{email}`
3. **FastAPI Route**: `forgot_password` endpoint in `auth.py` router
4. **Validation**: Pydantic model validates input
5. **Rate Limiting**: Checks IP-based rate limit for forgot password
6. **Service Layer**: (Generic response to prevent enumeration)
   - In real implementation: would look up user by email
   - If found and not locked: generate password reset token (hashed)
   - Store token hash with expiration
   - Send reset link via email service
7. **Response**: Generic message regardless of account existence
8. **Browser**: Shows message and redirects to login

### F. Password Reset

1. **Browser**: User clicks link in email, enters new password, submits
2. **HTTP Request**: `POST /api/auth/reset-password` with JSON `{token, new_password}`
3. **FastAPI Route**: `reset_password_endpoint` in `auth.py` router
4. **Validation**: Pydantic model validates input (token, new_password)
5. **Service Layer**: `reset_password` in `auth_service.py`
   - Hashes token and looks up password_reset_token record
   - Checks token not used and not expired
   - Hashes new password with Argon2id
   - Updates user's hashed_password
   - Marks token as used
   - Revokes all existing sessions for user (security best practice)
6. **Database**: PasswordResetToken record updated, User record updated, Session records updated
7. **Response**: Success message
8. **Browser**: Redirects to login page

## What a Real Company Would Add Next

### Essential Enhancements
1. **Multi-Factor Authentication (MFA)**
   - TOTP (Google Authenticator, Authy)
   - SMS-based OTP
   - Push notifications (Duo, Okta Verify)
   - Hardware keys (YubiKey, Titan Security Key)

2. **Social Login (OAuth/OIDC)**
   - Google, Facebook, Apple, Microsoft
   - Enterprise SSO (SAML, Azure AD)
   - Account linking capabilities

3. **Passkeys/WebAuthn**
   - Passwordless authentication
   - Biometric integration (Touch ID, Face ID, Windows Hello)
   - Cross-device credential synchronization

4. **Advanced Session & Device Management**
   - Detailed device information (browser, OS, IP geolocation)
   - Session activity tracking (last seen, location)
   - Remote session termination
   - Trusted devices feature

5. **Security Enhancements**
   - Suspicious login detection (impossible travel, new device)
   - Login attempt throttling by account (not just IP)
   - Password breach checking (haveibeenpwned API)
   - Account lockout after failed attempts
   - Security audit logs (SIEM integration)

6. **Operational Improvements**
   - Centralized secrets management (AWS Secrets Manager, HashiCorp Vault)
   - Observability (structured logging, metrics, tracing)
   - Distributed rate limiting (for microservices)
   - Background job queue for email sending (Celery, RQ)
   - Email template management and localization
   - Feature flags for gradual rollouts

7. **Compliance & Privacy**
   - GDPR/CCPA data subject access request tools
   - Data retention and deletion policies
   - Consent management for communications
   - Regular security penetration testing
   - SOC 2, ISO 27001 compliance preparations

8. **Scalability Considerations**
   - Read replicas for PostgreSQL
   - Redis clustering for high availability
   - CDN for frontend assets
   - API gateway for traffic management
   - Microservices decomposition (auth as separate service)

9. **User Experience Improvements**
   - Progressive enhancement for JavaScript-disabled browsers
   - Internationalization (i18n) support
   - Accessibility compliance (WCAG 2.1 AA)
   - Password strength meter during creation
   - Inline form validation
   - Toast notifications for user feedback

### Already Addressed in This Implementation
- ✅ Server-side sessions (more secure than localStorage JWT)
- ✅ Argon2id password hashing (industry standard)
- ✅ HttpOnly secure cookies with CSRF protection
- ✅ Rate limiting on critical endpoints
- ✅ Email verification and password reset workflows
- ✅ Session management and revocation
- ✅ Generic responses to prevent account enumeration
- ✅ Proper CORS and security headers
- ✅ Environment-based configuration
- ✅ Comprehensive test suite
- ✅ Dockerized for consistent deployment
- ✅ Alembic migrations for schema evolution
- ✅ Development email service (console logging)

This implementation provides a solid foundation that addresses the core security concerns of authentication while remaining understandable and maintainable. The production enhancements listed above would be added incrementally based on specific threat models, compliance requirements, and scaling needs.