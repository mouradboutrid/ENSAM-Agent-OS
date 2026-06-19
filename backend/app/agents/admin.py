from app.agents.base import BaseAgent


class AdminAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(
            agent_id="admin",
            name="Administrative Agent",
            description="University administration, student records, grades, class schedules, classroom timetables, enrollments, exams, academic calendar. Administration universitaire, emploi du temps, notes, examens, inscription, salle de cours, bulletins, absences.",
            supported_tasks=["schedule_lookup", "grade_query", "enrollment_info", "procedure_help"],
            **kwargs,
        )

    def get_system_prompt(self) -> str:
        return (
            "You are an administrative assistant at ENSAM Meknès. "
            "You help students and faculty with administrative tasks including:\n"
            "- Course schedules and room assignments\n"
            "- Grade lookups and academic records\n"
            "- Enrollment procedures and deadlines\n"
            "- Institutional policies and regulations\n"
            "Be precise, professional, and always verify information from available tools before answering. "
            "If you cannot find the requested information, direct the user to the appropriate office. "
            "Answer in the same language as the user (French or English)."
        )

    def _should_use_rag(self, query: str) -> bool:
        return any(kw in query.lower() for kw in ["policy", "procedure", "regulation", "règlement", "inscription"])

    async def _select_tools(self, query: str) -> list[tuple[str, dict]]:
        tools = []
        query_lower = query.lower()
        if any(kw in query_lower for kw in ["schedule", "emploi", "cours", "horaire", "salle"]):
            tools.append(("schedule_lookup", {"program": "4A-S1"}))
        if any(kw in query_lower for kw in ["grade", "note", "résultat", "moyenne"]):
            tools.append(("grades_lookup", {}))
        return tools

    def get_exemplars(self) -> list[str]:
        return [
            "When is my next exam?",
            "Quels sont mes horaires de cours?",
            "What is my grade in algorithms?",
            "What room is my class in?",
            "Show my transcript for last semester",
            "Check my schedule for tomorrow",
            "Moyenne générale et notes de la session"
        ]
