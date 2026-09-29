# Training report contract

Each training run is published as
`docs/training/<run_id>/training.json`. A run belongs to the datasets it
consumed and the model it produced; it does not belong to a catalogue document.

The current schema version is `1`.

## Required fields

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | integer | Contract version understood by the publisher. |
| `run_id` | string | Stable, URL-safe run identifier and directory name. |
| `model_id` | string | Identifier of the produced model. |
| `engine` | enum | `kraken`, `trocr`, or `vllm`. |
| `status` | enum | `completed`, `failed`, or `cancelled`. |
| `created_at` | ISO-8601 datetime | Time the run was submitted. |
| `epochs` | integer | Requested number of epochs. |
| `datasets` | array | One or more dataset-provenance records. |

`epochs_trained`, `finished_at`, `params`, `metrics`, `curves`, `base_model`,
and `log` are optional but should be emitted whenever the producer knows them.

## Evaluation context

Whenever `metrics.cer` or `metrics.wer` is reported, `metrics.evaluation_kind`
is required:

| Value | Meaning |
| --- | --- |
| `line_crop` | Scored on individual line images. Segmentation error is **not** in the number. |
| `full_page` | Scored on whole pages through our own segmentation. Segmentation error **is** in the number. |

`metrics.segmentation` (`ground_truth` or `predicted`) says where the line
boxes came from.

These are different measurements and will disagree, often by a lot. `ketos
test` scores line crops cut from ground-truth segmentation; the eval harness
scores a whole page through our own segmentation and so also pays for every
segmentation error. The training integration plan requires the two to stay
visibly distinct, and an unlabelled error rate gets compared anyway — the
overview used to take a single minimum across every completed run, so a 4%
line-crop run and a 19% full-page run of the same model collapsed into
"lowest CER: 4.00%".

Best scores are therefore reported per measurement, never across them, and a
rate with no declared kind is excluded from the best scores and said to be.

## Curve provenance

`curves_provenance` is optional but should always be emitted, because a curve
is not automatically every epoch:

| Field | Type | Meaning |
| --- | --- | --- |
| `complete` | boolean | Whether `curves` holds every trained epoch. |
| `source` | string | Where the points were read from. |
| `note` | string | What was kept and why. Required when `complete` is false. |

kraken keeps only its ten best checkpoints, and the trainer derives the curve
from those filenames because ketos renders progress through `rich` and the
numbers do not survive a redirected stdout (serving-atr-inference#38/#51). Ten
best epochs drawn as a line is a different claim from a training curve, and
which epochs survived is itself the finding: late ones mean the run was still
improving, early ones mean it peaked and then got worse. A report whose record
says nothing here shows the provenance as unknown rather than assuming the
curve is complete.

Separately, the rendered chart reduces long series to a point budget. Reduction
keeps the minimum and maximum of each section, so isolated spikes survive, and
the chart states how many points it drew. Axis bounds always come from the full
series, never from the reduced one.

## Validation rules that surprise producers

These are the rules a record is most often rejected by, and why each exists.

- **No unknown top-level fields.** A record carrying a field this contract does
  not define is refused, not partially read. The trainer writes a *different*
  document under the same filename — `training.json` in a job's store holds
  `job_id`, `points[]`, `complete` and `note` (serving-atr-inference#38) and
  shares no field with this contract. Ignoring unknown keys would let such a
  record validate as an almost-empty run and publish a report with no metrics
  and no curve, which is worse than refusing it. Extending the schema is a
  deliberate change here, not something a producer can do by writing a new key.
- **`schema_version` is required**, not defaulted. A record that does not say
  which contract it was written against cannot be read safely by a later build.
- **`epochs` and `epochs_trained` are whole numbers.** `2.7` is refused rather
  than truncated to an epoch count the trainer never ran.
- **`metrics.cer` and `metrics.wer` must be finite and must not be booleans.**
  In Python `True` is an `int`, so `"cer": true` cleared every range check and
  would have been published as an error rate of 1.0.
- **`run_id` must equal its directory name.** The run id is the published URL.
  This is checked when the published tree is walked, not by the record
  validator, which stays usable on a file sitting anywhere.

## Dataset provenance

Every dataset record requires `hf_repo` in `owner/name` form. It may additionally
carry:

- `revision`: immutable Hub commit or revision identifier;
- `split`: source split used by the run;
- `train_projects` and `eval_projects`: the included project names;
- `pages`, `lines`, and `chars`: retained input counts;
- `pages_skipped`: excluded page count.

The report links to the pinned revision when one is supplied. Runs over multiple
datasets must list every dataset separately.

## Curves

`curves` is an epoch-ordered array. Every entry requires an integer `epoch`,
starting at zero, and can provide finite numeric values for `train_loss`,
`val_loss`, `val_accuracy`, and `lr`.

The site renders these values as accessible inline SVG. The SVG contains a title,
description, labelled axes, and visually distinct series; an HTML table exposes
the exact same values without relying on graphics or JavaScript.

## Reproducibility and model identity

`params` is a JSON object containing the complete hyperparameter snapshot.
`base_model` identifies the starting checkpoint; Hub-style `owner/name` values
and DOIs become links. `log` is preserved as a path, not treated as a public URL.
The report also exposes the run timestamps, engine, epoch counts, schema version,
and a link to the original `training.json`.

## Validation metrics

`metrics.cer` and `metrics.wer` are ratios in `[0, 1]` measured against the
documented evaluation data. They are rendered with the shared
`reference_evaluation` vocabulary:

- unit: CER or WER;
- scope: evaluation corpus;
- reference: the named evaluation project(s);
- version: dataset revision(s);
- normalization: the training normalization parameter, when present;
- comparability: only runs with identical datasets, revisions, evaluation splits,
  and normalization can be compared directly.

Absent values remain absent; the renderer never substitutes zero.
