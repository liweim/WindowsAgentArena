# WindowsAgentArena Cognitive Tasks 检查与修复清单

检查范围：`src/win-arena-container/client/evaluation_examples_windows/examples/cognitive/` 下全部 **33** 个 JSON。

本轮处理原则：

- **Immersive Reader 不是 cognitive task 的硬性要求。** Cognitive 的核心是任务是否真实涉及记忆、注意、processing speed、信息处理、理解、规划、决策、步骤保持、external memory 或 simplified interaction。
- 老年人可以作为典型目标人群，但不能仅因为“用户年龄较大”或“任务步骤多”就归为 cognitive。
- **不改变任务语义。** `instruction` 可以做自然语言风格统一；凡是需要改变任务场景、目标、成功条件、信息需求或任务类别本身才能解决的问题，只给修改建议。
- 可以直接修复不改变任务目标的问题：README 规范冲突、evaluator 漏检、evaluator 确定性、固定日期、exact wording 检查范围等。

状态说明：

- ✅ **可保留**：当前任务适合作为 cognitive task；本轮发现的非语义问题已修或无阻塞问题。
- ⚠️ **可保留但仍建议优化**：cognitive 方向可接受，但仍存在任务设计边界、主观性或 evaluator 能力限制。
- ❌ **需要改任务**：当前场景本身不足以支撑 cognitive 分类；本轮没有直接改 task JSON 的任务目标。
- 🧪 **CAPTCHA slice**：作为 CAPTCHA stress-test 单独统计，不按普通 daily-life cognitive workflow 衡量。

---

## 本轮已直接修改

这些修改**没有改变用户要完成的任务目标**。

### 0. 全部 33 个 cognitive task：统一 instruction 风格

已将 `cognitive/` 下全部 33 个 JSON 的 `instruction` 统一为**简洁、直接的命令式表达**。改写原则：

- 直接描述 Agent 要完成的目标，不使用 `Could you...`、`Can you...`、`Please...`、`I need you to...` 等客套或问句式开场。
- 不写成操作手册；常规 UI 导航、菜单路径、点击顺序和窗口切换由 Agent 自己推理。
- 保留最终结果以及 Agent 无法安全推断的硬约束，例如指定应用、辅助功能、文件名、收件人、标题、日期、精确文本和 `do not send/restart`。
- 如果辅助功能本身由 evaluator 检查，例如 Immersive Reader，则 instruction 直接要求使用该功能，但不说明如何进入。
- `gt_steps` 面向标注/人工复现；需要复现指导的任务按一步一个动作书写，CAPTCHA 保持简短，`config` 继续负责初始环境准备。

示例：

```text
原：Could you install the Immersive Reader extension in Chrome for me?
现：Install the Immersive Reader extension in Chrome.
```

```text
原：Windows notifications disappear before I finish reading them. Please make them stay on screen for 5 minutes.
现：Set Windows notifications to stay on screen for 5 minutes.
```

这次只统一表达方式。对 Docker、Spotify、Elsa bottle、Wikipedia definition 等“任务本身需要重构”的条目，没有因为改 instruction 而改变任务目标；具体重构建议仍见后文。

### 0.1. `gt_steps`：统一复现规范

按最新标注口径，对适合保留或仅需小修的 cognitive task 统一了 `gt_steps`：

- 每一条只描述一个主要动作；
- UI 路径和中间操作可以写在 `gt_steps` 中，因为它面向标注/复现人员，而不是 Agent；
- 已知唯一标准答案时直接写出答案、日期、标题、文本、商品或设置值；
- evaluator 允许多个有效答案时描述选择标准，不人为制造唯一答案；
- `config` 中的环境准备不重复写进 `gt_steps`。

本轮有两个明确例外：

1. **7 个 CAPTCHA task 不展开步骤。** CAPTCHA 本身交互简单且 UI 已经说明要求，保留最初项目里的简短 `gt_steps`，不写固定 seed 的答案或逐次点击说明。
2. **4 个需要改任务的 task 不改 `gt_steps`。** `access-docker_install.json`、`access-spotify_install.json`、`consumption-shopping_title_elsa_bottle.json`、`information-wikipedia_accessibility_definition.json` 的任务定义尚需重构，因此保留最初项目里的步骤，等任务目标确定后再一起重写。

