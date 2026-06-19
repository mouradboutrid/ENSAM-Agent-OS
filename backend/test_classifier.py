import sys
sys.path.insert(0, ".")

from app.agents.intent_classifier import IntentClassifier
from app.core.events import AgentCapability

class MockAgent:
    def __init__(self, agent_id, name, description, supported_tasks, exemplars):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.supported_tasks = supported_tasks
        self.exemplars = exemplars

    def get_capability(self):
        return AgentCapability(
            agent_id=self.agent_id,
            name=self.name,
            description=self.description,
            supported_tasks=self.supported_tasks
        )

    def get_exemplars(self):
        return self.exemplars

agents_map = {
    "tutor": MockAgent(
        "tutor", 
        "Tutor Agent", 
        "Academic tutoring for engineering concepts.", 
        ["question_answering", "study_guide"],
        [
            "What is polymorphism in Java?",
            "How does a binary search tree work?",
            "Explain how bubblesort works",
            "Bonjour, expliquez-moi les diagrammes de classes",
            "What is a class constructor?",
            "Explain backpropagation in neural networks"
        ]
    ),
    "admin": MockAgent(
        "admin", 
        "Admin Agent", 
        "University administrative duties.", 
        ["schedule_lookup", "grade_lookup"],
        [
            "When is my next exam?",
            "Quels sont mes horaires de cours?",
            "What is my grade in algorithms?",
            "What room is my class in?",
            "Show my transcript for last semester",
            "Check my schedule for tomorrow"
        ]
    ),
    "orientation": MockAgent(
        "orientation", 
        "Orientation Agent", 
        "Career and academic orientation advice.", 
        ["career_guidance", "internship_search"],
        [
            "What career paths exist for engineers?",
            "Je veux faire un stage en informatique",
            "How to write a resume for a software engineering job?",
            "Internship opportunities in mechatronics",
            "Specialization choices after second year"
        ]
    ),
    "synthesis": MockAgent(
        "synthesis", 
        "Synthesis Agent", 
        "Document synthesis and summarizing.", 
        ["document_synthesis", "topic_comparison"],
        [
            "Summarize chapter 3",
            "Compare Java and Python for beginners",
            "Generate a comparison report on mechatronics and AI",
            "Synthèse de ce cours d'informatique",
            "Write a study guide comparing these two concepts"
        ]
    ),
    "research": MockAgent(
        "research",
        "Research Agent",
        "Academic citation styling and scientific literature summaries.",
        ["citation_formatting", "paper_search"],
        [
            "Search for papers on deep learning",
            "Trouver des articles scientifiques sur l'optimisation",
            "How to cite a journal paper in APA format?",
            "Générer une citation BibTeX",
            "Formater une citation IEEE pour un article de conférence",
            "Aide-moi à rédiger l'état de l'art pour mon projet"
        ]
    ),
    "project": MockAgent(
        "project",
        "Project Coordinator",
        "Project planning and software architecture.",
        ["project_planning", "uml_generation"],
        [
            "Create a project plan for my engineering project",
            "What UML diagram should I use for a banking app?",
            "Concevoir une architecture MVC en Spring Boot",
            "Planifier les tâches et créer un diagramme de Gantt",
            "Generate a sequence diagram for user login",
            "Mermaid code for an entity relationship diagram"
        ]
    ),
}

print("Loading local sentence-transformer model (~120MB)...")
c = IntentClassifier(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
c.register_agents(agents_map)

tests = [
    ("What is polymorphism in Java?", "tutor"),
    ("When is my next exam?", "admin"),
    ("What career paths exist for engineers?", "orientation"),
    ("Summarize chapter 3", "synthesis"),
    ("Bonjour, expliquez-moi les diagrammes de classes", "tutor"),
    ("Quels sont mes horaires de cours?", "admin"),
    ("Je veux faire un stage en informatique", "orientation"),
    ("Compare Java and Python for beginners", "synthesis"),
    ("How does a binary search tree work?", "tutor"),
    ("What is my grade in algorithms?", "admin"),
    ("How to cite a journal paper in APA format?", "research"),
    ("Générer une citation BibTeX", "research"),
    ("Create a project plan for my engineering project", "project"),
    ("Mermaid code for an entity relationship diagram", "project"),
]

print("=" * 95)
print(f"{'STATUS':6s} {'CONF':6s} {'METHOD':16s} {'PREDICTED':14s} {'EXPECTED':14s} QUERY")
print("=" * 95)

correct = 0
for query, expected in tests:
    result = c.classify(query)
    ok = result.intent == expected
    correct += int(ok)
    status = "  OK" if ok else "MISS"
    print(f"{status:6s} {result.confidence:.2f}   {result.method:16s} {result.intent:14s} {expected:14s} {query}")

print("=" * 95)
print(f"Accuracy: {correct}/{len(tests)} ({correct/len(tests)*100:.0f}%)")
print(f"Method: {result.method}")
