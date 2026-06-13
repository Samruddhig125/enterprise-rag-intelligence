"""
Synthetic Enterprise Dataset Generator
Generates realistic multi-format enterprise data for RAG demonstration
"""

import json
import csv
import os
import random
from datetime import datetime, timedelta

#  DIRECTORY SETUP 
os.makedirs("data/pdfs", exist_ok=True)
os.makedirs("data/csv", exist_ok=True)
os.makedirs("data/json_logs", exist_ok=True)
os.makedirs("data/reports", exist_ok=True)

#  1. SYNTHETIC DOCUMENT TEXTS (saved as .txt, treated as "PDF" content) ───

documents = {
    "data/pdfs/Q4_Financial_Report_2024.txt": """
ACME CORPORATION — Q4 2024 FINANCIAL REPORT
CONFIDENTIAL — FINANCE DEPARTMENT ONLY

Executive Summary
-----------------
ACME Corporation closed Q4 2024 with total revenue of $142.7 million, representing
a 23% year-over-year increase. Net profit margin improved to 18.4% from 15.1% in Q3.

Revenue Breakdown by Division:
- North America Enterprise: $67.3M (47.2% of total)
- EMEA Region: $38.9M (27.3% of total)
- APAC Region: $24.1M (16.9% of total)
- Emerging Markets: $12.4M (8.7% of total)

Key Financial Metrics:
- EBITDA: $38.2M (up 31% QoQ)
- Operating Cash Flow: $29.7M
- R&D Investment: $14.8M (10.4% of revenue)
- Customer Acquisition Cost: $3,240 (down 12% from Q3)

Budget Forecast for Q1 2025:
Total projected revenue: $155M–$162M
Approved headcount additions: 47 FTEs across Engineering and Sales
Capital expenditure approved: $8.3M for infrastructure modernization

Risk Factors:
- FX exposure in EMEA (~$4.2M risk at current rates)
- Supply chain delays affecting hardware division (est. $1.1M impact)
- Regulatory compliance costs in EU: est. $2.3M in Q1

Signed: CFO Sarah Mitchell
Date: January 15, 2025
""",

    "data/pdfs/HR_Policy_Handbook_2024.txt": """
ACME CORPORATION — HR POLICY HANDBOOK 2024
ALL EMPLOYEES

1. CODE OF CONDUCT
All employees are expected to maintain the highest standards of professional conduct.
Violations may result in disciplinary action up to and including termination.

2. COMPENSATION STRUCTURE
- Level 1 (Junior): $55,000 – $75,000
- Level 2 (Mid): $76,000 – $105,000
- Level 3 (Senior): $106,000 – $145,000
- Level 4 (Staff/Lead): $146,000 – $195,000
- Level 5 (Principal/Director): $196,000 – $260,000

Performance bonuses are paid annually in March, based on individual and company performance.
Target bonus percentages: L1: 5%, L2: 8%, L3: 12%, L4: 18%, L5: 25%

3. LEAVE POLICY
- Annual Leave: 20 days (increases to 25 after 3 years)
- Sick Leave: 10 days
- Parental Leave: 16 weeks primary, 6 weeks secondary caregiver
- Bereavement: 5 days

4. REMOTE WORK POLICY
Employees may work remotely up to 3 days per week. Manager approval required for
full-remote arrangements. Equipment stipend: $500/year for home office.

5. PERFORMANCE REVIEW CYCLE
Reviews are conducted bi-annually (June and December). Promotion decisions are made
in December cycle. 360-degree feedback introduced for L3 and above.

6. CONFIDENTIALITY
Employee compensation data is strictly confidential. Unauthorized disclosure is
grounds for immediate termination.

HR Director: James Okafor
Effective: January 1, 2024
""",

    "data/pdfs/IT_Security_Policy_2024.txt": """
ACME CORPORATION — INFORMATION SECURITY POLICY 2024
IT DEPARTMENT & ALL EMPLOYEES

1. ACCEPTABLE USE
Company systems are for business use only. Personal use is permitted in moderation
provided it does not interfere with work or violate this policy.

2. ACCESS CONTROL REQUIREMENTS
- All systems require MFA authentication as of Q3 2024
- Passwords must be 14+ characters, rotated every 90 days
- Privileged access requires additional approval via PAM system
- Zero-trust network access implemented for all remote connections

3. DATA CLASSIFICATION
CONFIDENTIAL: Financial records, PII, strategic plans, M&A activity
INTERNAL: Operational data, policies, general business data
PUBLIC: Marketing materials, public documentation

4. INCIDENT RESPONSE
Security incidents must be reported to security@acme.com within 1 hour of detection.
P1 (Critical): Response within 15 minutes, CISO notified immediately
P2 (High): Response within 2 hours
P3 (Medium): Response within 24 hours

5. VULNERABILITY MANAGEMENT
- Critical CVEs patched within 24 hours
- High CVEs patched within 7 days
- Monthly security scanning for all production systems
- Penetration testing conducted annually (Q2)

6. CLOUD SECURITY
All cloud workloads must be tagged with owner, environment, and data classification.
Untagged resources are automatically suspended after 72 hours.
AWS GuardDuty, SecurityHub, and Config Rules enforced across all accounts.

CISO: Dr. Priya Nair
Last Updated: November 2024
""",

    "data/reports/Operations_Summary_Dec2024.txt": """
ACME CORPORATION — OPERATIONS SUMMARY
DECEMBER 2024 | OPERATIONS DEPARTMENT

SYSTEM UPTIME & RELIABILITY
- Production API uptime: 99.94% (target: 99.9%) ✓
- Database cluster uptime: 99.97%
- CDN availability: 100%
- P50 API latency: 42ms | P95: 187ms | P99: 412ms

INCIDENTS THIS MONTH
- DEC-001: Database failover triggered Dec 3rd, 14:23 UTC. RCA: memory pressure on primary node.
  Duration: 4 minutes 12 seconds. Impact: ~0.3% of requests failed.
- DEC-002: Deployment pipeline stalled Dec 11th. Cause: third-party dependency version conflict.
  Duration: 2.5 hours. No customer impact.

CAPACITY PLANNING
Current utilization:
- Compute: 67% average (peak: 84% on Dec 20th)
- Storage: 71% (growing ~3.2TB/month)
- Network: 42% of provisioned bandwidth

Recommendations:
- Scale compute by 20% ahead of Q1 2025 growth projections
- Archive cold data (>18 months) to reduce storage costs by est. $12,400/month
- Evaluate CDN provider contract renewal in March 2025

DEPLOYMENTS
Total deployments in December: 47
Successful: 45 (95.7%)
Rolled back: 2 (DEC-DEP-031, DEC-DEP-039 — both due to integration test failures)

Head of Operations: Marcus Chen
Report Date: January 2, 2025
""",

    "data/reports/Compliance_Audit_2024.txt": """
ACME CORPORATION — ANNUAL COMPLIANCE AUDIT REPORT 2024
LEGAL & COMPLIANCE DEPARTMENT — STRICTLY CONFIDENTIAL

AUDIT SCOPE
This report covers SOC 2 Type II, ISO 27001, GDPR, and CCPA compliance for FY2024.

SOC 2 TYPE II RESULTS
Overall assessment: PASSED
- Security (CC6-CC9): Fully compliant
- Availability (A1): Fully compliant
- Confidentiality (C1): Minor finding — 3 instances of unencrypted data at rest in dev environment
- Processing Integrity (PI1): Fully compliant

GDPR COMPLIANCE
Status: Compliant with 2 observations
- Data subject request processing time: avg 18 days (target: <30 days) ✓
- Observation 1: Cookie consent banners need updating for new EU guidance (due Q1 2025)
- Observation 2: Data retention policy not enforced for 2 legacy systems (remediation in progress)

DSARs processed in 2024: 847 requests
Data breaches reported: 0 (zero reportable breaches)

CCPA COMPLIANCE
Status: Compliant
Opt-out requests processed: 1,203
Do-not-sell requests: 312

PENALTIES & REGULATORY ACTIONS
No fines or regulatory actions in FY2024.

Next audit scheduled: Q2 2025
Chief Compliance Officer: Amanda Torres
"""
}

