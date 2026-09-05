# Accessibility-Oriented GUI Agent Benchmark Guidelines

This benchmark evaluates GUI agents on accessibility-related digital tasks. Tasks should represent realistic workflows in which accessibility needs, assistive tools, accessibility settings, or cognitive-support strategies materially affect how a user completes the goal.

The benchmark supports platform-specific implementations while following shared principles for task design, annotation, and deterministic evaluation.

## 1. Benchmark Scope

### Tracks

| Track | Base Environment | Scope |
| --- | --- | --- |
| Windows | OSWorld / WindowsAgentArena | Desktop apps, browsers, files, media, system settings, and Windows accessibility tools |
| Android | AndroidWorld | Mobile apps, Android system features, and Android accessibility tools |

### Disability Groups and Assistive Tools

Each task should be grounded in the access needs of one primary disability group.

| Disability Group | Windows Tools / Supports | Android Tools / Supports |
| --- | --- | --- |
| Visual impairment | NVDA | TalkBack, Reading Mode, Seeing AI, Be My Eyes |
| Hearing impairment | Windows Live Captions, Chrome Live Caption | Android Live Caption |
| Motor impairment | On-Screen Keyboard, Sticky Keys, Filter Keys, Mouse Keys | Accessibility Menu |
| Cognitive impairment | Immersive Reader, notes/checklists, reminders, calendars/timers, notification timing, text sizing | Reading Mode and other cognitive-support features |

Task scenarios may involve visual, auditory, physical, speech, cognitive, language, learning, or neurological access needs, but the relevant access need should be clear from the scenario.

### Task Categories

Use one of the following exact lowercase category labels:

| Category | Description |
| --- | --- |
| `communication` | Messaging, email, meetings, contacts, and social interaction |
| `information` | Browsing, reading documents, searching, and comparing content |
| `management` | Calendars, reminders, to-do items, bills, deliveries, and appointments |
| `mobility` | Route planning, ride-hailing, transit schedules, location search, and accessible entrance lookup |
| `consumption` | Product search, price comparison, add-to-cart, orders, after-sales service, and coupon use |
| `service` | Bill payment, statement inquiry, form submission, government services, and identity verification |
| `health` | Medical appointments, health records, prescriptions, hospital information, and emergency contacts |
| `access` | Installing, enabling, or configuring accessibility tools such as screen readers, captions, magnification, reading mode, keyboard assistance, or mouse assistance |
| `setup` | Installing or setting up ordinary software or system components when setup itself is the primary user goal |
| `captcha` | Focused stress-test tasks for CAPTCHA-style verification barriers |

#### CAPTCHA Stress-Test Slice

The `captcha` category is analyzed separately from standard daily-life workflow categories. It measures whether GUI agents can handle verification barriers that may otherwise block end-to-end assistance.

Choose the category from the task's **primary user goal or workflow**, not merely from the source website, the output application, or the disability group. Use `access` when the installed or configured target is itself an accessibility tool; use `setup` for ordinary software installation or setup workflows. If changing a task's category, rename the JSON file so the lowercase category prefix changes with it, and update `id` to exactly match the new filename without `.json`.

The local Windows CAPTCHA service currently supports:

| CAPTCHA Type | Source | Interaction Required |
| --- | --- | --- |
| `audio` | Local mock service | Listen to an audio code and enter the digits |
| `click_sequence` | Local mock service | Click scattered characters in the requested order |
| `count_chars` | Local mock service | Count occurrences of a target character |
| `distorted_text` | Local mock service | Read and enter a distorted text code |
| `math` | Local mock service | Solve an arithmetic expression |
| `robot_checkbox` | Local mock service | Click an "I'm not a robot" checkbox after a short delay |
| `geometry_click` | OpenCaptchaWorld | Click the requested geometric shape or object |
| `slide_puzzle` | OpenCaptchaWorld | Drag the puzzle component to the target position |
| `image_recognition` | OpenCaptchaWorld | Select all images matching the prompt |
| `patch_select` | OpenCaptchaWorld | Select all grid patches containing the requested object |
| `hold_button` | OpenCaptchaWorld | Press and hold a button until progress completes |

