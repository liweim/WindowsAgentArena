# 四种 GUI Agent 方法的共同失败原因与 Accessibility 限制

## Material Passport

- Artifact ID：`four-method-common-failure-synthesis-20261030`
- 类型：cross-method benchmark synthesis
- Verification Status：`ANALYZED`
- 方法：Agent S3 (`agents3_qwen3.8-27b`)、CoAct (`coact_qwen3.8-27b`)、LocalLSTC (`locallstc_qwen3.8-27b`)、HISA wo-pattern (`hisa_qwen3.8-27b_wo_pattern`)
- 数据：每种方法各 198 个顶层任务，共 792 个运行
- 评价口径：nominal task outcome (T)、need-conditioned handoff (H)、full success (F=T\land H)
- Taxonomy：使用当前 task source metadata 统一映射到论文最终 14 个 need ID
- 统计版本：本报告的 (T)/(H) 与交集数字统一从当前四个结果目录的 `execution_log.json` 重算；它们取代旧单独报告中基于较早 metadata 快照的少量分项数字
- 限制：四种方法共享任务集合和基础模型家族，运行并非统计独立样本；汇总数字用于描述，不用于显著性或因果推断

## 1. 总体对比

| 方法 | 成功 (F=1) | 失败 (F=0) | 失败率 | (H=0) 失败 | `T=1,H=0` | `T=0,H=1` |
|---|---:|---:|---:|---:|---:|---:|
| Agent S3 | 91 | 107 | 54.04% | 91 | 10 | 16 |
| CoAct | 61 | 137 | 69.19% | 115 | 5 | 22 |
| LocalLSTC | 110 | 88 | 44.44% | 71 | 5 | 17 |
| HISA (wo pattern) | 88 | 110 | 55.56% | 84 | 5 | 26 |
| **四种方法合计** | **328** | **464** | **58.59%** | **361** | **25** | **81** |

合计 464 个失败运行中，361 个（77.80%）没有满足 need-conditioned handoff。四种方法都存在：

- `T=1,H=0`：普通任务已完成，但 accessibility handoff 未准备好；
- `T=0,H=1`：辅助状态或支持 artifact 已准备，但实际工作错误；
- `T=0,H=0`：普通任务与 accessibility handoff 同时失败；
- coincident failure：任务本身就是 accessibility support，不能把 (T) 与 (H) 独立分解。

同一任务在四种方法下均失败的共有 **50/198（25.25%）**。其中 hearing 17、visual 16、motor 9、cognitive 8；按 workflow 分布为 consumption 14、information 9、communication 5、health 5、mobility 5、CAPTCHA 4、service 3、management 3、access 2。

这说明失败不仅来自某一种 scaffold 的偶然实现；至少 50 个任务对四种方法都构成稳定困难。但四者共享 Qwen3.8-27B 和部分组件/环境，因此不能把这一交集直接解释为所有 GUI agents 的普遍失败率。

## 2. 四种方法共同的通用失败原因

### 2.1 过早结束与不完整的最终验证

四种方法最一致的失败机制是：agent 验证了局部变化，却没有验证完整任务和 handoff contract。

| 方法 | 自报完成但评测失败 | 其中 (H=0) |
|---|---:|---:|
| Agent S3 | 56 | 47 |
| CoAct | 52 | 47 |
| LocalLSTC | 52 | 43 |
| HISA (wo pattern) | 73 | 63 |

虽然四种日志中的 `done_action`、coordinator `terminate`、`finish` 和 HISA `Task COMPLETED` 语义并不完全相同，但共同模式清楚：

- 看到开关变色、进度条填满、文件属性存在或购物车角标变化就结束；
- 没有读取最终系统状态、重新打开文件或逐字段检查 artifact；
- 没有分别验证 (T) 与 (H)；
- 最终说明经常只是复述目标，而不是提供可机读的终态证据。

因此，false completion 是四种方法共同且最有证据支持的首要问题。HISA 的 110 个失败中有 73 个由代理主动判定完成，是四种方法中最突出的错误完成判断。

### 2.2 长流程无法收敛，恢复策略重复

四种方法都在复杂任务中出现步数耗尽、非终态中断或 stall：

- Agent S3：23 个失败达到 50 步，另有 16 个在非终态停止；
- CoAct：68 个无终态失败累积至少 50 条 action log，另有 GUI missing-action 和 instruction-only failures；
- LocalLSTC：22 个失败明确达到 50 步，12 个因连续三次 stall 停止。
- HISA：31 个失败达到 50 步；另有 6 个由 planner 主动判定 infeasible。

