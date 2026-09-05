# WindowsAgentArena 下一轮任务修改 Checklist

用途：下一次对话处理 `examples/` 下除 `cognitive/` 之外的任务时，按同一套规范检查和修改，避免重复讨论口径。

## 处理范围

下一轮优先检查：

- `src/win-arena-container/client/evaluation_examples_windows/examples/hearing/`
- `src/win-arena-container/client/evaluation_examples_windows/examples/motor/`
- `src/win-arena-container/client/evaluation_examples_windows/examples/visual/`

`cognitive/` 已完成本轮 category / `related_apps` 核对；除明确列出的待重构项外，不重复批量修改。

## 本轮已经确定的统一规则

### 1. Category

- category label 一律使用 README 中规定的**小写**值：
  - `communication`
  - `information`
  - `management`
  - `mobility`
  - `consumption`
  - `service`
  - `health`
  - `access`
  - `setup`
  - `captcha`
- 根据任务的**主要用户目标或工作流**确定 category，不要只根据来源网站、输出应用或 disability group 分类。
- `access` 用于安装、启用或配置 accessibility / access-support 功能本身作为主要目标的任务。
- `setup` 用于安装或设置普通软件/系统组件；普通软件安装不要为了 disability group 而归到 `access`。
- `captcha` 作为独立 stress-test slice。
- category 改动时必须同步：
  1. 修改 JSON `category`；
  2. 修改 filename prefix；
  3. 修改 `id`；
  4. 确认 `id == filename 去掉 .json`；
  5. 搜索项目内是否存在旧 id / filename 引用。

### 2. `id` 与 filename

对每个任务检查：

- [ ] `id` 与 JSON filename 去掉 `.json` 后完全一致。
- [ ] filename prefix 与 `category` 完全一致。
- [ ] 没有重复 `id`。
- [ ] 没有仅大小写不同的重复文件。
- [ ] 改名后旧文件加入 `DELETED_FILES.txt`，不能只新增新文件而保留旧文件。

### 3. `related_apps`

- 只列 Agent 在完成任务过程中**实际需要交互**的应用。
- 使用仓库现有 canonical app identifier，例如 `chrome`, `msedge`, `settings`, `thunderbird`, `notepad`, `sticky_notes`, `libreoffice_writer`, `libreoffice_calc` 等。
- 不写 setup-only 组件、后台服务或与实际执行路径无关的 app。
- 如果多个 app 只是互斥的可选路径，不要因为“可能用到”就全部列入；优先和预期成功轨迹对齐。
- 如果任务尚待重构，先记录 `related_apps` 风险，等任务目标稳定后与 instruction / gt_steps 一起调整。

检查项：

- [ ] instruction 中明确要求的 app 都在 `related_apps` 中。
- [ ] `gt_steps` 中实际操作的 app 都在 `related_apps` 中。
- [ ] config 中仅用于环境准备、但 Agent 不操作的组件没有误列。
- [ ] evaluator 依赖的目标 app 与 `related_apps` 不冲突。
- [ ] 没有重复 app label 或同一 app 的不同别名。

### 4. Instruction

统一为**简洁、直接的命令式表达**。

- 用 `Install`, `Set`, `Create`, `Find`, `Add`, `Write`, `Update`, `Copy`, `Complete` 等直接动词开头。
- 不使用 `Could you...`, `Can you...`, `Please...`, `I need you to...`, `I'd like you to...` 等客套铺垫。
- 不写成操作手册；菜单路径、按钮顺序、窗口切换等常规步骤让 Agent 自己推理。
- 保留无法安全推断的约束，例如精确文件名、标题、日期、收件人、目标值、不得发送/重启等。
- 某个 accessibility feature 只有在它本身属于任务要求或 evaluator 会检查时才明确要求。

### 5. `gt_steps`