除上述 11 个任务外，其余 **22 个 task** 的 `gt_steps` 已按“一步一个动作、标注人员可复现、已知标准答案直接给出”的规则统一。

### 1. README：Cognitive 定义与实际任务口径对齐

文件：`paper/README.md`

已修改：

- 不再把 Microsoft Edge Immersive Reader 描述为所有 Windows cognitive task 的事实硬门槛。
- Cognitive 工具表已扩展为 Immersive Reader、notes/checklists、reminders、calendars/timers、notification timing、text sizing 等示例，而不是单一 Reader。
- Task Requirements 不再要求每个任务都必须有一个显式 assistive tool；改为要求明确的 accessibility need / support strategy，并只在特定工具确实属于任务要求时明确指定。
- 文本输出要求改成“可确定评估的 destination”，允许 file、Sticky Notes、email draft、calendar event 等已有任务形态。
- 明确 cognitive task 还可以使用 reminders、notes、checklists、calendars、timers、reduced time pressure 和 structured multi-step workflows 等认知支持方式。
- 明确判定依据是 meaningful memory / attention / processing / planning / decision-making / step-tracking load，而不是年龄或步骤数本身。

### 2. README：CAPTCHA category 命名冲突

原 README 写 category label 为 `Captcha`，但现有 Windows task 数据（不仅 cognitive，motor/visual/hearing 也一样）统一使用小写：

```text
captcha-*.json
"category": "captcha"
```

本轮**没有批量改 task id/filename**，以免破坏现有引用；而是把 README 统一到仓库实际约定：

```text
captcha
```

同时将 Naming Rules 和示例统一成 lowercase category prefix。

因此之前“7 个 cognitive CAPTCHA task 命名不符合 README”的问题已通过**修规范文档**解决，不需要修改 7 个任务。

### 3. Thunderbird Calendar evaluator：新增绝对日期支持

文件：

`src/win-arena-container/client/desktop_env/evaluators/metrics/thunderbird.py`

`check_thunderbird_calendar_event` 新增向后兼容规则：

```json
"date": "YYYY-MM-DD"
```

逻辑：

- 有 `date` 时按绝对日期检查。
- 没有 `date` 时继续使用原来的 `days_from_today`。
- 原有相对日期 task 不受影响。
- 非法绝对日期直接返回失败，不会 fallback 成错误日期。

已做隔离测试：

- absolute date 正确日期：PASS
- absolute date 错误日期：正确返回失败
- 非法 date：正确返回失败
- 原 `days_from_today` 行为：PASS

### 4. `management-prescription_refill_reminder.json`

原 evaluator：

```json
"days_from_today": 17
```

但任务要求固定日期 `2026-07-20`，只有 VM today 为 `2026-07-03` 时才成立。

已改为：

```json
"date": "2026-07-20"
```

任务语义未改变。

### 5. `management-sunscreen_ingredient_reminder.json`

原 evaluator：

```json
"days_from_today": 13
```

但任务根据出生日期和 6 个月规则得到固定目标 `2026-07-15`，只有 VM today 为 `2026-07-02` 时才成立。

已改为：

```json
"date": "2026-07-15"
```

任务语义未改变。

### 6. `communication-ftc_scam_text_reply.json`

Instruction 明确要求：

```text
use Microsoft Edge Immersive Reader
```

原 evaluator 只检查 Thunderbird draft。

已增加：

```json
"check_edge_immersive_reader_state"
```

并使用：

```json
"conj": "and"
```

现在 draft 内容和 Reader 状态都必须满足。

### 7. `health-ap_doctor_appointment_questions.json`

原问题：

- instruction 明确要求 Immersive Reader；evaluator 未检查。
- instruction 明确写 `Do not paraphrase`；原 body evaluator 只检查较短/概括性片段。

