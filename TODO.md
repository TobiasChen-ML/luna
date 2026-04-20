# Roxy 项目 TODO 清单

> 生成日期: 2026-04-16  
> 依据: `config/docs/` 文档 + 代码现状核查  
> 格式: 模块 → 功能 → 是否完成 → 是否有测试 → 缺失/待办

---

## 符号说明

| 符号 | 含义 |
|------|------|
| ✅ | 已完成 |
| ⚠️ | 部分完成 |
| ❌ | 未完成 |
| 🧪 | 有测试 |
| 🔴 | 无测试 |
| 🟡 | 测试不完整 |

---

## 一、认证模块 (Authentication)

| 功能 | 完成 | 测试 | 缺失 / 待办 |
|------|------|------|-------------|
| Firebase 邮箱密码登录 (`POST /api/auth/verify-token`) | ✅ | 🧪 `tests/test_auth.py` | — |
| Google OAuth 登录 (`signInWithPopup`) | ✅ | 🔴 | 端到端已验证可用；已修复 LoginPage hooks 顺序错误 + `grant_signup_bonus` SQLAlchemy session 脱离 bug；缺前端单元测试 |
| Telegram Mini App 登录 (`POST /api/auth/telegram`) | ✅ | 🧪 `tests/test_integration.py` | — |
| Admin 登录 (`POST /admin/login`) | ✅ | 🧪 `tests/test_admin.py::TestAdminLogin` | 7 个场景全覆盖：成功、JWT is_admin、密码错误、非管理员邮箱、缺字段、密码未配置；全文件 50/50 通过 |
| App JWT 签发与验证 | ✅ | 🧪 | — |
| Refresh Token 滚动刷新 (`POST /api/auth/refresh`) | ✅ | 🟡 | 并发刷新竞态场景未测试 |
| 前端 Token 存储 (`lib/tokenStorage.ts`) | ✅ | 🔴 | 缺 Vitest 单元测试 |
| 前端请求拦截器 / 401 自动重试 (`services/api.ts`) | ✅ | 🔴 | 缺前端集成测试 |
| Telegram Mini App 401 不跳转特殊处理 | ✅ | 🔴 | 缺前端场景测试 |
| `AuthContext.tsx` 状态管理 | ✅ | 🔴 | 缺 React Testing Library 测试 |
| 生产环境 JWT Secret ≥ 32 字符强校验 | ✅ | 🧪 | — |
| **Token 存储迁移至 HttpOnly Cookie** | ❌ | 🔴 | 文档标注"可考虑"，尚未实现；localStorage 存在 XSS 风险 |

---

## 二、角色创建模块 (Character Creation)

