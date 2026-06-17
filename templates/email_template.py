from __future__ import annotations


def render_email(candidate: dict, hr_name: str, company_name: str, custom_paragraph: str = "") -> str:
    name = candidate.get("full_name", "")
    phone = candidate.get("phone_number", "")
    skills = candidate.get("skills", "")
    linkedin = candidate.get("linkedin", "")
    github = candidate.get("github", "")
    portfolio = candidate.get("portfolio", "")
    experience = candidate.get("experience_summary", "")

    optional_paragraph = f"\n{custom_paragraph}\n" if custom_paragraph else ""

    return f"""Dear {hr_name},

I hope you are doing well.

My name is {name}. {experience or "I am a software developer with experience in Python, AI, Full Stack Development, and Automation."}
{optional_paragraph}
I am interested in exploring opportunities at {company_name}. My resume and cover letter are attached for your review.

Skills:
{skills}

LinkedIn:
{linkedin}

GitHub:
{github}

Portfolio:
{portfolio}

Thank you for your time and consideration.

Regards,
{name}
{phone}
"""
