#!/usr/bin/env python3
"""
OnlineVakeel AWS Open Data Court Judgments Connector & Ingestion Utility
Connects to the AWS Open Data Registry for Indian Courts:
- s3://indian-supreme-court-judgments/ (Supreme Court of India, 1950 - 2025)
- s3://indian-high-court-judgments/ (25 Indian High Courts)

Operates 100% free via public S3 endpoints with NO AWS account or credentials needed!
Streams, extracts, and summarizes landmark judicial precedents into the OnlineVakeel RAG corpus.

Usage:
    python backend/scripts/sync_aws_court_data.py --court sci --year 2023 --limit 3
    python backend/scripts/sync_aws_court_data.py --court highcourt --year 2023 --limit 3
    python backend/scripts/sync_aws_court_data.py --search "cheque bounce" --limit 5
"""

import os
import sys
import re
import io
import json
import uuid
import argparse
import logging
import xml.etree.ElementTree as ET
import urllib.request
from typing import List, Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pypdf import PdfReader
from app.config import settings
from app.database.supabase_client import db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("aws_court_rag")

SC_BUCKET_URL = "https://indian-supreme-court-judgments.s3.ap-south-1.amazonaws.com"
HC_BUCKET_URL = "https://indian-high-court-judgments.s3.ap-south-1.amazonaws.com"


def list_s3_public_objects(bucket_url: str, prefix: str, max_keys: int = 10) -> List[str]:
    """Lists object keys from public S3 bucket using XML API (no AWS credentials required)."""
    url = f"{bucket_url}/?list-type=2&prefix={prefix}&max-keys={max_keys}"
    req = urllib.request.Request(url, headers={"User-Agent": "OnlineVakeel/1.0"})
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
            root = ET.fromstring(content)
            keys = []
            for item in root.findall(".//{http://s3.amazonaws.com/doc/2006-03-01/}Contents"):
                key_elem = item.find("{http://s3.amazonaws.com/doc/2006-03-01/}Key")
                if key_elem is not None and key_elem.text.endswith(".pdf"):
                    keys.append(key_elem.text)
            return keys
    except Exception as e:
        logger.error(f"Failed to list S3 objects from {bucket_url}: {e}")
        return []