for path, content in documents.items():
    with open(path, 'w') as f:
        f.write(content)

print(f"✓ Created {len(documents)} document files")

#  2. CSV / DATABASE DUMP 

employees = [
    ["EMP001", "Alice Chen", "Engineering", "Senior Engineer", "L3", 128000, "alice.chen@acme.com", "active", "2020-03-15"],
    ["EMP002", "Bob Martinez", "Finance", "Financial Analyst", "L2", 89000, "bob.martinez@acme.com", "active", "2021-07-22"],
    ["EMP003", "Carol Singh", "HR", "HR Business Partner", "L3", 112000, "carol.singh@acme.com", "active", "2019-11-01"],
    ["EMP004", "David Kim", "IT Security", "Security Engineer", "L3", 134000, "david.kim@acme.com", "active", "2020-06-10"],
    ["EMP005", "Eve Johnson", "Operations", "Operations Manager", "L4", 162000, "eve.johnson@acme.com", "active", "2018-02-28"],
    ["EMP006", "Frank Osei", "Engineering", "Staff Engineer", "L4", 178000, "frank.osei@acme.com", "active", "2017-09-14"],
    ["EMP007", "Grace Liu", "Legal", "Senior Counsel", "L4", 185000, "grace.liu@acme.com", "active", "2019-04-05"],
    ["EMP008", "Henry Park", "Sales", "Account Executive", "L2", 78000, "henry.park@acme.com", "active", "2022-01-10"],
    ["EMP009", "Iris Patel", "Engineering", "Junior Engineer", "L1", 68000, "iris.patel@acme.com", "active", "2023-08-21"],
    ["EMP010", "Jack Thompson", "Finance", "CFO", "L5", 245000, "jack.thompson@acme.com", "active", "2015-03-01"],
    ["EMP011", "Karen White", "IT", "System Administrator", "L2", 82000, "karen.white@acme.com", "active", "2021-05-17"],
    ["EMP012", "Leo Nakamura", "Engineering", "Principal Engineer", "L5", 228000, "leo.nakamura@acme.com", "active", "2016-07-19"],
    ["EMP013", "Maria Rodriguez", "HR", "HR Director", "L5", 215000, "maria.rodriguez@acme.com", "active", "2018-01-08"],
    ["EMP014", "Nathan Brown", "Sales", "VP Sales", "L5", 238000, "nathan.brown@acme.com", "active", "2017-11-30"],
    ["EMP015", "Olivia Davis", "Compliance", "Compliance Officer", "L3", 118000, "olivia.davis@acme.com", "active", "2020-09-22"],
]

