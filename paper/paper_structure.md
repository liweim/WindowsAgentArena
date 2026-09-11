# 中文论文框架：Accessibility-Oriented Computer-Use Agent Benchmark

> 用途：服务 ACL/ARR 论文写作、实验设计和论证组织。任务定义、JSON schema、evaluator 规则、task construction、环境维护等工程规范以 `README.md` 为准；本文档只保留 paper story、related-work positioning、research questions、实验与方法设计、claim-evidence 关系和投稿前检查项。

## 0. 一句话论文主线

现有 computer-use agents（CUAs）主要在“通用用户 + 标准 GUI + 通用任务”假设下被评测，但真实用户具有不同的 visual、hearing、motor 和 cognitive accessibility needs；一个 agent 即使能完成普通 GUI 任务，也不意味着它能可靠地替这些用户完成任务，并把系统留在用户可以继续检查、理解和接管的 accessible state。我们构建一个可执行、可重置、端到端、确定性评测的 accessibility-oriented computer-use benchmark，系统评测约 10 个代表性 baseline，揭示不同 user groups、modalities、accessibility features 和 workflow types 下的系统性能力差异，并基于这些 failure patterns 提出针对性的改进方法，在本 benchmark 上取得最佳结果，同时验证其在已有通用 computer-use benchmark 上的泛化能力。

这个 story 的核心不是“让 agent 模拟残障用户操作电脑”，而是：

**Agent solves the task for the user, while preserving an accessible user-facing handoff state.**

---

## 1. 最核心的研究问题

论文需要始终围绕下面几个问题展开，而不是把贡献写成“又做了 200 个 GUI tasks”。

### RQ1：现有 CUA 是否能可靠服务具有不同 accessibility needs 的用户？

测整体 task success，同时按 visual / hearing / motor / cognitive user group 分解。重点不是只报一个平均分，而是观察模型能力是否在不同 user groups 上出现显著不均衡。

### RQ2：accessibility-oriented task 与普通 GUI task 的难点具体不同在哪里？

分析可能包括：

- accessibility feature/state 的配置与保持；
- audio/video/text 等不同信息模态；
- accessible handoff state；
- 跨应用状态维持；
- 信息抽取与结构化；
- constraint adherence；
- 页面或系统状态变化后的恢复；
- 长程任务中的 completion verification。

如果能够构造 matched 或近似 matched 的普通任务 / accessibility-oriented task pairs，可以进一步报告 accessibility-induced performance gap；如果不能严格匹配，则不要强行声称 causal gap，而应表述为不同 task slices 上的 systematic performance differences。受 A11y-CUA “固定任务、改变交互条件”对照设计的启发，可以从现有任务中额外构造一个小规模 matched subset：保持 underlying user goal 基本不变，只增加 accessibility-oriented requirement / handoff state，用于更干净地估计额外难度。

### RQ3：不同 accessibility user groups 暴露出的 agent failure 是否不同？

这是 benchmark 最有研究价值的分析之一。目标不是证明“某一组更难”，而是找到不同需求对应的 failure signature，例如：

- visual：非视觉信息读取、结构化页面理解、screen-reader/accessible state 配置与验证；
- hearing：caption/live-caption state、音频信息获取、媒体状态同步；
- motor：输入方式、keyboard assistance、复杂 UI 操作、可靠完成与 handoff；
- cognitive：信息简化、记忆外部化、计划/状态保持、长流程 completion checking。

最终应形成一个可复用的 failure taxonomy，而不是只给 case study。

### RQ4：现有通用 CUA 的哪些设计假设导致这些 failure？

通过模型类别、observation type、planning mechanism、action space、是否使用 structured accessibility/UI information 等维度比较约 10 个代表性 baseline。

### RQ5：针对 benchmark 揭示的问题进行方法改进，能否显著缩小这些 failure，同时保持通用 computer-use 能力？

新方法必须由前面的 empirical findings 自然导出。论文逻辑应是：

**Benchmark reveals systematic failures → analysis identifies mechanisms → method directly addresses those mechanisms → gains concentrate on the predicted failure slices → cross-benchmark experiments show the method is not merely exploiting one evaluator.**

---

## 2. 论文最重要的概念定义

### 2.1 Accessibility-oriented computer use

本文研究的不是让 agent “体验残障”，也不是要求 agent 复制目标用户群的 AT interaction trajectory。

定义建议：

> An accessibility-oriented computer-use task asks an agent to complete a digital goal on behalf of a user with a particular access need, while producing a correct user-facing outcome and, when required, preserving or configuring an accessibility state that allows the user to inspect, understand, continue, or take over the workflow.

中文理解：agent 可以继续使用它正常的视觉、鼠标、键盘或 structured observation 能力；accessibility feature 主要是面向用户的最终状态或任务约束，而不是默认强迫 agent keyboard-only、screen-reader-only 或 magnifier-only。

**不规定唯一操作轨迹。** A11y-CUA 显示，即使具有相似 access needs 的真实用户也会采用不同的键盘导航、快捷键和确认策略。因此本文不要求 agent 模仿某一种 assistive-technology trajectory，而以正确的 user-facing outcome 和 required accessibility/handoff state 作为成功标准。这也为 deterministic end-state evaluation 提供了重要动机。

### 2.2 Accessible handoff state

这是和普通 GUI benchmark 拉开差异的一个重要概念，建议在 Introduction 和 Benchmark Design 中明确命名。

完成任务不只是“数据库状态变了”或“文件被保存了”，还可能要求：

- Live Caption / Reading Mode / keyboard assistance 等 feature 处于正确状态；
- 用户需要的信息已经被整理到可访问、可继续的 artifact；
- reminder、calendar、note、draft、document 等状态可以由用户后续接管；
- agent 没有破坏用户依赖的 accessibility configuration。

Evaluator 应检查 user-facing task outcome 以及 instruction 明确要求的 accessibility state。

