import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

import pytest
from chatbot.recommended_area_rules import (
    apply_area_rules,
    AREA_CARDIOLOGIA,
    AREA_NEUROLOGIA,
    AREA_OBSTETRICIA,
    AREA_CIRURGIA,
    AREA_ORTOPEDIA,
    AREA_PNEUMOLOGIA,
    AREA_PEDIATRIA,
    AREA_ENDOCRINOLOGIA,
    AREA_ONCOLOGIA,
    AREA_DERMATOLOGIA,
    AREA_CLINICA_MEDICA,
)


# ---------------------------------------------------------------------------
# Roteamento por condição (B23 — casos simulados para cada especialidade)
# ---------------------------------------------------------------------------

class TestAreaPorCondicao:
    def test_avc_vai_para_neurologia(self):
        assert apply_area_rules("AVC", 40) == AREA_NEUROLOGIA

    def test_stroke_vai_para_neurologia(self):
        assert apply_area_rules("Stroke", 55) == AREA_NEUROLOGIA

    def test_heart_disease_vai_para_cardiologia(self):
        assert apply_area_rules("Heart Disease", 60) == AREA_CARDIOLOGIA

    def test_chest_pain_vai_para_cardiologia(self):
        assert apply_area_rules("Chest Pain", 45) == AREA_CARDIOLOGIA

    def test_hypertension_vai_para_cardiologia(self):
        assert apply_area_rules("Hypertension", 50) == AREA_CARDIOLOGIA

    def test_gravidez_vai_para_obstetricia(self):
        assert apply_area_rules("Complicacao na Gravidez", 28) == AREA_OBSTETRICIA

    def test_childbirth_vai_para_obstetricia(self):
        assert apply_area_rules("Childbirth", 30) == AREA_OBSTETRICIA

    def test_appendicitis_vai_para_cirurgia(self):
        assert apply_area_rules("Appendicitis", 22) == AREA_CIRURGIA

    def test_fratura_vai_para_ortopedia(self):
        assert apply_area_rules("Fractured Arm", 35) == AREA_ORTOPEDIA

    def test_trauma_vai_para_ortopedia(self):
        assert apply_area_rules("Trauma", 30) == AREA_ORTOPEDIA

    def test_respiratory_infection_vai_para_pneumologia(self):
        assert apply_area_rules("Respiratory Infection", 30) == AREA_PNEUMOLOGIA

    def test_flu_vai_para_pneumologia(self):
        assert apply_area_rules("Flu", 25) == AREA_PNEUMOLOGIA

    def test_diabetes_vai_para_endocrinologia(self):
        assert apply_area_rules("Diabetes", 50) == AREA_ENDOCRINOLOGIA

    def test_cancer_vai_para_oncologia(self):
        assert apply_area_rules("Cancer", 55) == AREA_ONCOLOGIA

    def test_skin_disease_vai_para_dermatologia(self):
        assert apply_area_rules("Skin Disease", 30) == AREA_DERMATOLOGIA

    def test_condicao_desconhecida_vai_para_clinica_medica(self):
        assert apply_area_rules("Dor de cabeça", 40) == AREA_CLINICA_MEDICA


# ---------------------------------------------------------------------------
# Roteamento pediátrico por faixa etária
# ---------------------------------------------------------------------------

class TestPediatriaIdade:
    def test_crianca_respiratoria_vai_para_pediatria(self):
        assert apply_area_rules("Respiratory Infection", 8) == AREA_PEDIATRIA

    def test_crianca_exatamente_11_anos_vai_para_pediatria(self):
        assert apply_area_rules("Flu", 11) == AREA_PEDIATRIA

    def test_adolescente_12_anos_vai_para_pneumologia(self):
        assert apply_area_rules("Flu", 12) == AREA_PNEUMOLOGIA

    def test_adulto_respiratorio_nao_vai_para_pediatria(self):
        assert apply_area_rules("Respiratory Infection", 30) != AREA_PEDIATRIA

    def test_crianca_com_fratura_nao_vai_para_pediatria(self):
        # Pediatria só para condições respiratórias
        assert apply_area_rules("Fracture", 8) == AREA_ORTOPEDIA


# ---------------------------------------------------------------------------
# Fix #5 — keyword "infection" removida (não deve capturar condições genéricas)
# ---------------------------------------------------------------------------

class TestInfectionKeyword:
    def test_eye_infection_nao_vai_para_pneumologia(self):
        area = apply_area_rules("Eye Infection", 30)
        assert area != AREA_PNEUMOLOGIA

    def test_wound_infection_nao_vai_para_pneumologia(self):
        area = apply_area_rules("Wound Infection", 40)
        assert area != AREA_PNEUMOLOGIA

    def test_respiratory_infection_ainda_funciona(self):
        # "respiratory" basta para capturar o caso correto
        assert apply_area_rules("Respiratory Infection", 30) == AREA_PNEUMOLOGIA


# ---------------------------------------------------------------------------
# Normalização de entrada (case-insensitive, espaços extras)
# ---------------------------------------------------------------------------

class TestNormalizacao:
    def test_case_insensitive(self):
        assert apply_area_rules("STROKE", 40) == apply_area_rules("stroke", 40)

    def test_espacos_extras_ignorados(self):
        assert apply_area_rules("  Heart Disease  ", 45) == AREA_CARDIOLOGIA
