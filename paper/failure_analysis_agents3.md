# agents3_qwen3.8-27b Accessibility 失败原因汇总

## 1. 统计口径

- 数据目录：`results/agents3_qwen3.8-27b`
- 失败定义：任务目录中的 `eval(result.txt) < 1`
- 总任务数：198
- 成功：91（45.96%）
- 失败：107（54.04%）
- 本报告依据每个任务的 `result.txt`、`execution_log.json`、任务配置、最后动作和评测分项汇总。
- 本批次的分数只有 `0.0` 和 `1.0`，因此 107 个失败任务均为 `0.0`，不存在介于 0 和 1 之间的部分分。

## 2. 哪些失败与 accessibility 有关

### 2.1 不能把任务简单分成“accessibility 相关”和“无关”

按照 `paper/acl2027/main.tex` 的定义，这 198 个任务全部由 documented access need 构造。每个任务包含：

- 普通数字任务目标 (T)（`task_outcome`）；
- need-conditioned handoff contract (H)（`access_requirement`）；
- 完整成功 (F=T\land H)（`result.txt`）。

因此，所有 107 个失败都发生在 accessibility-conditioned benchmark 中。不过，不能把每个底层错误都称为“残障特有错误”：误点击、约束遗忘、跨应用导航、步数耗尽和过早结束通常是通用 GUI-agent 限制。benchmark 的贡献在于显示这些通用错误如何破坏 accessible information、persistent external support 或 usable continuation interface，并使用户接手时无法使用、核验或继续任务。

以下数字均从当前 `agents3_qwen3.8-27b` 的 198 个结果重新计算。它们不能与 `main.tex` 附录中尚未对齐的旧版 LocalLSTC 200-run case study（51 个 distinct-component tasks）直接混用；当前结果包含 **55 个 distinct-component tasks**。

### 2.2 最直接的 accessibility 失败：(H=0)（89 个）

107 个失败中有 **89 个（83.18%）的 handoff requirement 未通过**。这是最宽口径、由评测器直接支持的 accessibility-related failure 集合。

| 关系 | (T) | (H) | 数量 | accessibility 解释 |
|---|---:|---:|---:|---|
| distinct | 1 | 0 | 10 | **最纯粹的 handoff gap**：普通任务已经完成，但用户所需的辅助状态/表示/支持没有留下 |
| distinct | 0 | 0 | 14 | 普通任务与 handoff 都失败；与 accessibility 直接相关，但不能把根因只归于 handoff |
| coincident | 0 | 0 | 65 | 任务目标本身就是支持配置或支持 artifact；失败即 accessibility contract 失败，但无法独立分解 (T) 与 (H) |
| **合计** |  | 0 | **89** | handoff readiness 未满足 |

更值得关注的是，**47/89 个 (H=0) 任务最终以 `done_action` 结束**。也就是说，代理不仅没有准备好 accessibility-conditioned handoff，还错误地认为已经完成。这直接对应论文所强调的 final verification and honest termination limitation。

#### A. `T=1,H=0`：普通 benchmark 会判成功，但本 benchmark 揭示 handoff 失败（10 个）

这是论文中最核心的诊断集合：

- `cognitive/communication-library_program_reply`
- `hearing/consumption-sony_alpha`
- `hearing/information-laundry_tag_investigation`
- `hearing/information-maricopa_census_search`
- `hearing/management-double_dough_timer`
- `hearing/management-dryer_cycle_timer`
- `hearing/management-quick_sponge_timer`
- `hearing/mobility-opera_house_street_view`
- `hearing/mobility-walking_route_alhambra`
- `visual/consumption-saute_pan`

这些任务说明：商品、路线、计时器或其他普通目标可能已正确完成，但 Live Caption、Narrator 或相应的 persistent/continuation condition 没有在交还控制权时保持可用。若只汇报 nominal task success，这 10 个失败会被隐藏。

#### B. `T=0,H=0` 且组件 distinct：任务和 handoff 同时失败（14 个）

