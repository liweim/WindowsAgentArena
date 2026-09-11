# Motor Task Review

## Missing Assets

The following **6 source assets are missing** from `examples/motor/assets`:

| Task ID | Missing asset |
|---|---|
| `communication-meeting_agenda_draft` | `communication-meeting_agenda_draft.odt` |
| `consumption-shopping_list_cart` | `consumption-shopping_list_cart.ods` |
| `consumption-cheapest_polisher` | `consumption-cheapest_polisher.pdf` |
| `consumption-half_price_body_wash` | `consumption-half_price_body_wash.pdf` |
| `information-touchpad_cleaning_instructions` | `information-touchpad_cleaning_instructions.pdf` |
| `service-voter_certificate_link` | `service-voter_certificate_link.pdf` |

These tasks cannot be fully source-validated or executed until the assets are restored.

Two live-web tasks (`mobility-accessible_grade1_walks` and `mobility-nearest_accessible_beach`) have already experienced ground-truth drift; freezing their sources would improve reproducibility.

## Review Summary

Reviewed all **43 motor tasks**. The main changes were:

- Fixed task **category, ID, and filename consistency**, including several reclassified or renamed tasks.
- Simplified instructions and made them more **goal-oriented**, while keeping evaluator-visible constraints such as exact output, order, quantity, options, filenames, dates, and recurrence.
- Normalized `related_apps` and added or removed applications where necessary.
- Updated `gt_steps` and corrected stale live-web ground truth where needed.
- Strengthened evaluators for exact text output, ODS cells/formulas, shopping-cart quantities/options, Thunderbird drafts, and calendar date/recurrence checks.
- Re-evaluated difficulty for all tasks. Final distribution: **easy 14 / medium 15 / hard 14**.