### 2.3 Cognitive accessibility 的边界

不要把“任何多步骤任务”都称为 cognitive-access task，但也不要把 cognitive accessibility 限定成“必须额外生成 checklist / reminder”。

本文允许两类任务进入 cognitive slice：

1. **Support-output tasks**：agent 通过 reminder、checklist、calendar、简化后的 note、结构化信息等输出，直接降低用户的 memory、attention、information-processing 或 planning burden。
2. **Delegated-burden tasks**：数字流程本身对目标用户具有显著 cognitive burden，agent 通过代替用户完成流程来提供帮助。典型负担包括 multi-stage sequencing、working-memory / task-state tracking、选项或权限判断、状态解释、异常恢复以及 completion recognition。

因此，**software installation 可以是合理的 cognitive-access task**。下载、安装、处理权限或弹窗、理解安装状态并确认最终成功，本身就是一条需要持续 sequencing、state tracking 和 completion verification 的流程；这类流程对部分 older adults 或具有 cognitive accessibility needs 的用户可能构成明显障碍。论文中应把理由落在这些具体 cognitive demands 上，而不是把“年龄”本身当成 disability label，也不能仅因为任务步骤多就自动归为 cognitive。

同时，`category` 与 user group 是正交维度：`access`、`mobility`、`shopping`、`service` 等描述**任务类型**，visual / hearing / motor / cognitive 描述**服务的 accessibility user group**。因此 `access-chrome_font_size_large` 保持 `category: access` 是合理的；cognitive 组中保留 `mobility` 类任务也有价值，可以体现同一 user group 覆盖不同真实 workflow，而不是“一类用户只对应一种任务类型”。

对于 cognitive 任务，构建和验证时应能够指出至少一种具体需求，例如 memory / prospective memory、attention、information processing、planning / sequencing、task-state tracking、completion recognition、error recovery 或 reduced time pressure。

---

## 3. 与已有工作的定位

### 3.1 与通用 GUI / CUA benchmarks 的关系

Related Work 可以按三组写：

1. **Web agents**：WebArena、VisualWebArena 等；
2. **OS / mobile computer-use**：OSWorld、WindowsWorld、AndroidWorld 等；
3. **multimodal GUI benchmarks**：VideoWebArena、VideoGUI、OmniGUI 等。

这些工作主要回答“agent 能不能完成通用 GUI task”，而本文关注“这些能力是否同样适用于具有不同 accessibility needs 的用户目标，以及 agent 是否能留下合适的 accessible handoff state”。

不要把差异简单写成“我们多了 accessibility tasks”；更好的 framing 是 benchmark construct 不同：

- user population / access need 显式进入任务定义；
- multimodal accessibility information 进入任务；
- accessibility support state 可以成为 success condition；
- task success 需要同时满足 ordinary outcome 与 user-facing accessibility requirement；
- 分析目标是不同 user groups 的 capability gaps，而不是单一平均 GUI success rate。

### 3.2 与 A11y-CUA 的关系

这是最需要准确处理的 related work。

建议定位：

> A11y-CUA is an accessibility interaction dataset and empirical study that records rich human and agent trajectories on a shared set of Windows tasks and evaluates CUAs under default and accessibility-related interaction conditions. It is highly complementary to our work, but targets a different research question and artifact type.

A11y-CUA 的主要问题是：

**当 agent 所处的交互假设被改成 keyboard-only / screen-reader-related / magnified 等 accessibility conditions 时，能力会发生什么变化？真实 BLV 用户和 agent 的 interaction strategies 有什么差异？**

本文的问题是：

**给定具有不同 accessibility needs 的用户目标，agent 能否替用户完成真实任务，并产生正确且可供用户后续接管的 accessible state？**

二者关键区别可以写成：

| 维度 | A11y-CUA | 本文 |
| --- | --- | --- |
| 核心研究对象 | accessibility-conditioned interaction behavior / trajectories | accessibility-oriented end-to-end task completion |
| 主要人群覆盖 | 重点 BLV | visual / hearing / motor / cognitive |
| Agent 是否被要求模拟用户操作方式 | 实验中显式改变 agent interaction condition | 默认不要求；主要评估用户目标和 handoff state |
| 主要 artifact | multimodal interaction dataset + empirical study，可用于 benchmarking | reusable executable benchmark suite |
| Evaluation | task success + trajectory/behavior analysis | task-specific deterministic end-state evaluators |
| 研究价值 | 揭示 AT-constrained interaction gap | 衡量不同 access needs 下的 user-oriented agent capability，并支持系统比较和方法开发 |

措辞注意：不要写“A11y-CUA 不是 benchmark”。更准确的是它**支持 benchmark-style evaluation，但不是与 OSWorld/本文同类型的可重置 executable task benchmark infrastructure**。

可以借鉴 A11y-CUA 的三点方法论，而不复制其研究设定：**(1)** 用受控对照区分 accessibility requirement 带来的额外难度；**(2)** 除最终 success 外分析 actions / time / recovery 和失败轨迹；**(3)** 把 assistive-technology state 的保持视为用户接管的一部分。本文进一步把第 (3) 点系统化为可执行任务中的 deterministic `FullSuccess` 条件。

### 3.3 与 GUIDE 等 user-assistance 工作的关系

GUIDE 类工作关注从用户 demonstrations 中理解行为状态、意图和何时提供帮助；本文关注 autonomous agent 是否能直接完成 accessibility-oriented digital workflows。二者一个更偏 intent/help prediction，一个偏 end-to-end execution。

---

## 4. Introduction 建议写法

Introduction 建议形成 5 段递进，而不是一开始介绍任务数量。

### 第 1 段：CUA 发展很快，但评测默认 homogeneous user

说明通用 computer-use agents 已经能处理浏览器、桌面和移动端多种 workflow，但主流 benchmark 通常假设标准 GUI、通用用户目标以及统一的交互条件。