- cognitive：`consumption-lowest_price_white_mouse`、`consumption-movie_night_shopping`、`service-cms_import_service_product`、`service-cms_update_voyage_stock`
- hearing：`communication-dental_reschedule_voicemail`、`communication-equipment_reimbursement_email`、`communication-meeting_action_items`、`communication-passport_photo_checklist_email`、`consumption-insta360`、`consumption-order_substitution_audio`、`information-apartment_maintenance`、`information-ftc_2024_fraud_reports`、`information-ftc_florida_fraud_data`、`information-handwashing_steps`

这组通常反映复合失败：代理既没有完成普通工作，也没有建立或保持用户需要的 handoff 状态。应分别编码 generic execution cause 和 violated handoff obligation，不能笼统归因为“模型不懂 accessibility”。

#### C. `T=H=0` 且组件 coincident：accessibility 目标本身失败（65 个）

在 coincident 任务中，普通目标和 handoff contract 是同一个可观察目标，例如启用并保持某项辅助设置、创建正确的提醒/外部记忆 artifact、生成可访问的文本表示或代理完成原本不可执行的精细交互。这里不存在独立的“普通任务成功但 handoff 失败”比较；失败仍直接说明 accessibility-conditioned completion 没有实现。

按功能组分布为：cognitive 14、hearing 3、motor 23、visual 25。代表任务包括：

- assistive state：`motor/access-enable_filter_keys`、`visual/access-windows_magnifier_200`、`visual/access-high_contrast_aquatic`、`hearing/access-windows_audio_flash_window`
- persistent support：`cognitive/management-prescription_refill_reminder`、`cognitive/management-medication_timer`、`cognitive/health-running_hydration_guide_note`
- accessible representation：`visual/information-cat_image_alt_text`、`visual/information-cta_rail_map_alt_text`、`visual/health-hospital_wayfinding_map`
- delegated access barrier：`motor/captcha-hold_button_1`、`motor/captcha-slide_puzzle_1`、`visual/captcha-patch_select_2`

### 2.3 `H=1,T=0`：不是 handoff-condition failure，但仍是 accessibility 场景中的重要 limitation（18 个）

这 18 个任务已经满足被单独评测的 handoff condition，不能把它们描述成“辅助功能没有打开”或“handoff 未建立”。失败来自 nominal task：内容、选择、转写、artifact 字段或业务操作不正确。

- cognitive：`consumption-elsa_water_bottle`、`consumption-ginger_ale_note`、`consumption-kids_sunscreen_reviews`、`consumption-tomato_egg_stir_fry`、`service-cms_delete_obsolete_pickup_page`
- hearing：`communication-community_class_registration`、`communication-pharmacy_pickup_voicemail`、`consumption-dyson_travel_case`、`health-child_visit_preparation`、`health-long_covid_care_note`、`health-sepsis_act_fast`、`information-ftc_washington_q4_fraud`、`information-noaa_pillow_lava`、`management-home_delivery_window_audio`、`service-cms_update_access_desk_page_audio`
- visual：`consumption-guest_bathroom_towel_holders`、`consumption-keto_bread`、`consumption-lavender_coupon`

它们仍然对 accessibility agent 研究有价值，原因是“支持状态存在”不代表交还结果可用。例如：

- caption 已开启，但瞬时语音证据没有完整采集或没有正确转写到邮件、日历、CMS 或笔记；
- checklist/status 已更新，但购物车中的商品、规格或数量错误，形成了**错误但看似确定的外部记忆**；
- Narrator 已开启，但页面、商品或继续操作状态不正确。

因此这组应描述为 **accessible support established, nominal work incorrect**，而不是 accessibility handoff gap。

### 2.4 按论文最终 14 个 need ID 的结果

当前任务元数据仍同时含有 legacy `C3` 和 `C4`。下表按论文最终 taxonomy 将二者合并为 `C3`，并对同一任务去重。任务可有多个 need ID，因此各行样本数不能相加作为总任务数。

