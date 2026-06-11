# Accessibility-Oriented GUI Agent Benchmark Guidelines

This benchmark evaluates GUI agents on accessibility-related digital tasks. Each task should reflect a realistic scenario where users rely on assistive tools, accessibility settings, or alternative interaction methods to complete a workflow.

The benchmark supports platform-specific implementations while following shared task design, annotation, and evaluation principles.

## Tracks

| Track   | Base Environment            | Scope                                                                                  |
| ------- | --------------------------- | -------------------------------------------------------------------------------------- |
| Windows | OSWorld / WindowsAgentArena | Desktop apps, browsers, files, media, system settings, and Windows accessibility tools |
| Android | AndroidWorld                | Mobile apps, Android system features, and Android accessibility tools                  |

## Assignees

| Disability Group     | Assignees    |
| -------------------- | ------------ |
| Visual impairment    | chaw / kaung |
| Hearing impairment   | weiming      |
| Motor impairment     | chaw / kaung |
| Cognitive impairment | weiming      |

## Disability Groups and Assistive Tools

Tasks should be grounded in the access needs of one primary disability group.

| Disability Group     | Windows Tools                                            | Android Tools                                 |
| -------------------- | -------------------------------------------------------- | --------------------------------------------- |
| Visual impairment    | NVDA                                                     | TalkBack, Reading Mode, Seeing AI, Be My Eyes |
| Hearing impairment   | Windows Live Captions, Chrome Live Caption               | Android Live Caption                          |
| Motor impairment     | On-Screen Keyboard, Sticky Keys, Filter Keys, Mouse Keys | Accessibility Menu                            |
| Cognitive impairment | Immersive Reader in Edge                                 | Reading Mode                                  |

Task scenarios may involve visual, auditory, physical, speech, cognitive, language, learning, or neurological access needs, but each task should make the relevant access need clear.

## Task Categories

Use one of the following category labels:

