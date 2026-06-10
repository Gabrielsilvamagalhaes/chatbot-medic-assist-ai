BOAS_VINDAS = """
============================================================
     BEM-VINDO AO MEDIC ASSIST AI - TRIAGEM HOSPITALAR
============================================================

Olá! Sou o Medic Assist AI, um assistente de apoio à triagem
hospitalar inicial.

AVISO IMPORTANTE:
  - Este sistema NÃO realiza diagnósticos médicos.
  - Este sistema NÃO prescreve medicamentos.
  - Este sistema NÃO substitui avaliação médica profissional.
  - As sugestões geradas são apenas um apoio inicial ao
    encaminhamento. A decisão clínica final cabe sempre a
    um profissional de saúde.

Em caso de emergência com risco de vida, ligue imediatamente
para o SAMU (192) ou vá ao pronto-socorro mais próximo.

============================================================
Vamos começar a triagem. Por favor, responda às perguntas.
============================================================
"""

ENCERRAMENTO = """
============================================================
           TRIAGEM INICIAL CONCLUÍDA
============================================================

Obrigado por usar o Medic Assist AI.

Lembre-se:
  - Esta triagem é apenas uma orientação inicial.
  - Procure atendimento médico presencial para avaliação
    clínica completa.
  - Em emergências, não aguarde: ligue 192 (SAMU).

Cuide-se bem.
============================================================
"""

AVISO_EMERGENCIA = """
⚠  ATENÇÃO: Com base nas informações fornecidas, sua
   condição pode exigir atendimento IMEDIATO.

   Dirija-se ao pronto-socorro mais próximo ou ligue
   para o SAMU: 192.

   NÃO aguarde consulta agendada neste caso.
"""

AVISO_RESULTADO = """
------------------------------------------------------------
IMPORTANTE: A sugestão abaixo é gerada automaticamente com
base nas informações que você forneceu. Ela NÃO representa
um diagnóstico médico e NÃO deve substituir a avaliação de
um profissional de saúde.
------------------------------------------------------------
"""

# Feedback exibido entre a coleta de dados e a exibição do resultado (B22)
MENSAGEM_ANALISANDO = """
⏳  Analisando suas informações com o modelo de IA...
    Por favor, aguarde um momento.
"""

# Orientação de ação por nível de urgência — linguagem acessível, sem diagnóstico
ORIENTACAO_URGENCIA: dict[str, str] = {
    "baixa": (
        "Você pode agendar uma consulta ou procurar atendimento "
        "ambulatorial. Não é necessário ir ao pronto-socorro neste momento."
    ),
    "prioritario": (
        "Procure atendimento presencial em breve. "
        "Considere ir a uma unidade de saúde ou pronto atendimento hoje."
    ),
    "emergencia": (
        "Sua condição pode exigir atendimento imediato. "
        "Dirija-se ao pronto-socorro ou ligue 192 (SAMU)."
    ),
}

# Rótulos amigáveis para exibição da fonte da recomendação
FONTE_MODELO_IA = "Sugestão gerada pelo modelo de IA"
FONTE_REGRAS_SEGURANCA = "Avaliação por regras de segurança (emergência detectada)"
FONTE_REGRAS_FALLBACK = "Sugestão por regras clínicas (modelo não disponível)"