| Need | 论文中的含义 | n | 失败 | 失败率 | (T) | (H) | (F) |
|---|---|---:|---:|---:|---:|---:|---:|
| V1 | 视觉信息的其他模态 / 非视觉 continuation | 21 | 12 | 57.1% | 47.6% | 57.1% | 42.9% |
| V2 | 可适配视觉呈现：缩放、对比度、颜色、文字大小 | 13 | 9 | 69.2% | 30.8% | 30.8% | 30.8% |
| V3 | 非文本信息的文本替代 | 20 | 11 | 55.0% | 45.0% | 45.0% | 45.0% |
| H1 | 音频信息的其他模态：caption/transcript | 44 | 28 | 63.6% | 54.5% | 59.1% | 36.4% |
| H2 | 可管理的字幕/文本呈现 | 5 | 1 | 20.0% | 80.0% | 80.0% | 80.0% |
| H3 | 可感知的重要提醒 | 4 | 3 | 75.0% | 25.0% | 25.0% | 25.0% |
| H4 | 可适配音频呈现：mono/channel 等 | 5 | 5 | 100.0% | 0.0% | 40.0% | 0.0% |
| M1 | 替代输入模态：OSK/dictation 等 | 17 | 4 | 23.5% | 76.5% | 76.5% | 76.5% |
| M2 | 非同时、可自行控制节奏的操作 | 16 | 11 | 68.8% | 31.2% | 31.2% | 31.2% |
| M3 | 替代交互方式：Mouse Keys/键盘导航等 | 10 | 4 | 40.0% | 60.0% | 60.0% | 60.0% |
| M4 | 减少持续用力、精细瞄准和拖动 | 7 | 4 | 57.1% | 42.9% | 42.9% | 42.9% |
| C1 | 减少干扰 | 3 | 2 | 66.7% | 33.3% | 33.3% | 33.3% |
| C2 | 降低认知负担 / 简化呈现 | 16 | 7 | 43.8% | 56.2% | 56.2% | 56.2% |
| C3 | 记忆与回忆支持：记录、提醒、timer、calendar | 40 | 19 | 47.5% | 55.0% | 65.0% | 52.5% |

need-level 结果显示的主要薄弱点是 H4、H3、V2、M2、H1 和 M4，但 H2、H3、H4、C1、M4 的样本量较小，只能作为当前系统的描述性结果，不能据此推断一般能力排序。

### 2.5 对论文最有价值的 accessibility limitation

依照 `main.tex` 的两层分析框架，建议把当前轨迹归纳为以下“通用执行机制 → accessibility handoff 后果”：

1. **瞬时证据采集不完整 → accessible information 不完整。** H1 的 44 个任务中失败 28 个。系统只有稀疏截图，没有连续 caption transcript/audio buffer；字幕可能在两次观察之间消失，导致日期、代码、数量或顺序缺失。即使 caption 状态为 (H=1)，下游邮件、笔记、日历或 CMS 内容仍可能错误。
2. **视觉/OCR 不确定后进行 plausible inference → 错误的文本替代。** 在地图、图片、扫描件和复杂 PDF 中，代理会把局部合理推断当成已验证事实。对 V3 用户而言，生成文本是视觉内容的替代渠道，因此“看似合理但无证据”的答案会直接破坏可访问性。
3. **跨应用信息转移和结构化 artifact 构造错误 → support 存在但不可信。** 从网页/音频/PDF 转移到 Thunderbird、Calendar、Sticky Notes、Office 或 CMS 时，容易漏字段、改写代码、丢失日期年份、保存到错误对象，或只更新 checklist 而未正确完成业务动作。
4. **只能打开辅助功能，难以配置精确参数 → continuation interface 不可用。** V2 失败 9/13、M2 失败 11/16、H3 失败 3/4、H4 失败 5/5。模型较容易“打开” Narrator、Magnifier、OSK 等功能，但对 200% magnification、指定 color filter、Filter Keys 子项、audio-flash mode、mono/channel 等精确状态不稳定。
5. **grounding 和持续/精细交互不足 → 原有 motor access barrier 仍存在。** M4 中 4/7 失败；hold、slide、patch selection、dragging 明显比普通 click/checkbox 困难。底层问题是通用 control limitation，但在这些任务中用户正是因为难以完成持续或精细指针操作而委托代理，因此失败具有直接 accessibility 后果。
6. **过早结束和部分验证 → 未准备好却交还控制权。** 56 个失败以 `done_action` 结束，其中 47 个 (H=0)。代理经常只验证“发生了变化”，没有验证所有 contract 项；这是当前结果中证据最强、覆盖面最大的 handoff limitation。
7. **错误的 persistent memory artifact 比缺失更危险。** C3 中 19/40 失败，并出现 (H=1,T=0) 的情况：清单或状态可能已被更新，但购物车、来源事实或业务动作错误。用户后续依赖该记录时，错误会被固化并放大。

