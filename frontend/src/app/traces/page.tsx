"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock,
  Cpu,
  Lock,
  MessageSquareText,
  Play,
  RefreshCw,
  Scale,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

const BACKEND = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface TraceSpan {
  step: string;
  agent: string;
  model_or_tool: string;
  start_ms: number;
  duration_ms: number;
  status: string;
  detail: string;
  payload?: Record<string, unknown>;
}

interface QueryTrace {
  trace_id: string;
  case_id: string;
  timestamp: string;
  redacted_query: string;
  category: string;
  urgency: string;
  pii_redacted_count: number;
  pii_types: string[];
  citations_count: number;
  citations: string[];
  verified: boolean;
  verification_badge: string;
  matched_advocates_count: number;
  notice_title: string;
  final_answer?: string;
  total_latency_ms: number;
  spans: TraceSpan[];
}

interface TracesPayload {
  demo_only: boolean;
  notice: string;
  models: {
    embedding_model: string;
    embedding_ca_cert: string;
    chat_model: string;
    chat_ca_cert: string;
  };
  summary: {
    total_queries: number;
    avg_latency_ms: number;
    total_pii_masked: number;
    verification_pass_rate: number;
  };
  traces: QueryTrace[];
}

const SHOWCASE_QUERIES = [
  {
    label: "1. PII Masking + Tenancy Deposit",
    query:
      "Hi, I'm Rajesh Kumar (phone 9876543210, Aadhaar 1234-5678-9012). My landlord in Bengaluru hasn't returned my Rs. 1,20,000 security deposit 45 days after vacating.",
  },
  {
    label: "2. Cheque Bounce (Sec 138 NI Act)",
    query:
      "A client gave me a cheque for Rs. 3,50,000 in New Delhi that bounced due to insufficient funds 10 days ago. What is my legal deadline and next step?",
  },
  {
    label: "3. High-Urgency Escalation",
    query:
      "Police came to my shop without a warrant and threatened to arrest me tonight over a civil business dispute.",
  },
  {
    label: "4. Consumer Fraud (Defective Laptop)",
    query:
      "I bought a defective laptop online for Rs. 75,000 from TechMart India (Order ORD-88412) and the seller is refusing a refund.",
  },
  {
    label: "5. Anti-Hallucination Guardrail Test",
    query:
      "Can you cite Section 999 of the Indian Cyber Crime Act 2025 to sue my neighbor for loud music?",
  },
];