| 功能 | 完成 | 测试 | 缺失 / 待办 |
|------|------|------|-------------|
| 手动创建角色 (`POST /admin/api/characters`) | ✅ | 🧪 `tests/test_character.py` | — |
| 批量 AI 生成 (`POST /admin/api/characters/batch-generate`) | ✅ | 🧪 `tests/test_character_factory.py` | — |
| 模板变体生成 (`POST /admin/api/characters/from-template`) | ✅ | 🧪 | `tests/test_character_factory_concurrent.py` 14 tests: 并发、部分失败、错误处理 (已修复 400/422 响应) |
| 预设模板定义 (8 个模板) | ✅ | 🧪 `tests/test_character_templates.py` | — |
| 图片生成 (Novita/FAL) + R2 上传 | ✅ | 🧪 | FAL provider 路径已覆盖 (`tests/test_fal_provider.py`, `tests/test_media_service.py`) |
| SEO Slug 生成与冲突处理 | ✅ | 🧪 `tests/test_seo_slug.py` | — |
| SEO 内容生成 (`meta_title`, `meta_description`) | ✅ | 🧪 `tests/test_seo_slug.py` | — |
| 前台角色列表 / 发现页 (`GET /api/characters/discover`) | ✅ | 🧪 | — |
| 前台 SEO 详情页 (`GET /api/characters/by-slug/{slug}`) | ✅ | 🟡 | — |
| 管理后台角色列表页 (`CharactersTab.tsx`) | ✅ | 🟡 | Playwright E2E 框架已配置，测试登录端点已创建 (`POST /api/auth/test-login`)，需重启后端运行测试 |
| 管理后台角色创建页 (`CharacterCreatePage.tsx`) | ✅ | 🟡 | Playwright E2E 框架已配置 (`frontend/e2e/admin/character-create.spec.ts`) |
| 管理后台角色编辑页 (`CharacterEditPage.tsx`) | ✅ | 🟡 | Playwright E2E 框架已配置 (`frontend/e2e/admin/character-edit.spec.ts`) |
| 图片重新生成 (`POST /admin/api/characters/{id}/regenerate-images`) | ✅ | 🧪 `tests/test_character_factory.py::TestCharacterFactoryRegenerateImages` | 4 tests: 角色不存在、成功、部分图片、空图片 |
| 批量删除 (`POST /admin/api/characters/batch-delete`) | ✅ | 🧪 `tests/test_admin.py`, `tests/test_character_service.py::TestCharacterServiceBatchDelete` | 空 ID、不存在 ID、多 ID 删除测试 |
| 角色 `view_count` / `chat_count` 增量更新 | ✅ | 🧪 `tests/test_character_service.py::TestCharacterServiceIncrementCounts` | 基本功能 + 20 并发请求测试 |
| **用户自建角色 (UGC) 审核流程** | ✅ | 🧪 `tests/test_character_review.py` | 完整实现：`review_status` 字段 + 审核 API + 前端状态显示；13 tests |
| **角色克隆 / 分享功能** | ❌ | 🔴 | 文档未提及，业务有需求 |

---

## 三、积分系统 (Credit System)

| 功能 | 完成 | 测试 | 缺失 / 待办 |
|------|------|------|-------------|
| 用户注册赠送 10 积分 | ✅ | 🧪 `tests/test_billing.py` | — |
| 双桶积分 (monthly + purchased) | ✅ | 🧪 | — |
| 文字消息扣费 (0.1 积分 / 条) | ✅ | 🧪 | — |
| 语音生成扣费 (0.2 积分 / 条) | ✅ | 🧪 | — |
| 图片生成扣费 (2 积分 / 张) | ✅ | 🧪 | — |
| 视频生成扣费 (4 积分 / 条) | ✅ | 🧪 | — |
| Premium 用户文字消息免费 | ✅ | 🧪 | — |
| 积分包定义与价格 (6 个档位) | ✅ | 🧪 | — |
| 订阅计划 (1/3/12 个月) | ✅ | 🧪 | — |
| 管理后台积分配置 (`CreditsTab.tsx`) | ✅ | 🧪 | `tests/test_admin_credits.py` 18 tests |
| 用户积分余额查询 (`GET /api/billing/credits/balance`) | ✅ | 🧪 | — |
| 用户交易历史 (`GET /api/billing/credits/transactions`) | ✅ | 🧪 | — |
| 管理员手动调整积分 (`POST /api/admin/credits/adjust`) | ✅ | 🧪 | `tests/test_admin_credits.py::TestAdminAdjustCredits` |
| 每月自动赠积分 (APScheduler) | ✅ | 🧪 | 每日凌晨 2 点自动发放；`scheduler_service.py` |
| Stripe Webhook 处理 | ✅ | 🧪 | 支持 6 种事件：checkout.completed, invoice.paid, subscription.created/updated/deleted |
| 订阅到期自动降级 (APScheduler) | ✅ | 🧪 | 每 6 小时检查过期订阅并降级为 free |
| CCBill Webhook 业务逻辑 | ✅ | 🧪 | `billing.py:261-284` 调用 `credit_service.add_credits()` |
| USDT Webhook 业务逻辑 | ✅ | 🧪 | `billing.py:292-343` |
| Telegram Stars Webhook 业务逻辑 | ✅ | 🧪 | `billing.py:344-410` |
| Redis 积分余额缓存 | ✅ | 🧪 | `credit_service.py` 写穿透模式，TTL 1小时；`tests/test_credit_service.py::TestBalanceCache` 8 tests |
| 退款积分 (`credit_service.refund_credits`) | ✅ | 🧪 | 重复退款防护已测试 |

