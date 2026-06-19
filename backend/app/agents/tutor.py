from app.agents.base import BaseAgent


class TutorAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(
            agent_id="tutor",
            name="Tutor Agent",
            description="Academic tutoring for computer science, programming, algorithms, data structures (binary search trees, sorting), math, engineering, Java, Python, UML diagrams, class diagrams, polymorphism. Tutorage académique, programmation, algorithmes, mathématiques, cours, devoirs.",
            supported_tasks=["question_answering", "study_guide", "concept_explanation", "exercise_help"],
            **kwargs,
        )

    def get_system_prompt(self) -> str:
        return (
            "You are an expert academic tutor at ENSAM Meknès (École Nationale Supérieure d'Arts et Métiers). "
            "You help students understand course material in AI, Machine Learning, Deep Learning, Robotics, and Engineering. "
            "When answering questions:\n"
            "- Use clear, pedagogical explanations adapted to engineering students\n"
            "- Reference provided source materials when available\n"
            "- Use mathematical notation when appropriate\n"
            "- Provide examples and analogies to clarify complex concepts\n"
            "- If you're unsure about something, say so honestly\n"
            "- Answer in the same language the student uses (French or English)\n"
            "- Structure long answers with headers and bullet points"
        )

    def _should_use_rag(self, query: str) -> bool:
        return True

    async def _select_tools(self, query: str) -> list[tuple[str, dict]]:
        tools = []
        query_lower = query.lower()
        if any(kw in query_lower for kw in ["schedule", "emploi", "cours", "horaire", "quand"]):
            tools.append(("schedule_lookup", {"program": "4A-S1"}))
        if any(kw in query_lower for kw in ["document", "pdf", "support", "cours", "resource"]):
            tools.append(("document_search", {"query": query[:100]}))
        return tools

    def get_exemplars(self) -> list[str]:
        return [
            "What is polymorphism in Java?",
            "How does a binary search tree work?",
            "Explain how bubblesort works",
            "Bonjour, expliquez-moi les diagrammes de classes",
            "What is a class constructor?",
            "Explain backpropagation in neural networks",
            "Explain the difference between class and object",
            "Help me with this programming exercise"
        ]
