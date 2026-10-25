# locallstc_qwen3.8-27b Accessibility 失败原因汇总

## Material Passport

- Artifact ID：`locallstc-qwen38-failure-analysis-20261025`
- 类型：benchmark result validation / trajectory analysis
- Verification Status：`ANALYZED`
- 数据源：`results/locallstc_qwen3.8-27b` 的 198 个顶层 `result.txt` 与 `execution_log.json`
- 方法口径：`paper/acl2027/main.tex` 中的 nominal task outcome (T)、need-conditioned handoff (H) 与 full success (F=T\land H)
- 范围限制：描述当前单次运行；未重跑实验，不做跨模型因果推断

## 1. 统计口径与版本对齐

- 失败定义：顶层任务目录中的 `eval(result.txt) < 1`。
- 总任务数：198；成功 110；失败 88。
- 分数只有 `0.0` 和 `1.0`，不存在部分分。
- 当前结果包含 55 个 `distinct` tasks 和 143 个 `coincident` tasks。
- `execution_log.json` 保存的是较旧的 need taxonomy，包含 `V5/V6/H5/M5--M7/C4` 等旧标签。为与论文最终 14-ID taxonomy 对齐，本报告按 task ID 连接当前 `src/win-arena-container/client/evaluation_examples_windows/examples` 元数据，再计算 need-level 结果；198 个任务均成功匹配，其中 89 个任务的 need 标注已相对日志快照更新。
- `main.tex` 附录仍写 200 runs、112 successes、51 distinct tasks。本报告不复制旧数字，而是完全按当前 198 个结果重新计算。

## 2. 总体结果

| 指标 | 数量 | 比率 |
|---|---:|---:|
| 总任务 | 198 | 100.00% |
| Full success (F=1) | 110 | 55.56% |
| 失败 (F=0) | 88 | 44.44% |
| Nominal task (T=1) | 115 | 58.08% |
| Handoff ready (H=1) | 128 | 64.65% |

Handoff readiness 比 nominal task success 高 6.57 个百分点，主要是因为 18 个任务出现 `T=0,H=1`：辅助状态或支持 artifact 已满足，但实际业务结果错误。

在 55 个 distinct-component tasks 中：

| (T) | (H) | 数量 | 占 distinct tasks |
|---:|---:|---:|---:|
| 1 | 1 | 20 | 36.36% |
| 1 | 0 | 5 | 9.09% |
| 0 | 1 | 18 | 32.73% |
| 0 | 0 | 12 | 21.82% |

Distinct tasks 的 nominal success 为 45.45%，handoff readiness 为 69.09%，full success 为 36.36%。这说明 LocalLSTC 建立支持状态的能力明显强于完成与该状态配套的实际内容任务。

## 3. 哪些失败与 accessibility 有关

### 3.1 正确解释方式

按照论文定义，198 个任务全部由 documented accessibility need 构造，所以 88 个失败都发生在 accessibility-conditioned benchmark 中。但不能把每个误点击、OCR 错误、步数耗尽或跨应用导航失败称为 disability-specific mechanism。应分别记录：

1. generic execution cause；
2. 被破坏的 accessibility handoff obligation。

最直接的 accessibility-related failure 集合是 evaluator 给出 (H=0) 的 70 个任务：

| 关系 | (T) | (H) | 数量 | 解释 |
|---|---:|---:|---:|---|
| distinct | 1 | 0 | 5 | 普通任务完成，但 handoff requirement 未满足 |
| distinct | 0 | 0 | 12 | 普通任务和独立 handoff requirement 均失败 |
| coincident | 0 | 0 | 53 | 任务本身就是支持状态、支持 artifact 或 delegated access barrier |
| **合计** |  | **0** | **70** | 占全部失败的 **79.55%** |

其中 **43/70 个 (H=0) 任务由 agent 主动 `finish`**，没有在终止前发现 handoff 不正确。False completion 是最显著、覆盖范围最大的 accessibility limitation。

### 3.2 最核心的 handoff gap：`T=1,H=0`（5 个）

这些任务如果只按普通 GUI benchmark 的 nominal outcome 会被判成功，但用户所需的 handoff state 没有留下：

- `hearing/information-handwashing_steps`
- `hearing/information-maricopa_census_search`
- `hearing/management-quick_sponge_timer`
- `visual/consumption-lavender_coupon`
- `visual/consumption-saute_pan`

