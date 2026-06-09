"""
Testes para o script de codificação de variáveis categóricas (B10).

Todos os testes seguem TDD: escritos ANTES da implementação em
src/encode_dataset.py.  O fixture `encoded_output` executa o script uma
única vez por sessão de testes e disponibiliza o DataFrame e os mapas
para todos os casos.
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

PROCESSED_DIR = pathlib.Path(__file__).parent.parent / "dataset" / "processed"
LABELED_CSV   = PROCESSED_DIR / "hospital-data-labeled.csv"
ENCODED_CSV   = PROCESSED_DIR / "hospital-data-encoded.csv"
MAPS_JSON     = PROCESSED_DIR / "encoding_maps.json"


@pytest.fixture(scope="module")
def encoded_output():
    """Executa encode_dataset.main() uma vez e retorna (DataFrame, mapas)."""
    if not LABELED_CSV.exists():
        pytest.skip("Dataset rotulado não encontrado — execute src/preprocess_dataset.py primeiro")

    from encode_dataset import main
    main()

    df   = pd.read_csv(ENCODED_CSV)
    with open(MAPS_JSON, encoding="utf-8") as fh:
        maps = json.load(fh)
    return df, maps


# ---------------------------------------------------------------------------
# Integridade do DataFrame de saída
# ---------------------------------------------------------------------------

class TestIntegridadeDataset:
    def test_nenhuma_linha_perdida(self, encoded_output):
        """O número de linhas deve ser igual ao do dataset de entrada."""
        df, _ = encoded_output
        df_orig = pd.read_csv(LABELED_CSV)
        assert len(df) == len(df_orig)

    def test_nenhuma_coluna_textual_na_saida(self, encoded_output):
        """Todas as colunas devem ser numéricas — nenhum dtype object."""
        df, _ = encoded_output
        colunas_texto = [c for c in df.columns if df[c].dtype == object]
        assert colunas_texto == [], f"Colunas ainda textuais: {colunas_texto}"

    def test_sem_valores_nulos(self, encoded_output):
        """Nenhuma célula pode ser NaN após a codificação."""
        df, _ = encoded_output
        nulos = df.isnull().sum().sum()
        assert nulos == 0, f"Encontrados {nulos} valores nulos"

    def test_patient_id_removido(self, encoded_output):
        """Patient_ID não tem valor preditivo e deve ser descartado."""
        df, _ = encoded_output
        assert "Patient_ID" not in df.columns


# ---------------------------------------------------------------------------
# Codificação ordinal de urgência
# ---------------------------------------------------------------------------

class TestCodificacaoUrgencia:
    def test_ordem_semantica_preservada(self):
        """baixa < prioritario < emergencia — invariante fundamental do sistema."""
        from encode_dataset import URGENCY_ORDINAL
        assert URGENCY_ORDINAL["baixa"] < URGENCY_ORDINAL["prioritario"] < URGENCY_ORDINAL["emergencia"]

    def test_valores_ordinais_corretos(self, encoded_output):
        """Valores numéricos de urgência devem ser 0, 1 e 2."""
        _, maps = encoded_output
        assert maps["nivel_urgencia"]["baixa"]       == 0
        assert maps["nivel_urgencia"]["prioritario"] == 1
        assert maps["nivel_urgencia"]["emergencia"]  == 2

    def test_apenas_tres_valores_de_urgencia(self, encoded_output):
        """O campo nivel_urgencia deve conter exatamente os valores 0, 1 e 2."""
        df, _ = encoded_output
        assert set(df["nivel_urgencia"].unique()) == {0, 1, 2}


# ---------------------------------------------------------------------------
# Codificação de colunas binárias
# ---------------------------------------------------------------------------

class TestCodificacaoBinaria:
    def test_gender_female_zero_male_um(self, encoded_output):
        """Female=0 e Male=1 — mapa determinístico."""
        _, maps = encoded_output
        assert maps["Gender"]["Female"] == 0
        assert maps["Gender"]["Male"]   == 1

    def test_readmission_no_zero_yes_um(self, encoded_output):
        """No=0, Yes=1 — mapa determinístico."""
        _, maps = encoded_output
        assert maps["Readmission"]["No"]  == 0
        assert maps["Readmission"]["Yes"] == 1

    def test_outcome_dois_valores_numericos(self, encoded_output):
        """Outcome deve ter exatamente 2 valores numéricos distintos."""
        df, _ = encoded_output
        assert len(df["Outcome"].unique()) == 2
        assert df["Outcome"].dtype != object


# ---------------------------------------------------------------------------
# Arquivo de mapeamentos (auditoria ética)
# ---------------------------------------------------------------------------

class TestArquivoMapeamentos:
    def test_arquivo_json_criado(self):
        """encoding_maps.json deve existir após a execução."""
        assert MAPS_JSON.exists()

    def test_mapas_contem_todas_colunas_codificadas(self, encoded_output):
        """Todas as colunas categóricas devem ter entrada no JSON de mapeamentos."""
        _, maps = encoded_output
        esperadas = {
            "Gender", "Readmission", "Outcome",
            "Condition", "Procedure",
            "nivel_urgencia", "area_recomendada",
        }
        faltando = esperadas - set(maps.keys())
        assert faltando == set(), f"Mapeamentos ausentes: {faltando}"

    def test_mapa_legivel_por_humanos(self, encoded_output):
        """Cada mapa deve ser um dict {str: int}, legível sem código."""
        _, maps = encoded_output
        for coluna, mapa in maps.items():
            assert isinstance(mapa, dict), f"Coluna {coluna}: mapa não é dict"
            for rotulo, codigo in mapa.items():
                assert isinstance(rotulo, str), f"{coluna}: chave '{rotulo}' não é string"
                assert isinstance(codigo, int), f"{coluna}: valor {codigo} não é int"
