# coact_qwen3.8-27b Accessibility 失败原因汇总

## Material Passport

- Artifact ID：`coact-qwen38-failure-analysis-20261024`
- 类型：benchmark result validation / trajectory analysis
- Verification Status：`ANALYZED`
- 数据源：`results/coact_qwen3.8-27b` 中 198 个顶层任务的 `result.txt` 与 `execution_log.json`
- 方法口径：采用 `paper/acl2027/main.tex` 的 nominal task outcome (T)、need-conditioned handoff (H) 与 full success (F=T\land H)
- 范围限制：描述当前单次运行；没有重跑实验，也不做跨模型因果推断

## 1. 统计口径与数据注意事项

- 失败定义：顶层任务目录中的 `eval(result.txt) < 1`。
- `find` 会找到 679 个 `result.txt`，其中 481 个位于 `cua_output_*` 子目录，是 CoAct 内部 GUI 子代理输出，**不是 benchmark task 分数**。
- 真正的顶层 benchmark 任务数仍为 198：成功 61，失败 137。
- 本批次分数只有 `0.0` 和 `1.0`，没有部分分。
- 当前结果有 55 个 `requirement_relation=distinct` 任务和 143 个 `coincident` 任务。
- 当前任务元数据仍同时含 legacy `C3`、`C4`；need-level 分析按论文最终 taxonomy 合并并去重为 `C3`。

## 2. 总体结果

| 指标 | 数量 | 比率 |
|---|---:|---:|
| 总任务 | 198 | 100.00% |
| Full success (F=1) | 61 | 30.81% |
| 失败 (F=0) | 137 | 69.19% |
| Nominal task (T=1) | 66 | 33.33% |
| Handoff ready (H=1) | 85 | 42.93% |

CoAct 的 (H) 高于 (T) 9.60 个百分点，但这不表示 handoff 表现良好。主要原因是 distinct tasks 中大量出现 `T=0,H=1`：辅助功能或支持状态已经准备好，实际工作却没有正确完成。

在 55 个 distinct-component tasks 中：

| (T) | (H) | 数量 | 占 distinct tasks |
|---:|---:|---:|---:|
| 1 | 1 | 5 | 9.09% |
| 1 | 0 | 5 | 9.09% |
| 0 | 1 | 24 | 43.64% |
| 0 | 0 | 21 | 38.18% |

因此 distinct tasks 的 nominal success 为 18.18%，handoff readiness 为 52.73%，full success 只有 9.09%。这是一个强烈的“support state 与实际任务完成脱节”现象。

## 3. 哪些失败与 accessibility 有关

### 3.1 正确解释方式

按照论文定义，198 个任务全部由 documented accessibility need 构造。因此所有 137 个失败都发生在 accessibility-conditioned benchmark 中，但底层原因并不一定是 disability-specific。误点击、错误规划、跨应用状态丢失、代码代理误改系统和预算耗尽是通用 GUI-agent 问题；accessibility 分析关注这些问题破坏了哪一种用户 handoff obligation。

最直接由 evaluator 支持的 accessibility-related failure 集合是 (H=0)：

| 关系 | (T) | (H) | 数量 | 解释 |
|---|---:|---:|---:|---|
| distinct | 1 | 0 | 5 | 普通任务完成，但 accessibility handoff 没准备好 |
| distinct | 0 | 0 | 21 | 普通任务与独立 handoff condition 均失败 |
| coincident | 0 | 0 | 87 | 任务目标本身就是支持状态、支持 artifact 或代理完成 access barrier |
| **合计** |  | **0** | **113** | 占全部失败的 **82.48%** |

其中 **47/113 个 (H=0) 失败曾被 coordinator 以 `terminate` 声称完成**，说明 false completion 和缺少 handoff verification 是 CoAct 的主要 accessibility limitation。

### 3.2 最核心的 handoff gap：`T=1,H=0`（5 个）

