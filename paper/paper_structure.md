# 中文论文框架：Accessibility-Oriented Computer-Use Agent Benchmark

> 用途：按最终 ACL/ARR 论文结构组织 paper story、benchmark construct、实验设计和 claim–evidence 关系。任务 JSON、evaluator 实现、环境维护等工程规范仍以 `README.md` 为准。本文档优先回答“论文为什么成立、每一节要证明什么、证据放在哪里”。

## 0. 全文主线与术语约束（写作时始终遵守）

### 0.1 一句话主线

现有 computer-use agents（CUAs）主要在“通用用户目标 + 标准 GUI + 通用完成条件”下被评测，但真实用户具有不同的 accessibility needs。一个 agent 即使能完成 underlying GUI goal，也不意味着它能可靠处理由 access need 带来的信息获取、交互代理、输出表示、accessibility configuration 和 continuation requirements。本文构建一个可执行、可重置、端到端、确定性评测的 accessibility-oriented computer-use benchmark，系统评测代表性 CUAs，分析不同 user groups、modalities、workflow types 和 accessibility requirements 下的系统性 failure，并基于这些 failure patterns 设计改进方法，同时在已有通用 computer-use benchmark 上验证泛化性。

### 0.2 最重要的概念边界

本文**不要求 agent 模拟残障用户的操作轨迹，也不要求 agent 自己依赖 assistive technology (AT)**。Agent 可以使用其正常的视觉、鼠标、键盘或 structured observation 能力。我们评估的是：给定一个具有 documented access need 的用户目标，agent 是否能完成任务，并满足该 access need 对最终结果或用户环境提出的额外要求。

建议全文使用下面的核心定义：

> **An accessibility-oriented computer-use task asks an agent to complete an everyday digital goal on behalf of a user with a documented access need, where that need materially changes what information must be acquired, what interaction burden is delegated, what user-facing output must be produced, or what accessibility/continuation state must be preserved.**

因此：

> **Accessibility relevance ≠ agent-side AT usage.**

AT 是 access need 的一种 manifestation，不是 benchmark 的定义标准。

### 0.3 Accessibility-oriented 与 ordinary GUI task 的本质区别

底层 life goal 可以完全相同。残障用户同样会安装软件、购物、查路线、预约、发邮件。本文不需要制造“只有残障用户才会做”的特殊任务。

区别在于 **documented access need 是否实质性改变 success construct**：

\[
S_{ordinary}=\text{underlying goal completed}
\]

\[
S_{access}=\text{underlying goal completed}\land\text{access-need-specific requirement satisfied}
\]

一个 task 的 accessibility relevance 至少来自以下四类机制之一：

1. **Information access**：access need 改变 agent 必须替用户获取的信息路径，例如 visual-only information、speech/audio information、dense information extraction。
2. **Delegated interaction burden**：agent 代理 documented perceptual、motor、memory、planning、sequencing、decision 或 completion-recognition burden。
3. **Accessible user-facing output**：access need 改变最终 artifact/representation，例如 transcript、plain-language summary、persistent note、checklist、reminder、structured transfer instruction。
4. **Persistent accessibility / continuation state**：agent 需要配置或保留用户可能依赖的 accessibility setting 或 user-facing state，使用户保有后续 inspect、understand、continue 或 take over 的能力。

注意：一个 task 可以同时属于多类。

### 0.4 Accessible continuation state，而不是假设用户一定“handoff”

建议正文以 **accessible continuation state** 或 **continuation readiness** 作为主术语，弱化“用户一定马上接管”的暗示。

定义：

> **Accessible continuation state.** A user-facing system state in which the requested accessibility configuration and persistent artifacts remain available after task completion, so that the user retains the option to inspect, understand, continue, or take over the workflow under their access requirements.

Benchmark 不需要知道用户之后是否真的继续操作。它评估的是：**agent 是否保留了继续操作的可能性，而不是预测未来行为。**

例如，task 要求开启 Sticky Keys 后再完成其他配置。Agent 后续可能根本不使用 Sticky Keys；这不构成问题，因为 Sticky Keys 是 user-facing environment state，而不是 agent execution mechanism。只要该 setting 与用户 documented keyboard-access need 有合理关系，并且任务要求其保持，最终 evaluator 就应检查它。

推荐 reviewer-facing 表述：

> We distinguish **agent-side tool use** from **user-side accessibility state**. An agent may use its preferred interaction mechanisms while configuring or preserving captions, magnification, keyboard assistance, or other accessibility features for the user. We do not assume that the user necessarily continues the interaction after every task; rather, we evaluate whether the agent preserves the **option for accessible continuation**.

### 0.5 Task validity counterfactual：防止“普通任务 + 随机 accessibility toggle”

构建和 human validation 时加入一个核心检查：

> **If the accessibility-specific requirement were removed, would the task definition, required information/output, delegated burden, or success condition remain essentially unchanged?**

- 如果 access need 改变了 information、burden、output 或 continuation state，task 有明确 accessibility construct。
- 如果唯一差异只是任意附加一个与用户需求无关、也无 continuation value 的 accessibility toggle，则 task relevance 很弱，应重写或移除。

不要使用“agent 是否真的用上该 AT”作为 task validity 判据；这是错误维度。

### 0.6 最核心研究问题

**RQ1.** Current CUAs 能否可靠完成 accessibility-oriented user goals？整体 success 如何，不同 visual / hearing / motor / cognitive slices 是否存在显著差异？

**RQ2.** Accessibility-oriented requirements 相比 ordinary GUI completion 带来什么额外困难？重点分析 information access、delegated burden、accessible output、persistent accessibility/continuation state；如果资源允许，构造 small matched subset 控制 underlying goal。

**RQ3.** 不同 user groups / documented needs 是否暴露不同 failure signatures？

**RQ4.** 哪些 agent design assumptions（observation、planning、action space、state tracking、structured UI/accessibility information）与这些 failure 相关？

**RQ5.** 基于 benchmark failure mechanisms 的针对性方法，能否改善对应 slices，同时保持 general computer-use capability？

全文逻辑：

> **Benchmark construct → systematic evaluation → failure mechanism → targeted method → predicted slice gains → cross-benchmark validation.**

---

# 1 Introduction

Introduction 建议 5 段，围绕“为什么现有 benchmark 没回答这个问题”，不要从 task 数量开始。

## 1.1 Paragraph 1：CUA 能力快速发展，但 evaluation 默认 homogeneous user goal

说明 CUAs 已能处理浏览器、桌面和移动端真实 workflows；主流 benchmark 主要回答“agent 能否完成通用 GUI goal”。这些 benchmark 本身没有问题，但通常不显式建模 heterogeneous accessibility needs，也不评估 access-need-specific completion conditions。

避免使用“existing benchmarks are unfair / inaccessible”这类攻击性 framing。更准确的是：它们测的是不同 construct。

## 1.2 Paragraph 2：Access needs 改变的不是生活目标，而是可用完成条件

核心论点：

> **Accessibility-oriented does not mean disability-exclusive. Many underlying goals are shared with general users; what changes is the barrier and what counts as a usable completion state.**

建议用 3 个不同机制的例子，而不是都举“开 AT”：

- hearing：从视频中的 spoken content 获得信息，并提供 non-auditory representation；必要时保持 Live Caption 等 state；
- motor：agent 代理高精度 pointer、dragging、repetitive input 或配置 keyboard assistance；
- cognitive：把 dense/multi-step information 转为 persistent note/reminder/checklist，或代理 sequencing、task-state tracking、completion recognition burden。

