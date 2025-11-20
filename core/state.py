import operator
from typing import Annotated, List, TypedDict, Dict

class ProjectState(TypedDict):
    user_request: str
    requirements: str
    tech_stack: str
    generated_code: Dict[str, str]
    qa_feedback: str
    qa_status: str
    iteration_count: int
    logs: Annotated[List[str], operator.add]