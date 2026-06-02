"""
Job Templates — Canonical Skill & Domain Knowledge Base
=========================================================
Each entry maps a job title PATTERN (lowercase substring) to a template dict:

    "required_skills"  — skills that virtually every job with this title needs
    "preferred_skills" — skills commonly listed as "nice to have"
    "domain"           — the professional domain for title-relevance scoring
    "tools"            — specific software / platforms common to this role

Matching logic (in jsearch.py):
    1. Normalise the incoming job title to lowercase
    2. Walk JOB_TEMPLATES in order; first pattern that appears in the title wins
    3. Merge template skills with NLP-extracted skills (union, deduped)
    4. Template guarantees a correct baseline even when the posting is sparse

Order matters — put more specific patterns BEFORE broader ones so that
"data engineer" is matched before plain "engineer".
"""

from __future__ import annotations
from typing import Dict, Any


JOB_TEMPLATES: Dict[str, Dict[str, Any]] = {

    # ══════════════════════════════════════════════════════════════════
    # DATA & AI
    # ══════════════════════════════════════════════════════════════════

    "data scientist": {
        "domain": "data",
        "required_skills": [
            "python", "sql", "machine learning", "statistics",
            "data analysis", "data visualization", "pandas", "numpy",
            "scikit-learn", "feature engineering", "exploratory data analysis",
        ],
        "preferred_skills": [
            "tensorflow", "pytorch", "spark", "mlops", "tableau",
            "power bi", "a/b testing", "deep learning", "nlp",
            "time series", "docker", "git",
        ],
        "tools": ["jupyter", "git", "github", "vs code"],
    },

    "machine learning engineer": {
        "domain": "data",
        "required_skills": [
            "python", "machine learning", "deep learning", "tensorflow",
            "pytorch", "scikit-learn", "sql", "model deployment", "mlops",
            "feature engineering", "docker", "git",
        ],
        "preferred_skills": [
            "kubernetes", "spark", "aws", "azure", "gcp",
            "nlp", "computer vision", "transformers", "langchain",
        ],
        "tools": ["jupyter", "mlflow", "docker", "kubernetes", "git"],
    },

    "data engineer": {
        "domain": "data",
        "required_skills": [
            "python", "sql", "etl", "data pipeline", "data warehouse",
            "apache spark", "airflow", "data modeling", "git",
        ],
        "preferred_skills": [
            "kafka", "dbt", "snowflake", "bigquery", "redshift",
            "aws", "azure", "gcp", "docker", "kubernetes",
        ],
        "tools": ["airflow", "dbt", "spark", "docker", "git"],
    },

    "data analyst": {
        "domain": "data",
        "required_skills": [
            "sql", "excel", "data analysis", "data visualization",
            "reporting", "statistics", "python",
        ],
        "preferred_skills": [
            "tableau", "power bi", "looker", "r", "google analytics",
            "a/b testing", "google sheets",
        ],
        "tools": ["excel", "tableau", "power bi", "sql", "python"],
    },

    "business analyst": {
        "domain": "data",
        "required_skills": [
            "sql", "excel", "data analysis", "requirements gathering",
            "stakeholder management", "reporting", "process improvement",
            "business process modeling", "documentation",
        ],
        "preferred_skills": [
            "tableau", "power bi", "jira", "agile", "scrum",
            "python", "visio", "confluence",
        ],
        "tools": ["excel", "jira", "confluence", "visio"],
    },

    # ══════════════════════════════════════════════════════════════════
    # SOFTWARE ENGINEERING
    # ══════════════════════════════════════════════════════════════════

    "software engineer": {
        "domain": "tech",
        "required_skills": [
            "git", "data structures", "algorithms", "rest api",
            "sql", "testing", "code review", "agile",
        ],
        "preferred_skills": [
            "docker", "kubernetes", "ci/cd", "microservices",
            "aws", "azure", "gcp",
        ],
        "tools": ["git", "github", "jira", "vs code"],
    },

    "backend engineer": {
        "domain": "tech",
        "required_skills": [
            "rest api", "sql", "git", "testing", "databases",
            "data structures", "algorithms", "agile",
        ],
        "preferred_skills": [
            "docker", "kubernetes", "redis", "message queues",
            "aws", "microservices", "ci/cd",
        ],
        "tools": ["git", "docker", "postman", "jira"],
    },

    "frontend engineer": {
        "domain": "tech",
        "required_skills": [
            "javascript", "html", "css", "react", "git",
            "rest api", "responsive design", "testing",
        ],
        "preferred_skills": [
            "typescript", "vue.js", "angular", "webpack",
            "graphql", "tailwind", "figma",
        ],
        "tools": ["git", "webpack", "figma", "chrome devtools"],
    },

    "full stack": {
        "domain": "tech",
        "required_skills": [
            "javascript", "html", "css", "react", "node.js",
            "sql", "rest api", "git", "testing",
        ],
        "preferred_skills": [
            "typescript", "docker", "aws", "mongodb",
            "graphql", "ci/cd",
        ],
        "tools": ["git", "docker", "vs code", "postman"],
    },

    "devops engineer": {
        "domain": "tech",
        "required_skills": [
            "linux", "docker", "kubernetes", "ci/cd", "terraform",
            "git", "bash", "aws", "monitoring", "automation",
        ],
        "preferred_skills": [
            "ansible", "helm", "prometheus", "grafana",
            "azure", "gcp", "jenkins", "python",
        ],
        "tools": ["docker", "kubernetes", "terraform", "jenkins", "git"],
    },

    "cloud engineer": {
        "domain": "tech",
        "required_skills": [
            "aws", "azure", "gcp", "terraform", "linux",
            "docker", "kubernetes", "networking", "security",
        ],
        "preferred_skills": [
            "ansible", "python", "ci/cd", "monitoring",
            "cost optimisation", "serverless",
        ],
        "tools": ["terraform", "aws cli", "docker", "git"],
    },

    "security engineer": {
        "domain": "tech",
        "required_skills": [
            "penetration testing", "vulnerability assessment",
            "network security", "linux", "python", "incident response",
            "siem", "firewalls", "compliance",
        ],
        "preferred_skills": [
            "splunk", "aws security", "gdpr", "iso 27001",
            "owasp", "threat modeling", "forensics",
        ],
        "tools": ["burp suite", "wireshark", "nmap", "splunk"],
    },

    "product manager": {
        "domain": "tech",
        "required_skills": [
            "product roadmap", "stakeholder management", "agile",
            "user stories", "requirements gathering", "data analysis",
            "a/b testing", "prioritisation", "communication",
        ],
        "preferred_skills": [
            "sql", "figma", "jira", "product analytics",
            "customer research", "okrs",
        ],
        "tools": ["jira", "confluence", "figma", "mixpanel", "notion"],
    },

    # ══════════════════════════════════════════════════════════════════
    # DESIGN & UX
    # ══════════════════════════════════════════════════════════════════

    "ux designer": {
        "domain": "design",
        "required_skills": [
            "user research", "wireframing", "prototyping", "figma",
            "usability testing", "interaction design", "information architecture",
            "user flows", "design systems",
        ],
        "preferred_skills": [
            "sketch", "adobe xd", "motion design", "accessibility",
            "design tokens", "html", "css",
        ],
        "tools": ["figma", "miro", "notion", "maze"],
    },

    "graphic designer": {
        "domain": "design",
        "required_skills": [
            "adobe photoshop", "adobe illustrator", "typography",
            "visual design", "branding", "layout design",
            "colour theory", "print design",
        ],
        "preferred_skills": [
            "indesign", "after effects", "figma", "motion graphics",
            "digital marketing", "social media design",
        ],
        "tools": ["adobe creative suite", "figma", "canva"],
    },

    # ══════════════════════════════════════════════════════════════════
    # FINANCE & ACCOUNTING
    # ══════════════════════════════════════════════════════════════════

    "accounts receivable": {
        "domain": "accounting",
        "required_skills": [
            "accounts receivable", "billing", "invoicing",
            "reconciliation", "excel", "gaap",
            "journal entries", "general ledger", "month-end close",
        ],
        "preferred_skills": [
            "quickbooks", "sap", "erp", "accounts payable",
            "cash flow", "collections", "netsuite", "xero",
        ],
        "tools": ["excel", "quickbooks", "sap", "erp"],
    },

    "accounts payable": {
        "domain": "accounting",
        "required_skills": [
            "accounts payable", "invoicing", "reconciliation",
            "excel", "gaap", "journal entries",
            "vendor management", "month-end close",
        ],
        "preferred_skills": [
            "quickbooks", "sap", "erp", "purchase orders",
            "expense management", "netsuite", "xero",
        ],
        "tools": ["excel", "quickbooks", "sap", "erp"],
    },

    "staff accountant": {
        "domain": "accounting",
        "required_skills": [
            "gaap", "excel", "general ledger", "journal entries",
            "reconciliation", "month-end close", "financial reporting",
            "accounts payable", "accounts receivable",
        ],
        "preferred_skills": [
            "ifrs", "quickbooks", "sap", "erp", "sox",
            "audit preparation", "netsuite", "xero", "tax",
        ],
        "tools": ["excel", "quickbooks", "sap", "erp"],
    },

    "senior accountant": {
        "domain": "accounting",
        "required_skills": [
            "gaap", "ifrs", "excel", "general ledger", "journal entries",
            "reconciliation", "month-end close", "year-end close",
            "financial reporting", "financial statements",
            "accounts payable", "accounts receivable",
        ],
        "preferred_skills": [
            "sox", "audit", "tax compliance", "erp", "sap",
            "netsuite", "cpa", "budgeting", "forecasting",
        ],
        "tools": ["excel", "sap", "oracle financials", "netsuite"],
    },

    "bookkeeper": {
        "domain": "accounting",
        "required_skills": [
            "bookkeeping", "double entry", "accounts payable",
            "accounts receivable", "bank reconciliation", "excel",
            "payroll", "gaap", "general ledger",
        ],
        "preferred_skills": [
            "quickbooks", "xero", "sage", "tax filing",
            "invoicing", "billing",
        ],
        "tools": ["quickbooks", "xero", "excel"],
    },

    "financial analyst": {
        "domain": "finance",
        "required_skills": [
            "financial modeling", "excel", "financial analysis",
            "budgeting", "forecasting", "variance analysis",
            "financial statements", "data analysis", "reporting",
        ],
        "preferred_skills": [
            "sql", "power bi", "tableau", "bloomberg",
            "valuation", "dcf", "python", "sap",
        ],
        "tools": ["excel", "bloomberg", "power bi", "sap"],
    },

    "finance manager": {
        "domain": "finance",
        "required_skills": [
            "financial planning", "budgeting", "forecasting",
            "financial reporting", "financial analysis", "excel",
            "gaap", "stakeholder management", "team management",
        ],
        "preferred_skills": [
            "erp", "sap", "oracle financials", "ifrs",
            "cash flow management", "risk management",
        ],
        "tools": ["excel", "sap", "oracle financials"],
    },

    "auditor": {
        "domain": "accounting",
        "required_skills": [
            "audit", "gaap", "ifrs", "internal controls",
            "risk assessment", "financial statements", "excel",
            "compliance", "sox", "working papers",
        ],
        "preferred_skills": [
            "cpa", "ca", "erp", "data analytics",
            "tax", "fraud detection",
        ],
        "tools": ["excel", "caseware", "teammate", "sap"],
    },

    "tax accountant": {
        "domain": "accounting",
        "required_skills": [
            "tax compliance", "tax filing", "corporate tax",
            "income tax", "gaap", "excel", "tax planning",
            "tax research", "financial statements",
        ],
        "preferred_skills": [
            "cpa", "tax software", "indirect tax", "gst", "vat",
            "international tax", "sap",
        ],
        "tools": ["excel", "tax software", "quickbooks"],
    },

    "payroll specialist": {
        "domain": "hr",
        "required_skills": [
            "payroll processing", "payroll", "excel",
            "employment law", "tax compliance",
            "benefits administration", "hris",
        ],
        "preferred_skills": [
            "adp", "workday", "sap hr", "garnishments",
            "year-end reporting", "leave management",
        ],
        "tools": ["adp", "workday", "excel", "hris"],
    },

    # ══════════════════════════════════════════════════════════════════
    # HUMAN RESOURCES
    # ══════════════════════════════════════════════════════════════════

    "recruiter": {
        "domain": "hr",
        "required_skills": [
            "recruitment", "talent acquisition", "sourcing",
            "interviewing", "candidate assessment", "job posting",
            "employer branding", "onboarding", "stakeholder management",
        ],
        "preferred_skills": [
            "hris", "ats", "workday", "linkedin recruiter",
            "boolean search", "diversity recruiting",
        ],
        "tools": ["linkedin", "ats", "workday", "greenhouse", "lever"],
    },

    "hr manager": {
        "domain": "hr",
        "required_skills": [
            "human resources", "recruitment", "employee relations",
            "performance management", "employment law",
            "onboarding", "offboarding", "hris",
            "policy development", "stakeholder management",
        ],
        "preferred_skills": [
            "workday", "bamboohr", "adp", "learning and development",
            "succession planning", "compensation", "dei",
        ],
        "tools": ["hris", "workday", "bamboohr", "excel"],
    },

    "hr generalist": {
        "domain": "hr",
        "required_skills": [
            "human resources", "recruitment", "employee relations",
            "onboarding", "employment law", "hris",
            "performance management", "benefits administration",
        ],
        "preferred_skills": [
            "workday", "adp", "payroll", "training delivery",
            "compliance", "dei",
        ],
        "tools": ["hris", "excel", "adp", "workday"],
    },

    "learning and development": {
        "domain": "hr",
        "required_skills": [
            "training delivery", "instructional design", "needs analysis",
            "curriculum development", "facilitation", "e-learning",
            "adult learning", "lms",
        ],
        "preferred_skills": [
            "articulate", "captivate", "coaching", "succession planning",
            "performance consulting",
        ],
        "tools": ["lms", "articulate 360", "zoom", "ms teams"],
    },

    # ══════════════════════════════════════════════════════════════════
    # MARKETING
    # ══════════════════════════════════════════════════════════════════

    "digital marketing": {
        "domain": "marketing",
        "required_skills": [
            "digital marketing", "seo", "google analytics",
            "social media marketing", "content marketing",
            "email marketing", "paid advertising", "campaign management",
        ],
        "preferred_skills": [
            "sem", "google ads", "facebook ads", "hubspot",
            "marketing automation", "crm", "copywriting",
        ],
        "tools": ["google analytics", "google ads", "hubspot", "mailchimp"],
    },

    "seo specialist": {
        "domain": "marketing",
        "required_skills": [
            "seo", "keyword research", "on-page seo", "link building",
            "google analytics", "content strategy", "technical seo",
            "google search console",
        ],
        "preferred_skills": [
            "sem", "ahrefs", "semrush", "content writing",
            "html", "page speed optimisation",
        ],
        "tools": ["ahrefs", "semrush", "google analytics", "screaming frog"],
    },

    "content writer": {
        "domain": "marketing",
        "required_skills": [
            "copywriting", "content writing", "content strategy",
            "seo", "editing", "research", "storytelling",
        ],
        "preferred_skills": [
            "blog writing", "social media", "email marketing",
            "cms", "keyword research",
        ],
        "tools": ["wordpress", "google docs", "grammarly", "semrush"],
    },

    "marketing manager": {
        "domain": "marketing",
        "required_skills": [
            "marketing strategy", "campaign management", "budget management",
            "brand management", "digital marketing", "stakeholder management",
            "team management", "data analysis", "reporting",
        ],
        "preferred_skills": [
            "crm", "hubspot", "google analytics", "social media",
            "content marketing", "email marketing",
        ],
        "tools": ["hubspot", "salesforce", "google analytics", "excel"],
    },

    # ══════════════════════════════════════════════════════════════════
    # SALES
    # ══════════════════════════════════════════════════════════════════

    "account executive": {
        "domain": "sales",
        "required_skills": [
            "sales", "crm", "lead generation", "cold calling",
            "negotiation", "pipeline management", "closing deals",
            "client relationship management",
        ],
        "preferred_skills": [
            "salesforce", "b2b", "saas sales", "account management",
            "upselling", "customer success",
        ],
        "tools": ["salesforce", "hubspot", "linkedin sales navigator", "zoom"],
    },

    "sales representative": {
        "domain": "sales",
        "required_skills": [
            "sales", "cold calling", "lead generation", "crm",
            "negotiation", "product knowledge", "customer service",
        ],
        "preferred_skills": [
            "salesforce", "b2b", "b2c", "prospecting",
            "email outreach", "pipeline management",
        ],
        "tools": ["salesforce", "hubspot", "excel"],
    },

    "business development": {
        "domain": "sales",
        "required_skills": [
            "business development", "lead generation", "partnership management",
            "stakeholder management", "negotiation", "crm",
            "market research", "sales strategy",
        ],
        "preferred_skills": [
            "salesforce", "b2b", "account management",
            "contract negotiation", "pipeline management",
        ],
        "tools": ["salesforce", "linkedin", "excel", "zoom"],
    },

    "customer success": {
        "domain": "sales",
        "required_skills": [
            "customer success", "account management", "onboarding",
            "customer retention", "crm", "relationship management",
            "problem solving", "communication",
        ],
        "preferred_skills": [
            "salesforce", "gainsight", "upselling", "renewals",
            "product training", "churn reduction",
        ],
        "tools": ["salesforce", "gainsight", "zendesk", "zoom"],
    },

    # ══════════════════════════════════════════════════════════════════
    # LEGAL
    # ══════════════════════════════════════════════════════════════════

    "lawyer": {
        "domain": "legal",
        "required_skills": [
            "legal research", "contract drafting", "contract review",
            "legal writing", "negotiation", "compliance",
            "client management", "litigation",
        ],
        "preferred_skills": [
            "corporate law", "employment law", "due diligence",
            "mergers and acquisitions", "intellectual property",
        ],
        "tools": ["lexisnexis", "westlaw", "ms word", "case management"],
    },

    "paralegal": {
        "domain": "legal",
        "required_skills": [
            "legal research", "legal writing", "document review",
            "case management", "filing", "contract review",
            "administrative support", "compliance",
        ],
        "preferred_skills": [
            "litigation support", "e-discovery", "corporate law",
            "employment law",
        ],
        "tools": ["lexisnexis", "ms word", "excel", "case management"],
    },

    "compliance officer": {
        "domain": "legal",
        "required_skills": [
            "compliance", "regulatory compliance", "risk assessment",
            "policy development", "audit", "reporting",
            "employment law", "gdpr",
        ],
        "preferred_skills": [
            "sox", "hipaa", "iso 27001", "training delivery",
            "investigations",
        ],
        "tools": ["grc software", "excel", "sharepoint"],
    },

    # ══════════════════════════════════════════════════════════════════
    # OPERATIONS & SUPPLY CHAIN
    # ══════════════════════════════════════════════════════════════════

    "operations manager": {
        "domain": "operations",
        "required_skills": [
            "operations management", "process improvement", "team management",
            "budgeting", "stakeholder management", "reporting",
            "kpi", "vendor management", "project management",
        ],
        "preferred_skills": [
            "lean", "six sigma", "erp", "sap", "supply chain",
            "change management",
        ],
        "tools": ["excel", "erp", "jira", "ms project"],
    },

    "supply chain": {
        "domain": "operations",
        "required_skills": [
            "supply chain management", "logistics", "procurement",
            "inventory management", "demand planning", "vendor management",
            "erp", "excel",
        ],
        "preferred_skills": [
            "sap", "sap mm", "lean", "six sigma",
            "warehouse management", "import export", "incoterms",
        ],
        "tools": ["sap", "excel", "erp", "tableau"],
    },

    "procurement": {
        "domain": "operations",
        "required_skills": [
            "procurement", "sourcing", "contract negotiation",
            "vendor management", "purchase orders", "erp",
            "supplier evaluation", "cost reduction",
        ],
        "preferred_skills": [
            "sap", "ariba", "category management",
            "strategic sourcing", "risk management",
        ],
        "tools": ["sap ariba", "excel", "erp"],
    },

    "project manager": {
        "domain": "operations",
        "required_skills": [
            "project management", "stakeholder management", "risk management",
            "budgeting", "scheduling", "team management",
            "agile", "scrum", "reporting", "communication",
        ],
        "preferred_skills": [
            "pmp", "prince2", "jira", "ms project",
            "change management", "resource planning",
        ],
        "tools": ["jira", "ms project", "confluence", "excel", "trello"],
    },

    # ══════════════════════════════════════════════════════════════════
    # HEALTHCARE
    # ══════════════════════════════════════════════════════════════════

    "registered nurse": {
        "domain": "nursing",
        "required_skills": [
            "patient care", "clinical assessment", "medication administration",
            "vital signs", "nursing", "patient education",
            "care planning", "ehr", "emr", "documentation",
        ],
        "preferred_skills": [
            "epic", "meditech", "iv therapy", "wound care",
            "triage", "critical thinking",
        ],
        "tools": ["epic", "meditech", "ehr", "emr"],
    },

    "nurse": {
        "domain": "nursing",
        "required_skills": [
            "patient care", "nursing", "medication administration",
            "clinical assessment", "vital signs", "documentation",
            "care planning", "ehr",
        ],
        "preferred_skills": [
            "epic", "meditech", "iv therapy",
            "patient education", "wound care",
        ],
        "tools": ["epic", "meditech", "ehr"],
    },

    "physician": {
        "domain": "medicine",
        "required_skills": [
            "diagnosis", "treatment planning", "patient care",
            "clinical assessment", "medical terminology",
            "ehr", "documentation", "patient education",
        ],
        "preferred_skills": [
            "epic", "telemedicine", "medical research",
            "patient communication", "prescription management",
        ],
        "tools": ["epic", "meditech", "ehr"],
    },

    "pharmacist": {
        "domain": "healthcare",
        "required_skills": [
            "pharmacology", "medication dispensing", "drug interactions",
            "patient counselling", "prescription review",
            "clinical assessment", "documentation",
        ],
        "preferred_skills": [
            "compounding", "clinical pharmacy", "mtm",
            "pharmacy software", "regulatory compliance",
        ],
        "tools": ["pharmacy management system", "ehr"],
    },

    "medical coder": {
        "domain": "healthcare",
        "required_skills": [
            "medical coding", "icd-10", "cpt coding",
            "medical terminology", "anatomy", "ehr",
            "compliance", "documentation",
        ],
        "preferred_skills": [
            "hcpcs", "billing", "hipaa",
            "revenue cycle", "auditing",
        ],
        "tools": ["ehr", "coding software", "encoder"],
    },

    "clinical coordinator": {
        "domain": "healthcare",
        "required_skills": [
            "clinical coordination", "patient scheduling",
            "medical records", "ehr", "patient care",
            "administrative support", "compliance",
        ],
        "preferred_skills": [
            "epic", "meditech", "hipaa",
            "insurance verification", "referrals",
        ],
        "tools": ["epic", "ehr", "ms office"],
    },

    "physiotherapist": {
        "domain": "allied_health",
        "required_skills": [
            "physiotherapy", "patient assessment", "treatment planning",
            "rehabilitation", "exercise prescription",
            "patient education", "documentation",
        ],
        "preferred_skills": [
            "manual therapy", "electrotherapy",
            "sports rehabilitation", "ehr",
        ],
        "tools": ["ehr", "practice management software"],
    },

    # ══════════════════════════════════════════════════════════════════
    # EDUCATION
    # ══════════════════════════════════════════════════════════════════

    "teacher": {
        "domain": "teaching",
        "required_skills": [
            "lesson planning", "classroom management", "curriculum",
            "student assessment", "differentiated instruction",
            "communication", "teaching", "feedback",
        ],
        "preferred_skills": [
            "lms", "google classroom", "special education",
            "parent communication", "behaviour management",
        ],
        "tools": ["google classroom", "lms", "ms office", "zoom"],
    },

    "lecturer": {
        "domain": "teaching",
        "required_skills": [
            "teaching", "curriculum development", "lesson planning",
            "student assessment", "research", "academic writing",
            "communication", "feedback",
        ],
        "preferred_skills": [
            "lms", "moodle", "canvas", "academic research",
            "publications", "e-learning",
        ],
        "tools": ["lms", "moodle", "canvas", "ms office"],
    },

    "instructional designer": {
        "domain": "teaching",
        "required_skills": [
            "instructional design", "curriculum development", "e-learning",
            "lms", "adult learning", "needs analysis",
            "storyboarding", "training delivery",
        ],
        "preferred_skills": [
            "articulate", "captivate", "microlearning",
            "video production", "gamification",
        ],
        "tools": ["articulate 360", "captivate", "lms", "canva"],
    },

    "principal": {
        "domain": "teaching",
        "required_skills": [
            "school leadership", "curriculum", "staff management",
            "stakeholder management", "budgeting",
            "student wellbeing", "compliance", "policy development",
        ],
        "preferred_skills": [
            "strategic planning", "community engagement",
            "data-driven decision making",
        ],
        "tools": ["ms office", "school management system"],
    },

    # ══════════════════════════════════════════════════════════════════
    # SOCIAL WORK & MENTAL HEALTH
    # ══════════════════════════════════════════════════════════════════

    "social worker": {
        "domain": "mental_health",
        "required_skills": [
            "case management", "client assessment", "counselling",
            "risk assessment", "documentation", "advocacy",
            "community resources", "crisis intervention",
        ],
        "preferred_skills": [
            "child protection", "mental health first aid",
            "motivational interviewing", "family therapy",
        ],
        "tools": ["case management software", "ms office"],
    },

    "psychologist": {
        "domain": "mental_health",
        "required_skills": [
            "psychological assessment", "therapy", "counselling",
            "diagnosis", "treatment planning", "documentation",
            "client management", "evidence-based practice",
        ],
        "preferred_skills": [
            "cbt", "dbt", "group therapy",
            "research", "clinical supervision",
        ],
        "tools": ["practice management software", "ms office"],
    },

    # ══════════════════════════════════════════════════════════════════
    # CONSTRUCTION & ENGINEERING
    # ══════════════════════════════════════════════════════════════════

    "civil engineer": {
        "domain": "construction",
        "required_skills": [
            "structural design", "autocad", "project management",
            "construction management", "site supervision",
            "civil engineering", "documentation", "compliance",
        ],
        "preferred_skills": [
            "revit", "staad pro", "quantity surveying",
            "contract management", "environmental compliance",
        ],
        "tools": ["autocad", "revit", "ms project", "excel"],
    },

    "mechanical engineer": {
        "domain": "construction",
        "required_skills": [
            "mechanical engineering", "cad", "autocad",
            "solidworks", "product design", "manufacturing",
            "technical documentation", "testing",
        ],
        "preferred_skills": [
            "fea", "ansys", "cfm", "project management",
            "iso standards",
        ],
        "tools": ["autocad", "solidworks", "ansys", "excel"],
    },

    "electrical engineer": {
        "domain": "construction",
        "required_skills": [
            "electrical engineering", "autocad", "circuit design",
            "power systems", "control systems",
            "technical documentation", "compliance",
        ],
        "preferred_skills": [
            "plc", "scada", "matlab", "project management",
            "as/nzs standards",
        ],
        "tools": ["autocad", "matlab", "ms office"],
    },

    # ══════════════════════════════════════════════════════════════════
    # HOSPITALITY & RETAIL
    # ══════════════════════════════════════════════════════════════════

    "chef": {
        "domain": "hospitality",
        "required_skills": [
            "food preparation", "menu development", "kitchen management",
            "food safety", "haccp", "inventory management",
            "team management", "cost control",
        ],
        "preferred_skills": [
            "pastry", "butchery", "allergen management",
            "supplier management", "nutritional knowledge",
        ],
        "tools": ["pos system", "inventory software"],
    },

    "hotel manager": {
        "domain": "hospitality",
        "required_skills": [
            "hotel management", "guest services", "team management",
            "budgeting", "revenue management", "operations management",
            "customer service", "complaints handling",
        ],
        "preferred_skills": [
            "property management system", "pms", "otas",
            "housekeeping", "f&b management",
        ],
        "tools": ["opera pms", "excel", "booking systems"],
    },

    "retail manager": {
        "domain": "retail",
        "required_skills": [
            "retail management", "team management", "customer service",
            "inventory management", "sales", "visual merchandising",
            "loss prevention", "budgeting",
        ],
        "preferred_skills": [
            "pos system", "stock control", "kpi management",
            "merchandising", "supplier management",
        ],
        "tools": ["pos", "excel", "inventory management software"],
    },

    # ══════════════════════════════════════════════════════════════════
    # REAL ESTATE
    # ══════════════════════════════════════════════════════════════════

    "real estate agent": {
        "domain": "real_estate",
        "required_skills": [
            "real estate", "property sales", "client management",
            "negotiation", "market analysis", "listing management",
            "contract management", "communication",
        ],
        "preferred_skills": [
            "property management", "crm", "digital marketing",
            "auction", "property valuation",
        ],
        "tools": ["crm", "real estate portal software", "excel"],
    },

    "property manager": {
        "domain": "real_estate",
        "required_skills": [
            "property management", "tenant management", "lease management",
            "maintenance coordination", "rent collection",
            "compliance", "communication", "inspections",
        ],
        "preferred_skills": [
            "property management software", "landlord relations",
            "arrears management", "budgeting",
        ],
        "tools": ["property management software", "excel"],
    },

    # ══════════════════════════════════════════════════════════════════
    # RESEARCH & SCIENCE
    # ══════════════════════════════════════════════════════════════════

    "research scientist": {        "domain": "research",
        "required_skills": [
            "research methodology", "data analysis", "statistical analysis",
            "literature review", "academic writing", "lab techniques",
            "experimental design", "python", "r",
        ],
        "preferred_skills": [
            "publications", "grant writing", "spss",
            "stata", "matlab", "peer review",
        ],
        "tools": ["r", "python", "spss", "stata", "matlab"],
    },

    "lab technician": {
        "domain": "research",
        "required_skills": [
            "lab techniques", "sample preparation", "equipment operation",
            "documentation", "quality control", "safety compliance",
            "data recording",
        ],
        "preferred_skills": [
            "hplc", "pcr", "spectroscopy",
            "gmp", "iso standards",
        ],
        "tools": ["lims", "ms office"],
    },

}