| Category        | Description                                                                                                                                         |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Communication` | Messaging, email, meetings, contacts, and social interaction                                                                                        |
| `Information`   | Browsing, reading documents, searching, and comparing content                                                                                       |
| `Management`    | Calendars, reminders, to-do items, bills, deliveries, and appointments                                                                              |
| `Mobility`      | Route planning, ride-hailing, transit schedules, location search, and accessible entrance lookup                                                    |
| `Consumption`   | Product search, price comparison, add-to-cart, orders, after-sales service, and coupon use                                                          |
| `Service`       | Bill payment, statement inquiry, form submission, government services, and identity verification                                                    |
| `Health`        | Medical appointments, health records, prescriptions, hospital information, and emergency contacts                                                   |
| `Access`        | Enabling or configuring accessibility tools such as screen readers, captions, magnification, reading mode, keyboard assistance, or mouse assistance |

## Source Grounding

Each task should be based on a realistic accessibility use case from credible public resources, such as product documentation, accessibility support pages, tutorials, or user-oriented guidance.

Useful sources include:

| Resource                                               | Typical Use                                                                                                                     |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| Hadley Learn / Hadley Presents                         | Visual-access scenarios involving information access, travel, shopping, health management, organization, and independent living |
| APH ConnectCenter / VisionAware / CareerConnect        | Visual-access scenarios involving learning, employment, information management, navigation, and assistive technology            |
| RNIB Technology for Life                               | Screen reading, magnification, device setup, and mobile accessibility                                                           |
| It’s Done! / My PATI                                   | Cognitive-access scenarios involving memory support, daily routines, preferences, and simplified interaction                    |
| WorkingHandsFree                                       | Motor-access scenarios involving hands-free workflows and alternative input                                                     |
| AbilityNet / My Computer My Way                        | General accessibility setup across visual, hearing, motor, and cognitive needs                                                  |
| Apple / Google / Microsoft accessibility documentation | Official guidance for accessibility features, captions, screen readers, magnification, shortcuts, and input support             |
| Chrome reading and caption documentation               | Reading mode, captions, translation, and web content consumption                                                                |

The `source` field should point to the concrete webpage, document, support article, app documentation, file, or media page used by the task whenever possible.

## Task Requirements

Each task should include:

1. A realistic app, browser, media, document, or system-settings scenario.
2. A clearly required assistive tool or accessibility feature.
3. A concrete user goal that depends on accessible information, controls, or feedback.
4. An initial state that prepares the relevant app, page, file, media, message, or setting without completing the task.
5. A measurable final output or system state.
6. A deterministic evaluator that checks the result and, when possible, the required accessibility tool state.

If the task requires text output, the answer should be saved to a specified file so it can be evaluated deterministically.

## Task Construction Workflow

Use the following workflow:

1. Collect a realistic accessibility scenario from credible sources.
2. Derive an executable task from official instructions or product documentation.
3. Adapt the task to the target platform.
4. Define a measurable user goal.
5. Build a deterministic evaluator.
6. Manually verify that the task is realistic, executable, and evaluable.

## JSON Structure

Each task JSON should define the following keys:

`id` is a unique identifier for the task. It should match the JSON filename without the `.json` extension.

`snapshot` indicates the base environment or application context used for the task. (Not use any more)

`category` describes the task category. It must use one of the approved labels in the Task Categories section.

`difficulty` indicates the estimated task complexity.

`instruction` states the user-facing task goal.

`source` specifies the source of the task.

`gt_steps` lists the ground-truth steps needed to complete the task. These steps are for reproduction and verification.

`config` defines setup actions. Setup should prepare the task but not solve it.

`trajectory` specifies the directory where task execution traces or interaction logs may be stored. (Not use any more)

`related_apps` lists the applications involved in the task.

`evaluator` defines the deterministic logic used to judge whether the task was completed successfully.

Inside `evaluator`, `func` specifies the evaluation functions, `conj` defines how multiple conditions are combined, `result` describes the actual state or output to inspect, and `expected` defines the target condition used for comparison.

When a task has multiple required success conditions, use an `and` conjunction so that all conditions must pass.

## Naming Rules

Task JSON filenames and ids should follow this pattern:

```text
<Category>-<short_task_name>.json
```

Rules:

1. The category prefix must use the exact category label.
2. The JSON `category` value must match the filename prefix.
3. The short task name should use lowercase snake case.
4. The JSON `id` must match the filename without `.json`.
5. Add a short suffix only when needed to avoid duplicate names.

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

1. Whether the final answer is saved in the expected file.
2. Whether a target file, document, setting, browser tab, form, media state, or application state matches the expected result.
3. Whether required content is present and prohibited content is absent.
4. Whether the output is stable across repeated runs.

Expected outputs should be short, stable, and unambiguous. Avoid tasks that depend on current news, changing rankings, personalized recommendations, or volatile page layouts unless the source is pinned or cached.

## Hearing Tasks

For hearing-impairment tasks that require captions or live captions to extract spoken video content:

1. Prefer ordinary online video pages. Do not use YouTube Shorts or similar short-form pages.
2. Use videos that are short enough for practical evaluation, preferably no longer than 3 minutes.
3. The video must have captions or produce reliable live captions.
4. Avoid pages where the full transcript is directly visible before playback.
5. The instruction should require the relevant caption tool, such as Chrome Live Caption, Windows Live Captions, or Android Live Caption.
6. Expected answers should be extractable from captions alone unless the task explicitly permits visual inference.
7. For answer-list tasks, prefer concrete nouns, noun phrases, or short action phrases.
8. Expected answers must be unambiguous, stable, and directly grounded in the captions.
9. When possible, use the shortest complete continuous phrase that appears exactly in the captions.

Hearing-impairment tasks may also use AI text-to-speech audio instead of online videos. In particular, an `.mp3` file generated with ElevenLabs from a fixed script can be used as the caption input, which makes the spoken content easier to control, keeps expected answers stable, and reduces errors caused by unreliable live-caption recognition. The script should be saved with the task materials and treated as the source of truth for expected answers. The task should still require Windows Live Captions, Chrome Live Caption, or Android Live Caption, and the expected answers should be exact continuous phrases from the TTS script.

## Caption Phrase Evaluation

For hearing-impairment video tasks where answers are extracted from captions into a spreadsheet, use phrase-containment coverage unless a stronger task-specific evaluator is available.

The evaluator should:

1. Read the target answer column from the spreadsheet.
2. Remove blank rows and duplicate actual answers.
3. Lightly normalize answers by lowercasing, trimming whitespace, and collapsing repeated spaces.
4. For each expected answer, check whether any actual answer contains the complete expected phrase.
5. Count the expected answer as matched if the complete normalized expected phrase appears in at least one normalized actual answer.
6. Compute coverage as `matched_expected_count / expected_count`.

Expected answers should be complete, continuous caption phrases. Avoid broad single-word answers, overlapping expected answers, paraphrases, synonyms, or visually inferred answers unless the task explicitly requires them.

## Example Tasks

| Disability Group     | Category                    | Platform | Example Task                                                                            |
| -------------------- | --------------------------- | -------- | --------------------------------------------------------------------------------------- |
| Visual impairment    | Health / Access             | Android  | Enable Reading Mode and use it to read webpage content related to a medical appointment |
| Hearing impairment   | Communication / Information | Android  | Enable Live Caption and watch a video with spoken content                               |
| Motor impairment     | Access / Management         | Windows  | Open the On-Screen Keyboard and use it to enter a piece of text                         |
| Cognitive impairment | Information                 | Windows  | Enable Reading Mode in Chrome, read a web article, and adjust the font size or theme    |

## Benchmark Comparison

The following table compares our benchmark with representative GUI-agent, multimodal GUI, and accessibility-related benchmarks.

| Category                            | Benchmark      |                      Scale | Real OS / Interactive Env. | Text Input | Video Input | Audio Input | Accessibility-Oriented | Daily-Life Tasks |   Multi-Scenario   | End-to-End GUI Execution |
| ----------------------------------- | -------------- | -------------------------: | :------------------------: | :--------: | :---------: | :---------: | :--------------------: | :--------------: | :----------------: | :----------------------: |
| Web GUI Agents                      | WebArena       |                  812 tasks |              ◐             |      ✓     |      ✗      |      ✗      |            ✗           |         ◐        |          ✓         |             ✓            |
| Web GUI Agents                      | VisualWebArena |                  910 tasks |              ◐             |      ✓     |      ✗      |      ✗      |            ✗           |         ◐        |          ✓         |             ✓            |
| OS / Mobile Computer Use            | OSWorld        |                  369 tasks |              ✓             |      ✓     |      ✗      |      ✗      |            ✗           |         ◐        |          ✓         |             ✓            |
| OS / Mobile Computer Use            | AndroidWorld   |             116 task types |              ✓             |      ✓     |      ✗      |      ✗      |            ✗           |         ✓        |          ✓         |             ✓            |
| Multimodal / Video-Aware GUI Agents | VideoWebArena  |                2,021 tasks |              ◐             |      ✓     |      ✓      |      ◐      |            ✗           |         ◐        |          ✓         |             ✓            |
| Multimodal / Video-Aware GUI Agents | VideoGUI       |    86 tasks / 463 subtasks |              ◐             |      ✓     |      ✓      |      ✗      |            ✗           |         ✗        |          ✓         |             ◐            |
| Multimodal / Video-Aware GUI Agents | OmniGUI        | 709 episodes / 2,579 steps |              ✓             |      ✓     |      ✓      |      ✓      |            ✗           |         ◐        |          ✓         |             ◐            |
| Accessibility / User Assistance     | A11y-CUA       |                   60 tasks |              ✓             |      ✓     |      ✓      |      ✓      |            ✓           |         ✓        |          ◐         |             ✗            |
| Accessibility / User Assistance     | GUIDE          |   67.5h videos / 120 users |              ◐             |      ✓     |      ✓      |      ✓      |            ✗           |         ✗        |          ✓         |             ✗            |
| **Ours**                            | **Ours**       |              **200 tasks** |            **✓**           |    **✓**   |    **✓**    |    **✓**    |          **✓**         |       **✓**      | **✓, 8 scenarios** |           **✓**          |

**Symbols:** ✓ = supported; ✗ = not supported; ◐ = partially supported or limited setting.

Benchmarks are grouped by their primary focus: web-based GUI agents, OS/mobile computer-use agents, multimodal GUI agents, and accessibility/user-assistance datasets. Our benchmark is listed last for comparison.

Compared with existing benchmarks, our benchmark is designed specifically for accessibility-oriented GUI-agent evaluation. It combines real OS or mobile interactive environments, multimodal inputs including text, video, and audio, daily-life accessibility scenarios, and end-to-end GUI execution. Unlike general GUI benchmarks that mainly test web or app operation ability, our benchmark explicitly requires agents to use accessibility tools such as captions, screen readers, reading modes, and alternative input features. Compared with accessibility/user-assistance datasets that may focus on user behavior analysis or non-executable assistance, our benchmark provides executable tasks with deterministic evaluators, making it suitable for measuring whether GUI agents can actually complete accessibility-related workflows in realistic environments.
