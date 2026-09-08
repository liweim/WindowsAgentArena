# Motor Task Review

## 1. Overall Changes

Reviewed all 43 tasks in `examples/motor` against `paper/task_review.md`.

The changes mainly cover:

- **Category / ID / filename**
  - Corrected misclassified tasks.
  - Made every task ID match its filename.
  - Made filename prefixes consistent with `category`.
  - Recorded renamed files that must be removed.

- **Instruction**
  - Reworded OSK requirements from ambiguous “enabled” to verifiable “open”.
  - Added missing exact-output, ordering, quantity, option, and file-name constraints.
  - Rewrote 28 instructions to a higher-level, goal-oriented form: routine menu paths, search/click sequences, and app-switching steps are left for the Agent to infer, while boundary conditions and evaluator-visible constraints are preserved.

- **`related_apps`**
  - Added missing applications.
  - Removed unnecessary apps.
  - Replaced inconsistent aliases with canonical app names.

- **`gt_steps` / ground truth**
  - Added concrete expected values where needed.
  - Updated two live-web answers that had changed.
  - Aligned `gt_steps` with the instruction and evaluator.

- **Evaluator**
  - Added exact text-file comparison.
  - Added ODS cell/formula checks.
  - Added shopping-cart quantity and option checks.
  - Added Thunderbird “draft but not sent” checking.
  - Added fixed-date and recurrence checks for calendar tasks.

- **Final validation**
  - 43/43 JSON files parse successfully.
  - No ID/filename mismatches.
  - No category/filename-prefix mismatches.
  - No duplicate IDs or case-only duplicate files.
  - No missing evaluator functions/getters referenced by the motor tasks.
  - Re-evaluated `difficulty` for all 43 tasks; final distribution: **easy 14 / medium 15 / hard 14**. Nine task labels changed.

**Status:** all issues that can be checked from the current task/evaluator files have been fixed. The only remaining blockers are the missing source assets listed below.

---

## 2. Manual Actions Still Required

### 2.1 Restore missing source assets

These six tasks cannot be fully source-validated or executed until the original files are restored:

| Task ID | Missing asset |
|---|---|
| `communication-meeting_agenda_draft` | `MeetingAgenda.odt` |
| `consumption-shopping_list_cart` | `ShoppingList.ods` |
| `consumption-cheapest_polisher` | `Nov2020Catalog_Full.pdf` |
| `consumption-half_price_body_wash` | `COLNSWMETRO_220726_AQCAZRS1.pdf` |
| `information-touchpad_cleaning_instructions` | `desk_laptop_ug_en-us.pdf` |
| `service-voter_certificate_link` | `ER_How_to_apply_online_final.pdf` |

### 2.2 Live-source tasks

Two tasks have already experienced ground-truth drift:

- `mobility-accessible_grade1_walks`
- `mobility-nearest_accessible_beach`

For long-term reproducibility, freezing these web sources is preferable.

---

## 3. Task Change Log

