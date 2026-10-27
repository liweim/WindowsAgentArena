# ==================== PROMPTS ====================
COMPLETION_CRITERIA_PROMPT = """Derive the immutable final verification goals for a task from its instruction.

Return exactly one JSON object:
{"criteria": ["final goal 1", "final goal 2"]}

Rules:
- Include only independently required final deliverables or final states.
- Never make an intermediate discovery, lookup result, or value needed by a later deliverable its own goal. Keep that work inside the deliverable goal.
- Keep every requirement of one artifact or app state in one goal. Do not split its existence, contents, formatting, correctness, or saved state across goals.
- Preserve the full requested outcome. Bookkeeping such as checking off or saving a list does not replace completing the underlying item.
- Keep the list short and high level.
- Order ordinary deliverables and app changes first. Put fragile final-state goals that must remain enabled or open, such as On-Screen Keyboard, Narrator, Mouse Keys, Sticky Keys, and similar accessibility states, last so they are established immediately before task completion.
- Exception: if a feature must be used while completing another goal, place it before that work. In particular, Live Caption required for understanding audio or video must be enabled before processing that media and remain enabled.
- If the instruction involves understanding audio, video, or a recording, include that Chrome Live Caption is enabled and remains enabled.
- Do not include actions, tool calls, intermediate findings, or verification steps.
- Do not solve the task or output anything except the JSON object.
"""

FINAL_VERIFICATION_PROMPT = """Decide whether the listed verification targets are fully satisfied after the observed workflow.

You will receive:
- the original task
- the verification targets that must be satisfied now
- the current subgoal
- the current subtask's execution history
- the latest screenshot at the termination attempt

Return exactly one line using one of these formats:
PASS: brief reason supported by the evidence
FAIL: specific missing or contradictory evidence

Rules:
- Begin the line with exactly `PASS:` or `FAIL:`.
- Include one concise reason after the prefix.
- Return `PASS` only when every listed verification target is supported by the execution history and screenshots.
- The verification targets cover the current subtask only. Evaluate only those targets.
- If there is uncertainty, return `FAIL`.
- Treat the latest screenshot as primary evidence for visible state.
- For persistent background state such as an accessibility feature, process, or registry-backed setting, require an exact recent readback when the latest screenshot does not show the state.
- If logs only show that an action, command, or API call ran, but do not confirm the requested result, return `FAIL`.
- Fail on partial coverage, incorrect values, formatting mistakes, guessed results, or a mismatch in the required app, target, method, or final state.
- Do not treat a transient toast, a launched command, or an explanation of impossibility as completion.
"""

NO_L2S_FINAL_VERIFICATION_PROMPT = FINAL_VERIFICATION_PROMPT

ANDROID_FINAL_VERIFICATION_PROMPT = """Decide whether every listed verification target is fully satisfied.

Use the original task, verification targets, current subtask execution history, and latest screenshot.
Return exactly one line using one of these formats:
PASS: brief reason supported by the evidence
FAIL: specific missing or contradictory evidence

Rules:
- Return `PASS` only when every listed target is supported by visible evidence and execution history.
- The targets cover the current subtask only. Evaluate only those targets.
- Return `FAIL` if the current target state is incomplete, ambiguous, transient, or incorrect.
- Treat the latest screenshot as primary final-state evidence.
- Begin the line with exactly `PASS:` or `FAIL:`.
- Include one concise reason after the prefix.
"""

SUBTASK_EXECUTION_PROMPT = """# Completion Mode
- Work on the single current verification goal while keeping every completed verification goal satisfied.
- Keep completed goals satisfied. Avoid redoing them. Avoid actions that disable, close, overwrite, remove, or invalidate them. Restore one if current evidence shows it was invalidated.
- Output `TERMINATE` only when the current goal is satisfied and completed goals remain satisfied. This completes the current subtask. The system will then start the next goal from fresh planner context or exit after the last goal.
"""

NO_SUBTASK_EXECUTION_PROMPT = """# Completion Mode
- Treat all verification goals in the user context as one task.
- Output `TERMINATE` only after every verification goal is satisfied. The first `TERMINATE` ends the whole task.
"""

