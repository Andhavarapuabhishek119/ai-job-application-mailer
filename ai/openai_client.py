from __future__ import annotations

import os
import time


class OpenAIPersonalizer:
    def __init__(self, enabled: bool, retries: int = 3):
        self.enabled = enabled and bool(os.getenv("OPENAI_API_KEY"))
        self.retries = retries

    def generate(self, company_name: str, candidate_summary: str) -> str:
        if not self.enabled:
            return ""

        try:
            from openai import OpenAI
        except Exception:
            return ""

        client = OpenAI()
        prompt = (
            "Write one concise, professional paragraph for a job application email. "
            "Explain why the candidate is interested in the company. "
            "Avoid making unverifiable claims about the company. "
            f"Company: {company_name}\n"
            f"Candidate summary: {candidate_summary}"
        )

        for attempt in range(1, self.retries + 1):
            try:
                response = client.responses.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
                    input=prompt,
                    max_output_tokens=140,
                )
                return response.output_text.strip()
            except Exception:
                if attempt == self.retries:
                    return ""
                time.sleep(2**attempt)
        return ""
