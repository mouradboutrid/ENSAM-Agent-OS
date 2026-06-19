from app.agents.base import BaseAgent


class ProjectAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(
            agent_id="project",
            name="Project Coordinator",
            description="Project planning, Gantt charts, software architecture, UML diagram layouts (generating Mermaid.js code blocks), MVC architectures, task planning. Gestion de projet, diagramme de Gantt, architecture logicielle, diagrammes UML, Mermaid, MVC, planification de tâches.",
            supported_tasks=["project_planning", "uml_generation", "architecture_design", "task_scheduling"],
            **kwargs,
        )

    def get_system_prompt(self) -> str:
        return (
            "You are a Project Coordinator and Software Architect assistant at ENSAM Meknès. "
            "You help engineering students plan their projects, design software architectures, and generate UML diagrams. "
            "When requested to create or describe diagrams (like UML class, sequence, activity diagrams, workflows, or architectures):\n"
            "- ALWAYS output clean, valid Mermaid.js code blocks starting with ```mermaid and ending with ```\n"
            "- Provide step-by-step project plans, task breakdowns, resource allocations, or Gantt charts\n"
            "- Explain architectural patterns such as MVC, MVVM, Microservices, and Spring Boot designs\n"
            "- Answer in the same language as the user (French or English)\n"
            "- Keep explanations clear, structured, and engineering-focused"
        )

    def _should_use_rag(self, query: str) -> bool:
        return True

    async def _select_tools(self, query: str) -> list[tuple[str, dict]]:
        # Project agent can search documents if needed
        return [("document_search", {"query": query[:100]})]

    def get_exemplars(self) -> list[str]:
        return [
            "Create a project plan for my engineering project",
            "What UML diagram should I use for a banking app?",
            "Concevoir une architecture MVC en Spring Boot",
            "Planifier les tâches et créer un diagramme de Gantt",
            "Generate a sequence diagram for user login",
            "Mermaid code for an entity relationship diagram",
            "How to schedule tasks for a 3-month engineering team project",
            "Dessiner un diagramme de cas d'utilisation pour une bibliothèque",
            "UML class diagram for polymorphism"
        ]