这是 LocalLSTC 最直接的“nominal success conceals failed handoff”证据。

### 3.3 `T=0,H=0` 且组件 distinct（12 个）

- cognitive：`consumption-movie_night_shopping`、`consumption-tomato_egg_stir_fry`、`service-cms_import_service_product`
- hearing：`communication-community_class_registration`、`communication-equipment_reimbursement_email`、`communication-meeting_action_items`、`consumption-colgate_slimsoft_six_pack`、`health-anaphylaxis_medicine`、`information-ftc_2024_fraud_reports`、`mobility-opera_house_street_view`、`mobility-walking_route_alhambra`
- visual：`consumption-keto_bread`

这组同时包含 generic task failure 和 accessibility handoff failure，不能只用一个标签概括。

### 3.4 `T=H=0` 且组件 coincident（53 个）

在 coincident tasks 中，accessibility support 本身就是任务结果，例如设置辅助功能、创建 persistent memory artifact、生成文本替代或代替用户完成精细交互。按用户组分布为：

| 用户组 | coincident 失败数 |
|---|---:|
| cognitive | 8 |
| hearing | 2 |
| motor | 23 |
| visual | 20 |

完整清单见附录 A。

### 3.5 `H=1,T=0`：支持状态就绪，但实际工作错误（18 个）

这些任务的 handoff condition 已通过，不能称为“辅助功能未启用”。问题是内容获取、选择、转移或业务结果错误：

- cognitive：`communication-library_program_reply`、`consumption-elsa_water_bottle`、`consumption-ginger_ale_note`、`consumption-kids_sunscreen_reviews`、`consumption-lowest_price_white_mouse`
- hearing：`communication-dental_reschedule_voicemail`、`consumption-order_substitution_audio`、`consumption-sony_alpha`、`health-child_visit_preparation`、`health-long_covid_care_note`、`information-ftc_florida_fraud_data`、`information-ftc_washington_q4_fraud`、`information-noaa_pillow_lava`、`management-home_delivery_window_audio`、`management-service_appointment_audio`、`service-cms_update_access_desk_page_audio`、`service-council_document_pickup_audio`
- visual：`consumption-guest_bathroom_towel_holders`

这组应表述为 **support-ready but nominally incorrect**。它特别暴露两种风险：

- caption/Narrator/checklist 状态已经准备好，但实际事实、邮件、日历、商品或 CMS 操作错误；
- persistent support artifact 可能被更新为“Done”，却记录了错误业务结果，使用户后续依赖一个自信但不准确的外部记忆。

## 4. 按最终 14 个 need ID 的结果

任务可分配多个 need ID，因此各行样本数不能相加作为总任务数。

| Need | 主要 handoff 含义 | n | 失败 | 失败率 | (T) | (H) | (F) |
|---|---|---:|---:|---:|---:|---:|---:|
| V1 | 视觉信息的其他模态 / 非视觉 continuation | 21 | 11 | 52.4% | 57.1% | 52.4% | 47.6% |
| V2 | 可适配视觉呈现 | 13 | 5 | 38.5% | 61.5% | 61.5% | 61.5% |
| V3 | 非文本信息的文本替代 | 20 | 9 | 45.0% | 55.0% | 55.0% | 55.0% |
| H1 | 音频信息的其他模态 | 44 | 23 | 52.3% | 54.5% | 75.0% | 47.7% |
| H2 | 可管理的字幕/文本呈现 | 5 | 2 | 40.0% | 60.0% | 80.0% | 60.0% |
| H3 | 可感知的重要提醒 | 4 | 2 | 50.0% | 50.0% | 50.0% | 50.0% |
| H4 | 可适配音频呈现 | 5 | 3 | 60.0% | 40.0% | 100.0% | 40.0% |
| M1 | 替代输入模态 | 17 | 3 | 17.6% | 82.4% | 82.4% | 82.4% |
| M2 | 非同时、可自行控制节奏的操作 | 16 | 10 | 62.5% | 37.5% | 37.5% | 37.5% |
| M3 | 替代交互方式 | 10 | 5 | 50.0% | 50.0% | 50.0% | 50.0% |
| M4 | 减少持续用力、精细瞄准和拖动 | 7 | 5 | 71.4% | 28.6% | 28.6% | 28.6% |
| C1 | 减少干扰 | 3 | 1 | 33.3% | 66.7% | 66.7% | 66.7% |
| C2 | 降低认知负担 | 16 | 6 | 37.5% | 62.5% | 62.5% | 62.5% |
| C3 | 记忆与回忆支持 | 40 | 12 | 30.0% | 70.0% | 82.5% | 70.0% |