---

## 四、Prompt 构建系统 (Prompt System)

| 功能 | 完成 | 测试 | 缺失 / 待办 |
|------|------|------|-------------|
| 多段 Prompt 模板 (8 个默认模板) | ✅ | 🧪 `tests/test_prompt_security.py` | — |
| Jinja2 模板渲染 (`PromptTemplateService`) | ✅ | 🧪 | 已使用 `ImmutableSandboxedEnvironment` + 变量语法转义 |
| 启动自动初始化默认模板 | ✅ | 🔴 | — |
| `PromptBuilder.build_system_prompt()` | ✅ | 🔴 | — |
| `PromptBuilder.build_messages()` (含历史 20 条) | ✅ | 🔴 | — |
| 安全规则模板 (`safety_rules`, 最高优先级 1000) | ✅ | 🔴 | — |
| 关系状态模板注入 (`relationship_state`) | ✅ | 🔴 | — |
| 剧情上下文模板注入 (`plot_context`) | ✅ | 🔴 | — |
| 管理后台 Prompt 模板管理 (`PromptsTab.tsx`) | ✅ | 🔴 | — |
| 管理端模板渲染测试接口 (`POST /api/admin/prompts/{name}/test`) | ✅ | 🔴 | — |
| 内容安全检查 - 输入 (`ContentSafetyService.check_input`) | ✅ | 🧪 | 已支持中/英/法/德/西五语言关键词 |
| 内容安全检查 - 输出 | ✅ | 🧪 | — |
| **Prompt 注入攻击防护** | ✅ | 🧪 | 已实现 `PromptSanitizer`，检测注入模式并记录警告 |
| **多语言 Prompt 支持** | ❌ | 🔴 | 当前强制英文，国际化用户体验受限 |

---

## 五、剧本系统 (Script System)

| 功能 | 完成 | 测试 | 缺失 / 待办 |
|------|------|------|-------------|
| 剧本 CRUD (`scripts` 表 + 路由) | ✅ | 🧪 `tests/test_scripts.py` | — |
| 剧本节点 CRUD (`script_nodes` 表) | ✅ | 🧪 | — |
| 故事进度追踪 (`story_progress` 表) | ✅ | 🧪 `tests/test_story.py` | — |
| 四阶段状态机 (Start/Build/Climax/Resolve) | ✅ | 🧪 `tests/test_scripts.py::TestScriptStateTransition` | 阶段回退测试已补充 |
| 情感门槛检查 (`emotion_gates`) | ✅ | 🧪 | — |
| 关系阶段自动判定 (`STAGE_THRESHOLDS`) | ✅ | 🧪 `tests/test_services.py` | — |
| 关系属性 LLM 分析器 (`RelationshipAnalyzer`) | ✅ | 🧪 `tests/test_story_service.py::TestStoryServiceRobustness` | LLM JSON 容错测试已补充 |
| DAG 结构验证 (`/dag/validate`) | ✅ | 🧪 `tests/test_scripts.py::TestScriptDAGValidation` | 环检测 + 大图测试已补充 |
| 自然语言选项匹配 - 关键词级 | ✅ | 🧪 `tests/test_choice_matcher.py` | — |
| 自然语言选项匹配 - 语义相似度级 | ✅ | 🧪 | — |
| 自然语言选项匹配 - LLM 分类级 | ✅ | 🧪 | — |
| 多结局判定 (`good/neutral/bad/secret`) | ✅ | 🧪 `tests/test_story_service.py` | — |
| 结局奖励计算与上限 | ✅ | 🧪 `tests/test_story_service.py` | 最大奖励上限边界测试已补充 |
| 媒体触发器检查 (`/scripts/{id}/media/check`) | ✅ | 🧪 `tests/test_media_trigger.py` | — |
| 媒体触发器执行 (`/scripts/{id}/media/trigger`) | ✅ | 🧪 | — |
| 前端剧本选择组件 (`StorySelector.tsx`) | ✅ | 🔴 | 含 Replay 按钮 + 历史记录展开 |
| 前端选项组件 (`StoryChoices.tsx`) 含自由输入 | ✅ | 🔴 | — |
| 前端媒体触发按钮 (`MediaTriggerButton.tsx`) | ✅ | 🔴 | — |
| 前端结局弹窗 (`StoryCompletionModal.tsx`) | ✅ | 🔴 | — |
| 剧本编辑器页面 (`CreateScriptPage.tsx` / `EditScriptPage.tsx`) | ✅ | 🔴 | — |
| 管理后台剧本管理 (`StoriesTab.tsx`) | ✅ | 🔴 | 含审核按钮 + 状态筛选 |
| **可视化 DAG 节点编辑器** | ✅ | 🔴 | `DagEditor/` React Flow 实现：拖拽、连线、环检测、导出图片 |
| **剧本发布审核流程** | ✅ | 🧪 `tests/test_script_review.py` | draft→pending→published 流程 + 审核历史 |
| **剧本回放 / 复玩功能** | ✅ | 🧪 `tests/test_story_service.py::TestStoryReplayAndHistory` | 完整历史保留 + play_index 标记 |

