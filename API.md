# Coding Plan Quota Query API

FastAPI server for querying Google Cloud Code AI model quotas.

## Base URL

```
http://127.0.0.1:8000
```

> **Note**: Port is configurable via `PORT` environment variable in `.env` file.

## Running the Server

```bash
# Using uv (recommended)
uv run python main.py

# Using uvicorn directly
uv run uvicorn src.api:app --reload

# Custom host/port
uv run uvicorn src.api:app --host 0.0.0.0 --port 8080
```

## Configuration

All configuration is done via environment variables in a `.env` file:

```bash
# Copy the example file
cp .env.example .env
```

| Variable | Description | Default |
|----------|-------------|---------|
| `CLIENT_ID` | Google OAuth Client ID | (required) |
| `CLIENT_SECRET` | Google OAuth Client Secret | (required) |
| `ACCOUNT_FILE` | Path to account JSON file | `antigravity.json` |
| `PORT` | Server port | `8000` |
| `USER_AGENT` | HTTP User-Agent header | `antigravity/1.13.3 Darwin/arm64` |
| `ZAI_ANTHROPIC_BASE_URL` | Z.ai/ZHIPU API base URL | `https://api.z.ai/api/anthropic` |
| `ZAI_ANTHROPIC_AUTH_TOKEN` | Z.ai/ZHIPU authentication token | (required) |

---

## Endpoints

### 1. List Available Endpoints

Get a list of all available quota API endpoints.

```http
GET /quota
GET /quota/usage
```

> **Note**: `/quota/usage` is an alias for `/quota`.

**Response:**

```json
{
  "message": "Welcome to the Coding Plan Quota Query API",
  "endpoints": {
    "/quota": "This endpoint - lists all available endpoints",
    "/quota/overview": "Quick summary (e.g., 'Pro 95% | Flash 90% | Claude 80%')",
    "/quota/status": "Terminal status with nerdfont icons and colors",
    "/quota/status-zai": "GLM quota status with nerdfont icon and colors (e.g., 'Z 99%')",
    "/quota/all": "All models with percentage and relative reset time",
    "/quota/pro": "Gemini 3 Pro models (high, image, low)",
    "/quota/flash": "Gemini 3 Flash model",
    "/quota/claude": "Claude 4.5 models (opus, sonnet, thinking)",
    "/quota/glm": "GLM (Z.ai/ZHIPU) quota usage and limits"
  }
}
```

**Example:**

```bash
curl http://127.0.0.1:8000/quota
```

---

### 2. Get Quota Overview

Get a quick summary of quota percentages.

```http
GET /quota/overview
```

**Response:**

```json
{
  "overview": "Pro 100% | Flash 100% | Claude 81%"
}
```

**Example:**

```bash
curl http://127.0.0.1:8000/quota/overview
```

---

### 2b. Get Quota Status (Terminal)

Get a terminal-friendly status with nerdfont icons and ANSI colors.

```http
GET /quota/status
```

**Response:**

```json
{
  "overview": "\u001b[32mG\u001b[0m | F \u001b[33m45%\u001b[0m 2h18m | 󰛄 \u001b[31m5%\u001b[0m 1h30m"
}
```

**Features:**
- **Nerdfont icons**: (Claude)
- **Color-coded output**:
  - 100%: Green colored icon only (no percentage shown)
  - 50-99%: Icon + green percentage + reset time
  - 20-49%: Icon + yellow percentage + reset time
  - 1-19%: Icon + red percentage + reset time
  - 0%: Red colored icon only (no percentage shown)
- **Compact time format**: `2h18m` (no space, omits zero values)

**Example:**

```bash
# Display with colors in terminal
curl -s http://127.0.0.1:8000/quota/status | jq -r '.overview' | xargs -0 printf "%b\n"
```

---

### 2c. Get GLM Quota Status (Terminal)

Get a terminal-friendly GLM quota status with nerdfont icon and ANSI colors.

```http
GET /quota/status-zai
```

> **Note**: This endpoint requires `ZAI_ANTHROPIC_BASE_URL` and `ZAI_ANTHROPIC_AUTH_TOKEN` environment variables to be set.

**Response:**

```json
{
  "overview": "Z \u001b[32m99%\u001b[0m"
}
```

