# Data Manifests

[English](README.md)

이 디렉터리는 SkillOpt paper split용 lightweight split manifest를 배포합니다. 이 manifest들은 곧바로 실행 가능한 전체 benchmark payload가 아닙니다. benchmark를 평가하려면 필요할 때 raw data source에서 전체 example을 materialize한 뒤, 아래에 적힌 split directory를 `--split_dir`로 지정하세요.

이 README에서 "coverage"는 manifest가 upstream benchmark의 어느 부분을 참조하는지를 뜻합니다. release된 manifest directory가 실행 가능한 전체 example을 포함한다는 뜻이 아닙니다.

## Layout

release된 모든 manifest directory는 같은 file layout을 사용합니다.

```text
data/<benchmark>_<manifest_type>/
|-- split_manifest.json
|-- train/items.json
|-- val/items.json
`-- test/items.json
```

`split_manifest.json`은 source metadata, split counts, item fields를 기록합니다. 각 `items.json`은 stable ID 또는 source-path hint만 포함합니다.

## Released Splits

| Manifest directory | Benchmark | Counts | Coverage | Raw data source | `split_dir` |
|---|---|---:|---|---|---|
| `searchqa_id_split/` | SearchQA | 400 / 200 / 1400 | Official HF dataset IDs | [lucadiliello/searchqa](https://huggingface.co/datasets/lucadiliello/searchqa) | `data/searchqa_split` |
| `livemathematicianbench_id_split/` | LiveMathematicianBench | 35 / 18 / 124 | Four official monthly files | [LiveMathematicianBench/LiveMathematicianBench](https://huggingface.co/datasets/LiveMathematicianBench/LiveMathematicianBench) | `data/livemathematicianbench_split` |
| `docvqa_id_split/` | DocVQA | 107 / 53 / 374 | 10% subset of validation | [lmms-lab/DocVQA](https://huggingface.co/datasets/lmms-lab/DocVQA) | `data/docvqa/splits` |
| `officeqa_id_split/` | OfficeQA | 50 / 24 / 172 | OfficeQA Full | [databricks/officeqa](https://huggingface.co/datasets/databricks/officeqa) | `data/officeqa_split` |
| `spreadsheetbench_id_split/` | SpreadsheetBench | 80 / 40 / 280 | SpreadsheetBench Verified 400 | [KAKA22/SpreadsheetBench](https://huggingface.co/datasets/KAKA22/SpreadsheetBench) | `data/spreadsheetbench_split` |
| `alfworld_path_split/` | ALFWorld | 39 / 18 / 134 | ALFWorld `json_2.1.1` paths | [alfworld/alfworld](https://github.com/alfworld/alfworld) | `data/alfworld_path_split` |

Counts는 train / val / test 순서입니다.

## Direct Use

이 release에서 `alfworld_path_split/`만 `--split_dir`로 직접 사용할 수 있습니다. ALFWorld loader가 split item의 `gamefile`과 `task_type`을 읽기 때문입니다.

그렇다고 ALFWorld raw data가 포함되어 있다는 뜻은 아닙니다. 여전히 `alfworld-download`로 ALFWorld를 별도로 내려받고, `json_2.1.1`을 포함하는 data root를 `$ALFWORLD_DATA`로 설정해야 합니다.

다른 manifest directory들은 lookup manifest입니다. 질문, 답, context, image, task instruction 같은 전체 example field를 의도적으로 생략합니다. SkillOpt를 실행하기 전에 위 표의 `split_dir` path로 해당 benchmark를 materialize하세요.

## Lookup Keys

raw data를 다운로드했거나 사용할 수 있게 만든 뒤에는 manifest만으로 해당 raw example을 찾을 수 있습니다.

| Benchmark | Manifest lookup key |
|---|---|
| SearchQA | `items.json[].id`를 `lucadiliello/searchqa`의 `key` field와 매칭합니다. |
| LiveMathematicianBench | `source_file`을 열고 `no`를 매칭합니다. manifest `id`는 `<month>:<no>`입니다. |
| DocVQA | official DocVQA `validation` split 안에서 `questionId`를 매칭합니다. `image_path`는 예상 local image path를 기록합니다. |
| OfficeQA | `officeqa_full.csv`의 `uid`를 매칭합니다. `source_files`와 `source_docs`는 supporting document를 식별합니다. |
| SpreadsheetBench | `id`를 매칭합니다. `spreadsheet_path`는 참조 spreadsheet directory를 식별합니다. |
| ALFWorld | `$ALFWORLD_DATA` 기준 상대 경로로 `gamefile`을 resolve합니다. |

## Manifest Item Examples

SearchQA:

```json
{
  "id": "221c83e6630f4e7983da48fa28da1882"
}
```

LiveMathematicianBench:

```json
{
  "id": "202602:22",
  "month": "202602",
  "no": 22,
  "paper_link": "http://arxiv.org/abs/2602.10700v1",
  "source_file": "data/202602/qa_202602_final.json"
}
```

DocVQA:

```json
{
  "id": "50877",
  "questionId": "50877",
  "docId": "14724",
  "image_path": "data/docvqa_images/q50877_d14724.png",
  "source_split": "validation"
}
```

OfficeQA:

```json
{
  "id": "UID0002",
  "uid": "UID0002",
  "category": "easy",
  "source_files": "treasury_bulletin_1944_01.txt"
}
```

SpreadsheetBench:

```json
{
  "id": "32438",
  "spreadsheet_path": "spreadsheet/32438",
  "instruction_type": "Cell-Level Manipulation"
}
```

ALFWorld:

```json
{
  "id": "train:0000",
  "gamefile": "json_2.1.1/train/.../game.tw-pddl",
  "task_type": "look_at_obj_in_light"
}
```

## Benchmark Notes

### SearchQA

`searchqa_id_split/`은 ID-only manifest입니다. release된 각 `id`는 `lucadiliello/searchqa`의 `key` field와 정확히 일치합니다.

materialized example은 SearchQA environment가 소비하는 field를 포함해야 합니다.

```text
question
context
answers
```

### LiveMathematicianBench

`livemathematicianbench_id_split/`은 다음 raw files에서 생성되었습니다.

```text
data/202511/qa_202511_final.json
data/202512/qa_202512_final.json
data/202601/qa_202601_final.json
data/202602/qa_202602_final.json
```

manifest는 loader format으로 ID를 저장합니다.

```text
<month>:<no>
```

materialized example은 다음 field를 포함해야 합니다.

```text
question
choices
correct_choice
theorem_type
theorem
sketch
paper_link
```

### DocVQA

`docvqa_id_split/`은 official DocVQA `validation` split에서 sample한 10% subset인 `docvqa_validation_10pct`를 기록합니다.

```text
source_split: validation
docvqa_validation_10pct: train=107, val=53, test=374
```

각 manifest item은 question/document ID와 image location metadata를 포함합니다. materialized example은 `question`, `answer` 또는 `ground_truth`, 그리고 locally resolve되는 `image_path`를 제공해야 합니다.

### OfficeQA

`officeqa_id_split/`은 OfficeQA Full(`officeqa_full.csv`)의 split을 기록합니다. official OfficeQA CSV는 Hugging Face에서 gated 상태이므로 materialization에는 authorized access가 필요합니다.

각 manifest item은 `uid`, `category`, `source_files`, `source_docs` hint를 포함합니다. materialized example은 `question`과 `ground_truth` 또는 `answer`를 포함해야 합니다.

### SpreadsheetBench

`spreadsheetbench_id_split/`은 `spreadsheetbench_verified_400.tar.gz`의 SpreadsheetBench Verified 400 split을 기록합니다.

각 manifest item은 `id`, `spreadsheet_path`, `instruction_type` 같은 task identity metadata를 포함합니다. materialization은 참조되는 spreadsheet directory도 다음 위치에 배치해야 합니다.

```text
data/spreadsheetbench_verified_400
```

### ALFWorld

`alfworld_path_split/`은 `$ALFWORLD_DATA` 기준 상대 `gamefile` path를 기록합니다. source payload는 `json_2.1.1`이며, `alfworld-download`로 별도 다운로드해야 합니다.
