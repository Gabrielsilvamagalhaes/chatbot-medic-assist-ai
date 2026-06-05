# ---------------------------------------------------------------------------
# Áreas recomendadas
# ---------------------------------------------------------------------------
AREA_PRONTO_SOCORRO  = "Pronto-Socorro"
AREA_CARDIOLOGIA     = "Cardiologia / Pronto-Socorro"
AREA_NEUROLOGIA      = "Neurologia / Pronto-Socorro"
AREA_OBSTETRICIA     = "Obstetrícia / Pronto-Socorro"
AREA_CIRURGIA        = "Cirurgia / Pronto-Socorro"
AREA_ORTOPEDIA       = "Ortopedia / Pronto Atendimento"
AREA_PNEUMOLOGIA     = "Clínica Médica / Pneumologia"
AREA_PEDIATRIA       = "Pediatria"
AREA_ENDOCRINOLOGIA  = "Clínica Médica / Endocrinologia"
AREA_ONCOLOGIA       = "Oncologia / Clínica Médica"
AREA_DERMATOLOGIA    = "Dermatologia / Clínica Médica"
AREA_CLINICA_MEDICA  = "Clínica Médica"

# ---------------------------------------------------------------------------
# Keywords por condição — fonte única de verdade.
# silenciosa entre as duas tabelas de regras.
# ---------------------------------------------------------------------------
KEYWORDS_NEUROLOGICAL  = ("stroke", "neurological", "avc", "neurologico")
KEYWORDS_PREGNANCY     = ("pregnancy", "childbirth", "parto", "gravidez", "gestacao", "gestação", "obstetr")
KEYWORDS_APPENDICITIS  = ("appendicitis", "apendicite")
KEYWORDS_CARDIAC       = ("heart", "chest pain", "cardiac", "hypertension", "hipertensao", "hipertensão", "coração", "peito", "cardíaco")
KEYWORDS_FRACTURE      = ("fracture", "trauma", "fratura")
KEYWORDS_DIABETES      = ("diabetes", "glucose", "glicose", "glicemia")
KEYWORDS_CANCER        = ("cancer", "tumor", "oncol")
KEYWORDS_RESPIRATORY   = ("flu", "respiratory", "gripe", "respirar", "respiratorio", "respiratório")
KEYWORDS_SKIN          = ("skin", "pele", "dermat")

# ---------------------------------------------------------------------------
# Tabela de regras: (keywords, area)
# Ordem importa — condições mais específicas primeiro.
# ---------------------------------------------------------------------------
_AREA_RULES: list[tuple[tuple[str, ...], str]] = [
    (KEYWORDS_NEUROLOGICAL,  AREA_NEUROLOGIA),
    (KEYWORDS_PREGNANCY,     AREA_OBSTETRICIA),
    (KEYWORDS_APPENDICITIS,  AREA_CIRURGIA),
    (KEYWORDS_CARDIAC,       AREA_CARDIOLOGIA),
    (KEYWORDS_FRACTURE,      AREA_ORTOPEDIA),
    (KEYWORDS_DIABETES,      AREA_ENDOCRINOLOGIA),
    (KEYWORDS_CANCER,        AREA_ONCOLOGIA),
    (KEYWORDS_RESPIRATORY,   AREA_PNEUMOLOGIA),
    (KEYWORDS_SKIN,          AREA_DERMATOLOGIA),
]


def apply_area_rules(condition: str, age: int) -> str:
    """Retorna a area_recomendada para uma condição e idade."""
    normalized = condition.lower().strip()

    for keywords, area in _AREA_RULES:
        if any(keyword in normalized for keyword in keywords):
            if area == AREA_PNEUMOLOGIA and age < 12:
                return AREA_PEDIATRIA
            return area

    return AREA_CLINICA_MEDICA
