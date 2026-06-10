"""
Preditor de triagem integrado ao modelo treinado (B21).

Carrega o melhor algoritmo (DT ou RF) de models/, prediz área e urgência,
e aplica camada híbrida de segurança com regras clínicas existentes.
"""

import json
import pathlib

try:
    import joblib
    import pandas as pd
except ImportError:
    joblib = None
    pd = None

from .patient_encoder import encode_patient_data
from .recommended_area_rules import (
    AREA_PEDIATRIA,
    AREA_PNEUMOLOGIA,
    AREA_PRONTO_SOCORRO,
    apply_area_rules,
)
from .urgency_triage_rules import (
    URGENCIA_BAIXA,
    URGENCIA_EMERGENCIA,
    URGENCIA_PRIORITARIO,
    apply_urgency_rules,
    apply_rules,
)

ROOT_DIR       = pathlib.Path(__file__).parent.parent.parent
MODELS_DIR     = ROOT_DIR / "models"
ENCODING_MAPS  = ROOT_DIR / "dataset" / "processed" / "encoding_maps.json"
METADATA_FILE  = MODELS_DIR / "model_metadata.json"

# Ordem ordinal de urgência para comparação (maior = mais grave)
_URGENCY_ORDER = {
    URGENCIA_BAIXA:       0,
    URGENCIA_PRIORITARIO: 1,
    URGENCIA_EMERGENCIA:  2,
}

# Rótulos legíveis dos algoritmos para exibição ao paciente (B22)
_ALGO_DISPLAY = {
    "decision_tree": "Árvore de Decisão",
    "random_forest": "Random Forest",
}

# Cache dos modelos carregados — evita releitura a cada predição na mesma sessão
_models_cache: dict | None = None
_maps_cache: dict | None = None
_metadata_cache: dict | None = None


def _models_available() -> bool:
    """Verifica se os artefatos de treinamento existem."""
    return METADATA_FILE.exists() and joblib is not None


def _load_resources() -> tuple[dict, dict, object, object]:
    """Carrega metadados, mapas de codificação e par de modelos (área + urgência)."""
    global _models_cache, _maps_cache, _metadata_cache

    if _metadata_cache is None:
        with open(METADATA_FILE, encoding="utf-8") as fh:
            _metadata_cache = json.load(fh)
        with open(ENCODING_MAPS, encoding="utf-8") as fh:
            _maps_cache = json.load(fh)

        algo = _metadata_cache["best_algorithm"]
        _models_cache = {
            "area":    joblib.load(MODELS_DIR / f"{algo}_area.joblib"),
            "urgency": joblib.load(MODELS_DIR / f"{algo}_urgency.joblib"),
            "algo":    algo,
        }

    return _metadata_cache, _maps_cache, _models_cache["area"], _models_cache["urgency"]


def _decode_label(encoded_value: int, column: str, maps: dict) -> str:
    """Converte código numérico do modelo de volta ao rótulo legível."""
    inverted = {v: k for k, v in maps[column].items()}
    return inverted[int(encoded_value)]


def _max_urgency(urgency_a: str, urgency_b: str) -> str:
    """Retorna a urgência mais grave entre duas (escalada de segurança)."""
    if _URGENCY_ORDER.get(urgency_a, 0) >= _URGENCY_ORDER.get(urgency_b, 0):
        return urgency_a
    return urgency_b


def _apply_pediatric_override(patient_data: dict, area_ml: str) -> str:
    """
    Se paciente < 12 anos e área pneumologia/clínica, aplica regra pediátrica.

    O modelo pode não capturar faixa etária pediátrica com precisão — regra prevalece.
    """
    age = patient_data["age"]
    if age < 12:
        rule_area = apply_area_rules(patient_data["primary_condition"], age)
        if rule_area == AREA_PEDIATRIA:
            return AREA_PEDIATRIA
        if area_ml == AREA_PNEUMOLOGIA and age < 12:
            return AREA_PEDIATRIA
    return area_ml


def predict_triage(patient_data: dict) -> tuple[str, str, str]:
    """
    Retorna (area_recomendada, nivel_urgencia, fonte).

    fonte: "modelo_ia" | "regras_seguranca" | "regras_fallback"
    """
    # Camada 1 — emergência imediata: inconsciência ou dificuldade respiratória
    if not patient_data["is_conscious"] or patient_data["has_difficulty_breathing"]:
        return AREA_PRONTO_SOCORRO, URGENCIA_EMERGENCIA, "regras_seguranca"

    # Fallback gracioso se modelos não foram treinados
    if not _models_available():
        area, urgency = apply_rules(patient_data)
        return area, urgency, "regras_fallback"

    metadata, maps, model_area, model_urgency = _load_resources()

    # Codifica dados do paciente e prediz com o modelo vencedor (B15/B16)
    # DataFrame com nomes de colunas evita warning do sklearn na inferência
    feature_cols = metadata["feature_columns"]
    features = pd.DataFrame(
        [encode_patient_data(patient_data)],
        columns=feature_cols,
    )
    pred_area    = int(model_area.predict(features)[0])
    pred_urgency = int(model_urgency.predict(features)[0])

    area_ml    = _decode_label(pred_area, "area_recomendada", maps)
    urgency_ml = _decode_label(pred_urgency, "nivel_urgencia", maps)

    # Camada 2 — escalada por sintomas: urgência final = máximo entre ML e regras
    urgency_rules = apply_urgency_rules(patient_data)
    urgency_final = _max_urgency(urgency_ml, urgency_rules)

    # Camada 3 — override pediátrico quando aplicável
    area_final = _apply_pediatric_override(patient_data, area_ml)

    algo_name = _ALGO_DISPLAY.get(
        _models_cache["algo"], _models_cache["algo"]
    )
    return area_final, urgency_final, f"modelo_ia ({algo_name})"


def get_algorithm_display_name() -> str:
    """Retorna nome legível do algoritmo em uso (para exibição B22)."""
    if not _models_available():
        return "Regras clínicas"
    metadata, _, _, _ = _load_resources()
    return _ALGO_DISPLAY.get(metadata["best_algorithm"], metadata["best_algorithm"])