引出：

\[
\text{ordinary completion} \neq \text{accessibility-oriented completion}
\]

## 1.3 Paragraph 3：为什么不是“要求 agent 使用 assistive technology”

这一段建议 Introduction 就明确，否则 reviewer 容易误解整个 benchmark。

> Our goal is not to force an agent to interact as a disabled user would. Accessibility features may be part of the user-facing environment or success condition, but the agent may use its own visual, pointer, keyboard, or structured observations. We evaluate whether the user’s documented access requirement is satisfied, not whether the agent itself relies on assistive technology.

接着引入 **accessible continuation state**：如果用户要求或依赖某个 accessibility configuration，agent 完成 underlying task 后不应破坏它；benchmark 只要求保留用户继续操作的 option，不假设用户一定马上接管。

## 1.4 Paragraph 4：Research gap 与 benchmark

先承认 A11y-CUA 等工作说明 accessibility conditions 会显著改变 human/agent interaction behavior；再指出仍缺少一个跨多类 access needs、以 everyday digital goals 为单位、可重置执行、具 task-specific deterministic evaluators 的 benchmark，用于测 user-oriented end-to-end completion。

介绍本文 benchmark：

- [N] executable tasks；
- platform：[最终确认]；
- four top-level functional groups：visual / hearing / motor / cognitive；
- documented user need taxonomy；
- workflow categories informed by ICF Activities and Participation；
- text / image / video / audio 等 modalities；
- real applications + deterministic/self-hosted services；
- deterministic end-state evaluation；
- human/expert construct validation。

## 1.5 Paragraph 5：Findings、method、contributions

实验结束后填主要数字。逻辑顺序：

1. 代表性 CUAs 的 overall + group-wise result；
2. strongest empirical finding；
3. failure mechanism；
4. 由 failure 导出的 method；
5. benchmark + external benchmark 结果。

### Contributions 建议

1. **Benchmark.** 一个 executable accessibility-oriented CUA benchmark，以 documented access needs 为 grounding，覆盖 heterogeneous functional groups、daily-life workflows、multimodal information、accessible outputs 与 continuation states。
2. **Evaluation methodology.** Task-specific deterministic end-state evaluation，结合 structured state checking 与 atomic fact-based natural-language scoring，并通过 evaluator validity study 验证。
3. **Empirical findings.** 系统评测代表性 CUAs，揭示 user-group / need / modality / workflow / continuation-state disparities 和 failure patterns。
4. **Method.** 基于 failure analysis 的 targeted method，在预测 slices 上取得改善，并通过 cross-benchmark experiments 检查非 benchmark-specific overfitting。

---

# 2 Related Work

## 2.1 General computer-use agent benchmarks

可按三类组织：

- Web agents：WebArena、VisualWebArena 等；
- OS/mobile：OSWorld、WindowsWorld / WindowsAgentArena、AndroidWorld 等；
- multimodal/long-horizon GUI：VideoWebArena、VideoGUI、OmniGUI 等。

定位重点不是“我们多了 accessibility tasks”，而是 **benchmark construct 不同**：

- user access need 显式进入 task specification；
- accessibility relevance 可以来自 information、delegation、output 或 persistent state；
- success 不仅是 underlying state change；
- analysis 关注 heterogeneous user needs 与 failure signatures。

## 2.2 Accessibility and assistive-interaction studies

### A11y-CUA

建议定位：

> A11y-CUA is an accessibility interaction dataset and empirical study that records rich human and agent trajectories on shared Windows tasks and evaluates CUAs under default and accessibility-related interaction conditions. It is highly complementary to our work, but targets a different research question and artifact type.

A11y-CUA 更关注：

> 当 interaction condition 变成 keyboard-only / screen-reader-related / magnified 等时，agent capability 和真实 BLV user interaction strategy 如何变化？

本文更关注：

> 给定具有 documented access need 的 everyday digital goal，agent 能否完成 underlying task，并满足由该 access need 带来的 information、delegation、output 或 continuation-state requirement？

建议对比：

| 维度 | A11y-CUA | 本文 |
| --- | --- | --- |
| 核心对象 | accessibility-conditioned interaction behavior / trajectories | accessibility-oriented end-to-end task completion |
| 人群范围 | 重点 BLV | visual / hearing / motor / cognitive functional slices |
| 是否要求 agent 模拟用户操作方式 | 实验中显式改变 interaction condition | 默认不要求；agent-side strategy 与 user-side requirement 分离 |
| 主要 artifact | multimodal human/agent trajectory dataset + empirical study | reusable executable task benchmark |
| Evaluation | task success + trajectory/behavior analysis | task-specific deterministic end-state + accessibility requirement |
| 研究价值 | 揭示 AT-constrained interaction gap | 衡量 diverse access needs 下的 user-oriented capability，并驱动方法开发 |

不要写“A11y-CUA 不是 benchmark”；更准确地说，它支持 benchmark-style evaluation，但 artifact 和 research question 与本文不同。

本文可以借鉴其：matched/controlled comparison、trajectory analysis、accessibility state 关注，但不复制“agent 必须用 AT”的设定。

## 2.3 User assistance / intent-aware systems

GUIDE 类工作更关注从 user demonstration/interaction 推断 intent、state、何时提供帮助；本文关注 autonomous agent 直接完成 accessibility-oriented workflows。两者 complementary。

## 2.4 GUI-agent evaluation methodology

这里放 task success、end-state evaluator、trajectory/process diagnostics、structured state evaluation 等相关工作。本文的 differentiator 是 **atomic fact-based deterministic evaluation + structured application/system state checking**，并单独做 evaluator validity study。

---

# 3 Benchmark

## 3.1 Design goals and task definition

### Design goals

建议正文列 5 点：

1. **Documented accessibility relevance**：每个 task 必须映射到至少一个 documented user need；
2. **Everyday-life realism**：底层目标来自正常数字生活，不制造 disability-exclusive goals；
3. **Broad functional and workflow coverage**：覆盖四个 functional groups、多类 modalities 和 ICF-informed life workflows；
4. **Executable and reproducible environments**：可 reset、可重复执行；
5. **Deterministic but semantically tolerant evaluation**：对结构化 state 严格，对合理 surface variants 容忍。

### Formal task construct

推荐正文直接给出：

> An accessibility-oriented task is an everyday computer-use task for which a documented access need materially changes at least one of: (i) information that must be acquired, (ii) interaction burden delegated to the agent, (iii) user-facing representation/output, or (iv) accessibility/continuation state that must be preserved.

这一定义比“task for disabled users”或“task requiring assistive technology”都更可辩护。

### Four accessibility-relevance mechanisms

| Mechanism | What changes relative to ordinary GUI completion? | Typical examples |
| --- | --- | --- |
| Information access | agent must obtain information unavailable/unreliable through the user's constrained modality | speech→text, visual-only content, key facts from dense content |
| Delegated burden | agent substitutes for a documented interaction/cognitive burden | fine pointer control, dragging, multi-stage sequencing, completion verification |
| Accessible output | final representation must reduce an access barrier | transcript, plain-language note, checklist, reminder, persistent transfer instructions |
| Accessibility / continuation state | final system state must preserve a requested access condition | captions, magnification, keyboard assistance, readable settings |

这些机制是 task-level construct；`user_group` 只是 aggregate slice。

### Agent-side interaction vs user-side state

必须明确：

> The benchmark does not evaluate whether agents themselves use assistive technologies. Accessibility settings are properties of the user-facing environment and may be success conditions even when the agent never consumes them during execution.