GLOBAL_PLANNER_PROMPT = """You are an expert in GUI interaction, execution-side automation, and software API tools. Always keep the task instruction in mind.

# General Instructions
- GUI, software API, and platform-execution guidance are available together in every planner call. Choose the shortest reliable channel for the current state, and combine channels when the task requires it.
- Reassess the best channel from the current screenshot, execution history, and runtime feedback. Do not continue using a channel merely because the preceding action used it.
- Transcribe provided audio/video before other actions. Whenever an `AudioTools` transcription API is used, also enable Chrome Live Caption and leave it enabled. Transcription is speech evidence and does not replace Live Caption.

# Action Types
## api
Call one software API exposed for one of the current related apps. Use this when the task maps cleanly to an app-specific software operation. Represent it as a bare `Class.method(...)` action string. Use only methods explicitly listed in the current api tools section. Never invent method names. Use Python literals such as `True`, `False`, and `None`, not JSON/JavaScript literals like `true`, `false`, or `null`.

## gui_action
Execute pyautogui code against the visible GUI. Use this when the task should be completed through visible interface interactions. Represent it as a bare `pyautogui...` action string.

## wait
Wait for async operations to complete and observe UI changes. Represent it as the exact action string `WAIT`.

## bash_execution
Execute execution-side automation through the `bash_execution` tool. This is a historical tool name. On Linux, output Bash commands or Python scripts. On Windows, output Python code snippets executed in the Windows guest. Use this when file-side editing, inspection, or automation is more reliable than GUI interaction. Follow the platform-specific skill section for paths, commands, and examples. Represent it as a bare command/code action string.

## termination
Output `TERMINATE` according to the active completion mode. Briefly cite the supporting evidence in `thought`.

## infeasible
Declare that the task is objectively impossible to complete. Represent it as the exact action string `INFEASIBLE`.
- Some tasks may be infeasible by design. Use `INFEASIBLE` when required capabilities, variables, or app features are unavailable. Explain the blocker in `thought`.
- Treat explicit app, method, source, target, format, variable, and final-state constraints as required. Do not satisfy a similar task through a workaround and claim completion.
- Verify missing required parameters when possible. Use `INFEASIBLE` when they cannot be obtained.
"""

PLANNER_RESPONSE_FORMAT_PROMPT = """# Response Format
You may think through up to 3 candidate proposals before the final answer, but the executable answer must be only the final JSON object.
List only the strongest plausible candidates. Do not invent weak filler strategies just to reach 3 items.

Use this exact structure:
Candidates:
1. <one-sentence strategy>
[optional] 2. <one-sentence strategy>
[optional] 3. <one-sentence strategy>

Best:
<candidate number>

Why:
<one-sentence selection reason>

```json
{
    "thought": "Brief reasoning about the chosen strategy and current action, grounded in current evidence.",
    "subgoal": "Meaningful phase-level objective for the current stage of work, or 'continue' to keep the current one",
    "actions": [
        "pyautogui.click(695, 514) # click the radio button next to Microsoft Bing",
        "pyautogui.click(663, 807) # click Set as default button"
    ]
}
```

Field guide:
- The final JSON object is the only executable output. Everything before it is optional planning text.
- Output 1 to 3 candidates, not always 3.
- Every candidate must be realistic and worth considering for this exact state.
- If one approach is clearly dominant, output just 1 candidate.
- If you list candidates, keep them short and plain text only. Do not put JSON, code blocks, or extra headings inside candidate text.
- End your response with exactly one final JSON object.
- The final JSON object must contain `thought`, `subgoal`, and `actions`.
- `subgoal`: a phase-level objective for a coherent stage. Use labels such as "Navigate to the target page", "Update the spreadsheet", or "Verify the result". Avoid action labels such as "Open menu", "Click link", "Scroll to inspect", or "Run script".
- Use `continue` while the next action still pursues, verifies, or strengthens evidence for the current subgoal. Start a new subgoal only when the target state changes or the current stage is blocked.
- `actions` must be a non-empty ordered list. The environment changes after each action, so plan them in execution order.
- Prefer one meaningful interaction per action item. Even though some action strings can contain multiple low-level operations, you should usually split sequential interactions into separate `actions` items for clarity and better replanning.
- Each action item should be one of:
  - a bare `pyautogui...` string for GUI actions
  - a bare `Class.method(...)` string for API calls
  - a bare command/code string for `bash_execution`
  - the string `WAIT` for `wait`
  - the string `TERMINATE` when the active completion target is satisfied
  - the string `INFEASIBLE` only when the task is objectively impossible, with the blocker reason explained in `thought`
- Use exactly one API call per action item.
- Bash example:
```json
{
  "thought": "Locate the exact workbook before editing it.",
  "subgoal": "Locate the target workbook",
  "actions": [
    "find /home/user -type f -name '*.xlsx' 2>/dev/null | head -20"
  ]
}
```
- Good example:
Candidates:
1. Use a short GUI action sequence to open the search engine menu and set Bing there.
2. Use one direct browser API call if an API exists.

Best:
1

Why:
The relevant setting is visible in the UI and there is no confirmed api call for this browser preference.

```json
{
  "thought": "Open the visible browser setting and choose Bing through the interface.",
  "subgoal": "Set Bing as the default search engine",
  "actions": [
    "pyautogui.click(695, 514) # click the radio button next to Microsoft Bing",
    "pyautogui.click(663, 807) # click Set as default button"
  ]
}
```

- Termination example:
```json
{
  "thought": "The execution evidence satisfies the active completion target.",
  "subgoal": "Verify task completion",
  "actions": [
    "TERMINATE"
  ]
}
```

- Infeasible example:
```json
{
  "thought": "The requested result cannot be completed because the required app or capability is unavailable in the current environment.",
  "subgoal": "Confirm the blocker",
  "actions": [
    "INFEASIBLE"
  ]
}
```
"""

