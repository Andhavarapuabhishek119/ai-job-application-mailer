from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import streamlit as st

from ai.generator import EmailGenerator
from config.settings import (
    APP_DIRS,
    get_smtp_settings,
    load_candidate_config,
    load_env,
    save_candidate_config,
)
from database.db import EmailLogRepository, init_db
from emailer.sender import EmailSender
from emailer.throttle import RateLimiter
from parser.contact_parser import ContactParser
from parser.validators import ContactValidationResult


st.set_page_config(
    page_title="AI Job Application Mailer",
    page_icon="✉️",
    layout="wide",
)


def bootstrap() -> None:
    load_env()
    for directory in APP_DIRS:
        directory.mkdir(parents=True, exist_ok=True)
    init_db()
    st.session_state.setdefault("contacts", pd.DataFrame())
    st.session_state.setdefault("validation", None)
    st.session_state.setdefault("campaign_paused", False)


def save_uploaded_file(uploaded_file, destination: Path) -> Path | None:
    if uploaded_file is None:
        return None
    safe_name = Path(uploaded_file.name).name
    target = destination / safe_name
    target.write_bytes(uploaded_file.getbuffer())
    return target


def save_attachment(uploaded_file, filename: str) -> Path | None:
    if uploaded_file is None:
        return None
    target = Path("uploads") / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(uploaded_file.getbuffer())
    return target


def saved_attachment(filename: str) -> Path | None:
    path = Path("uploads") / filename
    return path if path.exists() else None


def render_dashboard(repo: EmailLogRepository) -> None:
    contacts = st.session_state.get("contacts", pd.DataFrame())
    stats = repo.stats()
    total_contacts = len(contacts)
    sent = stats.get("sent", 0)
    failed = stats.get("failed", 0)
    remaining = max(total_contacts - sent - failed, 0)

    st.title("AI Job Application Mailer")
    st.caption("Upload contacts, generate personalized applications, send safely, and export campaign reports.")

    cols = st.columns(4)
    cols[0].metric("Total Contacts", total_contacts)
    cols[1].metric("Emails Sent", sent)
    cols[2].metric("Failed Emails", failed)
    cols[3].metric("Remaining Contacts", remaining)

    st.subheader("Recent Activity")
    recent = repo.fetch_logs(limit=20)
    if recent.empty:
        st.info("No campaign activity yet.")
    else:
        st.dataframe(recent, use_container_width=True, hide_index=True)


def render_contacts() -> None:
    st.title("Contacts")
    st.write("Upload a PDF table, Excel workbook, or CSV containing HR Name, Company Name, and Email Address.")

    upload = st.file_uploader("Contact file", type=["pdf", "xlsx", "csv"])
    if upload:
        path = save_uploaded_file(upload, Path("uploads"))
        try:
            parser = ContactParser()
            validation: ContactValidationResult = parser.parse(path)
            st.session_state["contacts"] = validation.contacts
            st.session_state["validation"] = validation
            st.success(f"Loaded {len(validation.contacts)} clean contacts.")
        except Exception as exc:
            st.error(f"Could not parse contact file: {exc}")

    validation = st.session_state.get("validation")
    contacts = st.session_state.get("contacts", pd.DataFrame())
    if not contacts.empty:
        st.subheader("Clean Contacts")
        st.dataframe(contacts, use_container_width=True, hide_index=True)
        st.download_button(
            "Download Clean Contacts CSV",
            contacts.to_csv(index=False).encode("utf-8"),
            "clean_contacts.csv",
            "text/csv",
        )

    if validation:
        with st.expander("Validation Issues", expanded=False):
            for title, frame in {
                "Missing Fields": validation.missing_fields,
                "Invalid Emails": validation.invalid_emails,
                "Duplicate Emails": validation.duplicates,
            }.items():
                st.write(title)
                if frame.empty:
                    st.caption("None")
                else:
                    st.dataframe(frame, use_container_width=True, hide_index=True)


def render_settings() -> None:
    st.title("Profile Update")
    current = load_candidate_config()

    with st.form("candidate_settings"):
        full_name = st.text_input("Full Name", value=current.get("full_name", ""))
        phone_number = st.text_input("Phone Number", value=current.get("phone_number", ""))
        email = st.text_input("Email", value=current.get("email", ""))
        linkedin = st.text_input("LinkedIn URL", value=current.get("linkedin", ""))
        github = st.text_input("GitHub URL", value=current.get("github", ""))
        portfolio = st.text_input("Portfolio URL", value=current.get("portfolio", ""))
        skills = st.text_area("Skills", value=current.get("skills", ""), height=110)
        experience_summary = st.text_area(
            "Experience Summary",
            value=current.get("experience_summary", ""),
            height=150,
        )
        use_openai = st.checkbox("Use OpenAI personalization", value=current.get("use_openai", False))
        max_per_hour = st.number_input(
            "Maximum emails per hour",
            min_value=1,
            max_value=200,
            value=int(current.get("max_emails_per_hour", 25)),
        )
        submitted = st.form_submit_button("Save Profile")

    if submitted:
        save_candidate_config(
            {
                "full_name": full_name,
                "phone_number": phone_number,
                "email": email,
                "linkedin": linkedin,
                "github": github,
                "portfolio": portfolio,
                "skills": skills,
                "experience_summary": experience_summary,
                "use_openai": use_openai,
                "max_emails_per_hour": max_per_hour,
            }
        )
        st.success("Profile saved locally.")

    st.subheader("SMTP Environment")
    smtp = get_smtp_settings()
    st.code(
        "\n".join(
            [
                f"SMTP_HOST={'set' if smtp.host else 'missing'}",
                f"SMTP_PORT={smtp.port or 'missing'}",
                f"SMTP_USERNAME={'set' if smtp.username else 'missing'}",
                f"SMTP_PASSWORD={'set' if smtp.password else 'missing'}",
            ]
        )
    )