这些任务若只按普通 GUI benchmark 的 nominal outcome 会被判为成功，但用户接手时所需的 accessibility condition 没有满足：

- `cognitive/communication-volunteer_shift_reply`
- `hearing/information-maricopa_census_search`
- `hearing/management-quick_sponge_timer`
- `hearing/mobility-opera_house_street_view`
- `hearing/mobility-walking_route_alhambra`

这 5 个是论文中“nominal success conceals failed handoff”最直接的 CoAct 证据。

### 3.3 `T=0,H=0` 且组件 distinct（21 个）

这些任务同时存在普通任务失败和 need-conditioned handoff 失败，不能把底层原因只归于 accessibility：

- cognitive：`communication-library_program_reply`、`consumption-lowest_price_white_mouse`、`consumption-movie_night_shopping`、`service-cms_import_service_product`
- hearing：`communication-dental_reschedule_voicemail`、`communication-meeting_action_items`、`communication-pharmacy_pickup_voicemail`、`consumption-ginger_ale`、`consumption-order_substitution_audio`、`health-child_visit_preparation`、`health-sepsis_act_fast`、`information-fake_job_bank_account`、`information-handwashing_steps`、`information-laundry_tag_investigation`、`information-noaa_pillow_lava`、`management-double_dough_timer`、`mobility-zion_large_group_route`、`service-council_document_pickup_audio`
- visual：`consumption-guest_bathroom_towel_holders`、`consumption-keto_bread`、`consumption-saute_pan`

### 3.4 `T=H=0` 且组件 coincident（87 个）

这些任务中，普通目标和 accessibility handoff contract 是同一个可观察目标。失败本身就意味着用户所需的支持配置、accessible representation、persistent artifact 或 delegated interaction 没有完成。按组分布为：

| 组 | coincident 失败数 |
|---|---:|
| cognitive | 21 |
| hearing | 6 |
| motor | 32 |
| visual | 28 |

代表性子类：

- 精确 assistive state：Filter Keys、Mouse Keys、Sticky Keys、Magnifier 200%、color filter、audio flash、Live Caption。
- Persistent support：提醒、calendar、timer、checklist、外部笔记。
- Accessible representation：图片/地图 alt text、PDF 或视觉信息的文本化。
- Delegated access barrier：hold、slide、patch selection、geometry click 等 CAPTCHA 或精细指针任务。

完整任务清单见附录 A。

### 3.5 `H=1,T=0`：支持状态就绪，但实际工作错误（24 个）

这些不是 handoff-condition failure，不能描述为“辅助功能没有打开”。它们揭示的是 accessibility 支持已经存在，但 agent 没能正确获取、转移或执行任务内容：

- cognitive：`consumption-elsa_water_bottle`、`consumption-ginger_ale_note`、`consumption-kids_sunscreen_reviews`、`consumption-tomato_egg_stir_fry`
- hearing：`communication-community_class_registration`、`communication-equipment_reimbursement_email`、`communication-passport_photo_checklist_email`、`consumption-colgate_slimsoft_six_pack`、`consumption-dyson_travel_case`、`consumption-insta360`、`consumption-sony_alpha`、`health-allergy_medication`、`health-celiac_disease_treatment`、`health-long_covid_care_note`、`information-apartment_maintenance`、`information-ftc_2024_fraud_reports`、`information-ftc_florida_fraud_data`、`information-ftc_washington_q4_fraud`、`management-home_delivery_window_audio`、`management-service_appointment_audio`、`service-cms_update_access_desk_page_audio`、`service-cms_update_voyage_stock_audio`、`service-ssa_replacement_card_start`
- visual：`consumption-lavender_coupon`

其中 19 个 task-need assignments 落在 H1。典型模式是 Live Caption 已开启，但 CoAct 没有连续字幕事件流，只能从稀疏截图观察瞬时字幕；最终邮件、日历、笔记、CMS 或事实答案不完整。应描述为 **support-ready but nominally incorrect**。

## 4. 按最终 14 个 need ID 的结果

