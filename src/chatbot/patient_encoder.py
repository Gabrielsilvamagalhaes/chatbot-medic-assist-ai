"""
Codificador de dados do paciente para entrada do modelo (B21).

Converte o dict coletado pelo chatbot em vetor numérico [Age, Gender, Condition]
usando os mesmos mapeamentos do treinamento (encoding_maps.json).
"""

import json
import pathlib

from .recommended_area_rules import (
    KEYWORDS_APPENDICITIS,
    KEYWORDS_CANCER,
    KEYWORDS_CARDIAC,
    KEYWORDS_DIABETES,
    KEYWORDS_FRACTURE,
    KEYWORDS_NEUROLOGICAL,
    KEYWORDS_PREGNANCY,
    KEYWORDS_RESPIRATORY,
    KEYWORDS_SKIN,
)
from .conversation import CONDITIONS

ROOT_DIR      = pathlib.Path(__file__).parent.parent.parent
ENCODING_MAPS = ROOT_DIR / "dataset" / "processed" / "encoding_maps.json"

# Mapeamento gênero do chatbot → rótulo do dataset (alinhado a encoding_maps.json)
GENDER_CHATBOT_TO_DATASET: dict[str, str] = {
    "Feminino":                      "Female",
    "Masculino":                     "Male",
    "Outro / Prefiro não informar":  "Female",  # default documentado — dataset só tem Female/Male
}

# Mapeamento opções do chatbot → Condition do dataset Kaggle
CHATBOT_TO_DATASET_CONDITION: dict[str, str] = {
    CONDITIONS[0]: "Heart Disease",       # Dor cardíaca / peito
    CONDITIONS[1]: "Stroke",             # AVC / neurológico
    CONDITIONS[2]: "Fractured Arm",       # Fratura / trauma
    CONDITIONS[3]: "Respiratory Infection",  # Gripe / respiratório
    CONDITIONS[4]: "Childbirth",          # Complicação na gravidez
    CONDITIONS[5]: "Diabetes",            # Diabetes / glicose
    CONDITIONS[6]: "Allergic Reaction",    # Pele — condição mais próxima no dataset
}

# Tabela de keywords para texto livre (opção "Other")
_KEYWORD_TO_CONDITION: list[tuple[tuple[str, ...], str]] = [
    (KEYWORDS_NEUROLOGICAL,  "Stroke"),
    (KEYWORDS_PREGNANCY,     "Childbirth"),
    (KEYWORDS_APPENDICITIS,  "Appendicitis"),
    (KEYWORDS_CARDIAC,       "Heart Disease"),
    (KEYWORDS_FRACTURE,      "Fractured Arm"),
    (KEYWORDS_DIABETES,      "Diabetes"),
    (KEYWORDS_CANCER,        "Cancer"),
    (KEYWORDS_RESPIRATORY,   "Respiratory Infection"),
    (KEYWORDS_SKIN,          "Allergic Reaction"),
]

# Condition padrão quando nenhuma keyword é encontrada
DEFAULT_CONDITION = "Hypertension"  # Clínica Médica no dataset


def _load_encoding_maps() -> dict:
    """Carrega mapeamentos label→int do B10."""
    with open(ENCODING_MAPS, encoding="utf-8") as fh:
        return json.load(fh)


def _resolve_dataset_condition(primary_condition: str) -> str:
    """
    Converte a condição informada pelo paciente para o rótulo do dataset.

    Opções fixas do chatbot usam CHATBOT_TO_DATASET_CONDITION;
    texto livre (Other) usa heurística por keywords.
    """
    if primary_condition in CHATBOT_TO_DATASET_CONDITION:
        return CHATBOT_TO_DATASET_CONDITION[primary_condition]

    normalized = primary_condition.lower().strip()
    for keywords, condition in _KEYWORD_TO_CONDITION:
        if any(kw in normalized for kw in keywords):
            return condition

    return DEFAULT_CONDITION


def encode_patient_data(patient_data: dict) -> list[int]:
    """
    Retorna vetor [Age, Gender_encoded, Condition_encoded] para o modelo.

    Usa encoding_maps.json para garantir mesma codificação do treinamento.
    """
    maps = _load_encoding_maps()

    age = int(patient_data["age"])

    gender_label = GENDER_CHATBOT_TO_DATASET.get(
        patient_data["gender"], "Female"
    )
    gender_encoded = maps["Gender"][gender_label]

    condition_label = _resolve_dataset_condition(patient_data["primary_condition"])
    condition_encoded = maps["Condition"][condition_label]

    return [age, gender_encoded, condition_encoded]