### 2.6 论文写作时应避免的表述

- 不要写“89 个失败由 accessibility 导致”；数据只证明这些任务的 (H) 未满足，不证明 accessibility condition 是底层错误的因果来源。
- 不要把 `H=1,T=0` 的 18 个任务称为 failed handoff condition；应称为 support-ready but nominally incorrect。
- 不要把 agent 没有使用 Narrator/Live Caption/OSK 当作失败原因；论文明确评测的是用户接手时的终态，而非代理必须采用的执行通道。
- 不要从用户组失败率推断群体能力或用户难度；组别标记的是 handoff contract 的功能动机。
- 不要把当前 198-task 结果与附录旧版 200-run 数字合并或直接比较，除非先完成任务集合和配置对齐。

## 3. 总体结论

失败的首要问题是**完成判断与真实可评测状态不一致**：56 个失败任务以 `done_action` 结束，即代理明确声称任务完成，但评测仍为 0。这说明代理较多依赖截图观感、界面提示或自身推断，没有在结束前验证评测真正检查的持久状态，例如设置是否实际生效、文件是否保存到正确路径、邮件是否处于正确状态、购物车中的 SKU/规格/数量是否完全匹配、无障碍功能是否仍保持开启。

第二类主要问题是**操作效率低、陷入重复尝试并耗尽步数**：23 个任务执行到 50 步仍未完成。典型情形包括在网页或设置页反复滚动、反复点击相邻控件、不断调用代码代理做侦察但没有及时提交最终状态，以及多应用任务只完成了其中一部分。

此外，16 个任务的日志在普通 GUI、代码或等待动作后直接结束，没有 `DONE` 或 `FAIL` 终态；12 个任务以 `FAIL` 结束，其中只有 3 个是代理明确调用 `agent.fail()`，另外 9 个的计划文本仍要求继续执行，却被记录成 `FAIL`，表现出动作解析或执行控制层的不一致。

## 4. 按用户群与任务类别统计

### 4.1 用户群

| 用户群 | 失败数 | 总数 | 失败率 |
|---|---:|---:|---:|
| cognitive | 24 | 49 | 48.98% |
| hearing | 31 | 50 | 62.00% |
| motor | 23 | 50 | 46.00% |
| visual | 29 | 49 | 59.18% |
| **合计** | **107** | **198** | **54.04%** |

听觉组和视觉组失败率最高。这两组通常还要求保持 Live Captions、Narrator、Magnifier 等辅助功能处于特定状态；即使主任务完成，只要辅助状态没有被评测确认，最终仍会失败。

### 4.2 任务类别

| 类别 | 失败数 | 总数 | 失败率 |
|---|---:|---:|---:|
| communication | 15 | 18 | 83.33% |
| consumption | 19 | 24 | 79.17% |
| information | 17 | 29 | 58.62% |
| mobility | 9 | 16 | 56.25% |
| service | 9 | 19 | 47.37% |
| management | 9 | 20 | 45.00% |
| health | 9 | 21 | 42.86% |
| access | 11 | 26 | 42.31% |
| captcha | 9 | 25 | 36.00% |