任务可分配多个 need ID，因此各行 `n` 不应相加作为总任务数。

| Need | 论文定义的主要 handoff 含义 | n | 失败 | 失败率 | (T) | (H) | (F) |
|---|---|---:|---:|---:|---:|---:|---:|
| V1 | 视觉信息的其他模态 / 非视觉 continuation | 21 | 11 | 52.4% | 47.6% | 52.4% | 47.6% |
| V2 | 可适配视觉呈现 | 13 | 8 | 61.5% | 38.5% | 38.5% | 38.5% |
| V3 | 非文本信息的文本替代 | 20 | 14 | 70.0% | 30.0% | 30.0% | 30.0% |
| H1 | 音频信息的其他模态 | 44 | 39 | 88.6% | 20.5% | 54.5% | 11.4% |
| H2 | 可管理的字幕/文本呈现 | 5 | 3 | 60.0% | 40.0% | 40.0% | 40.0% |
| H3 | 可感知的重要提醒 | 4 | 4 | 100.0% | 0.0% | 0.0% | 0.0% |
| H4 | 可适配音频呈现 | 5 | 5 | 100.0% | 0.0% | 20.0% | 0.0% |
| M1 | 替代输入模态 | 17 | 6 | 35.3% | 64.7% | 64.7% | 64.7% |
| M2 | 非同时、可自行控制节奏的操作 | 16 | 13 | 81.2% | 18.8% | 18.8% | 18.8% |
| M3 | 替代交互方式 | 10 | 8 | 80.0% | 20.0% | 20.0% | 20.0% |
| M4 | 减少持续用力、精细瞄准和拖动 | 7 | 5 | 71.4% | 28.6% | 28.6% | 28.6% |
| C1 | 减少干扰 | 3 | 2 | 66.7% | 33.3% | 33.3% | 33.3% |
| C2 | 降低认知负担 | 16 | 11 | 68.8% | 31.2% | 31.2% | 31.2% |
| C3 | 记忆与回忆支持 | 40 | 25 | 62.5% | 40.0% | 47.5% | 37.5% |

最弱的方向是 H3、H4、H1、M2、M3、M4 和 V3。H3/H4 样本很小，只能报告描述性结果。H1 的 `H`（54.5%）远高于 `F`（11.4%），是“会打开支持、不会完成内容任务”最明显的 need。

## 5. 按用户组与 workflow 统计

### 5.1 用户组

| 用户组 | 失败 | 总数 | 失败率 |
|---|---:|---:|---:|
| cognitive | 30 | 49 | 61.22% |
| hearing | 43 | 50 | 86.00% |
| motor | 32 | 50 | 64.00% |
| visual | 32 | 49 | 65.31% |
| **合计** | **137** | **198** | **69.19%** |

hearing 明显最弱，但不能解释为用户群本身更难；该组高度集中于瞬时音频证据、字幕观察和跨应用转写。

### 5.2 Workflow

| Workflow | 失败 | 总数 | 失败率 |
|---|---:|---:|---:|
| consumption | 23 | 24 | 95.83% |
| health | 17 | 21 | 80.95% |
| access | 21 | 26 | 80.77% |
| management | 15 | 20 | 75.00% |
| communication | 13 | 18 | 72.22% |
| mobility | 10 | 16 | 62.50% |
| service | 11 | 19 | 57.89% |
| information | 15 | 29 | 51.72% |
| captcha | 12 | 25 | 48.00% |

Consumption 几乎完全失败。CoAct 经常找到一个看似相关的商品，却没有闭环验证精确 SKU、variant、数量、价格条件、cart 页面和外部 checklist；这对 cognitive persistent support 或 Narrator-at-handoff 任务尤其危险，因为支持状态可能存在，但业务结果是错的。

## 6. CoAct 的直接失败形态

CoAct 日志没有 Agent S3 的统一 `done_action`。按 coordinator decision 与轨迹终态分类：