因此，“Sticky Keys 开启后 agent 没有用 Sticky Keys”不是 construct flaw。真正需要审查的是：Sticky Keys 是否与 task 声明的 documented keyboard-access need 有合理关系，以及最终保持该 state 是否支持用户的 continuation option。

### Accessible continuation state

完成任务可能要求：

- requested caption / magnification / keyboard-assistance setting 仍处于正确状态；
- user-facing information 已保存为可持续访问的 artifact；
- reminder、calendar、note、draft、document 可供用户之后检查或继续；
- agent 没有破坏用户依赖的 existing accessibility configuration。

不声称用户一定继续操作；只评估 **continuation readiness**。

## 3.2 User-need taxonomy: why visual / hearing / motor / cognitive

四个一级 `user_group` 应表述为**面向 GUI interaction 的 functional grouping**，不是穷尽式医学/诊断 taxonomy。

选择理由：它们覆盖 benchmark 中最主要且可直接 operationalize 的 GUI barriers：

- acquiring visual information；
- acquiring auditory information；
- executing physical input actions；
- processing, retaining, planning, or tracking task information。

这与 benchmark observation/action space 直接对应：visual/audio inputs + clicking/typing/configuration + multi-step workflows。

外部 framing 可以支持但不要声称“标准规定了这四组”：

- W3C accessibility framing 明确涉及 hearing, movement, sight, cognitive ability；
- Washington Group Short Set 以 functioning 而非 diagnosis 为核心，包含 seeing、hearing、walking/climbing、remembering/concentrating 等核心 domains。

建议正文英文：

> We organize accessibility scenarios into four top-level functional groups—visual, hearing, motor, and cognitive—not as an exhaustive diagnostic taxonomy, but as an operational abstraction of the dominant barriers exercised by GUI interaction. These groups correspond to limitations in acquiring visual information, acquiring auditory information, executing physical input actions, and processing or maintaining task information. Conditions involving speech, language, learning, neurological, or multiple disabilities may cut across these slices; we represent them only when their task-relevant barriers can be operationalized by the documented needs measured in our benchmark.

### Broad subgroups

| User group | ID | Broad subgroup | Mapped need IDs |
| --- | --- | --- | --- |
| visual | `V-S1` | Blindness | `V1`, `V5`, `V6` |
| visual | `V-S2` | Low vision / visual perception difficulty | `V2`, `V3`, `V4`, `V5`, `V6` |
| hearing | `H-S1` | Deaf or hard of hearing | `H1`, `H2`, `H3`, `H4`, `H5` |
| motor | `M-S1` | Keyboard input difficulty | `M1`, `M2` |
| motor | `M-S2` | Pointer / fine-motor control difficulty | `M4`, `M5`, `M6`, `M7` |
| motor | `M-S3` | Involuntary input / timing difficulty | `M3`, `M7` |
| cognitive | `C-S1` | Attention / information-processing difficulty | `C1`, `C6` |
| cognitive | `C-S2` | Memory / time-management difficulty | `C2`, `C3`, `C7` |
| cognitive | `C-S3` | Executive function / decision-making difficulty | `C4`, `C5`, `C8` |
| cognitive | `C-S4` | Numerical / reconciliation difficulty | `C7` |

`subgroup_ids` 允许 multi-label，因此 subgroup counts 不要求相加等于 benchmark 总数。

### Documented user needs

#### Visual

| ID | Documented user need | Operational definition | Primary evidence |
| --- | --- | --- | --- |
| `V1` | Non-visual access to digital text and interface content | 通过 screen reader 或等价非视觉表示读取、导航并操作文本/控件。 | WebAIM Screen Reader Survey #10; W3C Visual Disabilities |
| `V2` | Magnification and text enlargement | browser zoom、text sizing 或 screen magnification。 | WebAIM Low Vision Survey #2; WCAG 1.4.4 |
| `V3` | Contrast and display-palette customization | 高对比度、前景/背景、反色或显示配色。 | WebAIM Low Vision Survey #2; W3C; Microsoft |
| `V4` | Color-vision differentiation support | color filters 或 non-color cues。 | WCAG 1.4.1; Microsoft color-filter docs |
| `V5` | Access to non-text visual information | 图片、地图、图表、扫描件、visual-only content 的等价信息。 | WebAIM; WCAG 1.1.1 |
| `V6` | Accessible CAPTCHA and verification | 视觉 verification 的替代 modality 或 delegated assistance。 | WebAIM; WCAG 1.1.1 |

#### Hearing

| ID | Documented user need | Operational definition | Primary evidence |
| --- | --- | --- | --- |
| `H1` | Speech-to-text access through captions or transcripts | captions/live captions/transcript 获取 speech 和相关 audio 信息。 | W3C media accessibility; ACMA; AFB |
| `H2` | Caption readability and language customization | caption language/visual presentation 调整。 | Microsoft; ACMA |
| `H3` | Visual and persistent alternatives to auditory notifications | visual notification + 足够 persistence。 | Microsoft |
| `H4` | Single-channel access to stereo audio | stereo → mono，避免遗漏单侧声道。 | Microsoft |
| `H5` | Verification without relying on hearing | non-auditory verification 或 delegated assistance。 | WCAG 1.1.1 |

#### Motor

| ID | Documented user need | Operational definition | Primary evidence |
| --- | --- | --- | --- |
| `M1` | Alternative text entry without a physical keyboard | on-screen keyboard 或 alternative input。 | WebAIM Motor Survey; Microsoft |
| `M2` | Sequential modifier-key input | Sticky Keys 等将 simultaneous shortcut 改成 sequential input。 | Microsoft |
| `M3` | Keystroke filtering and sensitivity control | Filter Keys 等过滤重复/短促按键。 | Microsoft |
| `M4` | Alternative pointer control or delegated pointing | keyboard/speech/alternative input 或 agent 代理 pointer activation。 | Microsoft; WebAIM |
| `M5` | Reduced press-hold and dragging demand | 减少持续按住、拖动、精确释放。 | WCAG 2.5.7 |
| `M6` | Mouse-button and handedness customization | primary mouse button 等 pointer setting。 | Microsoft |
| `M7` | Reduced pointer precision, repetition, and timing demand | 减少反复精确 target acquisition、timing、fine-motor operation。 | WebAIM; WCAG 2.5.7 |

#### Cognitive

| ID | Documented user need | Operational definition | Primary evidence |
| --- | --- | --- | --- |
| `C1` | Focus, readability, and simplification | 降低 distraction、clutter、reading load。 | W3C Cognitive Accessibility; COGA |
| `C2` | Memory externalization and short-term retention support | notes/checklists/persistent cues/delegation。 | COGA |
| `C3` | Time and prospective-memory support | reminders/calendar/timer/persistent time cues。 | COGA |
| `C4` | Planning, sequencing, task-state tracking, and completion recognition | 降低 unfamiliar multi-step workflow、progress tracking、completion burden。 | COGA; Pew supplementary |
| `C5` | Decision and choice support | alternatives/constraints/consequences 的比较与选择。 | COGA |
| `C6` | Important-information extraction and prioritization | dense/mixed information 中提取少量关键事实/actions。 | COGA |
| `C7` | Calculation, counting, copying, and cross-source reconciliation support | 减少 arithmetic/counting/copying/短期保持/跨 source reconciliation。 | COGA |
| `C8` | Error prevention and safety-critical guidance | 高风险选择、scam、health/safety guidance 的正确理解与执行。 | COGA |