已修改：

- 增加 `check_edge_immersive_reader_state`，并与 Calendar evaluator 用 `and` 组合。
- 将 Calendar description 的 `body_points` 收紧为文章中的连续原文短语。
- 同步修正 `gt_steps`，使 ground truth 与 evaluator 一致。

没有改变用户-facing task goal。

### 8. `information-passport_renewal_checklist.json`

原 evaluator 接受过短替代项，例如：

```text
25 or older
at least eight weeks
```

这与 instruction 的 `Use the article wording rather than paraphrasing` 不完全一致。

已删除过短 alternative，只保留完整、连续的 source phrase。

### 9. `service-cfpb_automatic_payment_stop_answer.json`

原 evaluator 第二条允许只出现：

```text
bank or credit union
```

而 instruction 要求复制 original wording。

已收紧为必须包含完整：

```text
Call and write your bank or credit union
```

### 10. `service-cms_product_record.json`

原 instruction 要求填写 14 个字段，但 evaluator 只检查 5 个字段。

本轮在**不修改 instruction** 的情况下做了可安全完成的 evaluator 加强：

- evaluator 的读取命令现在只输出 Value 非空的行。
- 14 个要求字段全部必须在输出中出现，因此可以检查每一个 Value cell 均已填写。
- 对已有稳定 ground truth 的 5 个字段继续检查具体值：
  - Name
  - Type
  - SKU
  - Price
  - Quantity

仍有一个限制：其余字段目前只能确定“已填写”，不能完全判断“值是否正确”，因为部分字段（例如 Last Updated At）可能是动态值。具体后续建议见该任务条目。

---

## 全量任务清单（修复后）

