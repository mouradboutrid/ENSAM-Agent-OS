from app.mcp.registry import ToolDefinition, ToolParameter, SecurityLevel

SCHEDULE_DATA = {
    "4A-S1": [
        {"day": "Monday", "time": "08:30-10:00", "course": "IA et Représentation", "professor": "Prof. Hajji", "room": "A201"},
        {"day": "Monday", "time": "10:15-11:45", "course": "Optimisation", "professor": "Prof. Benali", "room": "A202"},
        {"day": "Tuesday", "time": "08:30-10:00", "course": "Machine Learning", "professor": "Prof. Hajji", "room": "Lab3"},
        {"day": "Tuesday", "time": "14:00-15:30", "course": "Systèmes Embarqués", "professor": "Prof. Amrani", "room": "B105"},
        {"day": "Wednesday", "time": "10:15-11:45", "course": "Deep Learning", "professor": "Prof. Hajji", "room": "Lab3"},
        {"day": "Thursday", "time": "08:30-10:00", "course": "Robotique", "professor": "Prof. Fassi", "room": "Lab1"},
        {"day": "Thursday", "time": "14:00-17:00", "course": "Projet Intégré", "professor": "Prof. Hajji", "room": "Lab3"},
        {"day": "Friday", "time": "08:30-10:00", "course": "Anglais Technique", "professor": "Prof. Martin", "room": "C301"},
    ],
    "4A-S2": [
        {"day": "Monday", "time": "08:30-10:00", "course": "NLP", "professor": "Prof. Hajji", "room": "Lab3"},
        {"day": "Tuesday", "time": "10:15-11:45", "course": "Computer Vision", "professor": "Prof. Zaki", "room": "Lab2"},
        {"day": "Wednesday", "time": "08:30-10:00", "course": "Cloud Computing", "professor": "Prof. Idrissi", "room": "A203"},
        {"day": "Thursday", "time": "14:00-17:00", "course": "Projet de Recherche", "professor": "Prof. Hajji", "room": "Lab3"},
    ],
}


def lookup_schedule(program: str = "4A-S1", day: str = None, professor: str = None) -> list[dict]:
    schedule = SCHEDULE_DATA.get(program, [])
    if day:
        schedule = [s for s in schedule if s["day"].lower() == day.lower()]
    if professor:
        schedule = [s for s in schedule if professor.lower() in s["professor"].lower()]
    return schedule


def get_schedule_tool() -> ToolDefinition:
    return ToolDefinition(
        tool_id="schedule_lookup",
        name="Course Schedule Lookup",
        description="Look up course schedules by program, day, or professor at ENSAM Meknès",
        parameters=[
            ToolParameter(name="program", type="string", description="Program code (e.g., 4A-S1, 4A-S2)", required=False, default="4A-S1"),
            ToolParameter(name="day", type="string", description="Day of the week", required=False),
            ToolParameter(name="professor", type="string", description="Professor name filter", required=False),
        ],
        security_level=SecurityLevel.STUDENT,
        server_name="schedule_server",
        tags=["schedule", "courses", "timetable"],
        handler=lookup_schedule,
    )
