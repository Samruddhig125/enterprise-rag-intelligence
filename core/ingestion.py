"""
Enterprise Data Ingestion Engine
Handles multi-format data: TXT/PDF, CSV, JSON logs
Chunks, tags, and indexes all content with source metadata
"""

import os
import json
import csv
import glob
from typing import Optional
from dataclasses import dataclass, field


#  DATA CLASSES 

@dataclass
class DataChunk:
    chunk_id: str
    content: str
    source_name: str        # human-readable e.g. "Q4 Financial Report"
    source_file: str        # filename
    source_type: str        # pdf | csv | json | report
    department: str         # who owns this data
    classification: str     # CONFIDENTIAL | INTERNAL | PUBLIC
    page_or_row: str        # page number / row range / log entry range
    metadata: dict = field(default_factory=dict)


#  INGESTION ENGINE 

class DataIngestionEngine:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.chunks: list[DataChunk] = []

    def ingest_all(self) -> list[DataChunk]:
        self.chunks = []
        self._ingest_documents()
        self._ingest_csvs()
        self._ingest_json_logs()
        print(f"[Ingestion] Total chunks created: {len(self.chunks)}")
        return self.chunks

    # ── TEXT / DOCUMENT FILES ────────────────────────────────────────────────

    def _ingest_documents(self):
        source_meta = {
            "Q4_Financial_Report_2024.txt": {
                "name": "Q4 Financial Report 2024",
                "dept": "Finance",
                "classification": "CONFIDENTIAL",
                "type": "pdf",
            },
            "HR_Policy_Handbook_2024.txt": {
                "name": "HR Policy Handbook 2024",
                "dept": "HR",
                "classification": "INTERNAL",
                "type": "pdf",
            },
            "IT_Security_Policy_2024.txt": {
                "name": "IT Security Policy 2024",
                "dept": "IT Security",
                "classification": "INTERNAL",
                "type": "pdf",
            },
            "Operations_Summary_Dec2024.txt": {
                "name": "Operations Summary Dec 2024",
                "dept": "Operations",
                "classification": "INTERNAL",
                "type": "report",
            },
            "Compliance_Audit_2024.txt": {
                "name": "Compliance Audit Report 2024",
                "dept": "Legal & Compliance",
                "classification": "CONFIDENTIAL",
                "type": "pdf",
            },
        }

        for folder in ["pdfs", "reports"]:
            folder_path = os.path.join(self.data_dir, folder)
            for fpath in glob.glob(os.path.join(folder_path, "*.txt")):
                fname = os.path.basename(fpath)
                meta = source_meta.get(fname, {
                    "name": fname.replace(".txt", "").replace("_", " "),
                    "dept": "General",
                    "classification": "INTERNAL",
                    "type": "pdf" if folder == "pdfs" else "report",
                })
                with open(fpath) as f:
                    text = f.read()
                self._chunk_text(text, meta, fname)

    def _chunk_text(self, text: str, meta: dict, fname: str):
        """Chunk text by paragraphs, max ~600 chars per chunk"""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip() and len(p.strip()) > 30]
        chunk_size = 3  # paragraphs per chunk
        for i in range(0, len(paragraphs), chunk_size):
            group = paragraphs[i:i + chunk_size]
            content = "\n\n".join(group)
            chunk = DataChunk(
                chunk_id=f"{fname}-chunk-{i // chunk_size}",
                content=content,
                source_name=meta["name"],
                source_file=fname,
                source_type=meta["type"],
                department=meta["dept"],
                classification=meta["classification"],
                page_or_row=f"Section {i // chunk_size + 1}",
                metadata={"file": fname, "folder": "docs"},
            )
            self.chunks.append(chunk)

    #  CSV FILES 

    def _ingest_csvs(self):
        csv_meta = {
            "employees.csv": {
                "name": "Employee Directory",
                "dept": "HR",
                "classification": "CONFIDENTIAL",
            },
            "vendor_contracts.csv": {
                "name": "Vendor Contracts",
                "dept": "Finance",
                "classification": "CONFIDENTIAL",
            },
            "it_assets.csv": {
                "name": "IT Asset Inventory",
                "dept": "IT",
                "classification": "INTERNAL",
            },
        }

        csv_dir = os.path.join(self.data_dir, "csv")
        for fpath in glob.glob(os.path.join(csv_dir, "*.csv")):
            fname = os.path.basename(fpath)
            meta = csv_meta.get(fname, {"name": fname, "dept": "General", "classification": "INTERNAL"})
            with open(fpath, newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            # Create a summary chunk
            summary = self._summarize_csv(fname, rows, meta)
            self.chunks.append(DataChunk(
                chunk_id=f"{fname}-summary",
                content=summary,
                source_name=meta["name"],
                source_file=fname,
                source_type="csv",
                department=meta["dept"],
                classification=meta["classification"],
                page_or_row="Full table summary",
                metadata={"rows": len(rows), "columns": list(rows[0].keys()) if rows else []},
            ))

            # Create row-group chunks (10 rows per chunk)
            chunk_size = 10
            for i in range(0, len(rows), chunk_size):
                group = rows[i:i + chunk_size]
                content = self._rows_to_text(group, meta["name"])
                self.chunks.append(DataChunk(
                    chunk_id=f"{fname}-rows-{i}-{i + chunk_size}",
                    content=content,
                    source_name=meta["name"],
                    source_file=fname,
                    source_type="csv",
                    department=meta["dept"],
                    classification=meta["classification"],
                    page_or_row=f"Rows {i + 1}–{min(i + chunk_size, len(rows))}",
                    metadata={"row_start": i, "row_end": i + chunk_size},
                ))

    def _summarize_csv(self, fname: str, rows: list[dict], meta: dict) -> str:
        if not rows:
            return f"{meta['name']}: Empty dataset"
        cols = list(rows[0].keys())
        lines = [f"Dataset: {meta['name']} ({fname})"]
        lines.append(f"Total records: {len(rows)}")
        lines.append(f"Columns: {', '.join(cols)}")
        lines.append(f"Department: {meta['dept']} | Classification: {meta['classification']}")
        lines.append("")

        # Show first 5 rows as sample
        lines.append("Sample records:")
        for row in rows[:5]:
            lines.append("  " + " | ".join(f"{k}: {v}" for k, v in row.items()))
        return "\n".join(lines)

    def _rows_to_text(self, rows: list[dict], source_name: str) -> str:
        if not rows:
            return ""
        lines = [f"Records from {source_name}:"]
        for row in rows:
            lines.append("  " + " | ".join(f"{k}: {v}" for k, v in row.items()))
        return "\n".join(lines)

    #  JSON LOGS

    def _ingest_json_logs(self):
        log_meta = {
            "security_audit_logs.json": {
                "name": "Security Audit Logs",
                "dept": "IT Security",
                "classification": "CONFIDENTIAL",
            },
            "application_logs.json": {
                "name": "Application Performance Logs",
                "dept": "Operations",
                "classification": "INTERNAL",
            },
        }

        log_dir = os.path.join(self.data_dir, "json_logs")
        for fpath in glob.glob(os.path.join(log_dir, "*.json")):
            fname = os.path.basename(fpath)
            meta = log_meta.get(fname, {"name": fname, "dept": "IT", "classification": "INTERNAL"})
            with open(fpath) as f:
                logs = json.load(f)

            # Summary chunk
            self.chunks.append(DataChunk(
                chunk_id=f"{fname}-summary",
                content=self._summarize_logs(logs, meta),
                source_name=meta["name"],
                source_file=fname,
                source_type="json",
                department=meta["dept"],
                classification=meta["classification"],
                page_or_row="Summary",
                metadata={"total_events": len(logs)},
            ))

            # Chunked log entries (15 per chunk)
            chunk_size = 15
            for i in range(0, len(logs), chunk_size):
                group = logs[i:i + chunk_size]
                content = self._logs_to_text(group, meta["name"])
                self.chunks.append(DataChunk(
                    chunk_id=f"{fname}-entries-{i}",
                    content=content,
                    source_name=meta["name"],
                    source_file=fname,
                    source_type="json",
                    department=meta["dept"],
                    classification=meta["classification"],
                    page_or_row=f"Entries {i + 1}–{min(i + chunk_size, len(logs))}",
                    metadata={"entry_start": i},
                ))

    def _summarize_logs(self, logs: list[dict], meta: dict) -> str:
        lines = [f"Log File: {meta['name']}"]
        lines.append(f"Total entries: {len(logs)}")
        lines.append(f"Department: {meta['dept']} | Classification: {meta['classification']}")

        if logs:
            # Severity distribution
            severities = {}
            event_types = {}
            for log in logs:
                sev = log.get("severity", log.get("status_code", "unknown"))
                sev = str(sev)
                severities[sev] = severities.get(sev, 0) + 1
                et = log.get("event_type", log.get("service", "unknown"))
                event_types[et] = event_types.get(et, 0) + 1

            lines.append("\nSeverity/Status distribution:")
            for k, v in sorted(severities.items(), key=lambda x: -x[1])[:8]:
                lines.append(f"  {k}: {v} events")

            lines.append("\nTop event types / services:")
            for k, v in sorted(event_types.items(), key=lambda x: -x[1])[:6]:
                lines.append(f"  {k}: {v} occurrences")

            # Show 3 sample entries
            lines.append("\nSample log entries:")
            for log in logs[:3]:
                entry = " | ".join(f"{k}: {v}" for k, v in list(log.items())[:6])
                lines.append(f"  {entry}")

        return "\n".join(lines)

    def _logs_to_text(self, logs: list[dict], source_name: str) -> str:
        lines = [f"Log entries from {source_name}:"]
        for log in logs:
            entry = " | ".join(f"{k}: {v}" for k, v in log.items())
            lines.append(f"  [{log.get('timestamp', 'N/A')}] {entry}")
        return "\n".join(lines)

    def get_source_stats(self) -> dict:
        stats = {}
        for chunk in self.chunks:
            stype = chunk.source_type
            if stype not in stats:
                stats[stype] = {"count": 0, "sources": set()}
            stats[stype]["count"] += 1
            stats[stype]["sources"].add(chunk.source_name)
        # Convert sets to counts
        for k in stats:
            stats[k]["unique_sources"] = len(stats[k]["sources"])
            stats[k]["sources"] = list(stats[k]["sources"])
        return stats