| # | Task | 状态 | 本轮处理 | 剩余建议 |
|---:|---|---|---|---|
| 1 | `access-chrome_immersive_reader_extension.json` | ✅ | instruction 已统一；其余无需改 task/evaluator。 | `source` 若能固定到具体 Chrome Web Store listing 会更稳定，但不是当前阻塞问题。 |
| 2 | `access-docker_install.json` | ❌ | **instruction 已统一；未重构 task。** | 需要改任务或移出 cognitive；普通 Docker 安装的复杂度主要来自软件安装，不是 cognitive-support workload。见“需要改任务”章节。 |
| 3 | `access-edge_immersive_reader_setup.json` | ✅ | instruction 已统一；其余无需修改。 | 可作为 Access cognitive 模板。 |
| 4 | `access-spotify_install.json` | ❌ | **instruction 已统一；未重构 task。** | 需要改任务或移出 cognitive；单纯安装 Spotify 没有明确 memory/attention/planning support。 |
| 5 | `access-text_size_cognitive.json` | ✅ | instruction 已统一；其余无需修改。 | visual/cognitive overlap 可接受。 |
| 6 | `access-windows_notification_duration.json` | ✅ | instruction 已统一；其余无需修改。 | processing speed / attention support 明确。 |
| 7 | `captcha-audio_1.json` | 🧪 | instruction 已统一；未重构 task；README category label 已统一成 `captcha`。 | 作为 CAPTCHA slice 单独统计。 |
| 8 | `captcha-click_sequence_3.json` | 🧪 | instruction 已统一；未重构 task；CAPTCHA slice 规范同上。 | sequence / working-memory 压力可作为 CAPTCHA 内部分析维度。 |
| 9 | `captcha-count_chars_1.json` | 🧪 | instruction 已统一；未重构 task；CAPTCHA slice 规范同上。 | sustained attention stress-test。 |
| 10 | `captcha-distorted_text_2.json` | 🧪 | instruction 已统一；未重构 task；CAPTCHA slice 规范同上。 | 更偏视觉辨识，单独 CAPTCHA slice。 |
| 11 | `captcha-image_recognition_2.json` | 🧪 | instruction 已统一；未重构 task；CAPTCHA slice 规范同上。 | 更偏 visual verification，单独统计。 |
| 12 | `captcha-math_1.json` | 🧪 | instruction 已统一；未重构 task；CAPTCHA slice 规范同上。 | arithmetic cognitive load，但仍属于 CAPTCHA slice。 |
| 13 | `captcha-patch_select_1.json` | 🧪 | instruction 已统一；未重构 task；CAPTCHA slice 规范同上。 | 主要为视觉对象定位/选择。 |
| 14 | `communication-ftc_scam_text_reply.json` | ✅ | instruction 已统一；**已补 Reader evaluator + `and`。** | evaluator 与 instruction 现已一致。 |
| 15 | `consumption-ginger_ale_note.json` | ⚠️ | instruction 已统一；未重构 task。 | 多 review + 多偏好确有 decision load，但建议进一步消除 review 结论主观性，并确保唯一答案。 |
| 16 | `consumption-shopping_desktop_movie_night_note.json` | ✅ | instruction 已统一；其余无需修改。 | Desktop reminder → shopping 是很好的 external-memory / task-tracking 场景。 |
| 17 | `consumption-shopping_price_wireless_mouse.json` | ⚠️ | instruction 已统一；未重构 task。 | 当前多约束比价可接受，但仍接近普通 WebArena shopping；建议加入 reminder/checklist 等 external-memory context。 |
| 18 | `consumption-shopping_review_kids_sunscreen.json` | ⚠️ | instruction 已统一；未重构 task。 | `best-fitting product` 仍偏主观，需要改变任务表述/criteria 才能彻底解决。 |
| 19 | `consumption-shopping_title_elsa_bottle.json` | ❌ | **instruction 已统一；未重构 task。** | 单一标题定位+加购物车的 cognitive load 太弱，需要重构。 |
| 20 | `consumption-shopping_tomato_egg_stir_fry.json` | ⚠️ | instruction 已统一；未重构 task。 | everyday planning 有一定合理性；建议加入 checklist/reminder，使认知支持更明确。 |
| 21 | `health-ap_doctor_appointment_questions.json` | ✅ | instruction 已统一；**已补 Reader evaluator；exact wording evaluator 已收紧。** | 当前 instruction/evaluator 一致性明显改善。 |
| 22 | `information-emergency_kit_checklist.json` | ✅ | instruction 已统一；其余无需修改。 | dense information → actionable checklist，典型 cognitive support。 |
| 23 | `information-forum_post_quick_note.json` | ✅ | instruction 已统一；其余无需修改。 | 信息提取 → quick note，external memory 合理。 |
| 24 | `information-passport_renewal_checklist.json` | ✅ | instruction 已统一；**已删除过短 paraphrase-friendly evaluator alternatives。** | 当前与 exact wording 要求更一致。 |
| 25 | `information-wikipedia_accessibility_definition.json` | ❌ | **instruction 已统一；未重构 task。** | 当前只是找定义并复制，认知支持/复杂度不够，需要重构。 |
| 26 | `management-medication_timer.json` | ✅ | instruction 已统一；其余未修改。 | 当前 vclock URL evaluator 与仓库其他 timer task 使用同一约定；若以后增加 timer-running state getter，可进一步验证“已启动”而不只是 URL。 |
| 27 | `management-prescription_refill_reminder.json` | ✅ | instruction 已统一；**固定日期 evaluator 已改为 `date: 2026-07-20`。** | 已消除 VM today 依赖。 |
| 28 | `management-sunscreen_ingredient_reminder.json` | ✅ | instruction 已统一；**固定日期 evaluator 已改为 `date: 2026-07-15`。** | 已消除 VM today 依赖。 |
| 29 | `information-outdoor_running_supplies_note.json` | ✅ | instruction 已统一；其余无需修改。 | 信息过滤 → external memory note 合理。 |
| 30 | `service-cfpb_automatic_payment_stop_answer.json` | ✅ | instruction 已统一；**exact wording evaluator 已收紧。** | 当前更符合 instruction。 |
| 31 | `service-cms_product_record.json` | ⚠️ | instruction 已统一；**已从“只检查 5/14”提升为“14/14 必须非空 + 5 个稳定字段精确值”。** | 最佳方案是 evaluator 直接读取 CMS 当前 product record 并逐字段与 spreadsheet 比较；否则可考虑将任务改成只记录稳定字段。 |
| 32 | `service-ftc_scam_action_note.json` | ✅ | instruction 已统一；其余无需修改。 | 长指导信息 → 两个明确 action → note，场景清晰。 |
| 33 | `service-passport_documents_note.json` | ✅ | instruction 已统一；其余无需修改。 | complex service information → concise memory aid，Reader 非必需。 |

