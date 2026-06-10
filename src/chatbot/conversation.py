from .messages import (
    BOAS_VINDAS,
    ENCERRAMENTO,
    AVISO_EMERGENCIA,
    AVISO_RESULTADO,
    MENSAGEM_ANALISANDO,
    ORIENTACAO_URGENCIA,
    FONTE_MODELO_IA,
    FONTE_REGRAS_SEGURANCA,
    FONTE_REGRAS_FALLBACK,
)

CONDITIONS = [
    "Dor no Coração/Dor no Peito/ Heart Disease / Chest Pain",
    "AVC /Stroke / Neurological Issue",
    "Fratura/Fracture / Trauma",
    "Gripe / Dificuldade em Respirar / Flu / Respiratory Infection",
    "Complicacao na Gravidez/Pregnancy Complication",
    "Diabetes / High Glucose",
    "Doença de Pele/Skin Disease",
    "Other",
]

GENDERS = ["Masculino", "Feminino", "Outro / Prefiro não informar"]


def _ask(prompt: str, validator=None, error_msg: str = "Resposta inválida. Tente novamente.") -> str:
    while True:
        answer = input(prompt).strip()
        if validator is None or validator(answer):
            return answer
        print(f"  ⚠  {error_msg}\n")


def _ask_choice(prompt: str, options: list[str]) -> tuple[int, str]:
    n = len(options)
    print(prompt)
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")
    while True:
        raw = input("Sua escolha (número): ").strip()
        if raw.isdigit() and 1 <= int(raw) <= n:
            index = int(raw) - 1
            return index, options[index]
        print(f"  ⚠  Digite um número entre 1 e {n}.\n")


def _ask_yes_no(prompt: str) -> bool:
    while True:
        raw = input(f"{prompt} (s/n): ").strip().lower()
        if raw in ("s", "sim", "y", "yes"):
            return True
        if raw in ("n", "nao", "não", "no"):
            return False
        print("  ⚠  Responda com 's' para sim ou 'n' para não.\n")


def collect_patient_data() -> dict:
    """Run the guided conversation and return structured patient data."""
    print(BOAS_VINDAS)

    print("PASSO 1 de 4 — Dados básicos\n")
    age = int(_ask(
        "Qual é a sua idade? ",
        validator=lambda x: x.isdigit() and 0 < int(x) < 130,
        error_msg="Informe um número de idade válido (1–129).",
    ))

    _, gender = _ask_choice("\nQual é o seu gênero?", GENDERS)

    print("\nPASSO 2 de 4 — Condição principal\n")
    _, primary_condition = _ask_choice(
        "Qual melhor descreve o motivo da sua visita?", CONDITIONS
    )
    if primary_condition == "Other":
        primary_condition = _ask("Descreva brevemente sua condição: ")

    print("\nPASSO 3 de 4 — Sintomas adicionais\n")
    has_fever = _ask_yes_no("Você está com febre?")
    has_intense_pain = _ask_yes_no("Você sente dor intensa?")
    has_difficulty_breathing = _ask_yes_no("Você tem dificuldade para respirar?")
    is_conscious = _ask_yes_no("Você está consciente e consegue responder sozinho?")

    print("\nPASSO 4 de 4 — Histórico rápido\n")
    symptom_duration_days = int(_ask(
        "Há quantos dias você está com esses sintomas? ",
        validator=lambda x: x.isdigit() and int(x) >= 0,
        error_msg="Informe um número de dias válido (0 ou mais).",
    ))

    has_chronic_disease = _ask_yes_no("Você possui alguma doença crônica diagnosticada?")
    chronic_detail = _ask("Qual(is) doença(s) crônica(s)? ") if has_chronic_disease else ""

    return {
        "age": age,
        "gender": gender,
        "primary_condition": primary_condition,
        "has_fever": has_fever,
        "has_intense_pain": has_intense_pain,
        "has_difficulty_breathing": has_difficulty_breathing,
        "is_conscious": is_conscious,
        "symptom_duration_days": symptom_duration_days,
        "has_chronic_disease": has_chronic_disease,
        "chronic_detail": chronic_detail,
    }


def _format_source_label(source: str) -> str:
    """Converte código interno da fonte em texto amigável para o paciente."""
    if source.startswith("modelo_ia"):
        return f"{FONTE_MODELO_IA} ({source.split('(')[1].rstrip(')')})" if "(" in source else FONTE_MODELO_IA
    if source == "regras_seguranca":
        return FONTE_REGRAS_SEGURANCA
    return FONTE_REGRAS_FALLBACK


def display_result(
    patient_data: dict,
    recommended_area: str,
    urgency_level: str,
    source: str = "regras_fallback",
) -> None:
    """Exibe resultado da triagem com disclaimers de segurança e orientação clara (B22)."""
    print(AVISO_RESULTADO)

    print("=" * 60)
    print("  SUA TRIAGEM — RESUMO")
    print("=" * 60)

    print("\n  Dados informados:")
    print(f"    Idade              : {patient_data['age']} anos")
    print(f"    Gênero             : {patient_data['gender']}")
    print(f"    Condição principal : {patient_data['primary_condition']}")
    print(f"    Duração sintomas   : {patient_data['symptom_duration_days']} dia(s)")
    if patient_data["has_chronic_disease"]:
        print(f"    Doença crônica     : {patient_data['chronic_detail']}")

    urgency_key = urgency_level.lower()
    urgency_label = urgency_key.upper()

    print("\n  Recomendação:")
    print(f"    Área sugerida      : {recommended_area}")
    print(f"    Nível de urgência  : {urgency_label}")
    print(f"    Origem             : {_format_source_label(source)}")

    orientacao = ORIENTACAO_URGENCIA.get(urgency_key, "")
    if orientacao:
        print(f"\n  O que fazer agora:")
        print(f"    {orientacao}")

    if urgency_key == "emergencia":
        print(AVISO_EMERGENCIA)

    print(ENCERRAMENTO)


def build_triage_summary(
    patient_data: dict,
    recommended_area: str,
    urgency_level: str,
    source: str = "regras_fallback",
) -> dict:
    """Retorna dict estruturado para revisão humana da triagem."""
    return {
        "patient": {
            "age": patient_data["age"],
            "gender": patient_data["gender"],
            "primary_condition": patient_data["primary_condition"],
            "symptom_duration_days": patient_data["symptom_duration_days"],
            "has_fever": patient_data["has_fever"],
            "has_intense_pain": patient_data["has_intense_pain"],
            "has_difficulty_breathing": patient_data["has_difficulty_breathing"],
            "is_conscious": patient_data["is_conscious"],
            "has_chronic_disease": patient_data["has_chronic_disease"],
            "chronic_detail": patient_data["chronic_detail"],
        },
        "recommendation": {
            "area_recomendada": recommended_area,
            "nivel_urgencia": urgency_level,
        },
        "prediction_source": source,
        "disclaimer": (
            "Triagem gerada automaticamente pelo Medic Assist AI. "
            "Não representa diagnóstico. Validação clínica obrigatória."
        ),
    }