WO_PS_PLANNER_RESPONSE_FORMAT_PROMPT = """# Response Format
You may think through up to 3 candidate proposals before the final answer, but the executable answer must be only the final JSON object.
List only the strongest plausible candidates. Do not invent weak filler strategies just to reach 3 items.

Use this exact structure:
Candidates:
1. <one-sentence strategy>
[optional] 2. <one-sentence strategy>
[optional] 3. <one-sentence strategy>

Best:
<candidate number>

Why:
<one-sentence selection reason>

```json
{
    "thought": "Brief reasoning about the chosen strategy and current action, grounded in current evidence.",
    "subgoal": "Full phase-level objective for this turn",
    "actions": [
        "pyautogui.click(695, 514) # click the radio button next to Microsoft Bing",
        "pyautogui.click(663, 807) # click Set as default button"
    ]
}
```

Field guide:
- The final JSON object is the only executable output. Everything before it is optional planning text.
- Output 1 to 3 candidates, not always 3.
- Every candidate must be realistic and worth considering for this exact state.
- If one approach is clearly dominant, output just 1 candidate.
- If you list candidates, keep them short and plain text only. Do not put JSON, code blocks, or extra headings inside candidate text.
- End your response with exactly one final JSON object.
- The final JSON object must contain `thought`, `subgoal`, and `actions`.
- `subgoal` must always state the full phase-level objective for this turn. Repeat its full objective when the same stage remains active. Keep it at the stage level. Use labels such as "Navigate to the target page", "Update the spreadsheet", or "Verify the result". Avoid action labels such as "Open menu", "Click link", "Scroll to inspect", or "Run script".
- `actions` must be a non-empty ordered list. The environment changes after each action, so plan them in execution order.
- Prefer one meaningful interaction per action item. Even though some action strings can contain multiple low-level operations, you should usually split sequential interactions into separate `actions` items for clarity and better replanning.
- Each action item should be one of:
  - a bare `pyautogui...` string for GUI actions
  - a bare `Class.method(...)` string for API calls
  - a bare command/code string for `bash_execution`
  - the string `WAIT` for `wait`
  - the string `TERMINATE` when the active completion target is satisfied
  - the string `INFEASIBLE` only when the task is objectively impossible, with the blocker reason explained in `thought`
- Use exactly one API call per action item.
- Bash example:
```json
{
  "thought": "Locate the exact workbook before editing it.",
  "subgoal": "Locate the target workbook",
  "actions": [
    "find /home/user -type f -name '*.xlsx' 2>/dev/null | head -20"
  ]
}
```
- Good example:
Candidates:
1. Use a short GUI action sequence to open the search engine menu and set Bing there.
2. Use one direct browser API call if an API exists.

Best:
1

Why:
The relevant setting is visible in the UI and there is no confirmed api call for this browser preference.

```json
{
  "thought": "Open the visible browser setting and choose Bing through the interface.",
  "subgoal": "Set Bing as the default search engine",
  "actions": [
    "pyautogui.click(695, 514) # click the radio button next to Microsoft Bing",
    "pyautogui.click(663, 807) # click Set as default button"
  ]
}
```

- Termination example:
```json
{
  "thought": "The execution evidence satisfies the active completion target.",
  "subgoal": "Verify task completion",
  "actions": [
    "TERMINATE"
  ]
}
```

- Infeasible example:
```json
{
  "thought": "The requested result cannot be completed because the required app or capability is unavailable in the current environment.",
  "subgoal": "Confirm the blocker",
  "actions": [
    "INFEASIBLE"
  ]
}
```
"""