---

## 需要改任务：本轮未重构任务语义，给出具体建议

下面这些问题不能仅靠修 evaluator 完成，因为真正的问题在**任务场景/目标本身**。

### A. `access-docker_install.json`

当前问题：

- “安装 Docker”只是普通软件安装。
- 操作步骤较多并不能单独构成 cognitive-access task。
- 当前没有 external memory、attention support、processing-speed support、planning aid 等设计。

推荐两种处理方式：

**方案 1：移出 cognitive**

如果 benchmark 里允许普通复杂 GUI task 单独归类，直接移到更合适的集合，不改安装任务本身。

**方案 2：保留 cognitive，但重写场景**

把任务改成“根据 caregiver/IT support 提供的 Desktop checklist 完成安装并保持几个关键安装选项”，例如让用户需要：

1. 打开 Desktop 上的安装步骤清单。
2. 按 checklist 保持 `Use WSL 2` 开启。
3. 明确不要启用 Windows Containers。
4. 不重启。
5. 完成后记录/确认安装状态。

这样 cognitive component 来自 **step tracking + external checklist + remembering configuration constraints**，而不是仅来自安装本身复杂。

### B. `access-spotify_install.json`

当前问题：

- 单纯安装 Spotify 几乎没有 cognitive-specific support。
- instruction 没有需要保持的多条件或记忆辅助。

建议：

- 如果只是测试 app install，移出 cognitive。
- 如果必须保留 cognitive，可增加 Desktop reminder/checklist，例如要求从 caregiver note 中恢复“只安装官方 Windows app、不要登录、安装后固定到 Start”等多个步骤，并用 checklist 支持步骤保持。

不要只加一句“这是给老年人安装 Spotify”，年龄本身不足以改变 task 属性。

### C. `consumption-shopping_title_elsa_bottle.json`

当前问题：

- 根据标题找到一个 Elsa bottle 并加入购物车，目标单一、信息负担低。

建议重构为：

- 给 Desktop/Sticky Notes 一个购物 reminder，里面包含 3–4 个稳定条件。
- 要求用户从 reminder 恢复条件后筛选商品。
- 条件应来自页面上的确定字段，例如 title、容量、价格上限、颜色/类型等。
- evaluator 精确检查最终 product/SKU/cart state。

核心应该变成 **external memory + multi-constraint selection**。

### D. `information-wikipedia_accessibility_definition.json`

当前问题：

- “找到一个 definition → 复制到 Writer”过于直接。
- 缺少明显的 attention/memory/planning support。

建议重构为：

- 从较长页面中找到 2–3 个指定的、稳定的 exact phrases。
- 把内容整理成短 note/checklist，而不是简单复制一个定义。
- 可以使用 Reader，但不必强制；关键是 dense information → simplified output。
- evaluator 应检查完整 source phrase containment。

---

## 可保留但需要修改任务才能进一步提升的边界项

这些任务本轮只统一了 instruction 表达，没有重构用户-facing 场景，因为真正改善需要改变任务设计。

### `consumption-shopping_price_wireless_mouse.json`

建议：

- 把约束放在 Desktop reminder / Sticky Note，而不是全部直接写进 instruction。
- 让 agent 先恢复约束，再完成“wireless + white + standalone + lowest price”比较。
- 这样 working memory / external memory 的设计更清晰。

### `consumption-shopping_review_kids_sunscreen.json`

建议优先解决 `best-fitting` 主观性：