---

## 六、视频生成模块 (Video Generation)

| 功能 | 完成 | 测试 | 缺失 / 待办 |
|------|------|------|-------------|
| Novita wan-i2v 图片转视频 | ✅ | 🧪 `tests/test_video_generation.py` | — |
| Novita wan-t2v 文字转视频 | ✅ | 🧪 `tests/test_video_generation.py` | Mock 测试通过；生产环境需确认 Novita API 开通 |
| 聊天输入"Shoot Video"按钮 | ✅ | 🔴 | 缺前端 E2E |
| 消息气泡"Animate"按钮 | ✅ | 🧪 `tests/test_video_generation.py` | Mock 测试 |
| 生成图页"Animate"按钮 | ✅ | 🔴 | — |
| 视频意图关键词检测 (高置信度) | ✅ | 🧪 `tests/test_intent_detector.py` | 英/法/德/西四语种完整覆盖 |
| 视频意图 LLM 验证 (中置信度) | ✅ | 🧪 `tests/test_video_generation.py` | Mock 测试 |
| VideoIntentHandler 拒绝消息生成 | ✅ | 🧪 `tests/test_video_generation.py` | 人格匹配、fallback 测试 |
| SSE 事件 `video_completed` | ✅ | 🧪 `tests/test_video_generation.py` | Callback 测试 |
| 视频生成速率限制 (5次/60s) | ✅ | 🔴 | — |
| 视频积分扣费 (4 积分) | ✅ | 🧪 `tests/test_video_generation.py` | 扣费/退款测试 |
| Novita Callback 处理 | ✅ | 🧪 `tests/test_video_generation.py` | 成功/失败回调 |
| 图片视频媒体库页面 (`GalleryPage.tsx`) | ✅ | 🔴 | — |
| **视频生成预计时间展示** | ❌ | 🔴 | 文档 Future Work，前端仅有占位符 |
| **视频编辑 (剪辑/合并/特效)** | ❌ | 🔴 | 文档 Future Work |
| **多 LoRA 叠加** | ❌ | 🔴 | 文档 Future Work |

---

## 七、语音系统 (Voice System)

