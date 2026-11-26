"use client";

import "./landing.css";
import React, { useState, useRef, useEffect, useMemo, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Scale, ArrowRight, ShieldCheck, Lock, BookOpen, Mic, MicOff, Languages,
  PhoneCall, X, Loader2, ChevronDown, Menu, MessageSquare, FileText, UserCheck,
  CalendarCheck, BadgeCheck, EyeOff, Landmark, Sparkles,
} from "lucide-react";
import AdvocateAvatar from "./AdvocateAvatar";
import { serif, body, serifHi } from "./fonts";

/* ───────────────────────── Content ───────────────────────── */

type Lang = "en" | "hi";

const COPY: Record<Lang, {
  eyebrow: string; h1: string; sub: string; hello: string; cta: string; going: string;
  suggest: string; examples: string[]; detected: string; voiceUnsupported: string; fillHint: string; speech: string; speechFound: string;
}> = {
  en: {
    eyebrow: "Indian Bare Acts · Supreme Court & High Court Precedents",
    h1: "Your legal question, answered with the law cited",
    sub: "Cheque bounce? Builder delay? Online fraud? Describe it in plain Hindi or English and get the exact Bare Act sections, your options, and a draft legal notice. Free.",
    hello: "Hello, how can I help you today?",
    cta: "Ask now",
    going: "Opening…",
    suggest: "Try one of these:",
    examples: [
      "My cheque bounced and the drawer is not paying…",
      "My builder delayed possession of my flat by 2 years…",
      "I was cheated of ₹40,000 in an online scam…",
      "My employer fired me without paying my dues…",
    ],
    detected: "Looks like",
    voiceUnsupported: "Voice input isn't supported in this browser. Try Chrome or Edge.",
    fillHint: "Edit if you like, then press Enter.",
    speech: "Tell me what happened. I will find the law that applies.",
    speechFound: "That sounds like {label}. I will look at {law}.",
  },
  hi: {
    eyebrow: "भारतीय बेयर एक्ट्स · सुप्रीम कोर्ट और हाई कोर्ट के फैसले",
    h1: "आपका कानूनी सवाल, धाराओं के हवाले के साथ जवाब",
    sub: "चेक बाउंस? बिल्डर की देरी? ऑनलाइन ठगी? सरल हिन्दी या अंग्रेज़ी में बताइए और पाइए सही धाराएं, आपके विकल्प और कानूनी नोटिस का ड्राफ्ट। मुफ़्त।",
    hello: "नमस्ते, मैं आपकी कैसे मदद कर सकता हूँ?",
    cta: "पूछें",
    going: "खुल रहा है…",
    suggest: "इनमें से कोई आज़माएं:",
    examples: [
      "मेरा चेक बाउंस हो गया है और भुगतान नहीं हो रहा…",
      "बिल्डर ने फ्लैट का कब्ज़ा देने में 2 साल की देरी की…",
      "ऑनलाइन ठगी में मेरे ₹40,000 चले गए…",
      "मालिक ने बकाया दिए बिना नौकरी से निकाल दिया…",
    ],
    detected: "यह मामला लगता है",
    voiceUnsupported: "इस ब्राउज़र में वॉइस इनपुट उपलब्ध नहीं है। Chrome या Edge आज़माएं।",
    fillHint: "चाहें तो बदलें, फिर Enter दबाएं।",
    speech: "बताइए क्या हुआ। मैं लागू कानून ढूँढूँगा।",
    speechFound: "यह {label} जैसा लगता है। मैं {law} देखूँगा।",
  },
};