export default function TracesDemoPage() {
  const [data, setData] = useState<TracesPayload | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [runningQuery, setRunningQuery] = useState<string | null>(null);
  const [customQuery, setCustomQuery] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [expandedSteps, setExpandedSteps] = useState<Record<string, boolean>>({});

  const toggleStep = (stepKey: string) => {
    setExpandedSteps((prev) => ({ ...prev, [stepKey]: !prev[stepKey] }));
  };

  const setAllSteps = (spans: TraceSpan[], open: boolean) => {
    const next: Record<string, boolean> = {};
    spans.forEach((s) => {
      next[s.step] = open;
    });
    setExpandedSteps(next);
  };

  const fetchTraces = useCallback(async () => {
    try {
      setError(null);
      const res = await fetch(`${BACKEND}/api/traces`, { cache: "no-store" });
      if (!res.ok) throw new Error(`Backend returned ${res.status}`);
      const json: TracesPayload = await res.json();
      setData(json);
      if (json.traces.length > 0) {
        setSelectedId((prev) =>
          prev && json.traces.some((t) => t.trace_id === prev)
            ? prev
            : json.traces[0].trace_id
        );
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? `Could not connect to backend (${err.message}). Make sure FastAPI is running on ${BACKEND}.`
          : "Could not load traces."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTraces();
  }, [fetchTraces]);

  const executeRealQuery = async (queryText: string, label: string) => {
    if (!queryText.trim()) return;
    setRunningQuery(label);
    setError(null);
    try {
      const res = await fetch(`${BACKEND}/api/consult`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: queryText.trim(), language: "en" }),
      });
      if (!res.ok) throw new Error(`Consult API failed (${res.status})`);
      const consultJson = await res.json();
      await fetchTraces();
      if (consultJson.trace_id) {
        setSelectedId(consultJson.trace_id);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to execute query."
      );
    } finally {
      setRunningQuery(null);
    }
  };

  const selectedTrace =
    data?.traces.find((t) => t.trace_id === selectedId) || data?.traces[0] || null;

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#0b1120",
        color: "#e2e8f0",
        fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      }}
    >
      {/* Demo-Only Top Banner */}
      <div
        style={{
          background: "linear-gradient(90deg, #92400e 0%, #b45309 50%, #92400e 100%)",
          color: "#fef3c7",
          padding: "10px 24px",
          fontSize: "13px",
          fontWeight: 600,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "10px",
          borderBottom: "1px solid rgba(251, 191, 36, 0.35)",
          textAlign: "center",
        }}
      >
        <AlertTriangle size={16} />
        <span>
          DEMO OBSERVABILITY ONLY — This Trace Dashboard is included solely for live presentation &amp; demo verification and is NOT part of the core OnlineVakeel.com production product.
        </span>
      </div>

      <div style={{ maxWidth: "1280px", margin: "0 auto", padding: "24px" }}>
        {/* Header */}
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "16px",
            marginBottom: "24px",
          }}
        >
          <div>
            <Link
              href="/"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                color: "#94a3b8",
                textDecoration: "none",
                fontSize: "13px",
                marginBottom: "8px",
              }}
            >
              <ArrowLeft size={14} /> Back to OnlineVakeel.com
            </Link>
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <div
                style={{
                  width: "38px",
                  height: "38px",
                  borderRadius: "10px",
                  background: "rgba(217, 119, 6, 0.16)",
                  border: "1px solid rgba(217, 119, 6, 0.4)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#fbbf24",
                }}
              >
                <Activity size={20} />
              </div>
              <div>
                <h1 style={{ margin: 0, fontSize: "22px", fontWeight: 700, color: "#f8fafc" }}>
                  Live Query Execution Traces{" "}
                  <span
                    style={{
                      fontSize: "12px",
                      fontWeight: 600,
                      padding: "3px 8px",
                      borderRadius: "999px",
                      background: "rgba(245, 158, 11, 0.18)",
                      color: "#fbbf24",
                      border: "1px solid rgba(245, 158, 11, 0.35)",
                      verticalAlign: "middle",
                      marginLeft: "6px",
                    }}
                  >
                    DEMO ONLY
                  </span>
                </h1>
                <p style={{ margin: "2px 0 0", fontSize: "13px", color: "#94a3b8" }}>
                  Real-time multi-agent span waterfall for <code>/api/consult</code> executions
                </p>
              </div>
            </div>
          </div>

          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", alignItems: "center" }}>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                fontSize: "12px",
                padding: "6px 10px",
                borderRadius: "8px",
                background: "#1e293b",
                border: "1px solid #334155",
                color: "#cbd5e1",
              }}
            >
              <Lock size={13} color="#38bdf8" />
              Embed: <strong>{data?.models.embedding_model || "bge-small-en-v1.5"}</strong> (
              {data?.models.embedding_ca_cert || "certs/vm02-ca.crt"})
            </span>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                fontSize: "12px",
                padding: "6px 10px",
                borderRadius: "8px",
                background: "#1e293b",
                border: "1px solid #334155",
                color: "#cbd5e1",
              }}
            >
              <Cpu size={13} color="#a78bfa" />
              Chat: <strong>{data?.models.chat_model || "Qwen/Qwen3-8B"}</strong> (
              {data?.models.chat_ca_cert || "certs/vm07-ca.crt"})
            </span>
            <button
              onClick={fetchTraces}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                padding: "7px 12px",
                borderRadius: "8px",
                background: "#1e293b",
                border: "1px solid #475569",
                color: "#f8fafc",
                fontSize: "12px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              <RefreshCw size={13} /> Refresh
            </button>
          </div>
        </div>

        {/* KPI Cards */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))",
            gap: "14px",
            marginBottom: "22px",
          }}
        >
          {[
            {
              label: "Real Queries Executed",
              value: data?.summary.total_queries ?? 0,
              icon: <Scale size={18} color="#38bdf8" />,
            },
            {
              label: "Avg Pipeline Latency",
              value: `${data?.summary.avg_latency_ms ?? 0} ms`,
              icon: <Clock size={18} color="#fbbf24" />,
            },
            {
              label: "PII Entities Masked (DPDP)",
              value: data?.summary.total_pii_masked ?? 0,
              icon: <ShieldCheck size={18} color="#34d399" />,
            },
            {
              label: "Citation Verification Rate",
              value: `${data?.summary.verification_pass_rate ?? 100}%`,
              icon: <CheckCircle2 size={18} color="#a78bfa" />,
            },
          ].map((kpi) => (
            <div
              key={kpi.label}
              style={{
                background: "#111827",
                border: "1px solid #1f2937",
                borderRadius: "12px",
                padding: "16px",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <div>
                <div style={{ fontSize: "12px", color: "#94a3b8", marginBottom: "4px" }}>
                  {kpi.label}
                </div>
                <div style={{ fontSize: "24px", fontWeight: 700, color: "#f8fafc" }}>
                  {kpi.value}
                </div>
              </div>
              <div
                style={{
                  width: "38px",
                  height: "38px",
                  borderRadius: "10px",
                  background: "#1e293b",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                {kpi.icon}
              </div>
            </div>
          ))}
        </div>

        {/* Quick-Run Real Showcase Queries */}
        <div
          style={{
            background: "#111827",
            border: "1px solid #1f2937",
            borderRadius: "12px",
            padding: "16px",
            marginBottom: "22px",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "10px",
              flexWrap: "wrap",
              gap: "8px",
            }}
          >
            <div style={{ fontSize: "13px", fontWeight: 600, color: "#f8fafc", display: "flex", alignItems: "center", gap: "6px" }}>
              <Sparkles size={15} color="#fbbf24" />
              Run a Real Query Through <code>/api/consult</code> to Generate Live Trace
            </div>
            {runningQuery && (
              <span style={{ fontSize: "12px", color: "#fbbf24" }}>
                Executing &ldquo;{runningQuery}&rdquo;...
              </span>
            )}
          </div>

          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "12px" }}>
            {SHOWCASE_QUERIES.map((sq) => (
              <button
                key={sq.label}
                disabled={Boolean(runningQuery)}
                onClick={() => executeRealQuery(sq.query, sq.label)}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "7px 11px",
                  borderRadius: "8px",
                  background: "#1e293b",
                  border: "1px solid #334155",
                  color: "#e2e8f0",
                  fontSize: "12px",
                  fontWeight: 500,
                  cursor: runningQuery ? "not-allowed" : "pointer",
                  opacity: runningQuery ? 0.6 : 1,
                }}
              >
                <Play size={12} color="#34d399" />
                {sq.label}
              </button>
            ))}
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              executeRealQuery(customQuery, "Custom Query");
            }}
            style={{ display: "flex", gap: "8px" }}
          >
            <input
              type="text"
              value={customQuery}
              onChange={(e) => setCustomQuery(e.target.value)}
              placeholder="Or type any custom legal query (e.g., My employer hasn't paid 2 months salary in Mumbai)..."
              style={{
                flex: 1,
                padding: "9px 12px",
                borderRadius: "8px",
                background: "#0b1120",
                border: "1px solid #334155",
                color: "#f8fafc",
                fontSize: "13px",
              }}
            />
            <button
              type="submit"
              disabled={Boolean(runningQuery) || !customQuery.trim()}
              style={{
                padding: "9px 16px",
                borderRadius: "8px",
                background: "#d97706",
                border: "none",
                color: "#ffffff",
                fontSize: "13px",
                fontWeight: 600,
                cursor: runningQuery || !customQuery.trim() ? "not-allowed" : "pointer",
              }}
            >
              Run Trace
            </button>
          </form>
        </div>

        {error && (
          <div
            style={{
              background: "rgba(220, 38, 38, 0.14)",
              border: "1px solid rgba(248, 113, 113, 0.4)",
              color: "#fecaca",
              borderRadius: "10px",
              padding: "12px 16px",
              fontSize: "13px",
              marginBottom: "20px",
            }}
          >
            {error}
          </div>
        )}

        {/* Main Split: Trace List + Span Waterfall */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "minmax(280px, 380px) 1fr",
            gap: "16px",
            alignItems: "start",
          }}
        >
          {/* Left: Executions List */}
          <div
            style={{
              background: "#111827",
              border: "1px solid #1f2937",
              borderRadius: "12px",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                padding: "12px 16px",
                borderBottom: "1px solid #1f2937",
                fontSize: "13px",
                fontWeight: 600,
                color: "#cbd5e1",
              }}
            >
              Recorded Executions ({data?.traces.length ?? 0})
            </div>

            {loading ? (
              <div style={{ padding: "24px", fontSize: "13px", color: "#94a3b8" }}>
                Loading traces...
              </div>
            ) : !data || data.traces.length === 0 ? (
              <div style={{ padding: "24px", fontSize: "13px", color: "#94a3b8", lineHeight: 1.5 }}>
                No query traces recorded yet. Click any showcase button above (or submit a query in{" "}
                <Link href="/consult" style={{ color: "#fbbf24" }}>
                  /consult
                </Link>
                ) to record a real execution.
              </div>
            ) : (
              <div style={{ maxHeight: "620px", overflowY: "auto" }}>
                {data.traces.map((tr) => {
                  const isSelected = selectedTrace?.trace_id === tr.trace_id;
                  return (
                    <button
                      key={tr.trace_id}
                      onClick={() => setSelectedId(tr.trace_id)}
                      style={{
                        width: "100%",
                        textAlign: "left",
                        padding: "12px 16px",
                        background: isSelected ? "#1e293b" : "transparent",
                        border: "none",
                        borderBottom: "1px solid #1f2937",
                        borderLeft: isSelected ? "3px solid #f59e0b" : "3px solid transparent",
                        color: "#e2e8f0",
                        cursor: "pointer",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          marginBottom: "6px",
                          fontSize: "11px",
                        }}
                      >
                        <span style={{ color: "#fbbf24", fontWeight: 600 }}>
                          {tr.category.replace(/_/g, " ").toUpperCase()}
                        </span>
                        <span style={{ color: "#94a3b8" }}>{tr.total_latency_ms} ms</span>
                      </div>
                      <div
                        style={{
                          fontSize: "13px",
                          color: "#f8fafc",
                          marginBottom: "8px",
                          display: "-webkit-box",
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: "vertical",
                          overflow: "hidden",
                        }}
                      >
                        {tr.redacted_query}
                      </div>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", fontSize: "11px" }}>
                        <span
                          style={{
                            padding: "2px 6px",
                            borderRadius: "6px",
                            background:
                              tr.urgency === "emergency" || tr.urgency === "urgent"
                                ? "rgba(239, 68, 68, 0.18)"
                                : "rgba(56, 189, 248, 0.14)",
                            color:
                              tr.urgency === "emergency" || tr.urgency === "urgent"
                                ? "#fca5a5"
                                : "#7dd3fc",
                          }}
                        >
                          {tr.urgency}
                        </span>
                        <span
                          style={{
                            padding: "2px 6px",
                            borderRadius: "6px",
                            background: "rgba(52, 211, 153, 0.14)",
                            color: "#6ee7b7",
                          }}
                        >
                          PII masked: {tr.pii_redacted_count}
                        </span>
                        <span
                          style={{
                            padding: "2px 6px",
                            borderRadius: "6px",
                            background: "rgba(167, 139, 250, 0.14)",
                            color: "#c4b5fd",
                          }}
                        >
                          {tr.citations_count} cites
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Right: Span Waterfall Inspector */}
          <div
            style={{
              background: "#111827",
              border: "1px solid #1f2937",
              borderRadius: "12px",
              padding: "20px",
            }}
          >
            {!selectedTrace ? (
              <div style={{ color: "#94a3b8", fontSize: "14px" }}>
                Select or execute a query to inspect its multi-agent span waterfall.
              </div>
            ) : (
              <>
                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    justifyContent: "space-between",
                    gap: "12px",
                    paddingBottom: "14px",
                    borderBottom: "1px solid #1f2937",
                    marginBottom: "16px",
                  }}
                >
                  <div>
                    <div style={{ fontSize: "11px", color: "#94a3b8", marginBottom: "4px" }}>
                      TRACE ID: <code>{selectedTrace.trace_id}</code> · CASE:{" "}
                      <code>{selectedTrace.case_id}</code>
                    </div>
                    <div style={{ fontSize: "15px", fontWeight: 600, color: "#f8fafc" }}>
                      {selectedTrace.redacted_query}
                    </div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: "20px", fontWeight: 700, color: "#fbbf24" }}>
                      {selectedTrace.total_latency_ms} ms
                    </div>
                    <div style={{ fontSize: "11px", color: "#34d399" }}>
                      {selectedTrace.verification_badge}
                    </div>
                  </div>
                </div>

                {/* Waterfall Bars */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginBottom: "12px",
                    gap: "10px",
                    flexWrap: "wrap",
                  }}
                >
                  <div style={{ fontSize: "13px", fontWeight: 600, color: "#cbd5e1" }}>
                    Multi-Agent Execution Waterfall (Click any stage to expand details)
                  </div>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <button
                      onClick={() => setAllSteps(selectedTrace.spans, true)}
                      style={{
                        padding: "4px 10px",
                        borderRadius: "6px",
                        background: "#1e293b",
                        border: "1px solid #334155",
                        color: "#cbd5e1",
                        fontSize: "11px",
                        cursor: "pointer",
                      }}
                    >
                      Expand All
                    </button>
                    <button
                      onClick={() => setAllSteps(selectedTrace.spans, false)}
                      style={{
                        padding: "4px 10px",
                        borderRadius: "6px",
                        background: "#1e293b",
                        border: "1px solid #334155",
                        color: "#cbd5e1",
                        fontSize: "11px",
                        cursor: "pointer",
                      }}
                    >
                      Collapse All
                    </button>
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "20px" }}>
                  {selectedTrace.spans.map((sp) => {
                    const total = Math.max(selectedTrace.total_latency_ms, 1);
                    const leftPct = Math.min((sp.start_ms / total) * 100, 96);
                    const widthPct = Math.max((sp.duration_ms / total) * 100, 2);
                    const isExpanded = Boolean(expandedSteps[sp.step]);
                    return (
                      <div
                        key={sp.step}
                        style={{
                          background: "#0b1120",
                          border: isExpanded ? "1px solid #475569" : "1px solid #1e293b",
                          borderRadius: "8px",
                          padding: "10px 12px",
                        }}
                      >
                        <button
                          type="button"
                          onClick={() => toggleStep(sp.step)}
                          style={{
                            width: "100%",
                            background: "transparent",
                            border: "none",
                            padding: 0,
                            textAlign: "left",
                            color: "inherit",
                            cursor: "pointer",
                          }}
                        >
                          <div
                            style={{
                              display: "flex",
                              justifyContent: "space-between",
                              alignItems: "center",
                              fontSize: "12px",
                              marginBottom: "6px",
                            }}
                          >
                            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                              {isExpanded ? (
                                <ChevronDown size={14} color="#fbbf24" />
                              ) : (
                                <ChevronRight size={14} color="#94a3b8" />
                              )}
                              <strong style={{ color: "#f8fafc" }}>{sp.step}</strong>
                              <span style={{ color: "#64748b" }}>· {sp.model_or_tool}</span>
                            </div>
                            <span style={{ color: "#fbbf24", fontWeight: 600 }}>
                              {sp.duration_ms} ms
                            </span>
                          </div>
                          <div
                            style={{
                              height: "8px",
                              background: "#1e293b",
                              borderRadius: "999px",
                              position: "relative",
                              overflow: "hidden",
                              marginBottom: "6px",
                            }}
                          >
                            <div
                              style={{
                                position: "absolute",
                                left: `${leftPct}%`,
                                width: `${widthPct}%`,
                                height: "100%",
                                borderRadius: "999px",
                                background:
                                  sp.agent === "ResearchAgent"
                                    ? "#38bdf8"
                                    : sp.agent === "ConversationalAgent" || sp.agent === "DraftingAgent"
                                    ? "#a78bfa"
                                    : sp.agent === "PIIRedactor" || sp.agent === "VerifierAgent"
                                    ? "#34d399"
                                    : "#f59e0b",
                              }}
                            />
                          </div>
                          <div style={{ fontSize: "12px", color: "#94a3b8" }}>{sp.detail}</div>
                        </button>

                        {isExpanded && sp.payload && (
                          <div
                            style={{
                              marginTop: "10px",
                              paddingTop: "10px",
                              borderTop: "1px dashed #334155",
                            }}
                          >
                            <div
                              style={{
                                fontSize: "11px",
                                fontWeight: 600,
                                color: "#94a3b8",
                                marginBottom: "6px",
                                textTransform: "uppercase",
                                letterSpacing: "0.04em",
                              }}
                            >
                              Stage Output Details ({sp.agent})
                            </div>
                            <pre
                              style={{
                                margin: 0,
                                padding: "10px 12px",
                                borderRadius: "6px",
                                background: "#020617",
                                border: "1px solid #1e293b",
                                color: "#cbd5e1",
                                fontSize: "12px",
                                lineHeight: 1.5,
                                overflowX: "auto",
                                whiteSpace: "pre-wrap",
                                wordBreak: "break-word",
                              }}
                            >
                              {JSON.stringify(sp.payload, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* Final Conversational Agent Answer */}
                {selectedTrace.final_answer && (
                  <div
                    style={{
                      background: "#0b1120",
                      border: "1px solid rgba(167, 139, 250, 0.35)",
                      borderRadius: "10px",
                      padding: "16px",
                      marginBottom: "16px",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        fontSize: "13px",
                        fontWeight: 700,
                        color: "#c4b5fd",
                        marginBottom: "10px",
                      }}
                    >
                      <MessageSquareText size={16} />
                      Final Conversational Agent Answer (Qwen/Qwen3-8B / Guidance)
                    </div>
                    <div
                      style={{
                        fontSize: "13px",
                        lineHeight: 1.65,
                        color: "#e2e8f0",
                      }}
                    >
                      <ReactMarkdown>{selectedTrace.final_answer}</ReactMarkdown>
                    </div>
                  </div>
                )}

                {/* Metadata Footer */}
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                    gap: "12px",
                    fontSize: "12px",
                    background: "#0b1120",
                    border: "1px solid #1e293b",
                    borderRadius: "8px",
                    padding: "12px",
                  }}
                >
                  <div>
                    <div style={{ color: "#64748b", marginBottom: "4px" }}>Retrieved Statutes</div>
                    <div style={{ color: "#e2e8f0" }}>
                      {selectedTrace.citations.length > 0
                        ? selectedTrace.citations.join(" • ")
                        : "No direct statute matched"}
                    </div>
                  </div>
                  <div>
                    <div style={{ color: "#64748b", marginBottom: "4px" }}>Notice &amp; Handoff</div>
                    <div style={{ color: "#e2e8f0" }}>
                      {selectedTrace.notice_title} · {selectedTrace.matched_advocates_count} advocates matched
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
