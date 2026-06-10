"""Entry point do Medic Assist AI. Execute: python src/main.py"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from chatbot.conversation import collect_patient_data, display_result, build_triage_summary
from chatbot.messages import MENSAGEM_ANALISANDO
from chatbot.model_predictor import predict_triage


def run() -> dict:
    # Etapa 1–4: coleta guiada dos dados do paciente
    patient_data = collect_patient_data()

    # Feedback de UX enquanto o modelo processa (B22)
    print(MENSAGEM_ANALISANDO)

    # Etapa 5: predição via modelo treinado + camada de segurança (B21)
    recommended_area, urgency_level, source = predict_triage(patient_data)

    display_result(patient_data, recommended_area, urgency_level, source)
    return build_triage_summary(patient_data, recommended_area, urgency_level, source)


if __name__ == "__main__":
    run()