### Cognitive slice 的边界

不要把“任何多步骤任务”自动称为 cognitive-access task。本文允许两类：

1. **Support-output tasks**：通过 reminder/checklist/calendar/plain-language note 等降低 memory、attention、processing、planning burden；
2. **Delegated-burden tasks**：流程本身自然实例化 documented cognitive burden，如 sequencing、working-memory tracking、option/permission judgment、state interpretation、recovery、completion recognition。

Software installation 可以属于 `C4`，但理由必须是具体 cognitive demands，而不是“older adults”或“步骤多”。

## 3.3 Workflow taxonomy and ICF grounding

`category` 与 `user_group / subgroup_ids / need_ids` 正交：前者描述 **what life workflow is being performed**，后者描述 **what accessibility-related barrier/support need is exercised**。

当前 benchmark 使用以下 workflow categories；正文可以展示压缩后的类别与代表性 workflow，完整定义留 Appendix / README：

| Category | Benchmark meaning | Representative workflows |
| --- | --- | --- |
| `communication` | communication and social interaction | email, messaging, meetings, contacts |
| `information` | information acquisition and reading | browsing, documents, search, comparison |
| `management` | personal/time/resource management | calendars, reminders, to-do items, bills, deliveries, appointments |
| `mobility` | digital support for physical-world mobility | routes, transit schedules, ride-hailing, locations, accessible entrances |
| `consumption` | consumer workflows | product search/comparison, cart/order, coupons, after-sales service |
| `service` | administrative and public/private services | payments, statements, forms, government services, identity verification |
| `health` | health-related digital workflows | appointments, records, prescriptions, hospital information, emergency contacts |
| `access` | configuring accessibility support itself | captions, screen readers, magnification, reading mode, keyboard/pointer assistance |
| `setup` | ordinary software/system setup | installation or configuration where setup itself is the user goal |
| `captcha` | verification-barrier stress test | audio/text/image/pointer/puzzle CAPTCHA-like challenges |

其中 `captcha` 建议在结果中作为 **stress-test slice** 单独分析，而不是与 everyday-life categories 直接混合解释；`access` 和 `setup` 要区分“accessibility support 本身是目标”与“普通软件配置本身是目标”。

Task categories 可写成 **informed by WHO ICF Activities and Participation**，不要写“采用/复刻 ICF taxonomy”。ICF Activities and Participation 覆盖：

- learning and applying knowledge；
- general tasks and demands；
- communication；
- mobility；
- self-care；
- domestic life；
- interpersonal interactions and relationships；
- major life areas；
- community, social and civic life。

建议正文英文：

> Our workflow categories are informed by the ICF Activities and Participation component rather than reproducing the ICF hierarchy verbatim. We use ICF as a coverage guide for constructing realistic computer-use tasks across everyday life domains, while retaining benchmark-specific categories where needed (e.g., accessibility configuration and verification stress tests). Consequently, task category describes *what kind of life workflow is being performed*, whereas the user-need annotations describe *which accessibility-related functional barrier or support need the task exercises*.

WHODAS 2.0 可作为补充 framing，但不要让 taxonomy 显得依赖过多 standards。

## 3.4 Task collection, construction, and curation

正文描述流程，不展开工程细节：

1. 从 everyday digital workflows 和 documented accessibility needs 出发；
2. 将每个 task 映射到至少一个 `need_id`；
3. 配置 initial state、required outcome、必要的 continuation/accessibility state；
4. 编写 deterministic evaluator；
5. 执行 ground-truth / manual validation；
6. 做 task–need fit 和 naturalness review；
7. weak/unsupported tasks 重写、reassign 或移除。

### Task-level accessibility relevance checklist

构建阶段每个 task 至少回答：

- documented access need 是什么？
- 该 need 在任务中具体改变了 information / delegated burden / output / continuation state 中哪一项？
- 如果移除 accessibility-specific requirement，task construct 是否实质变化？
- 用户提出该要求是否自然，而不是 benchmark-engineered constraint？
- 如果有 AT setting，该 setting 是 user-facing requirement 还是仅为了增加 evaluator 条件？

正式发布 task 必须 `need_ids != []`。

### 当前 curation 原则

- `access-docker_install` / `access-spotify_install`：若保留 cognitive，依据 `C4` 的 unfamiliar setup / sequencing / completion-recognition burden，不把年龄本身当 disability evidence；
- cognitive CAPTCHA：只保留能自然实例化 retention、sequencing、focus/counting burden 的 challenge；
- consumption：generic exact lookup 改成 persistent reminder / natural preference constraints；
- information：长讨论→plain-language takeaway，Wikipedia→persistent reference artifact；
- cognitive × mobility：保留 workflow coverage，但 construct 是复杂 route/station info 的 simplification / step sequencing，而不是把 physical mobility access 当 cognitive need；
- visual/motor CAPTCHA：依据 verification delegation 或 pointer burden，而不是按 challenge 表面形式判断 group。

## 3.5 Execution environment and multimodal task realization

这一节应该进入 Benchmark 正文，而不是只放 README。它回答 reviewer 的两个问题：**任务如何做到可执行/可重复？多模态输入如何避免外部内容和识别结果漂移？** 正文讲设计原则和关键实现，端口、启动命令、镜像维护放 Appendix / released README。

### 3.5.1 Windows execution environment and applications

本文 benchmark **只评测 Windows computer-use agents**。执行环境基于 OSWorld / WindowsAgentArena 的 Windows stack，覆盖 desktop applications、browser、files、media、system settings 和 Windows accessibility tools。论文、released benchmark statistics 和实验结果均按单一 Windows platform 定义，不再设置 Android track，也不做跨平台能力比较。

Windows 侧优先使用稳定、可程序化检查结果的应用，例如 Edge / Chrome、Thunderbird Mail / Calendar、Sticky Notes、Notepad、LibreOffice Calc / Writer。应用的选择应服务于自然 user-facing outcome，而不是为了增加 app diversity：例如 appointment/reminder → calendar，communication → mail，短期 persistent memory support → notes/notepad，结构化 output → spreadsheet。

这一选择也使 benchmark 的研究问题更集中：本文关注不同 accessibility needs 如何改变 **同一 desktop GUI environment** 中的信息获取、任务代理、输出和 continuation requirements，而不是把 platform differences 与 accessibility effects 混在一起。Windows-only scope 应在 Introduction、Benchmark Scope 和 Limitations 中明确声明。

### 3.5.2 Self-hosted deterministic services

为减少 live websites 的 layout drift、content changes、ranking volatility、personalization 和 external-service failures，部分 web workflows 使用 self-hosted services。除本地 CAPTCHA service 外，这些服务继承自 WebArena self-hosted stack：

| Service | Internal port | Benchmark role |
| --- | ---: | --- |
| OneStopShop | 7770 | product search/comparison, cart/order and consumption workflows |
| E-commerce CMS/admin | 7780 | product/content/catalog/order-management workflows |
| Wikipedia via Kiwix | 8888 | pinned/offline encyclopedia lookup and information tasks |
| Reddit-style forum | 9999 | stable forum/post/comment information workflows |
| Local CAPTCHA service | 8765 | deterministic verification-barrier stress tests |

Windows agent environment 通过 `host.docker.internal:<port>` 访问这些本地服务。论文正文不需要给 SSH forwarding、Docker load/run 命令或账号密码；这些放 released README / Appendix implementation details。

这里需要明确论文动机：

