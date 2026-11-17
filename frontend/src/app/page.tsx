"use client";

import React, { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Scale, ArrowRight, ShieldCheck, Lock, BookOpen, Send } from "lucide-react";

const QUICK_PROMPTS = [
  { emoji: "💳", label: "Cheque bounce sec 138",  query: "My cheque of ₹2,50,000 bounced in Delhi. What notice do I send and what are my rights?" },
  { emoji: "🏢", label: "Builder delay (RERA)",   query: "My builder delayed flat handover in Bengaluru by 2 years after I paid ₹75 lakhs. Can I claim RERA delay interest?" },
  { emoji: "🛒", label: "Consumer complaint",     query: "An e-commerce site delivered a damaged laptop worth ₹65,000 and refused refund. What can I do?" },
  { emoji: "📄", label: "File an RTI",            query: "How do I file an RTI application against a government department? What sections apply?" },
  { emoji: "💼", label: "Wrongful termination",   query: "My employer terminated me without notice or dues. What are my legal rights under labour law?" },
  { emoji: "💻", label: "Cyber fraud",            query: "I was defrauded of ₹40,000 through an online scam. What FIR sections apply and how do I recover?" },
];

export default function LandingPage() {
  const router   = useRouter();
  const [input,  setInput]  = useState("");
  const textRef  = useRef<HTMLTextAreaElement>(null);

  /* Auto-resize textarea */
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 140)}px`;
  };

  const submit = (text?: string) => {
    const q = (text || input).trim();
    if (!q) return;
    router.push(`/consult?q=${encodeURIComponent(q)}`);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="land-root">

      {/* ── NAV ── */}
      <nav className="land-nav">
        <div className="land-nav-brand">
          <div className="land-nav-seal"><Scale size={16} /></div>
          <span className="land-nav-name">OnlineVakeel<span className="land-nav-dot">.com</span></span>
        </div>
        <div className="land-nav-links">
          <Link href="/consult?tab=advocate" className="land-nav-link">Advocate portal</Link>
          <Link href="/consult?tab=corpus"   className="land-nav-link">Bare Acts library</Link>
        </div>
      </nav>

      {/* ── HERO ── */}
      <main className="land-main">

        {/* Badge */}
        <div className="land-badge">
          <ShieldCheck size={12} />
          <span>Free · DPDP 2023 Compliant · Bar Council Verified Advocates</span>
        </div>

        {/* Headline */}
        <h1 className="land-h1">
          Your legal question,<br />
          <span className="land-h1-em">answered by Indian law.</span>
        </h1>

        <p className="land-sub">
          Describe your situation in plain language. The AI counsel will cite the exact Bare Act, explain your rights, and draft a formal legal notice — instantly.
        </p>

        {/* Chat input box */}
        <div className="land-input-card">
          <textarea
            ref={textRef}
            className="land-textarea"
            placeholder="Describe your legal situation… e.g. my cheque bounced, my builder delayed possession, I was cheated online…"
            value={input}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            rows={3}
            autoFocus
          />
          <div className="land-input-footer">
            <span className="land-input-hint">
              <Lock size={11} />
              Aadhaar, PAN &amp; phone auto-masked before AI processing
            </span>
            <button
              className="land-send-btn"
              onClick={() => submit()}
              disabled={!input.trim()}
            >
              Get legal guidance
              <ArrowRight size={15} />
            </button>
          </div>
        </div>

        {/* Quick prompts */}
        <div className="land-chips-label">Try a common situation:</div>
        <div className="land-chips">
          {QUICK_PROMPTS.map((p) => (
            <button key={p.label} className="land-chip" onClick={() => submit(p.query)}>
              <span>{p.emoji}</span>
              {p.label}
            </button>
          ))}
        </div>

        {/* Trust row */}
        <div className="land-trust-row">
          <div className="land-trust-item">
            <ShieldCheck size={13} style={{ color: "var(--emerald)" }} />
            <span>40+ Indian Bare Acts</span>
          </div>
          <div className="land-trust-dot" />
          <div className="land-trust-item">
            <Lock size={13} style={{ color: "var(--brand)" }} />
            <span>DPDP Act, 2023</span>
          </div>
          <div className="land-trust-dot" />
          <div className="land-trust-item">
            <BookOpen size={13} style={{ color: "var(--amber)" }} />
            <span>BNS · NI Act · RERA · CPA</span>
          </div>
          <div className="land-trust-dot" />
          <div className="land-trust-item">
            <Scale size={13} style={{ color: "var(--ink-muted)" }} />
            <span>BCI verified advocates</span>
          </div>
        </div>
      </main>

      {/* ── FOOTER ── */}
      <footer className="land-footer">
        <span>© 2024 OnlineVakeel.com</span>
        <span className="land-footer-sep">·</span>
        <span>Disclaimer: Informational guidance only. Not a substitute for enrolled advocate advice.</span>
        <span className="land-footer-sep">·</span>
        <a href="tel:15100" className="land-footer-link">NALSA: 15100</a>
        <span className="land-footer-sep">·</span>
        <a href="tel:1930"  className="land-footer-link">Cyber: 1930</a>
      </footer>
    </div>
  );
}
