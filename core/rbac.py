"""
Enterprise RBAC Engine
Enforces strict role-based access control for all data source queries
"""

import json
from typing import Optional
from dataclasses import dataclass

# DATA CLASSES 

@dataclass
class User:
    username: str
    name: str
    role: str
    dept: str

    @property
    def department(self):
        return self.dept

@dataclass
class AccessDecision:
    allowed: bool
    reason: str
    filtered_sources: list[str]
    redacted_fields: list[str]

# ─── RBAC ENGINE ──────────────────────────────────────────────────────────────

class RBACEngine:
    def __init__(self, policy_path: str = "data/rbac_policy.json"):
        with open(policy_path) as f:
            self.policy = json.load(f)
        self.roles = self.policy["roles"]
        self.users = self.policy["users"]

    def get_user(self, username: str) -> Optional[User]:
        if username not in self.users:
            return None
        u = self.users[username]
        return User(username=username, name=u["name"], role=u["role"], dept=u["dept"])

    def get_all_users(self) -> list[dict]:
        result = []
        for uname, udata in self.users.items():
            result.append({
                "username": uname,
                "name": udata["name"],
                "role": udata["role"],
                "dept": udata["dept"],
            })
        return result

    def get_role_config(self, role: str) -> dict:
        return self.roles.get(role, self.roles["employee"])

    def can_access_source(self, user: User, source_name: str) -> bool:
        role_cfg = self.get_role_config(user.role)
        allowed = role_cfg["allowed_sources"]
        denied = role_cfg["denied_sources"]

        # Executives get everything
        if "*" in allowed:
            return True

        # Check denied list first
        for denied_src in denied:
            if denied_src.lower() in source_name.lower():
                return False

        # Check allowed list
        for allowed_src in allowed:
            if allowed_src.lower() in source_name.lower() or allowed_src == "*":
                return True

        return False

    def can_access_chunk(self, user: User, source_name: str, source_file: str = "") -> bool:
        """
        Check a chunk against BOTH its display name and its filename.
        A match on either denied pattern blocks it; an allowed match on either lets it through.
        (Checking the two separately and OR-ing the results would let a denied source
        slip through whenever the other label happened to match an allowed pattern.)
        """
        role_cfg = self.get_role_config(user.role)
        allowed = role_cfg["allowed_sources"]
        denied = role_cfg["denied_sources"]
        if "*" in allowed:
            return True
        labels = [source_name.lower(), (source_file or "").lower()]
        if any(d.lower() in label for d in denied for label in labels):
            return False
        return any(a.lower() in label for a in allowed for label in labels)

    def filter_sources(self, user: User, candidate_sources: list[str]) -> list[str]:
        """Return only sources this user can access"""
        return [s for s in candidate_sources if self.can_access_source(user, s)]

    def check_query_sensitivity(self, user: User, query: str) -> AccessDecision:
        """
        Inspect the query for sensitive keywords and enforce access rules.
        Returns an AccessDecision with allowed/denied + reason.
        """
        role_cfg = self.get_role_config(user.role)
        query_lower = query.lower()

        sensitive_financial = ["salary", "revenue", "profit", "ebitda", "budget", "compensation", "financial", "earnings"]
        sensitive_hr = ["employee", "headcount", "hire", "termination", "payroll", "performance review"]
        sensitive_security = ["vulnerability", "cve", "incident", "breach", "audit log", "access log", "security event"]
        sensitive_compliance = ["audit", "compliance", "gdpr", "ccpa", "sox", "regulatory", "fine", "penalty"]

        redacted = []

        if any(kw in query_lower for kw in sensitive_financial):
            if not role_cfg["can_see_financials"] and user.role not in ["executive", "finance"]:
                return AccessDecision(
                    allowed=False,
                    reason=f"🔒 Access Denied: Your role ({user.role}) does not have permission to query financial data. Contact your manager or the Finance department.",
                    filtered_sources=[],
                    redacted_fields=[]
                )
            if not role_cfg["can_see_salaries"] and "salary" in query_lower:
                redacted.append("salary figures")

        if any(kw in query_lower for kw in sensitive_security):
            if not role_cfg["can_see_security_logs"] and user.role not in ["executive", "it_security"]:
                return AccessDecision(
                    allowed=False,
                    reason=f"🔒 Access Denied: Your role ({user.role}) does not have permission to query security logs or audit trails.",
                    filtered_sources=[],
                    redacted_fields=[]
                )

        return AccessDecision(
            allowed=True,
            reason="✅ Access granted",
            filtered_sources=[],
            redacted_fields=redacted
        )

    def get_permitted_sources_for_role(self, role: str) -> list[str]:
        role_cfg = self.get_role_config(role)
        if "*" in role_cfg["allowed_sources"]:
            return ["ALL SOURCES"]
        return role_cfg["allowed_sources"]

    def get_role_badge_color(self, role: str) -> str:
        colors = {
            "executive": "#FFD700",
            "finance": "#4CAF50",
            "hr": "#2196F3",
            "it_security": "#F44336",
            "operations": "#FF9800",
            "employee": "#9E9E9E",
        }
        return colors.get(role, "#9E9E9E")

    def get_role_description(self, role: str) -> str:
        return self.roles.get(role, {}).get("description", "Unknown role")