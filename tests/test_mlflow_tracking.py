from __future__ import annotations

import importlib.util
from contextlib import contextmanager
from types import SimpleNamespace

from demandpulse.mlops import registry, tracking


class FakeMlflow:
    def __init__(self):
        self.uri = None
        self.params = {}
        self.metrics = {}
        self.artifacts = []
        self.experiments = {}
        self.registered = []
        self.aliases = []
        self.version_tags = []
        outer = self

        class Client:
            def set_model_version_tag(self, name, version, key, value):
                outer.version_tags.append((name, version, key, value))

            def get_model_version_by_alias(self, name, alias):
                return SimpleNamespace(name=name, version="7", alias=alias)

            def get_model_version(self, name, version):
                return SimpleNamespace(name=name, version=str(version))

            def set_registered_model_alias(self, name, alias, version):
                outer.aliases.append((name, alias, str(version)))

        self.tracking = SimpleNamespace(MlflowClient=Client)
        self.pyfunc = SimpleNamespace(load_model=lambda uri: {"loaded_uri": uri})

    def set_tracking_uri(self, uri):
        self.uri = uri

    def get_tracking_uri(self):
        return self.uri

    def get_experiment_by_name(self, name):
        exp_id = self.experiments.get(name)
        return None if exp_id is None else SimpleNamespace(experiment_id=exp_id)

    def create_experiment(self, name):
        exp_id = str(len(self.experiments) + 1)
        self.experiments[name] = exp_id
        return exp_id

    @contextmanager
    def start_run(self, **kwargs):
        yield SimpleNamespace(info=SimpleNamespace(run_id="run-123"))

    def log_params(self, params):
        self.params.update(params)

    def log_metrics(self, metrics):
        self.metrics.update(metrics)

    def log_artifact(self, path):
        self.artifacts.append(path)

    def log_artifacts(self, path):
        self.artifacts.append(path)

    def register_model(self, model_uri, name, await_registration_for=300):
        version = SimpleNamespace(name=name, version="3", source=model_uri)
        self.registered.append(version)
        return version


def test_tracking_logs_experiment_parameters_metrics_and_artifact(monkeypatch, tmp_path):
    artifact = tmp_path / "metrics.csv"
    artifact.write_text("metric,value\nWAPE,0.2\n", encoding="utf-8")

    from demandpulse.config import DemandPulseConfig

    config = DemandPulseConfig(
        project_root=tmp_path,
        mlflow_tracking_uri=(tmp_path / "mlruns").as_uri(),
    )

    if importlib.util.find_spec("mlflow") is not None:
        run_id = tracking.log_experiment_run(
            experiment_name="demandpulse-point-forecasting",
            run_name="lgbm_horizon_7_core_features",
            params={"model_type": "LightGBM", "horizon": 7, "features": ["lag_1", "lag_7"]},
            metrics={"WAPE": 0.2, "Bias": -0.01},
            artifacts=[artifact],
            config=config,
        )
        import mlflow

        client = mlflow.tracking.MlflowClient(tracking_uri=config.mlflow_tracking_uri)
        run = client.get_run(run_id)
        assert run.data.params["horizon"] == "7"
        assert run.data.metrics["WAPE"] == 0.2
        assert (tmp_path / "mlruns").exists()
    else:
        # This execution sandbox has no network access to install MLflow. The same helper
        # is exercised through its client boundary; fresh installs run the local-store branch above.
        fake = FakeMlflow()
        monkeypatch.setattr(tracking, "_import_mlflow", lambda: fake)
        run_id = tracking.log_experiment_run(
            experiment_name="demandpulse-point-forecasting",
            run_name="lgbm_horizon_7_core_features",
            params={"model_type": "LightGBM", "horizon": 7, "features": ["lag_1", "lag_7"]},
            metrics={"WAPE": 0.2, "Bias": -0.01},
            artifacts=[artifact],
            config=config,
        )
        assert run_id == "run-123"
        assert fake.uri.startswith("file:")
        assert fake.params["horizon"] == 7
        assert fake.metrics["WAPE"] == 0.2
        assert str(artifact) in fake.artifacts


def test_registry_helpers_and_champion_rules(monkeypatch):
    fake = FakeMlflow()
    monkeypatch.setattr(registry, "_import_mlflow", lambda: fake)
    monkeypatch.setattr(registry, "configure_mlflow", lambda **kwargs: "file:///tmp/mlruns")

    version = registry.register_model("runs:/abc/model", "demandpulse-point", tags={"stage": "candidate"})
    assert version.version == "3"
    registry.set_model_alias("demandpulse-point", "candidate", 3)
    resolved = registry.get_model_version("demandpulse-point", alias="candidate")
    loaded = registry.load_registered_model("demandpulse-point", alias="candidate")

    assert resolved.version == "7"
    assert loaded["loaded_uri"] == "models:/demandpulse-point@candidate"
    assert fake.aliases == [("demandpulse-point", "candidate", "3")]

    passes, reasons = registry.candidate_passes_champion_rules(
        {"WAPE": 0.18, "Bias": 0.02, "Coverage": 0.80},
        {"WAPE": 0.20, "Bias": 0.01, "Coverage": 0.81},
        required_tests_passed=True,
        max_abs_bias=0.05,
        max_coverage_drop=0.03,
    )
    assert passes is True
    assert reasons == []