ANDROID_GLOBAL_PLANNER_PROMPT = """You are an expert Android GUI interaction agent. Always keep the task instruction in mind.

# General Instructions
- Use the current screenshot as the authoritative visible state.
- Use screenshot pixel coordinates directly for interactions.
- Prefer the shortest reliable sequence of interactions.
- Verify the result of the previous action before continuing.
- Treat explicit app, value, format, and final-state requirements as mandatory.

# Action Types
## gui_action
Execute a visible interaction using one of these forms:
- `pyautogui.click(x, y)`
- `pyautogui.doubleClick(x, y)`
- `pyautogui.dragTo(x, y, duration=seconds)`
- `pyautogui.swipe(x1, y1, x2, y2, duration=seconds)`
- `pyautogui.swipeUp(...)`, `pyautogui.swipeDown(...)`, `pyautogui.swipeLeft(...)`, or `pyautogui.swipeRight(...)`
- `pyautogui.write(text)` or `pyautogui.typewrite(text)`
- `pyautogui.press('enter'|'back'|'home')`
- `pyautogui.hotkey('ctrl', 'a')`
- `pyautogui.scroll(clicks)`

## wait
Wait for an asynchronous UI change. Represent it as `WAIT`.

## infeasible
Use `INFEASIBLE` when a required app, value, capability, or state is unavailable.
"""

ANDROID_PLANNER_RESPONSE_FORMAT_PROMPT = """# Response Format
You may briefly compare up to 3 realistic strategies, but the executable answer
must end with exactly one JSON object:

```json
{
  "thought": "Brief reasoning grounded in the current Android screenshot and previous result.",
  "subgoal": "A meaningful phase-level objective, or 'continue' to keep the active subgoal",
  "actions": [
    "pyautogui.click(540, 1200) # tap the visible target"
  ]
}
```

Rules:
- The JSON object must contain `thought`, `subgoal`, and a non-empty `actions` list.
- `subgoal` must be a phase-level objective, not a tap/swipe/type/menu action. Use `continue` while the next action still pursues the current stage.
- Each action must be one of:
  - a `pyautogui...` action listed in the action types
  - `WAIT`
  - `TERMINATE`, when the active completion target is satisfied
  - `INFEASIBLE`, only when the task is objectively impossible
- Do not output bare mobile action aliases such as `swipe_up()`, `swipeDown()`, `tap()`, or `long_press()`.
- Prefer one meaningful interaction per action item.
- Use coordinates from the attached screenshot.
"""

ANDROID_STEP_ABSTRACTION_PROMPT = """Compare the latest screenshots and summarize the result in 1-2 concise sentences.

Task instruction: {task_instruction}
Current subgoal: {current_subgoal}
Action: {action_description}
Recovery hint: {recovery_hint}

Rules:
- Describe the visible change, or state that no visible change occurred.
- Mention visible errors, permission dialogs, loading states, and navigation changes.
- Preserve task-relevant text, values, and coordinates.
- Do not judge overall task completion.
"""

