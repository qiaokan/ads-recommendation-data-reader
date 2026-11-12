# Claude review round 2

Reviewer: Claude Opus 5.5. Text-only review on November 12, 2026.

# Second review: beginner guide to ads and recommendation training data, with glossary

## Publication verdict

**Not approved as-is. Approve after the four minor corrections below; no further full review is needed.**

The revision fixes all eight earlier findings, and I found no remaining substantive technical errors in the probability, sampling, leakage, encoding or label-timing material. The worked numbers check out:

- −ln 0.20 ≈ 1.609 and −ln 0.80 ≈ 0.223.
- 9/23 for the hour.
- A negative weight of 99 for q = 1/99.
- A label finalized at 10:35 for a 30-minute window ending at 10:30, plus a 5-minute log allowance.
- History indices [12, 18, 33, 0, 0] and category indices [2, 2, 3, 0, 0].
- Strict `<` cutoffs that match "stop before that decision."

The remaining blockers are two beginner-critical terms used before or without definition, and two places where the guide breaks its own traceability promise.

### Status of earlier findings

| Earlier finding | Status |
| --- | --- |
| Decision time vs display time | Fixed. One wording slip remains (correction 3). |
| pCTR × pCVR conditioning | Fixed: joint probability, view-through exclusion, double-counting warning. |
| Missing acronym definitions | Mostly fixed. "One-hot" is still undefined (correction 2). |
| Reserved-index consistency | Fixed. Every vocabulary uses 0 for padding, 1 for unknown, and 2 or higher for real values. |
| Point-in-time joins | Fixed: occurred and available times, inclusive/exclusive version intervals. |
| First-use explanation | Mostly fixed. AUC is used before it is defined (correction 1). |
| Padding order | Fixed: latest 5 events, oldest first, padded on the right, which matches the data. |
| Label maturation | Fixed for both clicks and conversions, including the early-positive bias note. |

## Required corrections

### 1. AUC is used before it is defined

The intro promises "Technical terms are explained as they appear," but AUC first appears in the sampling section. It is defined only later, in the metrics table.

- **Quote:** "If negative sampling is independent of features within each class, AUC is unchanged in expectation for fixed scores, but raw log loss and calibration on the sampled data are not population estimates."
- **Replacement:** "If negative sampling is independent of features within each class, AUC (a ranking metric, defined in the metrics table below, that measures how often a random positive scores above a random negative) is unchanged in expectation for fixed scores, but raw log loss and calibration on the sampled data are not population estimates."

### 2. "One-hot" is undefined in both the body and the glossary

The definition of **sparse** depends on "one-hot," in the body and in the glossary entry "Sparse feature." A beginner cannot follow it.

- **Quote:** "**Sparse** conventionally describes categorical features whose full one-hot representation would be mostly zeros; the model usually receives compact indices instead."
- **Replacement:** "**Sparse** conventionally describes categorical features whose full **one-hot** representation would be mostly zeros. A one-hot vector has one position per vocabulary entry: 1 for the observed value and 0 everywhere else. With a million items, that is 999,999 zeros, so the model usually receives the compact index instead."
- **Glossary addition:** `{"term": "One-hot vector", "definition": "A vector with one position per vocabulary entry, set to 1 for the observed value and 0 elsewhere. Models usually receive the equivalent integer index instead."}`

### 3. Leftover "10:00 prediction" undercuts the decision-time fix

Right after establishing that the 10:00 impression was scored at 09:59:58, this sentence calls it a "10:00 prediction."

- **Quote:** "Delayed event arrival also matters: a behavior that occurred at 09:59 but reached your system at 10:02 was unavailable to a real 10:00 prediction."
- **Replacement:** "Delayed event arrival also matters: a behavior that occurred at 09:59:00 but reached your system at 10:02 was unavailable when the 10:00 impression was scored at 09:59:58."

### 4. Device, prediction time and hour cannot be traced to a source

The guide's stated first milestone is to "explain every number in its model input." Three values break that:

- `device: "mobile"` appears in the JSON, but no raw table contains device.
- `prediction_time` appears in the JSON without being linked to `scored_at`.
- The loader paragraph refers to `hour_utc`, which is missing from the starting schema.