主要薄弱方向为 M4、M2、H4、H1、V1、M3/H3。H2、H3、H4、C1、M4 样本较少，只能作为当前系统的描述性结果。H1 和 C3 的 (H) 明显高于 (T/F)，说明 LocalLSTC 比较擅长留下 caption 或 persistent-support 状态，但无法保证其承载的内容/业务结果正确。

## 5. 按用户组与 workflow 统计

### 5.1 用户组

| 用户组 | 失败 | 总数 | 失败率 |
|---|---:|---:|---:|
| cognitive | 16 | 49 | 32.65% |
| hearing | 25 | 50 | 50.00% |
| motor | 23 | 50 | 46.00% |
| visual | 24 | 49 | 48.98% |
| **合计** | **88** | **198** | **44.44%** |

Hearing、visual 和 motor 较弱，但这反映其 handoff mechanisms 与 workflow mix，不应解释为用户群本身更难或能力更低。

### 5.2 Workflow

| Workflow | 失败 | 总数 | 失败率 |
|---|---:|---:|---:|
| consumption | 20 | 24 | 83.33% |
| mobility | 10 | 16 | 62.50% |
| information | 13 | 29 | 44.83% |
| communication | 8 | 18 | 44.44% |
| health | 8 | 21 | 38.10% |
| management | 7 | 20 | 35.00% |
| access | 9 | 26 | 34.62% |
| service | 6 | 19 | 31.58% |
| captcha | 7 | 25 | 28.00% |

失败高度集中于 consumption 和 mobility。商品比较需要保持 SKU、variant、价格、数量、cart 与外部记录一致；mobility 需要可靠识别地图空间关系和路线段。这些是通用视觉/规划难点，但当生成结果用于替代用户无法直接检查的视觉信息或支撑记忆时，其 accessibility 后果更严重。

## 6. 直接终止形态

LocalLSTC 日志提供了明确的终止和失败字段，88 个失败可互斥分为：

| 失败形态 | 数量 | 占失败 | 解释 |
|---|---:|---:|---|
| Agent 主动 `finish`，评测失败 | 52 | 59.09% | False completion；其中 43 个为 (H=0) |
| 达到 50 步上限 | 22 | 25.00% | 长流程未完成或恢复过慢 |
| 连续 3 次 stall 后停止 | 12 | 13.64% | 同一路径无法产生有效进展 |
| 判定环境 infeasible | 2 | 2.27% | Live Caption 无音频设备；MedlinePlus DNS 失败 |

达到 50 步的任务集中在复杂购物、CMS、字幕信息提取、CAPTCHA、精确设置和 mobility 工作流；stall 则经常来自反复点击、滚动、页面控件不可定位或跨应用焦点丢失。

## 7. 对 accessibility 研究最有价值的失败机制

### 7.1 瞬时字幕证据未被完整观察和保存

H1 中 23/44 失败，并有 12 个 H1 assignments 为 `T=0,H=1`。LocalLSTC 没有连续 caption transcript 或音频流，只能在 action/observation 边界读取字幕 overlay。字幕可能在两次截图之间出现并消失，后一句也可能覆盖前一句。

典型后果：

- Live Caption 仍开启，因此 (H=1)；
- 日期、年份、确认码、数量、备选项或先后顺序没有完整进入 observation；
- 邮件、日历、Sticky Note、CMS 或 factual answer 缺字段或写错。

这是 observation-channel limitation，不是“agent 必须通过字幕理解音频”的论点。改进方向是连续 caption event stream、transcript buffer、密集触发观察或 replay-and-accumulate policy。

### 7.2 GUI grounding 错误及其放大后果

Grounder 会点到相邻开关、展开箭头或错误字段，或在点击无效后仍假设状态已改变。随后 planner 使用 stale state 继续推理。