| Task ID | Changes |
|---|---|
| `access-enable_clicklock` | Simplified instruction to a direct command; removed unnecessary `control_panel` from `related_apps`. |
| `access-enable_filter_keys` | Simplified instruction to a direct command. |
| `access-enable_mouse_keys` | Simplified instruction to a direct command. |
| `access-enable_on_screen_keyboard` | Simplified instruction; changed requirement to keep OSK **open**; added `settings`; aligned `gt_steps`. |
| `access-enable_sticky_keys` | Simplified instruction to a direct command. |
| `access-set_primary_mouse_button_right` | Simplified instruction to a direct command. |
| `communication-meeting_agenda_draft` | Changed OSK wording to **open**; aligned `gt_steps`; evaluator now checks the complete draft and verifies it was not sent. Instruction made high-level; routine operation steps removed, constraints preserved. Difficulty `medium` → `hard`. |
| `consumption-running_shoe_release_comparison` | Added one-unit requirement; recorded the correct latest-release shoe; evaluator now checks SKU, quantity, Black, and size 12. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `consumption-shopping_list_cart` | Reclassified `management` → `consumption`; renamed ID/filename; normalized `related_apps`; evaluator now enforces item quantities and no extra products. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `consumption-cheapest_bathroom_accessory` | Changed OSK wording to **open**; evaluator now enforces quantity 1. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `consumption-cheapest_polisher` | Added exact two-line output requirement; added OSK app; aligned `gt_steps`; enabled exact text evaluation. Instruction made high-level; routine operation steps removed, constraints preserved. Difficulty `easy` → `medium`. |
| `consumption-half_price_body_wash` | Added one-product-per-line and catalogue-order requirements; enabled exact text evaluation. Instruction made high-level; routine operation steps removed, constraints preserved. Difficulty `medium` → `hard`. |
| `consumption-wireless_mouse_search_result` | Evaluator now enforces quantity 1. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `health-wheelchair_charging_timer` | Instruction made high-level; routine operation steps removed, constraints preserved. |
| `health-insulin_storage_temperature` | Changed evaluator to exact-only text output. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `health-allied_health_form_download` | Instruction made high-level; routine operation steps removed, constraints preserved. |
| `health-physiotherapy_appointment_checklist` | Instruction made high-level; routine operation steps removed, constraints preserved. |
| `health-parkinsons_medication_reminders` | Evaluator now verifies all three reminders recur `DAILY`. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `information-singapore_real_gdp_comparison` | Simplified instruction; aligned output filename to `differenceGDP.txt`; enabled exact text evaluation. Difficulty `medium` → `hard`. |
| `information-psychology_coursework_upload_limit` | Instruction made high-level; routine operation steps removed, constraints preserved. |
| `information-unsw_comp2521_prerequisites` | Corrected task ID to match filename. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `information-touchpad_cleaning_instructions` | Reclassified to `information`; renamed ID/filename; added OSK app; changed OSK wording to **open**; enabled exact text evaluation. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `information-skill_building_hobbies` | Changed OSK wording to **open**; aligned `gt_steps`; evaluator now requires the exact 11-line output. Instruction made high-level; routine operation steps removed, constraints preserved. Difficulty `medium` → `hard`. |
| `information-world_cup_winners_hosts` | Added explicit six-line output order; enabled exact text evaluation; revalidated the 2026 result. Instruction made high-level; routine operation steps removed, constraints preserved. Difficulty `medium` → `hard`. |
| `information-ucla_economics_premajor_gpa` | Difficulty `easy` → `medium`. |
| `management-monthly_expenses_total` | Added expected total `648.49` to `gt_steps`; replaced unsupported spreadsheet evaluation with ODS cell/formula checks. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `management-next_meeting_calendar` | Evaluator now checks the fixed date `2008-08-30`, correct start time, and duration. Instruction made high-level; routine operation steps removed, constraints preserved. Difficulty `easy` → `medium`. |
| `management-electricity_bill_payment` | Changed OSK wording to **open**; aligned `gt_steps`; evaluator now checks saved ODS cells. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `management-water_bill_reminder` | Reclassified `service` → `management`; renamed ID/filename; evaluator now checks fixed date `2024-10-29`. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `management-student_gradebook` | Added expected averages/grades/order to `gt_steps`; evaluator now checks the completed ODS summary. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `mobility-nearest_passport_office_gwagwalada` | Reclassified `service` → `mobility`; renamed ID/filename. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `mobility-accessible_grade1_walks` | Updated instruction, `gt_steps`, and evaluator from one track to the current ten matching tracks in exact webpage order. Instruction made high-level; routine operation steps removed, constraints preserved. Difficulty `medium` → `hard`. |
| `mobility-nearest_accessible_beach` | Updated Bondi Beach ground truth; clarified required feature order; enabled exact text evaluation. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `service-voting_comment_links` | Instruction made high-level; routine operation steps removed, constraints preserved. |
| `service-voter_certificate_link` | Normalized ID/filename; narrowed instruction to the specific target link checked by the evaluator; added OSK app; aligned `gt_steps`. |
| `service-passport_application_post_office` | Corrected task ID; evaluator now requires exact `Yes` output. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `service-bank_investigation_period` | Corrected category `health` → `service`; evaluator now requires exact `90 days` output. Instruction made high-level; routine operation steps removed, constraints preserved. |