with open("data/csv/employees.csv", 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["emp_id", "name", "department", "title", "level", "salary", "email", "status", "hire_date"])
    writer.writerows(employees)

# Vendor contracts
vendors = [
    ["VND001", "CloudScale AWS", "Infrastructure", 480000, "2024-01-01", "2025-12-31", "Active", "Renew Q4 2025"],
    ["VND002", "DataSecure Inc", "Security Tools", 120000, "2024-03-01", "2025-02-28", "Active", "Auto-renew"],
    ["VND003", "HR Platform SaaS", "HR Systems", 96000, "2023-06-01", "2025-05-31", "Active", "Review pricing"],
    ["VND004", "LegalDocs Pro", "Legal", 36000, "2024-01-01", "2024-12-31", "Expired", "Renewal pending"],
    ["VND005", "SalesForce CRM", "Sales", 240000, "2024-02-01", "2026-01-31", "Active", "Multi-year deal"],
    ["VND006", "MonitorPro", "Observability", 72000, "2024-04-01", "2025-03-31", "Active", "Evaluate alternatives"],
]

with open("data/csv/vendor_contracts.csv", 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["vendor_id", "vendor_name", "category", "annual_value_usd", "start_date", "end_date", "status", "notes"])
    writer.writerows(vendors)

# IT assets
assets = [
    ["ASSET001", "MacBook Pro 16 M3", "Laptop", "EMP001", "active", "2023-09-01", 3499],
    ["ASSET002", "MacBook Pro 14 M2", "Laptop", "EMP002", "active", "2022-11-15", 2199],
    ["ASSET003", "Dell Server R740", "Server", "IT-POOL", "active", "2021-06-01", 12500],
    ["ASSET004", "Cisco Switch 9300", "Network", "IT-POOL", "active", "2022-01-10", 8400],
    ["ASSET005", "iPhone 15 Pro", "Mobile", "EMP010", "active", "2023-10-01", 1199],
    ["ASSET006", "MacBook Air M2", "Laptop", "EMP009", "active", "2023-08-21", 1299],
    ["ASSET007", "YubiKey 5C", "Security Token", "EMP004", "active", "2024-01-05", 75],
    ["ASSET008", "4K Monitor LG 32", "Display", "EMP006", "active", "2022-03-14", 899],
]