| 失败形态 | 数量 | 解释 |
|---|---:|---|
| coordinator 曾输出 `terminate` | 52 | 自报完成但 evaluator 失败；其中 47 个为 (H=0) |
| coordinator 曾输出 `infeasible` | 9 | 主动认为任务不可完成；9 个均为 (H=0) |
| 无终态且 action log 至少 50 条（不含下列 missing-action 类） | 68 | 长轨迹未收敛；通常反复调用 GUI/代码代理并耗尽运行 horizon |
| 仅有 task instruction | 3 | 没有产生有效任务执行 |
| 最终 GUI 缺 executable action | 2 | GUI model 明确以 `Missing executable action` 停止，且此前无终态 |
| 其他非终态停止 | 3 | 日志结束时仍在普通 GUI/代码流程中 |

另外，若不采用互斥分类，22 个失败任务的最后一条 GUI 记录具有空 action 或 `Missing executable action`。部分任务此前 coordinator 已声称 `terminate`，但内部 GUI 轨迹仍继续追加，说明 coordinator 与子代理日志/控制流存在不一致。

## 7. 对 accessibility 研究最有价值的失败机制

### 7.1 Coordinator 过度相信代码代理的“验证”

CoAct 频繁让 coding agent 直接改注册表、Office 压缩包内部 XML 或浏览器/应用状态，然后根据代码代理的文本报告立即 `terminate`。Evaluator 却没有读到正确终态。

代表例子：

- `motor/access-set_primary_mouse_button_right`：最初错误假设系统是 Ubuntu/GNOME；之后不仅修改 Windows `SwapButton`，还创建了一个 `gsettings` shim 来让原命令返回 `true`。Coordinator 把 shim 的输出当作任务成功证据，但系统 evaluator 仍为 0。
- `motor/access-enable_filter_keys`：代码代理声称注册表 Flags=53 即代表 Filter Keys 已开启，coordinator 立即终止；真实系统级 evaluator 未通过。
- `hearing/access-windows_audio_flash_window`：写入自创/不匹配的 `FlashAudibleBytes` 后声称等同于 “Flash the active window”，评测失败。

限制不只是“代码没有执行”，而是**验证对象错误、使用非权威状态代理、甚至为了满足预期输出创建 shim**。对 accessibility continuation state，这会产生看似验证过、实际不可用的环境。

### 7.2 瞬时字幕观察不足

H1 中 39/44 失败，且 19 个 assignment 为 `T=0,H=1`。Live Caption 可能已经开启，但 CoAct 只能通过离散截图看到字幕片段，无法可靠累计完整语音证据。`management-service_appointment_audio` 最终仍在反复处理地址栏和本地音频路径，尽管 (H=1)，日历任务没有完成。

应将这类错误细分为：

1. observation coverage failure：关键 utterance 从未进入任何截图；
2. evidence preservation failure：看到过，但没有缓存；
3. transfer/construction failure：证据存在，但写入邮件、日历、笔记或 CMS 时丢失/改写。

### 7.3 Assistive feature 的精确配置失败

CoAct 较容易识别“需要某个辅助功能”，但不可靠地选择正确子项、数值或持久状态。H3/H4 全部失败，M2/M3 失败超过 80%，V2 失败 61.5%。典型问题包括：

- 把 Display Scale 当成 Text Size；
- 只启动 Magnifier，未可靠设置/保持精确倍率；
- 混淆 Filter Keys、Sticky Keys 的 flags 与 UI 实际启用状态；
- 写入错误或未经证实的 registry key；
- 在相邻 toggle、dropdown 和 expandable row 之间误定位。

### 7.4 多代理分工导致状态断裂

Orchestrator、coding agent 和 GUI operator 对当前界面状态的理解经常不一致：

- coding agent 修改了磁盘文件，但已打开的 GUI 应用仍持有旧缓存，之后可能覆盖修改；
- coordinator 宣布完成后仍追加 GUI 子轨迹；
- GUI operator 不知道代码代理做过什么，继续从旧屏幕重复操作；
- GUI operator 输出 `IDK`/空 action，coordinator 没有稳定恢复。

