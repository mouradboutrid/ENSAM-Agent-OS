from app.agents.base import BaseAgent


class ResearchAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(
            agent_id="research",
            name="Research Agent",
            description="Academic citation styling, scientific literature summaries, and Google Scholar/web research queries. Bibliography, BibTeX, APA, IEEE, scientific paper writing, research methodology. Recherche scientifique, articles, résumés, citations bibliographiques, BibTeX, rédaction universitaire.",
            supported_tasks=["citation_formatting", "paper_search", "literature_summary", "academic_writing"],
            **kwargs,
        )

    def get_system_prompt(self) -> str:
        return (
            "You are an expert research assistant at ENSAM Meknès. "
            "You help engineering students with academic research, scientific literature, formatting citations (APA, IEEE, BibTeX, MLA), and writing research summaries. "
            "When answering questions:\n"
            "- Help find, analyze, and summarize academic sources and papers\n"
            "- Format bibliographic citations correctly according to requested styles (APA, IEEE, BibTeX, MLA, etc.)\n"
            "- Help draft academic texts, introduction sections, literature reviews, or conclusions\n"
            "- Reference provided materials when available\n"
            "- Answer in the same language as the user (French or English)\n"
            "- Structure long answers with clear sections, headers, and bullet points"
        )

    def _should_use_rag(self, query: str) -> bool:
        return True

    async def _select_tools(self, query: str) -> list[tuple[str, dict]]:
        query_lower = query.lower()
        if any(kw in query_lower for kw in ["pdf", "document", "cours", "paper", "article", "soutenance", "notes"]):
            return [("document_search", {"query": query[:100]})]
        return [("web_search", {"query": query})]

    def get_exemplars(self) -> list[str]:
        return [
            "Search for papers on deep learning",
            "Trouver des articles scientifiques sur l'optimisation",
            "How to cite a journal paper in APA format?",
            "Générer une citation BibTeX",
            "Formater une citation IEEE pour un article de conférence",
            "Aide-moi à rédiger l'état de l'art pour mon projet",
            "Summarize this research paper abstract",
            "Comment faire une bibliographie scientifique ?",
            "Provide APA citation for this book"
        ]
