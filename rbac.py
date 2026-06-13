ROLE_ACCESS = {
    "employee": ["general"],
    "manager": ["general", "operations"],
    "compliance_officer": ["general", "operations", "compliance"],
    "admin": ["*"]
}

DOCUMENT_TAGS = {
    "compliance.pdf": "compliance",
    "employees.csv": "general",
    "incidents.csv": "operations",
    "audit_logs.json": "operations"
}


def has_access(role, doc_name):
    permission = DOCUMENT_TAGS.get(doc_name, "general")

    if "*" in ROLE_ACCESS[role]:
        return True

    return permission in ROLE_ACCESS[role]