`communication` 和 `consumption` 是最薄弱的两类。前者通常涉及“读取来源 → 准确提取信息 → 创建邮件/联系人/日历 → 保存但不发送”等多阶段约束；后者通常涉及商品筛选、规格判断、数量、购物车状态以及同步更新本地记录，任何一个环节不符合都会使整体得分为 0。

## 5. 从评测分项看失败发生在哪里

`execution_log.json` 将结果拆为主任务结果 `task_outcome` 与辅助/无障碍要求 `access_requirement`。107 个失败任务的组合如下：

| 主任务 | 辅助要求 | 数量 | 含义 |
|---|---|---:|---|
| 失败 | 失败 | 79 | 主任务和辅助要求均未通过，或二者为同一要求且整体失败 |
| 失败 | 通过 | 18 | 辅助功能/交互要求满足，但核心任务未完成或结果不正确 |
| 通过 | 失败 | 10 | 核心任务完成，但指定的无障碍功能或辅助操作状态未满足 |

这 10 个“主任务通过、辅助要求失败”的样本尤其说明：仅验证邮件、计时器、路线、商品等业务结果不够，结束前还必须单独验证辅助功能的最终状态。它们包括：

- `cognitive/communication-library_program_reply`
- `hearing/consumption-sony_alpha`
- `hearing/information-laundry_tag_investigation`
- `hearing/information-maricopa_census_search`
- `hearing/management-double_dough_timer`
- `hearing/management-dryer_cycle_timer`
- `hearing/management-quick_sponge_timer`
- `hearing/mobility-opera_house_street_view`
- `hearing/mobility-walking_route_alhambra`
- `visual/consumption-saute_pan`

## 6. 失败原因分类

### 6.1 自报完成，但可评测状态不正确或未持久化（56 个）

这是最大的直接失败形态，占全部失败的 52.34%。日志最后是 `done_action`，但评测返回 0。

常见原因：

1. **把界面视觉反馈当作成功证据。** 例如看到开关呈蓝色、CAPTCHA 出现勾选或进度条、购物车角标为 1、编辑器没有未保存圆点，就直接结束；但评测读取的系统参数、页面状态或文件内容并不匹配。
2. **验证对象错位。** 代理验证了“页面已打开”“文本看起来存在”或“某个相邻设置已开启”，而评测检查的是精确的注册表/系统状态、特定字段、SKU、选项值或文件内容。
3. **保存与持久化不足。** LibreOffice、Thunderbird、Sticky Notes、日历等任务中，界面显示正确不等于最终文件、草稿或事件已被正确保存并可被评测读取。
4. **多条件任务漏项。** 主业务动作看似完成，但遗漏无障碍功能、指定应用、正确页面保持打开、草稿而非发送、准确数量、日期/时间/地点等附加条件。
5. **过度相信代码代理或自身复述。** 多个日志的最终说明非常肯定，但评测结果表明最终状态没有得到独立、机器可读的确认。

代表样本：

- `motor/access-enable_filter_keys`：多次点到展开箭头而不是开关；最终代理声称已开启，但系统级评测仍失败。
- `cognitive/access-windows_text_size_125`：代理把 Display Scale 125% 当成 Text Size 125%，目标设置发生混淆。
- `visual/captcha-robot_checkbox_2`、`visual/captcha-hold_button_2`：依据视觉成功提示直接结束，但 CAPTCHA 评测未通过。
- `visual/information-cat_image_alt_text`、`visual/information-invitation_image_alt_text`：声称替代文本已写入并保存，但文档评测不匹配。
- `cognitive/consumption-ginger_ale_note`、`cognitive/consumption-tomato_egg_stir_fry`：界面和代码代理均声称表格已更新，实际评测仍未读到完整目标状态。

### 6.2 达到 50 步上限，任务尚未收敛（23 个）

占全部失败的 21.50%。这些任务在第 50 步结束，且没有成功终态。

主要模式：