| 功能 | 完成 | 测试 | 缺失 / 待办 |
|------|------|------|-------------|
| 角色 Voice ID 配置 (`CharacterEditPage.tsx`) | ✅ | 🔴 | — |
| Audio Intent 检测 (`detect_intent`) | ✅ | 🟡 `tests/test_llm.py` | 中文语音请求场景覆盖不足 |
| ElevenLabs TTS 生成 (`VoiceService`) | ✅ | 🧪 `tests/test_voice_tts_cache.py` | — |
| DashScope TTS 备用提供商 | ✅ | 🔴 | 缺集成测试 |
| TTS 文本清理 (移除 `*action*` / `[emotion]`) | ✅ | 🧪 `tests/test_voice_tts_cache.py` | — |
| SSE 事件: `voice_note_pending/ready/failed` | ✅ | 🔴 | — |
| SSE 事件: `credit_update` (语音后更新余额) | ✅ | 🔴 | — |
| 语音条播放组件 (`VoiceNotePlayer.tsx`) | ✅ | 🔴 | — |
| 单例播放控制 (同时只能一条) | ✅ | 🔴 | — |
| 积分不足弹窗 (`InsufficientCreditsModal.tsx`) | ✅ | 🔴 | — |
| LiveKit Token 生成接口 (`/voice/generate_token`) | ✅ | 🧪 `tests/test_voice_tts_cache.py` | 支持 livekit-server-sdk JWT token |
| 实时语音通话弹窗 (`RealtimeCallModal.tsx`) | ✅ | 🔴 | — |
| 语音通话按分钟扣费 (3 积分/分钟) | ✅ | 🧪 `tests/test_voice_call_service.py` | 已实现 `VoiceCallService` 计时扣费 |
| 语音通话结束 Webhook / 计费回调 | ✅ | 🔴 | `POST /api/voice/webhook/livekit` 处理 `room_finished` |
| TTS 音频缓存 (相同文本复用) | ✅ | 🧪 `tests/test_voice_tts_cache.py` | Redis 缓存 7 天，SHA256 key |

---

## 八、记忆系统 (Memory System)

| 功能 | 完成 | 测试 | 缺失 / 待办 |
|------|------|------|-------------|
| 三层记忆 (working / episodic / semantic) | ✅ | 🧪 `tests/test_memory.py` | — |
| 情节记忆摘要 (Redis + DB 混合) | ✅ | 🧪 | Redis 失效回退已测试 |
| 语义事实提取 | ✅ | 🧪 | — |
| LLM 自动提取记忆 | ✅ | 🧪 | — |
| 记忆注入 Prompt (`memory_context` 模板) | ✅ | 🔴 | — |
| 用户主动删除记忆 (`/memory` 端点) | ✅ | 🧪 | — |
| 记忆管理页面 (`MemoryManagementPage.tsx`) | ✅ | 🔴 | — |
| **记忆重要性衰减 (14天半衰期)** | ✅ | 🧪 | 已实现 `calculate_decayed_importance()`；衰减公式：`decayed = importance * exp(-0.05 * days)` |
| **跨角色记忆共享 (用户确认模式)** | ✅ | 🧪 | 新增 `global_memories` 表；用户需确认才能推广到全局；前端支持管理 UI |
| **Redis 失效回退测试** | ✅ | 🧪 | `test_memory.py::TestRedisFallback` 覆盖 |
| **全局记忆建议功能** | ✅ | 🧪 | 系统自动检测可共享内容并建议用户确认 |
| **记忆批量衰减更新** | ✅ | 🧪 | `update_all_decayed_importance()` 可定时调用 |

---

## 九、聊天与 SSE 流 (Chat & Streaming)