# ══════════════════════════════════════════════════════════════════════════════
# BROAD FALLBACK PATTERNS  (must stay at the END — matched after specific ones)
# ══════════════════════════════════════════════════════════════════════════════

# ── Additional specific patterns missed by compound-word titles ──────────────

JOB_TEMPLATES["talent acquisition"] = {
    "domain": "hr",
    "required_skills": [
        "recruitment", "talent acquisition", "sourcing", "interviewing",
        "candidate assessment", "onboarding", "employer branding",
        "stakeholder management",
    ],
    "preferred_skills": ["hris", "ats", "workday", "linkedin recruiter",
                         "boolean search", "diversity recruiting"],
    "tools": ["linkedin", "ats", "workday", "greenhouse"],
}

JOB_TEMPLATES["seo"] = {
    "domain": "marketing",
    "required_skills": [
        "seo", "keyword research", "on-page seo", "google analytics",
        "content strategy", "google search console", "link building",
    ],
    "preferred_skills": ["sem", "ahrefs", "semrush", "technical seo",
                         "content writing", "html"],
    "tools": ["ahrefs", "semrush", "google analytics", "screaming frog"],
}

JOB_TEMPLATES["designer"] = {
    "domain": "design",
    "required_skills": [
        "visual design", "figma", "typography", "colour theory",
        "branding", "design systems",
    ],
    "preferred_skills": ["adobe photoshop", "adobe illustrator",
                         "sketch", "prototyping", "ux research"],
    "tools": ["figma", "adobe creative suite", "miro"],
}

