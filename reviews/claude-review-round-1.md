# Claude review round 1

Reviewer: Claude Opus 5.5 via Claude Code. Reviewed on November 12, 2026. Text-only review; no independent source or browser verification.

# Review: *A beginner guide to training data for ads and recommendations*

## Verdict

**Strong draft that needs targeted fixes before publication.** The structure works well for beginners. It separates raw logs, records, and tensors, keeps metadata, features, and labels distinct, and repeatedly stresses time boundaries. All the arithmetic I checked is correct (see the table below).

Five problems still need fixing:

1. **The feature cutoff is the wrong timestamp.** The worked example uses the display time, but the guide's own rule says the cutoff is the scoring decision.
2. **The pCTR × post-click pCVR claim is stated more broadly than it holds.**
3. **The worked encodings break the guide's own reserved-index convention,** and one encoding is never stated.
4. **The example tables cannot enforce the point-in-time rules the guide prescribes.**
5. **Core acronyms (CTR, pCTR, CVR, CPC, DIN) are never expanded,** even though the guide promises no prior knowledge.

**Scope.** I reviewed only the text provided. I did not browse, run code, or open any linked source. Wherever I compare the guide to Criteo, DIN, DeepCTR-Torch, TensorFlow, or Google material, the comparison comes from my recollection, is marked *(unverified)*, and should be confirmed against the source.

---

## Arithmetic and consistency checks that pass

| Check | Result |
|---|---|
| BCE for p=0.20, y=1 | −ln(0.20) = 1.6094 ✓ |
| BCE for p=0.20, y=0 | −ln(0.80) = 0.2231 ✓ (natural log assumed; see M6) |
| Base click rate | 1,000 / 100,000 = 1% ✓ |
| Sampled rate | 1,000 / 2,000 = 50% ✓ |
| Negative retention q and weight | q = 1,000/99,000 = 1/99, so weight = 99 ✓. Weighted total: 1,000 + 99 × 1,000 = 100,000, which restores 1% ✓ |
| Price scaling | 80 / 100 = 0.80 ✓ |
| Hour scaling | 10 / 23 ≈ 0.435 ✓ |
| History alignment | A12→12/shoes→2, A18→18/shoes→2, A33→33/books→3. Items `[12,18,33,0,0]` and categories `[2,2,3,0,0]` are aligned ✓ |
| Mask/length | 3 valid entries, mask `[1,1,1,0,0]`, length 3 ✓ |
| Shapes | `dense` is B×2, history is B×5, `y` is B×1 ✓ |
| Click label | Click at 10:00:05 falls inside the 30-min window, so `imp_101`=1. `imp_102` has no click, so 0 ✓ |
| Leakage example | The 10:00:05 click is correctly excluded from the history used to predict it ✓ |
| Double-counting warning | pCTR × impression-level pCVR is indeed wrong ✓ |

---

## Prioritized findings

### High

#### H1. The feature cutoff uses display time, not decision time

> `"prediction_time": "2026-11-01T10:00:00Z"`

> "For `imp_101`, attach the information about U7 and A42, the device and surface from the request, and U7's behavior before 10:00."

> "Features must represent information the scoring system could have used at its decision time."

The guide sets `prediction_time` equal to `shown_at`. In real systems, scoring happens at request time, before rendering. In feeds, an impression is often logged only when the item scrolls into view, which can be seconds or minutes later. Any event between scoring and display is then admitted into the features, which is exactly the leakage the guide warns against.

The mermaid node "Behavior before each impression" repeats the same conflation.

**Proposed wording**

> For this example, the request `req_10` was scored at 10:00:00 and both items were displayed at 10:00:00. In real systems these times can differ: an item may be scored at 09:59:58 and logged as shown only when it scrolls into view. **Features use the scoring time as their cutoff; the label window starts at the impression time.** Store both:
>
> ```text
> request_id  scored_at              impression_id  shown_at
> req_10      2026-11-01T10:00:00Z   imp_101        2026-11-01T10:00:00Z
> ```

Then apply these related changes:

- Rename the mermaid node to "Behavior before each scoring decision".
- Add `scored_at` to the starter schema.
- Define `prediction_time` as "the time the scoring system made its decision".