- 不要依赖“综合感觉最好”。
- 把条件定义成可从 reviews 中直接验证的稳定事实/短语。
- 最好设计成唯一 product 能同时满足所有 criteria。
- evaluator 应检查具体 product/SKU，而不是自由文本判断。

### `consumption-ginger_ale_note.json`

建议：

- 明确偏好条件如何映射到 reviews 中的稳定证据。
- 若任务最终是 yes/no 决策，应保证给定页面数据只有一个可重复结论。
- 如要强化 cognitive 场景，可以把多个偏好放入 external reminder，由 agent 对照 reviews 做决策。

### `consumption-shopping_tomato_egg_stir_fry.json`

建议：

- 当前“根据菜名推断缺失原料”有 everyday planning 成分，可以保留。
- 若想更强，可把已有食材/目标菜品放入 shopping checklist，让 agent 识别缺失项并完成购买。
- evaluator 只检查唯一缺失商品，避免常识答案分叉。

### `service-cms_product_record.json`

本轮 evaluator 已明显加强，但如果想做到真正 deterministic：

**推荐 evaluator 工程方案（不改任务）：**

- 新增 result getter/evaluator，在评分时读取 CMS 当前 `Joust Duffle Bag` record。
- 将 CMS 中 14 个当前值与 spreadsheet 14 个 Value cell 做逐字段比较。
- 对 `Last Updated At` 这类动态字段以评分时实际 CMS 值为 ground truth，而不是硬编码。

如果不想开发新的 CMS state evaluator，则需要**改任务**：只要求记录可稳定 hard-code 的字段，例如 Name、Type、SKU、Price、Quantity。

---

## 修复后的汇总

33 个 cognitive task：

- ✅ 可保留：**17**
- ⚠️ 可保留但建议进一步优化：**5**
- ❌ 需要改任务/移出 cognitive：**4**
- 🧪 CAPTCHA stress-test slice：**7**

### 本轮实际修改的 cognitive task JSON

- `cognitive/` 下 **全部 33 个 JSON**：`instruction` 已统一为自然、目标导向的 Agent 委托式表达。
- 其中以下 7 个 task 还包含上一轮已确认的 evaluator 修复：
  1. `communication-ftc_scam_text_reply.json`
  2. `health-ap_doctor_appointment_questions.json`
  3. `information-passport_renewal_checklist.json`
  4. `management-prescription_refill_reminder.json`
  5. `management-sunscreen_ingredient_reminder.json`
  6. `service-cfpb_automatic_payment_stop_answer.json`
  7. `service-cms_product_record.json`

### 本轮实际修改的非 task 文件

1. `paper/README.md`（含 cognitive 定义、CAPTCHA 命名和新增 Instruction Writing Style）
2. `src/win-arena-container/client/desktop_env/evaluators/metrics/thunderbird.py`

---

## 校验结果

本轮修改后对 cognitive 目录再次校验：

- JSON 文件数：**33**
- JSON 严格解析错误：**0**
- cognitive 文件 `id` 与 filename 不一致：**0**
- cognitive 重复 `id`：**0**
- instruction 风格复检：**33/33 已改为目标导向自然指令；未新增步骤式编号 instruction**
- `thunderbird.py` Python syntax compile：**通过**
- 新增 Calendar absolute-date 分支隔离测试：**通过**
- 原 `days_from_today` backward compatibility 隔离测试：**通过**

说明：在当前容器里尝试 import 整个 evaluator package 时，仓库运行环境缺少 `cssselect` Python dependency；该问题来自现有环境依赖链，与本轮 `thunderbird.py` 修改无关，因此额外采用了隔离加载方式验证 Calendar evaluator 的新旧日期路径。

---

## 后续优先级

### P0：已完成