JOB_TEMPLATES["hotel"] = {
    "domain": "hospitality",
    "required_skills": [
        "hotel management", "guest services", "team management",
        "customer service", "operations management", "complaints handling",
    ],
    "preferred_skills": ["pms", "opera", "revenue management",
                         "otas", "f&b management"],
    "tools": ["opera pms", "excel"],
}

JOB_TEMPLATES["retail"] = {
    "domain": "retail",
    "required_skills": [
        "retail management", "customer service", "inventory management",
        "sales", "visual merchandising", "team management",
    ],
    "preferred_skills": ["pos system", "stock control",
                         "kpi management", "loss prevention"],
    "tools": ["pos", "excel"],
}

JOB_TEMPLATES["hotel operations"] = {
    "domain": "hospitality",
    "required_skills": [
        "hotel management", "guest services", "team management",
        "customer service", "operations management", "complaints handling",
    ],
    "preferred_skills": ["pms", "opera", "revenue management", "otas"],
    "tools": ["opera pms", "excel"],
}

JOB_TEMPLATES["hotel operations manager"] = {
    "domain": "hospitality",
    "required_skills": [
        "hotel management", "guest services", "team management",
        "customer service", "operations management", "complaints handling",
        "budgeting", "revenue management",
    ],
    "preferred_skills": ["pms", "opera", "otas", "f&b management"],
    "tools": ["opera pms", "excel"],
}