def render_send_campaign(repo: EmailLogRepository) -> None:
    st.title("Send Campaign")
    contacts = st.session_state.get("contacts", pd.DataFrame())
    config = load_candidate_config()

    current_resume = saved_attachment("resume.pdf")
    current_cover_letter = saved_attachment("cover_letter.pdf")

    col_a, col_b = st.columns(2)
    with col_a:
        if current_resume:
            st.success("Saved resume.pdf is ready.")
        else:
            st.info("No resume saved yet.")
        resume = st.file_uploader("Add or replace resume PDF", type=["pdf"], key="resume_upload")
    with col_b:
        if current_cover_letter:
            st.success("Saved cover_letter.pdf is ready.")
        else:
            st.info("No cover letter saved yet.")
        cover_letter = st.file_uploader("Add or replace cover letter PDF", type=["pdf"], key="cover_letter_upload")

    if resume:
        current_resume = save_attachment(resume, "resume.pdf")
        st.success("Resume saved. It will be reused until you replace it.")
    if cover_letter:
        current_cover_letter = save_attachment(cover_letter, "cover_letter.pdf")
        st.success("Cover letter saved. It will be reused until you replace it.")

    st.write(f"Ready contacts: {len(contacts)}")
    st.toggle("Pause campaign", key="campaign_paused")

    preview_contact = contacts.iloc[0].to_dict() if not contacts.empty else None
    if preview_contact:
        preview = EmailGenerator(config).build_email(preview_contact)
        with st.expander("Email Preview", expanded=True):
            st.write(f"Subject: {preview.subject}")
            st.text(preview.body)

    if st.button("Start Sending", type="primary", disabled=contacts.empty):
        missing = []
        smtp = get_smtp_settings()
        if not smtp.is_complete:
            missing.append("SMTP environment variables")
        if not current_resume:
            missing.append("resume.pdf")
        if not current_cover_letter:
            missing.append("cover_letter.pdf")
        if not config.get("full_name"):
            missing.append("candidate settings")
        if missing:
            st.error("Please configure: " + ", ".join(missing))
            return

        sender = EmailSender(smtp)
        generator = EmailGenerator(config)
        limiter = RateLimiter(max_per_hour=int(config.get("max_emails_per_hour", 25)))
        progress = st.progress(0)
        status_box = st.empty()

        attachments = [current_resume, current_cover_letter]
        for idx, row in contacts.iterrows():
            if st.session_state.get("campaign_paused"):
                status_box.warning("Campaign paused. Unpause and start again to continue.")
                break

            contact = row.to_dict()
            email = generator.build_email(contact)
            try:
                limiter.wait_if_needed()
                sender.send(
                    to_email=contact["email"],
                    subject=email.subject,
                    body=email.body,
                    attachments=attachments,
                )
                repo.insert_log(contact, "sent", "")
                status_box.success(f"Sent to {contact['email']}")
            except Exception as exc:
                repo.insert_log(contact, "failed", str(exc))
                status_box.error(f"Failed for {contact['email']}: {exc}")

            progress.progress((idx + 1) / len(contacts))
            if idx < len(contacts) - 1:
                time.sleep(limiter.random_delay_seconds())


def render_logs(repo: EmailLogRepository) -> None:
    st.title("Logs")
    logs = repo.fetch_logs()
    if logs.empty:
        st.info("No logs yet.")
        return
    st.dataframe(logs, use_container_width=True, hide_index=True)

    sent = logs[logs["status"] == "sent"]
    failed = logs[logs["status"] == "failed"]
    c1, c2 = st.columns(2)
    c1.download_button("Export Sent CSV", sent.to_csv(index=False).encode("utf-8"), "sent_emails.csv", "text/csv")
    c2.download_button(
        "Export Failed CSV",
        failed.to_csv(index=False).encode("utf-8"),
        "failed_emails.csv",
        "text/csv",
    )


def main() -> None:
    bootstrap()
    repo = EmailLogRepository()

    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Contacts", "Profile Update", "Send Campaign", "Logs"],
    )

    if page == "Dashboard":
        render_dashboard(repo)
    elif page == "Contacts":
        render_contacts()
    elif page == "Profile Update":
        render_settings()
    elif page == "Send Campaign":
        render_send_campaign(repo)
    elif page == "Logs":
        render_logs(repo)


if __name__ == "__main__":
    main()
