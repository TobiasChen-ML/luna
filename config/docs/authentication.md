# 登录认证模块技术文档

## 概述

Roxy 采用统一 App JWT 的认证架构，支持多种登录方式，前端统一使用 App JWT 进行 API 鉴权。

---

## 登录方式

### 1. Firebase 邮箱密码登录

```
用户输入邮箱密码 → Firebase SDK 登录 → 获取 Firebase ID Token
→ 调用 /api/auth/verify-token → 后端验证 ID Token → 返回 App JWT + Refresh Token
→ 前端存储 Token → 后续请求使用 App JWT
```

**端点**: `POST /api/auth/verify-token`

**请求体**:
```json
{
  "token": "firebase_id_token"
}
```

**响应**:
```json
{
  "success": true,
  "access_token": "app_jwt",
  "refresh_token": "refresh_jwt",
  "token_type": "bearer",
  "is_admin": false,
  "firebase_uid": "user_id"
}
```

### 2. Google OAuth 登录

```
用户点击 Google 登录 → Firebase signInWithPopup → 获取 Firebase ID Token
→ 同步用户到后端 /api/auth/register → 调用 /api/auth/verify-token 换取 App JWT
```

### 3. Telegram Mini App 登录

```
用户打开 Telegram Mini App → 获取 initData → 调用 /api/auth/telegram
→ 后端验证 HMAC-SHA256 签名 → 提取用户信息 → 签发 App JWT
```

**端点**: `POST /api/auth/telegram`

**请求体**:
```json
{
  "init_data": "query_id=AAHdF5e4&user=%7B%22id%22%3A123%7D&auth_date=1234567890&hash=abc123"
}
```

**响应**:
```json
{
  "success": true,
  "access_token": "app_jwt",
  "refresh_token": "refresh_jwt",
  "token_type": "bearer",
  "user": {
    "id": "telegram_123",
    "email": "123@telegram.roxy.ai",
    "display_name": "用户名",
    "telegram_id": "123",
    "telegram_username": "username"
  },
  "is_new_user": true
}
```

### 4. Admin 登录

```
管理员输入邮箱密码 → 调用 /admin/login → 验证邮箱密码 → 签发 App JWT
```

**端点**: `POST /admin/login`

---

## Token 架构

### Token 类型

| Token | 过期时间 | 用途 |
|-------|---------|------|
| App JWT (Access Token) | 60 分钟 | API 请求鉴权 |
| Refresh Token | 30 天 | 刷新 Access Token |
| Firebase ID Token | 1 小时 | 仅用于换取 App JWT（过渡期） |

### Token 存储

前端使用 `localStorage` 存储：
- `roxy_access_token` - Access Token
- `roxy_refresh_token` - Refresh Token

**文件**: `frontend/src/lib/tokenStorage.ts`

### Token 刷新

```
API 请求返回 401 → 检查 Refresh Token 是否有效
→ 有效：调用 /api/auth/refresh 获取新 Token → 重试原请求
→ 无效：清除 Token → 跳转登录页
```

**端点**: `POST /api/auth/refresh`

**请求体**:
```json
{
  "refresh_token": "refresh_jwt"
}
```

**响应**:
```json
{
  "success": true,
  "access_token": "new_app_jwt",
  "refresh_token": "new_refresh_jwt",
  "token_type": "bearer"
}
```

---

## 鉴权流程

### 后端验证逻辑

**文件**: `backend/app/core/dependencies.py`

```
请求 → Authorization Header → 提取 Bearer Token
                              ↓
              ┌───────────────┴───────────────┐
              ↓                               ↓
        验证 App JWT                    App JWT 无效
              ↓                               ↓
        成功 → 返回用户信息              尝试验证 Firebase ID Token
                                              ↓
                                        成功 → 返回用户信息
                                        失败 → 401 Unauthorized
```

**过渡期策略**: 同时支持 App JWT 和 Firebase Token，便于平滑迁移。

### 前端请求拦截器

**文件**: `frontend/src/services/api.ts`

```
请求发送前：
1. 检查 localStorage 中的 App JWT
2. Token 有效 → 添加 Authorization Header
3. Token 过期但有 Refresh Token → 尝试刷新
4. 无有效 Token → 检查 Firebase 用户 → 使用 Firebase ID Token（过渡）
5. 都无效 → 无 Authorization Header

响应处理：
1. 401 响应 → 尝试 Refresh Token
2. Refresh 失败 → 清除 Token → 跳转登录
3. Telegram Mini App 场景 → 不跳转（等待自动重登）
```

---

## 配置项

### 后端环境变量

```env
# JWT 配置
JWT_SECRET_KEY=your_secret_key_at_least_32_chars

# Telegram Bot Token（用于验证 Mini App 签名）
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# Firebase 配置
FIREBASE_PROJECT_ID=your_firebase_project_id
FIREBASE_CREDENTIALS_PATH=./config/firebase-credentials.json

# Admin 配置
ADMIN_PASSWORD=your_admin_password
ADMIN_EMAILS=["admin@roxy.ai", "admin2@roxy.ai"]
```

### Token 过期配置

**文件**: `backend/app/core/config.py`

```python
jwt_expire_minutes: int = 60      # Access Token 过期时间（分钟）
```

Refresh Token 过期时间硬编码在 `backend/app/services/auth_service.py`：

```python
expire = datetime.utcnow() + timedelta(days=30)
```

---

## 移动端 / Telegram Mini App 特殊处理

### 自动登录流程

```
App 启动 → 检测 Telegram Mini App 环境
→ 存在 initData → 调用 /api/auth/telegram 自动登录
→ 成功 → 恢复会话
→ 失败 → 检查 localStorage 中的 App JWT → 尝试恢复会话
```

### 401 响应处理差异

| 场景 | 401 处理 |
|------|---------|
| Web | 清除 Token → 跳转 /login |
| Telegram Mini App | 不跳转 → 等待 AuthContext 自动重登 |

---

## 关键文件清单

### 后端

| 文件 | 说明 |
|------|------|
| `app/routers/auth.py` | 认证端点（verify-token, refresh） |
| `app/routers/integration.py` | Telegram 认证端点 |
| `app/services/auth_service.py` | JWT 签发与验证 |
| `app/core/dependencies.py` | 鉴权依赖 |
| `app/core/config.py` | 配置项 |
| `app/services/firebase_service.py` | Firebase Token 验证 |

### 前端

| 文件 | 说明 |
|------|------|
| `src/lib/tokenStorage.ts` | Token 存储工具 |
| `src/services/api.ts` | API 拦截器（Token 注入、Refresh） |
| `src/services/authService.ts` | 认证服务（登录、换 Token） |
| `src/contexts/AuthContext.tsx` | 认证状态管理 |
| `src/config/firebase.ts` | Firebase 初始化 |

---

## 安全注意事项

1. **JWT Secret**: 生产环境必须配置至少 32 字符的随机密钥
2. **HTTPS**: 生产环境必须使用 HTTPS
3. **Token 存储**: 使用 localStorage（可考虑迁移到 HttpOnly Cookie）
4. **Refresh Token 滚动刷新**: 每次刷新生成新的 Refresh Token
5. **Telegram 签名验证**: 严格验证 HMAC-SHA256 签名，防止伪造请求

---

## 扩展阅读

- Firebase Authentication: https://firebase.google.com/docs/auth
- Telegram Mini Apps: https://core.telegram.org/bots/webapps
- JWT Best Practices: https://datatracker.ietf.org/doc/html/rfc8725