OpenCaptchaWorld-derived types use copied local image assets and ground-truth metadata from `/home/weimingli/projects/OpenCaptchaWorld/captcha_data`. They are served locally by `src/win-arena-container/client/captcha_service.py` and must not contact external CAPTCHA providers during benchmark execution.

## 2. Task Design Guidelines

### Core Requirements

Each task should include:

1. A realistic app, browser, media, document, or system-settings scenario.
2. A clearly grounded accessibility need, support strategy, or disability-relevant interaction challenge.
3. A concrete user goal whose completion depends on accessible information, controls, feedback, or meaningful cognitive demands such as planning, sequencing, working memory, attention, decision-making, or maintaining task context.
4. An initial state that prepares the relevant app, page, file, media, message, or setting without completing the task.
5. A measurable final output or system state.
6. A deterministic evaluator that checks the result and, when applicable, the required accessibility tool or support state.

When a specific assistive tool or accessibility feature is part of the task, make that requirement explicit. If the task requires text output, place it in a deterministic destination such as a file, Sticky Note, email draft, calendar event, spreadsheet, or other evaluable state.

### Source Grounding

Tasks should be based on realistic accessibility use cases from credible public resources such as product documentation, accessibility support pages, tutorials, or user-oriented guidance.

Useful sources include:

| Resource | Typical Use |
| --- | --- |
| Hadley Learn / Hadley Presents | Visual-access scenarios involving information access, travel, shopping, health management, organization, and independent living |
| APH ConnectCenter / VisionAware / CareerConnect | Visual-access scenarios involving learning, employment, information management, navigation, and assistive technology |
| RNIB Technology for Life | Screen reading, magnification, device setup, and mobile accessibility |
| It’s Done! / My PATI | Cognitive-access scenarios involving memory support, daily routines, preferences, and simplified interaction |
| WorkingHandsFree | Motor-access scenarios involving hands-free workflows and alternative input |
| AbilityNet / My Computer My Way | General accessibility setup across visual, hearing, motor, and cognitive needs |
| Apple / Google / Microsoft accessibility documentation | Official guidance for accessibility features, captions, screen readers, magnification, shortcuts, and input support |
| Chrome reading and caption documentation | Reading mode, captions, translation, and web content consumption |

The task `source` should point to the concrete webpage, document, support article, app documentation, file, or media page used by the task whenever possible.

### Instruction Writing Style

Write `instruction` as a concise, direct command to the agent. Use imperative wording that states what should be accomplished. Do not frame the task as a question or polite request, and do not write it as a step-by-step UI procedure.

Prefer direct openings such as `Install`, `Set`, `Create`, `Find`, `Add`, `Write`, `Update`, `Copy`, or `Complete`. Avoid conversational lead-ins such as `Could you...`, `Can you...`, `Please...`, `I need you to...`, or `I'd like you to...`.

A good instruction should normally include only:

1. The task goal and any context needed to interpret it correctly.
2. The final result or artifact the agent must produce.
3. Constraints the agent cannot safely infer, such as an exact filename, recipient, title, date, value, preference, or `do not send/restart` requirement.
4. A specific app or accessibility feature only when using it is part of the task requirement or evaluator.

Keep the instruction goal-oriented and leave routine navigation and intermediate actions for the agent to infer. Do not spell out menu paths, button clicks, window switching, or page-by-page navigation when those actions are not themselves being evaluated. Reproducibility steps belong in `gt_steps`; environment preparation belongs in `config`.

Prefer:

```text
Install the Immersive Reader extension in Chrome.
```

```text
Set Windows notifications to stay on screen for 5 minutes.
```

```text
Create an all-day Thunderbird Calendar reminder titled `Refill medication` for the refill deadline in the pharmacy message on the Desktop.
```

Avoid polite-request framing:

```text
Could you install the Immersive Reader extension in Chrome for me?
```