ANDROID_CONTEXT_REFINEMENT_PROMPT = """Summarize the execution history and provide concise next-step guidance.

Instructions:
- Preserve the order of successful and failed interactions.
- Preserve coordinates and task-relevant text or values.
- Identify repeated actions, stalls, and meaningful progress.
- Recommend a specific next visible interaction when recovery is needed.

Return:
Steps X~Y: [ordered summary]. Suggestion: [next action, or 'Continue']"""

NO_API_GLOBAL_PLANNER_PROMPT = """You are an expert in GUI interaction and execution-side automation. Always keep the task instruction in mind.

# General Instructions
- GUI and platform-execution guidance are available together in every planner call. Choose the shortest reliable channel for the current state, and combine both channels when the task requires it.
- Reassess the best channel from the current screenshot, execution history, and runtime feedback. Do not continue using a channel merely because the preceding action used it.
- Treat an explicitly requested app, feature, or method as part of the required result. A shortcut or helper tool may improve accuracy, but it does not replace evidence that the requested method was actually used.

# Action Types
## gui_action
Execute pyautogui code against the visible GUI. Use this when the task should be completed through visible interface interactions. Represent it as a bare `pyautogui...` action string.

## wait
Wait for async operations to complete and observe UI changes. Represent it as the exact action string `WAIT`.

## bash_execution
Execute execution-side automation through the `bash_execution` tool. This is a historical tool name. On Linux, output Bash commands or Python scripts. On Windows, output Python code snippets executed in the Windows guest. Use this when file-side editing, inspection, or automation is more reliable than GUI interaction. Follow the platform-specific skill section for paths, commands, and examples. Represent it as a bare command/code action string.

## termination
Output `TERMINATE` according to the active completion mode. Briefly cite the supporting evidence in `thought`.

## infeasible
Declare that the task is objectively impossible to complete. Represent it as the exact action string `INFEASIBLE`.
- Some tasks may be infeasible by design. Use `INFEASIBLE` when required capabilities, variables, or app features are unavailable. Explain the blocker in `thought`.
- Treat explicit app, method, source, target, format, variable, and final-state constraints as required. Do not satisfy a similar task through a workaround and claim completion.
- Verify missing required parameters when possible. Use `INFEASIBLE` when they cannot be obtained.

# Disabled Channels
The api action channel is disabled. Do not output Class.method(...) actions.
"""

