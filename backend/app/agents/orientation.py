from app.agents.base import BaseAgent


class OrientationAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(
            agent_id="orientation",
            name="Orientation Agent",
            description="Career advice, job guidance, internships, CV, resume, professional opportunities, career path, post-graduation options. Orientation professionnelle, stages, emploi, CV, lettre de motivation, carrière, débouchés.",
            supported_tasks=["career_guidance", "program_recommendation", "skill_analysis", "orientation"],
            **kwargs,
        )

    def get_system_prompt(self) -> str:
        return (
            "You are a career orientation advisor at ENSAM Meknès. "
            "You help engineering students with:\n"
            "- Career path exploration in AI, Robotics, Mechatronics, and Industrial Engineering\n"
            "- Skill gap analysis based on their current coursework and career goals\n"
            "- Program and specialization recommendations\n"
            "- Industry trends and job market insights for Moroccan and international markets\n"
            "- Research orientation for students interested in graduate studies\n"
            "Be encouraging but realistic. Use knowledge graph data about the student when available. "
            "Answer in the same language as the user."
        )

    def _should_use_rag(self, query: str) -> bool:
        return True

    async def _select_tools(self, query: str) -> list[tuple[str, dict]]:
        tools = []
        query_lower = query.lower()
        if any(kw in query_lower for kw in ["grade", "note", "performance", "résultat"]):
            tools.append(("grades_lookup", {}))
        return tools

    def get_exemplars(self) -> list[str]:
        return [
            "What career paths exist for engineers?",
            "Je veux faire un stage en informatique",
            "How to write a resume for a software engineering job?",
            "Internship opportunities in mechatronics",
            "Specialization choices after second year",
            "What companies hire graduates from ENSAM?"
        ]


class SynthesisAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(
            agent_id="synthesis",
            name="Synthesis Agent",
            description="Document summarization, text synthesis, topic comparison, report generation, comparative analysis, summaries. Synthèse de documents, résumer un texte, comparaison, rapport, synthèse.",
            supported_tasks=["report_generation", "summary", "study_guide", "comparison"],
            **kwargs,
        )

    def get_system_prompt(self) -> str:
        return (
            "You are a research synthesis specialist at ENSAM Meknès. "
            "You excel at:\n"
            "- Creating comprehensive summaries from multiple documents\n"
            "- Generating structured study guides with key concepts, definitions, and examples\n"
            "- Comparing different approaches or methodologies\n"
            "- Writing well-structured reports in academic format\n"
            "Always structure your output with clear headers, bullet points, and numbered lists. "
            "Cite sources when available. Use markdown formatting for readability. "
            "Answer in the same language as the user."
        )

    def _should_use_rag(self, query: str) -> bool:
        return True

    async def _select_tools(self, query: str) -> list[tuple[str, dict]]:
        return [("document_search", {"query": query[:100]})]

    def get_exemplars(self) -> list[str]:
        return [
            "Summarize chapter 3",
            "Compare Java and Python for beginners",
            "Generate a comparison report on mechatronics and AI",
            "Synthèse de ce cours d'informatique",
            "Write a study guide comparing these two concepts",
            "Summarize this document"
        ]
