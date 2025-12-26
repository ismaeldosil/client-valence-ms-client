"""
Predefined responses for the mock agent.

Simulates a knowledge base with HR/company policy information.
"""

KNOWLEDGE_BASE: dict[str, dict] = {
    "vacaciones": {
        "text": (
            "La política de vacaciones permite 15 días hábiles al año. "
            "Los días no utilizados se pueden acumular hasta un máximo de 30 días. "
            "Las vacaciones deben solicitarse con al menos 2 semanas de anticipación "
            "a través del sistema de RRHH."
        ),
        "sources": ["hr-policies.pdf", "employee-handbook.pdf"],
        "confidence": 0.95,
    },
    "horario": {
        "text": (
            "El horario de trabajo es de 9:00 a 18:00, con una hora de almuerzo. "
            "Se permite flexibilidad de +/- 1 hora, previa coordinación con el manager. "
            "El horario core (obligatorio) es de 10:00 a 16:00."
        ),
        "sources": ["work-schedule.pdf"],
        "confidence": 0.92,
    },
    "remoto": {
        "text": (
            "La política de trabajo remoto permite hasta 3 días por semana "
            "desde casa. Se requiere coordinación previa con el equipo y "
            "disponibilidad durante horario core (10:00-16:00). "
            "El equipo debe tener al menos 2 días presenciales."
        ),
        "sources": ["remote-work-policy.pdf"],
        "confidence": 0.90,
    },
    "licencia": {
        "text": (
            "Las licencias médicas requieren certificado médico desde el primer día. "
            "Se tienen 3 días de licencia por enfermedad sin certificado al año. "
            "Para licencias mayores a 3 días, contactar a RRHH directamente."
        ),
        "sources": ["hr-policies.pdf"],
        "confidence": 0.88,
    },
    "beneficios": {
        "text": (
            "Los beneficios incluyen: seguro médico completo, seguro dental, "
            "membresía de gimnasio, capacitaciones pagadas, y bono anual por desempeño. "
            "Además, hay descuentos en comercios asociados."
        ),
        "sources": ["benefits-guide.pdf"],
        "confidence": 0.91,
    },
    "reembolso": {
        "text": (
            "Para solicitar reembolsos de gastos, debes cargar los comprobantes "
            "en el sistema de RRHH dentro de los 30 días posteriores al gasto. "
            "Los reembolsos se procesan en la siguiente quincena."
        ),
        "sources": ["expense-policy.pdf"],
        "confidence": 0.89,
    },
}

DEFAULT_RESPONSE: dict = {
    "text": (
        "No encontré información específica sobre eso en mi base de conocimiento. "
        "¿Podrías reformular tu pregunta o ser más específico? "
        "También puedes contactar a RRHH directamente para consultas especializadas."
    ),
    "sources": [],
    "confidence": 0.3,
}


def get_response_for_query(query: str) -> dict:
    """
    Search for a response in the knowledge base.

    Args:
        query: User's query text

    Returns:
        Dict with text, sources, confidence
    """
    query_lower = query.lower()

    for keyword, response in KNOWLEDGE_BASE.items():
        if keyword in query_lower:
            return response

    return DEFAULT_RESPONSE
