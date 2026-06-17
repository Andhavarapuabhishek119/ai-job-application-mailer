# AI Job Application Mailer

A production-ready Streamlit application for sending personalized job application emails from uploaded contact lists.

## Features

- Upload contacts from PDF tables, Excel `.xlsx`, or CSV files.
- Validate missing fields, invalid emails, and duplicate email addresses.
- Upload `resume.pdf` and `cover_letter.pdf` as temporary attachments.
- Store candidate profile settings locally in `config/candidate.json`.
- Generate personalized email subjects and bodies.
- Optional OpenAI paragraph personalization with retries and graceful fallback.
- Send through Gmail SMTP, Outlook SMTP, or any SMTP provider configured with environment variables.
- Random sending delay between 20 and 60 seconds.
- Configurable maximum emails per hour.
- Pause campaign from the Streamlit UI.
- Store sent and failed email logs in SQLite.
- Export sent and failed reports as CSV.

## Project Structure

```text
project/
├── app.py
├── parser/
├── emailer/
├── ai/
├── database/
├── templates/
├── uploads/
├── logs/
├── config/
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Installation

Python 3.11 or newer is recommended.

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux or macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment Setup

Create a `.env` file from `.env.example`.

```bash
cp .env.example .env
```

For Gmail, use an app password rather than your normal account password.

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

For Outlook:

```env
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=your-password-or-app-password
```

OpenAI personalization is optional:

```env
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4.1-mini
```

## Run

```bash
streamlit run app.py
```

Open the local Streamlit URL shown in the terminal.

## Expected Contact Columns

The app accepts common variants and normalizes them:

- `HR Name`, `Name`, `Recruiter Name`
- `Company Name`, `Company`, `Organization`
- `Email Address`, `Email`, `Mail`

If HR name is blank, the email uses `Hiring Team`.

## Database Schema

SQLite database: `database/email_logs.sqlite3`

```sql
CREATE TABLE IF NOT EXISTS email_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    hr_name TEXT NOT NULL,
    email TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('sent', 'failed')),
    error_message TEXT
);
```

## Deployment Notes

- Keep `.env` private and never commit real passwords.
- Use SMTP app passwords when available.
- Start with a low hourly limit and increase gradually.
- Review generated email previews before sending a campaign.
- On a VPS, run Streamlit behind a reverse proxy and restrict access with authentication.
