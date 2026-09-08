# Visual Task Review

## Overall Changes

- Reviewed all 40 JSON tasks in `examples/visual` against `paper/task_review.md`.
- Kept all task categories unchanged; every category prefix, filename, and `id` is consistent after the fixes, with no duplicate IDs or case-only duplicate filenames.
- Normalized `related_apps` to canonical app IDs and made Windows Narrator explicit wherever the evaluator requires Narrator.
- Rewrote affected instructions into concise imperative form and added exact canonical answers to `gt_steps` where needed. In the latest pass, 9 instructions were further raised to a goal-oriented level by removing routine navigation/app-switching steps while preserving boundary conditions and evaluator-visible constraints.
- Fixed local-resource/config problems: the keto shopping-note path, the Australia map path, a malformed Chrome remote-debugging argument, and the misspelled Thunderbird delivery-task filename/ID.
- Tightened evaluators so they cover the stated final state: Windows Magnifier 200%, exact cart quantities, exact Notepad output files, complete invitation alt text, ODS cells, and Thunderbird Calendar date/time/location/reminder/all-day/description checks.
- Extended the existing Thunderbird calendar metric with optional `location`, `reminder_minutes_before`, and `all_day` checks. Existing rules remain backward-compatible.
- The only canonical target/answer correction in the cumulative review is `access-windows_magnifier_200`: the task previously said/evaluated 300% even though its ID/filename specified 200%; it now consistently targets 200%.
- CAPTCHA tasks required no changes.
- Difficulty was re-evaluated across all 40 visual tasks; final distribution: **easy 21 / medium 12 / hard 7**. `mobility-nearest_pharmacy_unsw_library` changed from `easy` to `medium`.

## Manual Action Still Required

- `management-utility_bill_summary`: restore the missing source asset `examples/visual/assets/BillSummary.ods`. The evaluator expects sheet `Bill Summary` with the three bill rows in `B4:D6`; verify the restored template uses that layout. This is the only remaining missing local asset found in the visual directory.

## Change Log

| Task | Changes |
|---|---|
| `access-chrome_zoom_150` | Simplified instruction; replaced `human` source with the concrete page URL. |
| `access-high_contrast_aquatic_7news` | Rephrased the contrast-theme instruction; made sources concrete. |
| `access-windows_color_filter_grayscale_inverted` | Added canonical `settings` app; simplified instruction/source. |
| `access-windows_color_filter_protanopia` | Added canonical `settings` app; simplified instruction/source. |
| `access-windows_font_size_140` | Added canonical `settings` app; simplified instruction/source. |
| `access-windows_magnifier_200` | Corrected target from 300% to 200%; changed snapshot/app from Chrome to Windows Magnifier; replaced the Chrome zoom evaluator with Magnifier-open + registry 200% checks. |
| `access-windows_magnifier_open` | Canonicalized app to `magnifier`; simplified instruction and `gt_steps`. |
| `access-windows_narrator_open` | Fixed `basic_setup` typo to `base_setup`; canonicalized app to `narrator`; simplified instruction and `gt_steps`. |
| `communication-add_contact` | Instruction made high-level; routine operation steps removed, constraints preserved. |
| `consumption-toothbrush_price_comparison` | Made Narrator explicit/canonical; concrete local source; evaluator now requires exactly one unit of the correct product. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `consumption-lavender_coupon` | Made Narrator explicit/canonical; concrete local source; evaluator now requires exactly one unit. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `consumption-saute_pan` | Made Narrator explicit/canonical; concrete local source; evaluator now requires exactly one unit. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `consumption-keto_bread` | Made Narrator explicit/canonical; corrected the missing HTML asset reference to `assets/consumption-find_keto_bread_product.html`. |
| `consumption-marshmallow_bunnies` | Made Narrator explicit/canonical; concrete local source; evaluator now requires exactly one unit. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `consumption-swingset_price_filter` | Removed stale self-hosted comment; corrected source to Smyths Toys; rewrote instruction/`gt_steps`; added canonical `narrator` app. |
| `desktop_env/evaluators/metrics/thunderbird.py` | Added optional Thunderbird Calendar checks for location, reminder offset, all-day flag, and `description_points` compatibility. |
| `information-metal_density_comparison` | Fixed Kiwix URLs; added `notepad`; made Narrator explicit; required `answer.txt`; evaluator now checks exact two-line output `Gold\n19.3`. |
| `information-second_gold_rush` | Made Narrator explicit/canonical; added the unique answer `Carolina Gold Rush` to `gt_steps`; concrete Kiwix source. |
| `information-apple_q3_operating_margin` | Added `notepad`; concrete local PDF source; exact answer recorded in `gt_steps`; evaluator now requires exact `31.30%` in `answer.txt`. |
| `information-wikipedia_image_person` | Fixed `--remote-debugging-port=1337`; made Narrator explicit/canonical; concrete Kiwix source. |
| `information-town_southeast_of_brisbane` | Corrected asset path from `Australia_Map.pdf` to `Australia-Map.pdf`; added `notepad`; required `answer.txt`; evaluator now checks exact `Gold Coast`. |
| `information-cat_image_alt_text` | Rewrote instruction/`gt_steps`; replaced malformed external source with the local DOCX source. |
| `information-invitation_image_alt_text` | Rewrote instruction/`gt_steps`; replaced malformed source; fixed evaluator typo `costal` → `coastal`; strengthened the address check. |
| `management-cardiology_appointment_reminder` | Removed the optional Word path; changed calendar result to the supported Thunderbird getter; evaluator now checks absolute date/time, full location, and one-day reminder. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `management-utility_bill_summary` | Replaced invalid `pdf_viewer` alias with canonical `msedge`; replaced nonexistent `check_sheet` with `check_ods_cell_values`; corrected expected rule format. Source asset still needs manual restoration. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `management-weekly_planner_calendar` | Replaced `windows_settings` with canonical `settings`; replaced nonexistent plural calendar metric and raw SQLite file result with six supported Thunderbird event checks covering date/time/duration/location. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `management-package_delivery_calendar` | Renamed from misspelled `management-hunderbird_calendar_delivery_calendar`; removed tracking-number answer leakage from instruction; switched to supported Thunderbird getter; evaluator checks title/date/all-day state/description. Instruction made high-level; routine operation steps removed, constraints preserved. |
| `mobility-nearest_pharmacy_unsw_library` | Made Narrator explicit/canonical; recorded `Pharmacy at UNSW` as the unique expected answer in `gt_steps`; source set to Google Maps. Difficulty `easy` → `medium`. |
| `mobility-walking_route_opera_house` | Made Narrator explicit/canonical; source set to Google Maps. |
| `mobility-transit_route_grand_central_to_liberty` | Made Narrator explicit/canonical; source set to Google Maps. |

## Final Validation

- All 40 visual JSON files parse successfully.
- `id == filename without .json` for every task.
- Filename prefix matches `category` for every task.
- No duplicate IDs or case-only duplicate filenames were found.
- All evaluator metric/getter names used by visual tasks resolve to registered repository names.
- Modified Thunderbird evaluator code passes Python syntax compilation and synthetic checks for cardiology reminder/location, delivery all-day/description, and weekly-planner location rules.
- All referenced local assets exist except `assets/BillSummary.ods` noted above.
- Difficulty distribution after the latest pass: easy 21, medium 12, hard 7.
- The old misspelled delivery-task path is recorded in `DELETED_FILES.txt`.