const QUICK_PROMPTS = [
  { label: "Cheque bounce, sec 138", query: "My cheque of ₹2,50,000 bounced in Delhi. What notice do I send and what are my rights?" },
  { label: "Builder delay (RERA)",   query: "My builder delayed flat handover in Bengaluru by 2 years after I paid ₹75 lakhs. Can I claim RERA delay interest?" },
  { label: "Consumer complaint",     query: "An e-commerce site delivered a damaged laptop worth ₹65,000 and refused refund. What can I do?" },
  { label: "File an RTI",            query: "How do I file an RTI application against a government department? What sections apply?" },
  { label: "Wrongful termination",   query: "My employer terminated me without notice or dues. What are my legal rights under labour law?" },
  { label: "Cyber fraud",            query: "I was defrauded of ₹40,000 through an online scam. What FIR sections apply and how do I recover?" },
];

/* UI hint only: the backend Intake agent does the real classification. */
const CATEGORIES = [
  { key: "cheque",   label: "Cheque bounce",       law: "NI Act §138",       re: /cheque|check bounce|dishonou?r|चेक/i },
  { key: "rera",     label: "Property / RERA",     law: "RERA Act §18",      re: /builder|possession|handover|rera|flat|बिल्डर|फ्लैट|कब्ज़ा/i },
  { key: "consumer", label: "Consumer dispute",    law: "Consumer Act §35",  re: /refund|defective|damaged|warranty|e-?commerce|consumer|रिफंड/i },
  { key: "cyber",    label: "Cyber fraud",         law: "BNS §318",          re: /scam|fraud|upi|phishing|cheated|defrauded|ठगी|धोखा/i },
  { key: "labour",   label: "Employment / labour", law: "Labour Codes",      re: /terminat|fired|salary|employer|dues|नौकरी|वेतन/i },
  { key: "rti",      label: "RTI",                 law: "RTI Act §6",        re: /\brti\b|right to information|सूचना का अधिकार/i },
  { key: "bail",     label: "Criminal / bail",     law: "BNSS",              re: /\bbail\b|arrest|\bfir\b|जमानत|गिरफ्तार/i },
];

const ACTS = [
  "Negotiable Instruments Act, 1881",
  "Consumer Protection Act, 2019",
  "RERA Act, 2016",
  "Bharatiya Nyaya Sanhita, 2023",
  "Bharatiya Sakshya Adhiniyam, 2023",
  "Registration Act, 1908",
];

const FEATURES = [
  { icon: MessageSquare, tone: "blue", title: "Legal chat",            text: "Ask about any situation. A 7-agent pipeline works through triage, facts and research before answering." },
  { icon: BookOpen,      tone: "violet", title: "Cited Bare Acts",       text: "Answers are grounded in Indian Bare Acts and Supreme Court and High Court judgments." },
  { icon: BadgeCheck,    tone: "green", title: "Verified citations",    text: "Every section number, Act title, limitation period and penalty is checked against the corpus before you see it." },
  { icon: FileText,      tone: "orange", title: "Legal notice drafter",  text: "A 15-day pre-litigation notice that updates as you add facts. Print it or download a PDF." },
  { icon: UserCheck,     tone: "teal", title: "Advocate matching",     text: "Find Bar Council verified advocates by city, district court and practice area." },
  { icon: CalendarCheck, tone: "rose", title: "Book a consultation",   text: "Choose a phone call, video consult or chamber visit, pick a time and attach your notice." },
  { icon: EyeOff,        tone: "sky", title: "Privacy by default",    text: "Aadhaar, PAN, phone numbers and emails are masked before any AI or search call." },
  { icon: Languages,     tone: "amber", title: "Hindi and English",     text: "Type or speak your question in either language." },
];

const STEPS = [
  { title: "Ask your question",   text: "Type or speak it in plain language. No legal jargon needed." },
  { title: "Get the analysis",    text: "The agents check urgency, pull the relevant Acts and precedents, and verify every citation." },
  { title: "Take the next step",  text: "Read the exact sections and your options, download a draft notice, or book an advocate near your court." },
];