def stream_and_parse_judgment_pdf(bucket_url: str, s3_key: str) -> Optional[Dict[str, Any]]:
    """Streams a judgment PDF from S3 into memory and parses case title, bench, and legal text."""
    url = f"{bucket_url}/{s3_key}"
    logger.info(f"Streaming judgment: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "OnlineVakeel/1.0"})
    
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            pdf_bytes = io.BytesIO(resp.read())
            reader = PdfReader(pdf_bytes)
            num_pages = len(reader.pages)
            
            # Extract first 4 pages for case header, facts, and legal ratio
            pages_text = []
            for i in range(min(num_pages, 4)):
                text = reader.pages[i].extract_text() or ""
                pages_text.append(text)
            combined_text = "\n".join(pages_text)

            # Heuristics for Title, Citation, Coram
            lines = [l.strip() for l in combined_text.split("\n") if l.strip()]
            case_title = "Landmark Judgment"
            for idx, line in enumerate(lines[:30]):
                if any(vs in line.lower() for vs in [" v. ", " vs. ", " versus "]):
                    prev = lines[idx-1] if idx > 0 else ""
                    nxt = lines[idx+1] if idx < len(lines)-1 else ""
                    case_title = f"{prev} {line} {nxt}".strip()
                    break

            # Citation detection
            citation_match = re.search(r'\((?:Civil|Criminal|Special Leave|Writ)\s+Appeal[^\)]+\)', combined_text, re.IGNORECASE)
            citation = citation_match.group(0) if citation_match else f"Appeal Reference ({os.path.basename(s3_key).replace('.pdf', '')})"

            return {
                "source_bucket": bucket_url,
                "s3_key": s3_key,
                "case_title": case_title[:150],
                "citation": citation,
                "pages": num_pages,
                "text_excerpt": combined_text[:2500]
            }
    except Exception as e:
        logger.warning(f"Error streaming PDF {s3_key}: {e}")
        return None


def generate_judgment_summary(data: Dict[str, Any], court_type: str) -> Dict[str, Any]:
    """Generates judicial summary, legal principles, and relief using Gemini or heuristics."""
    court_name = "Supreme Court of India" if court_type == "sci" else "High Court of Judicature"
    
    sec = {
        "act_code": "SC_PRECEDENT" if court_type == "sci" else "HC_PRECEDENT",
        "act_name": f"{court_name} (AWS Open Data)",
        "chapter": "Judicial Precedents & Binding Case Law",
        "section_number": data["citation"],
        "section_title": data["case_title"],
        "legal_text": data["text_excerpt"],
        "plain_summary": f"Binding precedent of the {court_name} in {data['case_title']} establishing key principles of law and judicial procedure.",
        "limitation_period": "Subject to appellate / review limitation periods",
        "penalties": "Binding judicial ratio under Article 141/227 of Constitution",
        "bailable_status": f"{court_name} Precedent",
        "compoundable_status": "Binding Precedent"
    }

    if not settings.GEMINI_API_KEY:
        return sec

    try:
        import httpx
        prompt = f"""You are a legal research assistant for OnlineVakeel.
Summarize the following Indian Court Judgment excerpt into:
1. Plain Summary (2-3 sentences explaining the key legal holding/ratio for everyday citizens)
2. Practical Legal Impact (how this judgment helps citizens or advocates in court)
3. Key Statutory Acts cited

Court: {court_name}
Case: {data['case_title']} ({data['citation']})
Excerpt:
{data['text_excerpt'][:1500]}

Respond ONLY in JSON format:
{{"plain_summary": "...", "practical_impact": "...", "acts_cited": "..."}}"""

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={settings.GEMINI_API_KEY}"
        with httpx.Client(timeout=8.0) as client:
            resp = client.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
            if resp.status_code == 200:
                raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                m = re.search(r'\{[\s\S]*\}', raw)
                if m:
                    parsed = json.loads(m.group(0))
                    sec["plain_summary"] = parsed.get("plain_summary", sec["plain_summary"])
                    sec["penalties"] = parsed.get("practical_impact", sec["penalties"])
    except Exception as e:
        logger.warning(f"Could not generate AI summary for judgment: {e}")

    return sec


def ingest_judgment(record: Dict[str, Any]) -> None:
    """Ingests judicial precedent into Supabase legal_corpus or displays for fallback."""
    if db.is_connected and db.client:
        try:
            db_record = {
                "id": str(uuid.uuid4()),
                "act_code": record["act_code"],
                "act_name": record["act_name"],
                "chapter": record["chapter"],
                "section_number": record["section_number"],
                "section_title": record["section_title"],
                "legal_text": record["legal_text"],
                "plain_summary": record["plain_summary"],
                "limitation_period": record["limitation_period"],
                "penalties": record["penalties"],
                "bailable_status": record["bailable_status"],
                "compoundable_status": record["compoundable_status"]
            }
            db.client.table("legal_corpus").insert(db_record).execute()
            logger.info(f"✓ Ingested judgment into Supabase pgvector: {record['section_title'][:60]}")
            return
        except Exception as e:
            logger.warning(f"Supabase insertion failed: {e}")

    logger.info(f"✓ Parsed Precedent: {record['section_title']}")
    logger.info(f"  Summary: {record['plain_summary']}\n")


def main():
    parser = argparse.ArgumentParser(description="Sync Indian Supreme Court & High Court Judgments from AWS Open Data")
    parser.add_argument("--court", choices=["sci", "highcourt"], default="sci", help="Court bucket to query: sci (Supreme Court) or highcourt (High Courts)")
    parser.add_argument("--year", default="2023", help="Year partition (e.g. 2023, 2022, 2021)")
    parser.add_argument("--limit", type=int, default=3, help="Number of judgments to stream and ingest")
    parser.add_argument("--prefix", default="", help="Custom S3 prefix")

    args = parser.parse_args()

    bucket_url = SC_BUCKET_URL if args.court == "sci" else HC_BUCKET_URL
    if not args.prefix:
        if args.court == "sci":
            prefix = f"data/pdf/year={args.year}/english/"
        else:
            prefix = f"data/pdf/year={args.year}/"
    else:
        prefix = args.prefix

    logger.info(f"Querying AWS Open Data S3 ({args.court.upper()}) at: {prefix}")
    keys = list_s3_public_objects(bucket_url, prefix, max_keys=args.limit)

    if not keys:
        logger.warning(f"No judgment objects found under {prefix}")
        sys.exit(0)

    logger.info(f"Found {len(keys)} judgments. Beginning streaming & RAG ingestion...")
    for idx, key in enumerate(keys):
        logger.info(f"\n--- [{idx+1}/{len(keys)}] Processing: {key} ---")
        parsed = stream_and_parse_judgment_pdf(bucket_url, key)
        if parsed:
            record = generate_judgment_summary(parsed, args.court)
            ingest_judgment(record)

    logger.info(f"\n✓ Completed sync from AWS Open Data ({args.court.upper()}).")


if __name__ == "__main__":
    main()