NO_API_PLANNER_RESPONSE_FORMAT_PROMPT = """# Response Format
You may think through up to 3 candidate proposals before the final answer, but the executable answer must be only the final JSON object.
List only the strongest plausible candidates. Do not invent weak filler strategies just to reach 3 items.

Use this exact structure:
Candidates:
1. <one-sentence strategy>
[optional] 2. <one-sentence strategy>
[optional] 3. <one-sentence strategy>

Best:
<candidate number>

Why:
<one-sentence selection reason>

```json
{
    "thought": "Brief reasoning about the chosen strategy and current action, grounded in current evidence.",
    "subgoal": "Meaningful phase-level objective for the current stage of work, or 'continue' to keep the current one",
    "actions": [
        "pyautogui.click(695, 514) # click the radio button next to Microsoft Bing",
        "pyautogui.click(663, 807) # click Set as default button"
    ]
}
```

Field guide:
- The final JSON object is the only executable output. Everything before it is optional planning text.
- Output 1 to 3 candidates, not always 3.
- Every candidate must be realistic and worth considering for this exact state.
- If one approach is clearly dominant, output just 1 candidate.
- If you list candidates, keep them short and plain text only. Do not put JSON, code blocks, or extra headings inside candidate text.
- End your response with exactly one final JSON object.
- The final JSON object must contain `thought`, `subgoal`, and `actions`.
- `subgoal`: a phase-level objective for a coherent stage. Use labels such as "Navigate to the target page", "Update the spreadsheet", or "Verify the result". Avoid action labels such as "Open menu", "Click link", "Scroll to inspect", or "Run script".
- Use `continue` while the next action still pursues, verifies, or strengthens evidence for the current subgoal. Start a new subgoal only when the target state changes or the current stage is blocked.
- `actions` must be a non-empty ordered list. The environment changes after each action, so plan them in execution order.
- Prefer one meaningful interaction per action item. Even though some action strings can contain multiple low-level operations, you should usually split sequential interactions into separate `actions` items for clarity and better replanning.
- Each action item should be one of:
  - a bare `pyautogui...` string for GUI actions
  - a bare command/code string for `bash_execution`
  - the string `WAIT` for `wait`
  - the string `TERMINATE` when the active completion target is satisfied
  - the string `INFEASIBLE` only when the task is objectively impossible, with the blocker reason explained in `thought`
- Bash example:
```json
{
  "thought": "Locate the exact workbook before editing it.",
  "subgoal": "Locate the target workbook",
  "actions": [
    "find /home/user -type f -name '*.xlsx' 2>/dev/null | head -20"
  ]
}
```
- Good example:
Candidates:
1. Use a short GUI action sequence to open the search engine menu and set Bing there.

Best:
1

Why:
The relevant setting is visible in the UI and can be changed through direct interaction.

```json
{
  "thought": "Open the visible browser setting and choose Bing through the interface.",
  "subgoal": "Set Bing as the default search engine",
  "actions": [
    "pyautogui.click(695, 514) # click the radio button next to Microsoft Bing",
    "pyautogui.click(663, 807) # click Set as default button"
  ]
}
```

- Termination example:
```json
{
  "thought": "The execution evidence satisfies the active completion target.",
  "subgoal": "Verify task completion",
  "actions": [
    "TERMINATE"
  ]
}
```

- Infeasible example:
```json
{
  "thought": "The requested result cannot be completed because the required app or capability is unavailable in the current environment.",
  "subgoal": "Confirm the blocker",
  "actions": [
    "INFEASIBLE"
  ]
}
```
"""

NO_CP_PLANNER_RESPONSE_FORMAT_PROMPT = """# Response Format
Return exactly one final JSON object and no candidate strategy list.

Use this exact structure:
```json
{
    "thought": "Brief reasoning about the chosen strategy and current action, grounded in current evidence.",
    "subgoal": "Meaningful phase-level objective for the current stage of work, or 'continue' to keep the current one",
    "actions": [
        "pyautogui.click(695, 514) # click the radio button next to Microsoft Bing",
        "pyautogui.click(663, 807) # click Set as default button"
    ]
}
```

Field guide:
- The final JSON object is the only executable output.
- End your response with exactly one final JSON object.
- The final JSON object must contain `thought`, `subgoal`, and `actions`.
- `subgoal`: a phase-level objective for a coherent stage. Use labels such as "Navigate to the target page", "Update the spreadsheet", or "Verify the result". Avoid action labels such as "Open menu", "Click link", "Scroll to inspect", or "Run script".
- Use `continue` while the next action still pursues, verifies, or strengthens evidence for the current subgoal. Start a new subgoal only when the target state changes or the current stage is blocked.
- `actions` must be a non-empty ordered list. The environment changes after each action, so plan them in execution order.
- Prefer one meaningful interaction per action item. Even though some action strings can contain multiple low-level operations, you should usually split sequential interactions into separate `actions` items for clarity and better replanning.
- Each action item should be one of:
  - a bare `pyautogui...` string for GUI actions
  - a bare `Class.method(...)` string for API calls
  - a bare command/code string for `bash_execution`
  - the string `WAIT` for `wait`
  - the string `TERMINATE` when the active completion target is satisfied
  - the string `INFEASIBLE` only when the task is objectively impossible, with the blocker reason explained in `thought`
- Use exactly one API call per action item.
"""

