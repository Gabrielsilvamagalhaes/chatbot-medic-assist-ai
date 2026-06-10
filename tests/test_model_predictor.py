"""
Testes para integração chatbot ↔ modelo (B21) e encoder de paciente.
"""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

try:
    import sklearn  # noqa: F401
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not SKLEARN_AVAILABLE,
    reason="scikit-learn não instalado",
)

ROOT_DIR      = pathlib.Path(__file__).parent.parent
MODELS_DIR    = ROOT_DIR / "models"
PROCESSED_DIR = ROOT_DIR / "dataset" / "processed"
TRAIN_CSV     = PROCESSED_DIR / "hospital-data-train.csv"


@pytest.fixture(scope="module")
def trained_models():
    """Garante que os modelos estejam treinados antes dos testes de predição."""
    if not TRAIN_CSV.exists():
        pytest.skip("Dataset de treino não encontrado — execute pipeline B08–B11")

    if not (MODELS_DIR / "model_metadata.json").exists():
        from train_model import main as train_main
        train_main()

    # Reseta cache do predictor para recarregar modelos
    import chatbot.model_predictor as mp
    mp._models_cache = None
    mp._maps_cache = None
    mp._metadata_cache = None


def _base_patient(**overrides) -> dict:
    """Paciente simulado com valores padrão seguros."""
    data = {
        "age": 45,
        "gender": "Masculino",
        "primary_condition": "Dor no Coração/Dor no Peito/ Heart Disease / Chest Pain",
        "has_fever": False,
        "has_intense_pain": False,
        "has_difficulty_breathing": False,
        "is_conscious": True,
        "symptom_duration_days": 2,
        "has_chronic_disease": False,
        "chronic_detail": "",
    }
    data.update(overrides)
    return data


class TestEmergenciaRegras:
    def test_inconsciencia_usa_regras_seguranca(self, trained_models):
        from chatbot.model_predictor import predict_triage
        from chatbot.recommended_area_rules import AREA_PRONTO_SOCORRO

        patient = _base_patient(is_conscious=False)
        area, urgency, source = predict_triage(patient)

        assert source == "regras_seguranca"
        assert area == AREA_PRONTO_SOCORRO
        assert urgency == "emergencia"

    def test_dificuldade_respiratoria_usa_regras_seguranca(self, trained_models):
        from chatbot.model_predictor import predict_triage

        patient = _base_patient(has_difficulty_breathing=True)
        _, urgency, source = predict_triage(patient)

        assert source == "regras_seguranca"
        assert urgency == "emergencia"


class TestPredicaoModelo:
    def test_caso_cardiaco_retorna_area_valida(self, trained_models):
        from chatbot.model_predictor import predict_triage

        patient = _base_patient()
        area, urgency, source = predict_triage(patient)

        assert source.startswith("modelo_ia")
        assert "Cardiologia" in area or "Pronto" in area or "Clínica" in area
        assert urgency in ("baixa", "prioritario", "emergencia")

    def test_dor_intensa_escala_urgencia(self, trained_models):
        from chatbot.model_predictor import predict_triage

        patient = _base_patient(
            primary_condition="Gripe / Dificuldade em Respirar / Flu / Respiratory Infection",
            has_intense_pain=True,
        )
        _, urgency, _ = predict_triage(patient)

        assert urgency in ("prioritario", "emergencia")


class TestFallback:
    def test_sem_modelos_usa_regras_fallback(self, monkeypatch):
        import chatbot.model_predictor as mp
        mp._models_cache = None
        mp._maps_cache = None
        mp._metadata_cache = None

        monkeypatch.setattr(mp, "_models_available", lambda: False)

        patient = _base_patient()
        area, urgency, source = mp.predict_triage(patient)

        assert source == "regras_fallback"
        assert area
        assert urgency in ("baixa", "prioritario", "emergencia")


class TestPatientEncoder:
    def test_cada_opcao_chatbot_gera_vetor_valido(self, trained_models):
        from chatbot.patient_encoder import encode_patient_data, CHATBOT_TO_DATASET_CONDITION

        for condition in CHATBOT_TO_DATASET_CONDITION:
            patient = _base_patient(primary_condition=condition)
            vector = encode_patient_data(patient)

            assert len(vector) == 3
            assert isinstance(vector[0], int)   # Age
            assert vector[1] in (0, 1)          # Gender
            assert isinstance(vector[2], int)     # Condition

    def test_texto_livre_other_usa_heuristica(self, trained_models):
        from chatbot.patient_encoder import encode_patient_data

        patient = _base_patient(primary_condition="fratura no braço")
        vector = encode_patient_data(patient)
        assert len(vector) == 3