```text
Please make Windows notifications stay on screen for 5 minutes.
```

Avoid procedural instructions:

```text
Open Settings, click Accessibility, select Visual effects, open the notification duration dropdown, and choose 5 minutes.
```

If a task has decision criteria or user preferences, state them directly as constraints rather than wrapping them in conversational background. Any requirement that is explicitly graded must still appear in the instruction. For example, if the evaluator checks that Immersive Reader is active, require Immersive Reader without explaining how to activate it.

### Ground-Truth Step Writing Style

Write `gt_steps` for annotators and task maintainers who need to reproduce a successful trajectory. Unlike `instruction`, `gt_steps` may include concrete UI navigation, intermediate actions, and expected answers.

For tasks that benefit from reproducibility guidance, each `gt_steps` item should describe **one atomic action**. A step may name the target object and exact value used by that action, but it should have one primary action. Split independent actions into separate steps instead of writing a mini procedure inside one item.

Use the following rules:

1. Write steps in the order needed to reproduce a successful trajectory.
2. Keep one primary action per step, such as opening a page, selecting an option, entering a value, saving a file, or submitting a form.
3. Name the application, page, control, file, item, or field precisely enough for another annotator to follow the same path.
4. When a deterministic standard answer is known, include the exact answer in backticks. Examples include source phrases, dates, filenames, titles, calculated values, product names, and required settings.
5. When multiple outputs are genuinely valid and the evaluator accepts alternatives, describe the acceptance criterion instead of inventing a single canonical answer.
6. Keep submission, confirmation, save, or send actions separate when they are required to complete the task.
7. Do not copy environment preparation into `gt_steps`; setup actions that occur before the agent starts belong in `config`.
8. Do not hide a known deterministic answer behind vague wording such as `find the answer` or `enter the result`. `gt_steps` should let an annotator reproduce the expected outcome without rediscovering known ground truth.

CAPTCHA tasks do not need detailed step-by-step ground truth. Their interaction is self-explanatory from the challenge UI, so keep `gt_steps` minimal rather than expanding them into answer keys or click-by-click procedures.

If a task is still pending redesign because its goal or scenario needs to change, revise the task and its `gt_steps` together after the new task definition is settled instead of normalizing the old steps first.

Prefer:

```json
"gt_steps": [
  "Open Windows Settings.",
  "Open `Accessibility`.",
  "Open `Visual effects`.",
  "Set `Dismiss notifications after this amount of time` to `5 minutes`."
]
```

For a task with a fixed answer, include it explicitly:

```json
"gt_steps": [
  "Open `pharmacy_message.txt` on the Desktop.",
  "Read the refill deadline `July 20, 2026`.",
  "Open Thunderbird Calendar.",
  "Create a new all-day event on `July 20, 2026`.",
  "Set the event title to `Refill medication`.",
  "Save the calendar event."
]
```

Avoid multi-action steps:

```text
Open Settings, go to Accessibility, and set the notification duration to 5 minutes.
```

Avoid omitting a known deterministic answer:

```text
Find the correct value and enter it.
```

### Cognitive-Access Tasks

Cognitive-access tasks on Windows are not limited to Microsoft Edge Immersive Reader. Immersive Reader is one useful support for reducing page clutter and strengthening focus, but tasks may instead involve reminders, notes, checklists, calendars, timers, reduced time pressure, text sizing, or structured multi-step workflows.

Appropriate scenarios include older adults with memory, attention, processing-speed, or planning difficulties; users with dyslexia or reading difficulties; users with ADHD or distractibility; and users who need help turning dense information into short actionable output.

Age alone is not sufficient to classify a task as cognitive. However, ordinary multi-step digital workflows can qualify when they place meaningful demands on planning, sequencing, working memory, attention, information processing, decision-making, maintaining task context, or recognizing successful completion. Software installation and setup tasks are valid examples when the user must independently manage those demands; they do not need to use a dedicated accessibility feature.

A cognitive task should make at least one of the following central to the scenario:

