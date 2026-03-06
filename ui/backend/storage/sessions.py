"""
JSON file-based session storage.
Sessions saved to workspace/<project>/_system/sessions/<session_id>.json
"""

import json
import uuid
from datetime import datetime
from pathlib import Path


class SessionStore:

    def __init__(self, workspace_dir: Path, project: str):
        self.sessions_dir = workspace_dir / project / "_system" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def create(self, metadata: dict | None = None) -> dict:
        session_id = str(uuid.uuid4())
        session = {
            "id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "messages": [],
            "metadata": metadata or {},
        }
        self._save(session)
        return session

    def get(self, session_id: str) -> dict | None:
        path = self.sessions_dir / f"{session_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def append_message(self, session_id: str, role: str, content: str) -> dict | None:
        session = self.get(session_id)
        if session is None:
            return None
        session["messages"].append({
            "role": role,
            "content": content,
            "ts": datetime.utcnow().isoformat(),
        })
        session["updated_at"] = datetime.utcnow().isoformat()
        self._save(session)
        return session

    def list_sessions(self) -> list[dict]:
        sessions = []
        for path in sorted(self.sessions_dir.glob("*.json"), reverse=True):
            try:
                s = json.loads(path.read_text())
                msgs = s.get("messages", [])
                first_user = next((m["content"] for m in msgs if m["role"] == "user"), None)
                if first_user:
                    title = first_user[:60] + ("…" if len(first_user) > 60 else "")
                else:
                    title = s["id"][:12]
                sessions.append({
                    "id": s["id"],
                    "created_at": s["created_at"],
                    "message_count": len(msgs),
                    "title": title,
                })
            except Exception:
                pass
        return sessions

    def _save(self, session: dict) -> None:
        path = self.sessions_dir / f"{session['id']}.json"
        path.write_text(json.dumps(session, indent=2))