共同轨迹模式包括：

- 同一页面反复滚动；
- 对同一相邻控件重复点击，只做很小的坐标调整；
- 反复切换 GUI、代码或搜索路径，但没有确认上一条路径留下的状态；
- 在任务后半段仍进行开放式探索，没有预留保存与验证步骤；
- 恢复针对当前 UI 症状，而不是针对未满足的 (T/H) obligation。

### 2.3 GUI grounding 与精确控件操作不足

四种方法都会：

- 点到 toggle 旁的 chevron、错误字段或相邻按钮；
- 点击没有生效却假设状态已改变；
- 在放大、滚动、弹窗或多窗口环境中丢失焦点；
- 难以完成 hold、slide、drag、patch selection 和细小 target acquisition。

Grounding 是一般 GUI-agent 问题，不是 disability-specific mechanism。但当用户依赖 agent 进行非视觉操作或代理精细运动时，错误更难被用户独立发现、核验和恢复。

### 2.4 多条件约束跟踪不完整

许多任务是合取条件：正确内容、正确应用、正确对象、正确字段、正确保存语义、正确辅助状态和正确最终页面必须同时成立。四种方法都会只完成其中一部分。

高频遗漏包括：

- 邮件应保存为 draft 而不是发送；
- calendar 的日期、全天状态、起止时间、地点或提醒字段；
- 商品的 SKU、variant、数量、coupon 和 cart 页面；
- 文件路径、格式、保存状态和内容完整性；
- Narrator、Live Caption、Magnifier、OSK 等必须在 handoff 时仍可用。

### 2.5 跨应用信息转移与持久化不可靠

四种方法在“读取来源 → 提取证据 → 切换应用 → 构造 artifact → 保存 → 验证”流程中均容易丢失信息：

- 音频/PDF/网页中的日期、代码、数量或顺序未完整转入邮件、日历、笔记或 CMS；
- 文件在代码层被修改，但 GUI 应用仍持有旧缓存；
- Sticky Notes、LibreOffice、Thunderbird 的自动保存、Save、Save As、Save and Close 被混淆；
- agent 验证“对象存在”，却没有验证内容与 evaluator 完全一致。

### 2.6 感知不确定后进行 plausible inference

当 OCR、地图、图片或复杂 PDF 关系不清楚时，四种方法都会用世界知识或局部合理关系补全答案，然后在最终总结中把推断描述成已验证事实。

这在普通 benchmark 中会造成 factual error；在 accessibility 场景中，生成文字可能是用户替代视觉/听觉访问的主要渠道，因此错误信息会成为用户唯一可见的“事实”。

### 2.7 商品与路线等开放式比较任务困难

Consumption 是四种方法共同最弱的 workflow：

| 方法 | Consumption 失败率 |
|---|---:|
| Agent S3 | 19/24（79.17%） |
| CoAct | 23/24（95.83%） |
| LocalLSTC | 20/24（83.33%） |
| HISA (wo pattern) | 20/24（83.33%） |

Mobility 也持续较弱：56.25%、62.50%、62.50%、68.75%。共同难点包括候选比较、空间关系、tie-break、精确 variant/SKU、页面状态和外部记录同步。这些 workflow 的失败不能全部归因于 accessibility，但会破坏需要 accessible representation 或 persistent support 的 handoff。

## 3. 四种方法共同的 Accessibility-related 原因

### 3.1 Accessible information 的采集与保存不完整

H1 音频任务在四种方法下都较弱：Agent S3 失败 28/44、CoAct 39/44、LocalLSTC 23/44、HISA 30/44。

共同限制是 observation channel 不提供可靠的连续 caption transcript/audio buffer。Agent 依赖离散截图，关键 utterance 可能：

- 出现在两个 observation 之间；
- 被后续字幕覆盖；
- 只留下句子后半段；
- 被看到但没有存入可复用 evidence buffer。

结果是 Live Caption 可能已经开启并通过 (H)，但邮件、日历、笔记、CMS 或事实答案仍缺日期、年份、代码、数量或顺序。

### 3.2 Support state 与 nominal task 脱节

四种方法均出现 `T=0,H=1`：Agent S3 16、CoAct 22、LocalLSTC 17、HISA 26。共有 4 个具体任务在四种方法下都属于这一模式：

