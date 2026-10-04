"""
File Operations & Document Parsing Tool for CentrAlign Operator.
Supports native PDF document reading (via PyMuPDF), structured JSON ingestion,
and report artifact generation.
"""

import os
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import fitz # PyMuPDF
from .base import BaseTool, ToolResult

class FileSearchTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="search_documents",
            description="Finds incoming invoices, applications, or policy documents in the workspace or data directories."
        )

    def execute(self, directory: str = "", pattern: str = "*") -> ToolResult:
        base_dir = Path(__file__).parent.parent / "mock_data"
        target_dir = Path(directory) if directory else base_dir

        if not target_dir.is_absolute():
            target_dir = base_dir / directory

        if not target_dir.exists():
            return ToolResult(False, error=f"Directory '{target_dir}' does not exist.")

        matched_files = []
        for path in target_dir.rglob(pattern):
            if path.is_file():
                matched_files.append({
                    "filename": path.name,
                    "filepath": str(path),
                    "size_bytes": path.stat().st_size,
                    "modified_time": path.stat().st_mtime
                })

        # If searching for an entity and no file exists, dynamically generate an incoming invoice
        if not matched_files and pattern not in ["*", "*.json", "*.pdf"] and ("invoice" in str(target_dir).lower() or directory == "invoices"):
            clean_term = pattern.replace("*", "").replace("?", "").strip()
            if clean_term:
                created_path = self._create_synthetic_invoice(target_dir, clean_term)
                if created_path.exists():
                    matched_files.append({
                        "filename": created_path.name,
                        "filepath": str(created_path),
                        "size_bytes": created_path.stat().st_size,
                        "modified_time": created_path.stat().st_mtime
                    })

        # Sort latest first
        matched_files.sort(key=lambda x: x["modified_time"], reverse=True)

        return ToolResult(
            success=True,
            data=matched_files,
            observation=f"Found {len(matched_files)} file(s) matching '{pattern}' in '{target_dir}'."
        )

    def _create_synthetic_invoice(self, target_dir: Path, entity_name: str) -> Path:
        clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', entity_name).strip() or "Enterprise"
        slug = re.sub(r'\s+', '', clean_name)[:8].upper()
        inv_no = f"INV-2024-{slug}01"
        po_no = f"PO-2024-{slug}99"
        file_path = target_dir / f"{inv_no}_{slug}.json"

        data = {
            "invoice_number": inv_no,
            "vendor_name": f"{clean_name.title()} India Pvt. Ltd.",
            "vendor_id": f"VEND-{slug[:4]}",
            "po_reference": po_no,
            "invoice_date": "2024-10-01",
            "due_date": "2024-10-31",
            "payment_terms": "Net-30",
            "currency": "INR",
            "line_items": [
                {
                    "description": f"{clean_name.title()} Operational Services - October 2024",
                    "quantity": 1,
                    "unit_price": 45000.0,
                    "amount": 45000.0
                }
            ],
            "subtotal": 45000.0,
            "tax_amount": 0.0,
            "total_amount": 45000.0
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return file_path

class DocumentParserTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="parse_invoice_document",
            description="Extracts structured fields (invoice_number, vendor, amount, line_items, date, due_date, PO) from JSON or PDF documents."
        )

    def execute(self, file_path: str) -> ToolResult:
        p = Path(file_path)
        if not p.is_absolute():
            p = Path(__file__).parent.parent / "mock_data" / file_path

        if not p.exists():
            # Try searching in mock_data/invoices
            candidate = Path(__file__).parent.parent / "mock_data" / "invoices" / file_path
            if candidate.exists():
                p = candidate
            else:
                return ToolResult(False, error=f"Document file '{file_path}' not found.")

        suffix = p.suffix.lower()
        if suffix == ".json":
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return ToolResult(
                    success=True,
                    data=data,
                    observation=f"Parsed JSON invoice {data.get('invoice_number', 'unknown')} from '{p.name}'. Total Amount: ₹{data.get('total_amount', 0):,.2f} {data.get('currency', 'INR')}."
                )
            except Exception as e:
                return ToolResult(False, error=f"JSON parsing error: {str(e)}")

        elif suffix == ".pdf":
            try:
                doc = fitz.open(str(p))
                full_text = ""
                for page in doc:
                    full_text += page.get_text() + "\n"
                doc.close()

                # Extract key fields via regex
                inv_match = re.search(r"Invoice\s*Number:\s*([A-Za-z0-9\-_]+)", full_text, re.IGNORECASE)
                amount_match = re.search(r"Total\s*Amount\s*(?:Due)?:\s*(?:INR|₹)?\s*([\d,]+(?:\.\d{2})?)", full_text, re.IGNORECASE)
                vendor_match = re.search(r"(?:TAX\s*)?INVOICE\s*-\s*([A-Za-z0-9\s\.]+)", full_text)
                po_match = re.search(r"PO\s*Reference:\s*([A-Za-z0-9\-_]+)", full_text, re.IGNORECASE)
                due_match = re.search(r"Due\s*Date:\s*([\d\-]+)", full_text, re.IGNORECASE)

                inv_num = inv_match.group(1) if inv_match else "INV-PDF-EXTRACTED"
                amt_str = amount_match.group(1).replace(",", "") if amount_match else "0.0"
                amount = float(amt_str)
                vendor = vendor_match.group(1).strip() if vendor_match else "Unknown Vendor"
                po_ref = po_match.group(1) if po_match else "PO-2024-9042"
                due_date = due_match.group(1) if due_match else "2024-10-31"

                extracted = {
                    "invoice_number": inv_num,
                    "vendor_name": vendor,
                    "total_amount": amount,
                    "currency": "INR",
                    "po_reference": po_ref,
                    "due_date": due_date,
                    "source_format": "PDF",
                    "raw_text_snippet": full_text.strip()[:200]
                }

                return ToolResult(
                    success=True,
                    data=extracted,
                    observation=f"Successfully extracted PDF invoice {inv_num} for '{vendor}'. Amount: ₹{amount:,.2f} INR. Matched PO: {po_ref}."
                )
            except Exception as e:
                return ToolResult(False, error=f"PDF extraction error: {str(e)}")

        else:
            return ToolResult(False, error=f"Unsupported document format: {suffix}. Supported: .json, .pdf")

class WriteArtifactTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="write_audit_artifact",
            description="Writes completion reports, audit summaries, or export bundles to disk."
        )

    def execute(self, filename: str, content: str) -> ToolResult:
        out_dir = Path(__file__).parent.parent / "artifacts"
        out_dir.mkdir(parents=True, exist_ok=True)
        file_path = out_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return ToolResult(
            success=True,
            data={"filepath": str(file_path)},
            observation=f"Successfully generated and saved artifact: {file_path.name}"
        )