JOB_TEMPLATES["hr coordinator"] = {
    "domain": "hr",
    "required_skills": [
        "human resources", "recruitment", "onboarding",
        "hris", "employee records", "scheduling",
        "administrative support", "communication",
    ],
    "preferred_skills": ["workday", "bamboohr", "adp", "payroll"],
    "tools": ["hris", "excel", "ms office"],
}

JOB_TEMPLATES["marketing consultant"] = {
    "domain": "marketing",
    "required_skills": [
        "marketing strategy", "digital marketing", "client management",
        "campaign management", "data analysis", "reporting",
    ],
    "preferred_skills": ["seo", "google analytics", "crm", "hubspot"],
    "tools": ["google analytics", "excel", "hubspot"],
}

JOB_TEMPLATES["accountant"] = {
    "domain": "accounting",
    "required_skills": [
        "accounting", "gaap", "excel", "journal entries",
        "reconciliation", "financial reporting", "general ledger",
    ],
    "preferred_skills": [
        "ifrs", "erp", "quickbooks", "sap", "cpa",
        "month-end close", "accounts payable", "accounts receivable",
    ],
    "tools": ["excel", "quickbooks", "sap"],
}

JOB_TEMPLATES["nurse"] = {
    "domain": "nursing",
    "required_skills": [
        "patient care", "nursing", "medication administration",
        "clinical assessment", "vital signs", "documentation", "ehr",
    ],
    "preferred_skills": ["epic", "meditech", "iv therapy", "wound care"],
    "tools": ["epic", "meditech", "ehr"],
}