问题不是这些 benchmark “不公平”，而是它们没有回答 accessibility-oriented assistance 这个问题。

### 第 2 段：现实用户的 access needs 会改变“任务成功”的定义

举 2–3 个非常具体的例子：

- hearing-access 用户不仅需要 agent 找到媒体信息，还可能要求 Live Caption 保持开启以便后续接管；
- motor-access 用户可能需要 agent 完成设置并保留 keyboard assistance 状态；
- cognitive-access 用户既可能需要把复杂信息压缩成 reminder/checklist/calendar，也可能需要 agent 直接代为完成 installation、configuration、route planning 等具有较高 sequencing / state-tracking / completion-recognition burden 的流程。

由此引出：普通 task completion ≠ accessibility-oriented task completion。

### 第 3 段：现有研究仍缺一个可执行 benchmark

先承认 A11y-CUA 的重要贡献：它通过真实 BLV 用户 trajectories 和 accessibility-conditioned CUA experiments 证明 accessibility 会暴露显著的 interaction gap。

然后指出本文缺口：仍缺少一个跨多种 access needs、可重复执行、具有 task-specific deterministic evaluators、面向最终 user outcome/handoff 的 benchmark，用来系统比较现代 CUAs 并进一步驱动方法设计。

### 第 4 段：本文做了什么

介绍 benchmark：

- 当前规模：[最终 task 数量]；
- 平台：[Windows / Android 最终确认后填写]；
- user groups：visual / hearing / motor / cognitive；
- task scenarios / categories：[最终数量]；
- modalities：text / image / video / audio；
- real applications + self-hosted deterministic services；
- deterministic evaluators；
- human/expert validity review。

随后介绍约 10 个代表性 baselines 和主要 empirical finding，具体数字等实验后填。

### 第 5 段：方法和贡献收束

写 failure analysis 如何导出新方法，再给出主要提升和 external benchmark 结果。

最后 contributions 建议控制在 3–4 点。

---

## 5. Contributions 建议

最终可写成四点，但每一点必须对应实验证据。

1. **Benchmark.** 提出一个 accessibility-oriented executable computer-use benchmark，覆盖多类 accessibility needs、日常 workflows、multimodal information 和 user-facing accessible handoff states，并具有 deterministic task-specific evaluators。

2. **Evaluation methodology.** 提出并验证 atomic fact-based deterministic evaluation：自然语言输出按必要事实评分、接受合理 surface variants，同时对 email/calendar/system state 等进行 structured state checking，减少 whole-string exact match 的 false negatives 和 loose substring matching 的 false positives。

3. **Empirical findings.** 系统评测约 10 个代表性 CUAs，揭示总体表现、user-group disparities、modality / task type / accessibility-state effects 以及主要 failure modes。

4. **Method.** 基于这些 failure patterns 提出改进方法，在本文 benchmark 上取得 evaluated systems 中最佳结果，并在已有通用 computer-use benchmarks 上验证泛化性/兼容性。

不要把“我们自己的 benchmark 上 SOTA”单独作为贡献。更重要的是：**方法解决的是 benchmark 揭示出的机制性问题，而且效果符合预测。**

---

## 6. Benchmark Section 的论文结构

### 6.1 Design Goals

建议列 5 个原则：

- user-centered accessibility relevance；
- realistic daily-life workflows；
- broad user-group and modality coverage；
- executable and reproducible environments；
- deterministic but semantically tolerant evaluation。

### 6.2 Task Construction

描述来源、任务改写、平台适配、initial state、gt trajectory、final state、人工验证。

工程细节放 README / Appendix，正文只描述原则和统计。

### 6.3 Documented User Need Taxonomy 与 task-level annotation

当前任务目录按四个 primary user groups（visual / hearing / motor / cognitive）组织，因此**目录层级仍是一级 user-group label 的 authoritative source**，不在 JSON 中重复增加 `user_group` 字段。`category` 与 user group 正交：`category` 描述 workflow（如 `access`、`mobility`、`health`、`consumption`），user group 描述任务主要面向的 access-need slice。因此应保留 cognitive × mobility、cognitive × access 等交叉覆盖，而不能用 workflow category 代替 disability/access-need taxonomy。

为了回答 reviewer 最关键的 construct-validity 问题——“这些 benchmark tasks 为什么能够代表真实 accessibility needs？”——本文不要求每个具体任务主题都在 survey 中逐字出现，而是建立一个**可复用的 Documented User Need Taxonomy**。这里的 documented user need 指已有用户调查、用户研究、W3C accessibility user requirements / design patterns、或官方 accessibility documentation 明确记录的 access barrier 或 support requirement。每个 task 再映射到一个或多个 documented needs。也就是说，证据需要证明的是“用户确实存在这种 access barrier/support need”，而不是证明某个具体商品、地点或网页本身是残障用户特有的需求。

证据按三层使用：**(1) empirical user evidence**，优先使用 WebAIM、ACMA、AFB、Pew 等 survey / user research；**(2) accessibility user requirements**，使用 W3C WAI / COGA 对具体 barriers 和 user needs 的规范化描述；**(3) platform documentation**，使用 Microsoft 等官方文档确认具体 accessibility feature 与其服务的 access need。三类证据承担不同作用：survey/user research 说明需求在真实用户中存在，W3C requirements 提供可操作的 construct 定义，platform documentation 说明 benchmark 中具体 support state 的 intended accessibility purpose。

#### Visual needs