with open("data/csv/it_assets.csv", 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["asset_id", "asset_name", "category", "assigned_to", "status", "purchase_date", "cost_usd"])
    writer.writerows(assets)

print("✓ Created 3 CSV files (employees, vendors, assets)")

#  3. JSON LOGS 

def rand_time(days_ago=30):
    base = datetime.now() - timedelta(days=random.randint(0, days_ago))
    return base.strftime("%Y-%m-%dT%H:%M:%SZ")

security_logs = []
events = [
    ("LOGIN_SUCCESS", "INFO", "User authenticated successfully"),
    ("LOGIN_FAILURE", "WARNING", "Invalid credentials provided"),
    ("MFA_CHALLENGE", "INFO", "MFA challenge issued"),
    ("PRIVILEGE_ESCALATION", "CRITICAL", "Privileged access requested via PAM"),
    ("DATA_EXPORT", "WARNING", "Large data export initiated"),
    ("CONFIG_CHANGE", "HIGH", "System configuration modified"),
    ("UNAUTHORIZED_ACCESS", "CRITICAL", "Access denied — insufficient permissions"),
    ("PASSWORD_RESET", "INFO", "Password reset completed"),
    ("API_RATE_LIMIT", "WARNING", "API rate limit exceeded"),
    ("VULNERABILITY_SCAN", "INFO", "Scheduled vulnerability scan completed"),
]

users_for_logs = ["alice.chen", "bob.martinez", "david.kim", "iris.patel", "henry.park", "karen.white"]
ips = ["10.0.1.12", "10.0.2.45", "192.168.1.100", "203.0.113.42", "10.0.3.88"]

for i in range(50):
    event_type, severity, desc = random.choice(events)
    log = {
        "log_id": f"SEC-{2024100 + i}",
        "timestamp": rand_time(60),
        "event_type": event_type,
        "severity": severity,
        "user": random.choice(users_for_logs),
        "source_ip": random.choice(ips),
        "description": desc,
        "resource": random.choice(["/api/v1/data", "/admin/config", "/reports/financial", "/hr/payroll", "vpn-gateway"]),
        "action_taken": "logged" if severity in ["INFO", "WARNING"] else "blocked_and_alerted",
        "geo": random.choice(["US-CA", "US-NY", "IN-MH", "GB-LDN", "DE-BER"]),
    }
    security_logs.append(log)

with open("data/json_logs/security_audit_logs.json", 'w') as f:
    json.dump(security_logs, f, indent=2)

# Application performance logs
app_logs = []
endpoints = ["/api/search", "/api/reports", "/api/users", "/api/analytics", "/api/export"]
for i in range(40):
    log = {
        "log_id": f"APP-{3000 + i}",
        "timestamp": rand_time(30),
        "service": random.choice(["api-gateway", "auth-service", "data-service", "report-engine"]),
        "endpoint": random.choice(endpoints),
        "method": random.choice(["GET", "POST", "GET", "GET"]),
        "status_code": random.choice([200, 200, 200, 200, 200, 401, 403, 429, 500]),
        "latency_ms": random.randint(15, 850),
        "user_id": random.choice(["EMP001", "EMP002", "EMP005", "EMP008", "EMP009"]),
        "request_size_bytes": random.randint(128, 4096),
        "response_size_bytes": random.randint(512, 51200),
        "trace_id": f"trace-{random.randint(100000, 999999)}",
    }
    app_logs.append(log)