> We use self-hosted or pinned services when uncontrolled web content would make task state or expected answers unstable. This preserves realistic browser interaction while allowing task setup, ground-truth state, and deterministic evaluation to remain reproducible across runs.

同时不要把所有 local tasks 描述成“synthetic”：OneStopShop/CMS/forum/Wikipedia 是真实 web interaction pattern 的固定化环境；CAPTCHA service 才更明显是 benchmark-controlled stress-test infrastructure。

### 3.5.3 Hearing-task audio generation and caption-based tasks

hearing slice 的实现需要在正文中特别说明，因为它直接关系到 benchmark 的 multimodal validity 和 reproducibility。

对于需要从 speech 中获取信息的 caption/live-caption tasks：

1. 使用 Chrome Live Caption 或 Windows Live Captions 等 task 指定的 caption support；
2. 期望答案原则上应能 **仅从 captions 获得**，除非任务明确同时测试 visual inference；
3. 选择短、稳定、无歧义的 spoken content；在线视频应尽量短（README 建议不超过约 3 分钟），避免播放前已有完整 transcript；
4. expected answers 优先使用 concrete nouns / noun phrases / short action phrases，或 caption 中最短的完整连续 phrase；
5. 对需要更强 determinism 的任务，可不用在线视频，而使用 **fixed AI text-to-speech audio**：由固定 script 生成 `.mp3`（当前实现可使用 ElevenLabs），script 随 task materials 保存并作为 source of truth；
6. TTS 的目的不是生成“更容易”的音频，而是固定 speech content，减少视频变化和 live-caption recognition variance，使不同 agent run 面对相同 auditory stimulus；
7. 即使 audio 是预生成的，任务仍应要求 intended caption feature（当 caption state 本身属于 graded requirement），expected facts 来自固定 script，而不是 evaluator 依赖一次具体 caption rendering 的全部字符串。

推荐正文英文：

> To make auditory tasks reproducible, we use either short pinned media or fixed text-to-speech audio generated from task-specific scripts. For the latter, the script is stored with the task and serves as the source of truth, while the generated audio is presented through the normal media pipeline and must be accessed through the task-specified captioning support when required. This design fixes the underlying spoken content across runs and reduces variance caused by changing online media, while preserving the speech-to-caption interaction that the task is intended to test.

需要避免一个潜在误解：**我们不是拿 ground-truth script 直接给 agent。** script 是 benchmark construction/evaluation source；agent 在执行时接收 audio/media 页面，并按任务要求通过 captioning workflow 获取信息。

### 3.5.4 Caption phrase evaluation

如果 caption-extraction task 将答案写入 spreadsheet 或其他 structured artifact，可以使用 deterministic phrase-containment coverage：

- 去除 blank / duplicate actual answers；
- lowercase + trim + collapse repeated spaces；
- 对每个 expected continuous phrase，检查是否被某个 actual answer 完整包含；
- `coverage = matched_expected_count / expected_count`。

这一 evaluator 适用于 source phrase 足够稳定的 hearing tasks。避免 single-word、overlapping expected phrases、synonym-heavy paraphrases，除非 task-specific evaluator 明确支持。正文可只用一句说明，完整规则放 Appendix。

### 3.5.5 Local CAPTCHA stress-test service

CAPTCHA slice 使用本地 deterministic service，以避免接触真实第三方 CAPTCHA provider 和不可复现的 challenge generation。当前 Windows service 包括：

- local mock：`audio`, `click_sequence`, `count_chars`, `distorted_text`, `math`, `robot_checkbox`；
- OpenCaptchaWorld-derived local assets：`geometry_click`, `slide_puzzle`, `image_recognition`, `patch_select`, `hold_button`。

OpenCaptchaWorld-derived tasks 使用复制到本地的 image assets 和 ground-truth metadata；benchmark execution 不应访问外部 CAPTCHA provider。

正文不要展开所有 challenge names，建议只写：**audio/text/counting/click/drag/image/hold verification barriers**，完整类型表放 Appendix。并明确 `captcha` 是 stress-test category，目标是测 verification barrier 是否阻断 end-to-end assistance，不代表 everyday workflow 的主体分布。

### 3.5.6 Local vs public Internet resources

任务的 provenance 与 runtime dependency 要区分：

- public URL 仅作为 `source`/provenance、但任务运行使用本地保存的 PDF/image → runtime 不依赖公网；
- `host.docker.internal` self-hosted services → local benchmark infrastructure；
- setup 或 execution 真正需要 public Internet resource → 标记 `proxy: true`。

这一规则建议不进正文细节，但放 Appendix / artifact documentation，以解释 benchmark 哪些任务可完全离线复现、哪些仍依赖 external resources。

### 3.5.7 What belongs in the paper vs released artifact

**正文应保留：** Windows execution environment、representative apps、self-hosted-service rationale、服务类型、fixed-TTS hearing pipeline、local CAPTCHA rationale、deterministic setup/evaluation connection。

**Appendix / README 保留：** exact ports、Docker commands、SSH forwarding、VM storage rebuild、Windows-side package installation、service credentials、具体 filesystem paths。

这样实现细节能够支撑 reproducibility claim，又不会让 ACL 正文变成部署手册。

## 3.6 Benchmark statistics

正文至少报告：

- total tasks；
- user group；
- broad subgroup（multi-label，分母可重叠）；
- documented need；
- workflow category；
- modality；
- application；
- accessibility/continuation-state required vs not required；
- single-app vs cross-app；
- output type；

避免把几十个 slice 都塞进正文；完整统计放 Appendix。

## 3.7 Deterministic end-state evaluation

### Main principle

1. structured state > serialized-text substring；
2. natural-language output 用 atomic facts，不用 whole-answer exact match；
3. semantic tolerance 与 fact completeness 同时保证。

紧凑 DSL 可以正文给一个例子：

```text
"text"              = required expression
["a", "b"]          = any_of
{"all_of": [A, B]}  = all children required
{"regex": "..."}    = constrained pattern
```

术语使用 **atomic fact-based deterministic evaluation**，不要叫 semantic evaluator。

### Outcome decomposition

建议将每个 task 的 evaluator 显式区分：

- `TaskOutcome`：underlying life/GUI goal 是否完成；
- `AccessRequirement`：task 明确要求的 access-need-specific information/output/state 是否满足；
- `FullSuccess = TaskOutcome ∧ AccessRequirement`。

并定义：

\[
\text{AccessibilityRequirementGap}=P(TaskOutcome)-P(FullSuccess)
\]

这个指标比单纯 `HandoffGap` 更一般，因为不是所有 task 的 additional requirement 都是 handoff state。

对具有 continuation-state requirement 的 subset，可额外报告 `ContinuationStateSuccess`。

## 3.8 Construct validity: human / expert review

正式进入论文，而不是仅内部 QA。

建议评价：

- realism；
- accessibility relevance；
- clarity / determinacy；
- support appropriateness；
- **accessibility-specificity**：documented need 是否真实改变 information/burden/output/state，而不是 arbitrarily attached label/toggle。

理想设计：每个 task 或 representative stratified sample 至少两位 reviewer；如果资源允许，部分 reviewer 具有 accessibility expertise 或 lived experience。报告评分、分布、agreement、adjudication、revise/reassign/remove 数量。

这里证明的是 **construct validity**，不是模型能力。

## 3.9 Evaluator validity study

构造 natural-language evaluator cases：

- canonical correct；
- semantically equivalent variant；
- missing-fact；
- wrong-value near miss；
- negated answer；
- formatting variant。

比较：

