from app.mcp.registry import ToolDefinition, ToolParameter, SecurityLevel

GRADES_DATA = {
    "STU001": {"name": "Ahmed Bennani", "program": "4A", "grades": {"IA et Représentation": 16.5, "Machine Learning": 14.0, "Deep Learning": 15.5, "Optimisation": 13.0, "Robotique": 17.0}},
    "STU002": {"name": "Fatima Zahra El Alami", "program": "4A", "grades": {"IA et Représentation": 18.0, "Machine Learning": 17.5, "Deep Learning": 16.0, "Optimisation": 15.5, "Robotique": 14.5}},
    "STU003": {"name": "Youssef Tazi", "program": "4A", "grades": {"IA et Représentation": 12.0, "Machine Learning": 11.5, "Deep Learning": 13.0, "Optimisation": 10.5, "Robotique": 14.0}},
    "STU004": {"name": "Imane Chraibi", "program": "4A", "grades": {"IA et Représentation": 15.0, "Machine Learning": 16.0, "Deep Learning": 14.5, "Optimisation": 17.0, "Robotique": 15.5}},
}


def lookup_grades(student_id: str = None, course: str = None) -> dict:
    if student_id:
        student = GRADES_DATA.get(student_id)
        if not student:
            return {"error": f"Student {student_id} not found"}
        if course:
            grade = student["grades"].get(course)
            return {"student_id": student_id, "name": student["name"], "course": course, "grade": grade}
        return {"student_id": student_id, **student}
    if course:
        results = []
        for sid, data in GRADES_DATA.items():
            if course in data["grades"]:
                results.append({"student_id": sid, "name": data["name"], "grade": data["grades"][course]})
        return {"course": course, "results": results, "average": sum(r["grade"] for r in results) / len(results) if results else 0}
    return {"total_students": len(GRADES_DATA)}


def calculate_gpa(student_id: str = None, grades: dict = None) -> dict:
    if not student_id and not grades:
        return {"error": "Please provide either a student_id or a dict of grades."}
        
    student_name = None
    if student_id:
        student = GRADES_DATA.get(student_id)
        if not student:
            return {"error": f"Student {student_id} not found"}
        grades = dict(student["grades"])
        student_name = student["name"]
        
    if not grades:
        return {"error": "No grades available to calculate GPA."}
        
    parsed_grades = {}
    for module, val in grades.items():
        try:
            parsed_grades[module] = float(val)
        except (ValueError, TypeError):
            parsed_grades[module] = 0.0
            
    total_score = sum(parsed_grades.values())
    count = len(parsed_grades)
    average = total_score / count if count > 0 else 0.0
    
    # ENSAM Meknes Rules:
    # Pass threshold: average >= 12.0
    # Elimination threshold: any single module grade < 7.0
    failed_modules = [module for module, grade in parsed_grades.items() if grade < 7.0]
    eliminated = len(failed_modules) > 0
    
    if average >= 12.0 and not eliminated:
        status = "Passed (Admis)"
    elif eliminated:
        status = "Failed due to elimination threshold (< 7.0 in some module(s))"
    else:
        status = "Failed (Ajourné) due to average below 12.0"
        
    return {
        "student_id": student_id,
        "name": student_name,
        "average": round(average, 2),
        "total_modules": count,
        "status": status,
        "failed_modules": failed_modules,
        "grades_evaluated": parsed_grades
    }


def get_grades_tool() -> ToolDefinition:
    return ToolDefinition(
        tool_id="grades_lookup",
        name="Student Grades Database",
        description="Look up student grades by student ID or course name",
        parameters=[
            ToolParameter(name="student_id", type="string", description="Student ID (e.g., STU001)", required=False),
            ToolParameter(name="course", type="string", description="Course name filter", required=False),
        ],
        security_level=SecurityLevel.FACULTY,
        server_name="grades_server",
        tags=["grades", "students", "academic"],
        handler=lookup_grades,
    )


def get_gpa_calculator_tool() -> ToolDefinition:
    return ToolDefinition(
        tool_id="gpa_calculator",
        name="ENSAM GPA Calculator",
        description="Calculate the student's weighted GPA and check if they pass or fail according to ENSAM rules (12.0/20 pass threshold, < 7.0/20 module failure/elimination threshold)",
        parameters=[
            ToolParameter(name="student_id", type="string", description="Student ID (e.g., STU001) to compute GPA from database", required=False),
            ToolParameter(name="grades", type="object", description="Custom dictionary of module grades to calculate (e.g. {'Math': 15, 'Physics': 8})", required=False),
        ],
        security_level=SecurityLevel.STUDENT,
        server_name="grades_server",
        tags=["grades", "gpa", "academic", "evaluation"],
        handler=calculate_gpa,
    )
