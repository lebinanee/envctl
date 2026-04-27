"""Tests for envctl.pipeline."""
from __future__ import annotations

import pytest

from envctl.pipeline import (
    PipelineError,
    PipelineStep,
    PipelineResult,
    build_pipeline,
    run_pipeline,
)


class FakeConfig:
    def __init__(self, profiles: dict | None = None):
        self._profiles = profiles or {}
        self.saved = False

    def get_profile(self, name: str):
        return self._profiles.get(name)

    def set_profile(self, name: str, vars_: dict):
        self._profiles[name] = vars_

    def save(self):
        self.saved = True


def _upper_step() -> PipelineStep:
    return PipelineStep(
        name="uppercase",
        fn=lambda v: {k: val.upper() for k, val in v.items()},
    )


def _strip_step() -> PipelineStep:
    return PipelineStep(
        name="strip",
        fn=lambda v: {k: val.strip() for k, val in v.items()},
    )


def make_config(vars_: dict | None = None, profile: str = "local") -> FakeConfig:
    return FakeConfig({profile: vars_ or {"FOO": "bar", "BAZ": "  qux  "}})


def test_run_pipeline_applies_steps():
    cfg = make_config({"FOO": "hello"})
    result = run_pipeline(cfg, "local", [_upper_step()])
    assert result.final_vars == {"FOO": "HELLO"}
    assert result.steps_applied == ["uppercase"]
    assert cfg._profiles["local"]["FOO"] == "HELLO"


def test_run_pipeline_chains_multiple_steps():
    cfg = make_config({"FOO": "  world  "})
    result = run_pipeline(cfg, "local", [_strip_step(), _upper_step()])
    assert result.final_vars == {"FOO": "WORLD"}
    assert result.steps_applied == ["strip", "uppercase"]


def test_run_pipeline_dry_run_does_not_save():
    cfg = make_config({"FOO": "hello"})
    result = run_pipeline(cfg, "local", [_upper_step()], dry_run=True)
    assert result.final_vars == {"FOO": "HELLO"}
    assert not cfg.saved
    assert cfg._profiles["local"]["FOO"] == "hello"  # unchanged


def test_run_pipeline_missing_profile_raises():
    cfg = FakeConfig()
    with pytest.raises(PipelineError, match="not found"):
        run_pipeline(cfg, "missing", [_upper_step()])


def test_build_pipeline_rejects_duplicate_names():
    with pytest.raises(PipelineError, match="Duplicate step"):
        build_pipeline([_upper_step(), _upper_step()])


def test_run_pipeline_step_exception_raises_when_stop_on_error():
    def bad_fn(v):
        raise ValueError("boom")

    bad_step = PipelineStep(name="bad", fn=bad_fn)
    cfg = make_config({"FOO": "x"})
    with pytest.raises(PipelineError, match="boom"):
        run_pipeline(cfg, "local", [bad_step], stop_on_error=True)


def test_run_pipeline_step_exception_skipped_when_not_stop_on_error():
    def bad_fn(v):
        raise RuntimeError("skip me")

    bad_step = PipelineStep(name="bad", fn=bad_fn)
    cfg = make_config({"FOO": "hello"})
    result = run_pipeline(cfg, "local", [bad_step, _upper_step()], stop_on_error=False)
    assert "bad" in result.steps_skipped
    assert "uppercase" in result.steps_applied
    assert result.final_vars == {"FOO": "HELLO"}


def test_pipeline_result_total_applied():
    r = PipelineResult(profile="local", steps_applied=["a", "b"], steps_skipped=["c"])
    assert r.total_applied == 2
