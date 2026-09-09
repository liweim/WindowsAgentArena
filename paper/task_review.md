# WindowsAgentArena Task Modification Checklist

## Rules

### 1. Category

* Category labels must always use the **lowercase** values defined in the README:

  * `communication`

  * `information`

  * `management`

  * `mobility`

  * `consumption`

  * `service`

  * `health`

  * `access`

  * `setup`

  * `captcha`

* Determine the category based on the task's **primary user goal or workflow**, rather than categorizing it solely by the source website, output application, or disability group.

* Use `access` when the primary goal of the task is to install, enable, or configure an accessibility or access-support feature itself.

* Treat `captcha` as a separate stress-test slice.

* When changing a category, you must update all of the following:

  1. Update the JSON `category`;

  2. Update the filename prefix;

  3. Update the `id`;

  4. Confirm that `id == filename without .json`;

  5. Search the repository for any references to the old id or filename.

### 2. `id` and Filename

Check the following for every task:

* [ ] `id` exactly matches the JSON filename without `.json`.

* [ ] The filename prefix exactly matches the `category`.

* [ ] There are no duplicate `id` values.

* [ ] There are no duplicate files that differ only by letter case.

* [ ] After renaming a file, add the old file to `DELETED_FILES.txt`. Do not simply add the new file while keeping the old one.

### 3. `related_apps`

* Only include applications that the Agent **actually needs to interact with** while completing the task.

* Use existing canonical app identifiers from the repository, such as `chrome`, `msedge`, `settings`, `thunderbird`, `notepad`, `sticky_notes`, `libreoffice_writer`, `libreoffice_calc`, etc.

* Do not include setup-only components, background services, or apps unrelated to the actual execution path.

* If multiple apps represent mutually exclusive optional paths, do not include all of them simply because they "might be used." Prefer alignment with the expected successful trajectory.

* If the task still needs to be reworked, first record the `related_apps` risk, and update it together with the instruction and `gt_steps` once the task objective is stable.

Checklist:

* [ ] All apps explicitly required by the instruction are included in `related_apps`.

* [ ] All apps actually used in `gt_steps` are included in `related_apps`.

* [ ] Components used only for environment setup in the config, but not operated by the Agent, are not incorrectly included.

* [ ] The target app required by the evaluator does not conflict with `related_apps`.

* [ ] There are no duplicate app labels or multiple aliases for the same app.

### 4. Instruction

Use a consistent style with **concise, direct imperative phrasing**.

* Start with direct verbs such as `Install`, `Set`, `Create`, `Find`, `Add`, `Write`, `Update`, `Copy`, or `Complete`.

* Do not use polite lead-ins such as `Could you...`, `Can you...`, `Please...`, `I need you to...`, or `I'd like you to...`.

* Do not write the instruction like an operations manual. Let the Agent reason about routine steps such as menu paths, button sequences, and window switching.

* Preserve constraints that cannot be safely inferred, such as exact filenames, titles, dates, recipients, target values, or restrictions such as not sending a message or not restarting the system.

* Explicitly require an accessibility feature only when the feature itself is part of the task requirement or when the evaluator checks it.

### 5. `gt_steps`

* `gt_steps` are intended for annotators, and should allow them to reproduce the successful trajectory by following concrete UI/file operations.

* Each step should contain only one major **executable action**.

* A canonical answer may appear in `gt_steps` only when it is the exact value used by that action, for example: `Type WAT-4821 into the Booking reference field`, `Create the event on July 20, 2026`, or `Set the title to Refill medication`.

* Do **not** create standalone answer-key steps such as `Standard answer — pickup window: 8:20 AM-8:35 AM`, `The correct answer is ...`, or `Read X as Y`. Extracted facts, intermediate conclusions, comparison results, and reasoning are not actions and should not appear as separate `gt_steps`.

* Do **not** describe the reasoning used to reach a choice. Avoid steps that compare candidates, eliminate options, explain why a choice is correct, or summarize information from the source. Put only the resulting value into the UI action that actually uses it.

* If the task requires reading source material before acting, it is fine to include the executable action that opens or navigates to the source. Do not add a separate step whose only purpose is to state what was learned from it.

* Do not duplicate environment-preparation steps from `config` in `gt_steps`.

* CAPTCHA tasks do not need detailed steps or fixed seed answers. Keep them concise.

* For tasks that themselves require restructuring, do not normalize the old `gt_steps` yet. Rewrite them together once the new task definition is finalized.

### 6. Evaluator

* The evaluator must cover all explicitly required and verifiable final success conditions in the instruction.

* If the instruction explicitly requires a particular accessibility tool state and an existing evaluator can check it, include that check.

* For fixed absolute dates, do not use evaluators based on relative dates that depend on the VM's current date.

* If the instruction requires exact wording, do not replace the full-text requirement with a check for only a short keyword.

* When multiple independent success conditions must all be satisfied, use the appropriate conjunction.

* The evaluator should not check only a small subset of the required fields in a way that allows obviously incomplete results to pass.

## Recommended Execution Order for the Next Round

1. Strictly parse all JSON files in the target directory first.

2. Generate a summary table for every task containing `filename / id / category / related_apps / instruction / evaluator`.

3. First check consistency among category, filename, and id.

4. Then check whether `related_apps` matches the applications actually used by the instruction / gt_steps / evaluator.

5. Then check instruction style.

6. For tasks that are neither CAPTCHA tasks nor pending restructuring, check that every `gt_steps` item is an executable action and that any canonical answer appears only as the value used by that action, never as a standalone answer-key or reasoning step.

7. Check evaluator consistency with the instruction.

8. Re-parse all JSON files and check for duplicate ids and case-only duplicate filenames.

9. The final ZIP must **contain only the files actually modified in the current round**. Do not accumulate and repackage changes that were already delivered in previous rounds. Include `DELETED_FILES.txt` only when files were deleted or renamed in the current round.
