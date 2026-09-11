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

### Agent–User Handoff and the Role of Assistive Technology

The benchmark evaluates whether a computer-use agent can solve a user's task **for the user** while leaving the resulting computer state usable, inspectable, and continuable by that user. Assistive technology (AT) and accessibility settings are therefore primarily **user-facing handoff state**, not restrictions that force the agent to imitate how a person with a disability operates the computer.

Unless a task explicitly defines an interaction constraint, the agent may use its normal computer-use capabilities, including visual perception, mouse input, keyboard input, and supported structured observations. The agent is not expected to simulate a disability or reproduce a human AT interaction trajectory. Instead, it should complete the user's goal and, when required, preserve or configure the relevant accessibility state so the user can monitor the result, inspect it, continue the workflow, or take control afterward.

This design creates a meaningful distinction from ordinary GUI automation in two ways. First, some tasks require an accessibility feature or support state as part of successful completion, and the evaluator verifies that state in addition to the task result. Second, tasks are grounded in access needs that differ across user groups, enabling analysis of where current agents succeed or fail for visual, hearing, motor, and cognitive accessibility scenarios.

Accordingly, evaluators should score the **user-facing outcome and required accessibility state**, not whether the agent followed the same interaction strategy as the target user group. Studies that constrain an agent to keyboard-only, magnified, or screen-reader-mediated interaction answer a complementary question about AT-constrained agent behavior; this benchmark instead focuses on whether the agent can reliably complete accessibility-oriented user goals and hand control back in an appropriate state.

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
2. A clearly grounded accessibility need, support strategy, or disability-relevant interaction challenge mapped to the Documented User Need Taxonomy below.
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

### Documented User Need Taxonomy and Annotation

Every task must map to at least one **documented user need**: a reusable accessibility barrier or support requirement that is explicitly supported by user surveys/research, W3C accessibility user requirements/design patterns, or official accessibility documentation. The exact task topic does **not** need to appear in a survey. For example, a specific shopping item can instantiate a documented need for screen-reader access or decision support; the evidence must support the access need, not that particular product.

`paper/documented_user_need_taxonomy.json` is the machine-readable source of truth for need definitions, evidence-source IDs, and source URLs. Do not invent a new need for one task if an existing need already captures the underlying barrier. If no existing need defensibly fits, mark the task for review rather than forcing a mapping.

The user-group directory (`visual/`, `hearing/`, `motor/`, `cognitive/`) remains the authoritative primary group label. Do not duplicate it with a `user_group` JSON field. Workflow `category` remains orthogonal to user group.

#### Visual

| ID | Documented user need | Definition | Evidence |
| --- | --- | --- | --- |
| `V1` | Non-visual access to digital text and interface content | Use screen readers or equivalent non-visual representations to read, navigate, and act on digital text, controls, documents, and web content. | WebAIM Screen Reader Survey #10; W3C Visual Disabilities |
| `V2` | Magnification and text enlargement | Enlarge text, controls, or the screen through zoom, text sizing, or magnification so content is perceivable and usable. | WebAIM Low Vision Survey #2; WCAG 1.4.4 Resize Text |
| `V3` | Contrast and display-palette customization | Adjust contrast, foreground/background presentation, inversion, or display palette to improve visual readability. | WebAIM Low Vision Survey #2; W3C Visual Disabilities; Microsoft color/contrast docs |
| `V4` | Color-vision differentiation support | Use color filters or non-color cues when color differences are difficult or impossible to distinguish. | WCAG 1.4.1 Use of Color; Microsoft color-filter docs |
| `V5` | Access to non-text visual information | Obtain equivalent information from images, maps, charts, infographics, scans, labels, and other visual-only or poorly described content. | WebAIM Screen Reader Survey #10; WCAG 1.1.1 Non-text Content |
| `V6` | Accessible CAPTCHA and verification | Complete verification without depending on inaccessible visual perception, including alternative modalities or delegated assistance. | WebAIM Screen Reader Survey #10; WCAG 1.1.1 Non-text Content |

#### Hearing

