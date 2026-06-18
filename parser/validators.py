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
    df = df.copy()
    df.columns = _unique_columns(df.columns)
    column_map = {}
    for col in df.columns:
        key = _canonical_key(col)
        if key in {"hr", "hr_name", "hrperson", "name", "contact_name", "contactname", "recruiter_name", "recruitername", "recruiter", "hr_person"}:
            column_map[col] = "hr_name"
        elif key in {"company", "company_name", "companyname", "organization", "organisation", "employer"}:
            column_map[col] = "company_name"
        elif key in {"email", "email_address", "emailaddress", "mail", "e_mail", "emailid", "email_id"}:
            column_map[col] = "email"
    normalized = df.rename(columns=column_map)
    normalized = normalized.loc[:, ~normalized.columns.duplicated()].copy()
    return infer_missing_columns(normalized)


def _unique_columns(columns: object) -> list[str]:
    seen: dict[str, int] = {}
    unique: list[str] = []
    for index, column in enumerate(columns):
        base = str(column or "").strip() or f"column_{index + 1}"
        count = seen.get(base, 0)
        seen[base] = count + 1
        unique.append(base if count == 0 else f"{base}_{count + 1}")
    return unique


def _canonical_key(value: object) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")
    return key.replace("_", "") if key in {"company_name", "email_address", "email_id"} else key


def infer_missing_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    remaining = [column for column in df.columns if column not in REQUIRED_COLUMNS]

    if "email" not in df.columns:
        email_column = _best_email_column(df, remaining)
        if email_column is not None:
            df = df.rename(columns={email_column: "email"})
            remaining = [column for column in df.columns if column not in REQUIRED_COLUMNS]

    if "company_name" not in df.columns:
        company_column = _find_by_name(remaining, {"company", "company_name", "companyname", "organization", "organisation", "employer"})
        if company_column is None and "email" in df.columns and len(remaining) >= 2:
            company_column = remaining[-1]
        if company_column is not None:
            df = df.rename(columns={company_column: "company_name"})
            remaining = [column for column in df.columns if column not in REQUIRED_COLUMNS]

    if "hr_name" not in df.columns:
        hr_column = _find_by_name(remaining, {"hr", "hr_name", "hrperson", "name", "contact_name", "contactname", "recruiter", "recruiter_name", "recruitername"})
        if hr_column is None and remaining:
            hr_column = remaining[0]
        if hr_column is not None:
            df = df.rename(columns={hr_column: "hr_name"})

    return df


def _find_by_name(columns: list[object], names: set[str]) -> object | None:
    for column in columns:
        if _canonical_key(column) in names:
            return column
    return None


def _best_email_column(df: pd.DataFrame, columns: list[object]) -> object | None:
    best_column = None
    best_score = 0
    for column in columns:
        values = df[column].fillna("").astype(str).str.strip()
        score = values.apply(lambda value: bool(EMAIL_PATTERN.match(value))).sum()
        if "email" in _canonical_key(column):
            score += 2
        if score > best_score:
            best_score = score
            best_column = column
    return best_column if best_score > 0 else None


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