NO_AL_PLANNER_RESPONSE_FORMAT_PROMPT = """# Response Format
You may think through up to 3 candidate proposals before the final answer, but the executable answer must be only the final JSON object.
List only the strongest plausible candidates. Do not invent weak filler strategies just to reach 3 items.

Use this exact structure:
Candidates:
1. <one-sentence strategy>
[optional] 2. <one-sentence strategy>
[optional] 3. <one-sentence strategy>

Best:
<candidate number>

Why:
<one-sentence selection reason>

```json
{
    "thought": "Brief reasoning about the chosen action, grounded in current evidence.",
    "subgoal": "Meaningful phase-level objective for the current stage of work, or 'continue' to keep the current one",
    "action": "pyautogui.click(695, 514) # click the radio button next to Microsoft Bing"
}
```

Field guide:
- The final JSON object is the only executable output.
- Output 1 to 3 candidates, not always 3.
- Every candidate must be realistic and worth considering for this exact state.
- If one approach is clearly dominant, output just 1 candidate.
- If you list candidates, keep them short and plain text only. Do not put JSON, code blocks, or extra headings inside candidate text.
- The final JSON object must contain `thought`, `subgoal`, and `action`.
- `subgoal`: a phase-level objective for a coherent stage. Use labels such as "Navigate to the target page", "Update the spreadsheet", or "Verify the result". Avoid action labels such as "Open menu", "Click link", "Scroll to inspect", or "Run script".
- Use `continue` while the next action still pursues, verifies, or strengthens evidence for the current subgoal. Start a new subgoal only when the target state changes or the current stage is blocked.
- `action` must be one action string. It should be one of:
  - a bare `pyautogui...` string for GUI actions
  - a bare `Class.method(...)` string for API calls
  - a bare command/code string for `bash_execution`
  - the string `WAIT` for `wait`
  - the string `TERMINATE` when the active completion target is satisfied
  - the string `INFEASIBLE` only when the task is objectively impossible, with the blocker reason explained in `thought`
- Use exactly one API call per action item.
- End your response with exactly one final JSON object.
"""

NO_L2S_PLANNER_RESPONSE_FORMAT_PROMPT = """# Response Format
You may think through the next action briefly before the final answer, but the executable answer must be only the final JSON object.

Use this exact structure:
```json
{
    "thought": "Brief reasoning about the chosen action, grounded in current evidence.",
    "action": "pyautogui.click(695, 514) # click the radio button next to Microsoft Bing"
}
```

Field guide:
- The final JSON object is the only executable output.
- The final JSON object has exactly these fields: `thought` and `action`.
- `action` must be one action string. It should be one of:
  - a bare `pyautogui...` string for GUI actions
  - a bare `Class.method(...)` string for API calls
  - a bare command/code string for `bash_execution`
  - the string `WAIT` for `wait`
  - the string `TERMINATE` when the active completion target is satisfied
  - the string `INFEASIBLE` only when the task is objectively impossible, with the blocker reason explained in `thought`
- Use exactly one API call per action item.
- For a shell action, put only the command in `action`. Correct: `"action": "find /home/user -type f | head"`. Incorrect: `"action": "bash_execution(find ...)"` or `"action": "bash_execution: find ..."`.
"""

NO_API_NO_L2S_PLANNER_RESPONSE_FORMAT_PROMPT = """# Response Format
You may think through the next action briefly before the final answer, but the executable answer must be only the final JSON object.

Use this exact structure:
```json
{
    "thought": "Brief reasoning about the chosen action, grounded in current evidence.",
    "action": "pyautogui.click(695, 514) # click the radio button next to Microsoft Bing"
}
```

Field guide:
- The final JSON object is the only executable output.
- The final JSON object has exactly these fields: `thought` and `action`.
- `action` must be one action string. It should be one of:
  - a bare `pyautogui...` string for GUI actions
  - a bare command/code string for `bash_execution`
  - the string `WAIT` for `wait`
  - the string `TERMINATE` when the active completion target is satisfied
  - the string `INFEASIBLE` only when the task is objectively impossible, with the blocker reason explained in `thought`
- For a shell action, put only the command in `action`. Correct: `"action": "find /home/user -type f | head"`. Incorrect: `"action": "bash_execution(find ...)"`, `"action": "bash_execution: find ..."`, or `"action": "bash_execution find ..."`.

- Shell example:
```json
{
  "thought": "Locate the exact workbook before editing it.",
  "action": "find /home/user -type f -name '*.xlsx' 2>/dev/null | head -20"
}
```
"""

