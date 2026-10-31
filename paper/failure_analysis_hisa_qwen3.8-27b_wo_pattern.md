# HISA Qwen3.8-27B（wo pattern）任务失败原因分析

## 1. 统计口径

- 数据目录：`results/hisa_qwen3.8-27b_wo_pattern`
- 参考口径：`paper/failure_analysis_agents3.md`
- 失败定义：任务目录中的 `eval(result.txt) < 1`
- 分析证据：`result.txt`、`execution_log.json`、任务配置中的 evaluator/metric roles、逐步 `action_logs`，以及任务 `logs/*.log` 中的终止标记。
- 总任务数：198；成功 88（44.44%）；失败 110（55.56%）。所有分数均为 0 或 1。
- evaluator 将完整成功拆成普通任务结果 `(T)` 与 need-conditioned handoff/access requirement `(H)`；完整成功为 `(F=T∧H)`。

这里用一个可复核的操作性区分：

- **accessibility-related failure**：`H=0`。这表示最终 handoff/access requirement 未满足，但不表示底层错误必然是“残障特有”的；底层仍可能是误点击、错误设置值、未保存、步数耗尽或错误完成判断。
- **其他失败**：`H=1,T=0`。辅助状态已经满足，失败来自普通业务结果、内容、页面、文件、商品、路线或 artifact 不正确。

## 2. 总体结果与 accessibility/其他失败的区分

110 个失败的 evaluator 组合如下：

| `(T)` | `(H)` | relation | 数量 | 占全部失败 | 解释 |
|---:|---:|---|---:|---:|---|
| 1 | 0 | distinct | 5 | 4.55% | 普通任务已完成，但 accessibility handoff 未准备好；这是最纯粹的 handoff gap |
| 0 | 0 | distinct | 10 | 9.09% | 普通任务和独立 handoff requirement 同时失败 |
| 0 | 0 | coincident | 69 | 62.73% | 普通目标与 accessibility 目标是同一个可观察结果，整体失败 |
| 0 | 1 | distinct | 26 | 23.64% | accessibility support 已满足，但普通任务错误 |
| **合计** |  |  | **110** | **100%** |  |

因此：

- **84/110（76.36%）是直接的 accessibility-related failure（`H=0`）**；
- **26/110（23.64%）是其他失败（`H=1,T=0`）**。

这一区分比按用户组或任务名称判断更可靠。例如 hearing 任务并不一定是 accessibility handoff failure：本批次有 26 个任务已经成功保持 Live Caption、Mono Audio 或其他指定支持，但邮件、笔记、网页、路线或业务操作仍然不正确。

## 3. 轨迹层的直接失败机制

HISA 的 `action_logs` 不记录一个单独的 `done_action`，但运行日志明确记录 `Task COMPLETED`、`Reached max_steps` 或 `Task INFEASIBLE`。110 个失败可完整分为三类：

| 终止机制 | 数量 | 占失败 | accessibility-related (`H=0`) | 其他 (`H=1,T=0`) |
|---|---:|---:|---:|---:|
| 代理主动判定 `Task COMPLETED`，但 evaluator 为 0 | 73 | 66.36% | 63 | 10 |
| 达到 50 步上限 | 31 | 28.18% | 15 | 16 |
| 主动判定 infeasible | 6 | 5.45% | 6 | 0 |
| **合计** | **110** | **100%** | **84** | **26** |

首要问题不是单纯“不会操作”，而是**完成判断与机器可评测终态不一致**。73 个失败中，代理主动声称完成；其中 63 个还同时违反 `(H)`。常见模式包括：

1. 只验证屏幕观感，没有验证 evaluator 读取的系统状态、文件路径、数据库记录、草稿、日历事件或浏览器终态。
2. 将“执行了一条命令”当作“目标设置已生效”。注册表键名、值语义、当前会话状态和 evaluator 检查对象经常不一致。
3. 将“点击了 Save/Add to Cart/Start”当作持久化成功，没有再读取目标对象。
4. 多条件任务只验证最后一个动作，遗漏精确字段、数量、URL、辅助功能保持状态或页面保持状态。
5. 从文件名、局部字幕、搜索摘要或视觉提示进行 plausible inference，随后把推断当作已核验事实。

