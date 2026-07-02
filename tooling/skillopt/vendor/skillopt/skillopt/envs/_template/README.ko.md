# Benchmark Template

[English](README.md)

이 디렉터리는 SkillOpt에 새 benchmark를 추가할 때 쓰는 scaffold files를 제공합니다.

## 파일

- `env_template.py` — environment adapter template입니다. `EnvAdapter`를 subclass하고, 파일을 바로 instantiate할 수 있도록 5개 abstract method를 구현해 둡니다.
- `loader_template.py` — data loader template입니다. `SplitDataLoader`를 subclass하고 `.json`/`.jsonl`용 `load_split_items`를 구현합니다.
- `config_template.yaml` — config file template입니다.

## 사용법

1. **디렉터리를 복사합니다.**

   ```bash
   cp -r skillopt/envs/_template skillopt/envs/your_benchmark
   ```

2. **파일 이름을 바꿉니다**(`_template` suffix 제거).

   ```bash
   cd skillopt/envs/your_benchmark
   mv env_template.py    adapter.py
   mv loader_template.py loader.py
   ```

   그리고 각 파일 안에서 class 이름을 바꿉니다(`TemplateBenchmarkEnv → YourBenchmarkAdapter`, `TemplateBenchmarkLoader → YourBenchmarkLoader`). `adapter.py`의 cross-import도 맞게 고칩니다.

3. `adapter.py:rollout`의 TODO block과 `loader.py`의 `_normalize_item` helper를 구현합니다. 실제 reflection을 쓰려면 `adapter.py:reflect`의 `run_minibatch_reflect` block 주석을 해제합니다.

4. adapter를 **등록**합니다. `scripts/train.py`의 `_register_builtins()` mapping에 `try / except ImportError` block을 추가하고 registry key를 `YourBenchmarkAdapter` class에 매핑합니다. `skillopt/envs/__init__.py`에는 `BENCHMARK_REGISTRY` dict가 없습니다. 실제 registry는 `scripts/train.py`의 `_ENV_REGISTRY`입니다.

5. `configs/your_benchmark/default.yaml`에 config를 만듭니다(`config_template.yaml`에서 시작). `_base_`는 list가 아니라 **string path**입니다.

Upstream `docs/` tree는 이 trimmed vendor snapshot에 포함되어 있지 않습니다. 이 template을 `skillopt/envs/searchqa/`, `skillopt/envs/spreadsheetbench/` 같은 기존 benchmark package와 함께 local reference로 사용하세요.