JOB_TEMPLATES["engineer"] = {
    "domain": "tech",
    "required_skills": [
        "git", "testing", "documentation", "problem solving",
        "agile", "code review",
    ],
    "preferred_skills": ["docker", "ci/cd", "aws"],
    "tools": ["git", "jira"],
}

JOB_TEMPLATES["hotel"] = {
    "domain": "hospitality",
    "required_skills": [
        "hotel management", "guest services", "team management",
        "customer service", "operations management", "complaints handling",
    ],
    "preferred_skills": ["pms", "opera", "revenue management", "otas"],
    "tools": ["opera pms", "excel"],
}

JOB_TEMPLATES["retail"] = {
    "domain": "retail",
    "required_skills": [
        "retail management", "customer service", "inventory management",
        "sales", "visual merchandising", "team management",
    ],
    "preferred_skills": ["pos system", "stock control", "kpi management"],
    "tools": ["pos", "excel"],
}

JOB_TEMPLATES["manager"] = {
    "domain": "management",
    "required_skills": [
        "team management", "stakeholder management", "budgeting",
        "reporting", "communication", "planning",
    ],
    "preferred_skills": ["agile", "strategic planning", "change management"],
    "tools": ["excel", "ms office"],
}

JOB_TEMPLATES["analyst"] = {
    "domain": "data",
    "required_skills": [
        "data analysis", "excel", "reporting", "sql",
        "problem solving", "communication",
    ],
    "preferred_skills": ["tableau", "power bi", "python"],
    "tools": ["excel", "sql"],
}