| ID | Documented user need | Definition | Evidence |
| --- | --- | --- | --- |
| `H1` | Speech-to-text access through captions or transcripts | Access spoken and relevant non-speech audio information through captions, live captions, or transcripts. | W3C media accessibility guidance; ACMA captioning research; AFB caption survey analysis |
| `H2` | Caption readability and language customization | Configure caption language and visual presentation so caption text is readable and appropriate for the media. | Microsoft hearing-access docs; ACMA captioning research |
| `H3` | Visual and persistent alternatives to auditory notifications | Receive alerts visually rather than by sound alone and keep visual notifications available long enough to notice and read. | Microsoft hearing-access docs |
| `H4` | Single-channel access to stereo audio | Combine stereo channels so information is not missed when a user hears through one channel or one headphone. | Microsoft hearing-access docs |
| `H5` | Verification without relying on hearing | Complete verification when the challenge depends on auditory perception, using a non-auditory alternative or delegated assistance. | WCAG 1.1.1 Non-text Content |

#### Motor

| ID | Documented user need | Definition | Evidence |
| --- | --- | --- | --- |
| `M1` | Alternative text entry without a physical keyboard | Enter text through an on-screen keyboard or other alternative input when physical keyboard use is difficult. | WebAIM Motor Disability Survey; Microsoft mobility docs |
| `M2` | Sequential modifier-key input | Use multi-key commands one key at a time instead of holding multiple keys simultaneously. | Microsoft mobility docs / Sticky Keys |
| `M3` | Keystroke filtering and sensitivity control | Reduce accidental repeated or brief key presses by adjusting keyboard sensitivity/filtering. | Microsoft mobility docs / Filter Keys |
| `M4` | Alternative pointer control or delegated pointing | Use keyboard, speech/other alternative input, or delegated pointer activation when conventional mouse use is difficult. | Microsoft mobility docs; WebAIM Motor Disability Survey |
| `M5` | Reduced press-hold and dragging demand | Avoid or reduce sustained press-hold-drag-release movements that require dexterity or sustained pointer control. | WCAG 2.5.7 Dragging Movements |
| `M6` | Mouse-button and handedness customization | Configure the primary mouse button or equivalent pointer settings to match reach, strength, dexterity, or unilateral motor needs. | Microsoft mobility docs |
| `M7` | Reduced pointer precision, repetition, and timing demand | Avoid or delegate repeated precise target acquisition, tightly timed pointer actions, or fine motor control. | WebAIM Motor Disability Survey; WCAG 2.5.7 |

#### Cognitive

| ID | Documented user need | Definition | Evidence |
| --- | --- | --- | --- |
| `C1` | Focus, readability, and simplification | Reduce distraction, visual/cognitive clutter, or reading load so attention, language processing, and comprehension are easier to sustain. | W3C Cognitive Accessibility; COGA Support Simplification |
| `C2` | Memory externalization and short-term retention support | Reduce reliance on working memory or short-term retention through notes, checklists, persistent cues, or delegated assistance. | COGA memory/calculation pattern |
| `C3` | Time and prospective-memory support | Use reminders, calendars, timers, and persistent time-based cues to manage appointments, deadlines, intervals, and future actions. | COGA Provide Reminders |
| `C4` | Planning, sequencing, task-state tracking, and completion recognition | Reduce the burden of unfamiliar or multi-step workflows, maintaining context, recovering after distraction, tracking progress, and recognizing successful completion. | COGA clear-steps/task-expectations/feedback patterns; Pew setup evidence only as supplementary age-related evidence |
| `C5` | Decision and choice support | Help compare alternatives, apply constraints, understand consequences, and select an appropriate option. | COGA Supported Choice |
| `C6` | Important-information extraction and prioritization | Identify and preserve the small set of important facts/actions from dense, mixed, or distracting information. | COGA Important Information; Support Simplification |
| `C7` | Calculation, counting, copying, and cross-source reconciliation support | Reduce reliance on arithmetic/counting, copying, short-term retention, or reconciliation across sources and steps. | COGA memory/calculation pattern |
| `C8` | Error prevention and safety-critical guidance | Make risky actions, scams, health/safety guidance, and error-prone choices easier to understand and act on correctly. | COGA error prevention; Supported Choice; Important Information |

#### Evidence source registry

