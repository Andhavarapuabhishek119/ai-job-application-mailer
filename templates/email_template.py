from __future__ import annotations


def render_email(candidate: dict, hr_name: str, company_name: str, custom_paragraph: str = "") -> str:
    name = (candidate.get("full_name", "") or "").strip()
    phone = (candidate.get("phone_number", "") or "").strip()
    email = (candidate.get("email", "") or "").strip()
    skills = (candidate.get("skills", "") or "").strip()

    skill_text = skills or "Python, SQL, Machine Learning, React.js, and Web Development"
    company_text = company_name or "[Company Name]"
    phone_line = f"\n{phone}" if phone else ""
    email_line = f"\n[{email}]" if email else ""
    optional_paragraph = f"\n{custom_paragraph}\n" if custom_paragraph else ""

    return f"""Dear {hr_name},

I am interested in the [Job Title] position at {company_text}. I recently graduated in Artificial Intelligence and Machine Learning and have hands-on experience in {skill_text} through projects and internships.
{optional_paragraph}
I have attached my resume for your review. Thank you for your consideration, and I look forward to hearing from you.

Best regards,

{name}{phone_line}{email_line}
"""
