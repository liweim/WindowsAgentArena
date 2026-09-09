# WindowsAgentArena Accessibility Tasks — 8-task review batch

This batch adds two non-CAPTCHA tasks to each user group.

| Group | Task ID | Category | Core scenario | Deterministic evaluator |
|---|---|---|---|---|
| cognitive | `mobility-paratransit_pickup_checklist` | mobility | Turn a dense paratransit confirmation into a compact Sticky Note memory aid | Sticky Notes content points |
| cognitive | `communication-volunteer_shift_reply` | communication | Integrate availability constraints with three shift options, choose the only valid/latest shift, draft email | Thunderbird draft content |
| hearing | `communication-dental_reschedule_voicemail` | communication | Chrome Live Caption on fixed audio, choose earlier appointment, draft email | Thunderbird draft + Chrome Live Caption state |
| hearing | `service-interpreter_request_audio` | service | Windows Live Captions on fixed service audio, capture form/lead time/phone/code | Live Captions process + exact `answer.txt` |
| motor | `information-bookmark_accessibility_reference` | information | Use Mouse Keys while saving a stable local Wikipedia reference to bookmark bar | Mouse Keys state + Chrome bookmarks |
| motor | `service-accessible_transport_request` | service | Use On-Screen Keyboard to complete a structured accessible-transport request | OSK process + exact `answer.txt` |
| visual | `service-accessible_parking_renewal_notice` | service | Use Magnifier to read a small-print permit-renewal image and capture key details | Magnifier process + exact `answer.txt` |
| visual | `communication-community_event_rsvp` | communication | Use Narrator to read an HTML invitation and draft an RSVP with an accommodation request | Narrator process + Thunderbird draft |

## `gt_steps` convention

- `gt_steps` now contains only direct executable actions and explicit standard answers/target states.
- No reasoning trace is included (for example, no "reject option A/C", comparison narrative, or hidden decision process).
- For text files and email drafts, the standard output content is given directly so the expected result is unambiguous.

## Counts after this batch

- cognitive: 35 (target 50; 15 remaining after this batch)
- hearing: 43 (target 50; 7 remaining)
- motor: 45 (target 50; 5 remaining)
- visual: 42 (target 50; 8 remaining)

## Validation performed

- Parsed every JSON file successfully.
- Confirmed `id` matches filename and category prefix.
- Confirmed no new task uses category `captcha`.
- Confirmed all referenced local assets exist.
- Confirmed every new evaluator function/result getter name is exported by the repository evaluator API.
- Fixed synthetic hearing audio is ~21 s and ~23 s; transcript source text is included both beside the audio asset and in task JSON.
- Full runtime execution inside the Windows VM was not performed in this environment.
