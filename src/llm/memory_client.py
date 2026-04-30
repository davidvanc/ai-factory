"""
Client voor de Memory Service op de Storage VM.
Geen secrets in code - URL via environment variable.
"""
import os
import requests
from typing import Optional


class MemoryClient:
    def __init__(self):
        self.base_url = os.getenv("MEMORY_URL", "http://192.168.129.20:8765")
        self.timeout = 5  # snel timeouten - memory mag nooit de pipeline blokkeren

    def _safe_request(self, method: str, path: str, **kwargs) -> Optional[dict]:
        """Memory mag nooit de pipeline doen falen - bij fout gewoon None terug."""
        try:
            response = requests.request(
                method, f"{self.base_url}{path}",
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[memory] {method} {path} faalde: {e}")
            return None

    def add_project(self, project_name: str, task: str, description: str,
                    status: str, attempts: int, premium_used: bool = False,
                    metadata: dict = None) -> Optional[int]:
        result = self._safe_request("POST", "/projects", json={
            "project_name": project_name,
            "task": task,
            "description": description,
            "status": status,
            "attempts": attempts,
            "premium_used": premium_used,
            "metadata": metadata
        })
        return result.get("id") if result else None

    def add_lesson(self, category: str, pattern: str, fix: str = None,
                   project_id: int = None) -> Optional[int]:
        result = self._safe_request("POST", "/lessons", json={
            "project_id": project_id,
            "category": category,
            "pattern": pattern,
            "fix": fix
        })
        return result.get("id") if result else None

    def get_relevant_lessons(self, task: str, limit: int = 10) -> list:
        result = self._safe_request("GET", "/lessons/relevant",
                                     params={"task": task, "limit": limit})
        return result if result else []

    def get_stats(self) -> Optional[dict]:
        return self._safe_request("GET", "/stats")