31 个步数耗尽任务则表现为：反复滚动/点击相邻位置、在音频转写和依赖安装上消耗大量步骤、过晚开始写 artifact、停留在搜索或 CMS 定位阶段、以及 CAPTCHA/购物页面的坐标校准无法收敛。

6 个主动 infeasible 中：

- 3 个是初始环境落在 Chromium sign-in 页面、目标 CAPTCHA 未出现：`cognitive/captcha-audio_1`、`cognitive/captcha-click_sequence_3`、`cognitive/captcha-click_sequence_4`；
- 2 个是 patch-select CAPTCHA 多次识别/坐标提交均被拒绝：`motor/captcha-patch_select_3`、`visual/captcha-patch_select_2`；
- 1 个是错误判断 Windows 不存在所需通知持续时间设置：`cognitive/access-windows_notification_duration`。

## 4. Accessibility-related failures（84 个）

### 4.1 最纯粹的 handoff gap：`T=1,H=0`（5 个）

- `cognitive/service-cms_delete_obsolete_pickup_page`：CMS 页面已删除，但 Sticky Note 把正确的 `NP-41` 写成 `NF-41`；普通业务动作成功，持久记忆记录错误。
- `hearing/management-double_dough_timer`
- `hearing/management-quick_sponge_timer`
- `hearing/mobility-opera_house_street_view`
- `hearing/mobility-walking_route_alhambra`

后四个 hearing 任务的计时器、Street View 或路线目标通过，但独立的 caption/handoff 条件未通过。它们直接说明：只完成 nominal task 不足以保证用户接手时仍有可用的辅助通道。

### 4.2 `T=0,H=0` 且 relation=distinct（10 个）

这些任务的普通目标和独立 handoff requirement 同时失败：

- cognitive：`consumption-kids_sunscreen_reviews`、`consumption-lowest_price_white_mouse`、`consumption-movie_night_shopping`、`consumption-tomato_egg_stir_fry`、`service-cms_import_service_product`
- hearing：`information-handwashing_steps`
- visual：`consumption-guest_bathroom_towel_holders`、`consumption-keto_bread`、`consumption-lavender_coupon`、`consumption-saute_pan`

其中 9 个达到 50 步上限；`information-handwashing_steps` 主动完成，但代理自己在最后一步已经观察到笔记缺少第一项 `Wet hands`，仍然终止。该例是“已有反证但仍完成”的强证据。

### 4.3 `T=H=0` 且 relation=coincident（69 个）

这些任务中，支持配置、外部记忆、可访问表示或 delegated barrier 本身就是任务目标，无法再把 `(T)` 和 `(H)` 独立拆开。主要失败机制如下。

#### A. 辅助设置的精确状态错误（11 个 access 类失败）

- `cognitive/access-windows_notification_duration`
- `hearing/access-windows_audio_flash_title_bar`
- `hearing/access-windows_audio_flash_window`
- `hearing/access-windows_mono_audio_screen_flash`
- `hearing/access-windows_notification_5_minutes`
- `motor/access-enable_clicklock`
- `motor/access-enable_mouse_keys`
- `motor/access-enable_sticky_keys`
- `motor/access-set_primary_mouse_button_right`
- `visual/access-windows_color_filter_protanopia`
- `visual/access-windows_magnifier_200`

轨迹显示的共同问题是**写入近似或自造的注册表值、只验证持久值而未验证当前有效状态、混淆设置所在页面、或停在接近但不精确的参数**。代表性证据包括：

- `access-windows_color_filter_protanopia` 最后仍观察到 Intensity=76，而目标为 80；
- `access-windows_magnifier_200` 最后观察到 200% 已设置但 Magnifier 仍为 Off，随后点击开关却未做 evaluator 等价验证；
- Sticky Keys、Mouse Keys、ClickLock 和 audio flash 任务通过直接写注册表尝试完成，但 evaluator 未确认目标系统状态；
- 两个通知持续时间任务错误地在普通 Notifications 页寻找设置或断言设置不存在，未对齐任务实际检查的 accessibility 状态。

