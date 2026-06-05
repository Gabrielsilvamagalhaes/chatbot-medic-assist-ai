import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

import pytest

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

pytestmark = pytest.mark.skipif(not PANDAS_AVAILABLE, reason="pandas não instalado")


# ---------------------------------------------------------------------------
# Fix #2 — Age NaN não crasha o pipeline
# ---------------------------------------------------------------------------

class TestAgeNaNHandling:
    def test_age_nan_convertido_para_zero(self):
        import numpy as np
        from chatbot.recommended_area_rules import apply_area_rules
        from chatbot.urgency_triage_rules import get_base_urgency

        df = pd.DataFrame({
            "Condition": ["Flu", "Heart Disease"],
            "Age": [float("nan"), 45.0],
        })
        df["Age"] = pd.to_numeric(df["Age"], errors="coerce").fillna(0).astype(int)

        assert df["Age"].dtype == int or str(df["Age"].dtype) == "int64"
        assert df.loc[0, "Age"] == 0
        assert df.loc[1, "Age"] == 45

    def test_age_string_invalida_vira_zero(self):
        df = pd.DataFrame({"Age": ["N/A", "45", "unknown"]})
        df["Age"] = pd.to_numeric(df["Age"], errors="coerce").fillna(0).astype(int)

        assert df.loc[0, "Age"] == 0
        assert df.loc[1, "Age"] == 45
        assert df.loc[2, "Age"] == 0

    def test_pipeline_nao_crasha_com_age_nan(self):
        from chatbot.recommended_area_rules import apply_area_rules
        from chatbot.urgency_triage_rules import get_base_urgency

        df = pd.DataFrame({
            "Condition": ["Flu", "Diabetes"],
            "Age": [float("nan"), 50.0],
        })
        df["Age"] = pd.to_numeric(df["Age"], errors="coerce").fillna(0).astype(int)

        def label(row):
            area = apply_area_rules(str(row["Condition"]), int(row["Age"]))
            urgency = get_base_urgency(str(row["Condition"]))
            return pd.Series({"area_recomendada": area, "nivel_urgencia": urgency})

        result = df.apply(label, axis=1)
        assert len(result) == 2
        # age NaN → fillna(0) → age=0 < 12 → Flu vai para Pediatria (correto)
        assert result.loc[0, "area_recomendada"] == "Pediatria"
        assert result.loc[1, "nivel_urgencia"] == "prioritario"


# ---------------------------------------------------------------------------
# Integridade das colunas geradas no CSV processado
# ---------------------------------------------------------------------------

class TestDatasetProcessado:
    @pytest.fixture
    def csv_path(self):
        p = pathlib.Path(__file__).parent.parent / "dataset" / "processed" / "hospital-data-labeled.csv"
        if not p.exists():
            pytest.skip("Dataset processado não encontrado — execute src/preprocess_dataset.py primeiro")
        return p

    def test_colunas_geradas_existem(self, csv_path):
        df = pd.read_csv(csv_path)
        assert "area_recomendada" in df.columns
        assert "nivel_urgencia" in df.columns

    def test_sem_valores_nulos_nas_colunas_alvo(self, csv_path):
        df = pd.read_csv(csv_path)
        assert df["area_recomendada"].isna().sum() == 0
        assert df["nivel_urgencia"].isna().sum() == 0

    def test_urgencia_apenas_valores_validos(self, csv_path):
        df = pd.read_csv(csv_path)
        validos = {"baixa", "prioritario", "emergencia"}
        assert set(df["nivel_urgencia"].unique()).issubset(validos)

    def test_todas_especialidades_presentes(self, csv_path):
        df = pd.read_csv(csv_path)
        areas = set(df["area_recomendada"].unique())
        esperadas = {
            "Cardiologia / Pronto-Socorro",
            "Neurologia / Pronto-Socorro",
            "Ortopedia / Pronto Atendimento",
            "Obstetrícia / Pronto-Socorro",
        }
        assert esperadas.issubset(areas), f"Áreas faltando: {esperadas - areas}"