const FAQS = [
  { q: "Is OnlineVakeel free?", a: "Asking questions and drafting a notice is free. Advocates set their own consultation fees, and you see the fee in ₹ on their profile before you book." },
  { q: "Is this legal advice?", a: "No. It is informational guidance based on public Bare Acts and judgments. For advice on your specific case, consult an enrolled advocate. You can book one from the results." },
  { q: "How do you stop wrong citations?", a: "A separate verifier agent checks every section number, Act title, limitation deadline and penalty against the indexed corpus before the answer reaches you." },
  { q: "What happens to my personal details?", a: "Aadhaar numbers, PAN, phone numbers and emails are redacted before any model or vector search call. An advocate sees your phone number only after they accept your consultation." },
  { q: "Which areas of law are covered?", a: "Cheque bounce (NI Act §138), property and RERA, consumer disputes, cyber fraud, employment, criminal bail and RTI. More Acts can be added to the corpus." },
];

const HELPLINES = [
  { name: "Emergency",            number: "112" },
  { name: "NALSA free legal aid", number: "15100" },
  { name: "Cyber crime",          number: "1930" },
  { name: "Women helpline",       number: "1091" },
];

/* ───────────────────────── Hooks / small components ───────────────────────── */

function useTypewriter(lines: string[], paused: boolean) {
  const [text, setText] = useState("");
  useEffect(() => {
    if (paused) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) { setText(lines[0]); return; }
    let line = 0, char = 0, deleting = false;
    let timer: ReturnType<typeof setTimeout>;
    setText("");
    const tick = () => {
      const full = lines[line];
      char += deleting ? -1 : 1;
      setText(full.slice(0, char));
      let delay = deleting ? 22 : 42;
      if (!deleting && char === full.length) { deleting = true; delay = 1800; }
      else if (deleting && char === 0) { deleting = false; line = (line + 1) % lines.length; delay = 350; }
      timer = setTimeout(tick, delay);
    };
    timer = setTimeout(tick, 500);
    return () => clearTimeout(timer);
  }, [lines, paused]);
  return text;
}

/* Counts up once, the first time it scrolls into view. */
function CountUp({ to, suffix = "" }: { to: number; suffix?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const [n, setN] = useState(0);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return;
      io.disconnect();
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) { setN(to); return; }
      const start = performance.now(), dur = 1200;
      const step = (now: number) => {
        const p = Math.min((now - start) / dur, 1);
        setN(Math.round(to * (1 - Math.pow(1 - p, 3))));
        if (p < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    }, { threshold: 0.4 });
    io.observe(el);
    return () => io.disconnect();
  }, [to]);
  return <span ref={ref}>{n}{suffix}</span>;
}

/* ───────────────────────── Page ───────────────────────── */