#### B. persistent support / external memory artifact 不正确

典型任务包括日历、Sticky Notes、文档、表格和提醒：

- `cognitive/health-doctor_appointment_preparation`
- `cognitive/health-medication_change_calendar`
- `cognitive/health-running_hydration_guide_note`
- `cognitive/management-sunscreen_ingredient_reminder`
- `cognitive/mobility-harvard_mather_evening_plan`
- `motor/health-parkinsons_medication_reminders`
- `motor/health-sticky_keys_emergency_contact_card`
- `motor/management-next_meeting_calendar`
- `motor/management-student_gradebook`
- `visual/management-cardiology_appointment_reminder`
- `visual/management-weekly_planner_calendar`

常见原因是字段内容、日期/时间、重复规则、路径或保存对象不完全匹配；代理通常在点击 Save、键入文本或直接改写文档内部结构后立即完成，没有重新读取 evaluator 对应的持久对象。

#### C. accessible representation 的内容或保存不正确

典型任务包括：

- `visual/information-cat_image_alt_text`
- `visual/information-cta_rail_map_alt_text`
- `visual/health-hospital_wayfinding_map`
- `visual/health-drug_facts_package`
- `visual/information-apple_q3_operating_margin`
- `visual/information-metal_density_comparison`
- `visual/information-second_gold_rush`
- `visual/information-wikipedia_image_person`
- `visual/service-medicare_card_sample`
- `visual/service-real_id_infographic`

失败来自 OCR/视觉证据不完整、从局部画面推断答案、错误文本内容、错误文件位置，或认为格式确认对话框关闭后文档就已按 evaluator 要求保存。对这些任务而言，文本是用户替代视觉内容的主要渠道，因此内容精度和持久化本身就是 accessibility outcome。

#### D. delegated motor/visual barrier 未被可靠完成

失败 CAPTCHA 包括：

- 环境目标未出现：`cognitive/captcha-audio_1`、`cognitive/captcha-click_sequence_3`、`cognitive/captcha-click_sequence_4`
- 持续按压/滑块/图块选择失败：`motor/captcha-hold_button_1`、`motor/captcha-patch_select_3`、`motor/captcha-slide_puzzle_1`、`visual/captcha-hold_button_2`、`visual/captcha-patch_select_2`

底层机制是环境恢复、视觉 grounding、按住/拖动时长、网格边界估计和服务端反馈闭环不足。它们是一般控制限制，但在这些任务中，用户正是因为无法可靠完成精细或持续输入而委托代理，因此失败具有直接 accessibility 后果。

#### E. 商品、路线、CMS 等复合任务破坏 handoff

coincident 任务中还存在大量普通 GUI 错误：商品未真正入车、数量/variant 不对、路线模式或终点错误、CMS 尚未保存、文件写到错误路径。因为 evaluator 将支持目标与业务目标定义为同一 observable outcome，这些错误仍计入 `H=0`，但不应被描述为“accessibility 导致了误点击”。更准确的表述是：**通用执行错误使 accessibility-conditioned continuation 或 support artifact 不可用。**

## 5. 其他失败：`H=1,T=0`（26 个）

这 26 个任务不能称为 failed accessibility handoff：指定辅助状态已经通过。它们的终止结构是 16 个达到 50 步上限、10 个错误完成判断。

| 任务类别 | 数量 | 主要原因 |
|---|---:|---|
| communication | 5 | 草稿未被 evaluator 找到、字段/内容不完整、音频事实未提取、Thunderbird 保存失败 |
| consumption | 4 | 商品定位、variant/数量、Add to Cart 和购物车终态未完成 |
| health | 2 | 笔记内容或持久化错误；Sticky Notes 窗口/内容未完成 |
| information | 7 | 音频/网页数据未取得、错误季度/州数据、错误文件内容或未生成 artifact |
| management | 2 | 音频事实已部分提取，但笔记/日历未完成 |
| mobility | 1 | 从不完整字幕推断了错误 trail，随后展示了错误路线 |
| service | 5 | CMS 未提交、答案文件路径错误、官方表单/URL 选错、精确答案不匹配 |
| **合计** | **26** |  |