- memory or maintaining task context;
- attention or distraction management;
- information processing or comprehension;
- planning, sequencing, or decision-making;
- step tracking or prospective memory;
- recognizing successful completion;
- simplified interaction or reduced time pressure.

For cognitive reading and information-extraction tasks:

1. Use realistic everyday content such as scam guidance, health instructions, travel assistance, government services, shopping policies, or payment instructions.
2. Use Immersive Reader when it meaningfully supports the scenario or when Reader configuration itself is the task; do not require it merely to label a task as cognitive.
3. Do not place the answer directly in the instruction. The requested information should come from the source page or task context.
4. Prefer stable, unique source-grounded outputs such as exact short phrases, dates, phone numbers, form names, or URLs when deterministic evaluation requires them.
5. Save extracted information to a natural target such as Thunderbird, Sticky Notes, Notepad, a calendar event, or LibreOffice.
6. Evaluate the final content/state and any explicitly required support state. For `access` tasks, evaluating only the configured accessibility state can be sufficient.

Avoid broad prompts such as "summarize what to do" unless the evaluator defines specific required content. If paraphrases would create many valid answers, request or evaluate stable source phrases instead.

### Hearing-Access Tasks

For tasks that use captions or live captions to extract spoken content:

1. Prefer ordinary online video pages rather than short-form pages such as YouTube Shorts.
2. Keep videos short enough for practical evaluation, preferably no longer than 3 minutes.
3. Use media that has captions or produces reliable live captions.
4. Avoid pages where the full transcript is already visible before playback.
5. Require the relevant caption tool when using that tool is part of the task, such as Chrome Live Caption, Windows Live Captions, or Android Live Caption.
6. Make expected answers extractable from captions alone unless visual inference is explicitly part of the task.
7. Prefer concrete nouns, noun phrases, short action phrases, or the shortest complete continuous phrase that appears in the captions.
8. Keep expected answers stable and unambiguous.

Fixed AI text-to-speech audio may be used instead of online video when it improves determinism. For example, an `.mp3` generated from a fixed ElevenLabs script can reduce live-caption recognition variance. Save the script with the task materials and treat it as the source of truth. The task should still require the intended caption feature, and expected answers should be exact continuous phrases from the fixed script.

#### Caption Phrase Evaluation

For caption-extraction tasks whose answers are stored in a spreadsheet, use phrase-containment coverage unless a stronger task-specific evaluator is available:

1. Read the target answer column.
2. Remove blank rows and duplicate actual answers.
3. Normalize by lowercasing, trimming whitespace, and collapsing repeated spaces.
4. For each expected answer, check whether any actual answer contains the complete normalized expected phrase.
5. Compute coverage as `matched_expected_count / expected_count`.

Expected answers should be complete continuous caption phrases. Avoid broad single-word answers, overlapping expected answers, paraphrases, synonyms, or visually inferred answers unless the task explicitly requires them.

### Construction Workflow

Use the following workflow:

1. Collect a realistic accessibility scenario from credible sources.
2. Derive an executable task from the scenario and source material.
3. Adapt it to the target platform and available applications.
4. Define the user-facing goal and measurable final state.
5. Write a concise, direct, goal-oriented instruction.
6. Write reproducible `gt_steps` where they add value, using one primary action per step and including known deterministic answers.
7. Build a deterministic evaluator covering all graded requirements.
8. Manually verify that setup does not solve the task and that the task is realistic, executable, and repeatable.

## 3. Task JSON Specification

### Required / Supported Fields

Each task JSON may use the following fields:

| Field | Purpose |
| --- | --- |
| `id` | Unique task identifier. Must match the JSON filename without `.json`. |
| `category` | One approved lowercase category label. |
| `difficulty` | Estimated task complexity. |
| `instruction` | Direct user-facing task command. Follow the instruction style above. |
| `source` | Concrete source used to ground the task. |
| `gt_steps` | Ground-truth actions for annotator reproduction and verification. Keep each useful step atomic and include known deterministic answers; CAPTCHA tasks may remain minimal. |
| `config` | Environment setup actions. Setup must prepare but not complete the task. |
| `related_apps` | Applications the agent actually interacts with while completing the task. Use the benchmark's existing canonical app identifiers; omit setup-only components and unrelated alternatives. |
| `evaluator` | Deterministic completion logic. |
| `snapshot` | Legacy field for the base environment/application context; no longer used for new tasks. |
| `trajectory` | Legacy field for trace/log storage; no longer used for new tasks. |