| ID | Documented user need | Operational definition | Primary evidence |
| --- | --- | --- | --- |
| `V1` | Non-visual access to digital text and interface content | 通过 screen reader 或等价的非视觉表示读取、导航并操作网页、文档、文本和控件。 | WebAIM Screen Reader Survey #10; W3C Visual Disabilities — Abilities and Barriers |
| `V2` | Magnification and text enlargement | 通过 browser zoom、text sizing 或 screen magnification 放大文本、控件或整个显示内容，使其可感知和可操作。 | WebAIM Low Vision Survey #2; WCAG 2.2 Understanding 1.4.4 Resize Text |
| `V3` | Contrast and display-palette customization | 调整高对比度、前景/背景、反色或显示配色，以提高低视力用户的可读性。 | WebAIM Low Vision Survey #2; W3C Visual Disabilities; Microsoft color/contrast accessibility documentation |
| `V4` | Color-vision differentiation support | 当颜色差异难以区分时，使用 color filters 或非颜色线索来获取信息。 | WCAG 2.2 Understanding 1.4.1 Use of Color; Microsoft color-filter documentation |
| `V5` | Access to non-text visual information | 获得图片、地图、图表、扫描件、标签等 visual-only / poorly-described content 的等价信息。 | WebAIM Screen Reader Survey #10; WCAG Understanding 1.1.1 Non-text Content |
| `V6` | Accessible CAPTCHA and verification | 在 verification 依赖视觉感知时，通过替代 modality 或 delegated assistance 完成验证。 | WebAIM Screen Reader Survey #10; WCAG Understanding 1.1.1 Non-text Content |

#### Hearing needs

| ID | Documented user need | Operational definition | Primary evidence |
| --- | --- | --- | --- |
| `H1` | Speech-to-text access through captions or transcripts | 通过 captions、live captions 或 transcript 获取 speech 和相关 non-speech audio 信息。 | W3C Making Audio and Video Media Accessible; ACMA captioning consumer research; AFB *Innovation for Access* caption survey analysis |
| `H2` | Caption readability and language customization | 调整 caption 的语言和视觉呈现，使字幕适合当前媒体且可读。 | Microsoft Make Windows easier to hear; ACMA captioning consumer research |
| `H3` | Visual and persistent alternatives to auditory notifications | 用视觉提示替代仅声音提醒，并让 notification 保留足够时间供用户察觉和阅读。 | Microsoft Make Windows easier to hear |
| `H4` | Single-channel access to stereo audio | 将 stereo channels 合并为 mono，避免使用单侧听力/单耳设备时遗漏某一声道的信息。 | Microsoft Make Windows easier to hear |
| `H5` | Verification without relying on hearing | 当 verification 依赖听觉感知时，使用非听觉替代方式或 delegated assistance。 | WCAG Understanding 1.1.1 Non-text Content |

#### Motor needs

| ID | Documented user need | Operational definition | Primary evidence |
| --- | --- | --- | --- |
| `M1` | Alternative text entry without a physical keyboard | 当 physical keyboard 难以操作时，通过 on-screen keyboard 或其他 alternative input 输入文本。 | WebAIM Motor Disability Survey; Microsoft Accessibility tools for mobility |
| `M2` | Sequential modifier-key input | 将需要同时按下多个键的 shortcut 改为逐键输入。 | Microsoft Accessibility tools for mobility (Sticky Keys) |
| `M3` | Keystroke filtering and sensitivity control | 过滤意外重复/短促按键并调整键盘灵敏度。 | Microsoft Accessibility tools for mobility (Filter Keys) |
| `M4` | Alternative pointer control or delegated pointing | 当传统鼠标操作困难时，用 keyboard、speech/其他 alternative input，或由 agent 代理完成 pointer activation。 | Microsoft Accessibility tools for mobility; WebAIM Motor Disability Survey |
| `M5` | Reduced press-hold and dragging demand | 避免或减少要求持续按住、拖动并精确释放的动作。 | WCAG 2.2 Understanding 2.5.7 Dragging Movements |
| `M6` | Mouse-button and handedness customization | 根据 reach、strength、dexterity 或单侧运动需求调整 primary mouse button 等 pointer settings。 | Microsoft Accessibility tools for mobility |
| `M7` | Reduced pointer precision, repetition, and timing demand | 避免/代理反复精确 target acquisition、严格 timing 或 fine-motor pointer 操作。 | WebAIM Motor Disability Survey; WCAG 2.2 Understanding 2.5.7 |

#### Cognitive needs

| ID | Documented user need | Operational definition | Primary evidence |
| --- | --- | --- | --- |
| `C1` | Focus, readability, and simplification | 降低 distraction、visual/cognitive clutter 或 reading load，使 attention、language processing 和 comprehension 更容易持续。 | W3C Cognitive Accessibility; COGA Support Simplification |
| `C2` | Memory externalization and short-term retention support | 通过 notes、checklists、persistent cues 或 delegated assistance，减少对 working memory / short-term retention 的依赖。 | COGA Do Not Rely on Users Calculations or Memorizing Information |
| `C3` | Time and prospective-memory support | 使用 reminders、calendar、timer 和 persistent time cues 管理 appointment、deadline、interval 和 future action。 | COGA Provide Reminders |
| `C4` | Planning, sequencing, task-state tracking, and completion recognition | 降低 unfamiliar / multi-step workflow、维持 context、受打断后恢复、progress tracking 和识别 completion 的负担。 | COGA Make Each Step Clear; COGA Task Expectations; COGA Provide Feedback; Pew technology-setup evidence（仅作补充） |
| `C5` | Decision and choice support | 帮助比较 alternatives、应用约束、理解 consequences 并选择合适 option。 | COGA Clearly State Results and Disadvantages of Choices |
| `C6` | Important-information extraction and prioritization | 从 dense / mixed / distracting information 中找出并保留少量重要事实或 actions。 | COGA Make Important Tasks and Information Easy to Find; COGA Support Simplification |
| `C7` | Calculation, counting, copying, and cross-source reconciliation support | 减少 arithmetic/counting、copying、短期保持信息以及跨 source/step reconciliation 的需求。 | COGA Do Not Rely on Users Calculations or Memorizing Information |
| `C8` | Error prevention and safety-critical guidance | 让高风险操作、scam、health/safety guidance 和易错 choices 更容易理解并正确执行。 | COGA Design Forms to Prevent Mistakes; COGA Supported Choice; COGA Important Information |

