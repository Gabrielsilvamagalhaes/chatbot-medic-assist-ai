"""
Testes para o script de treinamento e avaliação (B15–B20).

O fixture `trained_models` executa train_model.main() uma vez por sessão.
"""
import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import sklearn  # noqa: F401
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not (PANDAS_AVAILABLE and SKLEARN_AVAILABLE),
    reason="pandas e/ou scikit-learn não instalados",
)

ROOT_DIR      = pathlib.Path(__file__).parent.parent
MODELS_DIR    = ROOT_DIR / "models"
PROCESSED_DIR = ROOT_DIR / "dataset" / "processed"
TRAIN_CSV     = PROCESSED_DIR / "hospital-data-train.csv"
TEST_CSV      = PROCESSED_DIR / "hospital-data-test.csv"

ALGORITHMS = ["decision_tree", "random_forest"]


@pytest.fixture(scope="module")
def trained_models():
    """Executa train_model.main() uma vez e retorna metadados."""
    if not TRAIN_CSV.exists() or not TEST_CSV.exists():
        pytest.skip("Conjuntos treino/teste não encontrados — execute src/split_dataset.py")

    from train_model import main
    main()

    with open(MODELS_DIR / "model_metadata.json", encoding="utf-8") as fh:
        metadata = json.load(fh)
    return metadata


class TestArtefatosModelo:
    def test_quatro_modelos_joblib_criados(self, trained_models):
        for algo in ALGORITHMS:
            assert (MODELS_DIR / f"{algo}_area.joblib").exists()
            assert (MODELS_DIR / f"{algo}_urgency.joblib").exists()

    def test_metricas_json_criados(self, trained_models):
        for algo in ALGORITHMS:
            assert (MODELS_DIR / f"metrics_{algo}.json").exists()

    def test_model_metadata_criado(self, trained_models):
        assert (MODELS_DIR / "model_metadata.json").exists()


class TestMetricas:
    @pytest.mark.parametrize("algo", ALGORITHMS)
    def test_acuracia_entre_zero_e_um(self, trained_models, algo):
        with open(MODELS_DIR / f"metrics_{algo}.json", encoding="utf-8") as fh:
            metrics = json.load(fh)
        for target in ("area_recomendada", "nivel_urgencia", "media"):
            acc = metrics["accuracy"][target]
            assert 0.0 <= acc <= 1.0

    @pytest.mark.parametrize("algo", ALGORITHMS)
    def test_matriz_confusao_presente(self, trained_models, algo):
        with open(MODELS_DIR / f"metrics_{algo}.json", encoding="utf-8") as fh:
            metrics = json.load(fh)
        for target in ("area_recomendada", "nivel_urgencia"):
            matrix = metrics["confusion_matrix"][target]
            assert isinstance(matrix, list)
            assert len(matrix) > 0

    @pytest.mark.parametrize("algo", ALGORITHMS)
    def test_classification_report_presente(self, trained_models, algo):
        with open(MODELS_DIR / f"metrics_{algo}.json", encoding="utf-8") as fh:
            metrics = json.load(fh)
        for target in ("area_recomendada", "nivel_urgencia"):
            report = metrics["classification_report"][target]
            assert "accuracy" in report


class TestSelecaoAlgoritmo:
    def test_best_algorithm_valido(self, trained_models):
        assert trained_models["best_algorithm"] in ALGORITHMS

    def test_feature_columns_corretas(self, trained_models):
        assert trained_models["feature_columns"] == ["Age", "Gender", "Condition"]
