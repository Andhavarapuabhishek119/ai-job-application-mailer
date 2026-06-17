from __future__ import annotations

from dataclasses import dataclass

from ai.openai_client import OpenAIPersonalizer
from templates.email_template import render_email


@dataclass
class GeneratedEmail:
    subject: str
    body: str


class EmailGenerator:
    def __init__(self, candidate_config: dict):
        self.config = candidate_config
        self.personalizer = OpenAIPersonalizer(enabled=bool(candidate_config.get("use_openai")))

    def build_email(self, contact: dict) -> GeneratedEmail:
        company_name = contact.get("company_name", "").strip()
        hr_name = contact.get("hr_name", "").strip() or "Hiring Team"
        subject = f"Application for Software Engineer Opportunities at {company_name}"
        custom_paragraph = self.personalizer.generate(
            company_name=company_name,
            candidate_summary=self.config.get("experience_summary", ""),
        )
        body = render_email(
            candidate=self.config,
            hr_name=hr_name,
            company_name=company_name,
            custom_paragraph=custom_paragraph,
        )
        return GeneratedEmail(subject=subject, body=body)