#### H2. The pCTR × post-click pCVR claim needs its conditions stated

> "Under matching attribution definitions, multiplying pCTR by post-click pCVR estimates conversion probability per impression."

The chain rule gives P(click ∧ conv | x) = P(click | x) · P(conv | click, x). That product equals the per-impression conversion probability only under three conditions:

1. **Click-only attribution.** Conversions are counted only when attributed to a click. If view-through or no-click conversions count, the product underestimates P(conv | impression).
2. **Same click definition.** The CVR model's training population must use the same click definition as the CTR label: same window, same deduplication, same invalid-click filtering.
3. **Same features.** Both models condition on the same impression features x.

There is also a practical problem. A post-click CVR model is trained only on clicked impressions. Serving it on every impression extrapolates to a population it never saw. This is known as sample selection bias, and multi-task designs such as ESMM address it.

"Matching attribution definitions" is too vague for a beginner to apply.

**Proposed wording**

> A post-click CVR model estimates P(conversion | click, impression features). Multiplying it by pCTR gives P(click **and** click-attributed conversion | impression), sometimes called pCTCVR. This equals the impression-level conversion probability only when conversions count solely through clicks (no view-through attribution) and both models share the same click definition and features. Because a post-click CVR model is trained only on clicked rows but applied to every candidate, its estimates can be biased for impressions unlike those that were clicked. Multi-task approaches that train on all impressions are one response.

#### H3. The worked encodings violate the guide's own reserved indices

> `PAD -> 0` / `UNKNOWN -> 1`

> "Assume these invented encodings: U7 becomes user index 7; A42 becomes item index 42; mobile becomes device index 1; shoes and books use category indices 2 and 3."

> `"surface": [1],`

There are three problems:

- **Device clashes with UNKNOWN.** The guide's only illustrated convention reserves 1 for UNKNOWN, so `mobile → 1` reads as "unknown device".
- **Surface is never stated.** `home_feed → 1` is never declared, so a reader tracing every number (the guide's own "first milestone") cannot do it.
- **Items can clash with reserved indices.** The digit-preserving item mapping means an item `A1` would collide with UNKNOWN, and an item `A0` would collide with PAD.

The guide also never says whether user, device, and surface vocabularies reserve PAD at all. They do not need a PAD index, because they are never padded. The DIN demo reflects this, using user 0 and gender 0 as real values *(unverified)*. A beginner will not infer this.

**Proposed wording**

> Assume these invented encodings. Every vocabulary reserves 0 for padding and 1 for unknown, so real values start at 2:
>
> | Feature | Mapping used here |
> |---|---|
> | user | U7 → 7 |
> | item (candidate and history share this vocabulary) | A12 → 12, A18 → 18, A33 → 33, A42 → 42; real catalogs would not keep original digits, and no real item may use 0 or 1 |
> | device | mobile → 2 |
> | surface | home_feed → 2 |
> | category | shoes → 2, books → 3 |
>
> Vocabularies for features that are never padded may skip the PAD slot; document whichever convention you choose.

Update `x` accordingly: `"device": [2]` and `"surface": [2]`.

#### H4. The example tables cannot enforce the time rules the guide prescribes

> "**Item information available at the time**" (table with only `item_id category price`)

> "Delayed event arrival also matters: a behavior that occurred at 09:59 but reached your system at 10:02 was unavailable to a real 10:00 prediction."

The guide states two time rules: avoid using the noon price, and exclude late-arriving events. Its own tables lack the columns needed to apply either one:

- The item table has no validity interval.
- The behavior table has `occurred_at` but no arrival time.

A beginner who builds the tables as shown will silently violate the rules.

**Proposed wording**

Extend the tables:

```text
item_id  category  price   valid_from            valid_to
A42      shoes     80.00   2026-10-20T00:00:00Z  2026-11-01T12:00:00Z
A42      shoes     65.00   2026-11-01T12:00:00Z  (open)

user_id  item_id  category  action  occurred_at           available_at
U7       A12      shoes     view    2026-11-01T09:40:00Z  2026-11-01T09:40:02Z
```

Then add this rule:

> A history event is eligible when `available_at < scored_at`. Pick the item row whose `[valid_from, valid_to)` interval contains `scored_at`. This is called a point-in-time join.

Also document whether "before" is strict (`<`) or inclusive (`≤`) for events stamped exactly at the cutoff.

#### H5. The beginner prerequisite claim is unmet and core acronyms are never expanded

> "You need no prior knowledge of recommendation systems."

The following terms are used but never expanded or defined:

- **Acronyms:** CTR (first appears as "a basic CTR model"), pCTR, CVR, pCVR, CPC, DIN, AUC, NDCG.
- **DIN before introduction:** "DIN uses the candidate to weight historical behaviors" appears two sections before DIN is introduced.
- **ML concepts:** neural network, loss, parameters, binary cross-entropy (no formula), concatenate, two-tower, causal sequence training, and recurrent state.

Readers also need conditional probability and logarithms to follow the pCVR and BCE passages.

**Proposed wording** (replace the sentence)

> You need no prior knowledge of recommendation systems. It helps to know basic probability, including conditional probability ("the chance of A given B"), what a logarithm is, and the idea that a neural network has adjustable numbers (parameters) that training changes to reduce an error score (the loss). Acronyms are expanded on first use and collected in the glossary.

Also make these changes:

- Expand on first use: "CTR (click-through rate: clicks ÷ impressions)", "pCTR (predicted CTR)", "CVR (conversion rate)", "CPC (cost per click)", "DIN (Deep Interest Network, a model from Alibaba)".
- In the history section, write "the DIN model, described later," or move the sentence.

### Medium

#### M1. Probability interpretation needs calibration, and the guide omits the sampling effect on evaluation

> "A predicted probability of 0.03 means a predicted 3% chance of a click for that opportunity."

This holds only for a calibrated model trained on, or corrected to, the live distribution. "Calibrated" first appears in the retrieval section and is defined only in the metrics table.

Missing points:

- **Metric invariance.** Negative downsampling leaves AUC unchanged in expectation, but it distorts log loss and calibration.
- **Evaluation data.** Evaluation should use unsampled data or apply the sampling weights.
- **Prior correction.** Weighting is not the only fix. For a model trained on negatives retained with probability q, the standard correction is p = p′ / (p′ + (1 − p′)/q). With q = 1/99, a sampled-model prediction of 0.5 maps to 0.5 / (0.5 + 0.5·99) = 1%.

The ads section's "pCTR × bid" scoring also depends on calibration, unlike ranking by pCTR alone, where only order matters. That link is worth stating.

**Proposed wording**

> Interpreted literally, 0.03 means "about 3 of every 100 similar opportunities get a click." That interpretation holds only if the model is **calibrated** on live traffic (defined in the metrics section). Training on sampled data or a different population can break it.

Add to the sampling section:

> Evaluate on unsampled data, or apply the same weights during evaluation. Ranking metrics such as AUC are largely unaffected by negative downsampling, but log loss and calibration are not. Instead of weighting, you can correct predictions afterward: with negatives kept at rate q, p_live = p / (p + (1 − p)/q). For q = 1/99, a sampled prediction of 0.5 corresponds to 1% in live traffic.

Add to the ads section:

> Because pCTR × bid compares probabilities across ads, it requires calibrated pCTR; ranking by pCTR alone needs only the correct order.

#### M2. The text implies DIN is order-sensitive

> "A simple sum or average discards ordering. DIN uses the candidate to weight historical behaviors; sequence models may additionally encode positions, times, or recurrent state."

"Additionally" implies DIN already captures order. As I recall the original DIN *(unverified)*, it uses candidate-dependent weighted pooling, which is also order-insensitive. Reordering the history does not change its output unless position or time features are added.

**Proposed wording**

> A simple sum or average discards ordering. DIN weights each historical behavior by its relevance to the candidate, but its weighted sum is still order-insensitive unless position or time features are added. Sequence models encode order explicitly through positions, timestamps, or recurrent state.

#### M3. A shared vocabulary alone does not give a consistent representation

> "A candidate item and an item in the user's history often share an item vocabulary so that the same item has a consistent representation."

Consistent representation requires a shared **embedding table** as well. Two tables indexed by the same vocabulary learn unrelated vectors.

**Proposed wording**

> A candidate item and an item in the user's history often share both an item vocabulary and an embedding table, so the same item maps to the same index and the same learned vector in both places.

#### M4. History order and padding side are never documented

> "For a first implementation, retain the latest L events in a documented order."

The worked example never documents its order. Its data is oldest-first (09:40, 09:50, 09:55) and right-padded. Some sequence models expect left padding or most-recent-first order, and truncation (keeping the latest L) interacts with both choices.

**Proposed wording** (after the padded example)

> Here events are ordered oldest-first and padded on the right. After truncation to the latest L=5 events, position 0 holds the oldest retained event. Record order, padding side, L, and the truncation rule in the data dictionary; the same rule must apply in training and serving.

#### M5. The Criteo excerpt contradicts itself and conflicts with the guide's own advice

> "The original row has all 39 features; this excerpt omits the rest."

> "replaces missing values, label-encodes categorical fields independently, and scales numerical columns."

- **"Has all 39 features" conflicts with `"I1": None`.** The row has all 39 *columns*, some of them empty.
- **The script conflates missing and zero.** As I recall, it fills missing numerical values with 0 and missing categorical values with `"-1"` *(unverified)*. Filling with 0 contradicts the guide's own advice that "Missing and zero are different facts." Readers should see that tension called out.
- **LabelEncoder reserves no slots.** It starts indices at 0 with no PAD or UNKNOWN slot. Combined with fitting on the whole file, this means unseen categories cannot occur in the demo but would fail at serving time.
- **The encoded indices are fragile.** The stated indices (0, 4, 96) depend on sorted unique strings across the entire 200-row file, *including the `"-1"` fill token*, which sorts before hex digits. Unverified.

**Proposed wording**

> The original row has 39 feature columns, some of them empty; this excerpt shows a few.
>
> The script fills missing numerical values with a default and missing categorical values with a placeholder string, label-encodes each categorical column on the full file, and scales numerical columns. Two choices are convenient for a demo but differ from this guide's advice. First, filling missing numbers with 0 merges "missing" with "zero"; consider adding a missing indicator. Second, the label encoder reserves no padding or unknown index, so a category unseen during fitting would have no valid index at serving time. The specific indices (0, 4, 96) depend on every value in the file, including the fill token, and are not stable across datasets.

#### M6. BCE has no formula or log base

> "Suppose it predicts 0.20 and the label is 1. Binary cross-entropy gives a loss of approximately 1.609."

The numbers are correct only with the natural log. A reader using log₂ gets 2.32.

**Proposed wording**

> Binary cross-entropy for one example is −[y·ln(p) + (1 − y)·ln(1 − p)], using the natural logarithm. With p = 0.20 and y = 1, the loss is −ln(0.20) ≈ 1.609. With y = 0, it is −ln(0.80) ≈ 0.223. Confident wrong predictions are penalized far more than confident right ones. "Log loss" is the same quantity averaged over examples.

#### M7. Label windows lack an anchor and maturity depends on log arrival

> "For an invented seven-day conversion target, a record collected one hour after an impression cannot yet be confidently labeled “no conversion.”"

> "For this example, assume a 30-minute click window and complete observation through 10:30."

- **No anchor for the conversion window.** It is unclear whether seven days are measured from the impression or the click, which matters for H2.
- **Click logs arrive late too.** "Complete observation through 10:30" assumes click logs have fully arrived by then. `label_finalized_at` should be the window end plus the expected click-log delay.
- **Positives and negatives mature differently.** A positive can be known as soon as the click arrives, but a negative is known only after the window and arrival delay.

**Proposed wording**

> For an invented seven-day post-click conversion target (measured from the click time), …
>
> A click window ending at 10:30 is complete only once click logs for that period have fully arrived; set `label_finalized_at` to the window end plus that arrival delay. A positive can be confirmed as soon as its click arrives, but a negative is known only after finalization.

#### M8. Real versus synthetic labels need sharper caveats

> "## Criteo provides real anonymized rows"

> "This is synthetic demonstration data from a third-party library, not an Alibaba production record. The history has three valid entries and one padding position."

- **Criteo.** The labels are real logged outcomes. To my recollection *(unverified)*, though, the public Criteo display-advertising dataset was subsampled at different rates for positives and negatives. If so, its click rate (roughly 25% in commonly reported figures) is far above live CTR, a direct instance of this guide's sampling section. The 200-row sample is also hosted by DeepCTR-Torch, not Criteo, and I cannot confirm its provenance from the text alone.
- **DIN demo.** In the first toy row, the candidate `item: [1]` also appears in `hist_item: [[1, 2, 3, 0]]`, according to the guide's own excerpt. That is fine in synthetic data. Beginners should still learn that a candidate in its own history is legitimate only when it reflects a genuinely earlier interaction, never the event being predicted.
- **Label shape varies by library.** The DIN demo uses `y = [1]`, shape B and integer, while the guide uses B×1 float. Note that shapes and dtypes vary by library.

**Proposed wording**

Retitle the section "Criteo: real but anonymized and sampled rows". Then add:

> The labels are real logged outcomes, but public CTR datasets are commonly subsampled, so their click rate need not match live traffic. Check the dataset's documentation before interpreting predicted probabilities. The sample file is distributed with DeepCTR-Torch.
>
> In this toy row, the candidate item 1 also appears in its own history. In real data that is acceptable only when the history entry is a genuinely earlier interaction.
>
> Libraries differ on label shape (B versus B×1) and type; match what your loss function expects.

#### M9. Retrieval negatives omit popularity bias

> "Some training methods use other examples' positive items as **in-batch negatives**."

In-batch negatives oversample popular items, because popular items appear more often as other examples' positives. Common methods correct for this, for example by subtracting log sampling probability (logQ correction). The guide notes false negatives but not this bias.

**Proposed wording** (append)

> Because popular items appear more often as other examples' positives, in-batch negatives over-represent them; many implementations apply a sampling-probability correction.

### Low

| # | Passage | Issue | Fix |
|---|---|---|---|
| L1 | `category_id`, `item_id`, `recent_item_ids` (schema) vs. `candidate_category`, `candidate_item_id`, `recent_history` (JSON) vs. `history_item_ids` (x) | Three naming schemes for the same fields confuse beginners tracing one row | Use one name set throughout, or add a mapping note |
| L2 | `Valid-entry mask: [1, 1, 1, 0, 0]` vs. `[[True, True, True, False, False]]` | Integer vs. boolean | Say "1/0 or True/False, depending on the framework" |
| L3 | "Mobile home feed at 10 AM"; `"hour_utc": 10` | The timezone of "10 AM" is unstated. Local hour often matters more than UTC. Dividing by 23 treats 23:00 and 00:00 as far apart | State UTC in the first table and mention local time and cyclic or categorical hour encoding as options |
| L4 | `"I2": 3,` vs. `"I3": 260.0,` | Mixed int/float display, although pandas loads both as float because of NaNs | Note that the display mirrors file text, or show both as floats |
| L5 | "Model tensors" (representation table) | "Tensor" is used long before it is defined. "Epoch" is defined but never used | Add a forward reference. Drop "epoch" or use it |
| L6 | "The file extension does not determine what the model learns." | True logically, but CSV can alter values (empty string vs. null, lost leading zeros, IDs parsed as numbers) | Append: "…provided the loader preserves types; CSV in particular can turn empty fields, leading zeros, or ID strings into different values." |
| L7 | `clicked_at` table (one row per impression) | There is no rule for multiple clicks per impression or for invalid or fraudulent clicks | Say: "`clicked=1` if at least one valid click falls in the window" |
| L8 | Retrieval invented example, `"sampled_other_items"` | "Positive" and "negative" are used earlier ("`imp_101` positive") but never defined | Define them at the first use in the 30-minute window paragraph |
| L9 | DIN feature example rendered as lists | As I recall *(unverified)*, the paper writes behavior IDs as a set, `{Bag, Book}` | Say "reformatted; the paper writes the visited categories as a set" |
| L10 | Whole guide | No note on privacy, consent, or retention for user-level logs | Add one sentence pointing readers to their organization's data policies |
| L11 | `loss = mean(weight * loss_per_example)` | Some frameworks normalize by the sum of weights. The choice changes the effective learning rate, not the optimum | Optional note |

---

## Glossary of missing or late-defined terms

| Term | Suggested definition |
|---|---|
| **CTR** | Click-through rate: clicks ÷ impressions. |
| **pCTR / pCVR** | Predicted CTR / predicted conversion rate (model outputs). |
| **CVR** | Conversion rate. State the denominator (clicks or impressions). |
| **Conversion** | A valuable downstream action, such as a purchase or sign-up, credited to an ad by an attribution rule. |
| **Attribution** | The rule deciding which impression or click gets credit for a later event, including its time window. |
| **View-through conversion** | A conversion credited to an impression without a click. |
| **pCTCVR** | P(click and conversion \| impression) = pCTR × post-click pCVR under click-only attribution. |
| **CPC** | Cost per click: the advertiser pays when a click occurs. |
| **Bid** | The amount an advertiser offers per billable event, distinct from product price. |
| **Positive / negative example** | A row with label 1 / label 0 under the stated rule. |
| **Scoring time / decision time** | When the model produced its score. This is the feature cutoff. |
| **Point-in-time join** | Joining each row to the version of data valid at its cutoff. |
| **Serving / live prediction** | Running the model on real requests. |
| **Calibration** | Predicted probabilities match observed frequencies. |
| **Binary cross-entropy / log loss** | −[y ln p + (1−y) ln(1−p)], averaged over examples. |
| **Loss** | A number measuring prediction error, which training minimizes. |
| **Parameters** | Numbers the model learns, including embeddings. |
| **Neural network** | A model built from layers of weighted sums and nonlinear functions. |
| **Concatenate** | Join vectors end to end into one longer vector. |
| **Dense / sparse features** | Numerical floats / categorical IDs. Appears as the field name `dense`. |
| **Mask** | An array marking which positions or labels are valid. |
| **Positive-class sampling rate q** | The probability a row is kept in training data. |
| **Inverse-probability weighting** | Weighting each kept row by 1/q to restore the original distribution. |
| **Prior correction** | Adjusting predictions afterward to undo sampling. |
| **DIN** | Deep Interest Network: weights a user's past behaviors by relevance to the candidate. |
| **Two-tower model** | Separate networks produce user and item vectors, and their compatibility (often a dot product) is the score. |
| **Causal sequence training** | Each position predicts its next item using only earlier positions. |
| **Recurrent state** | A running summary updated item by item in RNN-style models. |
| **Label encoding** | Mapping each distinct string to an integer, as in Criteo's LabelEncoder. |
| **AUC** | Area under the ROC curve: the probability that a random positive scores above a random negative. |
| **Recall@K / NDCG@K** | Share of relevant items in the top K / position-discounted ranking quality, normalized to 1. |
| **Position bias, selection bias, feedback loop** | Outcomes shaped by where items were shown, which items were shown, and the past model's choices. |
| **Online experiment (A/B test)** | Randomly assigning live traffic to old and new systems to compare them. |
| **Parquet** | A columnar file format that supports typed and list-valued columns. |
| **Embedding table** | Defined in the guide; note it can be shared across features (M3). |
| **UTC / ISO 8601** | Explain the `Z` suffix in the timestamps. |

---

## Remaining limitations

- **No external verification.** I did not check any of the following:
  - the Criteo row values;
  - the encoded indices 0/4/96;
  - DeepCTR-Torch script behavior and the `#L11-L30` line anchor;
  - DIN section numbers and the example's wording;
  - TensorFlow tutorial contents;
  - Google pages;
  - the Criteo dataset's subsampling.
  
  Statements marked *(unverified)* are recollections and should be confirmed against the sources.
- **Links may be stale.** URLs and anchors may have moved; I did not test them.
- **Nothing was executed.** I did not run the Python snippets, render the mermaid diagram, or reproduce the preprocessing.
- **Out of scope.** I did not assess advanced topics the guide reasonably omits: auction mechanics beyond CPC, delayed-feedback models, counterfactual or off-policy evaluation, debiasing methods, and streaming or online training.
- **Proposed numbers are invented.** Proposed wording keeps the guide's invented examples. New figures, such as the 09:59:58 scoring time and the price validity rows, are also invented and should be labeled as such if adopted.