- 在同一页面反复滚动、定位或点击，缺少失败次数阈值和替代路径。
- 研究/侦察花费过多，直到最后几步才开始写文件、填表或提交。
- 代码代理调用给出分析或建议，但没有形成可评测的最终操作。
- 多应用任务没有按子目标逐项闭环，前面环节消耗过多步数，后续保存、提交或验证来不及完成。
- CAPTCHA 等精细视觉任务反复试错，缺少可靠的坐标校准和提交后反馈闭环。

达到步数上限的任务：

- cognitive：`captcha-audio_1`、`communication-library_program_reply`、`consumption-lowest_price_white_mouse`、`consumption-movie_night_shopping`、`service-cms_delete_obsolete_pickup_page`、`service-cms_import_service_product`、`service-cms_simplify_service_hours`、`service-cms_update_voyage_stock`
- hearing：`communication-community_class_registration`、`communication-meeting_action_items`、`communication-pharmacy_pickup_voicemail`、`health-long_covid_care_note`、`service-cms_update_access_desk_page_audio`
- motor：`captcha-slide_puzzle_1`、`communication-mouse_keys_equipment_update_email`、`consumption-shopping_list_cart`、`health-parkinsons_medication_reminders`、`health-sticky_keys_emergency_contact_card`
- visual：`captcha-patch_select_2`、`consumption-guest_bathroom_towel_holders`、`consumption-keto_bread`、`consumption-lavender_coupon`、`health-hospital_wayfinding_map`

### 6.3 日志在非终态中途停止（16 个）

占全部失败的 14.95%。最后一条记录仍是 `gui_action`、`code_action` 或 `wait_action`，总步数又小于 50；日志中没有完成或主动失败结论。只能从现有证据确认“运行未正常收尾”，无法仅凭日志进一步断言是超时、进程退出还是调度中断。

受影响任务：

- cognitive：`access-windows_notification_duration`、`communication-ftc_gift_card_pressure_email`、`health-doctor_appointment_preparation`、`management-prescription_refill_reminder`、`mobility-nih_after_hours_entry_note`
- hearing：`access-windows_mono_audio_screen_flash`、`communication-equipment_reimbursement_email`、`communication-passport_photo_checklist_email`、`consumption-insta360`、`consumption-order_substitution_audio`、`information-apartment_maintenance`、`information-ftc_2024_fraud_reports`、`information-ftc_florida_fraud_data`
- motor：`communication-meeting_agenda_draft`、`mobility-accessible_grade1_walks`
- visual：`captcha-click_sequence_2`

### 6.4 以 FAIL 结束：真实不可完成与动作不一致混在一起（12 个）

占全部失败的 11.21%。

其中 3 个是代理明确选择 `agent.fail()`：

- `hearing/access-windows_notification_5_minutes`：代理认为 Windows 11 没有可确认的 5 分钟通知显示设置，并否定了先前未经验证的注册表方案。
- `motor/captcha-patch_select_3`：多种网格选择均被拒绝，无法可靠判断船体覆盖格。
- `motor/captcha-slide_puzzle_3`：多种拖动和图像匹配方案仍被服务端拒绝，怀疑抓取锚点或反自动化检测问题。

另外 9 个存在明显的**计划—执行不一致**：最后的自然语言计划和 `plan_code` 仍是继续滚动、点击或按键，日志中的实际动作却成为 `FAIL`。这更像动作解析/控制层异常，而不是代理主动放弃：

- `cognitive/communication-ftc_gift_card_scam_email`
- `hearing/information-ftc_washington_q4_fraud`
- `motor/consumption-running_shoe_release_comparison`
- `motor/management-student_gradebook`
- `visual/access-chrome_zoom_150`
- `visual/access-windows_font_size_140`
- `visual/communication-add_contact`
- `visual/information-second_gold_rush`
- `visual/management-weekly_planner_calendar`

### 6.5 跨任务反复出现的根因

除上述可直接计数的终止形态外，从轨迹内容还能看到以下反复出现的行为根因。它们可能在同一任务中重叠，因此不做互斥计数。

#### A. 视觉定位与控件消歧不足

