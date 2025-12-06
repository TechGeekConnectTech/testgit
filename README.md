# 🔐 FastAPI Security - Complete Guide

Complete implementation of OAuth2, JWT tokens, and custom header authentication in FastAPI.

## 📚 Table of Contents

- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Authentication Methods](#-authentication-methods)
- [API Endpoints](#-api-endpoints)
- [Testing](#-testing)
- [Security Concepts](#-security-concepts)
- [Production Checklist](#-production-checklist)

## ✨ Features

- ✅ OAuth2 with Password Bearer Flow
- ✅ JWT token generation and validation
- ✅ Password hashing with bcrypt
- ✅ Custom API key authentication
- ✅ Multiple authentication layers
- ✅ Comprehensive inline documentation
- ✅ Working examples for all endpoints
- ✅ Swagger UI integration

## 🚀 Installation

### Step 1: Clone or Download

```powershell
# Create directory and navigate to it
mkdir fastapi_security_example
cd fastapi_security_example
```

### Step 2: Install Dependencies

```powershell
pip install -r requirements.txt
```

Dependencies installed:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `python-jose` - JWT handling
- `passlib` - Password hashing
- `python-multipart` - Form data support

## 🎯 Quick Start

### Run the Server

```powershell
python main.py
```

Or with uvicorn directly:

```powershell
uvicorn main:app --reload
```

### Access Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API Root**: http://localhost:8000/

### Test Credentials

| Username | Password | Role |
|----------|----------|------|
| johndoe  | secret   | User |
| alice    | secret   | User |

## 🔑 Authentication Methods

### 1️⃣ OAuth2 with JWT (Recommended)

**Step 1: Login to get token**

```powershell
# Using curl
curl -X POST "http://localhost:8000/token" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=johndoe&password=secret"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Step 2: Use token for protected endpoints**

```powershell
# Save token to variable
$TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Access protected endpoint
curl -X GET "http://localhost:8000/users/me" `
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "username": "johndoe",
  "email": "johndoe@example.com",
  "full_name": "John Doe",
  "disabled": false
}
```

### 2️⃣ API Key Header

**Request:**
```powershell
curl -X GET "http://localhost:8000/secure/data" `
  -H "X-API-Key: super-secret-api-key-123"
```

**Valid API Keys:**
- `super-secret-api-key-123`
- `another-valid-key-456`

### 3️⃣ Custom Authorization Header

**Request:**
```powershell
curl -X GET "http://localhost:8000/custom/protected" `
  -H "Authorization: Token my-custom-token"
```

Supports both formats:
- `Authorization: Bearer <token>`
- `Authorization: Token <token>`

### 4️⃣ Multiple Authentication Layers

**Request:**
```powershell
curl -X GET "http://localhost:8000/admin/dashboard" `
  -H "Authorization: Bearer $TOKEN" `
  -H "X-Admin-Token: admin-secret-token"
```

Requires BOTH OAuth2 token AND admin token.

## 📍 API Endpoints

### Public Endpoints (No Auth)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API welcome and info |
| GET | `/public/info` | Security features info |
| POST | `/register` | Register new user |

### Protected Endpoints (OAuth2)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/token` | Login and get JWT token |
| GET | `/users/me` | Get current user info |
| GET | `/users/me/items` | Get user's items |

### Protected Endpoints (API Key)

| Method | Endpoint | Header Required | Description |
|--------|----------|-----------------|-------------|
| GET | `/secure/data` | X-API-Key | Access with API key |

### Protected Endpoints (Custom)

| Method | Endpoint | Header Required | Description |
|--------|----------|-----------------|-------------|
| GET | `/custom/protected` | Authorization: Token | Custom token format |
| GET | `/admin/dashboard` | Authorization + X-Admin-Token | Multi-layer auth |

## 🧪 Testing

### Using Swagger UI (Easiest)

1. Open http://localhost:8000/docs
2. Click **"Authorize"** button (top right)
3. Enter credentials: `johndoe` / `secret`
4. Click **"Authorize"**
5. Try any protected endpoint

### Using PowerShell

```powershell
# 1. Login and save token
$response = Invoke-RestMethod -Uri "http://localhost:8000/token" `
  -Method POST `
  -ContentType "application/x-www-form-urlencoded" `
  -Body "username=johndoe&password=secret"

$token = $response.access_token

# 2. Access protected endpoint
$headers = @{ Authorization = "Bearer $token" }
Invoke-RestMethod -Uri "http://localhost:8000/users/me" -Headers $headers
```

### Using Python

```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/token",
    data={"username": "johndoe", "password": "secret"}
)
token = response.json()["access_token"]

# Access protected endpoint
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:8000/users/me", headers=headers)
print(response.json())
```

## 🎓 Security Concepts

### What is OAuth2?

OAuth2 is an authorization framework that enables applications to obtain limited access to user accounts. 

**Flow in this example:**
1. User sends credentials to `/token`
2. Server validates and returns JWT token
3. Client stores token
4. Client sends token with each request
5. Server validates token and grants access

### What is JWT?

JWT (JSON Web Token) is a compact, URL-safe token format.

**Structure:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJzdWIiOiJqb2huZG9lIiwiZXhwIjoxNjM4MzYwMDAwfQ.
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

**Parts:**
- **Header**: Algorithm and token type
- **Payload**: Claims (data like username, expiration)
- **Signature**: Cryptographic signature to verify integrity

**Verify your token:** https://jwt.io

### Password Hashing with bcrypt

```python
# Plain password -> Hashed password
"secret" -> "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
```

**Why bcrypt?**
- ✅ Slow by design (prevents brute force)
- ✅ Includes salt (prevents rainbow table attacks)
- ✅ Adaptive (can increase difficulty over time)
- ✅ One-way (cannot reverse to get original password)

### Dependencies in FastAPI

Dependencies automatically inject values into endpoint functions:

```python
@app.get("/protected")
async def protected_route(user: User = Depends(get_current_user)):
    # FastAPI automatically:
    # 1. Extracts token from Authorization header
    # 2. Validates token
    # 3. Gets user from database
    # 4. Injects user into function
    # 5. Returns 401 if any step fails
    return {"message": f"Hello {user.username}"}
```

**Dependency Chain:**
```
oauth2_scheme (extract token)
    ↓
get_current_user (validate token)
    ↓
get_current_active_user (check if active)
    ↓
Your endpoint function
```

## 🔒 Production Checklist

### Security

- [ ] Use environment variables for secrets
  ```python
  SECRET_KEY = os.getenv("SECRET_KEY")
  ```
- [ ] Generate strong SECRET_KEY
  ```powershell
  openssl rand -hex 32
  ```
- [ ] Use HTTPS only (SSL/TLS)
- [ ] Implement rate limiting
- [ ] Add CORS properly
- [ ] Implement refresh tokens
- [ ] Add token blacklist for logout
- [ ] Hash API keys in database
- [ ] Add audit logging
- [ ] Implement account lockout after failed attempts

### Database

- [ ] Replace fake database with real one (PostgreSQL, MongoDB)
- [ ] Use proper ORM (SQLAlchemy, Tortoise ORM)
- [ ] Index username/email fields
- [ ] Add database migrations (Alembic)

### Password Requirements

- [ ] Minimum 8 characters
- [ ] Require mixed case, numbers, special chars
- [ ] Check against common password lists
- [ ] Implement password reset flow
- [ ] Add password change endpoint

### User Management

- [ ] Email verification
- [ ] Password reset via email
- [ ] Two-factor authentication (2FA)
- [ ] Session management
- [ ] Remember me functionality
- [ ] Account deletion

### Monitoring

- [ ] Add logging (structlog, loguru)
- [ ] Monitor failed login attempts
- [ ] Set up alerts for suspicious activity
- [ ] Track API usage per user/key

### Performance

- [ ] Cache user data (Redis)
- [ ] Database connection pooling
- [ ] Async database queries
- [ ] Load testing

## 🌟 Key Takeaways

1. **OAuth2 + JWT** = Industry standard for API authentication
2. **Never store plain passwords** - Always use bcrypt or similar
3. **Dependencies** = FastAPI's powerful way to handle auth
4. **Multiple auth methods** = Flexibility for different use cases
5. **Token expiration** = Balance security and user experience

## 📖 Learn More

- [FastAPI Security Tutorial](https://fastapi.tiangolo.com/tutorial/security/)
- [OAuth2 RFC](https://tools.ietf.org/html/rfc6749)
- [JWT Introduction](https://jwt.io/introduction)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

## 🤝 Contributing

This is an educational example. Feel free to:
- Add more authentication methods
- Implement RBAC (Role-Based Access Control)
- Add database integration
- Improve error handling
- Add comprehensive tests

## 📝 License

MIT License - Free to use for learning and projects.

---

**Happy Coding! 🚀**