with open("data/json_logs/application_logs.json", 'w') as f:
    json.dump(app_logs, f, indent=2)

print("✓ Created 2 JSON log files (security audit, application logs)")

#  4. RBAC POLICY 

rbac_policy = {
    "roles": {
        "executive": {
            "description": "C-suite and VP level — full access",
            "allowed_sources": ["*"],
            "denied_sources": [],
            "can_see_salaries": True,
            "can_see_financials": True,
            "can_see_compliance": True,
            "can_see_security_logs": True,
        },
        "finance": {
            "description": "Finance department employees",
            "allowed_sources": ["Q4_Financial_Report_2024", "employees", "vendor_contracts", "Compliance_Audit_2024"],
            "denied_sources": ["security_audit_logs", "IT_Security_Policy_2024"],
            "can_see_salaries": False,
            "can_see_financials": True,
            "can_see_compliance": True,
            "can_see_security_logs": False,
        },
        "hr": {
            "description": "Human Resources department",
            "allowed_sources": ["HR_Policy_Handbook_2024", "employees", "Compliance_Audit_2024"],
            "denied_sources": ["Q4_Financial_Report_2024", "security_audit_logs"],
            "can_see_salaries": True,
            "can_see_financials": False,
            "can_see_compliance": True,
            "can_see_security_logs": False,
        },
        "it_security": {
            "description": "IT and Security teams",
            "allowed_sources": ["IT_Security_Policy_2024", "security_audit_logs", "application_logs", "it_assets", "Operations_Summary_Dec2024"],
            "denied_sources": ["Q4_Financial_Report_2024", "HR_Policy_Handbook_2024"],
            "can_see_salaries": False,
            "can_see_financials": False,
            "can_see_compliance": True,
            "can_see_security_logs": True,
        },
        "operations": {
            "description": "Operations and Engineering",
            "allowed_sources": ["Operations_Summary_Dec2024", "it_assets", "application_logs", "IT_Security_Policy_2024"],
            "denied_sources": ["Q4_Financial_Report_2024", "HR_Policy_Handbook_2024", "Compliance_Audit_2024"],
            "can_see_salaries": False,
            "can_see_financials": False,
            "can_see_compliance": False,
            "can_see_security_logs": False,
        },
        "employee": {
            "description": "General employee — basic access only",
            "allowed_sources": ["HR_Policy_Handbook_2024"],
            "denied_sources": ["Q4_Financial_Report_2024", "Compliance_Audit_2024", "security_audit_logs", "employees", "vendor_contracts"],
            "can_see_salaries": False,
            "can_see_financials": False,
            "can_see_compliance": False,
            "can_see_security_logs": False,
        }
    },
    "users": {
        "sarah.mitchell": {"role": "executive", "name": "Sarah Mitchell", "dept": "Finance"},
        "james.okafor": {"role": "hr", "name": "James Okafor", "dept": "HR"},
        "dr.priya.nair": {"role": "it_security", "name": "Dr. Priya Nair", "dept": "IT Security"},
        "marcus.chen": {"role": "operations", "name": "Marcus Chen", "dept": "Operations"},
        "alice.chen": {"role": "operations", "name": "Alice Chen", "dept": "Engineering"},
        "bob.martinez": {"role": "finance", "name": "Bob Martinez", "dept": "Finance"},
        "david.kim": {"role": "it_security", "name": "David Kim", "dept": "IT Security"},
        "henry.park": {"role": "employee", "name": "Henry Park", "dept": "Sales"},
        "amanda.torres": {"role": "finance", "name": "Amanda Torres", "dept": "Compliance"},
        "guest": {"role": "employee", "name": "Guest User", "dept": "General"},
    }
}

with open("data/rbac_policy.json", 'w') as f:
    json.dump(rbac_policy, f, indent=2)

print("✓ Created RBAC policy file")
print("\n✅ All synthetic enterprise datasets generated successfully!")
print("   → 5 document files (PDFs/reports)")
print("   → 3 CSV files (employees, vendors, assets)")
print("   → 2 JSON log files (security, application)")
print("   → 1 RBAC policy file")