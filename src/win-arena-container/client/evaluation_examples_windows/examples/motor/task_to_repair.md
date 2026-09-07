# Motor Task Review: Missing Source Assets and Ground-Truth Changes

## 1. Missing Source Assets

The following motor tasks reference local source assets that are not present in the provided repository/archive. These tasks cannot be executed reliably until the original source files are restored.

| Task ID | Missing source asset | Impact |
|---|---|---|
| `communication-osk_meeting_agenda_draft` | `MeetingAgenda.odt` | The task cannot open or inspect the meeting agenda document required to compose the draft email. |
| `consumption-filter_keys_shopping_list_cart` | `ShoppingList.ods` | The task cannot read the product names and quantities that must be added to the shopping cart. |
| `consumption-osk_cheapest_polisher` | `Nov2020Catalog_Full.pdf` | The task cannot inspect the referenced catalog to determine the required product answer. |
| `consumption-sticky_keys_half_price_body_wash` | `COLNSWMETRO_220726_AQCAZRS1.pdf` | The task cannot inspect the referenced catalog/source PDF used to determine the required product information. |
| `information-osk_clean_touchpad_instructions` | `desk_laptop_ug_en-us.pdf` | The task cannot inspect the laptop user guide containing the touchpad-cleaning instructions. |
| `service-osk_open_pdf_links` | `ER_How_to_apply_online_final.pdf` | The task cannot open the application guide PDF or follow the links contained in it. |

---

## 2. Ground-Truth Changes Caused by Live Web Content

Some motor tasks use live websites as their information source. Because these pages are actively maintained, their contents can change after the benchmark is created. A previously correct hard-coded answer can therefore become stale even when the task logic itself has not changed.

### 2.1 `mobility-osk_accessible_grade1_walking_tracks`

**Source:** NSW National Parks access-friendly walking tracks webpage.

The previous ground truth accepted only:

- `Three Sisters walk`

The currently observed page contains ten walking tracks satisfying the task condition: Grade 1 with a maximum listed walking time of 45 minutes or less.

The updated expected output, in webpage order, is:

1. `Fairfax Heritage walking track`
2. `Jennifer Street boardwalk`
3. `Three Sisters walk`
4. `Bungoona lookout and path`
5. `Palm Valley Currenbah walking track`
6. `Victoria Park boardwalk`
7. `Devils Hole lookout walk and picnic area`
8. `Point lookout walking track`
9. `Rainforest walking track`
10. `Whitegum lookout walking track`

The evaluator was updated from a single-track expectation to an exact ten-line output.

**Future drift risk:** High. The result can change again if NSW National Parks adds, removes, renames, or reclassifies tracks, or changes their listed grade/time metadata.

---

### 2.2 `mobility-osk_nearest_accessible_beach`

**Source:** Accessible Beaches NSW directory, Bondi Beach entry.

The previous expected seventh line was:

- `Changing Places facility`

The currently observed Bondi Beach entry instead lists:

- `Retail within 150 metres`

The updated exact expected output is:

1. `Bondi Beach`
2. `Accessible Beach Matting`
3. `Beach Wheelchair availability`
4. `Accessible Bathroom`
5. `Accessible Shower`
6. `Accessible Parking`
7. `Retail within 150 metres`

The task's `gt_steps` and evaluator were updated accordingly.

**Future drift risk:** High. The directory represents maintained accessibility information, so listed facilities/features may be changed by the site operator.

---

## 3. Stability Assessment

These issues illustrate three levels of benchmark stability:

1. **Local static assets**  
   PDF, ODT, ODS, and similar files bundled with the benchmark are the most stable option. Their contents remain fixed as long as the exact source assets are preserved.

2. **Historical facts on live websites**  
   The underlying fact is usually stable, but the URL, page structure, wording, or discoverability can still change.

3. **Current-state data on live websites**  
   Lists, accessibility features, prices, locations, availability, and similar maintained information can change at any time. Hard-coded evaluator answers for these tasks are inherently vulnerable to ground-truth drift.

---

## 4. Recommendation for Long-Term Reproducibility

For benchmark tasks whose answers depend on mutable live webpages, prefer one of the following approaches:

- Save a fixed HTML or PDF snapshot and use that snapshot as the task source.
- Bundle the relevant webpage content as a local benchmark asset.
- Rewrite the task around a historical fact that is unlikely to change.
- If a live webpage must remain the source, periodically revalidate the ground truth and explicitly treat the task as non-static.

For a reproducible WindowsAgentArena benchmark, freezing the source content is preferable to repeatedly updating hard-coded evaluator answers whenever an external website changes.
