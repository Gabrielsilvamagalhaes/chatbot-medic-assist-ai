import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

import pytest
from chatbot.urgency_triage_rules import (
    apply_rules,
    apply_urgency_rules,
    get_base_urgency,
    URGENCIA_BAIXA,
    URGENCIA_PRIORITARIO,
    URGENCIA_EMERGENCIA,
)
from chatbot.recommended_area_rules import (
    AREA_PRONTO_SOCORRO,
    KEYWORDS_CARDIAC,
    KEYWORDS_NEUROLOGICAL,
)


def _patient(condition, age=40, conscious=True, breathing=True, pain=False, fever=False):
    """Helper para montar patient_data com defaults razoáveis."""
    return {
        "primary_condition": condition,
        "age": age,
        "is_conscious": conscious,
        "has_difficulty_breathing": not breathing,
        "has_intense_pain": pain,
        "has_fever": fever,
    }


# ---------------------------------------------------------------------------
# get_base_urgency — urgência por condição sem sintomas
# ---------------------------------------------------------------------------

class TestGetBaseUrgency:
    def test_stroke_e_emergencia(self):
        assert get_base_urgency("Stroke") == URGENCIA_EMERGENCIA

    def test_pregnancy_e_emergencia(self):
        assert get_base_urgency("Pregnancy Complication") == URGENCIA_EMERGENCIA

    def test_appendicitis_e_emergencia(self):
        assert get_base_urgency("Appendicitis") == URGENCIA_EMERGENCIA

    def test_heart_disease_e_prioritario(self):
        assert get_base_urgency("Heart Disease") == URGENCIA_PRIORITARIO

    def test_hypertension_e_prioritario(self):
        assert get_base_urgency("Hypertension") == URGENCIA_PRIORITARIO

    def test_fracture_e_prioritario(self):
        assert get_base_urgency("Fractured Arm") == URGENCIA_PRIORITARIO

    def test_diabetes_e_prioritario(self):
        assert get_base_urgency("Diabetes") == URGENCIA_PRIORITARIO

    def test_cancer_e_prioritario(self):
        assert get_base_urgency("Cancer") == URGENCIA_PRIORITARIO

    def test_flu_e_baixa(self):
        assert get_base_urgency("Flu") == URGENCIA_BAIXA

    def test_skin_disease_e_baixa(self):
        assert get_base_urgency("Skin Disease") == URGENCIA_BAIXA

    def test_condicao_desconhecida_e_baixa(self):
        assert get_base_urgency("Dor de cabeça") == URGENCIA_BAIXA


# ---------------------------------------------------------------------------
# apply_urgency_rules — escalada por sintomas (B05)
# ---------------------------------------------------------------------------

class TestEscaladaUrgencia:
    def test_dor_intensa_escala_baixa_para_prioritario(self):
        p = _patient("Flu", pain=True)
        assert apply_urgency_rules(p) == URGENCIA_PRIORITARIO

    def test_dor_intensa_nao_escala_prioritario(self):
        # Dor intensa só escala BAIXA → não muda PRIORITARIO para cima
        p = _patient("Heart Disease", pain=True)
        assert apply_urgency_rules(p) == URGENCIA_PRIORITARIO

    def test_inconsciencia_e_emergencia_independente_de_condicao(self):
        p = _patient("Flu", conscious=False)
        assert apply_urgency_rules(p) == URGENCIA_EMERGENCIA

    def test_dificuldade_respiratoria_e_emergencia(self):
        p = _patient("Skin Disease", breathing=False)
        assert apply_urgency_rules(p) == URGENCIA_EMERGENCIA

    def test_sem_sintomas_agravantes_mantem_urgencia_base(self):
        p = _patient("Skin Disease")
        assert apply_urgency_rules(p) == URGENCIA_BAIXA


# ---------------------------------------------------------------------------
# apply_rules — caminho completo (B23 — casos simulados)
# ---------------------------------------------------------------------------

class TestApplyRules:
    def test_cardiologia_prioritario(self):
        area, urgency = apply_rules(_patient("Heart Disease"))
        assert "Cardiologia" in area
        assert urgency == URGENCIA_PRIORITARIO

    def test_neurologia_emergencia(self):
        area, urgency = apply_rules(_patient("Stroke"))
        assert "Neurologia" in area
        assert urgency == URGENCIA_EMERGENCIA

    def test_ortopedia_prioritario(self):
        area, urgency = apply_rules(_patient("Fractured Arm"))
        assert "Ortopedia" in area
        assert urgency == URGENCIA_PRIORITARIO

    def test_obstetricia_emergencia(self):
        area, urgency = apply_rules(_patient("Pregnancy Complication"))
        assert "Obstetrícia" in area
        assert urgency == URGENCIA_EMERGENCIA

    def test_clinica_medica_baixa(self):
        area, urgency = apply_rules(_patient("Dor de cabeça"))
        assert area == "Clínica Médica"
        assert urgency == URGENCIA_BAIXA

    def test_clinica_medica_com_dor_escalada(self):
        # Fallback com dor intensa deve escalar para prioritario
        area, urgency = apply_rules(_patient("Dor de cabeça", pain=True))
        assert urgency == URGENCIA_PRIORITARIO

    def test_emergencia_imediata_inconsciencia(self):
        area, urgency = apply_rules(_patient("Flu", conscious=False))
        assert area == AREA_PRONTO_SOCORRO
        assert urgency == URGENCIA_EMERGENCIA

    def test_emergencia_imediata_dificuldade_respiratoria(self):
        area, urgency = apply_rules(_patient("Skin Disease", breathing=False))
        assert area == AREA_PRONTO_SOCORRO
        assert urgency == URGENCIA_EMERGENCIA


# ---------------------------------------------------------------------------
# Fix #1 — keywords são o mesmo objeto entre os dois módulos
# ---------------------------------------------------------------------------

class TestKeywordsCompartilhadas:
    def test_cardiac_keywords_sao_o_mesmo_objeto(self):
        from chatbot.urgency_triage_rules import KEYWORDS_CARDIAC as UK
        from chatbot.recommended_area_rules import KEYWORDS_CARDIAC as AK
        assert UK is AK

    def test_neurological_keywords_sao_o_mesmo_objeto(self):
        from chatbot.urgency_triage_rules import KEYWORDS_NEUROLOGICAL as UK
        from chatbot.recommended_area_rules import KEYWORDS_NEUROLOGICAL as AK
        assert UK is AK


# ---------------------------------------------------------------------------
# Fix #3 — _escalate_urgency não checa emergência (checks removidos)
# ---------------------------------------------------------------------------

class TestEscalateUrgencyNaoVerificaEmergencia:
    def test_escala_dor_baixa_para_prioritario(self):
        # Verifica que o comportamento de escalada ainda funciona corretamente
        p = _patient("Respiratory Infection", pain=True)
        _, urgency = apply_rules(p)
        assert urgency == URGENCIA_PRIORITARIO

    def test_sem_dor_mantem_urgencia_base_baixa(self):
        p = _patient("Respiratory Infection")
        _, urgency = apply_rules(p)
        assert urgency == URGENCIA_BAIXA