- `hearing/health-long_covid_care_note`
- `hearing/information-ftc_washington_q4_fraud`
- `hearing/management-home_delivery_window_audio`
- `hearing/service-cms_update_access_desk_page_audio`

这说明“打开辅助功能”或“更新支持 artifact”不是完整的 accessible assistance。支持必须承载正确的业务结果。

### 3.3 Nominal success 隐藏 handoff failure

四种方法均出现 `T=1,H=0`：Agent S3 10、CoAct 5、LocalLSTC 5、HISA 5。`management-quick_sponge_timer` 在四种方法下都属于这一纯 handoff-gap 模式。

这些任务是 benchmark 核心主张的直接证据：普通任务成功率会把它们判为成功，但用户接手时没有需要的 caption、screen-reader、timer/continuation state 或其他 handoff support。

### 3.4 精确 assistive-state configuration 不稳定

四种方法都比“打开某功能”更难完成精确设置：

- exact magnification / text size；
- 特定 color filter 或 contrast theme；
- Filter Keys、Sticky Keys、Mouse Keys 的正确子项和 flags；
- ClickLock、primary mouse button；
- audio flash、mono/channel、caption style/language。

最终 14-ID 中，M2 的失败率为 68.8%、81.2%、62.5%、93.8%；M3 为 40.0%、80.0%、50.0%、60.0%；V2 为 69.2%、61.5%、38.5%、38.5%。共同根因是 settings navigation、相邻控件 grounding、精确值选择以及缺少权威终态查询。

### 3.5 Persistent external support 可能缺失、过时或错误

C3 记忆/回忆支持的失败率为 Agent S3 47.5%、CoAct 62.5%、LocalLSTC 30.0%、HISA 47.5%。四种方法都出现：

- checklist 或 spreadsheet status 没有保存；
- reminder/calendar 字段不完整；
- timer 没有真正运行或 handoff 时不可见；
- artifact 已标记 Done，但商品、事实或实际操作错误。

错误 persistent artifact 比缺失更危险，因为用户可能把它作为后续行动依据。

### 3.6 Accessible representation 不完整或未经证据支持

V3 的失败率为 55.0%、70.0%、45.0%、50.0%。常见问题：

- alt text 字段存在，但缺少 task-relevant visual attributes；
- 地图路线文字混淆线路、换乘站或顺序；
- 图表、标签、扫描件和复杂 PDF 的空间关系被线性 OCR 破坏；
- agent 用合理猜测补齐不可见信息。

Accessibility 后果是用户得到一个形式上可访问、内容上不可靠的替代表示。

### 3.7 Delegated motor barrier 仍未被解除

M4 的失败率为 Agent S3 57.1%、CoAct 71.4%、LocalLSTC 71.4%、HISA 57.1%。四种方法都难以稳定完成持续按压、拖动、滑块、patch selection 和精确目标点击。

这不是一种新的 motor-specific 算法错误，而是普通 control limitation 在 accessibility 委托场景中的直接后果：用户委托 agent 正是因为原操作需要不可及的持续或精细动作；agent 失败后，原始 barrier 原封不动地留下。

### 3.8 错误 handoff 增加用户核验与恢复负担

四个方法都会留下“看起来完成”的错误状态。对于能够轻松视觉检查和修复的用户，这可能只是额外工作；对于依赖非视觉访问、替代输入或记忆支持的用户，错误可能无法被发现，或修复本身仍不可及。

因此论文应把同一个 generic failure 的 accessibility consequence 单独编码：

- nominal result corruption；
- accessible information loss；
- persistent artifact corruption；
- assistive state not preserved；
- unusable continuation state；
- increased verification/recovery burden。

## 4. 最终 14 个 Need ID 的统一对比

下表全部使用当前 source metadata，而不是各运行日志中的历史标签。