完整任务列表：

- cognitive：`communication-library_program_reply`
- hearing：`communication-dental_reschedule_voicemail`、`communication-equipment_reimbursement_email`、`communication-passport_photo_checklist_email`、`communication-pharmacy_pickup_voicemail`、`consumption-colgate_slimsoft_six_pack`、`consumption-dyson_travel_case`、`consumption-insta360`、`consumption-sony_alpha`、`health-child_visit_preparation`、`health-long_covid_care_note`、`information-fake_job_bank_account`、`information-ftc_2024_fraud_reports`、`information-ftc_florida_fraud_data`、`information-ftc_washington_q4_fraud`、`information-laundry_tag_investigation`、`information-maricopa_census_search`、`information-noaa_pillow_lava`、`management-home_delivery_window_audio`、`management-service_appointment_audio`、`mobility-zion_large_group_route`、`service-cms_update_access_desk_page_audio`、`service-cms_update_voyage_stock_audio`、`service-council_document_pickup_audio`、`service-irs_ip_pin_alternative_form`、`service-ssa_replacement_card_start`

几个可直接定位的例子：

- `service-council_document_pickup_audio` 已正确提取四项信息，但把 `answer.txt` 写到 `C:\Users\Docker\answer.txt`，不是 Desktop；`H` 通过而 `T` 失败。
- `service-irs_ip_pin_alternative_form` 打开了 Form 14039；evaluator 要求的是 Form 15227，属于目标表单选择错误。
- `service-ssa_replacement_card_start` 写成 “most arrive in about 10 business days”，而 evaluator 要求 `5 to 10 business days`，且需保持精确 replacement-card 页面。
- `mobility-zion_large_group_route` 在字幕未可靠显示限制信息时，轨迹明确写道“proceed with the expected permitted trail”，随后基于未经验证的猜测建立路线。
- `communication-equipment_reimbursement_email` 与 `communication-passport_photo_checklist_email` 的屏幕轨迹显示字段看似正确并执行 Ctrl+S，但 evaluator 未找到匹配草稿；这说明 UI 观感不能替代对 Thunderbird 持久对象的验证。
- `communication-library_program_reply` 的草稿和日历在 UI 中看似均存在，但 task component 仍失败；现有日志足以确认“最终持久对象未匹配 evaluator”，但不能仅凭截图进一步断言究竟是哪一个底层 Thunderbird 字段序列化不一致。

## 6. 分组统计

### 6.1 用户组

| 用户组 | 总数 | 失败 | 失败率 |
|---|---:|---:|---:|
| cognitive | 49 | 22 | 44.90% |
| hearing | 50 | 34 | 68.00% |
| motor | 50 | 28 | 56.00% |
| visual | 49 | 26 | 53.06% |
| **合计** | **198** | **110** | **55.56%** |

hearing 失败率最高，但其中 26 个失败是 `H=1,T=0`；因此不能将 68% 直接解释为 Live Caption/Mono Audio 配置失败。更准确的结论是：HISA 较常成功建立听觉支持状态，却仍难以完成音频事实提取和下游业务操作。

### 6.2 任务类别

| 类别 | 总数 | 失败 | 失败率 |
|---|---:|---:|---:|
| consumption | 24 | 20 | 83.33% |
| mobility | 16 | 11 | 68.75% |
| service | 19 | 13 | 68.42% |
| information | 29 | 18 | 62.07% |
| health | 21 | 11 | 52.38% |
| management | 20 | 10 | 50.00% |
| communication | 18 | 8 | 44.44% |
| access | 26 | 11 | 42.31% |
| captcha | 25 | 8 | 32.00% |

