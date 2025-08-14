import base64
import json
from typing import Optional, Tuple
import httpx

from app.config import settings

class JiraService:
	def __init__(self):
		self.base_url: Optional[str] = settings.JIRA_BASE_URL
		self.email: Optional[str] = settings.JIRA_EMAIL
		self.api_token: Optional[str] = settings.JIRA_API_TOKEN
		self.project_key: Optional[str] = settings.JIRA_PROJECT_KEY
		self.issue_type: str = settings.JIRA_ISSUE_TYPE

	def is_configured(self) -> bool:
		return all([self.base_url, self.email, self.api_token, self.project_key])

	def _auth_headers(self) -> dict:
		# Basic auth with email:token
		token = base64.b64encode(f"{self.email}:{self.api_token}".encode()).decode()
		return {
			"Authorization": f"Basic {token}",
			"Content-Type": "application/json"
		}

	async def create_issue(self, summary: str, description: str) -> Tuple[bool, Optional[str], Optional[str]]:
		"""Create a Jira issue. Returns (ok, key, error_message)."""
		if not self.is_configured():
			return False, None, "Jira not configured"

		payload = {
			"fields": {
				"project": {"key": self.project_key},
				"summary": summary,
				"description": description,
				"issuetype": {"name": self.issue_type}
			}
		}

		url = f"{self.base_url}/rest/api/3/issue"
		async with httpx.AsyncClient(timeout=30.0) as client:
			resp = await client.post(url, headers=self._auth_headers(), content=json.dumps(payload))
			if resp.status_code in (200, 201):
				data = resp.json()
				return True, data.get("key"), None
			else:
				try:
					data = resp.json()
					msg = data.get("errorMessages") or data.get("errors") or str(data)
				except Exception:
					msg = resp.text
				return False, None, f"{resp.status_code}: {msg}"