| 功能 | 完成 | 测试 | 缺失 / 待办 |
|------|------|------|-------------|
| SSE 流式对话 (`POST /api/chat/stream`) | ✅ | 🧪 `tests/test_chat.py` | — |
| 会话创建与管理 (`chat_sessions` 表) | ✅ | 🧪 | — |
| 消息持久化 (Redis 缓存 + DB 存储) | ✅ | 🧪 | Redis 失效告警 + DB 回退已在 `test_chat_history.py` 测试 |
| 图片意图检测 (`image_intent_handler.py`) | ✅ | 🧪 | — |
| 视频意图检测 (`video_intent_handler.py`) | ✅ | 🧪 | — |
| 关系属性异步更新 (流结束后) | ✅ | 🧪 | LLM 分析失败日志告警已补全 (`logger.warning` + 上下文) |
| 游客聊天模式 (`GuestChatPage.tsx`) | ✅ | 🔴 | — |
| **Redis 缓存失效告警与降级** | ✅ | 🧪 | `_redis_failure_count` 计数器 + 退化状态 + `redis_health_check()` |
| **多角色群聊 (并行生成模式)** | ✅ | 🧪 | `group_chat_service.py` + 前端 `GroupChatPage.tsx`；SSE 携带 `speaker_id` |
| **消息撤回 / 编辑** | ❌ | 🔴 | — |
| **聊天历史导出** | ❌ | 🔴 | — |

---

## 十、支付与账单 (Billing & Payments)

| 功能 | 完成 | 测试 | 缺失 / 待办 |
|------|------|------|-------------|
| 账单页面 (`BillingPage.tsx`) | ✅ | 🔴 | — |
| 订阅页面 (`SubscriptionsPage.tsx`) | ✅ | 🔴 | — |
| 支付成功/取消页 (`billing/SuccessPage.tsx`, `CancelPage.tsx`) | ✅ | 🔴 | — |
| CCBill Webhook 接收与验签 | ✅ | 🔴 | — |
| USDT Webhook 接收与验签 | ✅ | 🔴 | — |
| Telegram Stars Webhook 接收与验签 | ✅ | 🔴 | — |
| **Stripe Webhook 接收与处理** | ✅ | 🧪 | `billing_service.py:177-205` 含 checkout/subscription/refund 事件 |
| **CCBill 付款成功后充值逻辑** | ✅ | 🧪 | `billing.py:267-279` 调用 `credit_service.add_credits()` |
| **USDT 付款成功后充值逻辑** | ✅ | 🧪 | `billing.py:325-337` |
| **Telegram Stars 付款成功后充值逻辑** | ✅ | 🧪 | `billing.py:382-393` |
| **退款处理流程** | ✅ | 🧪 | `billing_service.py:391-462` 扣减积分，防重复退款 |
| **订阅到期自动处理** | ✅ | 🔴 | `scheduler_service.py:17-45` 每 6 小时检查 |
| **月度积分自动发放** | ✅ | 🔴 | `scheduler_service.py:48-80` 每日检查 |

---

## 十一、管理后台 (Admin)

| 功能 | 完成 | 测试 | 缺失 / 待办 |
|------|------|------|-------------|
| Dashboard 总览 (`DashboardTab.tsx`) | ✅ | 🔴 | — |
| 用户管理 (`UsersTab.tsx`) | ✅ | 🔴 | — |
| 角色管理 (`CharactersTab.tsx`) | ✅ | 🔴 | — |
| 积分管理 (`CreditsTab.tsx`) | ✅ | 🔴 | — |
| Prompt 模板管理 (`PromptsTab.tsx`) | ✅ | 🔴 | — |
| 剧本管理 (`StoriesTab.tsx`) | ✅ | 🔴 | — |
| 语音管理 (`VoicesTab.tsx`) | ✅ | 🔴 | — |
| 任务队列监控 (`TasksTab.tsx`) | ✅ | 🔴 | — |
| 订单管理 (`OrdersTab.tsx`) | ✅ | 🔴 | — |
| API Key 管理 (`ApiKeysTab.tsx`) | ✅ | 🔴 | — |
| 模板管理 (`TemplatesTab.tsx`) | ✅ | 🔴 | — |
| Admin 权限校验 (`ADMIN_PASSWORD`) | ✅ | 🧪 `tests/test_admin.py` | — |
| **管理后台操作日志 (Audit Log)** | ✅ | 🧪 `tests/test_audit_service.py` | `AuditLogTab.tsx` + `audit_service.py` + API endpoints |
| **批量用户积分调整** | ✅ | 🧪 `frontend/e2e/admin/credits-tab.spec.ts` | `POST /api/admin/credits/batch-adjust` |
| 操作日志页面 (`AuditLogTab.tsx`) | ✅ | 🧪 `frontend/e2e/admin/audit-log-tab.spec.ts` | — |

