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
| `communication-osk_meeting_agenda_draft` | `MeetingAgenda.odt` |
| `consumption-filter_keys_shopping_list_cart` | `ShoppingList.ods` |
| `consumption-osk_cheapest_polisher` | `Nov2020Catalog_Full.pdf` |
| `consumption-sticky_keys_half_price_body_wash` | `COLNSWMETRO_220726_AQCAZRS1.pdf` |
| `information-osk_clean_touchpad_instructions` | `desk_laptop_ug_en-us.pdf` |
| `service-osk_open_pdf_links` | `ER_How_to_apply_online_final.pdf` |

### 2.2 Live-source tasks

Two tasks have already experienced ground-truth drift:

- `mobility-osk_accessible_grade1_walking_tracks`
- `mobility-osk_nearest_accessible_beach`

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
| `communication-osk_meeting_agenda_draft` | Changed OSK wording to **open**; aligned `gt_steps`; evaluator now checks the complete draft and verifies it was not sent. Instruction made high-level; routine operation steps removed, constraints preserved. Difficulty `medium` → `hard`. |
| `consumption-filter_keys_compare_running_shoes_latest_release` | Added one-unit requirement; recorded the correct latest-release shoe; evaluator now checks SKU, quantity, Black, and size 12. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `consumption-filter_keys_shopping_list_cart` | Reclassified `management` → `consumption`; renamed ID/filename; normalized `related_apps`; evaluator now enforces item quantities and no extra products. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `consumption-osk_cheapest_bathroom_accessory` | Changed OSK wording to **open**; evaluator now enforces quantity 1. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `consumption-osk_cheapest_polisher` | Added exact two-line output requirement; added OSK app; aligned `gt_steps`; enabled exact text evaluation. Instruction made high-level; routine operation steps removed, constraints preserved. Difficulty `easy` → `medium`. |
| `consumption-sticky_keys_half_price_body_wash` | Added one-product-per-line and catalogue-order requirements; enabled exact text evaluation. Instruction made high-level; routine operation steps removed, constraints preserved. Difficulty `medium` → `hard`. |
| `consumption-sticky_keys_wireless_mouse` | Evaluator now enforces quantity 1. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `health-filter_keys_wheelchair_charging_timer` | Instruction made high-level; routine operation steps removed, constraints preserved. |
| `health-insulin_storage_temperature` | Changed evaluator to exact-only text output. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `health-mouse_keys_download_allied_health_form` | Instruction made high-level; routine operation steps removed, constraints preserved. |
| `health-osk_physiotherapy_appointment_mistakes` | Instruction made high-level; routine operation steps removed, constraints preserved. |
| `health-sticky_keys_parkinsons_medication_reminders` | Evaluator now verifies all three reminders recur `DAILY`. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `information-filter_keys_compare_singapore_real_gdp` | Simplified instruction; aligned output filename to `differenceGDP.txt`; enabled exact text evaluation. Difficulty `medium` → `hard`. |
| `information-filter_keys_psychology_coursework_max_upload_size` | Instruction made high-level; routine operation steps removed, constraints preserved. |
| `information-osk-unsw_comp2521_prerequisites` | Corrected task ID to match filename. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `information-osk_clean_touchpad_instructions` | Reclassified to `information`; renamed ID/filename; added OSK app; changed OSK wording to **open**; enabled exact text evaluation. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `information-osk_skill_building_hobbies` | Changed OSK wording to **open**; aligned `gt_steps`; evaluator now requires the exact 11-line output. Instruction made high-level; routine operation steps removed, constraints preserved. Difficulty `medium` → `hard`. |
| `information-osk_world_cup_winners_final_hosts` | Added explicit six-line output order; enabled exact text evaluation; revalidated the 2026 result. Instruction made high-level; routine operation steps removed, constraints preserved. Difficulty `medium` → `hard`. |
| `information-sticky_keys_ucla_economics_premajor_gpa` | Difficulty `easy` → `medium`. |
| `management-filter_keys_calculate_monthly_expenses` | Added expected total `648.49` to `gt_steps`; replaced unsupported spreadsheet evaluation with ODS cell/formula checks. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `management-mouse_keys_meeting_minutes_calendar` | Evaluator now checks the fixed date `2008-08-30`, correct start time, and duration. Instruction made high-level; routine operation steps removed, constraints preserved. Difficulty `easy` → `medium`. |
| `management-osk_update_electricity_bill` | Changed OSK wording to **open**; aligned `gt_steps`; evaluator now checks saved ODS cells. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `management-osk_water_bill_due_date_reminder` | Reclassified `service` → `management`; renamed ID/filename; evaluator now checks fixed date `2024-10-29`. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `management-sticky_keys_student_gradebook` | Added expected averages/grades/order to `gt_steps`; evaluator now checks the completed ODS summary. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `mobility-filter_keys_nearest_passport_office_gwagwalada` | Reclassified `service` → `mobility`; renamed ID/filename. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `mobility-osk_accessible_grade1_walking_tracks` | Updated instruction, `gt_steps`, and evaluator from one track to the current ten matching tracks in exact webpage order. Instruction made high-level; routine operation steps removed, constraints preserved. Difficulty `medium` → `hard`. |
| `mobility-osk_nearest_accessible_beach` | Updated Bondi Beach ground truth; clarified required feature order; enabled exact text evaluation. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `service-mouse_keys_open_voting_links` | Instruction made high-level; routine operation steps removed, constraints preserved. |
| `service-osk_open_pdf_links` | Normalized ID/filename; narrowed instruction to the specific target link checked by the evaluator; added OSK app; aligned `gt_steps`. |
| `service-osk_passport_application_post_office` | Corrected task ID; evaluator now requires exact `Yes` output. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `service-sticky_keys_maximum_investigation_period` | Corrected category `health` → `service`; evaluator now requires exact `90 days` output. Instruction made high-level; routine operation steps removed, constraints preserved. |