**(a) Raw tables.** Rename "**Request timing**" to "**Requests**" and replace its table with:

```text
request_id  scored_at             device
req_10      2026-11-01T09:59:58Z  mobile
```

**(b) Row assembly.**

- **Quote:** "For imp_101, attach the information about U7 and A42, the device and surface from the request, and behavior available before 09:59:58."
- **Replacement:** "For imp_101, attach the information about U7 and A42, the device from the request, the surface from the impression, and behavior available before 09:59:58. The training record stores the request's scored_at as prediction_time."

**(c) Schema table.** Add a row after `surface`:

`| hour_utc | Feature | Hour of prediction_time in UTC, derived by the loader |`

**(d) Loader paragraph.**

- **Quote:** "The loader turns recent_history into history_item_ids and history_category_ids, generates a mask, and puts transformed candidate_price and hour_utc into dense. It maps category strings to indices."
- **Replacement:** "The loader turns recent_history into history_item_ids and history_category_ids, generates a mask, derives hour_utc from prediction_time, and puts transformed candidate_price and hour_utc into dense. It maps each categorical string field (user, item, category, device and surface) to indices."

## Optional refinements

1. **Recall at K wording.** "Fraction of relevant items found among the first K results" can be misread as precision. Suggested: "Of all relevant items, the fraction that appear in the first K results." Apply the same change to the glossary entry.
2. **Binary vs count.** In "It represents all attributed conversions per impression only if…", pCTR × pCVR is a probability of at least one conversion, not a count. Suggested: "It represents the probability of an attributed conversion per impression only if…"
3. **Clicked-only CVR training.** "Training a CVR model only on clicked rows also limits the population it learns from" is vague. Suggested: "A post-click CVR model trains on clicked rows but is scored on impressions whose click is not yet known; this mismatch is called sample selection bias."
4. **Unused glossary term.** "pCTCVR" never appears in the body, and its acronym is not expanded. Either add to the body "This product is sometimes called pCTCVR (predicted click-through conversion rate)," or remove the entry.
5. **Weighted-loss reduction.** "This rescales the update" is exact only within a batch. Dividing by each batch's weight sum changes the relative contribution of batches. A clause noting this would help readers who use large inverse-probability weights such as 99.
6. **Small glossary gaps.** Consider adding:
   - **Shape:** "B × 5 means B rows of 5 entries."
   - **Boolean:** used in the shapes table.
   - **Dot product:** used in "Two-tower model."
   - **Token** and **encoder:** used in the text and images section.
   - Rename "Recurrent state" to "Recurrent model" to match the body.
   - Drop "ISO-style" from the UTC entry, or define it.
7. **Batch first use.** "A model batch often pads lists" comes before "That group is a **batch**." A parenthetical "(a group of examples processed together)" at first use fixes this.
8. **Digit-like mappings.** "The digit-like item mappings below are explicitly chosen" should also cover U7 → 7. Suggested: "The digit-like ID mappings below…"
9. **DIN demo index 0.** In the demo, 0 is a real value for `user` and `gender` but padding for `hist_item`. One sentence would prevent confusion with the worked example's rule that 0 is reserved everywhere.
10. **Situation table.** The intro table's "10 AM UTC" is display time, while `hour_utc` is 9. The later text explains this, but labeling the column "Situation (display time)" would head off a double-take.

## Scope limitations

- **No browsing, per instructions.** I did not verify any external claims:
  - the selected Criteo values and the encoded indices 0, 4 and 96;
  - the DIN demo keys (`seq_length`, `score`) and the `#L11-L30` line range;
  - the arXiv section anchors;
  - the content of the TensorFlow, Google and NVIDIA pages.

  They match my recollection of those sources, but that is not verification.
- I did not render the Mermaid diagram, Markdown tables or links.
- I reviewed technical accuracy and beginner accessibility only. I did not assess legal, privacy or compliance adequacy beyond noting that the guide flags consent and retention.
- Pedagogical judgments, such as which terms count as beginner-critical, are mine and have not been tested with actual readers.