这是通用 GUI limitation，但 accessibility 后果更大：依赖非视觉或代理交互的用户可能无法独立发现、核验或撤销错误；一个小的 grounding mistake 可能留下更难使用的设置或不可继续界面。

### 7.3 Partial verification 与 false completion

52/88 个失败由 agent 主动结束，43 个 handoff evaluator 为 0。常见模式是只确认“发生了一些变化”，没有覆盖完整 contract：

- `motor/captcha-hold_button_1`：按钮显示 Complete、进度条填满后结束，但 evaluator 还要求进入 success URL。
- `visual/information-cat_image_alt_text`：确认 DOCX 中存在 description 属性，却没有逐项验证 evaluator 要求的视觉属性。
- `motor/access-enable_filter_keys`：根据局部 UI 或设置反馈结束，但最终系统状态未满足 evaluator。

### 7.4 感知不确定后生成 plausible but unsupported answer

在地图、图片、扫描件和复杂 PDF 中，LocalLSTC 有时明确记录 OCR/视觉不确定，随后仍选择一个世界知识上合理的答案并称其已验证。

代表例子 `visual/mobility-cta_airport_transfer`：识别了 O'Hare、Blue Line、Clark/Lake 和 Midway，却写成 Green Line 而不是 Orange Line。这里的底层错误是视觉关系识别；accessibility 后果是错误文字路线被用于替代用户对地图的直接视觉访问。

### 7.5 Persistent artifact 正确更新，但 nominal result 错误

`cognitive/consumption-lowest_price_white_mouse` 满足 (H=1)：spreadsheet/status 或 persistent note 得到更新；但购物车没有正确商品/选项，因此 (T=0)。类似问题也出现在 Elsa water bottle、ginger ale、kids sunscreen 等任务。

错误外部记忆比缺失更危险：用户可能相信清单中的 Done 状态，随后基于错误记录继续行动。

### 7.6 精确 assistive-state configuration 不稳定

系统较容易打开 Magnifier、Narrator、OSK、Mouse Keys、Sticky Keys 等常见功能，但对精确倍率、特定 color filter、ClickLock、Filter Keys 子项、audio-flash mode 和 swapped primary button 更不稳定。

当前 need-level 结果中 M2 失败 10/16，M3 失败 5/10，V2 失败 5/13。问题通常结合 settings navigation、相邻控件 grounding、精确值选择和结束前缺少系统级读取。

### 7.7 持续与精细 pointer interaction

M4 失败 5/7，是最终 taxonomy 中最弱的 need。Hold、slide、patch selection、拖动和精确 target acquisition 明显比简单点击更困难。底层是通用 motor-control proxy limitation；但任务正是为无法完成持续或精细指针操作的用户委托代理，因此失败会保留原始 access barrier。

### 7.8 长流程与有界恢复不足

22 个失败耗尽 50 步，12 个因连续 stall 停止。重复模式包括：

- 在同一页面反复滚动或点击；
- 反复切换 GUI 与代码路径，却没有验证上一种路径留下的状态；
- 接近步数上限仍在收集候选信息，没有预留保存与最终验证步骤；
- 恢复动作针对当前 UI 症状，而不是针对未满足的 (T/H) obligation。

## 8. 两个 infeasible cases 的解释

1. `hearing/communication-meeting_action_items`：Windows Live Captions 报告没有音频设备，日志通过多个系统查询确认无可用 audio endpoint，因此无法执行依赖 Windows Live Caption 的录音任务。
2. `hearing/health-anaphylaxis_medicine`：MedlinePlus 页面出现 `DNS_PROBE_FINISHED_NXDOMAIN`，guest 内 DNS 和 urllib 查询同样失败，目标视频无法加载，Chrome Live Caption 没有输入源。

这两个属于环境/基础设施 infeasibility，而不是 agent 推理能力本身。论文中应单独报告，避免把它们与规划或 handoff omission 混合。

## 9. 优先改进建议