最薄弱的是 consumption：20/24 失败。轨迹反复显示页面滚动失效、商品定位错误、variant/数量未确认、Add to Cart 后没有机器可读验证，以及在 50 步时仍停留在商品页。mobility、service 和 information 也较弱，分别受错误事实推断、跨站/跨应用操作链和精确 URL/文件内容要求影响。

### 6.3 need ID

| Need | n | 失败 | 失败率 | `(T)` 成功率 | `(H)` 成功率 |
|---|---:|---:|---:|---:|---:|
| V1 | 21 | 14 | 66.7% | 33.3% | 33.3% |
| V2 | 13 | 5 | 38.5% | 61.5% | 61.5% |
| V3 | 20 | 10 | 50.0% | 50.0% | 50.0% |
| H1 | 44 | 30 | 68.2% | 40.9% | 88.6% |
| H2 | 5 | 1 | 20.0% | 80.0% | 100.0% |
| H3 | 4 | 4 | 100.0% | 0.0% | 0.0% |
| H4 | 5 | 4 | 80.0% | 20.0% | 80.0% |
| M1 | 17 | 3 | 17.6% | 82.4% | 82.4% |
| M2 | 16 | 15 | 93.8% | 6.3% | 6.3% |
| M3 | 10 | 6 | 60.0% | 40.0% | 40.0% |
| M4 | 7 | 4 | 57.1% | 42.9% | 42.9% |
| C1 | 3 | 1 | 33.3% | 66.7% | 66.7% |
| C2 | 16 | 6 | 37.5% | 62.5% | 62.5% |
| C3 | 40 | 19 | 47.5% | 55.0% | 55.0% |

任务可以包含多个 need ID，因此各行不能相加得到总任务数。最明显的模式是：

- H1 的 `(H)` 成功率很高（88.6%），但 `(T)` 只有 40.9%；支持状态成功不等于音频信息被准确转成可用结果。
- M2 失败 15/16，是本批次最弱的较大样本 need；持续、可控节奏或精细交互任务仍难收敛。
- H3 为 4/4 失败，H4 为 4/5 失败，但样本较小，只能作为当前系统的描述性结果。

## 7. 与 agents3 参考结果的主要差异

在同为 198 个任务的当前结果上：

- HISA wo-pattern 完整成功率为 44.44%，略低于参考 agents3 的 45.96%；
- HISA 的 `(H)` 成功率为 57.58%，高于参考结果由 89 个 `H=0` 推得的 55.05%；
- 但 HISA 的 `(T)` 成功率只有 46.97%，低于参考结果由 97 个 `T=0` 推得的 51.01%；
- HISA 的纯 handoff gap `T=1,H=0` 为 5 个，少于 agents3 的 10 个；与此同时 `H=1,T=0` 为 26 个，高于 agents3 的 18 个。

因此，HISA wo-pattern 的主要相对特征不是“更难打开辅助功能”，而是**更常建立辅助状态后仍无法完成普通任务**。尤其在 hearing 任务中，caption/mono support 经常通过，但音频事实采集、精确转写、跨应用迁移和最终 artifact 验证仍然失败。

## 8. 总结

HISA Qwen3.8-27B wo-pattern 的 110 个失败中，84 个直接违反 `(H)`，26 个已满足 `(H)` 但普通任务失败。最强的轨迹证据是 73 个错误完成判断：代理主动报告完成，但最终 evaluator 为 0；其中 63 个还没有准备好 accessibility-conditioned handoff。

从 accessibility 角度，关键限制是：精确辅助设置状态不可靠、支持 artifact 的字段/内容/持久化不可信、视觉或音频证据被不完整采集后进行推断、持续/精细交互无法闭环，以及结束前缺少对 `(T)` 和 `(H)` 的独立机器可读验证。

从其他失败角度，核心是：即使 Live Caption、Mono Audio 或其他支持已建立，商品、邮件、笔记、CMS、路线、官方页面和文件结果仍可能错误。最准确的总体表述是：**HISA wo-pattern 在“建立部分支持状态”上相对可行，但在把来源证据准确转移到持久、可评测、可继续的最终状态上仍不稳定。**
