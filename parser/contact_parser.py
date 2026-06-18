from __future__ import annotations

from pathlib import Path

import pandas as pd
import pdfplumber

from parser.validators import ContactValidationResult, validate_contacts


class ContactParser:
    allowed_extensions = {".pdf", ".xlsx", ".csv"}

    def parse(self, path: Path) -> ContactValidationResult:
        path = Path(path)
        extension = path.suffix.lower()
        if extension not in self.allowed_extensions:
            raise ValueError("Unsupported file type. Upload PDF, XLSX, or CSV.")

        if extension == ".csv":
            df = pd.read_csv(path)
        elif extension == ".xlsx":
            df = pd.read_excel(path, engine="openpyxl")
        else:
            df = self._parse_pdf_tables(path)

        if df.empty:
            raise ValueError("No tabular contact data was found.")
        return validate_contacts(df)

    def _parse_pdf_tables(self, path: Path) -> pd.DataFrame:
        frames: list[pd.DataFrame] = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    if self._looks_like_header(table[0]):
                        header = table[0]
                        rows = table[1:]
                    else:
                        header = [f"column_{index + 1}" for index in range(len(table[0]))]
                        rows = table
                    frames.append(pd.DataFrame(rows, columns=header))

        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)

    @staticmethod
    def _looks_like_header(row: list[object]) -> bool:
        text = " ".join(str(cell or "").lower() for cell in row)
        header_words = ["name", "company", "email", "mail", "organization", "organisation", "recruiter"]
        return any(word in text for word in header_words) and "@" not in text
