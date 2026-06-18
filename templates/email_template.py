from __future__ import annotations


def _section(label: str, value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    return f"\n{label}:\n{value}\n"


def render_email(candidate: dict, hr_name: str, company_name: str, custom_paragraph: str = "") -> str:
    name = (candidate.get("full_name", "") or "").strip()
    phone = (candidate.get("phone_number", "") or "").strip()
    skills = (candidate.get("skills", "") or "").strip()
    linkedin = (candidate.get("linkedin", "") or "").strip()
    github = (candidate.get("github", "") or "").strip()
    portfolio = (candidate.get("portfolio", "") or "").strip()
    email = (candidate.get("email", "") or "").strip()
    experience = (candidate.get("experience_summary", "") or "").strip()

    optional_paragraph = f"\n{custom_paragraph}\n" if custom_paragraph else ""
    profile_sections = "".join(
        [
            _section("Skills", skills),
            _section("Email", email),
            _section("LinkedIn", linkedin),
            _section("GitHub", github),
            _section("Portfolio", portfolio),
        ]
    )
    phone_line = f"\n{phone}" if phone else ""

    return f"""Dear {hr_name},

I hope you are doing well.

My name is {name}. {experience or "I am a software developer with experience in Python, AI, Full Stack Development, and Automation."}
{optional_paragraph}
I am interested in exploring opportunities at {company_name}. My resume and cover letter are attached for your review.
{profile_sections}

Thank you for your time and consideration.

Regards,
{name}{phone_line}
"""