每个 task JSON **只新增 `need_ids`**，保存一个或多个 taxonomy ID。`[]` 只允许在构建阶段暂时表示 unresolved mapping；正式发布任务必须至少有一个可辩护的 need ID，否则应继续重写或暂缓纳入。task–need fit 和“目标 user group 是否会自然提出这种请求”仍然是构建阶段必须人工审核的问题，但应保存在单独的 review checklist / curation notes 中，而不是成为 benchmark runtime metadata。这样可以避免把主观、会随任务修改而变化的审核状态固化进任务定义。

论文中的核心 claim 应写成：**tasks are grounded in documented accessibility user needs**，而不是在没有 target-user study 时声称 “the benchmark satisfies users' real needs”。WebAIM Screen Reader Survey #10 明确说明样本未受控，WebAIM Motor Disability Survey 也只有 46 个 convenience-sample respondents，因此这些数据用于证明某类 barrier/support need 的存在和合理性，而不是估计 population prevalence。W3C / Microsoft documentation 同样是 construct / feature-purpose evidence，而不是 prevalence evidence。Direct target-user validation 如果无法完成，应作为 limitation / future validation 诚实说明，并用 expert review、task-level need mapping 与 naturalness curation 加强 construct validity。

**主要 evidence sources（写论文时优先引用）：**

- WebAIM, *Screen Reader User Survey #10 Results* (2024): https://webaim.org/projects/screenreadersurvey10/
- WebAIM, *Survey of Users with Low Vision #2 Results* (2018): https://webaim.org/projects/lowvisionsurvey2/
- WebAIM, *Survey of Users with Motor Disabilities* (2013): https://webaim.org/projects/motordisabilitysurvey/
- W3C WAI, *Visual Disabilities — Abilities and Barriers*: https://www.w3.org/WAI/people-use-web/abilities-barriers/visual/
- W3C WAI, *Making Audio and Video Media Accessible*: https://www.w3.org/WAI/media/av/
- W3C WAI, *Cognitive Accessibility*: https://www.w3.org/WAI/cognitive/
- W3C COGA supplemental design patterns: https://www.w3.org/WAI/WCAG2/supplemental/patterns/
- W3C WCAG 2.2 Understanding documents, especially Non-text Content, Resize Text, Use of Color, and Dragging Movements: https://www.w3.org/WAI/WCAG22/Understanding/
- Microsoft, *Make Windows easier to hear*: https://support.microsoft.com/en-us/accessibility/windows/make-windows-easier-to-hear
- Microsoft, *Accessibility tools for mobility*: https://support.microsoft.com/en-US/accessibility/accessibility-tools-for-mobility
- ACMA, *Use and experience of captioning: consumer research* (2023): https://www.acma.gov.au/publications/2023-05/report/use-and-experience-captioning-consumer-research-support-acmas-captioning-quality-standard-review
- American Foundation for the Blind, *Innovation for Access* (2026; analysis of a 2025 survey): https://www.afb.org/research-and-initiatives/ai-series/innovation-access
- Pew Research Center, *Navigating technological challenges* (2021): https://www.pewresearch.org/internet/2021/09/01/navigating-technological-challenges/

`paper/documented_user_need_taxonomy.json` 作为 taxonomy 和 source registry 的 machine-readable source of truth；正文只保留压缩后的 taxonomy、evidence hierarchy 和 representative statistics，完整 mapping / source registry 可放 Appendix 或 supplement。

### 6.4 Deterministic Evaluation

正文强调三个原则：

1. structured state > serialized-text substring；
2. natural-language answer 用 atomic facts，不用 whole-answer exact；
3. semantic tolerance 与 fact completeness 同时保证。

紧凑规则 DSL 可以放一个短例子：

```text
"text"              = required expression
["a", "b"]          = any_of
{"all_of": [A, B]}  = all children required
{"regex": "..."}    = constrained pattern
```

自然语言建议称为 **atomic fact-based deterministic evaluation**，不要称“semantic evaluator”，避免 reviewer 误以为 evaluator 做开放式 semantic inference。

### 6.5 Human / Expert Validation

这个实验建议正式进入论文，而不是只做内部 QA。

至少评价：

- realism；
- accessibility relevance；
- clarity / determinacy；
- support appropriateness。

理想设计：每个 task 或代表性 sample 至少两位独立 reviewer；如果资源允许，至少部分 reviewer 具有 accessibility expertise 或 lived experience。报告平均分、分布、inter-rater agreement、adjudication procedure，以及被 revise/reassign/remove 的数量。

这里的作用是证明 **construct validity**，不是证明模型能力。

### 6.6 Evaluator Validity Study

建议做一个独立的小实验，将当前 evaluator 设计从“实现细节”变成 methodology contribution。

对自然语言 evaluator 构造：

- canonical correct；
- semantically equivalent variant；
- missing-fact answer；
- wrong-value near miss；
- negated answer；
- formatting variant。

比较：

1. whole exact match；
2. naive substring / point matching；
3. 本文 atomic fact-based evaluator。

用人工 correctness label 作为参考，报告 precision / recall / F1 或 agreement。

预期 story：exact match 高 false negative；naive substring 高 false positive；本文方法在保持 deterministic/reproducible 的同时更接近 human correctness judgment。

---

## 7. Baseline 实验设计

### 7.1 Baseline 选择原则

约 10 个足够，不需要为了数量堆模型。关键是覆盖不同 agent design families，例如：

- strong proprietary native computer-use agent；
- strong general multimodal model + agent scaffold；
- GUI-specialized open-source agent；
- screenshot-centric agent；
- structured observation / accessibility-tree-aware agent；
- planning-heavy agent；
- lightweight/reactive agent。