1. whole exact match；
2. naive substring/point matching；
3. atomic fact-based evaluator。

以人工 correctness label 为参考，报告 precision / recall / F1 或 agreement。

预期结论：exact match false negatives 高；loose matching false positives 高；本文在 deterministic/reproducible 前提下更接近 human correctness judgment。

---

# 4 Benchmarking Current Computer-Use Agents

## 4.1 Baselines and experimental setup

约 10 个代表性 agents，覆盖 design families：

- strong proprietary native computer-use agent；
- general multimodal model + agent scaffold；
- GUI-specialized open-source agent；
- screenshot-centric agent；
- structured observation / accessibility-tree-aware agent；
- planning-heavy agent；
- lightweight/reactive agent。

最终名单投稿前按代表性与可复现性更新。

## 4.2 Main metrics

主指标：`FullSuccess` / task success rate。

辅助诊断：

- `TaskOutcome`；
- `AccessRequirementSuccess`；
- `AccessibilityRequirementGap`；
- partial fact/state score；
- steps/actions；
- completion time；
- token/inference cost；
- recovery/backtracking；
- continuation-state success（相关 subset）。

## 4.3 Overall and group-wise results

主表：行 = agents；列至少 Overall + visual + hearing + motor + cognitive。

报告 bootstrap CI / uncertainty；group size 不均衡时避免过强 rank claim。

## 4.4 Performance across documented needs and task factors

重点选最解释 RQ 的 factors：

- documented need / broad subgroup；
- modality；
- four accessibility-relevance mechanisms；
- accessibility/continuation setting required vs not required；
- single-app vs cross-app；
- workflow category；
- difficulty / horizon；
- output type。

关键目的：说明 performance difference 不是“某组 tasks 恰好更难”的简单复述。

## 4.5 Matched ordinary vs accessibility-oriented subset（强烈建议）

构造小规模 paired subset：保持 underlying user goal、app、initial state 尽量一致，只改变 access-need-specific requirement。

例如：

- ordinary：find three spoken instructions from a video；access-oriented：obtain the spoken instructions and save a non-auditory persistent representation；
- ordinary：find route information；access-oriented：produce a concise persistent transfer note；
- ordinary：configure app X；access-oriented：configure X while preserving requested keyboard-assistance state。

报告：

\[
\Delta_{access}=SR_{ordinary}-SR_{access-oriented}
\]

如果无法严格匹配，不声称 causal effect；改写为 controlled/near-matched evidence。

---

# 5 Failure Analysis

这一节承担 benchmark → method 的桥梁，不能只放 case studies。

## 5.1 Failure taxonomy

先从 trajectories 归纳，再最终合并。候选 coding：

1. **Accessibility-state failure**：未配置、保持或验证 requested feature/state；
2. **Information acquisition failure**：没有正确获得 text/audio/video/visual information；
3. **Grounding / focus failure**：定位、焦点、control-state 判断错误；
4. **Task-state tracking failure**：忘记进度/下一步；
5. **Constraint failure**：underlying goal 成功但违反 user/access constraint；
6. **Artifact construction failure**：note/email/calendar/document 字段或 accessible representation 不完整；
7. **Cross-app transfer failure**：跨 app 信息传递错误；
8. **Completion verification failure**：遗漏 Save/Apply/Submit/final check；
9. **Recovery failure**：popup/page change/error 后无法恢复；
10. **Evaluator-near-miss but semantically wrong**：用于 benchmark QA。

## 5.2 Annotation protocol

对 stratified failed trajectories 至少两位 annotator 独立编码；报告 agreement 和 adjudication。同步记录 repeated retry、backtracking、focus recovery、遗漏 final action 等 process signals。

## 5.3 Analysis questions

重点不是“哪个 failure 最多”，而是：

- 哪些 failure 在 visual/hearing/motor/cognitive 中集中？
- 哪些 failure 与 information/delegation/output/continuation mechanism 相关？
- 哪些 agent family 更容易发生哪些 failure？
- accessibility requirement failure 是否常发生在 underlying `TaskOutcome` 已成功之后？
- structured observation / persistent planning / verification 是否与更低的特定 failure rate 相关？

目标形成可复用的 failure signature，而不是主观 anecdotes。

---

# 6 [Our Method]

方法不要提前写死。最终 architecture 必须由 §5 的 empirical mechanism 导出。

## 6.1 Motivation from failures

推荐逻辑模板：

> Our analysis shows that current agents often fail not because they cannot execute primitive GUI actions, but because they do not reliably maintain access-need-specific requirements, task state, multimodal evidence, and completion conditions across long-horizon workflows. We therefore introduce [METHOD], which explicitly models [observed mechanisms].

候选模块：

- accessibility-aware requirement representation；
- persistent task / constraint state；
- multimodal evidence aggregation；
- structured UI / accessibility-state observation；
- final-state verifier；
- adaptive action strategy；
- continuation-state verifier。

## 6.2 Method design requirement

每个模块必须回答：

1. 对应哪个 observed failure mechanism？
2. 预测在哪些 task slices 上带来最大 gain？
3. 是否可能损害普通 GUI ability？如何验证？

---

# 7 Method Evaluation

## 7.1 Main results

与 strongest baselines 比较 overall + four groups。

不要只写“本 benchmark SOTA”；强调 failure-driven design 和 targeted improvements。

## 7.2 Targeted slice analysis

验证方法收益是否集中在理论预测的 slices，例如：

- persistent state → cross-app / cognitive support；
- accessibility-state verifier → configuration/continuation tasks；
- multimodal evidence → audio/visual information tasks；
- final verifier → Save/Apply/Submit / completion-recognition tasks。

## 7.3 Ablations

每个 module 都绑定 failure hypothesis，而不是只报总分：

- remove persistent state → task-state / cross-app failure 回升；
- remove accessibility-state verification → continuation-setting tasks 下降；
- remove final verifier → completion verification failure 回升。

## 7.4 Cross-benchmark generalization

至少一个已有的 **Windows-compatible general CUA benchmark**（最终可选 OSWorld 或 WindowsAgentArena 中与本文任务集独立的标准 evaluation suite）。

目的：

- 排除 evaluator-specific hack；
- 检查方法没有严重损害 general CUA capability；
- 若有提升，可说明机制具有 broader robustness value。

不要把 external benchmark SOTA 设成 benchmark 合法性的必要条件。

---

# 8 Discussion

## 8.1 Accessibility relevance is not AT usage

正文 Discussion 可重申：

- agent 不需要体验/模拟 disability；
- agent-side strategy 与 user-side requirement 分离；
- accessibility setting 即使未被 agent 使用，也可能是 legitimate persistent user environment state；
- benchmark 评估的是满足 access need，而不是 AT adoption rate。

## 8.2 Ordinary goals, different usable completion conditions

强调很多 underlying goals 与 general users 相同是设计优点，不是缺陷：benchmark 要测的是 everyday assistance，而不是 disability-exclusive activities。

真正区别来自 information pathway、delegated burden、output representation、continuation state。

## 8.3 Accessible continuation without predicting future user behavior

不声称用户一定接管。`continuation readiness` 的价值在于避免 agent 完成任务后破坏用户依赖的环境，并保留 future option。

## 8.4 Functional groups are analytical slices, not user identities

visual/hearing/motor/cognitive 是 operational functional slices；真实用户需求可 overlap、变化、情境化。不要把 group-level performance 解读成某类真实人群的完整能力预测。

## 8.5 Broader implication

