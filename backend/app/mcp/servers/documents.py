from app.mcp.registry import ToolDefinition, ToolParameter, SecurityLevel


def search_documents(query: str = "", file_type: str = None, limit: int = 10) -> dict:
    mock_docs = [
        {"id": "DOC001", "title": "Introduction to AI Agents", "type": "pdf", "author": "Prof. Hajji", "module": "IA et Représentation", "pages": 45},
        {"id": "DOC002", "title": "LangGraph Tutorial", "type": "pdf", "author": "Prof. Hajji", "module": "IA et Représentation", "pages": 30},
        {"id": "DOC003", "title": "RAG Architecture Patterns", "type": "md", "author": "Prof. Hajji", "module": "Deep Learning", "pages": 12},
        {"id": "DOC004", "title": "MCP Protocol Specification", "type": "pdf", "author": "Anthropic", "module": "IA et Représentation", "pages": 25},
        {"id": "DOC005", "title": "Exam 2024 - ML", "type": "pdf", "author": "Prof. Hajji", "module": "Machine Learning", "pages": 5},
        {"id": "DOC006", "title": "Student Project Guidelines", "type": "docx", "author": "Admin", "module": "General", "pages": 8},
    ]
    results = mock_docs
    if query:
        query_lower = query.lower()
        results = [d for d in results if query_lower in d["title"].lower() or query_lower in d.get("module", "").lower()]
    if file_type:
        results = [d for d in results if d["type"] == file_type]
    return {"results": results[:limit], "total": len(results)}


def get_documents_tool() -> ToolDefinition:
    return ToolDefinition(
        tool_id="document_search",
        name="Document Index Search",
        description="Search the university document index by query, file type, or module",
        parameters=[
            ToolParameter(name="query", type="string", description="Search query", required=False, default=""),
            ToolParameter(name="file_type", type="string", description="Filter by file type (pdf, docx, md)", required=False),
            ToolParameter(name="limit", type="integer", description="Max results to return", required=False, default=10),
        ],
        security_level=SecurityLevel.STUDENT,
        server_name="documents_server",
        tags=["documents", "search", "library"],
        handler=search_documents,
    )


def web_search_ddg(query: str) -> dict:
    from app.core.web_search import search_web_ddg
    result_str = search_web_ddg(query)
    return {"results": result_str}


def get_web_search_tool() -> ToolDefinition:
    return ToolDefinition(
        tool_id="web_search",
        name="Web Search Engine",
        description="Search the web (via DuckDuckGo) for real-time information, current events, facts, game seeds, or scientific articles",
        parameters=[
            ToolParameter(name="query", type="string", description="The search query to look up on the web", required=True),
        ],
        security_level=SecurityLevel.PUBLIC,
        server_name="documents_server",
        tags=["search", "web", "internet", "lookup"],
        handler=web_search_ddg,
    )