最终 baseline 列表按投稿时间的代表性模型更新。

### 7.2 Main metric

主指标建议仍是 task success rate，因为 benchmark 核心是 end-to-end user goal completion。

可选辅助指标：

- partial fact/state score（仅用于诊断，不能替代 success rate）；
- steps / actions；
- wall-clock time；
- token / inference cost；
- completion-with-correct-accessibility-state rate；
- ordinary outcome success vs full accessible-handoff success。

最后一个尤其值得考虑。可以定义：

- `TaskOutcome`: 普通任务目标是否完成；
- `FullSuccess`: TaskOutcome + required accessibility/handoff state 均完成；
- `HandoffGap = TaskOutcome - FullSuccess`: agent 完成 underlying task、但没有留下正确 accessible state 的比例。

这个差值可以直接量化“事情做完了，但用户仍无法按要求接管”的问题。参考 A11y-CUA 的 outcome + process 分析，建议同时保存 trajectory，并把 `actions per success`、completion time、recovery/backtracking rate 作为诊断指标，而不替代主 success metric。

### 7.3 Breakdown

至少报告：

- overall；
- user group；
- category；
- modality；
- accessibility feature required / not required；
- single-app vs cross-app；
- difficulty；
- task output type；
- Windows / Android（如果最终双平台）。

不要同时展示几十个 breakdown；正文挑最能解释研究问题的，剩余放 Appendix。

---

## 8. Failure Analysis

Failure taxonomy 应由真实 trajectories 归纳，而不是预先硬套 A11y-CUA 的 perception/cognitive/action 三分类。

可以先用以下候选 coding scheme，实验后再合并：

1. **Accessibility-state failure**：没有开启、保持或验证用户需要的 feature；
2. **Information acquisition failure**：没有正确获得 text/audio/video/page 中的关键信息；
3. **Grounding / focus failure**：定位错误、焦点丢失、控件状态判断错误；
4. **Task-state tracking failure**：忘记已经完成什么、下一步是什么；
5. **Constraint failure**：满足主目标但违反用户约束；
6. **Artifact construction failure**：note/email/calendar/document 的字段或内容不完整；
7. **Cross-app transfer failure**：信息在应用之间传递错误；
8. **Completion verification failure**：做完前置步骤但没有 Save / Apply / Submit / final check；
9. **Recovery failure**：遇到 popup、页面变化、错误操作后无法恢复；
10. **Evaluator-near-miss but semantically wrong**：用于检查 benchmark/evaluator 是否仍存在漏洞。

建议两位 annotator 对 stratified sample 的 failed trajectories 独立编码，报告 agreement；不必人工标注全部运行。除 failure category 外，可同步记录是否发生 repeated retry、backtracking、focus recovery、遗漏 Save/Apply/Submit 等 process signals。A11y-CUA 的经验值得借鉴的是“定量结果 → trajectory inspection → failure mechanism”的分析链，而不是直接复用其 perception/cognitive/action 三分类。

最重要的不是 taxonomy 本身，而是回答：

**哪些 failure 在什么 user group / task factor / agent family 下显著集中？**

---

## 9. 方法部分的 story

现在不要提前把方法写死。方法应该在 baseline failure analysis 后最终定型。

论文中的逻辑模板：

> Our analysis reveals that current agents frequently fail not because they cannot execute primitive GUI actions, but because they do not consistently maintain user-specific accessibility requirements, task state, and completion conditions across multimodal and multi-application workflows. We therefore introduce [METHOD], which explicitly models [failure mechanisms].

候选模块方向可以包括，但只有实验真正支持时才采用：

- accessibility-aware requirement representation；
- persistent task / constraint state；
- multimodal evidence aggregation；
- structured UI / accessibility-state observation；
- final-state verification / self-check；
- adaptive action strategy；
- handoff-state verifier。

方法必须回答两个问题：

1. 为什么这个机制是 benchmark analysis 揭示出来的，而不是随便加的 agent trick？
2. 为什么 gains 应该集中发生在特定 failure slices？

### 9.1 Method ablation

每个模块都需要对应 failure hypothesis。例如：

- 去掉 persistent state → cross-app / cognitive-support tasks 明显下降；
- 去掉 accessibility-state verification → access-feature tasks 下降；
- 去掉 final verifier → Save/Apply/Submit 类型 failure 回升。

这种 ablation 比单纯“模块 A +2.1，模块 B +1.7”更有解释力。

### 9.2 Cross-benchmark evaluation

在至少一个或多个已有 computer-use benchmark 上测试本文方法。

目的不是要求 accessibility-specific method 在普通 benchmark 上也必须大幅 SOTA，而是证明：

- 改进不是 evaluator-specific hack；
- 新机制没有严重损害 general computer-use capability；
- 如果还能提升，则说明这些机制对 general robustness 也有价值。

论文中可以称为 **cross-benchmark generalization / transfer**，不必把它包装成 benchmark 合法性的必要条件。

---

## 10. 推荐结果表和图

### Figure 1：Benchmark overview / teaser

画四类用户需求 → 多种真实 workflow/modalities → agent → ordinary task outcome + accessible handoff state → deterministic evaluator。

这是最应该放首页的图。

### Table 1：与已有 benchmark / dataset 对比

建议维度：

- executable environment；
- end-to-end tasks；
- deterministic evaluators；
- multimodal input；
- accessibility-oriented user goals；
- multiple access-need groups；
- accessibility/handoff state evaluation；
- human trajectory dataset（A11y-CUA 的优势要诚实体现）。

不要设计成“所有列我们都是 ✓、别人都是 ✗”的 marketing table。给 prior work 保留它们真正独特的优势，可信度更高。

### Table 2：Benchmark statistics

