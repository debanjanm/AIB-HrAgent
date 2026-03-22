from pydantic import BaseModel, Field
from typing import List, Optional
import json
import uuid
# from models import Job, Skills
import requests
import os
import re

from dotenv import load_dotenv

load_dotenv()

from typing import Annotated, List, Optional
 
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic.config import ConfigDict

class Salary(BaseModel):
    currency: Optional[str] = Field(None, description="Salary currency (e.g., INR, USD)")
    min: Optional[int] = Field(None, description="Minimum salary")
    max: Optional[int] = Field(None, description="Maximum salary")
    period: Optional[str] = Field(None, description="Salary period (yearly, monthly, hourly)")
    notes: Optional[str] = Field(None, description="Additional compensation info")


class ApplicationMeta(BaseModel):
    posted: Optional[str] = Field(None, description="Posting date info (e.g., '1 week ago')")
    applicants: Optional[str] = Field(None, description="Number of applicants")
    source: Optional[str] = Field(None, description="Source platform (LinkedIn, company site)")
    applicationType: Optional[str] = Field(None, description="Application method")


# class Skills(BaseModel):
#     programming: List[str] = Field(default_factory=list)
#     frameworks: List[str] = Field(default_factory=list)
#     tools: List[str] = Field(default_factory=list)
#     platforms: List[str] = Field(default_factory=list)
#     databases: List[str] = Field(default_factory=list)
#     data_pipeline: List[str] = Field(default_factory=list)
#     core_aiml_pipeline: List[str] = Field(default_factory=list)
#     backend: List[str] = Field(default_factory=list)
#     deployment: List[str] = Field(default_factory=list)
#     methodologies: List[str] = Field(default_factory=list)
#     domain: List[str] = Field(default_factory=list)

from pydantic import BaseModel, Field
from typing import List


class Skills(BaseModel):
    programming: List[str] = Field(
        default_factory=list,
        description="Programming languages required or used in the role (e.g., Python, Go, TypeScript, Java, SQL)."
    )
    frameworks: List[str] = Field(
        default_factory=list,
        description="Frameworks and libraries used for development, data processing, or AI/ML (e.g., TensorFlow, PyTorch, LangChain, Django, FastAPI)."
    )
    tools: List[str] = Field(
        default_factory=list,
        description="Development, productivity, and AI-assisted tools (e.g., Git, Airflow, MLflow, Cursor, GitHub Copilot, Claude Code, Codex)."
    )
    platforms: List[str] = Field(
        default_factory=list,
        description="Cloud platforms and infrastructure providers (e.g., AWS, GCP, Azure)."
    )
    databases: List[str] = Field(
        default_factory=list,
        description="Databases and storage systems including relational, NoSQL, and vector databases (e.g., SQL, PostgreSQL, MongoDB, Pinecone, FAISS)."
    )
    data_pipeline: List[str] = Field(
        default_factory=list,
        description="Data ingestion, processing, and transformation techniques (e.g., ETL, RAG, data pipelines, structured data handling)."
    )
    core_aiml_pipeline: List[str] = Field(
        default_factory=list,
        description="Core AI/ML capabilities and techniques (e.g., Machine Learning, Deep Learning, Natural Language Processing, Computer Vision, LLM, Agentic AI)."
    )
    backend: List[str] = Field(
        default_factory=list,
        description="Backend technologies, APIs, and frameworks (e.g., REST, gRPC, FastAPI, Django, microservices architecture)."
    )
    frontend: List[str] = Field(
        default_factory=list,
        description="Frontend technologies and frameworks (e.g., React, Angular, Vue.js, HTML, CSS, JavaScript, Next.js, Streamlit, Gradio, Marimo)."
    )
    deployment: List[str] = Field(
        default_factory=list,
        description="Deployment, MLOps, and DevOps practices (e.g., Docker, Kubernetes, model serving, monitoring, production systems)."
    )
    methodologies: List[str] = Field(
        default_factory=list,
        description="Development and analytical methodologies (e.g., Agile, A/B testing, experimentation, collaborative development)."
    )
    domain: List[str] = Field(
        default_factory=list,
        description="Business or industry domains relevant to the role (e.g., Financial Services, Healthcare, E-commerce, Retail)."
    )

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
 
