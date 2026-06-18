from __future__ import annotations


def render_email(candidate: dict, hr_name: str, company_name: str, custom_paragraph: str = "") -> str:
    name = (candidate.get("full_name", "") or "").strip()
    phone = (candidate.get("phone_number", "") or "").strip()
    email = (candidate.get("email", "") or "").strip()
    skills = (candidate.get("skills", "") or "").strip()

    skill_text = skills or "Python, SQL, Machine Learning, React.js, HTML, CSS, and JavaScript"
    phone_line = f"\n{phone}" if phone else ""
    email_line = f"\n[{email}]" if email else ""
    optional_paragraph = f"\n{custom_paragraph}\n" if custom_paragraph else ""

    return f"""Dear {hr_name},

I hope you are doing well.

I am {name}, a recent B.Tech graduate in Artificial Intelligence and Machine Learning. I am currently seeking entry-level opportunities in Software Development, Python Development, Web Development, or related technology roles.
{optional_paragraph}
I have hands-on experience in {skill_text} through internships and academic projects. I have attached my resume for your review and would appreciate your consideration for any suitable openings.

Thank you for your time. I look forward to hearing from you.

Best Regards,

{name}{phone_line}{email_line}
"""
