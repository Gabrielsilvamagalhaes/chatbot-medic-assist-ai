"""
Script de treinamento e avaliação dos modelos de classificação (B15–B20).

Treina Árvore de Decisão (B15) e Random Forest (B16) para prever:
  - area_recomendada  (área hospitalar sugerida)
  - nivel_urgencia    (baixa, prioritario, emergencia)

Usa apenas Age, Gender e Condition como features — variáveis disponíveis
na triagem via chatbot. Colunas pós-atendimento (Procedure, Cost, Outcome)
são excluídas para evitar data leakage na inferência.

Métricas (B17–B19): acurácia, matriz de confusão e classification_report.
Modelos salvos em models/ (B20).

Uso:
    python src/train_model.py
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
    import joblib
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
except ImportError:
    print("scikit-learn não encontrado. Execute: pip install scikit-learn")
    sys.exit(1)

ROOT_DIR      = pathlib.Path(__file__).parent.parent
PROCESSED_DIR = ROOT_DIR / "dataset" / "processed"
MODELS_DIR    = ROOT_DIR / "models"
TRAIN_CSV     = PROCESSED_DIR / "hospital-data-train.csv"
TEST_CSV      = PROCESSED_DIR / "hospital-data-test.csv"
ENCODING_MAPS = PROCESSED_DIR / "encoding_maps.json"

# Features disponíveis na triagem — idade, gênero e condição principal
FEATURE_COLS = ["Age", "Gender", "Condition"]

# Colunas-alvo: dois problemas de classificação independentes
TARGET_AREA    = "area_recomendada"
TARGET_URGENCY = "nivel_urgencia"

# Semente fixa para reprodutibilidade entre execuções e comparação DT vs RF
RANDOM_STATE = 42

# Nomes dos algoritmos para arquivos e metadados
ALGO_DECISION_TREE = "decision_tree"
ALGO_RANDOM_FOREST = "random_forest"


def _load_splits() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Carrega conjuntos de treino e teste gerados pelo B11."""
    if not TRAIN_CSV.exists() or not TEST_CSV.exists():
        print("Conjuntos treino/teste não encontrados. Execute: python src/split_dataset.py")
        sys.exit(1)
    return pd.read_csv(TRAIN_CSV), pd.read_csv(TEST_CSV)


def _evaluate_model(
    model_area,
    model_urgency,
    X_test: pd.DataFrame,
    y_area_test: pd.Series,
    y_urgency_test: pd.Series,
) -> dict:
    """
    Calcula métricas de avaliação (B17–B19) no conjunto de teste.

    Retorna dict com acurácia, matrizes de confusão e classification_report
    para área e urgência — serializável em JSON.
    """
    pred_area    = model_area.predict(X_test)
    pred_urgency = model_urgency.predict(X_test)

    acc_area    = accuracy_score(y_area_test, pred_area)
    acc_urgency = accuracy_score(y_urgency_test, pred_urgency)

    return {
        "accuracy": {
            "area_recomendada": round(float(acc_area), 4),
            "nivel_urgencia":   round(float(acc_urgency), 4),
            "media":            round(float((acc_area + acc_urgency) / 2), 4),
        },
        "confusion_matrix": {
            "area_recomendada": confusion_matrix(y_area_test, pred_area).tolist(),
            "nivel_urgencia":   confusion_matrix(y_urgency_test, pred_urgency).tolist(),
        },
        "classification_report": {
            "area_recomendada": classification_report(
                y_area_test, pred_area, output_dict=True, zero_division=0
            ),
            "nivel_urgencia": classification_report(
                y_urgency_test, pred_urgency, output_dict=True, zero_division=0
            ),
        },
    }


def _train_and_save(
    algo_name: str,
    model_area,
    model_urgency,
    X_train: pd.DataFrame,
    y_area_train: pd.Series,
    y_urgency_train: pd.Series,
    X_test: pd.DataFrame,
    y_area_test: pd.Series,
    y_urgency_test: pd.Series,
) -> dict:
    """
    Treina par de modelos (área + urgência), salva .joblib e retorna métricas.
    """
    model_area.fit(X_train, y_area_train)
    model_urgency.fit(X_train, y_urgency_train)

    joblib.dump(model_area,    MODELS_DIR / f"{algo_name}_area.joblib")
    joblib.dump(model_urgency, MODELS_DIR / f"{algo_name}_urgency.joblib")

    metrics = _evaluate_model(model_area, model_urgency, X_test, y_area_test, y_urgency_test)
    metrics["algorithm"] = algo_name

    metrics_path = MODELS_DIR / f"metrics_{algo_name}.json"
    with open(metrics_path, "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2, ensure_ascii=False)

    return metrics


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    train_df, test_df = _load_splits()

    X_train = train_df[FEATURE_COLS]
    X_test  = test_df[FEATURE_COLS]
    y_area_train    = train_df[TARGET_AREA]
    y_urgency_train = train_df[TARGET_URGENCY]
    y_area_test     = test_df[TARGET_AREA]
    y_urgency_test  = test_df[TARGET_URGENCY]

    # B15 — Árvore de Decisão: interpretável, adequada para apresentação A3
    dt_area = DecisionTreeClassifier(random_state=RANDOM_STATE)
    dt_urgency = DecisionTreeClassifier(random_state=RANDOM_STATE)
    metrics_dt = _train_and_save(
        ALGO_DECISION_TREE, dt_area, dt_urgency,
        X_train, y_area_train, y_urgency_train,
        X_test, y_area_test, y_urgency_test,
    )

    # B16 — Random Forest: ensemble para comparação com Árvore de Decisão
    rf_area = RandomForestClassifier(random_state=RANDOM_STATE, n_estimators=100)
    rf_urgency = RandomForestClassifier(random_state=RANDOM_STATE, n_estimators=100)
    metrics_rf = _train_and_save(
        ALGO_RANDOM_FOREST, rf_area, rf_urgency,
        X_train, y_area_train, y_urgency_train,
        X_test, y_area_test, y_urgency_test,
    )

    # Seleciona algoritmo com maior acurácia média para uso no chatbot (B21)
    best = (
        ALGO_DECISION_TREE
        if metrics_dt["accuracy"]["media"] >= metrics_rf["accuracy"]["media"]
        else ALGO_RANDOM_FOREST
    )

    metadata = {
        "feature_columns": FEATURE_COLS,
        "target_columns": [TARGET_AREA, TARGET_URGENCY],
        "random_state": RANDOM_STATE,
        "best_algorithm": best,
        "comparison": {
            ALGO_DECISION_TREE: metrics_dt["accuracy"],
            ALGO_RANDOM_FOREST: metrics_rf["accuracy"],
        },
        "encoding_maps_file": str(ENCODING_MAPS.name),
    }

    with open(MODELS_DIR / "model_metadata.json", "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2, ensure_ascii=False)

    print("Modelos treinados e salvos em:", MODELS_DIR)
    print(f"  Árvore de Decisão — acurácia média: {metrics_dt['accuracy']['media']}")
    print(f"  Random Forest      — acurácia média: {metrics_rf['accuracy']['media']}")
    print(f"  Algoritmo selecionado para o chatbot: {best}")


if __name__ == "__main__":
    main()
