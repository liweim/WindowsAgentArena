# Visual Task Review

## Missing Assets

The following **1 source asset is missing** from `examples/visual/assets`:

| Task ID | Missing asset |
|---|---|
| `management-utility_bill_summary` | `management-utility_bill_summary.ods` |

The evaluator expects sheet `Bill Summary` with the three bill rows in `B4:D6`, so the restored template should preserve that layout.

## Review Summary

Reviewed all **40 visual tasks**. The main changes were:

- Kept task categories unchanged and fixed **ID, filename, and configuration consistency** where needed.
- Normalized `related_apps`, especially Windows Narrator and other canonical app IDs.
- Simplified instructions and made affected tasks more **goal-oriented**, while preserving exact evaluator-visible requirements.
- Fixed local resource/configuration issues, including asset paths, Chrome remote-debugging arguments, and the misspelled Thunderbird delivery-task ID/filename.
- Corrected the Windows Magnifier task so `access-windows_magnifier_200` consistently targets **200%** rather than 300%.
- Strengthened evaluators for Magnifier state, cart quantities, exact Notepad output, image alt text, ODS cells, and Thunderbird Calendar fields such as date/time/location/reminder/all-day/description.
- Extended the Thunderbird calendar metric with optional location, reminder, and all-day checks.
- Re-evaluated difficulty for all tasks. Final distribution: **easy 21 / medium 12 / hard 7**.