FIX_RESPONSE_PROMPT = """Repair the planner response below and preserve the intended plan.

Repair rules:
- Focus on fixing the concrete parse/schema/tool-syntax error shown above.
- If the error points to a specific line, column, or token, fix that exact location.
- Action content must be a bare string, not an object.
- A GUI action must be a valid Python `pyautogui` code string.
- An API action must be exactly one Python call expression such as `GoogleDriveTools.upload_file(...)`.
- A shell action must contain only raw shell/Python code. Remove any leading `bash_execution` wrapper, function syntax, colon, or label.
- Return exactly one repaired response.
- The final output must satisfy this response format exactly:

{response_format_prompt}

Original response:
{response}

Parse traceback:
{error_message}
"""

STEP_ABSTRACTION_PROMPT = """Compare the latest observations and summarize what happened in 1-2 concise sentences.

Task instruction: {task_instruction}
Current subgoal: {current_subgoal}
Action: {action_description}
Runtime feedback: {recovery_hint}

Rules:
- Describe what changed, or say no visible change.
- Mention clear errors if shown.
- Do not judge subgoal status or long-horizon task completion.
- Keep the summary concise and concrete.
- For bash/API output, preserve exact task-relevant identifiers from the output, especially paths, filenames, URLs, IDs, sheet/table/column names, window titles, counts, and selected values.
- Use the task instruction and current subgoal to decide which output details are key. Preserve needed paths and IDs exactly.
"""

NO_L2S_STEP_ABSTRACTION_PROMPT = """Compare the latest observations and summarize what happened in 1-2 concise sentences.

Task instruction: {task_instruction}
Action: {action_description}
Runtime feedback: {recovery_hint}

Rules:
- Describe what changed, or say no visible change.
- Mention clear errors if shown.
- Do not judge long-horizon task completion.
- Keep the summary concise and concrete.
- For bash/API output, preserve exact task-relevant identifiers from the output, especially paths, filenames, URLs, IDs, sheet/table/column names, window titles, counts, and selected values.
- Use the task instruction to decide which output details are key. Preserve needed paths and IDs exactly.
"""

CONTEXT_REFINEMENT_PROMPT = """Analyze task execution progress and provide guidance.

You will receive: a task instruction, execution history range and execution history

Instructions:
- Summarize the full execution history into one unified summary covering the entire range
- List what was done in order (successes and failures)
- **IMPORTANT**: Preserve coordinates in click actions (e.g., "click(500,300)") so the summary records the exact prior interactions
- Identify repeated no-progress behavior, task-relevant progress, or stalled execution.
- Provide actionable suggestions for the next step if there are issues

Return a concise summary string in this format:
Steps X~Y: [ordered list of what was done, keeping coordinates]. Suggestion: [actionable advice, or 'Continue' if progressing well]

Examples:
- Steps 1~5: Opened file, tried to edit (failed 3 times with permission error), attempted sudo (failed). Suggestion: Try a different approach - copy file to temp location first.
- Steps 1~5: Clicked Submit button at click(850,620), typed text, clicked Save at click(920,580). Suggestion: Continue - forms being filled correctly.
- Steps 1~10: Previously installed package and ran script (steps 1~5). Then verified output, tested functionality (steps 6~10). Suggestion: Continue - good progress.
- Steps 1~15: Clicked the same button 5 times with no response, tried alternative buttons (failed). Suggestion: Try an alternative method, or use INFEASIBLE if the task is objectively impossible.
"""

SUBGOAL_TRANSITION_VERIFICATION_PROMPT = """Decide whether to accept the proposed subgoal. Return only PASS or FAIL.

PASS if the current subgoal is complete, the proposal is a task-aligned recovery from a blocked/invalid subgoal, or the proposal merely continues, refines, or restates the same stage. Successful execution of all required actions without an explicit error is sufficient completion evidence. FAIL only when the proposal moves to a genuinely different stage while required actions remain unexecuted, an explicit execution error is unresolved, or required work is skipped."""