强 general CUA performance 不保证 strong accessibility-oriented assistance。更可靠的 agent 需要显式跟踪 user-specific constraints、persistent environment requirements 和 multimodal evidence，而不仅是完成 nominal GUI goal。

---

# 9 Limitations and Ethical Considerations

至少主动承认：

1. **Four-group simplification**：不是完整 disability taxonomy；speech/language/learning/neurological/multiple disabilities 覆盖有限。
2. **Task-level proxy**：documented needs + expert review 不能替代大规模 target-user study；不能声称 benchmark “代表所有 disabled users”。
3. **Functional need ≠ diagnosis**：同一 diagnosis 内 heterogeneity 大，group label 仅用于 benchmark slicing。
4. **Continuation state is potential, not observed future behavior**：benchmark 测 readiness，不测用户真实后续使用。
5. **AT feature purpose vs individual preference**：官方 feature documentation 说明 intended purpose，不代表每位用户都希望启用该 feature。
6. **Environment/platform coverage**：本文只覆盖 Windows desktop environment；结果不能直接外推到 Android、iOS、macOS 或其他 interaction paradigms，且具体 app selection 仍会限制 generalization。
7. **Synthetic/self-hosted tasks**：为确定性可能牺牲部分开放世界 realism。
8. **Evaluator coverage**：deterministic evaluation 仍可能遗漏未建模但合理的 success variants；用 validity study 降低风险。
9. **Cognitive construct sensitivity**：尤其避免将年龄、普通 long-horizon difficulty 或“步骤多”直接等同 cognitive disability。
10. **No claim of replacing user autonomy**：benchmark 测 delegated assistance capability，不意味着 agent 应默认替用户做决定；高风险任务需用户 control/confirmation。

---

# 10 Conclusion

结论控制在三层：

1. 提出 accessibility-oriented executable benchmark；
2. 发现 general GUI competence 与 access-need-specific reliable assistance 存在 gap，并具有不同 failure signatures；
3. failure-driven method 说明显式建模 access requirements / state / verification 有价值。

最后一句建议：

> Strong general computer-use performance does not by itself guarantee reliable assistance across heterogeneous accessibility needs; evaluating and preserving access-need-specific requirements is a necessary step toward agents that can more robustly support diverse users.

---

# Appendix / Supplement 规划

## A. Full documented-user-need taxonomy and source registry

论文核心 claim：**tasks are grounded in documented accessibility user needs**，而不是在没有 target-user study 时声称 “the benchmark satisfies users' real needs”。

证据分层：

1. **Empirical user evidence**：WebAIM、ACMA、AFB、Pew 等 survey/user research；
2. **Accessibility user requirements**：W3C WAI / COGA / WCAG；
3. **Platform documentation**：Microsoft 等，用于确认具体 accessibility feature 的 intended purpose。

这些来源分别支持 need existence、construct definition、feature purpose；不要把 survey 当 prevalence estimate，也不要把 platform docs 当 user study。

主要 sources：

- WebAIM, *Screen Reader User Survey #10 Results* (2024): https://webaim.org/projects/screenreadersurvey10/
- WebAIM, *Survey of Users with Low Vision #2 Results* (2018): https://webaim.org/projects/lowvisionsurvey2/
- WebAIM, *Survey of Users with Motor Disabilities* (2013): https://webaim.org/projects/motordisabilitysurvey/
- W3C WAI, *Introduction to Web Accessibility*: https://www.w3.org/WAI/fundamentals/accessibility-intro/
- W3C WAI, *Diverse Abilities and Barriers*: https://www.w3.org/WAI/people-use-web/abilities-barriers/
- Washington Group on Disability Statistics, *Short Set on Functioning / FAQ*: https://www.washingtongroup-disability.com/resources/frequently-asked-questions/short-set/
- WHO, *International Classification of Functioning, Disability and Health (ICF)*: https://www.who.int/classifications/international-classification-of-functioning-disability-and-health
- WHO, *ICF Browser — Activities and Participation*: https://apps.who.int/classifications/icfbrowser/Browse.aspx?code=d
- WHO, *WHODAS 2.0*: https://www.who.int/standards/classifications/international-classification-of-functioning-disability-and-health/who-disability-assessment-schedule
- W3C WAI, *Visual Disabilities — Abilities and Barriers*: https://www.w3.org/WAI/people-use-web/abilities-barriers/visual/
- W3C WAI, *Making Audio and Video Media Accessible*: https://www.w3.org/WAI/media/av/
- W3C WAI, *Cognitive Accessibility*: https://www.w3.org/WAI/cognitive/
- W3C COGA supplemental design patterns: https://www.w3.org/WAI/WCAG2/supplemental/patterns/
- W3C WCAG 2.2 Understanding: https://www.w3.org/WAI/WCAG22/Understanding/
- Microsoft, *Make Windows easier to hear*: https://support.microsoft.com/en-us/accessibility/windows/make-windows-easier-to-hear
- Microsoft, *Accessibility tools for mobility*: https://support.microsoft.com/en-US/accessibility/accessibility-tools-for-mobility
- ACMA, *Use and experience of captioning: consumer research* (2023)
- American Foundation for the Blind, *Innovation for Access* (2026; analysis of 2025 survey)
- Pew Research Center, *Navigating technological challenges* (2021)

`paper/documented_user_need_taxonomy.json` 应作为 machine-readable source of truth。

## B. Benchmark implementation and reproducibility details

这一 Appendix 对应正文 §3.5，建议与 released README 保持一致，但只保留论文复现所需的信息。

### B.1 Platform/runtime stack

- Windows-only runtime: OSWorld / WindowsAgentArena-based environment；
- 不设置 Android track；paper 与 released benchmark 的主结果均限定在 Windows desktop computer use；
- task `config` 负责准备 initial state，但不能提前完成 graded goal；
- `gt_steps` 用于 annotator reproduction，保持 one executable action per step；
- Windows accessibility/system settings 或 Windows-side dependencies 若依赖 persistent VM state，需要在 released artifact 中说明 image/storage preparation procedure。

### B.2 Self-hosted service registry

完整记录 service name、version/image、port、reset mechanism、task families 和 evaluator access method。当前主要 registry：OneStopShop `7770`、CMS `7780`、Kiwix Wikipedia `8888`、forum `9999`、CAPTCHA `8765`。

论文 supplement 中可以给表，但不要公开不必要的 credentials；正式 artifact README 负责启动/重置命令。

### B.3 Hearing media provenance

对每个 fixed-TTS task 保存：

- canonical script；
- generated audio asset；
- TTS provider/model/voice/version（最终 release 时固定）；
- expected continuous caption phrases / atomic facts；
- media duration；
- required caption feature；
- generation date/hash（建议加入，便于 artifact integrity）。

如果使用 ElevenLabs，论文可以写“fixed text-to-speech audio (e.g., ElevenLabs in our current implementation)”；若投稿前 provider/model 仍可能变化，主文只写 fixed TTS，Appendix 再给最终具体版本。

### B.4 CAPTCHA service provenance

说明 local mock challenges 与 OpenCaptchaWorld-derived local assets 的来源、ground-truth metadata、随机种子/固定 challenge URL（若适用）以及 external-network isolation。强调 benchmark execution 不联系真实 CAPTCHA providers。

### B.5 External-resource policy

报告 local-only 与 `proxy: true` task 数量。对于 source provenance 是公网、runtime 使用 pinned/local copy 的任务，明确其不属于 runtime Internet dependency。

### B.6 Environment maintenance