### Naming Rules

Task filenames must follow:

```text
<category>-<short_task_name>.json
```

Rules:

1. Use the exact lowercase category label as the filename prefix.
2. Make the JSON `category` value match the filename prefix.
3. Write the short task name in lowercase snake case.
4. Make `id` match the filename without `.json`.
5. Add a short suffix only when needed to avoid a duplicate name.

Examples:

```text
access-live_caption.json
service-ftc_complaint.json
information-read_video_caption.json
management-onscreen_keyboard_reminder.json
```

### Evaluator Rules

Prefer deterministic state checks over subjective grading.

Inside `evaluator`:

- `func` specifies the evaluation function or functions;
- `conj` defines how multiple conditions are combined;
- `result` describes the actual state or output to inspect;
- `expected` defines the target condition.

When a task has multiple required success conditions, use an `and` conjunction so that all required conditions must pass.

Evaluators may check:

1. A saved file, note, draft, event, spreadsheet cell, or other final artifact.
2. A system setting, browser state, form state, media state, or application state.
3. Required content and prohibited content.
4. A required accessibility/support feature state when that feature is explicitly part of the task.

The evaluator should cover every requirement that is necessary for task success. Do not ask for a field, accessibility feature, or output in the instruction and then omit it from evaluation when it can be checked deterministically.

Expected outputs should be short, stable, and unambiguous. Avoid tasks that depend on current news, changing rankings, personalized recommendations, or volatile page layouts unless the source is pinned, cached, or self-hosted.

## 4. Windows Apps and Deterministic Services

### Supported Windows Apps and Tools

Use stable, commonly available applications when possible.

| App / Tool | Typical Use |
| --- | --- |
| Microsoft Edge | Web reading, Immersive Reader, browser-based information lookup |
| Google Chrome | Web browsing, Chrome Live Caption, online video/audio, and web tasks |
| Thunderbird Mail | Communication tasks such as composing, replying to, or saving email drafts |
| Thunderbird Calendar | Calendar tasks such as creating events, appointments, and reminders |
| `https://vclock.com` | Browser-based timer and timing-related management tasks |
| Sticky Notes | Short reminders, quick notes, and lightweight memory-support outputs |
| Notepad | Plain-text notes, short checklists, copied phrases, and deterministic files |
| LibreOffice Calc | Spreadsheets, small tables, lists, comparisons, and structured outputs |
| LibreOffice Writer | Documents, formatted notes, letters, forms, and longer text outputs |

Choose the target application based on the natural user outcome. For example, use Thunderbird Calendar for appointments/reminders, Thunderbird Mail for communication, Sticky Notes or Notepad for short memory-support artifacts, and LibreOffice for structured or longer outputs.

### Self-Hosted Services

Use self-hosted services when external websites would make a task unstable or difficult to evaluate deterministically. Except for the local CAPTCHA service, these services are inherited from the WebArena self-hosted stack.

| Service | Port | Typical Task Use |
| --- | ---: | --- |
| OneStopShop shopping website | 7770 | Product search, add-to-cart, comparison, shopping reminders, and checkout/cart checks |
| E-commerce CMS / admin website | 7780 | Product, content, catalog, and order-management workflows |
| Wikipedia via Kiwix | 8888 | Stable offline encyclopedia lookup and source-grounded information tasks |
| Reddit-style forum | 9999 | Forum browsing, post/comment lookup, and social-content workflows |
| Local CAPTCHA service | 8765 | Deterministic audio, text, image, click, puzzle, and hold-button verification tasks |

