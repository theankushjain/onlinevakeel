#!/usr/bin/env python3
"""
Generate an executive, publication-grade, beautifully designed 4-page PDF
explaining the functioning of all 8 agents in OnlineVakeel with end-to-end examples.
"""
import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        width, height = self._pagesize
        margin = 36  # 0.5 inch

        # Running Header on all pages
        self.drawString(margin, height - 26, "OnlineVakeel.com — Multi-Agent AI Legal Aid Architecture")
        self.drawRightString(width - margin, height - 26, "8-Agent Deep Dive & Real-World Case Study")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.75)
        self.line(margin, height - 30, width - margin, height - 30)

        # Running Footer on all pages
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.75)
        self.line(margin, 32, width - margin, 32)

        self.drawString(margin, 20, "Confidential & Proprietary • OnlineVakeel Legal Platform • DPDP Act 2023 Compliant")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(width - margin, 20, page_str)
        self.restoreState()


def build_pdf(filename="OnlineVakeel_8_Agents_Architecture.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=38,
        bottomMargin=38
    )

    styles = getSampleStyleSheet()

    # Brand Colors
    c_primary = colors.HexColor("#0f172a")     # Deep Navy
    c_accent = colors.HexColor("#1e40af")      # Royal Blue
    c_gold = colors.HexColor("#b45309")        # Deep Amber
    c_text = colors.HexColor("#1e293b")        # Slate Text
    c_subtext = colors.HexColor("#475569")     # Slate Muted
    c_border = colors.HexColor("#cbd5e1")      # Slate Border
    c_green = colors.HexColor("#065f46")

    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=c_primary,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=c_accent,
        spaceAfter=8
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=c_primary,
        spaceBefore=8,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=c_text,
        spaceAfter=3
    )

    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#334155")
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=c_text
    )

    def make_agent_card(ag):
        box_data = [
            [
                Paragraph(f"<b>AGENT {ag['num']}: {ag['name'].upper()}</b>", ParagraphStyle('A_H', fontName='Helvetica-Bold', fontSize=8.5, textColor=c_primary)),
                Paragraph(ag['role'], ParagraphStyle('A_R', fontName='Helvetica-Bold', fontSize=7.5, textColor=c_accent, alignment=2))
            ],
            [
                Paragraph(f"<b>Source Code:</b> <code>{ag['code']}</code>", ParagraphStyle('A_F', fontName='Helvetica', fontSize=7, textColor=c_subtext)),
                Paragraph("", body_style)
            ],
            [
                Paragraph(f"<b>How it Operates:</b> {ag['how']}", body_style),
                Paragraph("", body_style)
            ],
            [
                Paragraph(f"<b>Example Input:</b> {ag['input_ex']}", ParagraphStyle('A_In', fontName='Helvetica-Oblique', fontSize=7.5, textColor=c_subtext)),
                Paragraph("", body_style)
            ],
            [
                Paragraph(f"<b>Deterministic Output:</b> <b>{ag['output_ex']}</b>", ParagraphStyle('A_Out', fontName='Helvetica', fontSize=7.5, textColor=c_green)),
                Paragraph("", body_style)
            ]
        ]
        t = Table(box_data, colWidths=[370, 150])
        t.setStyle(TableStyle([
            ('SPAN', (0, 1), (1, 1)),
            ('SPAN', (0, 2), (1, 2)),
            ('SPAN', (0, 3), (1, 3)),
            ('SPAN', (0, 4), (1, 4)),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#ffffff")),
            ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor("#e2e8f0")),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 4),
            ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor("#f0fdf4")),
        ]))
        return t

    story = []

    # =========================================================================
    # PAGE 1: Executive Overview, Architecture Pipeline & Case Study
    # =========================================================================
    banner_content = [
        [
            Paragraph("<b>ONLINEVAKEEL.COM</b> • ARCHITECTURAL SPECIFICATION & SYSTEM DESIGN", ParagraphStyle('B1', fontName='Helvetica-Bold', fontSize=7.5, textColor=c_gold)),
        ],
        [
            Paragraph("The 8 Autonomous Legal AI Agents: Complete Operational Breakdown", title_style),
        ],
        [
            Paragraph("A complete technical guide explaining how OnlineVakeel solves the critical failure modes of generic LLMs in Indian law through deterministic statutory retrieval, DPDP Act 2023 compliance, anti-hallucination verification, automated notice drafting, and exact court proximity matching.", subtitle_style),
        ]
    ]
    banner_table = Table(banner_content, colWidths=[520])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("1. Executive Summary: Why Generic LLMs Fail in Indian Law", h1_style))
    summary_text = (
        "Standard LLMs (ChatGPT, raw Gemini, Claude) predict tokens statistically based on global datasets. In Indian jurisprudence, "
        "this causes catastrophic failure: <b>hallucinating repealed criminal statutes</b> (quoting IPC 420 or CrPC 156(3) instead of "
        "the modern Bharatiya Nyaya Sanhita 2023), <b>fabricating non-existent judgments</b>, <b>leaking confidential citizen PII</b> "
        "(Aadhaar, PAN, bank accounts) to cloud servers in violation of the Digital Personal Data Protection Act (DPDP Act 2023), and "
        "<b>ignoring territorial court jurisdiction</b>. OnlineVakeel solves this through a sequential 8-agent deterministic pipeline."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("2. Multi-Agent Pipeline Flow", h1_style))
    pipe_data = [
        [
            Paragraph("<b>1. PII Redactor</b><br/>DPDP Act Masking", table_cell_style),
            Paragraph("<b>➔ 2. Triage Agent</b><br/>Emergency / NALSA 15100", table_cell_style),
            Paragraph("<b>➔ 3. Intake Agent</b><br/>Facts, Claims & City", table_cell_style),
            Paragraph("<b>➔ 4. Research RAG</b><br/>Bare Acts & Precedents", table_cell_style),
        ],
        [
            Paragraph("<b>➔ 5. Verifier Agent</b><br/>Zero-Hallucination Seal", table_cell_style),
            Paragraph("<b>➔ 6. Conversational</b><br/>Empathetic Layman Advice", table_cell_style),
            Paragraph("<b>➔ 7. Drafting Agent</b><br/>15-Day Notice & PDF", table_cell_style),
            Paragraph("<b>➔ 8. Handoff Matcher</b><br/>Local Advocate Booking", table_cell_style),
        ]
    ]
    t_pipe = Table(pipe_data, colWidths=[130, 130, 130, 130])
    t_pipe.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 5),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(t_pipe)
    story.append(Spacer(1, 8))

    story.append(Paragraph("3. The Running Real-World Case Study", h1_style))
    case_intro = (
        "Throughout this document, the following authentic citizen grievance is traced step-by-step through all 8 agents:"
    )
    story.append(Paragraph(case_intro, body_style))

    case_box = [
        [
            Paragraph("<b>CITIZEN'S RAW GRIEVANCE (INPUT MESSAGE)</b>", ParagraphStyle('C1', fontName='Helvetica-Bold', fontSize=7.5, textColor=c_accent)),
        ],
        [
            Paragraph(
                "<i>\"Hi, my builder in Saket South Delhi gave me a cheque of Rs 5,00,000 on 10th October which bounced with memo "
                "'funds insufficient'. My phone number is 9876543210 and Aadhaar is 5489 1234 5678. I am very stressed, please help me recover my money.\"</i>",
                callout_style
            )
        ]
    ]
    t_case = Table(case_box, colWidths=[520])
    t_case.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#eff6ff")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#bfdbfe")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_case)

    # Force Page Break -> Page 2
    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: Agents 1 to 4 (Data Safety, Emergency Triage, Intake, Statutory RAG)
    # =========================================================================
    story.append(Paragraph("4. Specialized Agents Deep Dive: Phase I — Intake & Grounding", h1_style))

    agents_page2 = [
        {
            "num": "1",
            "name": "PII Redaction Engine",
            "code": "PIIRedactor (backend/app/safety/pii_redactor.py)",
            "role": "DPDP Act 2023 Compliance & Privacy Perimeter",
            "how": (
                "Operates before any text is transmitted to an LLM or database. Uses high-speed regex and Verhoeff checksums "
                "to detect and mask Indian mobile numbers (+91, 10-digit formats), 12-digit Aadhaar cards, 10-character PAN cards, "
                "and bank account numbers into safe pseudonymous tokens."
            ),
            "input_ex": "Cheque of Rs 5,00,000... phone: 9876543210, Aadhaar: 5489 1234 5678",
            "output_ex": "Cheque of Rs 5,00,000... phone: [PHONE_MASKED], Aadhaar: [AADHAAR_MASKED]"
        },
        {
            "num": "2",
            "name": "Urgency Triage & Emergency Escalation",
            "code": "UrgencyTriage (backend/app/safety/urgency_triage.py)",
            "role": "Instant Safety Screening & Legal Crisis Dispatch",
            "how": (
                "Screens queries in microseconds for physical threat, domestic violence, imminent arrest, or self-harm. Categorizes "
                "cases into Emergency, Urgent, or Routine. If an emergency is flagged, it preempts chat to display priority statutory helplines: "
                "NALSA 24/7 Free Legal Aid (15100), Police/Emergency (112), Cyber Crime (1930), and Women Helpline (1091)."
            ),
            "input_ex": "Mentions high emotional stress over bounced cheque with no physical violence or custodial detention.",
            "output_ex": "urgency_level: 'routine_financial' | is_emergency: false | helplines_triggered: None"
        },
        {
            "num": "3",
            "name": "Legal Case Intake & Entity Extraction",
            "code": "IntakeAgent (backend/app/agents/intake_agent.py)",
            "role": "Converting Natural Grievance into Structured Legal Parameters",
            "how": (
                "Applies domain classification (Cheque Bounce NI 138, RERA Builder Delays, Consumer CPA 35, Cyber Cheating BNS 318, Bail). "
                "Extracts normalized financial sums, incident dates, and resolves territorial court jurisdiction across 60+ Indian cities and "
                "court complexes using bi-directional inference (e.g., 'Saket South Delhi' -> Saket District Court, South Delhi, Delhi)."
            ),
            "input_ex": "Raw text mentioning 'Saket South Delhi', 'Rs 5,00,000', '10th October', 'cheque bounced'",
            "output_ex": "domain: 'cheque_bounce' | claim: ₹5,00,000 | court: 'Saket District Court' | city: 'Delhi' | notice_window: '30-Day Active'"
        },
        {
            "num": "4",
            "name": "Grounded Statutory RAG",
            "code": "ResearchAgent (backend/app/agents/research_agent.py)",
            "role": "Retrieving Verified Indian Bare Acts & Supreme Court Precedents",
            "how": (
                "Queries an internal canonical knowledge graph containing active Indian Bare Acts and Supreme Court ratios. "
                "Retrieves exact sections: Sec 138 NI Act (dishonour of cheque for insufficiency of funds), Sec 142(2) NI Act (territorial "
                "jurisdiction of the payee bank branch), Sec 63 Bharatiya Sakshya Adhiniyam 2023 (electronic evidence certificate), "
                "and landmark precedent: Dalmia Cement v. Galaxy Traders (2001 SC)."
            ),
            "input_ex": "Query vector: {domain: 'cheque_bounce', dispute_type: 'funds_insufficient'}",
            "output_ex": "Retrieved: NI Act Sec 138, Sec 142(2); BSA 2023 Sec 63; Dalmia Cement v. Galaxy Traders (2001) 1 SCC 631"
        }
    ]

    for ag in agents_page2:
        story.append(make_agent_card(ag))
        story.append(Spacer(1, 5))

    # Force Page Break -> Page 3
    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: Agents 5 to 8 (Verification, Guidance, Notice Drafting, Advocate Handoff)
    # =========================================================================
    story.append(Paragraph("4. Specialized Agents Deep Dive: Phase II — Verification & Delivery", h1_style))

    agents_page3 = [
        {
            "num": "5",
            "name": "Anti-Hallucination Gatekeeper",
            "code": "VerifierAgent (backend/app/agents/verifier_agent.py)",
            "role": "Zero-Tolerance Statutory Integrity & Cryptographic Seal",
            "how": (
                "Cross-checks every extracted citation against the official India Code database. Strictly rejects obsolete laws (IPC 420, "
                "CrPC 156(3), Evidence Act 65B). Upon confirming validity, attaches a cryptographic trust seal: "
                "'100% Verified Statutory Citation (India Code & Supreme Court Repository)'."
            ),
            "input_ex": "Draft citations: [Sec 138 NI Act, Sec 142(2) NI Act, Sec 63 BSA 2023]",
            "output_ex": "Status: PASSED | Hallucination: 0% | Badge: '100% Verified Statutory Citation'"
        },
        {
            "num": "6",
            "name": "Conversational Counsel Agent",
            "code": "ConversationalAgent (backend/app/agents/conversational_agent.py)",
            "role": "Dual-Engine Empathetic Guidance & In-Chat Location Trigger",
            "how": (
                "Dual-Engine Design: Calls Google Gemini Flash bound to verified statutory context. If the API is throttled or offline, "
                "fails over seamlessly to a deterministic legal explanation engine. Translates statutory legal jargon into empathetic, "
                "step-by-step guidance over tea. If location is missing, renders 1-click interactive city chips."
            ),
            "input_ex": "Verified legal citations + citizen's ₹5,00,000 claim facts + Saket jurisdiction",
            "output_ex": "Detailed counsel explaining 15-day statutory demand notice, Saket Magistrate jurisdiction, and criminal penal liability."
        },
        {
            "num": "7",
            "name": "Synchronized Legal Notice Drafter",
            "code": "DraftingAgent (backend/app/agents/drafting_agent.py)",
            "role": "Automated 15-Day Statutory Legal Demand Notice Generator",
            "how": (
                "As the consultation proceeds, dynamically populates a court-ready 15-day pre-litigation legal demand notice on advocate letterhead. "
                "Incorporates complainant and defaulter details, cheque number, return memo date, 18% statutory interest, notice cost (₹5,500), "
                "Sec 63 BSA electronic evidence clause, and provides 1-click vector PDF download and printing."
            ),
            "input_ex": "Client: Anonymous | Defaulter: Builder | Amount: ₹5,00,000 | Date: 10/10/2026 | Court: Saket",
            "output_ex": "Complete formal legal notice ready for Speed Post / Registered Post AD with 15-day cure deadline."
        },
        {
            "num": "8",
            "name": "Advocate Handoff & Proximity Matcher",
            "code": "HandoffAgent + DatabaseClient (backend/app/database/supabase_client.py)",
            "role": "Territorial Court Proximity Ranking & Booking Dispatch",
            "how": (
                "Calculates a multi-factor proximity score: Score = S_court (+50) + S_chamber (+40) + S_city (+25) + S_domain (+15) + R_bar (1-5). "
                "Matches advocates specifically practicing at Saket District Court with chambers in South Delhi, surfaces verified Bar Council "
                "credentials, and enables 1-click booking (Phone, Video, or Chamber visit) with privacy-protected brief sharing."
            ),
            "input_ex": "Client City: 'Delhi' | Court: 'Saket District Court' | Domain: 'cheque_bounce'",
            "output_ex": "Top Match: Advocate A (Saket District Court, Score: 134 pts) | Renders booking modal & unlocks advocate dossier."
        }
    ]

    for ag in agents_page3:
        story.append(make_agent_card(ag))
        story.append(Spacer(1, 5))

    # Force Page Break -> Page 4
    story.append(PageBreak())

    # =========================================================================
    # PAGE 4: Comparison Benchmark, Mathematical Formula & Architecture Summary
    # =========================================================================
    story.append(Paragraph("5. Benchmark: OnlineVakeel vs. Generic LLMs (ChatGPT / Claude)", h1_style))
    matrix_data = [
        [
            Paragraph("Evaluation Dimension", table_header_style),
            Paragraph("Generic LLMs (ChatGPT / Claude / Raw Gemini)", table_header_style),
            Paragraph("OnlineVakeel Multi-Agent Engine", table_header_style)
        ],
        [
            Paragraph("<b>Criminal Law Framework</b>", table_cell_style),
            Paragraph("Repeatedly hallucinates repealed <b>IPC 1860, CrPC 1973</b>, and <b>Evidence Act 1872</b>.", table_cell_style),
            Paragraph("Strictly applies <b>BNS 2023, BNSS 2023</b>, and <b>BSA 2023</b> statutory codes.", table_cell_style)
        ],
        [
            Paragraph("<b>Data Privacy & DPDP Compliance</b>", table_cell_style),
            Paragraph("Transmits citizen's unmasked Aadhaar, PAN, phone to external cloud training logs.", table_cell_style),
            Paragraph("Deterministic <b>PIIRedactor</b> strips all sensitive identifiers before inference.", table_cell_style)
        ],
        [
            Paragraph("<b>Citation Verifiability</b>", table_cell_style),
            Paragraph("Frequent hallucinations of non-existent sections, limitation rules, and rulings.", table_cell_style),
            Paragraph("<b>VerifierAgent</b> validates citations against canonical India Code database.", table_cell_style)
        ],
        [
            Paragraph("<b>Territorial Court Jurisdiction</b>", table_cell_style),
            Paragraph("Completely oblivious to Indian territorial jurisdiction and court complexes.", table_cell_style),
            Paragraph("Bi-directional mapping across <b>60+ Indian cities and specific District Courts</b>.", table_cell_style)
        ],
        [
            Paragraph("<b>Actionable Pre-Litigation Output</b>", table_cell_style),
            Paragraph("Outputs unstructured conversational essays; no formal legal instruments.", table_cell_style),
            Paragraph("Auto-generates <b>15-Day Statutory Demand Notice</b> on letterhead with PDF export.", table_cell_style)
        ],
        [
            Paragraph("<b>Legal Practitioner Connection</b>", table_cell_style),
            Paragraph("No connection; leaves citizens stranded with theoretical text.", table_cell_style),
            Paragraph("Direct proximity matching to verified Bar Council advocates at their local court.", table_cell_style)
        ],
        [
            Paragraph("<b>Service Uptime & Reliability</b>", table_cell_style),
            Paragraph("Single point of failure when LLM API rate limits, fails, or crashes.", table_cell_style),
            Paragraph("<b>Dual-Engine Architecture</b>: Seamless fallback to deterministic human legal rules.", table_cell_style)
        ]
    ]
    t_matrix = Table(matrix_data, colWidths=[120, 195, 205])
    t_matrix.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('PADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    story.append(t_matrix)
    story.append(Spacer(1, 8))

    story.append(Paragraph("6. Territorial Proximity Matching Mathematical Formula", h1_style))
    story.append(Paragraph(
        "Advocate recommendations are calculated deterministically by <code>HandoffAgent</code> and <code>DatabaseClient</code> "
        "using the following multi-factor scoring formula:",
        body_style
    ))

    formula_data = [
        [Paragraph("Match Layer", table_header_style), Paragraph("Points Weight", table_header_style), Paragraph("Jurisdiction & Practical Rationale", table_header_style)],
        [Paragraph("<b>Exact District Court Match</b>", table_cell_style), Paragraph("<b>+50 pts</b>", table_cell_style), Paragraph("Advocate's primary designated court matches the client's court complex (e.g. Saket District Court).", table_cell_style)],
        [Paragraph("<b>Chamber Locality Proximity</b>", table_cell_style), Paragraph("<b>+40 pts</b>", table_cell_style), Paragraph("Advocate's chamber or office address is located in the client's sub-district / neighbourhood.", table_cell_style)],
        [Paragraph("<b>City Territorial Jurisdiction</b>", table_cell_style), Paragraph("<b>+25 pts</b>", table_cell_style), Paragraph("Enrolled practice city matches the client's city (e.g. Delhi NCR).", table_cell_style)],
        [Paragraph("<b>Practice Area Specialization</b>", table_cell_style), Paragraph("<b>+15 pts</b>", table_cell_style), Paragraph("Advocate has proven track record in the specific case category (e.g. Cheque Dishonour NI 138).", table_cell_style)],
        [Paragraph("<b>Bar Council Verified Rating</b>", table_cell_style), Paragraph("<b>+1 to +5 pts</b>", table_cell_style), Paragraph("Peer review, Bar standing, and verified client consultation feedback score.", table_cell_style)],
    ]
    t_formula = Table(formula_data, colWidths=[150, 85, 285])
    t_formula.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_accent),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('PADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    story.append(t_formula)
    story.append(Spacer(1, 8))

    story.append(Paragraph("7. Architectural Conclusion", h1_style))
    conclusion_text = (
        "By enforcing strict separation of concerns across 8 autonomous agents, OnlineVakeel achieves what single-prompt LLM wrappers cannot: "
        "<b>statutory precision, Zero-Hallucination guarantees, DPDP Act privacy compliance, automated pre-litigation documentation, and localized judicial proximity</b>. "
        "The system transforms a complex, adversarial legal system into accessible, reliable justice for millions of Indian citizens."
    )
    story.append(Paragraph(conclusion_text, body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] PDF built cleanly: {filename}")

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "OnlineVakeel_8_Agents_Architecture.pdf"
    build_pdf(out_file)