---

## 十二、基础设施 / 运维 (Infrastructure)

| 功能 | 完成 | 测试 | 缺失 / 待办 |
|------|------|------|-------------|
| SQLite 开发数据库 | ✅ | 🧪 | — |
| PostgreSQL 生产数据库支持 | ✅ | 🔴 | 未在 CI 中测试 PostgreSQL 路径 |
| Redis 缓存层 | ✅ | 🟡 | Redis 断连降级测试缺失 |
| R2 云存储 (`StorageService`) | ✅ | 🔴 | 缺 mock 集成测试 |
| Docker Compose 本地开发 | ✅ | 🔴 | — |
| 速率限制中间件 | ✅ | 🔴 | — |
| Firebase 服务账号配置 | ✅ | 🔴 | — |
| 生产环境配置强校验 | ✅ | 🧪 | — |
| **PostgreSQL 迁移脚本 CI 验证** | ❌ | 🔴 | `app/migrations/` 只有 SQLite 迁移，PostgreSQL 迁移未在 CI 中验证 |
| **定时任务调度框架** | ✅ | 🔴 | `scheduler_service.py` APScheduler 已集成；订阅到期 + 月度积分 |
| **监控 / 告警 (Sentry / Prometheus)** | ❌ | 🔴 | 无错误追踪和指标监控 |
| **CI/CD Pipeline** | ✅ | 🔴 | `.github/workflows/ci.yml` 已创建：backend-test (pytest+cov) + frontend-test (lint+vitest+build) + docker-build |

---

## 汇总：优先级矩阵

### P0 — 阻断线上收入 (已修复 ✅)

| # | 问题 | 状态 |
|---|------|------|
| 1 | ~~所有支付 Webhook 仅接收不充值~~ | ✅ 已修复 - CCBill/USDT/Telegram Stars webhook 现调用 `credit_service.add_credits()` |
| 2 | ~~Stripe Webhook 端点缺失~~ | ✅ 已修复 - `billing_service.py` 完整实现 |

### P1 — 核心体验缺陷 (已修复 ✅)

| # | 问题 | 状态 |
|---|------|------|
| 3 | ~~月度积分无定时任务~~ | ✅ 已修复 - `scheduler_service.py` APScheduler |
| 4 | ~~订阅到期不自动降级~~ | ✅ 已修复 - 每 6 小时检查 |
| 5 | ~~Redis 积分余额缓存~~ | ✅ 已修复 - 写穿透模式，TTL 1小时 |

### P2 — 技术债 (下迭代规划)

| # | 问题 | 影响 |
|---|------|------|
| 6 | ~~Redis 积分余额缓存~~ | ✅ 已完成 - 写穿透 + 1小时 TTL |
| 7 | ~~Prompt 注入防护~~ | ✅ 已完成 - `PromptSanitizer` |
| 8 | ~~CI/CD Pipeline~~ | ✅ 已完成 - `.github/workflows/ci.yml` |
| 9 | 前端 E2E 测试 | Playwright 框架已配置，需扩展覆盖 |

### P3 — 功能扩展 (Backlog)

- ~~可视化 DAG 节点编辑器~~ ✅ 已完成 - `DagEditor/` React Flow
- 视频编辑功能
- ~~跨角色记忆共享~~ ✅ 已完成 - `global_memories` 表
- ~~多角色群聊~~ ✅ 已完成 - `group_chat_service.py`
- ~~剧本发布审核流程~~ ✅ 已完成 - `script_reviews` 表
- ~~剧本回放/复玩功能~~ ✅ 已完成 - 完整历史保留
- Token 迁移至 HttpOnly Cookie
- 多语言 Prompt 支持

---

*最后更新: 2026-04-16 (积分系统完善：Redis 缓存 + Webhook 充值逻辑 + 完整测试覆盖)*
