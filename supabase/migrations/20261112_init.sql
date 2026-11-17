-- =====================================================================
-- ONLINEVAKEEL.COM - SUPABASE DATABASE INITIALIZATION MIGRATION
-- Multi-Agent Legal System with pgvector, DPDP-Compliant Case Store,
-- Advocate Onboarding & Matching, and Verified Bare Acts Corpus
-- =====================================================================

-- 1. Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. User Profiles (Citizens, Advocates, Admin)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE,
    phone_number TEXT,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('citizen', 'advocate', 'admin')),
    language_pref TEXT DEFAULT 'en' CHECK (language_pref IN ('en', 'hi', 'bn', 'te', 'mr', 'ta')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Advocate Profiles & Verification
CREATE TABLE IF NOT EXISTS public.advocate_profiles (
    id UUID PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    bar_council_id TEXT UNIQUE NOT NULL,
    bar_council_state TEXT NOT NULL,
    practice_areas TEXT[] NOT NULL DEFAULT '{}',
    courts TEXT[] NOT NULL DEFAULT '{}',
    district_court TEXT,
    office_location TEXT,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    experience_years INT DEFAULT 1,
    languages_spoken TEXT[] DEFAULT '{"en", "hi"}',
    bio TEXT,
    hourly_consult_fee INT DEFAULT 0,
    rating NUMERIC(2,1) DEFAULT 4.8,
    reviews_count INT DEFAULT 0,
    is_verified BOOLEAN DEFAULT FALSE,
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Citizen Cases & Triage State
CREATE TABLE IF NOT EXISTS public.cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    citizen_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    session_id TEXT NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN (
        'cheque_bounce',
        'consumer_dispute',
        'property_rera',
        'employment_labour',
        'family_divorce',
        'cyber_fraud',
        'criminal_bail',
        'rti_public',
        'general_civil'
    )),
    status TEXT NOT NULL DEFAULT 'intake' CHECK (status IN (
        'intake',
        'analyzing',
        'remedy_ready',
        'drafting',
        'advocate_matched',
        'lawyer_contacted',
        'closed'
    )),
    urgency TEXT NOT NULL DEFAULT 'routine' CHECK (urgency IN ('routine', 'urgent', 'emergency')),
    jurisdiction_state TEXT,
    jurisdiction_city TEXT,
    facts JSONB DEFAULT '{}'::JSONB,
    legal_remedies JSONB DEFAULT '[]'::JSONB,
    drafted_documents JSONB DEFAULT '[]'::JSONB,
    dpdp_consent BOOLEAN DEFAULT TRUE,
    dpdp_consent_timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Chat Messages (Multi-Agent Conversation Store)
CREATE TABLE IF NOT EXISTS public.chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID REFERENCES public.cases(id) ON DELETE CASCADE,
    sender_role TEXT NOT NULL CHECK (sender_role IN ('citizen', 'agent', 'advocate', 'system')),
    agent_type TEXT CHECK (agent_type IN ('orchestrator', 'intake', 'research', 'drafting', 'verifier', 'handoff')),
    content TEXT NOT NULL,
    raw_unredacted_pii BOOLEAN DEFAULT FALSE,
    citations JSONB DEFAULT '[]'::JSONB,
    is_verified BOOLEAN DEFAULT TRUE,
    verification_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Indian Legal Corpus (Bare Acts, Judgments & Procedural Rules)
CREATE TABLE IF NOT EXISTS public.legal_corpus (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    act_code TEXT NOT NULL,           -- e.g. 'NI_ACT_1881', 'BNS_2023', 'CPA_2019'
    act_name TEXT NOT NULL,           -- e.g. 'Negotiable Instruments Act, 1881'
    chapter TEXT,
    section_number TEXT NOT NULL,     -- e.g. '138', '318', '35'
    section_title TEXT NOT NULL,      -- e.g. 'Dishonour of cheque for insufficiency, etc., of funds in the account'
    legal_text TEXT NOT NULL,         -- verbatim statutory text
    plain_summary TEXT NOT NULL,      -- layman explanation in plain English
    penalties TEXT,                   -- statutory jail / fine summary
    limitation_period TEXT,          -- procedural timeline (e.g. '15 days demand notice + 30 days filing')
    bailable_status TEXT,            -- 'Bailable' / 'Non-Bailable' / 'N/A (Civil)'
    compoundable_status TEXT,        -- 'Compoundable' / 'Non-compoundable'
    embedding VECTOR(384),           -- Fast, 100% free BGE-M3 / MiniLM embeddings
    search_tsv TSVECTOR,             -- Hybrid keyword matching
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Advocate Lead Handoffs & Consultations
CREATE TABLE IF NOT EXISTS public.advocate_handoffs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES public.cases(id) ON DELETE CASCADE,
    advocate_id UUID NOT NULL REFERENCES public.advocate_profiles(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'completed')),
    client_masked_brief TEXT NOT NULL,
    urgency TEXT DEFAULT 'routine',
    scheduled_slot TIMESTAMPTZ,
    advocate_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. DPDP Audit Logs (Compliance & Privacy Tracking)
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID REFERENCES public.cases(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    actor_id TEXT,
    details JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================================
-- INDEXES FOR HYBRID SEARCH & HIGH PERFORMANCE
-- =====================================================================

-- Full Text Search Index for Legal Corpus
CREATE INDEX IF NOT EXISTS idx_legal_corpus_tsv ON public.legal_corpus USING GIN(search_tsv);

-- Vector Cosine Similarity Index (HNSW for high-speed RAG)
CREATE INDEX IF NOT EXISTS idx_legal_corpus_embedding ON public.legal_corpus 
USING hnsw (embedding vector_cosine_ops);

-- Case Lookup Indexes
CREATE INDEX IF NOT EXISTS idx_cases_citizen ON public.cases(citizen_id);
CREATE INDEX IF NOT EXISTS idx_cases_session ON public.cases(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_case ON public.chat_messages(case_id);
CREATE INDEX IF NOT EXISTS idx_advocate_city_area ON public.advocate_profiles(city, is_available);

-- Auto-update search_tsv on legal corpus
CREATE OR REPLACE FUNCTION update_legal_corpus_tsv()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_tsv := 
        setweight(to_tsvector('english', COALESCE(NEW.act_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.section_number, '') || ' ' || COALESCE(NEW.section_title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.plain_summary, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.legal_text, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_legal_corpus_tsv ON public.legal_corpus;
CREATE TRIGGER trg_legal_corpus_tsv
BEFORE INSERT OR UPDATE ON public.legal_corpus
FOR EACH ROW EXECUTE FUNCTION update_legal_corpus_tsv();

-- =====================================================================
-- STORED PROCEDURE: HYBRID SEARCH FOR LEGAL CITATIONS
-- =====================================================================
CREATE OR REPLACE FUNCTION match_legal_sections(
    query_embedding VECTOR(384),
    query_text TEXT,
    match_threshold FLOAT DEFAULT 0.35,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    act_code TEXT,
    act_name TEXT,
    section_number TEXT,
    section_title TEXT,
    legal_text TEXT,
    plain_summary TEXT,
    limitation_period TEXT,
    penalties TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        lc.id,
        lc.act_code,
        lc.act_name,
        lc.section_number,
        lc.section_title,
        lc.legal_text,
        lc.plain_summary,
        lc.limitation_period,
        lc.penalties,
        (1 - (lc.embedding <=> query_embedding))::FLOAT AS similarity
    FROM public.legal_corpus lc
    WHERE 
        (lc.embedding IS NOT NULL AND 1 - (lc.embedding <=> query_embedding) > match_threshold)
        OR (query_text IS NOT NULL AND lc.search_tsv @@ plainto_tsquery('english', query_text))
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- SEED DATA: CORE INDIAN BARE ACTS FOR INSTANT DEMO & ACCURACY
-- =====================================================================

INSERT INTO public.legal_corpus (
    act_code, act_name, chapter, section_number, section_title, 
    legal_text, plain_summary, limitation_period, penalties, bailable_status, compoundable_status
) VALUES
(
    'NI_ACT_1881',
    'Negotiable Instruments Act, 1881',
    'Chapter XVII',
    '138',
    'Dishonour of cheque for insufficiency, etc., of funds in the account',
    'Where any cheque drawn by a person on an account maintained by him with a banker for payment of any amount of money to another person from out of that account for the discharge, in whole or in part, of any debt or other liability, is returned by the bank unpaid, either because of the amount of money standing to the credit of that account is insufficient to honour the cheque or that it exceeds the amount arranged to be paid from that account by an agreement made with that bank, such person shall be deemed to have committed an offence...',
    'If a person issues a cheque against a debt or legal liability and it bounces due to insufficient funds or account closure, it is a criminal offence. The complainant must send a formal legal demand notice within 30 days of receiving the bank return memo giving 15 days to pay.',
    'Notice within 30 days of bounce; 15 days to pay; Complaint in court within 30 days thereafter',
    'Imprisonment up to 2 years, or fine up to twice the cheque amount, or both',
    'Bailable',
    'Compoundable'
),
(
    'NI_ACT_1881',
    'Negotiable Instruments Act, 1881',
    'Chapter XVII',
    '142',
    'Cognizance of offences',
    'Notwithstanding anything contained in the Code of Criminal Procedure, 1973, no court shall take cognizance of any offence punishable under section 138 except upon a complaint, in writing, made by the payee or, as the case may be, the holder in due course of the cheque. Such complaint must be made within one month of the date on which the cause of action arises under clause (c) of the proviso to section 138.',
    'Sets the strict territorial jurisdiction (where the branch of the payee bank is situated) and the 1-month limitation period to file the complaint before the Judicial Magistrate after the 15-day statutory notice expires.',
    '1 month from expiry of 15 days of notice delivery',
    'Procedural jurisdiction rule',
    'N/A',
    'N/A'
),
(
    'CPA_2019',
    'Consumer Protection Act, 2019',
    'Chapter IV',
    '35',
    'Manner in which complaint shall be made to District Commission',
    'A complaint, in relation to any goods sold or delivered or agreed to be sold or delivered or any service provided or agreed to be provided, may be filed with a District Commission by the consumer, or any recognized consumer association, or the Central Authority...',
    'A consumer who receives defective goods, deficient service, or false advertising can file a consumer complaint before the District Consumer Commission online through e-Daakhil or in person where they reside or work.',
    '2 years from the date on which the cause of action arose',
    'Refund with interest, replacement of goods, compensation for mental agony, punitive damages',
    'Civil / Quasi-Judicial',
    'Compoundable via mediation'
),
(
    'RERA_2016',
    'Real Estate (Regulation and Development) Act, 2016',
    'Chapter III',
    '18',
    'Return of amount and compensation for delayed possession',
    'If the promoter fails to complete or is unable to give possession of an apartment, plot or building in accordance with the terms of the agreement for sale or duly completed by the date specified therein, he shall be liable on demand to the allottees to return the amount received by him with interest...',
    'If a builder/promoter delays possession of an apartment or commercial unit beyond the agreement date, the homebuyer has the right to withdraw and demand full refund with prescribed state RERA interest (MCLR + 2%), or stay in the project and claim monthly interest for every month of delay.',
    'Can be filed anytime during the ongoing delay before State RERA Authority',
    'Refund of principal + prescribed interest + compensation for delay',
    'Civil / Regulatory',
    'Settlement allowed'
),
(
    'BNS_2023',
    'Bharatiya Nyaya Sanhita, 2023',
    'Chapter XVIII',
    '318',
    'Cheating',
    'Whoever, by deceiving any person, fraudulently or dishonestly induces the person so deceived to deliver any property to any person, or to consent that any person shall retain any property... commits cheating. (Replaces Section 415 & 420 of Indian Penal Code)',
    'Covers fraud, fake online schemes, and dishonest inducement to transfer money or property. Sub-section (4) covers cheating with dishonest inducement to deliver property.',
    '3 years from commission or discovery of fraud',
    'Imprisonment up to 7 years and fine (under Section 318(4))',
    'Non-bailable (for serious fraud over statutory limits)',
    'Compoundable with permission of court'
),
(
    'RTI_2005',
    'Right to Information Act, 2005',
    'Chapter II',
    '6',
    'Request for obtaining information',
    'A person, who desires to obtain any information under this Act, shall make a request in writing or through electronic means in English or Hindi or in the official language of the area in which the application is being made, accompanying such fee as may be prescribed, to the Central Public Information Officer or State Public Information Officer...',
    'Allows any citizen of India to request government records, inspection of works, copies of files, or tender details from any public authority for a nominal fee of Rs. 10.',
    'Response must be given within 30 days (48 hours if life and liberty is concerned)',
    'Penalty of Rs. 250 per day up to Rs. 25,000 on defaulting PIO',
    'Administrative',
    'N/A'
)
ON CONFLICT DO NOTHING;

-- Seed Sample Verified Advocates for Immediate Demo
INSERT INTO public.profiles (id, email, phone_number, full_name, role, language_pref)
VALUES 
    ('d1111111-1111-1111-1111-111111111111', 'adv.sharma@onlinevakeel.com', '+919811122233', 'Adv. Rajesh Sharma', 'advocate', 'hi'),
    ('d2222222-2222-2222-2222-222222222222', 'adv.iyer@onlinevakeel.com', '+919844455566', 'Adv. Priya Iyer', 'advocate', 'en'),
    ('d3333333-3333-3333-3333-333333333333', 'adv.patel@onlinevakeel.com', '+919877788899', 'Adv. Amit Patel', 'advocate', 'en')
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.advocate_profiles (
    id, bar_council_id, bar_council_state, practice_areas, courts, city, state, 
    experience_years, languages_spoken, bio, hourly_consult_fee, rating, reviews_count, is_verified, is_available
) VALUES
(
    'd1111111-1111-1111-1111-111111111111',
    'D/1420/2012',
    'Bar Council of Delhi',
    '{"cheque_bounce", "criminal_bail", "cyber_fraud"}',
    '{"Tis Hazari Court", "Saket District Court", "Delhi High Court"}',
    'New Delhi',
    'Delhi',
    14,
    '{"en", "hi", "pa"}',
    'Senior trial advocate specializing in NI Act 138 cheque bounce proceedings, white-collar financial disputes, and bail representations across Delhi NCR.',
    1500,
    4.9,
    142,
    TRUE,
    TRUE
),
(
    'd2222222-2222-2222-2222-222222222222',
    'KAR/982/2016',
    'Karnataka State Bar Council',
    '{"property_rera", "consumer_dispute", "employment_labour"}',
    '{"City Civil Court Bengaluru", "Karnataka RERA", "High Court of Karnataka"}',
    'Bengaluru',
    'Karnataka',
    10,
    '{"en", "hi", "kn", "ta"}',
    'Specialist in RERA builder disputes, delayed possession claims, consumer protection commissions, and tech employment contracts.',
    1200,
    4.8,
    98,
    TRUE,
    TRUE
),
(
    'd3333333-3333-3333-3333-333333333333',
    'MAH/2311/2015',
    'Bar Council of Maharashtra & Goa',
    '{"consumer_dispute", "cheque_bounce", "general_civil"}',
    '{"Bombay High Court", "City Civil & Sessions Court Mumbai", "State Consumer Forum"}',
    'Mumbai',
    'Maharashtra',
    11,
    '{"en", "hi", "mr", "gu"}',
    'Advocate handling commercial contracts, consumer defect litigation against major brands, and recovery notices under Indian commercial statutes.',
    1800,
    4.9,
    116,
    TRUE,
    TRUE
)
ON CONFLICT (id) DO NOTHING;