| Source ID | Evidence source | Construction use |
| --- | --- | --- |
| `webaim_sr10` | [WebAIM Screen Reader User Survey #10 Results](https://webaim.org/projects/screenreadersurvey10/) | Screen-reader use, information finding, web/shopping use, alt-text and CAPTCHA barriers. 1,539 valid responses; WebAIM explicitly notes the sample was uncontrolled. |
| `webaim_lv2` | [WebAIM Survey of Users with Low Vision #2](https://webaim.org/projects/lowvisionsurvey2/) | Magnification, browser zoom, text sizing, high contrast, custom colors, reader settings. |
| `w3c_visual` | [W3C Visual Disabilities — Abilities and Barriers](https://www.w3.org/WAI/people-use-web/abilities-barriers/visual/) | Construct definitions for non-visual access, resizing, contrast, custom presentation, and navigation barriers. |
| `w3c_nontext` | [WCAG Understanding 1.1.1 Non-text Content](https://www.w3.org/WAI/WCAG21/Understanding/non-text-content) | Text alternatives and sensory alternatives for CAPTCHA/non-text content. |
| `w3c_resize` | [WCAG Understanding 1.4.4 Resize Text](https://www.w3.org/WAI/WCAG22/Understanding/resize-text) | Need for enlarged text/content. |
| `w3c_color` | [WCAG Understanding 1.4.1 Use of Color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color) | Barriers when information depends on color perception. |
| `ms_color` | [Microsoft: Use color and contrast for accessibility](https://support.microsoft.com/en-US/accessibility/windows/use-color-and-contrast-for-accessibility-in-microsoft-365) | Intended accessibility purpose of Windows/Microsoft color and contrast supports. |
| `w3c_media` | [W3C: Making Audio and Video Media Accessible](https://www.w3.org/WAI/media/av/) | Captions/transcripts as access to speech and relevant non-speech audio for Deaf and hard-of-hearing users. |
| `afb_ai_captions` | [AFB: Innovation for Access](https://www.afb.org/research-and-initiatives/ai-series/innovation-access) | 2026 report analyzing a 2025 survey; includes real caption-use patterns among D/HH participants. |
| `acma_captioning` | [ACMA: Use and experience of captioning consumer research](https://www.acma.gov.au/publications/2023-05/report/use-and-experience-captioning-consumer-research-support-acmas-captioning-quality-standard-review) | Deaf/HoH consumer use and expectations for captions across live, prerecorded, broadcast, and streaming media. |
| `ms_hearing` | [Microsoft: Make Windows easier to hear](https://support.microsoft.com/en-us/accessibility/windows/make-windows-easier-to-hear) | Mono audio, visual audio alerts, persistent notifications, live captions, and caption display customization. |
| `webaim_motor` | [WebAIM Survey of Users with Motor Disabilities](https://webaim.org/projects/motordisabilitysurvey/) | Alternative input, OS settings, speech input, on-screen keyboards, pointer modifications. The 46-response convenience sample is evidence that needs exist, not prevalence evidence. |
| `ms_mobility` | [Microsoft: Accessibility tools for mobility](https://support.microsoft.com/en-US/accessibility/accessibility-tools-for-mobility) | Sticky Keys, Filter Keys, Mouse Keys, on-screen keyboard, voice access, and eye control for limited reach/strength/dexterity. |
| `w3c_dragging` | [WCAG Understanding 2.5.7 Dragging Movements](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html) | Documents dexterity barriers in press-hold-drag-release interaction and the need for alternatives. |
| `w3c_coga_overview` | [W3C Cognitive Accessibility](https://www.w3.org/WAI/cognitive/) | High-level cognitive/learning access needs involving memory, attention, language, problem solving, and comprehension. |
| `coga_simplify` | [COGA: Support Simplification](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o8p03-complexity/) | Reduced content complexity and cognitive overload. |
| `coga_memory_calc` | [COGA: Do Not Rely on Users Calculations or Memorizing Information](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o6p05-low-cognition/) | Memory, calculation, copying, executive-function, and cross-step recall burdens. |
| `coga_reminders` | [COGA: Provide Reminders](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o7p07-reminders/) | Appointment/deadline reminders and time-management support. |
| `coga_steps` | [COGA: Make Each Step Clear](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o1p04-clear-steps/) | Orientation, step/progress awareness, and recovery after distraction in multi-step processes. |
| `coga_task_expectations` | [COGA: Provide Information So a User Can Complete and Prepare for a Task](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o5p04-task-expectations/) | Planning, working-memory load, process overview, and completion recognition. |
| `coga_choice` | [COGA: Clearly State Results and Disadvantages of Choices](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o7p03-supported-choice/) | Understanding alternatives, risks, consequences, and selections. |
| `coga_important` | [COGA: Make Important Tasks and Information Easy to Find](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o2p01-site-important/) | Locating and prioritizing important information under executive-function/memory limitations. |
| `coga_feedback` | [COGA: Provide Feedback](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o4p10-status-feedback/) | Status/completion feedback and reduced uncertainty/memory burden. |
| `coga_errors` | [COGA: Design Forms to Prevent Mistakes](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o4p04-supportive-forms/) | Error-prevention support for cognitive and learning disabilities. |
| `pew_setup` | [Pew Research Center: Navigating technological challenges](https://www.pewresearch.org/internet/2021/09/01/navigating-technological-challenges/) | Supplementary evidence for age-related/new-technology setup and learning support. **Do not use this as evidence that age itself is a cognitive disability.** |

#### Annotation rules

Each task JSON adds **one field only**:

- `need_ids`: one or more IDs from `paper/documented_user_need_taxonomy.json` (for example, `C2`, `M4`, `V6`). `[]` may be used only during drafting to flag an unresolved mapping; a released task must have at least one defensible need ID. Do not add ad-hoc status, naturalness, or free-text review fields to released task JSON.

The mapping question is: **Which documented accessibility barrier or support need does this task instantiate for its directory user group?** The exact task topic does not need to appear in the evidence source. Do not force a mapping merely to pass the schema: an unresolved task should be revised or withheld from release. Naturalness and task–need fit should still be reviewed during curation, but those judgments belong in review notes/checklists rather than released task metadata.

For CAPTCHA tasks, inspect the actual challenge rather than inferring the barrier from the word “CAPTCHA.” An audio-only challenge can directly instantiate `H5`; a visual CAPTCHA can instantiate `V6`; sustained press/hold or dragging can instantiate `M5`; and an otherwise ordinary pointer activation can instantiate `M4` when the relevant motor need is alternative/delegated pointing rather than fine precision.

Do not use survey percentages as population prevalence unless the survey design supports that inference. In particular, WebAIM explicitly describes Screen Reader Survey #10 as uncontrolled, and its Motor Disability Survey has a small convenience sample. These sources are used here to establish the existence and character of needs, not population-level rates.

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

Write `gt_steps` for annotators and task maintainers who need to reproduce a successful trajectory. Unlike `instruction`, `gt_steps` may include concrete UI navigation, intermediate UI actions, and exact values that must be entered or selected.

For tasks that benefit from reproducibility guidance, each `gt_steps` item should describe **one atomic executable action**. A step may contain the exact canonical value required by that action, but the value must be embedded in an operation such as typing it into a field, selecting it from a control, naming a file, or creating an item. Split independent actions into separate steps instead of writing a mini procedure inside one item.

Use the following rules:

1. Write steps in the order needed to reproduce a successful trajectory.
2. Keep one primary executable action per step, such as opening a page, selecting an option, entering a value, saving a file, or submitting a form.
3. Name the application, page, control, file, item, or field precisely enough for another annotator to follow the same path.
4. When an action requires a deterministic canonical value, include the exact value in backticks **inside that action**. Examples include text to type, a date to select, a filename to save, an event title to enter, a product to choose, or a setting value to select.
5. Do **not** add standalone answer-key steps such as `Standard answer — ...`, `The correct answer is ...`, `Read ... as ...`, or other steps whose only purpose is to state an extracted fact, intermediate conclusion, comparison result, or reasoning outcome. If a canonical answer matters, place it directly in the later UI action that uses it.
6. Do **not** expose reasoning or decision-making in `gt_steps`. Avoid steps such as comparing alternatives, explaining why one option is valid, eliminating candidates, or restating facts learned from source material. `gt_steps` should show what to do, not how to think about it.
7. When multiple outputs are genuinely valid and the evaluator accepts alternatives, describe the actionable acceptance criterion without inventing a single canonical answer.
8. Keep submission, confirmation, save, or send actions separate when they are required to complete the task.
9. Do not copy environment preparation into `gt_steps`; setup actions that occur before the agent starts belong in `config`.
10. Do not hide a known deterministic value behind vague wording such as `enter the result` when that value is required for reproduction. Put the exact value directly in the corresponding executable step.

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

For a task with a fixed answer, embed the answer only in the executable action that uses it:

```json
"gt_steps": [
  "Open `pharmacy_message.txt` on the Desktop.",
  "Open Thunderbird Calendar.",
  "Create a new all-day event on `July 20, 2026`.",
  "Set the event title to `Refill medication`.",
  "Save the calendar event."
]
```

Do not add a separate step such as `Standard answer — refill deadline: July 20, 2026` or `Read the refill deadline as July 20, 2026`. The canonical date is already present where it is operationally needed: the calendar-creation step.

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

Age alone is not sufficient to classify a task as cognitive. Task complexity alone is also not sufficient: an ordinary multi-step workflow should not be labeled cognitive merely because it requires planning, sequencing, working memory, attention, or decision-making. A cognitive-access task should make the agent's assistance materially reduce one of those barriers for the user—for example by externalizing memory into a reminder or checklist, simplifying dense information into an actionable form, reconciling multiple pieces of information, reducing time pressure, preserving task state, or producing a structured artifact that makes the next user action easier. Generic software installation, product lookup, shopping, or administrative data-entry tasks without such a cognitive-support outcome should be reassigned, redesigned, or removed.

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

1. Identify the primary user-group directory and at least one documented user need from the taxonomy above; record the supporting evidence source(s).
2. Collect or adapt a realistic scenario that naturally instantiates that need. Do not force a generic workflow into a disability group merely because a related accessibility citation exists.
3. Derive an executable task from the scenario and source material.
4. Adapt it to the target platform and available applications.
5. Define the user-facing goal and measurable final state.
6. Write a concise, direct, goal-oriented instruction.
7. Write reproducible `gt_steps` where they add value, using one executable action per step and embedding any deterministic canonical value only in the action that uses it.
8. Build a deterministic evaluator covering all graded requirements.
9. Annotate only `need_ids` using IDs from `paper/documented_user_need_taxonomy.json`; use `[]` only when no defensible mapping exists and flag that task in the separate construction review.
10. Set `proxy: true` whenever task setup or execution needs a public Internet resource. Do not infer this from `source` alone: a task that uses a locally saved copy of an externally sourced PDF/image remains `proxy: false`. `host.docker.internal` services are local benchmark infrastructure and remain `false`.
10. Manually verify that setup does not solve the task and that the task is realistic, executable, repeatable, and natural for the intended access-need group.

### Human / Expert Task Validation

Before benchmark release, validate the task set with reviewers who have accessibility expertise and, where feasible, people with lived experience of the represented access needs. Source grounding establishes that a scenario is plausible, but it does not by itself establish that the adapted GUI task is a valid or useful representation of an accessibility-oriented user goal.

The validation protocol should assess at least four dimensions:

1. **Realism:** whether the task resembles a plausible real-world computer-use need.
2. **Accessibility relevance:** whether the stated access need or support materially changes the user goal, required final state, information modality, or handoff requirement rather than serving only as superficial framing.
3. **Clarity and determinacy:** whether the instruction has a well-defined success condition without unintended ambiguity.
4. **Support appropriateness:** whether the selected assistive feature, accessibility setting, note, reminder, checklist, captioning workflow, route constraint, or other support is appropriate for the intended user need.

Use at least two independent reviewers per validated task or task sample when practical. Record ratings, disagreements, adjudication decisions, and any resulting task revisions. Revise, reassign, or remove tasks that fall below the pre-defined acceptance threshold. Paper-level framing, construct-validity claims, and reporting guidance are maintained in `paper_structure.md`.

## 3. Task JSON Specification

### Required / Supported Fields

Each task JSON may use the following fields:

| Field | Purpose |
| --- | --- |
| `id` | Unique task identifier. Must match the JSON filename without `.json`. |
| `category` | One approved lowercase category label. |
| `need_ids` | IDs from `paper/documented_user_need_taxonomy.json` that capture the documented access barrier/support need instantiated by the task. Keep this key immediately after `category`; use `[]` if no defensible mapping has been established. |
| `difficulty` | Estimated task complexity. |
| `instruction` | Direct user-facing task command. Follow the instruction style above. |
| `source` | Concrete source used to ground the task. |
| `gt_steps` | Ground-truth executable actions for annotator reproduction and verification. Keep each useful step atomic; embed canonical values only in the UI action that uses them, never as standalone answer-key or reasoning steps. CAPTCHA tasks may remain minimal. |
| `config` | Environment setup actions. Setup must prepare but not complete the task. |
| `related_apps` | Applications the agent actually interacts with while completing the task. Use the benchmark's existing canonical app identifiers; omit setup-only components and unrelated alternatives. |
| `evaluator` | Deterministic completion logic. |
| `proxy` | Whether task setup or execution requires access to a public Internet resource. Set `true` for real external sites/services/downloads (including external setup downloads); set `false` for local files, synthetic pages, and services under `host.docker.internal`. A public URL recorded only as provenance in `source` does not by itself make the task proxied when the task uses a local copy. |

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

Prefer deterministic state checks over subjective grading. The evaluator should judge whether the agent achieved the task goal, not whether it reproduced one arbitrary surface form of a correct answer.

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

#### Evaluation Design Principles

Use the following priorities when designing or reviewing an evaluator:

1. **Make the task answer unique at the semantic level.** A task should have one well-defined target state or set of facts. If the source permits multiple equally valid recommendations, rankings, interpretations, or summaries, add a deterministic selection criterion, pin the source state, or rewrite the task.
2. **Accept semantically equivalent natural-language answers.** Do not reject a correct answer because of capitalization, harmless whitespace, hyphenation, equivalent numeric formatting, or an accepted synonym.
3. **Require all essential facts.** Semantic tolerance must not make the evaluator permissive enough to accept an incomplete answer. Split an answer into atomic facts and require every fact that is necessary for correctness.
4. **Evaluate state structurally whenever possible.** Check recipients as addresses, calendar titles as titles, dates as dates, URLs as URLs, quantities as numbers, and application settings as settings rather than searching for those values anywhere in a large text dump.
5. **Use exact matching only when exact representation is part of the task.** Examples include text explicitly requested `exactly as shown`, a fixed template, a canonical filename, a specific URL, a required subject/title, or another field whose literal value is itself graded.
6. **Keep evaluation deterministic and reproducible.** Rule-based evaluators are preferred over LLM judges for benchmark scoring. LLM-based semantic judging should be reserved for tasks that cannot reasonably be reduced to stable facts or structured state.

#### Natural-Language Content Evaluation

For ordinary natural-language answers, avoid whole-answer `exact_match` or literal equality. Instead, decompose the expected answer into independently scoreable semantic points.

The compact text-rule notation is:

```text
"text"                 = this required expression must match
["a", "b", "c"]      = any_of: any one equivalent expression may match
{"all_of": [A, B]}    = all child rules A and B must match
{"regex": "..."}      = match a constrained pattern when literal variants are unsuitable
```

Lists deliberately serve as the compact `any_of` form so task JSON does not become dominated by repetitive wrapper objects. Dictionaries are reserved for explicit operators such as `all_of` and `regex`.

For example:

```json
"body_points": [
  {
    "all_of": [
      ["two", "2"],
      ["batteries", "battery"]
    ]
  },
  ["12-volt", "12 volt"],
  ["deep-cycle", "deep cycle"],
  "sealed",
  ["maintenance free", "maintenance-free"],
  [
    "supplied off-board battery charger",
    "supplied charger",
    "off-board battery charger"
  ],
  [
    "never use an extension cord",
    "do not use an extension cord",
    "no extension cord"
  ]
]
```

The first point means `(two OR 2) AND (batteries OR battery)`. This prevents a partial answer containing only `2` or only `battery` from receiving credit for the complete fact. The remaining list-valued points accept alternative surface forms of the same fact.

A point should represent one semantic fact. Do not place independent required facts in the same `any_of` list, because that changes an intended `AND` into an `OR`. Conversely, do not create separate required points for two phrases that are merely synonyms of each other.

For a task with several required facts, score coverage over the required points:

```text
score = matched_required_points / total_required_points
```

Use a stricter all-or-nothing state evaluator when partial completion is not meaningful. When text-point coverage is combined with other requirements such as the correct file, recipient, event date, or accessibility setting, combine those requirements explicitly rather than relying on text content to imply them.

#### Text Normalization

Text matching should normalize harmless presentation differences while preserving distinctions that affect meaning. Appropriate normalization includes:

- Unicode normalization;
- case-insensitive comparison unless capitalization is explicitly significant;
- trimming and collapsing repeated whitespace;
- treating common hyphen/dash variants consistently when they do not change meaning;
- accepting equivalent numeric formatting where appropriate, such as `0.6%` and `0.60%`;
- using boundaries for short numbers or tokens so that `20` does not accidentally match `2026`.

Do not globally strip arbitrary punctuation or units if doing so could change meaning. Dates, times, percentages, phone numbers, medication amounts, prices, and similar values should preferably use structured or constrained matching rather than loose substring checks.

#### When Exact Matching Is Appropriate

Whole-file or literal exact matching is appropriate when the instruction makes the representation itself part of the goal, for example:

```text
Copy the full product name exactly as shown.
```

or when the output follows a fixed canonical template. It is usually inappropriate for a fact-retrieval answer such as `gluten-free diet`, where `gluten free diet` is semantically identical, or for a short prose answer where labels such as `Start:` are not requested by the task.

Before using `exact_match`, ask: **Would a human consider a differently formatted but semantically identical answer wrong under the instruction?** If not, use semantic points or a structured evaluator instead.

#### Structured Artifact Rules

For email, calendar, file, and similar artifact tasks, evaluate each field according to its semantics rather than searching the entire serialized artifact.

- **Email recipients:** compare parsed addresses, not recipient-name substrings.
- **Email subject:** use exact or normalized equality when the instruction specifies a subject.
- **Email body:** use semantic points unless exact wording is requested.
- **Draft-only email tasks:** evaluate that the required draft exists with the correct fields/content. Do not add a Sent-folder absence check merely because the instruction says to save the message as a draft.
- **Calendar title:** compare against the event title/summary field, not arbitrary event text.
- **Calendar date/time:** compare parsed date/time values and relevant all-day/time-zone semantics.
- **Files:** separately check the correct path/name and the required content.
- **Spreadsheets:** prefer cell-, row-, or column-level values over whole-workbook textual comparison.
- **Browser/system settings:** use the underlying stable setting/state when available instead of visual text that may vary across versions.

#### Avoiding False Positives and False Negatives

Common false-negative patterns include:

- exact matching a natural-language answer;
- requiring an evaluator-invented label or punctuation that the instruction never requested;
- rejecting accepted synonyms or equivalent number/date formatting;
- coupling semantic correctness to irrelevant line wrapping or whitespace.

Common false-positive patterns include:

- treating several required components as alternatives;
- using loose substring matching for short numbers, dates, or addresses;
- checking a title, recipient, or field value anywhere in the full artifact instead of in the correct field;
- giving full credit for one fragment of a multi-part fact;
- accepting an answer selected by subjective preference when the task does not define a tie-break rule.

Every evaluator should therefore be tested with at least:

1. the canonical correct answer;
2. one or more semantically equivalent correct variants;
3. an answer missing each major required fact;
4. a plausible near-match that should be rejected;
5. formatting variants relevant to the task, such as case, whitespace, hyphens, dates, units, or numeric precision.

#### Expected-Answer Stability

Expected outputs should be short, stable, and unambiguous. Avoid tasks that depend on current news, changing rankings, personalized recommendations, volatile page layouts, or subjective review interpretation unless the source is pinned, cached, self-hosted, or the instruction defines a deterministic selection rule.

If multiple natural-language realizations are valid, encode those alternatives in the evaluator rather than forcing the task author to invent one canonical sentence. Determinism should come from the required facts and final state, not from arbitrary wording.

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

## 5. Task Examples

| Disability Group | Category | Platform | Example Task |
| --- | --- | --- | --- |
| Visual impairment | Health / Access | Android | Enable Reading Mode and use it to read webpage content related to a medical appointment |
| Hearing impairment | Communication / Information | Android | Enable Live Caption and watch a video with spoken content |
| Motor impairment | Access / Management | Windows | Use the On-Screen Keyboard to enter required text |
| Cognitive impairment | Information / Management | Windows | Turn dense information into a short note, checklist, reminder, or calendar item using an appropriate cognitive support |

These examples illustrate task-construction patterns only. Benchmark positioning, comparisons with prior work, research questions, experimental plans, and paper-level claims are maintained separately in `paper_structure.md`.

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
| Visual impairment | chaw & kaung |
| Hearing impairment | weiming |
| Motor impairment | chaw & kaung |
| Cognitive impairment | weiming |
