from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd


EMAIL_PATTERN = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)
REQUIRED_COLUMNS = ["hr_name", "company_name", "email"]


@dataclass
class ContactValidationResult:
    contacts: pd.DataFrame
    missing_fields: pd.DataFrame
    invalid_emails: pd.DataFrame
    duplicates: pd.DataFrame


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    column_map = {}
    for col in df.columns:
        key = str(col).strip().lower().replace(" ", "_").replace("-", "_")
        if key in {"hr", "hr_name", "name", "contact_name", "recruiter_name"}:
            column_map[col] = "hr_name"
        elif key in {"company", "company_name", "organization", "organisation"}:
            column_map[col] = "company_name"
        elif key in {"email", "email_address", "mail", "e_mail"}:
            column_map[col] = "email"
    return df.rename(columns=column_map)


def validate_contacts(df: pd.DataFrame) -> ContactValidationResult:
    df = normalize_columns(df).copy()
    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    df = df[REQUIRED_COLUMNS].fillna("")
    for column in REQUIRED_COLUMNS:
        df[column] = df[column].astype(str).str.strip()

    missing_mask = (df["company_name"] == "") | (df["email"] == "")
    missing_fields = df[missing_mask].copy()

    email_mask = df["email"].apply(lambda value: bool(EMAIL_PATTERN.match(value)))
    invalid_emails = df[(df["email"] != "") & ~email_mask].copy()

    duplicate_mask = df["email"].str.lower().duplicated(keep="first") & (df["email"] != "")
    duplicates = df[duplicate_mask].copy()

    clean = df[~missing_mask & email_mask & ~duplicate_mask].copy()
    clean.loc[clean["hr_name"] == "", "hr_name"] = "Hiring Team"
    clean = clean.drop_duplicates(subset=["email"], keep="first").reset_index(drop=True)

    return ContactValidationResult(
        contacts=clean,
        missing_fields=missing_fields.reset_index(drop=True),
        invalid_emails=invalid_emails.reset_index(drop=True),
        duplicates=duplicates.reset_index(drop=True),
    )