1. **显式维护 (T/H) obligation ledger。** 每个子条件需要独立、可引用证据；未验证的 obligation 阻止 `finish`。
2. **为 transient evidence 增加缓冲。** 保存 caption/audio facts，并在写入 artifact 前进行 completeness check。
3. **Grounding uncertainty 触发独立状态查询。** 点击设置后读取系统/应用真实状态，不能只凭截图观感。
4. **对 accessible representation 做逐字段验证。** Alt text、路线、标签、地图关系和视觉描述必须覆盖所有 task-relevant facts。
5. **Persistent artifact 与 nominal result 双向一致性检查。** 只有商品、路线或事实正确后才能把 checklist/status 标记为 Done。
6. **限制重复恢复。** 同一策略失败 2--3 次后切换路径，并以未满足的 handoff item 为恢复目标。
7. **给最后保存和验证预留步数。** 接近预算时停止无界探索，优先形成最小可评测闭环。
8. **把环境 infeasibility 单独计量。** 音频设备和 DNS 故障应从 agent capability failure 中分离。

## 10. 论文表述注意事项

- 可以说 70 个失败的 handoff evaluator 为 0；不能说这些失败“由 accessibility 导致”。
- 5 个 `T=1,H=0` 是最纯粹的 handoff-gap 证据。
- 18 个 `T=0,H=1` 应称为 support-ready but nominally incorrect。
- Agent 不需要使用用户的 assistive technology 作为自己的感知/控制通道；评测的是用户接手时的终态。
- 应把 grounding、constraint loss、planning、stall、budget exhaustion 等通用原因与 accessibility consequence 分开编码。
- Need-level 结果来自当前 source metadata，而不是旧 execution-log taxonomy。
- 本报告的 198/110/55 数字不能与 `main.tex` 中旧版 200/112/51 直接混用。

## 11. 一句话总结

LocalLSTC 的主要 accessibility limitation 不是完全无法建立支持状态，而是**无法确保支持状态承载正确、完整的任务结果，并且经常在只完成局部验证时提前交还控制权**。88 个失败中 70 个 (H=0)，43 个 (H=0) 仍被主动 `finish`；另有 18 个任务虽 (H=1)，但 nominal work 错误。最优先的改进方向是连续证据保存、(T/H) 双重验证、persistent artifact 一致性和 grounding 后的独立状态检查。

## 附录 A：53 个 coincident accessibility failures

### Cognitive（8）

`access-chrome_font_size_large`、`communication-ftc_gift_card_pressure_email`、`health-running_hydration_guide_note`、`information-food_calorie_forum_answer`、`management-cfpb_autopay_review_reminder`、`mobility-harvard_mather_evening_plan`、`mobility-victoria_train_interchange_note`、`service-cms_simplify_service_hours`

### Hearing（2）

`access-windows_audio_flash_title_bar`、`access-windows_audio_flash_window`

### Motor（23）

`access-enable_clicklock`、`access-enable_filter_keys`、`access-set_primary_mouse_button_right`、`captcha-hold_button_1`、`captcha-patch_select_3`、`captcha-slide_puzzle_1`、`captcha-slide_puzzle_3`、`communication-filter_keys_volunteer_email`、`communication-mouse_keys_equipment_update_email`、`consumption-cheapest_bathroom_accessory`、`consumption-half_price_body_wash`、`consumption-running_shoe_release_comparison`、`consumption-shopping_list_cart`、`consumption-wireless_mouse_search_result`、`health-allied_health_form_download`、`health-physiotherapy_appointment_checklist`、`health-sticky_keys_emergency_contact_card`、`information-singapore_real_gdp_comparison`、`information-ucla_economics_premajor_gpa`、`management-student_gradebook`、`mobility-accessible_grade1_walks`、`mobility-mouse_keys_google_maps_route`、`service-reddit_monitor_post_count`

### Visual（20）

`access-windows_color_filter_grayscale_inverted`、`access-windows_color_filter_protanopia`、`access-windows_magnifier_200`、`captcha-hold_button_2`、`captcha-patch_select_2`、`captcha-slide_puzzle_2`、`consumption-marshmallow_bunnies`、`consumption-toothbrush_price_comparison`、`health-drug_facts_package`、`information-cat_image_alt_text`、`information-cta_rail_map_alt_text`、`information-invitation_image_alt_text`、`information-wikipedia_image_person`、`management-cardiology_appointment_reminder`、`management-weekly_planner_calendar`、`mobility-cta_airport_transfer`、`mobility-nearest_pharmacy_marina_bay_sands`、`mobility-transit_route_grand_central_to_liberty`、`mobility-walking_route_wat_arun`、`service-real_id_infographic`