按 user group、category、modality、apps、feature requirement、single/cross-app 展示 task 数。

### Table 3：Main baseline results

行 = 约 10 个 agents；列至少包括 Overall + 四个 user groups。更多 breakdown 放后续表/附录。

### Figure 2：User-group performance disparity

每个模型在 visual/hearing/motor/cognitive 上的分布或 gap。

### Figure 3：Task factors / accessibility features

展示 modality、handoff、cross-app、AT state 等因素对应的成功率变化。

### Figure 4：Failure taxonomy

不同 agent family / user group 的 failure composition。

### Table 4：Our method vs baselines

突出 overall + hard slices + user groups。

### Table 5：Ablation

模块与对应 failure slice。

### Table 6：Cross-benchmark results

本文 benchmark + OSWorld / WindowsAgentArena / AndroidWorld 等最终选定 benchmark。

---

## 11. Claim → Evidence 对照表

这个表建议在整个项目过程中一直维护。

| Claim | 必须有的证据 |
| --- | --- |
| 现有 CUA 对 accessibility-oriented user goals 能力不足 | 多个强 baseline 的总体 success rate；不能只挑弱模型 |
| 不同 user groups 面临不同程度/类型的困难 | group-wise results + significance/CI + failure breakdown |
| 这不是普通 GUI difficulty 的简单复现 | task-factor analysis；如果有 matched tasks 更强 |
| benchmark task 真正具有 accessibility relevance | documented-user-need taxonomy + task-level mapping/naturalness curation + source grounding + human/expert validation |
| evaluator 合理且不会因为表面措辞错杀正确答案 | evaluator validity study |
| accessible handoff 是额外真实难点 | TaskOutcome vs FullSuccess 对比，或 feature-state failure 统计 |
| 本文方法解决了 benchmark 揭示的机制 | targeted slice gains + failure reduction + ablation |
| 方法不是 benchmark/evaluator 特化 hack | cross-benchmark results + qualitative mechanism analysis |
| 本文比已有 accessibility work 提供新的研究能力 | 与 A11y-CUA / GUIDE 的 artifact 和 research-question 区分 |

如果某个 claim 找不到对应 evidence，就删掉 claim 或补实验，不要靠 Discussion 补叙事。

---

## 12. Reviewer 最可能攻击的点，以及正文提前怎么堵住

### Concern A：为什么 agent 要使用 assistive technology？

回答：**默认并不要求 agent 模仿用户使用 AT。** AT/accessibility state 是用户侧的 handoff requirement。agent 的目标是替用户完成任务，并留下用户可继续访问的状态。

Introduction 必须早说，否则 reviewer 很容易误解。

### Concern B：这和 A11y-CUA 有什么本质区别？

回答：A11y-CUA 重点是 rich human/agent trajectory dataset + AT-conditioned interaction study；本文是覆盖多个 access-need groups 的 reusable executable task benchmark，以 deterministic end-state evaluators 测 user-oriented task completion 和 accessible handoff。

不要贬低 A11y-CUA；把二者写成 complementary。

### Concern C：cognitive tasks 是否只是普通 long-horizon tasks 套了 disability label？

回答：用 `C1–C8` documented cognitive needs 做 task-level mapping，released task JSON 只保存 `need_ids`；task–need fit 与 naturalness 在构建阶段通过独立 review checklist 审核。只有能自然 operationalize reading simplification、memory externalization、prospective-memory/time support、planning/task-state、decision support、important-information extraction、cross-source reconciliation 或 error-prevention 等 documented needs 的任务保留在 cognitive group，再用 human/expert validation 做第二层 construct-validity check。

### Concern D：自然语言 evaluator 是否太 brittle 或太宽松？

回答：atomic fact-based deterministic evaluation + structured state evaluator + evaluator validity study。

### Concern E：自己的 benchmark 上提出方法再取得最好结果，是不是 overfit？

回答：这是 benchmark-driven method development 的正常研究路径。为了证明方法价值，进一步报告 cross-benchmark performance 和 failure-specific ablations，而不是仅凭本 benchmark 单一总分声称通用 SOTA。

### Concern F：200 tasks 是否足以支持四类用户？

回答要依赖最终 task distribution。需要保证每组有足够覆盖，并报告 bootstrap CI / uncertainty。如果某个 group 明显样本太少，就减少过强的跨组结论。

### Concern G：disability group 是否过度简化真实用户？

论文措辞尽量用 **access needs / accessibility scenarios**，group label 主要用于 benchmark organization 和 aggregate analysis。承认同一 disability group 内部需求高度异质，不声称四个 label 能完整代表所有用户。

---

## 13. Benchmark curation：当前 task-need review 结论

第一轮 task-level grounding 曾标出 15 个 `weak` 和 8 个 `unsupported` task。重新检查实际 task implementation 后，不应机械地按旧标签删任务，而应区分“旧 review 判断过严”和“任务本身确实需要重写”。当前处理原则如下：

