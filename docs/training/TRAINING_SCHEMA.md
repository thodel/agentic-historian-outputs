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
