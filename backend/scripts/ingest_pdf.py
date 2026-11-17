#!/usr/bin/env python3
"""
OnlineVakeel PDF Ingestion Utility
Ingests Bare Acts, statutory rules, and court judgments from PDF files into the RAG corpus.
Supports both Supabase Cloud (pgvector) and Local In-Memory Fallback Corpus.

Usage:
    python backend/scripts/ingest_pdf.py /path/to/act.pdf --act-name "Information Technology Act, 2000" --act-code "IT_ACT_2000"
"""

import os
import sys
import re
import uuid
import argparse
import logging
from typing import List, Dict, Any, Optional

# Add parent directory to path to import app config and database client
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pypdf import PdfReader
from app.config import settings
from app.database.supabase_client import db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("pdf_ingest")


def extract_text_from_pdf(pdf_path: str) -> str:
    """Reads all pages from a PDF file and returns the combined text."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")
    
    logger.info(f"Reading PDF: {pdf_path}")
    reader = PdfReader(pdf_path)
    logger.info(f"Total pages detected: {len(reader.pages)}")
    
    full_text = []
    for page_idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        full_text.append(f"\n--- PAGE {page_idx + 1} ---\n" + text)
        
    return "\n".join(full_text)


def segment_into_sections(text: str, act_name: str, act_code: str) -> List[Dict[str, Any]]:
    """
    Parses statutory PDF text into structured sections.
    Detects patterns like 'Section 138.', '138. Dishonour of cheque...', etc.
    Falls back to chunking by page or 1000-character blocks if no section headers found.
    """
    sections = []
    
    # Pattern to match Indian statutory sections:
    # e.g., 'Section 66D. Punishment for...' or '66D. Punishment for...'
    section_pattern = re.compile(
        r'(?:Section\s+)?(\d+[A-Z]?)\s*[\.\:\-]\s*([^\n\r]+)([\s\S]*?)(?=(?:(?:Section\s+)?\d+[A-Z]?\s*[\.\:\-])|\Z)',
        re.IGNORECASE
    )
    
    matches = list(section_pattern.finditer(text))
    
    if matches and len(matches) > 1:
        logger.info(f"Detected {len(matches)} statutory sections via regex parsing.")
        for m in matches:
            sec_num = m.group(1).strip()
            sec_title = m.group(2).strip()
            body_text = m.group(3).strip()
            
            # Clean up page markers
            body_text = re.sub(r'--- PAGE \d+ ---', '', body_text).strip()
            if len(body_text) < 20:
                continue
                
            sections.append({
                "act_code": act_code,
                "act_name": act_name,
                "chapter": "General",
                "section_number": sec_num,
                "section_title": sec_title[:120],
                "legal_text": body_text[:2000],
                "plain_summary": f"Statutory provision of Section {sec_num} ({sec_title[:80]}) under {act_name}.",
                "limitation_period": "3 years general statutory limitation under Limitation Act, 1963",
                "penalties": "As prescribed under the statutory schedule",
                "bailable_status": "Bailable / Civil",
                "compoundable_status": "Compoundable"
            })
    else:
        # Fallback: Segment by logical chunks/pages if specific section headers aren't detected
        logger.info("Section headers not distinctly matched. Chunking by document pages...")
        pages = text.split("--- PAGE ")
        for p in pages:
            p_clean = p.strip()
            if not p_clean or len(p_clean) < 50:
                continue
            lines = [l.strip() for l in p_clean.split("\n") if l.strip()]
            header = lines[0] if lines else "General Provision"
            sections.append({
                "act_code": act_code,
                "act_name": act_name,
                "chapter": "Provisions",
                "section_number": f"Doc-{len(sections)+1}",
                "section_title": header[:90],
                "legal_text": p_clean[:2000],
                "plain_summary": f"Excerpts from {act_name}: {header[:120]}.",
                "limitation_period": "As per statutory procedure",
                "penalties": "Civil damages / relief / statutory compliance",
                "bailable_status": "N/A",
                "compoundable_status": "N/A"
            })

    return sections


def generate_ai_summary(sec: Dict[str, Any]) -> Dict[str, Any]:
    """Optionally uses Gemini to create a warm layman summary and extract limitation period."""
    if not settings.GEMINI_API_KEY:
        return sec
        
    try:
        import httpx
        prompt = f"""You are an Indian legal analyst for OnlineVakeel.com.
