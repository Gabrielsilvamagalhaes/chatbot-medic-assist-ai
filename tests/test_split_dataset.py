"""
Testes para o script de separação treino/teste (B11).

O fixture `split_output` executa split_dataset.main() uma vez por sessão
e disponibiliza os DataFrames de treino/teste e os metadados para todos os casos.
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
ENCODED_CSV   = PROCESSED_DIR / "hospital-data-encoded.csv"
TRAIN_CSV     = PROCESSED_DIR / "hospital-data-train.csv"
TEST_CSV      = PROCESSED_DIR / "hospital-data-test.csv"
METADATA_JSON = PROCESSED_DIR / "split_metadata.json"


@pytest.fixture(scope="module")
def split_output():
    """Executa split_dataset.main() uma vez e retorna (train, test, metadata)."""
    if not ENCODED_CSV.exists():
        pytest.skip("Dataset codificado não encontrado — execute src/encode_dataset.py primeiro")

    from split_dataset import main
    main()

    train_df = pd.read_csv(TRAIN_CSV)
    test_df  = pd.read_csv(TEST_CSV)
    with open(METADATA_JSON, encoding="utf-8") as fh:
        metadata = json.load(fh)
    return train_df, test_df, metadata


# ---------------------------------------------------------------------------
# Arquivos de saída
# ---------------------------------------------------------------------------

class TestArquivosSaida:
    def test_train_csv_criado(self):
        assert TRAIN_CSV.exists()

    def test_test_csv_criado(self):
        assert TEST_CSV.exists()

    def test_metadata_json_criado(self):
        assert METADATA_JSON.exists()


# ---------------------------------------------------------------------------
# Integridade dos conjuntos
# ---------------------------------------------------------------------------

class TestIntegridadeConjuntos:
    def test_soma_das_linhas_igual_ao_total(self, split_output):
        """Nenhum registro deve ser perdido na divisão."""
        train_df, test_df, metadata = split_output
        df_encoded = pd.read_csv(ENCODED_CSV)
        assert len(train_df) + len(test_df) == len(df_encoded)
        assert metadata["total_rows"] == len(df_encoded)

    def test_proporcao_aproximadamente_80_20(self, split_output):
        """Treino ~80% e teste ~20%, com tolerância de ±2 registros."""
        train_df, test_df, _ = split_output
        total = len(train_df) + len(test_df)
        expected_test = round(total * 0.2)
        assert abs(len(test_df) - expected_test) <= 2
        assert abs(len(train_df) - (total - expected_test)) <= 2

    def test_colunas_preservadas(self, split_output):
        """Treino e teste devem ter as mesmas colunas do dataset codificado."""
        train_df, test_df, _ = split_output
        df_encoded = pd.read_csv(ENCODED_CSV)
        assert list(train_df.columns) == list(df_encoded.columns)
        assert list(test_df.columns) == list(df_encoded.columns)

    def test_sem_valores_nulos(self, split_output):
        """Nenhuma célula pode ser NaN após a divisão."""
        train_df, test_df, _ = split_output
        assert train_df.isnull().sum().sum() == 0
        assert test_df.isnull().sum().sum() == 0


# ---------------------------------------------------------------------------
# Metadados de auditoria
# ---------------------------------------------------------------------------

class TestMetadados:
    def test_campos_obrigatorios_presentes(self, split_output):
        _, _, metadata = split_output
        campos = {"test_size", "random_state", "train_rows", "test_rows", "total_rows"}
        faltando = campos - set(metadata.keys())
        assert faltando == set(), f"Campos ausentes: {faltando}"

    def test_test_size_correto(self, split_output):
        _, _, metadata = split_output
        assert metadata["test_size"] == 0.2

    def test_random_state_correto(self, split_output):
        _, _, metadata = split_output
        assert metadata["random_state"] == 42

    def test_contagens_consistentes(self, split_output):
        train_df, test_df, metadata = split_output
        assert metadata["train_rows"] == len(train_df)
        assert metadata["test_rows"] == len(test_df)