def _skill_field(
    title: str,
    description: str,
    examples: list[list[str]],
    category: str,
) -> any:
    """
    Factory that builds a fully annotated Field for a skills list.
    Keeps each field declaration DRY while preserving rich JSON-schema output.
    """
    return Field(
        default_factory=list,
        title=title,
        description=description,
        examples=examples,
        json_schema_extra={
            "category": category,
            "item_type": "string",
            "uniqueItems": True,       # hint to consumers / LLM that duplicates are unwanted
            "x-normalise": True,       # custom marker — parsers should apply abbreviation expansion
        },
    )
 
 
def _deduplicate(values: list[str]) -> list[str]:
    """Case-insensitive deduplication while preserving original casing and order."""
    seen: set[str] = set()
    result: list[str] = []
    for v in values:
        key = v.strip().lower()
        if key and key not in seen:
            seen.add(key)
            result.append(v.strip())
    return result
 
 
# ---------------------------------------------------------------------------
# Salary
# ---------------------------------------------------------------------------
 
class Salary(BaseModel):
    currency: Optional[str] = Field(
        None,
        title="Currency",
        description="ISO 4217 currency code for the salary (e.g., 'INR', 'USD', 'EUR').",
        examples=["INR", "USD", "EUR"],
    )
    min: Optional[int] = Field(
        None,
        title="Minimum Salary",
        description="Lower bound of the salary range in the stated currency and period.",
        ge=0,
        examples=[800000, 120000],
    )
    max: Optional[int] = Field(
        None,
        title="Maximum Salary",
        description="Upper bound of the salary range in the stated currency and period.",
        ge=0,
        examples=[1500000, 200000],
    )
    period: Optional[str] = Field(
        None,
        title="Salary Period",
        description="Frequency at which the salary figure is quoted.",
        examples=["yearly", "monthly", "hourly"],
        json_schema_extra={"enum_hint": ["yearly", "monthly", "hourly"]},
    )
    notes: Optional[str] = Field(
        None,
        title="Compensation Notes",
        description=(
            "Free-text field for additional compensation details not captured by the "
            "structured fields (e.g., 'plus equity', 'performance bonus up to 20%')."
        ),
        examples=["plus equity", "performance bonus up to 20%", "includes RSUs"],
        max_length=500,
    )
 
    @model_validator(mode="after")
    def _validate_range(self) -> "Salary":
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError(
                f"Salary min ({self.min}) must not exceed max ({self.max})."
            )
        return self
 
 
# ---------------------------------------------------------------------------
# ApplicationMeta
# ---------------------------------------------------------------------------
 
class ApplicationMeta(BaseModel):
    posted: Optional[str] = Field(
        None,
        title="Posted",
        description="Human-readable posting recency as shown on the source platform (e.g., '3 days ago', '1 week ago').",
        examples=["3 days ago", "1 week ago", "Just now"],
        max_length=100,
    )
    applicants: Optional[str] = Field(
        None,
        title="Applicant Count",
        description="Approximate number of applicants as displayed by the source (e.g., '200+ applicants', 'Be an early applicant').",
        examples=["47 applicants", "200+ applicants", "Be an early applicant"],
        max_length=100,
    )
    source: Optional[str] = Field(
        None,
        title="Source Platform",
        description="Platform or website where the job was posted or discovered.",
        examples=["LinkedIn", "company website", "Naukri", "Indeed"],
        max_length=100,
    )
    applicationType: Optional[str] = Field(
        None,
        title="Application Type",
        description="Method or flow used to apply for the role.",
        examples=["Easy Apply", "External link", "Email"],
        max_length=100,
    )
 
 
# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------
 