- [x] 固定日期 task 不再依赖 VM today。
- [x] 两个 instruction 强制 Reader 的 task 补 Reader evaluator。
- [x] passport exact wording evaluator 收紧。
- [x] CFPB exact wording evaluator 收紧。
- [x] CMS evaluator 从只覆盖 5/14 提升到 14/14 非空覆盖，并保留稳定字段精确检查。
- [x] README cognitive 定义与当前 benchmark 口径对齐。
- [x] README CAPTCHA lowercase naming 与仓库实际数据对齐。

### P1：需要改任务，未重构（仅统一 instruction 表达）

- [ ] `access-docker_install.json`
- [ ] `access-spotify_install.json`
- [ ] `consumption-shopping_title_elsa_bottle.json`
- [ ] `information-wikipedia_accessibility_definition.json`

### P2：建议优化任务设计，未重构（仅统一 instruction 表达）

- [ ] `consumption-shopping_price_wireless_mouse.json`
- [ ] `consumption-shopping_review_kids_sunscreen.json`
- [ ] `consumption-ginger_ale_note.json`
- [ ] `consumption-shopping_tomato_egg_stir_fry.json`
- [ ] `service-cms_product_record.json`：如需完整 correctness，增加 CMS live-state evaluator。


---

## Category 与 `related_apps` 全量核对（最新）

本轮只检查 `cognitive/` 下 33 个任务，不重新评定 `difficulty`，也不处理 hearing / motor / visual。判定规则：

- `category` 使用 README 中的小写标签，并按**任务主要用户目标/工作流**选择，而不是按来源网站或输出应用机械归类。
- 如果 `category` 发生变化，filename prefix 和 `id` 必须一起变化，并继续满足 `id == filename 去掉 .json`。
- `related_apps` 只列 Agent 完成任务时实际交互的应用；不把 setup-only 组件、无关工具或纯后台服务写进去。
- 对尚待重构的任务，不为了临时满足分类而提前改 category / `related_apps`；等任务目标稳定后一起调整。

