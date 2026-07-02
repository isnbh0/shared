# SkillOpt: Self-Evolving Agent Skills를 위한 Executive Strategy

[English](README.md)

> 이 문서는 vendored snapshot 안에 보관된 upstream SkillOpt README의 한국어 번역입니다.
> local fork metadata와 backend delta는 [`PINNED_UPSTREAM.ko.md`](PINNED_UPSTREAM.ko.md)에,
> 실행 가능한 wrapper 문서는 [`../../README.ko.md`](../../README.ko.md)에 있습니다.

*신경망을 학습하듯 agent skill을 학습합니다. epoch, (mini-)batchsize, learning rate, validation gate를 사용하지만 model weight는 건드리지 않습니다.*

[![Project Page](https://img.shields.io/badge/Project%20Page-SkillOpt-8dbb3c)](https://microsoft.github.io/SkillOpt/) [![Paper](https://img.shields.io/badge/Paper-arXiv-b31b1b)](https://arxiv.org/abs/2605.23904) [![Project Video](https://img.shields.io/badge/Project%20Video-Watch%20Demo-ff0000)](https://youtu.be/JUBMDTCiM0M) [![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

현대 agent skill은 보통 사람이 직접 작성하거나, 강한 LLM이 한 번 생성하거나, 느슨하게 통제된 self-revision으로 발전시킵니다. 이런 방식은 skill 자체를 deep-learning optimizer처럼 다루지 못하고, feedback 아래에서 시작점보다 안정적으로 좋아진다고 보장하기 어렵습니다.

**SkillOpt는 skill document를 frozen agent의 trainable state로 취급**하고, weight-space optimization의 재현성을 만드는 규율로 학습합니다. 별도의 optimizer model이 scored rollout을 하나의 skill document에 대한 bounded add / delete / replace edit으로 바꿉니다. candidate edit은 held-out validation score를 엄격히 개선할 때만 accepted 됩니다. textual learning-rate budget, rejected-edit buffer, epoch-wise slow / meta update가 skill training을 안정화하며, deployment 시 **추가 inference-time model call은 0개**입니다.

배포 artifact는 compact한 `best_skill.md`입니다(보통 300–2,000 tokens). 이 artifact는 변경되지 않은 target model 위에서 실행됩니다. SkillOpt는 **six benchmarks, seven target models, three execution harnesses**(direct chat, Codex CLI, Claude Code CLI)에서 평가되었고, **all 52 evaluated (model, benchmark, harness) cells**에서 best 또는 tied-best입니다. GPT-5.5 기준 평균 no-skill accuracy lift는 direct chat에서 **+23.5 points**, Codex agentic loop에서 **+24.8**, Claude Code에서 **+19.1**입니다. optimized skill artifact는 model scale, Codex와 Claude Code harness, 인접 benchmark 사이에서도 추가 최적화 없이 transfer됩니다.

전체 method, ablation, per-cell results는 [paper](https://arxiv.org/abs/2605.23904)를 참고하세요. loop의 시각적 walkthrough는 [project page](https://microsoft.github.io/SkillOpt/)에 있습니다. upstream `docs/` directory는 이 trimmed vendor snapshot에 포함되어 있지 않습니다.

## Demo Video

https://github.com/user-attachments/assets/eb12d3bc-371c-467f-904d-91b61f339ed7

<p align="center">
  <a href="https://youtu.be/JUBMDTCiM0M"><b>전체 demo를 YouTube에서 보기</b></a>
</p>

---

## Install

### Requirements

- Python 3.10+

```bash
git clone https://github.com/microsoft/SkillOpt.git
cd SkillOpt
pip install -e .

# ALFWorld benchmark용(optional):
pip install -e ".[alfworld]"
alfworld-download
```

### API Credentials 설정

```bash
cp .env.example .env
# .env에 API credentials를 넣은 뒤:
source .env
```

#### Azure OpenAI *(recommended)*

```bash
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
# Option 1: API key auth
export AZURE_OPENAI_API_KEY="your-key"
# Option 2: Azure CLI auth (API key 불필요)
export AZURE_OPENAI_AUTH_MODE="azure_cli"
```

> **Note:** `AZURE_OPENAI_ENDPOINT`는 세 mode(`api_key`, `azure_cli`, `openai_compatible`) 모두에서 필요합니다. 없으면 모든 LLM call이 실패합니다.

#### OpenAI-compatible endpoints

```bash
export AZURE_OPENAI_ENDPOINT="https://api.openai.com/v1"
export AZURE_OPENAI_API_KEY="sk-..."
export AZURE_OPENAI_AUTH_MODE="openai_compatible"
```

이 설정은 모든 call을 plain OpenAI Python client로 라우팅합니다(Azure auth 없음, `api-version` header 없음).

> **Note:** SkillOpt는 이 mode에서도 `AZURE_OPENAI_*` env var 이름을 재사용합니다. 별도의 `OPENAI_API_KEY` knob는 없습니다.

#### Anthropic Claude

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

#### Qwen *(local vLLM)*

```bash
export QWEN_CHAT_BASE_URL="http://localhost:8000/v1"
export QWEN_CHAT_MODEL="Qwen/Qwen3.5-4B"
```

`qwen_chat`은 optimizer backend로도 사용할 수 있습니다. optimizer와 target이 서로 다른 local vLLM service를 가리켜야 하면 role-specific setting을 사용합니다.

```bash
python scripts/train.py \
    --config configs/searchqa/default.yaml \
    --optimizer_backend qwen_chat \
    --target_backend qwen_chat \
    --optimizer_model Qwen/Qwen3.5-4B \
    --target_model Qwen/Qwen3.5-4B \
    --optimizer_qwen_chat_base_url http://localhost:8001/v1 \
    --target_qwen_chat_base_url http://localhost:8000/v1
```

#### MiniMax

```bash
export MINIMAX_BASE_URL="https://api.minimax.io/v1"
export MINIMAX_API_KEY="..."
export MINIMAX_MODEL="MiniMax-M2.7"
```

---

## Quick Start

### Training

```bash
# Minimal example: SearchQA 학습
python scripts/train.py \
    --config configs/searchqa/default.yaml \
    --split_dir /path/to/your/searchqa_split \
    --azure_openai_endpoint https://your-resource.openai.azure.com/ \
    --optimizer_model gpt-5.5 \
    --target_model gpt-5.5

# LiveMathematicianBench 학습
python scripts/train.py \
    --config configs/livemathematicianbench/default.yaml \
    --split_dir /path/to/your/livemath_split \
    --azure_openai_endpoint https://your-resource.openai.azure.com/ \
    --optimizer_model gpt-5.5 \
    --target_model gpt-5.5

# ALFWorld 학습
python scripts/train.py \
    --config configs/alfworld/default.yaml \
    --split_dir data/alfworld_path_split \
    --azure_openai_endpoint https://your-resource.openai.azure.com/ \
    --optimizer_model gpt-5.5 \
    --target_model gpt-5.5
```

주요 CLI arguments:

| Argument | Description | Example |
|---|---|---|
| `--config` | Benchmark config YAML | `configs/searchqa/default.yaml` |
| `--split_dir` | Data split directory path | `/path/to/split` |
| `--azure_openai_endpoint` | Azure OpenAI endpoint URL | `https://your-resource.openai.azure.com/` |
| `--optimizer_model` | Optimizer model deployment name | `gpt-5.5` |
| `--target_model` | Target model deployment name | `gpt-5.5` |
| `--num_epochs` | Training epochs 수 | `4` |
| `--batch_size` | Step당 batch size | `40` |
| `--workers` | Parallel rollout workers | `8` |
| `--out_root` | Output directory | `outputs/my_run` |

### Eval Only

학습 없이 특정 data split에서 trained skill을 평가합니다.

```bash
# packaged GPT-5.5 SearchQA skill을 test split에서 평가:
python scripts/eval_only.py \
  --config configs/searchqa/default.yaml \
  --skill ckpt/searchqa/gpt5.5_skill.md \
  --split valid_unseen \
  --split_dir /path/to/searchqa_split \
  --azure_openai_endpoint https://your-resource.openai.azure.com/

# 모든 split(train + val + test)에서 평가:
python scripts/eval_only.py \
  --config configs/searchqa/default.yaml \
  --skill ckpt/searchqa/gpt5.5_skill.md \
  --split all \
  --split_dir /path/to/searchqa_split \
  --azure_openai_endpoint https://your-resource.openai.azure.com/
```

자체 training run이 만든 skill을 평가하려면 `--skill`을 해당 run의 best-skill path로 바꿉니다. 예: `outputs/my_run/best_skill.md`.

| Split | Description |
|---|---|
| `valid_unseen` | Test set |
| `valid_seen` | Validation set |
| `train` | Training set |
| `all` | 모든 split combined(default) |

### Output Structure

각 training run은 structured output directory를 씁니다.

```text
outputs/<run_name>/
├── config.json              # Flattened runtime config
├── history.json             # Per-step training history
├── runtime_state.json       # Resume checkpoint
├── best_skill.md            # Best validated skill document
├── skills/skill_vXXXX.md   # Skill snapshot per step
├── steps/step_XXXX/        # Per-step artifacts (patches, evals)
├── slow_update/epoch_XX/   # Slow update logs
└── meta_skill/epoch_XX/    # Meta skill logs
```

같은 command를 다시 실행하면 마지막으로 완료된 step부터 자동 resume합니다.

### Pretrained Skill Artifacts

Upstream은 paper main Table 1의 GPT-5.5 optimized skill 일부를 `ckpt/` reference artifact로 제공합니다. 이 trimmed vendor snapshot에는 `ckpt/` tree가 포함되어 있지 않습니다. `scripts/eval_only.py`에서 packaged skill을 사용해야 하면 upstream에서 가져오세요.

---

## Data Preparation

### Directory layout

SkillOpt는 `train/`, `val/`, `test/` subdirectory를 가진 **split directory**를 기대합니다. 각 subdirectory에는 JSON file(예: `items.json`)이 있습니다.

```text
data/my_split/
├── train/items.json
├── val/items.json
└── test/items.json
```

각 JSON file은 task item array입니다. 필요한 field는 benchmark마다 다릅니다. 예를 들어 SearchQA item은 다음과 같습니다.

```json
[
  {
    "id": "unique_item_id",
    "question": "Who wrote the novel ...",
    "context": "[DOC] relevant passage text ...",
    "answers": ["expected answer"]
  }
]
```

각 benchmark가 기대하는 정확한 format은 `skillopt/envs/<benchmark>/dataloader.py`를 확인하세요.

> **Note:** 대부분의 benchmark dataset은 이 repository에 포함되어 있지 않습니다. 위 format에 맞춰 직접 data를 준비하세요. paper에서 사용한 정확한 SearchQA split은 [`data/searchqa_id_split/`](data/searchqa_id_split)에 제공됩니다(400 train / 200 val / 1400 test).

### Supported Benchmarks

| Benchmark | Type | Config |
|---|---|---|
| SearchQA | QA | `configs/searchqa/default.yaml` |
| ALFWorld | Embodied agent | `configs/alfworld/default.yaml` |
| DocVQA | Document QA | `configs/docvqa/default.yaml` |
| LiveMathematicianBench | Math | `configs/livemathematicianbench/default.yaml` |
| SpreadsheetBench | Code generation | `configs/spreadsheetbench/default.yaml` |
| OfficeQA | Tool-augmented QA | `configs/officeqa/default.yaml` |

---

## Configuration

### Default settings and paper-reproduction knobs

`configs/_base_/default.yaml`은 SkillOpt runtime knob의 single source of truth입니다. 포함된 모든 benchmark config는 기본적으로 이를 inherit하며 paper protocol을 보이게 유지합니다. 4 epochs, rollout batch 40, reflection minibatch 8, cosine decay를 적용한 textual learning rate 4, strict hard validation gating, slow-update + meta-skill enabled입니다. 주의할 점은 slow-update acceptance입니다. 현재 `main` default는 더 새로운 post-submission force-accept mode이고, paper protocol 및 `ckpt/` 아래 paper-aligned skill은 paper Section 3.6의 gated semantics를 사용합니다.

### Slow-update acceptance mode

Epoch boundary의 slow / meta update는 `optimizer.slow_update_gate_with_selection`으로 제어되는 두 방식 중 하나로 적용됩니다.

```yaml
optimizer:
  slow_update_gate_with_selection: false   # current main default
```

- **`false`** *(current `main` default)*: force-accept. slow-update guidance가 epoch boundary에서 `current_skill`과 `best_skill` 모두에 unconditional injection됩니다. `main`의 newer post-submission behavior입니다.
- **`true`** *(paper / ckpt-skill reproduction)*: gated. paper Section 3.6과 일치합니다. slow-update candidate를 selection split에서 평가하고, step-level edit과 같은 validation gate를 통과할 때만 accepted 됩니다. paper protocol 및 제공된 `ckpt/` skill provenance와 맞춰 optimization을 다시 실행하려면 이 setting을 사용하세요.

Trainer는 startup 때 active mode를 출력합니다(`[slow update] acceptance=...`). 해당 flag가 도입된 논의는 issue #22를 참고하세요.

### Gate metric (`hard` / `soft` / `mixed`)

Validation gate는 `gate_metric`을 사용해 selection split에서 candidate skill과 current skill을 비교합니다.

- **`hard`** *(default, paper)*: exact-match accuracy입니다. current score보다 strict하게 커야 합니다.
- **`soft`**: item별 soft / partial-credit score입니다. selection split이 작고(예: ≤10 items) reward가 continuous라서 discrete hard gate가 대부분 candidate를 reject할 때 유용합니다.
- **`mixed`**: `(1 - w) * hard + w * soft` weighted average이며, `w`는 `gate_mixed_weight`(default `0.5`)가 정합니다.

Default는 `hard`입니다. 전환하려면 아래 optional feature config를 사용하세요.

### Optional feature configs

이들은 default SkillOpt setting이 아닙니다. 특정 scenario를 위해 user가 기여한 optional feature config입니다. paper-reported numbers는 이 설정이 아니라 default setting으로 얻었습니다.

- **[`configs/features/soft_gate.yaml`](configs/features/soft_gate.yaml)** *(PR #25, contributed by [@lvbaocheng](https://github.com/lvbaocheng))* — `gate_metric`을 `soft`(또는 `mixed`)로 전환합니다. 언제 써야 하고 언제 쓰면 안 되는지는 file 상단 comment를 보세요.

---

## Extensibility & WebUI

### Adding a new backend

Backend는 chat / exec target입니다. 예: `openai_chat`, `claude_chat`, `qwen_chat`, `minimax_chat`, `codex_exec`, `claude_code_exec`, `pi_chat`, `pi_exec`. 간단히 말해 `skillopt/model/<name>_backend.py` module을 추가하고, `skillopt/model/common.py`와 `backend_config.py`에 등록한 뒤, `skillopt/model/__init__.py` router에 연결합니다. `qwen_backend.py`, `minimax_backend.py`, `pi_backend.py`가 유용한 local example입니다.

### Adding a new benchmark

Benchmark는 `dataloader.py`, `rollout.py`, `initial.md` seed skill을 가진 `skillopt/envs/<name>/` package입니다. Upstream `docs/` tree는 이 trimmed vendor snapshot에 포함되어 있지 않습니다. 가장 단순한 local reference로 `skillopt/envs/searchqa/`를 사용하세요.

### WebUI

Monitoring dashboard를 실행합니다(optional).

```bash
pip install -e ".[webui]"
python -m skillopt_webui.app
```

| Flag | Default | Description |
|---|---|---|
| `--port` | 7860 | Server port |
| `--host` | `0.0.0.0` | Bind address |
| `--share` | off | Public Gradio share link 생성 |

---

## Citation

```bibtex
@misc{yang2026skilloptexecutivestrategyselfevolving,
      title={SkillOpt: Executive Strategy for Self-Evolving Agent Skills},
      author={Yifan Yang and Ziyang Gong and Weiquan Huang and Qihao Yang and Ziwei Zhou and Zisu Huang and Yan Li and Xuemei Gao and Qi Dai and Bei Liu and Kai Qiu and Yuqing Yang and Dongdong Chen and Xue Yang and Chong Luo},
      year={2026},
      eprint={2605.23904},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2605.23904}
}
```