class Skills(BaseModel):
    """
    Structured taxonomy of technical and domain skills extracted from a job description.
 
    Each field targets a distinct skill category. Values are deduplicated
    (case-insensitive) and stripped of leading/trailing whitespace automatically.
    Common abbreviations (ML, NLP, CV) are expected to be expanded by the parser
    before populating these fields.
    """
 
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        json_schema_extra={
            "x-skill-taxonomy-version": "2.0",
            "x-description": (
                "Flat, categorised skill lists extracted from a job posting. "
                "Each category is mutually exclusive — a skill should appear in "
                "only the most specific applicable bucket."
            ),
        },
    )
 
    # ------------------------------------------------------------------ #
    # Fields                                                               #
    # ------------------------------------------------------------------ #
 
    programming: List[str] = _skill_field(
        title="Programming Languages",
        description=(
            "Programming and scripting languages explicitly required or preferred. "
            "Include query languages (SQL, GraphQL) but exclude frameworks and libraries — "
            "those belong in `frameworks`."
        ),
        examples=[["Python", "Go", "TypeScript", "Java", "SQL", "Bash"]],
        category="engineering",
    )
 
    frameworks: List[str] = _skill_field(
        title="Frameworks & Libraries",
        description=(
            "Software frameworks, libraries, and SDKs used for application development, "
            "data processing, or AI/ML. Covers both general-purpose (Django, Spring) and "
            "AI-specific (TensorFlow, LangChain, Hugging Face Transformers) libraries."
        ),
        examples=[["FastAPI", "PyTorch", "LangChain", "Spring Boot", "Hugging Face Transformers"]],
        category="engineering",
    )
 
    tools: List[str] = _skill_field(
        title="Developer & Productivity Tools",
        description=(
            "Standalone tools used throughout the development lifecycle — version control, "
            "workflow orchestration, experiment tracking, and AI-assisted coding assistants. "
            "Does NOT include cloud platforms (→ `platforms`) or deployment tooling (→ `deployment`)."
        ),
        examples=[["Git", "Airflow", "MLflow", "Weights & Biases", "GitHub Copilot", "Cursor", "Jira"]],
        category="engineering",
    )
 
    platforms: List[str] = _skill_field(
        title="Cloud & Infrastructure Platforms",
        description=(
            "Public cloud providers and managed infrastructure platforms. "
            "Include specific managed services where relevant "
            "(e.g., 'AWS SageMaker', not just 'AWS') when the JD calls them out explicitly."
        ),
        examples=[["AWS", "GCP", "Azure", "AWS SageMaker", "Google Vertex AI", "Databricks"]],
        category="infrastructure",
    )
 
    databases: List[str] = _skill_field(
        title="Databases & Storage",
        description=(
            "Relational, NoSQL, time-series, graph, and vector databases, as well as "
            "object/blob storage systems. Include both the technology name and its type "
            "when the JD specifies (e.g., 'Pinecone' for vector search, 'Redis' for caching)."
        ),
        examples=[["PostgreSQL", "MongoDB", "Redis", "Pinecone", "FAISS", "BigQuery", "Snowflake"]],
        category="data",
    )
 
    data_pipeline: List[str] = _skill_field(
        title="Data Pipeline & Processing",
        description=(
            "Techniques, patterns, and technologies for ingesting, transforming, and serving data. "
            "Covers batch and streaming pipelines, feature engineering, and retrieval patterns "
            "such as RAG. Does NOT include the storage layer (→ `databases`) or ML training (→ `core_aiml_pipeline`)."
        ),
        examples=[["ETL", "Apache Spark", "Kafka", "RAG", "Feature Engineering", "dbt", "Flink"]],
        category="data",
    )
 
    core_aiml_pipeline: List[str] = _skill_field(
        title="Core AI / ML Capabilities",
        description=(
            "Fundamental AI and machine learning disciplines, paradigms, and techniques. "
            "Use expanded, canonical names — 'Natural Language Processing' not 'NLP', "
            "'Machine Learning' not 'ML', 'Large Language Models' not 'LLMs'. "
            "Fine-grained sub-techniques (e.g., 'LoRA fine-tuning', 'RLHF') are welcome when explicit in the JD."
        ),
        examples=[
            [
                "Machine Learning",
                "Deep Learning",
                "Natural Language Processing",
                "Computer Vision",
                "Large Language Models",
                "Reinforcement Learning from Human Feedback",
                "Agentic AI",
            ]
        ],
        category="ai_ml",
    )
 
    backend: List[str] = _skill_field(
        title="Backend & API Technologies",
        description=(
            "Server-side frameworks, API paradigms, and architectural patterns. "
            "Framework entries that overlap with `frameworks` (e.g., FastAPI, Django) should "
            "appear here when the JD focuses on their use as backend/API layers, otherwise "
            "prefer `frameworks`."
        ),
        examples=[["REST", "gRPC", "GraphQL", "FastAPI", "Django", "Microservices", "Event-driven architecture"]],
        category="engineering",
    )
 
    frontend: List[str] = _skill_field(
        title="Frontend & UI Technologies",
        description=(
            "Client-side frameworks, UI libraries, and data-app/notebook UI toolkits. "
            "Include both traditional web frontends (React, Vue.js) and ML-oriented UI tools "
            "(Streamlit, Gradio, Marimo) when the role involves building interactive demos or dashboards."
        ),
        examples=[["React", "Next.js", "TypeScript", "Streamlit", "Gradio", "Tailwind CSS", "Marimo"]],
        category="engineering",
    )
 
    deployment: List[str] = _skill_field(
        title="Deployment, MLOps & DevOps",
        description=(
            "Technologies, practices, and platforms for packaging, shipping, and operating "
            "software and ML models in production. Covers containerisation, orchestration, "
            "CI/CD, model serving, observability, and infrastructure-as-code."
        ),
        examples=[["Docker", "Kubernetes", "CI/CD", "Terraform", "Prometheus", "Model serving", "A/B testing infrastructure"]],
        category="infrastructure",
    )
 
    methodologies: List[str] = _skill_field(
        title="Methodologies & Practices",
        description=(
            "Software engineering, product, and analytical working practices. "
            "Includes delivery frameworks (Agile, Scrum), experimentation approaches "
            "(A/B testing, causal inference), and collaboration norms (code review, pair programming)."
        ),
        examples=[["Agile", "Scrum", "A/B Testing", "Test-Driven Development", "Code Review", "Design Sprints"]],
        category="process",
    )
 
    domain: List[str] = _skill_field(
        title="Industry & Business Domains",
        description=(
            "Vertical industry knowledge or business-function expertise that the role "
            "requires or prefers. Use standardised domain names where possible "
            "(e.g., 'Financial Services' rather than 'Fintech')."
        ),
        examples=[["Financial Services", "Healthcare", "E-commerce", "Retail", "AdTech", "Supply Chain"]],
        category="domain",
    )
 
    # ------------------------------------------------------------------ #
    # Validators                                                           #
    # ------------------------------------------------------------------ #
 
    @field_validator(
        "programming", "frameworks", "tools", "platforms", "databases",
        "data_pipeline", "core_aiml_pipeline", "backend", "frontend",
        "deployment", "methodologies", "domain",
        mode="before",
    )
    @classmethod
    def _clean_and_deduplicate(cls, values: list) -> list[str]:
        """
        Applied to every skill list before Pydantic validates item types.
        - Coerces non-string items to strings
        - Strips whitespace from each item
        - Removes blank entries
        - Deduplicates case-insensitively while preserving first-seen casing and order
        """
        if not isinstance(values, list):
            return []
        coerced = [str(v) for v in values if v is not None]
        return _deduplicate(coerced)
 
    @model_validator(mode="after")
    def _warn_on_empty(self) -> "Skills":
        """
        Emits a debug-level warning when every skill category is empty —
        a signal that the LLM may have failed to extract skills at all.
        This is non-fatal; the caller decides how to handle it.
        """
        all_empty = not any(
            getattr(self, field)
            for field in self.model_fields
        )
        if all_empty:
            import logging
            logging.getLogger(__name__).warning(
                "Skills model has no populated fields — "
                "the LLM may not have extracted any skills from the job description."
            )
        return self
 
    # ------------------------------------------------------------------ #
    # Convenience                                                          #
    # ------------------------------------------------------------------ #
 
    def all_skills(self) -> list[str]:
        """Flat, deduplicated list of every skill across all categories."""
        combined: list[str] = []
        for field_name in self.model_fields:
            combined.extend(getattr(self, field_name))
        return _deduplicate(combined)
 
    def by_category(self) -> dict[str, list[str]]:
        """
        Returns skills grouped by the `category` metadata tag defined in each Field.
        Useful for rendering grouped skill chips in a UI.
        """
        groups: dict[str, list[str]] = {}
        for field_name, field_info in self.model_fields.items():
            cat = (field_info.json_schema_extra or {}).get("category", "other")
            groups.setdefault(cat, [])
            groups[cat].extend(getattr(self, field_name))
        return {k: _deduplicate(v) for k, v in groups.items() if v}
 
 