JOB_TEMPLATES["coordinator"] = {
    "domain": "operations",
    "required_skills": [
        "coordination", "administrative support", "scheduling",
        "communication", "documentation", "stakeholder management",
    ],
    "preferred_skills": ["ms office", "project management", "crm"],
    "tools": ["ms office", "excel"],
}

JOB_TEMPLATES["consultant"] = {
    "domain": "operations",
    "required_skills": [
        "consulting", "stakeholder management", "problem solving",
        "presentation", "data analysis", "documentation", "client management",
    ],
    "preferred_skills": ["project management", "excel", "powerpoint"],
    "tools": ["ms office", "excel", "powerpoint"],
}

JOB_TEMPLATES["specialist"] = {
    "domain": "operations",
    "required_skills": [
        "subject matter expertise", "communication", "documentation",
        "reporting", "stakeholder management",
    ],
    "preferred_skills": ["ms office", "data analysis"],
    "tools": ["ms office"],
}


def find_template(job_title: str) -> "Dict[str, Any] | None":
    """
    Find the best-matching template for a given job title using two passes.

    Pass 1 — domain-specific patterns (e.g. "seo", "hotel operations",
              "hr coordinator").  Longest match wins among specific patterns.
    Pass 2 — generic role-type fallbacks (e.g. "analyst", "manager",
              "coordinator") only if Pass 1 found nothing.

    This ensures domain intent beats generic role label:
        "SEO Analyst"            -> "seo"               (not "analyst")
        "Retail Store Manager"   -> "retail"             (not "manager")
        "Hotel Operations Mgr"   -> "hotel operations"   (not "operations manager")
        "Support Analyst"        -> "analyst" (Pass 2)   (no specific match)
    """
    # Role-type words that are generic fallbacks — checked last
    _GENERIC = {
        "manager", "analyst", "coordinator", "consultant",
        "specialist", "engineer", "nurse",
    }

    title_lower = (job_title or "").lower()

    # Pass 1: specific domain patterns (longest match)
    best_template = None
    best_length = 0
    for pattern, template in JOB_TEMPLATES.items():
        if pattern not in _GENERIC and pattern in title_lower:
            if len(pattern) > best_length:
                best_length = len(pattern)
                best_template = template
    if best_template:
        return best_template

    # Pass 2: generic role-type fallbacks (longest match)
    best_template = None
    best_length = 0
    for pattern, template in JOB_TEMPLATES.items():
        if pattern in _GENERIC and pattern in title_lower:
            if len(pattern) > best_length:
                best_length = len(pattern)
                best_template = template
    return best_template