export default function LandingPage() {
  const router  = useRouter();
  const textRef = useRef<HTMLTextAreaElement>(null);
  const recRef  = useRef<any>(null);
  const fillRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  const [input,      setInput]      = useState("");
  const [lang,       setLang]       = useState<Lang>("en");
  const [listening,  setListening]  = useState(false);
  const [voiceNote,  setVoiceNote]  = useState("");
  const [going,      setGoing]      = useState(false);
  const [justFilled, setJustFilled] = useState(false);
  const [sosOpen,    setSosOpen]    = useState(false);
  const [lawsOpen,   setLawsOpen]   = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled,   setScrolled]   = useState(false);

  const t = COPY[lang];
  const placeholder = useTypewriter(t.examples, input.length > 0);

  /* Saved language + header shadow on scroll */
  useEffect(() => {
    try {
      const saved = localStorage.getItem("ov-lang");
      if (saved === "hi" || saved === "en") setLang(saved);
    } catch { /* storage unavailable */ }
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const changeLang = (next: Lang) => {
    setLang(next);
    try { localStorage.setItem("ov-lang", next); } catch { /* ignore */ }
    recRef.current?.stop();
  };

  /* Auto-resize the textarea */
  useEffect(() => {
    const el = textRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 150)}px`;
  }, [input]);

  const detected = useMemo(() => {
    if (input.trim().length < 12) return null;
    return CATEGORIES.find((c) => c.re.test(input)) ?? null;
  }, [input]);

  const speech = detected
    ? t.speechFound.replace("{label}", detected.label).replace("{law}", detected.law)
    : t.speech;

  const cancelFill = useCallback(() => {
    if (fillRef.current) { clearInterval(fillRef.current); fillRef.current = null; }
  }, []);

  const fillFromChip = (query: string) => {
    cancelFill();
    setJustFilled(true);
    textRef.current?.focus();
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) { setInput(query); return; }
    let i = 0;
    setInput("");
    fillRef.current = setInterval(() => {
      i += 3;
      setInput(query.slice(0, i));
      if (i >= query.length) cancelFill();
    }, 14);
  };

  const submit = (text?: string) => {
    const q = (text ?? input).trim();
    if (!q || going) return;
    cancelFill();
    recRef.current?.stop();
    setGoing(true);
    router.push(`/consult?q=${encodeURIComponent(q)}${lang === "hi" ? "&lang=hi" : ""}`);
  };

  const toggleVoice = () => {
    if (listening) { recRef.current?.stop(); return; }
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) { setVoiceNote(t.voiceUnsupported); return; }
    setVoiceNote("");
    cancelFill();
    const base = input.trim() ? input.trim() + " " : "";
    const rec = new SR();
    rec.lang = lang === "hi" ? "hi-IN" : "en-IN";
    rec.interimResults = true;
    rec.continuous = true;
    rec.onresult = (e: any) => {
      let transcript = "";
      for (let i = 0; i < e.results.length; i++) transcript += e.results[i][0].transcript;
      setInput(base + transcript);
    };
    rec.onerror = () => setListening(false);
    rec.onend   = () => setListening(false);
    recRef.current = rec;
    rec.start();
    setListening(true);
  };

  /* "Start free" and similar buttons jump to the chat box */
  const focusAsk = () => {
    setMobileOpen(false);
    document.getElementById("ask")?.scrollIntoView({ behavior: "smooth", block: "center" });
    setTimeout(() => textRef.current?.focus({ preventScroll: true }), 350);
  };

  /* Close menus on outside click / Escape */
  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setLawsOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") { setLawsOpen(false); setSosOpen(false); setMobileOpen(false); }
    };
    document.addEventListener("mousedown", onClick);
    window.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("mousedown", onClick); window.removeEventListener("keydown", onKey); };
  }, []);

  useEffect(() => () => { cancelFill(); recRef.current?.stop(); }, [cancelFill]);

  return (
    <div className={`nv-root ${serif.variable} ${body.variable} ${serifHi.variable}`}>

      {/* ── HEADER ── */}
      <header className={`nv-header ${scrolled ? "is-scrolled" : ""}`}>
        <div className="nv-header-inner">
          <Link href="/" className="nv-brand">
            <span className="nv-seal"><Scale size={16} /></span>
            <span>OnlineVakeel<span className="nv-brand-dot">.com</span></span>
          </Link>

          <nav className={`nv-nav ${mobileOpen ? "is-open" : ""}`} aria-label="Main">
            <a href="#features" onClick={() => setMobileOpen(false)}>Features</a>
            <a href="#how" onClick={() => setMobileOpen(false)}>How it works</a>

            <div className="nv-dropdown" ref={menuRef}>
              <button
                className="nv-dropdown-btn"
                aria-expanded={lawsOpen}
                aria-haspopup="true"
                onClick={() => setLawsOpen((o) => !o)}
              >
                Bare Acts <ChevronDown size={14} className={lawsOpen ? "nv-flip" : ""} />
              </button>
              {lawsOpen && (
                <div className="nv-menu" role="menu">
                  {ACTS.map((a) => (
                    <Link key={a} href="/consult?tab=corpus" role="menuitem" onClick={() => { setLawsOpen(false); setMobileOpen(false); }}>
                      {a}
                    </Link>
                  ))}
                  <Link href="/consult?tab=corpus" className="nv-menu-all" role="menuitem">All Bare Acts</Link>
                </div>
              )}
            </div>

            <a href="#faqs" onClick={() => setMobileOpen(false)}>FAQs</a>
            <Link href="/consult?tab=advocate">For advocates</Link>
          </nav>

          <div className="nv-header-actions">
            <div className="nv-lang" role="group" aria-label="Language">
              <button className={lang === "en" ? "is-active" : ""} aria-pressed={lang === "en"} onClick={() => changeLang("en")}>EN</button>
              <button className={lang === "hi" ? "is-active" : ""} aria-pressed={lang === "hi"} onClick={() => changeLang("hi")} lang="hi">हिं</button>
            </div>
            <button className="nv-btn nv-btn-primary nv-hide-sm" onClick={focusAsk}>Ask for free</button>
            <button className="nv-burger" aria-label="Menu" aria-expanded={mobileOpen} onClick={() => setMobileOpen((o) => !o)}>
              {mobileOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>
      </header>

      <main>
        {/* ── HERO ── */}
        <section className="nv-hero-band" id="ask">
          {/* Floating judicial background watermarks & law badges */}
          <div className="nv-hero-bg" aria-hidden="true">
            {/* Scales of Justice (top right) */}
            <svg className="nv-hero-watermark nv-wm-right" viewBox="0 0 240 240" fill="none">
              <g stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M120 26v164" />
                <path d="M88 190h64M76 202h88" />
                <path d="M52 64h136" />
                <circle cx="120" cy="40" r="7" />
                <path d="M52 64L30 116h44L52 64z" />
                <path d="M30 116a22 10 0 0 0 44 0" />
                <path d="M188 64l-22 52h44l-22-52z" />
                <path d="M166 116a22 10 0 0 0 44 0" />
              </g>
            </svg>

            {/* Courthouse Pillars (bottom left) */}
            <svg className="nv-hero-watermark nv-wm-left" viewBox="0 0 220 220" fill="none">
              <g stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                <path d="M34 76L110 34l76 42H34z" />
                <path d="M44 86h132" />
                <path d="M56 86v76M82 86v76M110 86v76M138 86v76M164 86v76" />
                <path d="M38 162h144M30 176h160" />
              </g>
            </svg>

            {/* Judge's Gavel (top left) */}
            <svg className="nv-hero-watermark nv-wm-gavel" viewBox="0 0 180 180" fill="none">
              <g stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <rect x="66" y="34" width="44" height="24" rx="4" transform="rotate(35 88 46)" />
                <path d="M98 62l48 48" />
                <path d="M34 136h64M26 148h80" />
              </g>
            </svg>

            {/* Statute / Bare Act Book (bottom right) */}
            <svg className="nv-hero-watermark nv-wm-book" viewBox="0 0 180 180" fill="none">
              <g stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                <path d="M38 42h46a14 14 0 0 1 14 14v86a10 10 0 0 0-10-10H38V42z" />
                <path d="M158 42h-46a14 14 0 0 0-14 14v86a10 10 0 0 1 10-10h50V42z" />
                <path d="M52 68h26M52 86h26M118 68h26M118 86h26" />
              </g>
            </svg>

            <span className="nv-float-item nv-fl-1">
              <Scale size={14} />
              <span>§ 138 · Cheque Bounce</span>
            </span>
            <span className="nv-float-item nv-fl-2">
              <Landmark size={14} />
              <span>BNS · Criminal Law</span>
            </span>
            <span className="nv-float-item nv-fl-3">
              <FileText size={14} />
              <span>Legal Notice · 15 Days</span>
            </span>
            <span className="nv-float-item nv-fl-4">
              <BookOpen size={14} />
              <span>RERA · Consumer Act</span>
            </span>
            <span className="nv-float-item nv-fl-5">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="m14 13-7.5 7.5c-.83.83-2.17.83-3 0 0 0 0 0 0 0a2.12 2.12 0 0 1 0-3L11 10" />
                <path d="m16 16 6-6" />
                <path d="m8 8 6-6" />
                <path d="m9 7 8 8" />
                <path d="m21 11-8-8" />
              </svg>
              <span>Supreme Court &amp; HC</span>
            </span>

            <span className="nv-float-glyph nv-fg-1">§</span>
            <span className="nv-float-glyph nv-fg-2">¶</span>
          </div>
          <div className="nv-hero">
          <div className="nv-hero-copy">
            <div className="nv-eyebrow" lang={lang}>
              <Scale size={13} aria-hidden="true" />
              <span>{t.eyebrow}</span>
            </div>
            <h1 lang={lang}>{t.h1}</h1>
            <p className="nv-sub" lang={lang}>{t.sub}</p>

            <div className={`nv-chat ${listening ? "is-listening" : ""}`}>
              <div className="nv-bot">
                <span className="nv-bot-avatar"><AdvocateAvatar variant="bust" /></span>
                <span className="nv-bubble" key={detected ? speech : "hello"} lang={lang}>{detected ? speech : t.hello}</span>
              </div>

              <textarea
                ref={textRef}
                className="nv-textarea"
                placeholder={placeholder}
                aria-label="Describe your legal situation"
                value={input}
                rows={2}
                lang={lang}
                onChange={(e) => { cancelFill(); setJustFilled(false); setInput(e.target.value); }}
                onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); } }}
              />

              <div className="nv-detect-slot" aria-live="polite">
                {detected && (
                  <span className="nv-detect" key={detected.key}>
                    <Sparkles size={12} />
                    {t.detected}: <strong>{detected.label}</strong>
                    <span className="nv-law">{detected.law}</span>
                  </span>
                )}
                {!detected && justFilled && input.length > 0 && <span className="nv-detect nv-quiet">{t.fillHint}</span>}
              </div>

              <div className="nv-chat-footer">
                <span className="nv-hint"><Lock size={12} /> Aadhaar, PAN and phone numbers are masked before AI processing</span>
                <div className="nv-actions">
                  <button
                    type="button"
                    className={`nv-icon-btn ${listening ? "is-on" : ""}`}
                    onClick={toggleVoice}
                    aria-pressed={listening}
                    aria-label={listening ? "Stop voice input" : "Start voice input"}
                  >
                    {listening ? <MicOff size={16} /> : <Mic size={16} />}
                  </button>
                  <button className="nv-btn nv-btn-primary" onClick={() => submit()} disabled={!input.trim() || going}>
                    {going ? <>{t.going}<Loader2 size={15} className="nv-spin" /></> : <>{t.cta}<ArrowRight size={15} /></>}
                  </button>
                </div>
              </div>
            </div>
            {voiceNote && <p className="nv-voice-note" role="status">{voiceNote}</p>}

            <div className="nv-suggest" lang={lang}>
              <span>{t.suggest}</span>
              {QUICK_PROMPTS.map((p) => (
                <button key={p.label} className="nv-chip" onClick={() => fillFromChip(p.query)}>{p.label}</button>
              ))}
            </div>

            <ul className="nv-pills">
              <li className="tone-blue"><Languages size={14} /> Hindi &amp; English</li>
              <li className="tone-green"><BadgeCheck size={14} /> Citations verified</li>
              <li className="tone-violet"><ShieldCheck size={14} /> DPDP Act 2023</li>
              <li className="tone-orange"><Landmark size={14} /> Free to start</li>
            </ul>
          </div>

          </div>
        </section>

        {/* ── COVERAGE STATS ── */}
        <section className="nv-stats" aria-label="Coverage">
          <div className="tone-blue"><strong><CountUp to={40} suffix="+" /></strong><span>Indian Bare Acts</span></div>
          <div className="tone-green"><strong><CountUp to={25} /></strong><span>High Courts in the judgment index</span></div>
          <div className="tone-orange"><strong><CountUp to={60} suffix="+" /></strong><span>Cities for advocate matching</span></div>
          <div className="tone-violet"><strong><CountUp to={8} /></strong><span>Agents on every consultation</span></div>
        </section>

        {/* ── FEATURES ── */}
        <section className="nv-section" id="features">
          <div className="nv-law-rule" aria-hidden="true"><span>§</span></div>
          <h2>What you can do on OnlineVakeel</h2>
          <p className="nv-section-sub">From your first question to a booked advocate, in one place.</p>
          <div className="nv-grid">
            {FEATURES.map(({ icon: Icon, tone, title, text }) => (
              <article key={title} className={`nv-card tone-${tone}`}>
                <span className="nv-card-icon"><Icon size={18} /></span>
                <h3>{title}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
        </section>

        {/* ── HOW IT WORKS ── */}
        <section className="nv-section nv-section-tint" id="how">
          <div className="nv-law-rule" aria-hidden="true"><span>§</span></div>
          <h2>How it works</h2>
          <p className="nv-section-sub">No appointment needed to get started. Available any time.</p>
          <ol className="nv-steps">
            {STEPS.map((s, i) => (
              <li key={s.title} className={`tone-${["blue", "green", "orange"][i]}`}>
                <span className="nv-step-n">{i + 1}</span>
                <h3>{s.title}</h3>
                <p>{s.text}</p>
              </li>
            ))}
          </ol>
        </section>

        {/* ── FAQ ── */}
        <section className="nv-section" id="faqs">
          <h2>Frequently asked questions</h2>
          <div className="nv-faq">
            {FAQS.map((f) => (
              <details key={f.q}>
                <summary>{f.q}<ChevronDown size={16} /></summary>
                <p>{f.a}</p>
              </details>
            ))}
          </div>
        </section>

        {/* ── FINAL CTA ── */}
        <section className="nv-cta">
          <h2>Have a legal question? Ask it now.</h2>
          <p>Describe your situation and see the law that applies to it.</p>
          <div className="nv-cta-actions">
            <button className="nv-btn nv-btn-light" onClick={focusAsk}>Ask for free</button>
            <Link href="/consult?tab=advocate" className="nv-btn nv-btn-ghost">I'm an advocate</Link>
          </div>
        </section>
      </main>

      {/* ── FOOTER ── */}
      <footer className="nv-footer">
        <div className="nv-footer-inner">
          <div>
            <Link href="/" className="nv-brand"><span className="nv-seal"><Scale size={16} /></span><span>OnlineVakeel<span className="nv-brand-dot">.com</span></span></Link>
            <p>Informational guidance only. Not a substitute for advice from an enrolled advocate.</p>
          </div>
          <div>
            <h4>Explore</h4>
            <a href="#features">Features</a>
            <a href="#how">How it works</a>
            <a href="#faqs">FAQs</a>
          </div>
          <div>
            <h4>Use it</h4>
            <Link href="/consult">Consultation desk</Link>
            <Link href="/consult?tab=corpus">Bare Acts library</Link>
            <Link href="/consult?tab=advocate">Advocate portal</Link>
          </div>
          <div>
            <h4>Helplines</h4>
            {HELPLINES.map((h) => <a key={h.number} href={`tel:${h.number}`}>{h.name}: {h.number}</a>)}
          </div>
        </div>
        <div className="nv-footer-bottom">© {new Date().getFullYear()} OnlineVakeel.com</div>
      </footer>

      {/* ── FLOATING HELPLINES ── */}
      <div className="nv-sos">
        {sosOpen && (
          <div className="nv-sos-panel" role="dialog" aria-label="Emergency helplines">
            <div className="nv-sos-head"><span>Need help right now?</span><button onClick={() => setSosOpen(false)} aria-label="Close"><X size={14} /></button></div>
            {HELPLINES.map((h) => (
              <a key={h.number} href={`tel:${h.number}`}><span>{h.name}</span><strong>{h.number}</strong></a>
            ))}
          </div>
        )}
        <button className="nv-sos-btn" onClick={() => setSosOpen((o) => !o)} aria-expanded={sosOpen}>
          <PhoneCall size={14} /> Emergency helplines
        </button>
      </div>
    </div>
  );
}
