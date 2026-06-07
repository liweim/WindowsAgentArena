# Accessibility-Oriented GUI Agent Benchmark Guidelines

This benchmark evaluates GUI agents in accessibility-related usage scenarios. Tasks should reflect realistic situations where users with different assistive access needs rely on accessibility tools, system features, or alternative interaction methods to complete digital workflows.

The benchmark uses unified objectives, task construction logic, annotation conventions, and evaluation protocols, while supporting platform-specific implementations.

## Tracks

The benchmark contains two implementation tracks:

| Track   | Base Environment            | Scope                                                                                          |
| ------- | --------------------------- | ---------------------------------------------------------------------------------------------- |
| Windows | OSWorld / WindowsAgentArena | Desktop applications, browsers, files, media, system settings, and Windows accessibility tools |
| Android | AndroidWorld                | Mobile applications, Android system features, and Android accessibility tools                  |

The two tracks should be implemented and evaluated independently while following the same task design principles.

## Disability Groups and Assignees

| Disability Group     | Assignees    |
| -------------------- | ------------ |
| Visual impairment    | chaw / kaung |
| Hearing impairment   | weiming      |
| Motor impairment     | chaw / kaung |
| Cognitive impairment | weiming      |

## Disability Groups and Assistive Tools

Tasks should be grounded in the needs of specific disability groups. Different groups may rely on different assistive technologies, accessibility settings, or interaction methods.

| Disability Group     | Windows Tools                                            | Android Tools                                 |
| -------------------- | -------------------------------------------------------- | --------------------------------------------- |
| Visual impairment    | NVDA                                                     | TalkBack, Reading Mode, Seeing AI, Be My Eyes |
| Hearing impairment   | Windows Live Captions, Chrome Live Caption               | Android Live Caption                          |
| Motor impairment     | On-Screen Keyboard, Sticky Keys, Filter Keys, Mouse Keys | Accessibility Menu                            |
| Cognitive impairment | Immersive Reader in Edge                                 | Reading Mode                                  |

WCAG 2.2 covers users with visual, auditory, physical, speech, cognitive, language, learning, and neurological disabilities. Task design may focus on one disability group at a time, but the scenario should clearly reflect that group’s access needs.

## Task Categories

Use the following category labels:

* `Communication`
* `Information`
* `Management`
* `Mobility`
* `Consumption`
* `Service`
* `Health`
* `Access`

These categories are inspired by the ICF Activities and Participation domains, including communication, mobility, domestic life, interpersonal interactions, major life areas, and community, social, and civic life.