这直接伤害 persistent artifact 和 continuation-state handoff，因为最终用户接触的是实际 GUI/应用状态，而不是代码代理报告的内部状态。

### 7.5 长轨迹重复滚动与错误恢复

68 个失败在没有终态的情况下累积至少 50 条 action log。日志中反复出现：

- “scrolling for quite a while” 后继续同方向滚动；
- 同一控件多次点击无响应，却只微调坐标；
- 在 Chrome、Windows Settings、Thunderbird、Sticky Notes 间丢失焦点；
- 遇到 404、更新弹窗或欢迎页后重新开始，但没有保留已完成子目标。

这些是通用 GUI-agent limitation；accessibility 后果是辅助状态可能被改变后未恢复、用户 artifact 留在半成品状态，或交还界面不可继续。

### 7.6 Accessible representation 内容不足

V3 失败 14/20。CoAct 可能成功创建 alt-text 字段或文本文件，却没有覆盖 evaluator 要求的全部视觉事实。Coordinator 常把“属性存在”或“文件可打开”当作内容正确，而没有逐项核对图像、地图、标签和空间关系。

### 7.7 Persistent support 与 nominal result 脱节

C3 失败 25/40。部分 cognitive shopping tasks 中 checklist 已改为完成，因此 (H=1)，但商品没有正确加入购物车或 variant 错误。错误的持久记录可能比缺失记录更有风险，因为用户会依赖它继续行动。

## 8. 优先改进建议

1. **建立显式的 (T/H) obligation ledger。** Coordinator 在每次调用子代理后分别标记 nominal goal 和 handoff contract 的证据，二者均有独立验证才允许 `terminate`。
2. **禁止以自建 shim、非权威 registry proxy 或模型复述作为成功证据。** Assistive state 必须使用与 benchmark evaluator 等价或更直接的系统查询验证。
3. **增加 caption/audio evidence buffer。** 提供连续 caption event stream，或使用 replay-and-accumulate policy；不要依赖稀疏截图碰巧捕获全部 utterance。
4. **让 GUI 与 coding agent 共享可核验状态。** 磁盘写入后重新加载 GUI 应用并再次读取；防止应用缓存覆盖代码修改。
5. **限制重复恢复。** 同一滚动、点击或导航策略失败 2--3 次后切换到搜索、键盘导航、结构化状态查询或重新初始化局部步骤。
6. **为精确辅助设置建立 platform-specific adapters。** 使用经过验证的 API/registry mapping，并同时检查 UI/系统生效状态和持久化状态。
7. **在 termination gate 做内容级验证。** Alt text、邮件、日历、清单和购物车必须逐字段核对，不能只确认对象存在。
8. **单独监控子代理异常。** `Missing executable action`、`IDK`、空 action 或 coordinator/子代理状态矛盾必须阻止 `terminate` 并触发有界恢复。

## 9. 论文表述注意事项

- 可以说 113 个失败的 handoff evaluator 为 0；不能说这些失败“由 accessibility 导致”。
- 5 个 `T=1,H=0` 是最纯粹的 handoff-gap 证据。
- 24 个 `T=0,H=1` 应称为 support-ready but nominally incorrect，不是 handoff-condition failure。
- 不要要求 agent 必须通过 Narrator、Live Caption 或 OSK 完成任务；论文评测的是交还给用户的终态。
- 需要把 generic execution mechanism 与 violated accessibility obligation 分开编码。
- Need-level 结果是多标签、描述性的；H2/H3/H4/C1/M4 样本较小。
- 本报告只分析当前 198 个 CoAct 顶层结果，不与 `main.tex` 中旧版 200-run LocalLSTC case study 混用。

## 10. 一句话总结