- **保留但重新论证的任务**：`access-docker_install` / `access-spotify_install` 归入 `C4`，其依据是 unfamiliar multi-step setup / completion-recognition burden；Pew 的 older-adult setup-help 数据只作为 tech-readiness 的补充证据，不能写成“年龄 = cognitive disability”。`service-cms_product_record` 归入 `C2+C7`，因为 task 本身要求用 spreadsheet checklist 外化并跨 CMS/表格复制、核对多个字段。
- **cognitive CAPTCHA 重构**：保留 audio-code、click-sequence、character-count 等能自然实例化 short-term retention、sequencing、focus/counting burden 的 challenge；原 cognitive slice 中以 distorted visual perception、image recognition、patch selection 为核心的 3 个 challenge 已替换为 `captcha-math_3`、`captcha-click_sequence_4`、`captcha-count_chars_3`。CAPTCHA 仍作为 stress-test category，但 task-level need mapping 必须根据 challenge 的实际 interaction demand，而不是根据 CAPTCHA 名称推断。
- **consumption task 重构**：generic exact-product lookup 改为从 persistent shopping reminder 恢复需求；review-heavy 商品选择删除“数 supporting statements + 多级 tie-break”这类 benchmark-engineered rule，改成用户可自然表达的 product constraints / preferences，再由 agent 完成 comparison/choice。
- **information task 重构**：forum task 明确要求把长讨论压缩为 one-sentence plain-language takeaway；Wikipedia task 的输出定位为 persistent reference artifact，而不是单纯 search-and-copy。
- **cognitive × mobility 保留，但改变 construct**：保留 mobility workflow coverage，但任务核心改为把复杂 station/route information 压缩成可跟随的短 transfer note / step sequence；不再把 step-free、mobility-aid access 本身当成 cognitive need。
- **旧 review 的 false positives**：`visual/captcha-hold_button_2`、`visual/captcha-robot_checkbox_2` 和 `motor/captcha-robot_checkbox_1` 不再因为 challenge 看起来“更像 motor/visual”就判错配。visual slice 的核心是 blind/non-visual user 的 verification delegation (`V6`)；motor robot-checkbox 对应 conventional pointer use 困难时的 alternative/delegated pointing (`M4`)。

当前 released 200 tasks 均应具有非空 `need_ids`；若后续新 task 无法自然映射到 taxonomy，应在构建阶段重写或暂缓发布，而不是强行给一个 need ID。

## 14. Abstract 写作模板

先不要填具体数字，实验结束后按这个逻辑压缩：

> Computer-use agents are increasingly capable of completing everyday digital tasks, yet existing evaluations largely assume a homogeneous user and standard interaction setting. We introduce [BENCHMARK], an executable benchmark for evaluating whether agents can complete real-world tasks on behalf of users with diverse accessibility needs while preserving user-facing accessible handoff states. [BENCHMARK] contains [N] tasks spanning visual, hearing, motor, and cognitive accessibility scenarios, multiple applications and modalities, and uses task-specific deterministic evaluators with atomic fact-based natural-language scoring. Evaluating [K] representative agents reveals [MAIN FINDING 1], with substantial variation across [GROUPS/FACTORS], and identifies [MAIN FAILURE MODES]. Based on these findings, we introduce [METHOD], which [ONE-SENTENCE MECHANISM] and improves success by [X] points over the strongest baseline while [preserving/improving] performance on [EXTERNAL BENCHMARKS]. Our results show that strong general computer-use performance does not guarantee reliable accessibility-oriented assistance and provide a reproducible foundation for developing agents that better serve heterogeneous user needs.

注意最后一句不要写“agents for disabled users”这种过宽结论，更准确的是“agents that better serve heterogeneous accessibility needs”。

---

## 15. 标题候选

方法没定之前，标题最好先以 benchmark 为主：

1. **[Name]: Benchmarking Computer-Use Agents for Accessibility-Oriented User Tasks**
2. **[Name]: Evaluating Computer-Use Agents Across Diverse Accessibility Needs**
3. **Beyond the Standard GUI: Benchmarking Computer-Use Agents for Accessibility-Oriented Assistance**
4. **Accessible Handoff: Evaluating Computer-Use Agents for Users with Diverse Accessibility Needs**

如果最终方法贡献非常强，再考虑标题同时体现 benchmark + method；否则 benchmark 名字本身最清晰。

---

## 16. 推荐的整篇 ACL 结构

```text
1 Introduction
2 Related Work
  2.1 Computer-Use Agent Benchmarks
  2.2 Accessibility and User-Assistance Datasets
  2.3 Evaluation of GUI Agents
3 Benchmark
  3.1 Design Goals and Accessibility-Oriented Task Definition
  3.2 Task Collection and Construction
  3.3 Task Taxonomy and Statistics
  3.4 Deterministic End-State Evaluation
  3.5 Human / Expert Validation
4 Benchmarking Current Computer-Use Agents
  4.1 Baselines and Experimental Setup
  4.2 Overall Results
  4.3 Performance Across Accessibility Needs
  4.4 Task-Factor Analysis
5 Failure Analysis
6 [Our Method]
  6.1 Motivation from Benchmark Failures
  6.2 Method
7 Method Evaluation
  7.1 Main Results
  7.2 Targeted Slice Analysis
  7.3 Ablations
  7.4 Cross-Benchmark Generalization
8 Discussion
9 Limitations and Ethical Considerations
10 Conclusion
```

如果 ACL 页数吃紧，可以把 Human/Expert Validation 和 Evaluator Validity Study 各压成半页，把详细 protocol 放 Appendix；Failure Analysis 不能压得太狠，因为它承担从 benchmark 到 method 的桥梁作用。

---

## 17. 最终 paper story 的压缩版本

写作过程中如果主线开始散掉，就回到下面六句话：

1. **现有 CUA benchmark 默认的是通用用户目标，而不同 accessibility needs 会改变任务成功的要求。**
2. **我们不要求 agent 模仿残障用户操作；我们要求它替用户可靠完成任务，并留下用户可访问、可继续接管的状态。**
3. **为此，我们构建一个覆盖 visual/hearing/motor/cognitive needs、真实 workflows 和 multimodal information 的 executable benchmark，并用 deterministic end-state evaluators 评分。**
4. **约 10 个代表性 CUAs 的评测显示：高通用 GUI 能力并不等价于高 accessibility-oriented assistance 能力，而且不同 user groups 暴露出不同 failure patterns。**
5. **这些 failure 不是排行榜附带现象，而是直接指导我们设计新的 agent 改进方法。**
6. **新方法在本文 benchmark 上显著提升，并通过 existing computer-use benchmarks 验证不是只针对本 benchmark 的特化。**

整篇论文的每个 section 都应该服务于这六句话中的至少一句。