- 相邻的开关、展开箭头、按钮或放大后的控件容易点错。
- 代理虽然在反思中识别了误点击，却继续使用非常接近的坐标重复尝试。
- CAPTCHA 的网格边界、滑块锚点和细小目标对坐标误差敏感。

#### B. 缺少面向评测器的最终验证

- 完成声明常基于“看起来正确”，而不是读取最终系统参数、重新打开保存文件、检查准确 SKU/数量、查询草稿/日历记录等。
- 对合取评测任务，只验证了一个子条件；任一遗漏都会使总分归零。
- 代理的最终总结有时只是复述目标，并不能证明状态真的符合目标。

#### C. 长流程规划和步数管理较弱

- 搜索信息、浏览长 PDF/网页、填写邮件或日历、保存和验证串在一个任务中时，没有给每个阶段预留步数。
- 对已经连续失败的策略切换过晚。
- 在接近 50 步时仍执行探索性动作，而不是优先完成最小可评测闭环。

#### D. 多应用状态与保存语义处理不稳

- 浏览器、Office、Thunderbird、Sticky Notes、Windows Settings 之间切换时容易丢失焦点或混淆当前窗口。
- “保存”“另存为”“保存草稿”“保存并关闭”“自动保存”被当作相同语义，容易导致文件路径、格式或对象状态不符合评测。
- 日期、时间、全天事件、重复规则、收件人、主题等结构化字段容易出现局部正确但整体失败。

#### E. 辅助功能被遗漏、设置错误或未保持

- 主任务完成后，没有重新确认 Narrator、Magnifier、Live Captions、Mouse Keys、Filter Keys 等是否仍处于要求状态。
- 存在相似设置混淆，例如 Display Scale 与 Text Size、Filter Keys 的不同子开关。
- 10 个任务明确表现为主任务通过但辅助要求失败。

#### F. 研究结果到最终动作之间缺少闭环

- 代理能找到来源或通过代码代理提取内容，但没有及时把结果写入指定应用/文件。
- 商品任务中能找到候选项，却没有完成精确规格选择、加购、数量设置和本地清单更新的全部步骤。
- CMS 任务中花费大量步骤确认页面或字段，但未在步数内保存最终更改。

## 7. 改进优先级

1. **增加结束前的机器可读验证。** 对设置读取系统状态，对文档重新打开并读取目标字段，对购物车检查 SKU、选项和数量，对邮件/日历确认对象已持久化；验证失败不得调用 `done()`。
2. **把主任务和辅助要求拆成独立检查项。** 最终验证必须分别覆盖 `task_outcome` 和 `access_requirement`，尤其关注 hearing、visual 任务。
3. **修复 `plan_code` 与实际 `FAIL` 的控制层不一致。** 9 个任务不是计划主动失败却被记录为 `FAIL`，应优先检查动作解析、异常映射和 runner 终止逻辑。
4. **为重复失败设置硬阈值。** 同一控件或同一路径连续失败 2–3 次后，必须切换为键盘导航、搜索、DOM/系统查询或其他可验证路径。
5. **引入步数预算。** 复杂任务预留最后 20%–30% 步数用于写入、保存和最终验证；接近上限时停止无界探索。
6. **对多应用任务采用子目标提交。** 每完成一个阶段立即保存并验证，避免最后统一提交导致状态丢失。
7. **加强精确字段和持久化语义。** 对日期时间、邮件草稿、文件格式、保存路径、商品规格等使用结构化核对表，避免“内容大致正确但评测失败”。

## 8. 一句话总结

该批次最重要的 accessibility 结论是：**89/107 个失败没有满足 need-conditioned handoff，其中 47 个仍被代理自报为完成；另有 18 个任务虽然建立了辅助状态，却没有正确完成实际工作。** 这表明主要限制不是代理是否“使用”辅助技术，而是能否完整采集并转移证据、构造可信的用户支持 artifact、精确保持 continuation state，并在 `done()` 前诚实验证全部 handoff contract。