**Features:**
- **Nerdfont icon**: Z (Z.ai/ZHIPU)
- **Color-coded output**:
  - 100%: Green colored icon only (no percentage shown)
  - 50-99%: Icon + green percentage
  - 20-49%: Icon + yellow percentage
  - 1-19%: Icon + red percentage
  - 0%: Red colored icon only (no percentage shown)

**Example:**

```bash
# Display with colors in terminal
curl -s http://127.0.0.1:8000/quota/status-zai | jq -r '.overview' | xargs -0 printf "%b\n"
```

---

### 3. Get All Models

Get quota information for all Gemini and Claude models.

```http
GET /quota/all
```

**Response:**

```json
{
  "quota": {
    "models": [
      {
        "name": "claude-opus-4-5-thinking",
        "percentage": 81,
        "reset_time": "2025-12-26T07:15:53Z",
        "reset_time_relative": "2h 31m"
      },
      {
        "name": "claude-sonnet-4-5",
        "percentage": 81,
        "reset_time": "2025-12-26T07:15:53Z",
        "reset_time_relative": "2h 31m"
      },
      {
        "name": "claude-sonnet-4-5-thinking",
        "percentage": 81,
        "reset_time": "2025-12-26T07:15:53Z",
        "reset_time_relative": "2h 31m"
      },
      {
        "name": "gemini-2.5-flash",
        "percentage": 99,
        "reset_time": "2025-12-26T09:27:46Z",
        "reset_time_relative": "4h 43m"
      },
      {
        "name": "gemini-2.5-flash-lite",
        "percentage": 99,
        "reset_time": "2025-12-26T09:39:31Z",
        "reset_time_relative": "4h 54m"
      },
      {
        "name": "gemini-2.5-flash-thinking",
        "percentage": 99,
        "reset_time": "2025-12-26T09:27:46Z",
        "reset_time_relative": "4h 43m"
      },
      {
        "name": "gemini-2.5-pro",
        "percentage": 100,
        "reset_time": "2025-12-26T09:44:43Z",
        "reset_time_relative": "4h 59m"
      },
      {
        "name": "gemini-3-flash",
        "percentage": 100,
        "reset_time": "2025-12-26T09:44:43Z",
        "reset_time_relative": "4h 59m"
      },
      {
        "name": "gemini-3-pro-high",
        "percentage": 100,
        "reset_time": "2025-12-26T09:44:43Z",
        "reset_time_relative": "4h 59m"
      },
      {
        "name": "gemini-3-pro-image",
        "percentage": 100,
        "reset_time": "2025-12-26T09:44:43Z",
        "reset_time_relative": "4h 59m"
      },
      {
        "name": "gemini-3-pro-low",
        "percentage": 100,
        "reset_time": "2025-12-26T09:44:43Z",
        "reset_time_relative": "4h 59m"
      }
    ],
    "last_updated": 1766724284,
    "is_forbidden": false
  }
}
```

**Example:**

```bash
curl -s http://127.0.0.1:8000/quota/all | jq '.quota.models[].name'
```

---

### 4. Get Gemini 3 Pro Models

Get quota for Gemini 3 Pro variants (high, image, low).

```http
GET /quota/pro
```

**Response:**

```json
{
  "quota": {
    "models": [
      {
        "name": "gemini-3-pro-high",
        "percentage": 100,
        "reset_time": "2025-12-26T09:44:43Z",
        "reset_time_relative": "4h 59m"
      },
      {
        "name": "gemini-3-pro-image",
        "percentage": 100,
        "reset_time": "2025-12-26T09:44:43Z",
        "reset_time_relative": "4h 59m"
      },
      {
        "name": "gemini-3-pro-low",
        "percentage": 100,
        "reset_time": "2025-12-26T09:44:43Z",
        "reset_time_relative": "4h 59m"
      }
    ],
    "last_updated": 1766724285,
    "is_forbidden": false
  }
}
```

**Example:**

```bash
curl -s http://127.0.0.1:8000/quota/pro | jq '.quota.models[] | {name, percentage}'
```

---

### 5. Get Gemini 3 Flash Model

Get quota for Gemini 3 Flash model.

```http
GET /quota/flash
```

**Response:**