From inside the Windows environment, address services with `http://host.docker.internal:<port>/`. For local browser access through SSH forwarding, use the corresponding `http://localhost:<port>/` URL.

Prefer opening the stable service URL directly in `config`. Evaluators should check stable local URLs/page content rather than volatile search-result pages or third-party layouts.

The OneStopShop and CMS services are Magento-based. OneStopShop is intended for user-facing `consumption` tasks, while the CMS is intended for administrative workflows.

#### Local Access Through SSH

Add the required forwarding rule to the `CSE_T2` SSH configuration:

```text
LocalForward <port> 127.0.0.1:<port>
```

Connect with `ssh CSE_T2`, keep the SSH session open, and visit `http://localhost:<port>/` in the local browser.

#### OneStopShop

```bash
cd ~/docker-images
docker load --input shopping_final_0712.tar
docker run --name shopping -p 7770:80 -p 13306:3306 -d shopping_final_0712
# wait about 1 minute for all services to start

docker exec shopping /var/www/magento2/bin/magento setup:store-config:set --base-url="http://localhost:7770"
docker exec shopping mysql -u magentouser -pMyPassword magentodb -e 'UPDATE core_config_data SET value="http://localhost:7770/" WHERE path = "web/secure/base_url";'
docker exec shopping /var/www/magento2/bin/magento cache:flush

# Allow WinArena task setup to reset the cart database through host.docker.internal:13306.
docker exec shopping mysql -uroot -p1234567890 -e "GRANT ALL ON magentodb.* TO 'magentouser'@'%' IDENTIFIED BY 'MyPassword'; FLUSH PRIVILEGES;"
```

Local URL: `http://localhost:7770/`

#### E-commerce CMS

```bash
docker load --input shopping_admin_final_0719.tar
docker run --name shopping_admin -p 7780:80 -d shopping_admin_final_0719
# wait about 1 minute for all services to start

docker exec shopping_admin /var/www/magento2/bin/magento setup:store-config:set --base-url="http://localhost:7780"
docker exec shopping_admin mysql -u magentouser -pMyPassword magentodb -e 'UPDATE core_config_data SET value="http://localhost:7780/" WHERE path = "web/secure/base_url";'
docker exec shopping_admin /var/www/magento2/bin/magento cache:flush
```

Local admin URL: `http://localhost:7780/admin`

```text
username: admin
password: admin1234
```

#### Wikipedia

```bash
docker run -d --name=wikipedia --volume=./:/data -p 8888:80 ghcr.io/kiwix/kiwix-serve:3.3.0 wikipedia_en_all_maxi_2022-05.zim
```

Local URL: `http://localhost:8888/wikipedia_en_all_maxi_2022-05/A/User:The_other_Kiwix_guy/Landing`

#### Reddit-Style Forum

```bash
docker load --input postmill-populated-exposed-withimg.tar
docker run --name forum -p 9999:80 -d postmill-populated-exposed-withimg
```

Local URL: `http://localhost:9999/`

#### CAPTCHA Service

```bash
cd scripts
bash run_captcha_service.sh
```

Use deterministic challenge URLs generated by `src/win-arena-container/client/captcha_service.py` or the provided task examples.

## 5. Examples and Benchmark Positioning

### Example Tasks

| Disability Group | Category | Platform | Example Task |
| --- | --- | --- | --- |
| Visual impairment | Health / Access | Android | Enable Reading Mode and use it to read webpage content related to a medical appointment |
| Hearing impairment | Communication / Information | Android | Enable Live Caption and watch a video with spoken content |
| Motor impairment | Access / Management | Windows | Use the On-Screen Keyboard to enter required text |
| Cognitive impairment | Information / Management | Windows | Turn dense information into a short note, checklist, reminder, or calendar item using an appropriate cognitive support |

### Benchmark Comparison

