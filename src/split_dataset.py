"""
Script de separação treino/teste (B11).

Lê o dataset já codificado (hospital-data-encoded.csv, saída de B10) e
gera dois conjuntos para treinamento e avaliação do modelo de classificação:
  - hospital-data-train.csv  — 80% dos registros
  - hospital-data-test.csv   — 20% dos registros
  - split_metadata.json      — parâmetros e contagens para auditoria

Usamos o dataset codificado (e não o rotulado) porque B10 já converteu todas
as variáveis categóricas para numéricas — formato exigido pelos algoritmos
de classificação (B15/B16: Árvore de Decisão e Random Forest).

Uso:
    python src/split_dataset.py
"""

import json
import pathlib
import sys

try:
    import pandas as pd
except ImportError:
    print("pandas não encontrado. Execute: pip install pandas")
    sys.exit(1)

try:
    from sklearn.model_selection import train_test_split
except ImportError:
    print("scikit-learn não encontrado. Execute: pip install scikit-learn")
    sys.exit(1)

PROCESSED_DIR = pathlib.Path(__file__).parent.parent / "dataset" / "processed"
INPUT_CSV     = PROCESSED_DIR / "hospital-data-encoded.csv"
TRAIN_CSV     = PROCESSED_DIR / "hospital-data-train.csv"
TEST_CSV      = PROCESSED_DIR / "hospital-data-test.csv"
METADATA_JSON = PROCESSED_DIR / "split_metadata.json"

# Proporção fixa: 80% treino / 20% teste — padrão comum em classificação
TEST_SIZE = 0.2

# Semente fixa garante que a mesma divisão seja reproduzida em cada execução,
# essencial para comparar modelos (B15 vs B16) e reproduzir métricas (B17–B19).
RANDOM_STATE = 42

# Colunas-alvo do modelo — usadas na estratificação para manter a proporção
# de cada combinação área+urgência nos conjuntos de treino e teste.
STRATIFY_COLS = ["area_recomendada", "nivel_urgencia"]


def _build_stratify_key(df: pd.DataFrame) -> pd.Series:
    """
    Cria chave composta area_recomendada + nivel_urgencia.

    Estratificar em ambas as colunas-alvo evita que classes raras fiquem
    apenas no treino ou apenas no teste, o que distorceria as métricas.
    """
    return (
        df["area_recomendada"].astype(str)
        + "_"
        + df["nivel_urgencia"].astype(str)
    )


def main() -> None:
    df = pd.read_csv(INPUT_CSV)
    total_rows = len(df)

    # Chave de estratificação: cada combinação única de área e urgência
    stratify_key = _build_stratify_key(df)

    # Se alguma combinação tiver apenas 1 registro, stratify falha no sklearn.
    # Nesse caso, fazemos split sem estratificação (raro em datasets grandes).
    min_class_count = stratify_key.value_counts().min()
    stratify = stratify_key if min_class_count >= 2 else None

    train_df, test_df = train_test_split(
        df,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=stratify,
    )

    train_df.to_csv(TRAIN_CSV, index=False)
    test_df.to_csv(TEST_CSV, index=False)

    train_rows = len(train_df)
    test_rows = len(test_df)

    metadata = {
        "input_file": str(INPUT_CSV.name),
        "test_size": TEST_SIZE,
        "train_ratio": round(1 - TEST_SIZE, 2),
        "random_state": RANDOM_STATE,
        "stratify_columns": STRATIFY_COLS,
        "stratify_applied": stratify is not None,
        "total_rows": total_rows,
        "train_rows": train_rows,
        "test_rows": test_rows,
        "train_percent": round(train_rows / total_rows * 100, 1),
        "test_percent": round(test_rows / total_rows * 100, 1),
    }

    with open(METADATA_JSON, "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2, ensure_ascii=False)

    print(f"Dataset de treino salvo em: {TRAIN_CSV}")
    print(f"Dataset de teste salvo em:  {TEST_CSV}")
    print(f"Metadados salvos em:        {METADATA_JSON}")
    print(f"Total: {total_rows} | Treino: {train_rows} ({metadata['train_percent']}%) | Teste: {test_rows} ({metadata['test_percent']}%)")


if __name__ == "__main__":
    main()