class Job(BaseModel):
    id: Optional[str] = Field(None)
    title: Optional[str] = Field(None)
    standardizedTitle: Optional[str] = Field(None)
    companyName: Optional[str] = Field(None)
    companyLogo: Optional[str] = Field(None)
    location: Optional[str] = Field(None)
    country: Optional[str] = Field(None)
    workplaceTypes: List[str] = Field(default_factory=list)
    employmentType: Optional[str] = Field(None)
    seniorityLevel: Optional[str] = Field(None)
    jobFunction: List[str] = Field(default_factory=list)
    industries: List[str] = Field(default_factory=list)
    salary: Salary = Field(default_factory=Salary)
    experienceRequired: Optional[str] = Field(None)
    skills: Skills = Field(default_factory=Skills)
    responsibilities: List[str] = Field(default_factory=list)
    preferredQualifications: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)
    applicationMeta: ApplicationMeta = Field(default_factory=ApplicationMeta)

class Job(BaseModel):
    id: Optional[str] = Field(None)
    title: Optional[str] = Field(None)
    standardizedTitle: Optional[str] = Field(None)
    companyName: Optional[str] = Field(None)
    companyLogo: Optional[str] = Field(None)
    location: Optional[str] = Field(None)
    country: Optional[str] = Field(None)
    workplaceTypes: List[str] = Field(default_factory=list)
    employmentType: Optional[str] = Field(None)
    type: Optional[str] = Field(None)
    seniorityLevel: Optional[str] = Field(None)
    jobFunction: List[str] = Field(default_factory=list)
    industries: List[str] = Field(default_factory=list)
    salary: Salary = Field(default_factory=Salary)
    experienceRequired: Optional[str] = Field(None)
    skills: Skills = Field(default_factory=Skills)
    responsibilities: List[str] = Field(default_factory=list)
    preferredQualifications: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)
    applicationMeta: ApplicationMeta = Field(default_factory=ApplicationMeta)