| Category | Benchmark | Scale | Real OS / Interactive Env. | Text Input | Video Input | Audio Input | Accessibility-Oriented | Daily-Life Tasks | Multi-Scenario | End-to-End GUI Execution |
| --- | --- | ---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Web GUI Agents | WebArena | 812 tasks | ◐ | ✓ | ✗ | ✗ | ✗ | ◐ | ✓ | ✓ |
| Web GUI Agents | VisualWebArena | 910 tasks | ◐ | ✓ | ✗ | ✗ | ✗ | ◐ | ✓ | ✓ |
| OS / Mobile Computer Use | OSWorld | 369 tasks | ✓ | ✓ | ✗ | ✗ | ✗ | ◐ | ✓ | ✓ |
| OS / Mobile Computer Use | AndroidWorld | 116 task types | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ |
| Multimodal / Video-Aware GUI Agents | VideoWebArena | 2,021 tasks | ◐ | ✓ | ✓ | ◐ | ✗ | ◐ | ✓ | ✓ |
| Multimodal / Video-Aware GUI Agents | VideoGUI | 86 tasks / 463 subtasks | ◐ | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ | ◐ |
| Multimodal / Video-Aware GUI Agents | OmniGUI | 709 episodes / 2,579 steps | ✓ | ✓ | ✓ | ✓ | ✗ | ◐ | ✓ | ◐ |
| Accessibility / User Assistance | A11y-CUA | 60 tasks | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ◐ | ✗ |
| Accessibility / User Assistance | GUIDE | 67.5h videos / 120 users | ◐ | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ |
| **Ours** | **Ours** | **200 tasks** | **✓** | **✓** | **✓** | **✓** | **✓** | **✓** | **✓, 8 scenarios** | **✓** |

**Symbols:** ✓ = supported; ✗ = not supported; ◐ = partially supported or limited setting.

Our benchmark is designed specifically for accessibility-oriented GUI-agent evaluation. It combines real OS/mobile interactive environments, multimodal inputs, daily-life accessibility scenarios, and end-to-end GUI execution with deterministic evaluators.

## 6. Environment Maintenance

### Rebuild the WinArena Image

Changes to `src/win-arena-container/Dockerfile-WinArena`, including added Python packages, take effect only after rebuilding the WinArena image. Restart `run_human.py` after the rebuild so it creates a fresh container from the updated image.

```bash
cd ~/WindowsAgentArena/scripts
./build-container-image.sh --mode dev
```

### Recreate the Windows VM Storage

Rebuilding the Docker image does not update an already-prepared Windows VM disk at `src/win-arena-container/vm/storage/data.img`. If Windows-side setup changes are needed, back up the old VM storage and prepare a fresh VM image:

```bash
cd /home/weimingli/projects/WindowsAgentArena
mv src/win-arena-container/vm/storage src/win-arena-container/vm/storage.bak
mkdir -p src/win-arena-container/vm/storage

cd scripts
./run.sh --mode dev --prepare-image true --skip-build true --start-client false --container-name winarena
```

### Make Persistent Changes to the Windows VM

To make manual changes directly to the persistent VM, start it without prepare mode:

```bash
cd /home/weimingli/projects/WindowsAgentArena/scripts
./run.sh --mode dev --prepare-image false --skip-build true --start-client false --container-name winarena
```

This uses `src/win-arena-container/vm/storage` directly. Windows-side changes such as installed software, system settings, or Python packages are saved to that storage only after a normal Windows shutdown.

### Install Missing Windows-Side Python Packages

If a command inside the Windows VM fails with `ModuleNotFoundError`, add the package to `src/win-arena-container/vm/setup/server/requirements.txt`. For an already-running VM, install it in the Windows VM Python environment using Python 3.10 explicitly:

```powershell
$py310 = "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe"
& $py310 -m pip install --no-cache-dir <package-name>
```

Example:

```powershell
$py310 = "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe"
& $py310 -m pip install --no-cache-dir openpyxl
& $py310 -c "import openpyxl; print('openpyxl ok')"
```

## 7. Assignees

| Disability Group | Assignee |
| --- | --- |
| Visual impairment | chaw |
| Hearing impairment | weiming |
| Motor impairment | kaung |
| Cognitive impairment | weiming |