- 面向标注人员，原则是按步骤能够复现成功轨迹。
- 对需要复现指导的任务，一步只完成一个主要动作。
- 有唯一标准答案时直接给出标准答案、日期、标题、文本、商品或设置值。
- 不把 `config` 的环境准备重复写入 `gt_steps`。
- CAPTCHA 任务不需要展开详细步骤或固定 seed 答案，保持简短即可。
- 对“任务本身需要重构”的任务，先不要规范旧 `gt_steps`；等新任务定义确定后一起重写。

### 6. Evaluator

- evaluator 必须覆盖 instruction 中明确要求且可验证的最终成功条件。
- instruction 明确要求某个 accessibility tool state 时，如果已有 evaluator 能检查，应加入检查。
- 固定绝对日期不要用依赖 VM today 的相对日期 evaluator。
- instruction 要求 exact wording 时，不要用过短的关键词替代完整原文要求。
- 多个独立成功条件需要全部满足时使用合适的 conjunction。
- evaluator 不应只检查任务要求字段的一小部分而允许明显不完整结果通过。

### 7. Difficulty

**暂不处理。**

下一轮 category / related_apps / instruction / gt_steps / evaluator 审核时，不顺手修改 `difficulty`。难度需要等全部任务统一后，再基于整个任务集用 `easy / medium / hard` 三档重新评定。

## Cognitive 已处理状态，下一轮不要重复

- cognitive JSON 已完成 category 与 `related_apps` 复核；普通软件安装现使用 `setup` category。
- `mobility-outdoor_running_supplies_note.json` 已改为 `information-outdoor_running_supplies_note.json`：
  - category `mobility` → `information`
  - id / filename 同步更新
  - `related_apps` 保持 `msedge`, `sticky_notes`
- 其余 cognitive task 的 category / `related_apps` 当前保持不变。
- Docker / Spotify 已确认可作为 cognitive 的多步骤软件安装任务保留，并分别改为 `setup-docker_install` / `setup-spotify_install`。
- 6 个 `consumption-*` task 已按本 checklist 全量复核：category / id / filename / related_apps / instruction / gt_steps / evaluator 均已闭环。多条件购物、review 比较、价格比较、约束记忆和食材规划本身可构成 cognitive load，不要求额外加入 reminder 或 accessibility feature。
- `consumption-shopping_title_elsa_bottle.json` 已改为同时匹配 Elsa、24 oz、Tritan 的多条件商品识别任务。
- `information-wikipedia_accessibility_definition.json` 已改为从文章中识别设计概念定义句并定点替换 Writer 占位符的任务。
- 当前 cognitive 没有仍标记为“必须先改任务本身”的条目；仅 `service-cms_product_record.json` 还有可选的 live-state evaluator 工程增强。

## 下一轮建议执行顺序

1. 先严格解析目标目录全部 JSON。
2. 生成每个任务的 `filename / id / category / related_apps / instruction / evaluator` 汇总表。
3. 先检查 category、filename、id 三者一致性。
4. 再检查 `related_apps` 是否和 instruction / gt_steps / evaluator 的实际应用一致。
5. 再检查 instruction 风格。
6. 对非 CAPTCHA、非待重构任务检查 `gt_steps` 原子性和标准答案。
7. 检查 evaluator 与 instruction 一致性。
8. 全量 JSON 重新解析，并检查重复 id / 大小写重复文件。
9. 不修改 difficulty。
10. 最终 ZIP **只包含当前这一轮实际修改的文件**；不要累计打包以前已经交付过的改动。只有当前这一轮发生删除或改名时才附 `DELETED_FILES.txt`。

## 输出要求

下一轮完成后应提供：

- 一个修改后的 checklist，列出每个 task 的结论和实际修改；
- 一个仅包含**当前这一轮实际修改文件**的 ZIP；
- `DELETED_FILES.txt`，记录需要从原项目删除的旧文件；
- 简短校验汇总：JSON parse errors、id/filename mismatch、duplicate id、category mismatch、related_apps 明显问题数量。