Summarize the following statutory provision into:
1. Plain Summary (2-3 sentences for a common citizen)
2. Limitation Period (strict deadlines to take action)
3. Penalties / Relief

Act: {sec['act_name']}
Section: {sec['section_number']} - {sec['section_title']}
Text:
{sec['legal_text'][:1200]}

Respond ONLY in JSON format:
{{"plain_summary": "...", "limitation_period": "...", "penalties": "..."}}"""

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={settings.GEMINI_API_KEY}"
        with httpx.Client(timeout=8.0) as client:
            resp = client.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
            if resp.status_code == 200:
                import json
                raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                # extract JSON
                json_match = re.search(r'\{[\s\S]*\}', raw)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    sec["plain_summary"] = parsed.get("plain_summary", sec["plain_summary"])
                    sec["limitation_period"] = parsed.get("limitation_period", sec["limitation_period"])
                    sec["penalties"] = parsed.get("penalties", sec["penalties"])
    except Exception as e:
        logger.warning(f"Could not generate AI summary: {e}")
        
    return sec


def ingest_sections(sections: List[Dict[str, Any]], target: str = "auto") -> None:
    """Ingests processed sections into Supabase or local FALLBACK_LEGAL_CORPUS."""
    if (target in ["auto", "supabase"]) and db.is_connected and db.client:
        logger.info(f"Ingesting {len(sections)} sections into live Supabase Cloud table 'legal_corpus'...")
        records = []
        for s in sections:
            rec = {
                "id": str(uuid.uuid4()),
                "act_code": s["act_code"],
                "act_name": s["act_name"],
                "chapter": s.get("chapter", "General"),
                "section_number": s["section_number"],
                "section_title": s["section_title"],
                "legal_text": s["legal_text"],
                "plain_summary": s["plain_summary"],
                "limitation_period": s["limitation_period"],
                "penalties": s["penalties"],
                "bailable_status": s["bailable_status"],
                "compoundable_status": s["compoundable_status"]
            }
            records.append(rec)
        
        try:
            res = db.client.table("legal_corpus").insert(records).execute()
            logger.info(f"✓ Successfully inserted {len(records)} records into Supabase pgvector corpus!")
            return
        except Exception as e:
            logger.error(f"Failed to insert into Supabase: {e}. Falling back to local display.")
            
    # Local In-Memory Fallback
    logger.info(f"\n✓ Successfully parsed {len(sections)} sections from PDF.")
    logger.info("Generated ready-to-use Python dictionaries for 'FALLBACK_LEGAL_CORPUS':\n")
    import json
    for s in sections[:5]:
        print(json.dumps(s, indent=2))
    if len(sections) > 5:
        print(f"\n... and {len(sections) - 5} more sections.")


def main():
    parser = argparse.ArgumentParser(description="Ingest statutory and case law PDFs into OnlineVakeel RAG")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("--act-name", required=True, help="Full official name of the Act/Document (e.g. 'Information Technology Act, 2000')")
    parser.add_argument("--act-code", required=True, help="Short act code (e.g. 'IT_ACT_2000')")
    parser.add_argument("--target", choices=["auto", "supabase", "local"], default="auto", help="Where to ingest the sections")

    args = parser.parse_args()

    text = extract_text_from_pdf(args.pdf_path)
    sections = segment_into_sections(text, args.act_name, args.act_code)
    
    if not sections:
        logger.error("No sections could be extracted from PDF.")
        sys.exit(1)

    logger.info(f"Processing and summarizing {len(sections)} sections...")
    for idx, sec in enumerate(sections):
        logger.info(f"  [{idx+1}/{len(sections)}] Section {sec['section_number']}: {sec['section_title']}")
        generate_ai_summary(sec)

    ingest_sections(sections, target=args.target)


if __name__ == "__main__":
    main()