| Need | Agent S3 失败率 | CoAct 失败率 | LocalLSTC 失败率 | HISA 失败率 | 共同观察 |
|---|---:|---:|---:|---:|---|
| V1 | 57.1% | 52.4% | 52.4% | 66.7% | 四者均超过 50%，非视觉 continuation 持续困难 |
| V2 | 69.2% | 61.5% | 38.5% | 38.5% | 精确视觉设置困难，LocalLSTC/HISA 相对较强 |
| V3 | 55.0% | 70.0% | 45.0% | 50.0% | 文本替代的完整性与证据问题 |
| H1 | 63.6% | 88.6% | 52.3% | 68.2% | 四者共同弱项，CoAct 最严重 |
| H2 | 20.0% | 60.0% | 40.0% | 20.0% | 样本仅 5，谨慎解释 |
| H3 | 75.0% | 100.0% | 50.0% | 100.0% | 样本仅 4，但四者都不稳定 |
| H4 | 100.0% | 100.0% | 60.0% | 80.0% | 四者共同弱项，样本仅 5 |
| M1 | 23.5% | 35.3% | 17.6% | 17.6% | 四者相对最强；打开替代输入较容易 |
| M2 | 68.8% | 81.2% | 62.5% | 93.8% | 四者共同弱项；HISA 最严重 |
| M3 | 40.0% | 80.0% | 50.0% | 60.0% | 替代交互配置不稳定 |
| M4 | 57.1% | 71.4% | 71.4% | 57.1% | 四者共同弱项；持续/精细操作困难 |
| C1 | 66.7% | 66.7% | 33.3% | 33.3% | 样本仅 3，不宜排序 |
| C2 | 43.8% | 68.8% | 37.5% | 37.5% | 简化/结构化表达仍有遗漏 |
| C3 | 47.5% | 62.5% | 30.0% | 47.5% | Artifact 建立与内容正确性脱节 |

跨方法最稳定的弱项是 H1、H4、M2、M4、V1 和 V3。M1 在四种方法中都相对较强，说明“打开或保留常见替代输入”比“精确配置参数、获取瞬时信息、生成完整替代表示或代理持续精细操作”容易。

## 5. 50 个四种方法共同失败任务的结构

共同失败并不等于同一底层原因，但其分布能定位最稳定的困难：

| 维度 | 共同失败数 |
|---|---:|
| Hearing group | 17 |
| Visual group | 16 |
| Motor group | 9 |
| Cognitive group | 8 |
| Consumption workflow | 14 |
| Information workflow | 9 |
| Communication / Health / Mobility workflow | 各 5 |
| CAPTCHA | 4 |
| Service | 3 |
| Management | 3 |
| Access | 2 |

四种方法共同 `(H=0)` 的具体任务有 33 个；这比仅看各方法总体失败更强地表明某些 handoff contracts 对当前 agent family 一致困难。完整 50-task 清单见附录 A。

## 6. 不应归入“共同原因”的方法特有问题

为了避免过度概括，下列问题不应直接写成四种方法共同失败机制：

- Agent S3：9 个“计划仍要继续、实际记录为 FAIL”的 action-control mismatch，以及若干非终态中断。
- CoAct：coding agent 创建 shim、使用错误 registry proxy、coordinator 与 GUI/coding 子代理状态不一致等多代理架构问题。
- LocalLSTC：两个有明确系统证据的环境 infeasibility（无音频设备、DNS failure），以及其专门的三次 stall gate。
- HISA wo-pattern：73 个失败被 planner 错误判定为 `Task COMPLETED`，31 个达到 50 步，另有 6 个被主动判定 infeasible；其 global planner/state manager 终止机制及不使用 pattern memory 的配置不应直接推广到其他三种方法。

这些可以作为各方法 case study，但不能用于描述所有方法的共同 limitation。

## 7. 对论文 failure taxonomy 的建议

建议每个失败采用两层编码，而不是单一“accessibility failure”标签。

### 7.1 第一层：Generic execution cause

1. evidence not observed；
2. grounding / actuation error；
3. constraint loss；
4. cross-application transfer failure；
5. persistence/save failure；
6. plausible inference under uncertainty；
7. repeated recovery / budget exhaustion；
8. premature or dishonest termination；
9. environment/infrastructure infeasibility；
10. scaffold/controller failure。

### 7.2 第二层：Accessibility handoff consequence

1. accessible information incomplete or wrong；
2. persistent external support missing, stale, or incorrect；
3. assistive/continuation state not established or not preserved；
4. delegated interaction barrier remains；
5. user cannot independently verify or recover；
6. no handoff failure (`H=1`), but nominal task remains incorrect。

这种两层结构能够承认大部分底层错误是通用 GUI limitation，同时准确说明为什么它们在 accessibility-conditioned assistance 中更严重。

## 8. 跨方法共同改进优先级