class OpenRouterLLM:
    def __init__(self, model="openai/gpt-4o-mini", temperature=0):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = model
        self.temperature = temperature
        self.url = "https://openrouter.ai/api/v1/chat/completions"

    def generate(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": prompt}
            ]
        }

        response = requests.post(self.url, headers=headers, json=payload)

        if response.status_code != 200:
            raise Exception(f"OpenRouter error: {response.text}")

        return response.json()["choices"][0]["message"]["content"]


class JobParser:
    def __init__(self, llm: OpenRouterLLM):
        self.llm = llm
        self.skills_template = Skills().model_dump()

    def _build_prompt(self, jd_text: str) -> str:
        return f"""
You are an expert job parser.

Extract structured job data from the given job description.

RULES:
- Output ONLY valid JSON
- Do NOT hallucinate
- Use null or empty arrays if missing
- Follow schema strictly

SKILLS SCHEMA:
{json.dumps(self.skills_template, indent=2)}

JOB SCHEMA:
{Job.model_json_schema()}

Normalize:
- NLP → Natural Language Processing
- ML → Machine Learning

JOB DESCRIPTION:
\"\"\"{jd_text}\"\"\"
"""

    def parse(self, jd_text: str) -> Job:
        prompt = self._build_prompt(jd_text)

        raw_output = self.llm.generate(prompt)

        # Strip markdown code blocks if present
        raw_output = re.sub(r'```json\s*', '', raw_output)
        raw_output = re.sub(r'```\s*$', '', raw_output)

        print("Raw LLM output after stripping:")
        print(raw_output)
        print("---")

        try:
            data = json.loads(raw_output)
        except Exception:
            raise ValueError("Invalid JSON from LLM")

        # Handle None salary
        if data.get("salary") is None:
            data["salary"] = {}

        # Generate ID
        data["id"] = self._generate_id(data)

        return Job(**data)

    def _generate_id(self, data: dict) -> str:
        company = (data.get("companyName") or "company").lower().replace(" ", "-")
        title = (data.get("title") or "role").lower().replace(" ", "-")
        location = (data.get("location") or "loc").lower().replace(" ", "-")

        return f"{company}-{title}-{location}-{str(uuid.uuid4())[:6]}"

if __name__ == "__main__":
    # from openrouter_manager import OpenRouterLLM
    # from job_parser_full import JobParser

    jd_text = open("jd.txt").read()

    llm = OpenRouterLLM(model="openai/gpt-4o-mini")
    parser = JobParser(llm)

    job = parser.parse(jd_text)

    print(job.model_dump_json(indent=2))