Docker image rebuild、Windows VM storage recreation、persistent VM changes、Windows-side Python package installation等操作属于 artifact maintenance instructions，不放正文。最终提交 artifact 时保证 README 与 benchmark release commit/tag 对齐。

---

## C. Claim → Evidence matrix

| Claim | Required evidence |
| --- | --- |
| Current CUAs struggle with accessibility-oriented goals | multiple strong baselines + CIs |
| Different needs expose different capability/failure patterns | group/need-wise results + failure analysis |
| Accessibility-oriented construct is not ordinary GUI difficulty relabeled | task mechanisms + matched/near-matched subset + task-factor analysis |
| Tasks have real accessibility relevance | documented need mapping + counterfactual relevance check + human/expert validation |
| AT usage is not the benchmark definition | task definition + agent-side/user-side separation + results by mechanism |
| Persistent accessibility state is a real additional success condition | TaskOutcome vs FullSuccess / continuation-state subset |
| Evaluator is valid | evaluator validity study |
| Proposed method addresses observed mechanisms | targeted gains + failure reduction + ablation |
| Method is not evaluator-specific overfit | cross-benchmark results |
| Contribution differs from A11y-CUA / GUIDE | artifact/research-question comparison |

如果 claim 没有 evidence，就删 claim 或补实验。

## D. Reviewer concerns and concise answers

### C1. “Why should the agent use assistive technology?”

它不需要。Benchmark 分离 agent-side interaction strategy 与 user-side accessibility requirement。AT/settings 可以是最终 user-facing environment state，而不是 agent observation/action method。

### C2. “The agent never used Sticky Keys after enabling it. Isn’t that artificial?”

“agent 是否使用”不是有效判据。问题应是：Sticky Keys 是否对应 documented keyboard-access need，以及 task 是否合理要求保持该 persistent user setting。Benchmark 不假设用户一定继续操作，只要求保留 accessible continuation option。若 setting 与 user need 无关，只是随意附加 evaluator condition，则应在 curation 中重写/删除。

### C3. “Aren’t these just normal tasks with disability labels?”

Underlying goals 故意是普通生活目标。Accessibility-oriented 的差异在于 documented need materially changes information、delegated burden、output 或 continuation state。用 task-level need mapping、counterfactual relevance check、human validation 和 matched subset 支撑。

### C4. “How is this different from A11y-CUA?”

A11y-CUA 主要研究 accessibility-conditioned interaction behavior/trajectory；本文研究 diverse access needs 下的 executable end-to-end user goals 和 deterministic end state，不要求 agent 模拟用户 AT trajectory。

### C5. “Are cognitive tasks just long-horizon tasks?”

不是。只有能映射到 C1–C8 documented needs 且具体 operationalize simplification、memory externalization、prospective memory、sequencing/state tracking、decision support、information extraction、reconciliation 或 error prevention 的任务保留。

### C6. “Are four disability groups reductive?”

四组是 non-diagnostic functional benchmark slices，不声称穷尽真实 disability categories；真实 needs 可重叠。

### C7. “Does continuation state assume the user actually takes over?”

不。它测的是 option/readiness，不是未来行为。

### C8. “Is the evaluator brittle?”

structured state + atomic fact-based deterministic scoring + evaluator validity study。

### C9. “Method overfits your benchmark?”

failure-specific ablation + external benchmark transfer；不只报 own-benchmark SOTA。

## E. Figure / table plan

### Figure 1 — Benchmark overview / teaser

推荐画成：

**Documented access needs (4 functional groups)** → **everyday workflows / modalities** → **four accessibility-relevance mechanisms** → **agent** → **TaskOutcome + AccessRequirement / continuation state** → **deterministic evaluator**。

这比旧版“four user groups → agent → handoff state”更能回答“和普通 task 有什么区别”。

### Table 1 — Prior benchmark comparison

列：executable environment、end-to-end tasks、deterministic evaluator、multimodal input、documented access-need grounding、multiple functional groups、accessible output/state evaluation、human trajectory dataset。

不要做成所有列本文都是 ✓ 的 marketing table。

### Table 2 — Benchmark statistics

user group / subgroup / need / category / modality / mechanism / apps / continuation-state requirement / single-cross app。

### Table 3 — Baseline main results

Overall + visual/hearing/motor/cognitive + TaskOutcome/FullSuccess。

### Figure 2 — Accessibility Requirement Gap

展示 `TaskOutcome` vs `FullSuccess`，最好按 group 或 mechanism 分解。

### Figure 3 — Mechanism/task-factor performance

information / delegation / output / continuation；modalities；cross-app 等。

### Figure 4 — Failure taxonomy

按 user group / agent family 展示 failure composition。

### Table 4 — Our method

Overall + hard slices + mechanism slices。

### Table 5 — Ablation

模块 × 对应 failure slice。

### Table 6 — Cross-benchmark

本文 benchmark + 1–2 个 general CUA benchmarks。

## F. Abstract template（实验后填数字）

> Computer-use agents are increasingly capable of completing everyday digital tasks, yet existing evaluations largely assume general user goals and standard completion conditions. We introduce [BENCHMARK], an executable benchmark for evaluating whether agents can complete everyday computer-use tasks on behalf of users with diverse accessibility needs. Rather than requiring agents to emulate assistive-technology interaction, our tasks are grounded in documented access needs that materially affect required information, delegated interaction burden, user-facing output, or persistent accessibility and continuation states. [BENCHMARK] contains [N] tasks spanning visual, hearing, motor, and cognitive functional scenarios, multiple life-workflow categories and modalities, and uses task-specific deterministic evaluators with structured state checking and atomic fact-based natural-language scoring. Evaluating [K] representative agents reveals [MAIN FINDING], including substantial variation across [GROUPS/MECHANISMS] and a gap between nominal task completion and full accessibility-oriented success. Based on these failures, we introduce [METHOD], which [MECHANISM] and improves [RESULT] while [preserving/improving] performance on [EXTERNAL BENCHMARK]. Our results show that strong general computer-use performance does not guarantee reliable assistance under heterogeneous accessibility requirements.

## G. Title candidates

1. **[Name]: Benchmarking Computer-Use Agents for Accessibility-Oriented User Tasks**
2. **[Name]: Evaluating Computer-Use Agents Across Diverse Accessibility Needs**
3. **Beyond the Standard GUI: Benchmarking Computer-Use Agents for Accessibility-Oriented Assistance**
4. **Accessible Continuation: Evaluating Computer-Use Agents Across Diverse Accessibility Needs**

如果方法贡献最终很强，再考虑 benchmark + method 双主线标题。

## H. 六句话 paper story

1. **现有 CUA benchmark 主要评测通用用户目标，而 documented accessibility needs 会改变任务的 usable completion requirements。**
2. **本文不要求 agent 模仿残障用户或依赖 AT；accessibility relevance 来自 information access、delegated burden、accessible output 或 persistent accessibility/continuation state。**
3. **我们构建一个覆盖 visual/hearing/motor/cognitive functional slices、ICF-informed everyday workflows 和 multimodal information 的 executable benchmark，并用 deterministic end-state evaluator 评分。**
4. **代表性 CUAs 的评测显示：nominal GUI task completion 不等价于 full accessibility-oriented success，而且不同 needs 暴露不同 failure signatures。**
5. **这些 failure 直接指导新的 agent method，而不是只产生一个排行榜。**
6. **方法在预测 slices 上显著改善，并通过 existing general CUA benchmark 检查非 benchmark-specific overfitting。**

整篇论文每个 section 都应服务于这六句话中的至少一句。