```json
{
  "quota": {
    "models": [
      {
        "name": "gemini-3-flash",
        "percentage": 100,
        "reset_time": "2025-12-26T09:44:43Z",
        "reset_time_relative": "4h 59m"
      }
    ],
    "last_updated": 1766724286,
    "is_forbidden": false
  }
}
```

**Example:**

```bash
curl -s http://127.0.0.1:8000/quota/flash | jq '.quota.models[0]'
```

---

### 6. Get Claude 4.5 Models

Get quota for Claude 4.5 models.

```http
GET /quota/claude
```

**Response:**

```json
{
  "quota": {
    "models": [
      {
        "name": "claude-opus-4-5-thinking",
        "percentage": 81,
        "reset_time": "2025-12-26T07:15:53Z",
        "reset_time_relative": "2h 31m"
      },
      {
        "name": "claude-sonnet-4-5",
        "percentage": 81,
        "reset_time": "2025-12-26T07:15:53Z",
        "reset_time_relative": "2h 31m"
      },
      {
        "name": "claude-sonnet-4-5-thinking",
        "percentage": 81,
        "reset_time": "2025-12-26T07:15:53Z",
        "reset_time_relative": "2h 31m"
      }
    ],
    "last_updated": 1766724287,
    "is_forbidden": false
  }
}
```

**Example:**

```bash
curl -s http://127.0.0.1:8000/quota/claude | jq '.quota.models[] | select(.percentage < 100)'
```

---

### 7. Get GLM Quota (Z.ai/ZHIPU)

Get quota for GLM coding plan (Z.ai or ZHIPU platforms).

```http
GET /quota/glm
```

> **Note**: This endpoint requires `ZAI_ANTHROPIC_BASE_URL` and `ZAI_ANTHROPIC_AUTH_TOKEN` environment variables to be set.

**Required Environment Variables:**

```bash
export ZAI_ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic"
# or
export ZAI_ANTHROPIC_BASE_URL="https://open.bigmodel.cn/api/anthropic"

export ZAI_ANTHROPIC_AUTH_TOKEN="your-zai-coding-plan-token-here"
```

> **Note**: ZAI_ prefixed variables are automatically mapped to ANTHROPIC_ variables internally.

**Response:**

```json
{
  "quota": {
    "models": [
      {
        "name": "glm",
        "percentage": 99
      },
      {
        "name": "glm-coding-plan-mcp-monthly",
        "percentage": 100
      },
      {
        "name": "glm-coding-plan-search-prime",
        "percentage": 100
      },
      {
        "name": "glm-coding-plan-web-reader",
        "percentage": 100
      }
    ],
    "last_updated": 1766825445,
    "is_forbidden": false
  }
}
```

**Model Names:**
- `glm` - Token quota (5 hour window)
- `glm-coding-plan-mcp-monthly` - Overall MCP usage quota (1 month window)
- `glm-coding-plan-search-prime` - Search Prime MCP tool usage
- `glm-coding-plan-web-reader` - Web Reader MCP tool usage

**Example:**

```bash
curl -s http://127.0.0.1:8000/quota/glm | jq '.quota.models[] | {name, percentage}'
```

---

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Model identifier |
| `percentage` | integer | Remaining quota percentage (0-100) |
| `reset_time` | string | ISO 8601 timestamp when quota resets |
| `reset_time_relative` | string | Human-readable time until reset (e.g., "4h 35m") |
| `last_updated` | integer | Unix timestamp of when quota was fetched |
| `is_forbidden` | boolean | Whether the account is forbidden (403 error) |

---

## Interactive API Docs

When the server is running, visit:

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

---

## Common Queries

### Get quick overview
```bash
curl -s http://127.0.0.1:8000/quota/overview | jq -r '.overview'
```

### Get low quota models (< 20%)
```bash
curl -s http://127.0.0.1:8000/quota/all | jq '.quota.models[] | select(.percentage < 20)'
```

### Get models expiring soon (< 1 hour)
```bash
curl -s http://127.0.0.1:8000/quota/all | jq '.quota.models[] | select(.reset_time_relative | contains("0h"))'
```

### Get percentage for specific model
```bash
curl -s http://127.0.0.1:8000/quota/all | jq '.quota.models[] | select(.name == "gemini-3-pro-high") | .percentage'
```

### Get all model names
```bash
curl -s http://127.0.0.1:8000/quota/all | jq -r '.quota.models[].name'
```