1. **显式 (T/H) ledger。** Planner 必须分别追踪普通任务和 handoff obligation，不能用一个“完成”状态替代。
2. **Termination gate。** `done/terminate/finish` 前执行与 evaluator 对齐的系统级、文件级和内容级验证。
3. **连续 multimodal evidence buffer。** 保存 caption/audio/OCR facts，记录来源、时间和完整性。
4. **Grounding 后独立读取状态。** 设置 toggle、数值或 dropdown 后用可靠 API/UI query 验证。
5. **Artifact 与 nominal result 一致性检查。** 业务结果未验证前，不得把 checklist/status 标记为 Done。
6. **有界恢复。** 同一动作失败 2--3 次后切换策略，并以未满足的 (T/H) item 为恢复目标。
7. **步数预算。** 为保存、重新打开和最终验证预留最后 20%--30% 的 action budget。
8. **不确定性诚实报告。** OCR/视觉证据不足时不得把 plausible inference 表述成已验证事实。
9. **区分环境与 agent failure。** 音频设备、DNS、页面不可用等基础设施问题单独统计。

## 9. 论文表述注意事项

- 可以说四种方法当前日志重算后合计 361 个失败运行的 `(H=0)`；不能说它们“由 accessibility 导致”。
- `T=1,H=0` 是最直接的 failed-handoff event；`T=0,H=1` 不是 handoff-condition failure。
- Assistive technology 是用户接手时的支持状态，不要求 agent 必须使用同一工具完成任务。
- Need-level 表是多标签描述性统计，样本小的 H2/H3/H4/C1/M4 不宜做稳定排名。
- 四种方法共享任务、模型家族和环境，不应把 792 runs 当作独立随机样本。
- 共同失败原因应基于四种轨迹都出现的机制；scaffold-specific abnormality 应单独报告。

## 10. 一句话总结

四种方法的共同问题不是简单的“不会打开辅助功能”，而是**无法把证据采集、普通任务执行、用户支持 artifact、assistive continuation state 和最终验证稳定地闭环**。最普遍的表现是局部完成后过早结束、长流程重复恢复、grounding/精确设置错误、瞬时字幕和视觉证据丢失，以及支持状态与实际任务结果脱节；这些通用 GUI-agent limitation 在 accessibility handoff 中会变成不可访问、不可核验或不可继续的用户终态。

## 附录 A：50 个四种方法共同失败的任务

### Cognitive（8）

`communication-library_program_reply`、`consumption-kids_sunscreen_reviews`、`consumption-lowest_price_white_mouse`、`consumption-movie_night_shopping`、`consumption-tomato_egg_stir_fry`、`health-running_hydration_guide_note`、`mobility-victoria_train_interchange_note`、`service-cms_import_service_product`

### Hearing（17）

`access-windows_audio_flash_window`、`communication-dental_reschedule_voicemail`、`communication-equipment_reimbursement_email`、`consumption-sony_alpha`、`health-child_visit_preparation`、`health-long_covid_care_note`、`information-ftc_2024_fraud_reports`、`information-ftc_florida_fraud_data`、`information-ftc_washington_q4_fraud`、`information-handwashing_steps`、`information-maricopa_census_search`、`information-noaa_pillow_lava`、`management-home_delivery_window_audio`、`management-quick_sponge_timer`、`mobility-opera_house_street_view`、`mobility-walking_route_alhambra`、`service-cms_update_access_desk_page_audio`

### Motor（9）

`captcha-patch_select_3`、`captcha-slide_puzzle_1`、`communication-filter_keys_volunteer_email`、`communication-mouse_keys_equipment_update_email`、`consumption-running_shoe_release_comparison`、`consumption-shopping_list_cart`、`consumption-wireless_mouse_search_result`、`health-sticky_keys_emergency_contact_card`、`information-ucla_economics_premajor_gpa`

### Visual（16）

`access-windows_magnifier_200`、`captcha-hold_button_2`、`captcha-patch_select_2`、`consumption-guest_bathroom_towel_holders`、`consumption-keto_bread`、`consumption-lavender_coupon`、`consumption-marshmallow_bunnies`、`consumption-saute_pan`、`consumption-toothbrush_price_comparison`、`health-drug_facts_package`、`information-cta_rail_map_alt_text`、`information-wikipedia_image_person`、`management-weekly_planner_calendar`、`mobility-cta_airport_transfer`、`mobility-walking_route_wat_arun`、`service-real_id_infographic`

## 附录 B：四份单独报告

- `paper/failure_analysis_agents3.md`
- `paper/failure_analysis_coact.md`
- `paper/failure_analysis_locallstc.md`
- `paper/failure_analysis_hisa_qwen3.8-27b_wo_pattern.md`