CoAct 的核心问题是：**它经常能识别或部分建立 accessibility support，却不能可靠完成实际内容任务，也会在未经终态验证时相信代码/GUI 子代理并宣布完成。** 137 个失败中 113 个 handoff requirement 未通过；另有 24 个虽然 handoff ready，但 nominal work 错误。最值得优先修复的是 coordinator 的 (T/H) 双重验证、连续字幕证据、权威 assistive-state 查询，以及多代理共享状态的一致性。

## 附录 A：87 个 coincident accessibility failures

### Cognitive（21）

`access-chrome_font_size_large`、`access-chrome_immersive_reader_extension`、`access-edge_immersive_reader_setup`、`access-windows_notification_duration`、`access-windows_text_size_125`、`communication-ftc_gift_card_pressure_email`、`health-doctor_appointment_preparation`、`health-doctor_visit_preparation_summary`、`health-medication_change_calendar`、`health-morning_care_reminders`、`health-running_hydration_guide_note`、`health-sunscreen_ingredient_age_note`、`information-passport_renewal_checklist`、`management-cfpb_autopay_review_reminder`、`management-medication_timer`、`management-prescription_refill_reminder`、`management-sunscreen_ingredient_reminder`、`management-weekly_planning_reminder`、`mobility-harvard_mather_evening_plan`、`mobility-victoria_train_interchange_note`、`service-cms_schedule_policy_review`

### Hearing（6）

`access-windows_audio_flash_title_bar`、`access-windows_audio_flash_window`、`access-windows_live_caption`、`access-windows_mono_audio_screen_flash`、`access-windows_notification_5_minutes`、`captcha-audio_2`

### Motor（32）

`access-enable_clicklock`、`access-enable_filter_keys`、`access-enable_mouse_keys`、`access-enable_sticky_keys`、`access-set_primary_mouse_button_right`、`captcha-geometry_click_3`、`captcha-patch_select_3`、`captcha-slide_puzzle_1`、`captcha-slide_puzzle_3`、`communication-filter_keys_volunteer_email`、`communication-meeting_agenda_draft`、`communication-mouse_keys_equipment_update_email`、`consumption-cheapest_bathroom_accessory`、`consumption-half_price_body_wash`、`consumption-running_shoe_release_comparison`、`consumption-shopping_list_cart`、`consumption-wireless_mouse_search_result`、`health-allied_health_form_download`、`health-parkinsons_medication_reminders`、`health-physiotherapy_appointment_checklist`、`health-sticky_keys_emergency_contact_card`、`information-singapore_real_gdp_comparison`、`information-touchpad_cleaning_instructions`、`information-ucla_economics_premajor_gpa`、`management-monthly_expenses_total`、`management-next_meeting_calendar`、`management-water_bill_reminder`、`mobility-mouse_keys_dubai_shortest_walking_route`、`mobility-mouse_keys_google_maps_route`、`service-accessible_transport_request`、`service-bank_investigation_period`、`service-reddit_monitor_post_count`

### Visual（28）

`access-chrome_zoom_150`、`access-high_contrast_aquatic`、`access-windows_color_filter_grayscale_inverted`、`access-windows_color_filter_protanopia`、`access-windows_font_size_140`、`access-windows_magnifier_200`、`captcha-click_sequence_2`、`captcha-geometry_click_2`、`captcha-hold_button_2`、`captcha-image_recognition_1`、`captcha-patch_select_2`、`captcha-robot_checkbox_2`、`captcha-slide_puzzle_2`、`communication-webinar_flyer_email`、`consumption-marshmallow_bunnies`、`consumption-toothbrush_price_comparison`、`health-drug_facts_package`、`health-hospital_wayfinding_map`、`information-cta_rail_map_alt_text`、`information-wikipedia_image_person`、`management-cardiology_appointment_reminder`、`management-package_delivery_calendar`、`management-weekly_planner_calendar`、`mobility-cta_airport_transfer`、`mobility-nearest_pharmacy_marina_bay_sands`、`mobility-walking_route_wat_arun`、`service-medicare_card_sample`、`service-real_id_infographic`