| Task | Category 检查 | `related_apps` 检查 |
| --- | --- | --- |
| `access-chrome_immersive_reader_extension.json` | ✅ 保持 `access` | ✅ `chrome` 与任务执行路径一致 |
| `access-docker_install.json` | ⚠️ 暂保留 `access`，待任务重构时重新定类 | ⚠️ `powershell`, `cmd`, `chrome` 是可选路径集合；随任务重构一起收敛 |
| `access-edge_immersive_reader_setup.json` | ✅ 保持 `access` | ✅ `msedge` 与任务执行路径一致 |
| `access-spotify_install.json` | ⚠️ 暂保留 `access`，待任务重构时重新定类 | ⚠️ `chrome`, `powershell`, `cmd` 是可选路径集合；随任务重构一起收敛 |
| `access-text_size_cognitive.json` | ✅ 保持 `access` | ✅ `chrome` 与任务执行路径一致 |
| `access-windows_notification_duration.json` | ✅ 保持 `access` | ✅ `settings` 与任务执行路径一致 |
| `captcha-audio_1.json` | ✅ 保持 `captcha` | ✅ `chrome` 与任务执行路径一致 |
| `captcha-click_sequence_3.json` | ✅ 保持 `captcha` | ✅ `chrome` 与任务执行路径一致 |
| `captcha-count_chars_1.json` | ✅ 保持 `captcha` | ✅ `chrome` 与任务执行路径一致 |
| `captcha-distorted_text_2.json` | ✅ 保持 `captcha` | ✅ `chrome` 与任务执行路径一致 |
| `captcha-image_recognition_2.json` | ✅ 保持 `captcha` | ✅ `chrome` 与任务执行路径一致 |
| `captcha-math_1.json` | ✅ 保持 `captcha` | ✅ `chrome` 与任务执行路径一致 |
| `captcha-patch_select_1.json` | ✅ 保持 `captcha` | ✅ `chrome` 与任务执行路径一致 |
| `communication-ftc_scam_text_reply.json` | ✅ 保持 `communication` | ✅ `msedge, thunderbird` 与任务执行路径一致 |
| `consumption-ginger_ale_note.json` | ✅ 保持 `consumption` | ✅ `chrome, notepad` 与任务执行路径一致 |
| `consumption-shopping_desktop_movie_night_note.json` | ✅ 保持 `consumption` | ✅ `chrome, notepad` 与任务执行路径一致 |
| `consumption-shopping_price_wireless_mouse.json` | ✅ 保持 `consumption` | ✅ `chrome` 与任务执行路径一致 |
| `consumption-shopping_review_kids_sunscreen.json` | ✅ 保持 `consumption` | ✅ `chrome` 与任务执行路径一致 |
| `consumption-shopping_title_elsa_bottle.json` | ✅ `consumption` 与商品查找/加购目标匹配；任务本身仍待重构 | ✅ `chrome` 匹配 |
| `consumption-shopping_tomato_egg_stir_fry.json` | ✅ 保持 `consumption` | ✅ `chrome` 与任务执行路径一致 |
| `health-ap_doctor_appointment_questions.json` | ✅ 保持 `health`；医疗预约与准备信息是主领域 | ✅ `msedge`, `thunderbird` 匹配 |
| `information-emergency_kit_checklist.json` | ✅ 保持 `information` | ✅ `msedge, sticky_notes` 与任务执行路径一致 |
| `information-forum_post_quick_note.json` | ✅ 保持 `information` | ✅ `chrome, notepad` 与任务执行路径一致 |
| `information-outdoor_running_supplies_note.json` | ✅ 已由 `mobility` 改为 `information`；核心工作是读取文章并记录信息 | ✅ `msedge`, `sticky_notes` 与执行路径一致 |
| `information-passport_renewal_checklist.json` | ✅ 保持 `information` | ✅ `msedge, sticky_notes` 与任务执行路径一致 |
| `information-wikipedia_accessibility_definition.json` | ✅ `information` 与当前查找/写入定义的任务目标匹配；任务本身仍待重构 | ✅ `chrome`, `libreoffice_writer` 匹配 |
| `management-medication_timer.json` | ✅ 保持 `management`；主要结果是创建并运行时间管理工具 | ✅ `notepad`, `chrome` 匹配 |
| `management-prescription_refill_reminder.json` | ✅ 保持 `management`；主要结果是日历提醒，虽有健康语境 | ✅ `notepad`, `thunderbird` 匹配 |
| `management-sunscreen_ingredient_reminder.json` | ✅ 保持 `management`；主要结果是计算日期并创建提醒 | ✅ `msedge`, `thunderbird` 匹配 |
| `service-cfpb_automatic_payment_stop_answer.json` | ✅ 保持 `service`；围绕金融服务/自动扣款处理指导 | ✅ `msedge`, `notepad` 匹配 |
| `service-cms_product_record.json` | ✅ 保持 `service`；属于后台服务/产品记录处理工作流 | ✅ `chrome`, `libreoffice_calc` 匹配 |
| `service-ftc_scam_action_note.json` | ✅ 保持 `service`；围绕政府消费者保护服务指导 | ✅ `msedge`, `sticky_notes` 匹配 |
| `service-passport_documents_note.json` | ✅ 保持 `service`；围绕政府护照服务选项 | ✅ `chrome`, `sticky_notes` 匹配 |

### 本轮实际字段修改

- `mobility-outdoor_running_supplies_note.json` → `information-outdoor_running_supplies_note.json`
  - `category`: `mobility` → `information`
  - `id`: `mobility-outdoor_running_supplies_note` → `information-outdoor_running_supplies_note`
  - filename 同步改名，继续满足 `id == filename stem`。
  - `related_apps` 保持 `msedge`, `sticky_notes`。
- 其余 32 个 cognitive task 的 `category` 和 `related_apps` 均未修改。
- `difficulty` 本轮完全未调整。

### 待随任务重构一起复查

- `access-docker_install.json`：当前 `access` 分类与纯 Docker 安装目标并不自然；重构 cognitive 场景后重新确定 category，并同步收敛 `related_apps`。
- `access-spotify_install.json`：同上；当前 `related_apps` 包含多个可选安装/验证路径，应在新任务路径明确后重新确定。