| Category        | Description                                                                                                                                         |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Communication` | Sending and receiving messages, email communication, meetings, contact management, and social interaction                                           |
| `Information`   | Browsing webpages, reading documents and PDFs, searching for information, and comparing content                                                     |
| `Management`    | Managing calendars, reminders, to-do items, deliveries, bills, and appointments                                                                     |
| `Mobility`      | Route planning, ride-hailing, public transit schedules, location search, and accessible entrance lookup                                             |
| `Consumption`   | Product search, price comparison, add-to-cart, order placement, after-sales service, and coupon use                                                 |
| `Service`       | Bill payment, statement inquiry, form submission, government service appointments, and identity verification                                        |
| `Health`        | Medical appointment booking, health records, prescription ordering, hospital information, and emergency contacts                                    |
| `Access`        | Enabling or configuring accessibility tools such as screen readers, captions, magnification, reading mode, keyboard assistance, or mouse assistance |

## Source Grounding

Each task should be grounded in a realistic accessibility use case from public accessibility resources, product documentation, support pages, tutorials, or user-oriented guidance.

Useful sources include:

| Resource                                                                                                                   | Disability Groups                 | Typical Task Types                                                                                                                                  |
| -------------------------------------------------------------------------------------------------------------------------- | --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Hadley Learn / Hadley Presents                                                                                             | Visual                            | Information access, travel, shopping, health management, organization, and independent living                                                       |
| APH ConnectCenter / VisionAware / CareerConnect                                                                            | Visual                            | Learning, employment, information management, independent living, navigation, and assistive technology use                                          |
| RNIB Technology for Life                                                                                                   | Visual                            | Device setup, screen reading, magnification, and basic mobile operations                                                                            |
| It’s Done!                                                                                                                 | Cognitive                         | Memory support, daily routine tracking, everyday task confirmation, and independent living support                                                  |
| My PATI                                                                                                                    | Cognitive                         | Preference expression, daily activity selection, communication support, and simplified touchscreen interaction                                      |
| WorkingHandsFree                                                                                                           | Motor                             | Hands-free device use, alternative input workflows, and computer or phone control without hand use                                                  |
| AbilityNet / My Computer My Way                                                                                            | Visual, Hearing, Motor, Cognitive | Device setup, reading optimization, captions, input assistance, and general digital skills                                                          |
| Apple Accessibility User Guides / Google Android Accessibility Help / Microsoft Accessibility Help / Windows Accessibility | Visual, Hearing, Motor, Cognitive | Accessibility feature setup, captions, simplified interfaces, screen readers, magnification, shortcuts, on-screen keyboards, and input optimization |
| Chrome Reading / Caption documentation                                                                                     | Visual, Hearing, Cognitive        | Reading mode, captions, translation, and web content consumption                                                                                    |

The task `source` field should point to the concrete webpage, document, support article, app documentation, file, or media page used by the task whenever possible.

## Task Construction Workflow

A task should be constructed through the following process:

1. Collect realistic user scenarios from credible resources.
2. Derive executable procedures from official instructions or product documentation.
3. Translate the procedure into a specific platform environment.
4. Define a measurable user goal.
5. Build a deterministic evaluator.
6. Manually verify that the task is authentic, workable, and evaluable.

## Task Requirements

Each task should include:

1. A realistic application, browser, media, document, or system-settings scenario.
2. A clearly required assistive tool or accessibility feature.
3. A concrete user goal that depends on accessible information, controls, or feedback.
4. An initial state that prepares the relevant app, page, file, media, message, or setting.
5. A measurable final output or system state.
6. A deterministic evaluator that checks the result and, when possible, the assistive tool state.

The setup should prepare the task without completing it. It may launch an app, open a webpage, place files in known folders, create input data, start media, or open a settings page.

If the model needs to output text, the output should be saved to a specified file so that it can be evaluated deterministically.

## Example Tasks

| Disability Group | Category                    | Platform | Example Task                                                                            |
| ---------------- | --------------------------- | -------- | --------------------------------------------------------------------------------------- |
| Visual           | Health / Access             | Android  | Enable Reading Mode and use it to read webpage content related to a medical appointment |
| Hearing          | Communication / Information | Android  | Enable Live Caption and watch a video with spoken content                               |
| Motor            | Access / Management         | Windows  | Open the On-Screen Keyboard and use it to enter a piece of text                         |
| Cognitive        | Information                 | Windows  | Enable Reading Mode in Chrome, read a web article, and adjust the font size or theme    |

## JSON Structure

Each task JSON should define:

* `id`: task identifier.
* `snapshot`: base environment snapshot.
* `instruction`: user-facing task instruction.
* `source`: grounding source for the scenario.
* `config`: setup actions for the app, page, file, media, or system state.
* `trajectory`: trajectory output directory.
* `related_apps`: applications involved in the task.
* `evaluator`: deterministic checks for task success.

When a task has multiple required success conditions, use an `and` conjunction so all conditions must be satisfied.

## Naming Rules

Task JSON filenames and ids should use this pattern:

```text
<Category>-<short_task_name>.json
```

Rules:

* The category prefix must use the exact category label.
* The short task name should use lowercase snake case.
* The JSON `id` must match the filename without `.json`.
* Add a short suffix only when needed to avoid duplicate names.

Examples:

```text
Access-live_caption.json
Service-ftc_complaint.json
Information-read_video_caption.json
Management-onscreen_keyboard_reminder.json
```

## Evaluation Rules

Prefer deterministic checks over subjective grading.

Evaluators may check:

* whether the final answer is saved in the expected file;
* whether the target file, document, setting, browser tab, form, media state, or application state matches the expected result;
* whether required content is present and prohibited content is absent;
* whether the output is stable across repeated runs.

Expected outputs should be short, stable, and unambiguous. Avoid tasks that depend on current news, changing rankings, personalized recommendations, or volatile page layouts unless the source is pinned or cached.

## Task Quality Checklist

Before submission, verify that:

* the scenario is realistic and source-grounded;
* the task matches the selected disability group’s needs;
* the assistive tool is necessary for the workflow;
* the task can be completed in the target platform environment;
* the setup initializes the task without solving it;
* the instruction clearly states the tool and goal;
* the evaluator is deterministic and stable;
* the expected output is clear and reproducible;
* the task avoids unnecessary open-ended browsing or unstable web content;
* the task is meaningfully different from a general GUI task.