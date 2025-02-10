from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class GitInfo:
    repository_url: str
    branch: str
    sparse_checkout_paths: List[str]

@dataclass
class CodeMatch:
    keyword: str
    line_number: int
    line_content: str
    context: str

@dataclass
class ProjectError:
    project: str
    url: str
    error_type: str
    error_message: str
    timestamp: datetime = datetime.now()

@dataclass
class SearchResult:
    server: str
    group: str
    project: str
    url: str
    matches: List[CodeMatch]
    git_info: Optional[GitInfo] = None
    error: Optional[ProjectError] = None
    timestamp: datetime = datetime.now()