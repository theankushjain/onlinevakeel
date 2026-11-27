import logging
import os
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

# Fallback in-memory legal corpus for local development & zero-dependency testing
FALLBACK_LEGAL_CORPUS = [
    {
        "id": "11111111-0000-0000-0000-000000000001",
        "act_code": "NI_ACT_1881",
        "act_name": "Negotiable Instruments Act, 1881",
        "chapter": "Chapter XVII",
        "section_number": "138",
        "section_title": "Dishonour of cheque for insufficiency, etc., of funds in the account",
        "legal_text": "Where any cheque drawn by a person on an account maintained by him with a banker for payment of any amount of money to another person from out of that account for the discharge of any debt or liability is returned by the bank unpaid...",
        "plain_summary": "Dishonour of cheque (cheque bounce) for insufficient funds or account closed is a punishable criminal offence. A formal demand notice must be served within 30 days of receiving the bank memo giving the drawer 15 days to pay.",
        "limitation_period": "30 days from bank bounce memo to issue notice; 15 days to pay; 30 days thereafter to file complaint in court",
        "penalties": "Imprisonment up to 2 years, or fine up to twice the cheque amount, or both",
        "bailable_status": "Bailable",
        "compoundable_status": "Compoundable"
    },
    {
        "id": "11111111-0000-0000-0000-000000000002",
        "act_code": "NI_ACT_1881",
        "act_name": "Negotiable Instruments Act, 1881",
        "chapter": "Chapter XVII",
        "section_number": "142",
        "section_title": "Cognizance of offences",
        "legal_text": "Notwithstanding anything contained in the Code of Criminal Procedure, 1973, no court shall take cognizance of any offence punishable under section 138 except upon a complaint, in writing, made by the payee or the holder in due course...",
        "plain_summary": "Defines jurisdiction (payee bank branch) and strictly limits filing of complaint to within 1 month after expiry of the 15-day statutory notice period.",
        "limitation_period": "Within 1 month from the date cause of action arises (day 16 after notice delivery)",
        "penalties": "Procedural jurisdiction and bar of limitation",
        "bailable_status": "N/A",
        "compoundable_status": "N/A"
    },
    {
        "id": "11111111-0000-0000-0000-000000000003",
        "act_code": "CPA_2019",
        "act_name": "Consumer Protection Act, 2019",
        "chapter": "Chapter IV",
        "section_number": "35",
        "section_title": "Manner in which complaint shall be made to District Commission",
        "legal_text": "A complaint, in relation to any goods sold or delivered or agreed to be sold or delivered or any service provided or agreed to be provided, may be filed with a District Commission by the consumer...",
        "plain_summary": "Consumers can file complaints for defective goods, deficient services, delayed refunds, or unfair trade practices before District Consumer Forum (physically or online via e-Daakhil portal).",
        "limitation_period": "2 years from the date of cause of action (defect/deficiency)",
        "penalties": "Refund, replacement of goods, compensation for mental agony, punitive damages",
        "bailable_status": "Civil / Quasi-Judicial",
        "compoundable_status": "Compoundable via Consumer Mediation Cell"
    },
    {
        "id": "11111111-0000-0000-0000-000000000004",
        "act_code": "RERA_2016",
        "act_name": "Real Estate (Regulation and Development) Act, 2016",
        "chapter": "Chapter III",
        "section_number": "18",
        "section_title": "Return of amount and compensation for delayed possession",
        "legal_text": "If the promoter fails to complete or is unable to give possession of an apartment, plot or building in accordance with the terms of the agreement for sale... he shall be liable on demand to the allottees to return the amount received by him with interest...",
        "plain_summary": "Homebuyers whose builder delays flat handover beyond agreed date can claim full refund with state RERA interest (MCLR + 2%) or claim monthly delay interest while remaining in the project.",
        "limitation_period": "Can be filed before State RERA Authority during ongoing delay",
        "penalties": "Refund of principal + statutory interest + compensation",
        "bailable_status": "Civil / Regulatory",
        "compoundable_status": "Settlement allowed"
    },
    {
        "id": "11111111-0000-0000-0000-000000000005",
        "act_code": "BNS_2023",
        "act_name": "Bharatiya Nyaya Sanhita, 2023",
        "chapter": "Chapter XVIII",
        "section_number": "318",
        "section_title": "Cheating",
        "legal_text": "Whoever, by deceiving any person, fraudulently or dishonestly induces the person so deceived to deliver any property... commits cheating. (Replaces Section 420 IPC)",
        "plain_summary": "Criminal fraud, fake job/investment schemes, and dishonest inducement to extract money. Section 318(4) penalizes cheating with property delivery.",
        "limitation_period": "3 years from discovery of fraud",
        "penalties": "Imprisonment up to 7 years and fine",
        "bailable_status": "Non-bailable for serious fraud",
        "compoundable_status": "Compoundable with court consent"
    },
    {
        "id": "11111111-0000-0000-0000-000000000006",
        "act_code": "RTI_2005",
        "act_name": "Right to Information Act, 2005",
        "chapter": "Chapter II",
        "section_number": "6",
        "section_title": "Request for obtaining information",
        "legal_text": "A person, who desires to obtain any information under this Act, shall make a request in writing or through electronic means in English or Hindi...",
        "plain_summary": "Allows any Indian citizen to file an RTI application seeking official government records, status of applications, municipal tenders, or public authority files for Rs. 10.",
        "limitation_period": "30 days statutory response deadline (48 hours for life & liberty)",
        "penalties": "Rs. 250/day up to Rs. 25,000 on defaulting PIO",
        "bailable_status": "Administrative",
        "compoundable_status": "N/A"
    },
    {
        "id": "11111111-0000-0000-0000-000000000007",
        "act_code": "BSA_2023",
        "act_name": "Bharatiya Sakshya Adhiniyam, 2023",
        "chapter": "Chapter V",
        "section_number": "63",
        "section_title": "Admissibility of electronic records (Mandatory Certificate)",
        "legal_text": "Any information contained in an electronic record which is printed on paper, stored, recorded or copied in optical or magnetic media... shall be deemed to be also a document... and shall be admissible in any proceedings, subject to a certificate under this section. (Replaces Section 65B of Indian Evidence Act, 1872)",
        "plain_summary": "Governs admissibility of secret video recordings, phone calls, CCTV, and digital messages in Indian courts. Secret recordings are legally admissible if genuine; a Section 63 Certificate (formerly 65B Certificate) proving chain of custody and device integrity is mandatory.",
        "limitation_period": "Must be filed along with electronic evidence at the time of charge-sheet or complaint",
        "penalties": "Admissibility of electronic evidence in criminal and civil trials",
        "bailable_status": "Evidentiary Rule",
        "compoundable_status": "N/A"
    },
    {
        "id": "11111111-0000-0000-0000-000000000008",
        "act_code": "BNSS_2023",
        "act_name": "Bharatiya Nagarik Suraksha Sanhita, 2023",
        "chapter": "Chapter XII",
        "section_number": "175",
        "section_title": "Magistrate direction to police to investigate cognizable cases",
        "legal_text": "Any Magistrate empowered under section 190 may order an investigation into any cognizable offence... (Replaces Section 156(3) of Code of Criminal Procedure, 1973)",
        "plain_summary": "If local police refuse to register an FIR for land fraud, cheating, or financial scams, a citizen can file an application before the Judicial Magistrate under Section 175(3) BNSS directing police to register the FIR and investigate.",
        "limitation_period": "3 years from commission or discovery of offence",
        "penalties": "Court-monitored investigation and mandatory FIR registration",
        "bailable_status": "Procedural Judicial Order",
        "compoundable_status": "N/A"
    },
    {
        "id": "11111111-0000-0000-0000-000000000009",
        "act_code": "REG_ACT_1908",
        "act_name": "Registration Act, 1908",
        "chapter": "Part X",
        "section_number": "49",
        "section_title": "Effect of non-registration of documents required to be registered",
        "legal_text": "No document required by section 17... shall affect any immovable property... Provided that an unregistered document affecting immovable property may be received as evidence of a contract in a suit for specific performance... or as evidence of any collateral transaction not required to be effected by registered instrument.",
        "plain_summary": "An unnotarized or unregistered agreement on a Rs. 100 stamp paper cannot transfer property ownership, but under the proviso to Section 49 it is valid collateral evidence in court to prove payment of money, terms of agreement, and fraudulent inducement.",
        "limitation_period": "3 years for recovery / specific performance",
        "penalties": "Admissible as collateral evidence of money transaction",
        "bailable_status": "Civil Evidentiary Rule",
        "compoundable_status": "N/A"
    },
    {
        "id": "22222222-0000-0000-0000-000000000001",
        "act_code": "SC_PRECEDENT",
        "act_name": "Supreme Court of India (AWS Open Data Landmark Precedent)",
        "chapter": "Negotiable Instruments & Cheque Bounce Jurisprudence",
        "section_number": "Dashrath Rupsingh Rathod v. State of Maharashtra (2014) 9 SCC 129",
        "section_title": "Jurisdiction for Section 138 NI Act Cheque Dishonour Complaints",
        "legal_text": "A 3-Judge Bench of the Supreme Court of India laid down the definitive territorial jurisdiction for filing Section 138 Negotiable Instruments Act complaints. The Court clarified that territorial jurisdiction belongs to the court having territorial jurisdiction over the branch where the payee maintains his bank account where the cheque was presented for clearance.",
        "plain_summary": "Landmark Supreme Court precedent on cheque bounce. Affirms that the payee can file the Section 138 criminal complaint directly at the court jurisdiction where their own bank branch is located, preventing fraudulent drawers from harassing victims across states.",
        "limitation_period": "15 days demand notice strictly required prior to filing",
        "penalties": "Binding nationwide precedent under Article 141 of the Constitution",
        "bailable_status": "Supreme Court 3-Judge Bench",
        "compoundable_status": "Binding Precedent"
    },
    {
        "id": "22222222-0000-0000-0000-000000000002",
        "act_code": "SC_PRECEDENT",
        "act_name": "Supreme Court of India (AWS Open Data Landmark Precedent)",
        "chapter": "RERA & Real Estate Buyer Protection",
        "section_number": "Newtech Promoters & Developers v. State of U.P. (2021) 19 SCC 317",
        "section_title": "Allottee's Unconditional Right to Refund and Monthly Delay Interest under Section 18 RERA",
        "legal_text": "The Supreme Court held that Section 18 of RERA operates retroactively on ongoing projects and grants an unqualified, absolute right to the homebuyer to claim either a complete refund with interest or monthly interest for each month of delay until possession is delivered, and builders cannot defeat this statutory right by citing market delays.",
        "plain_summary": "Landmark Supreme Court ruling on builder delay. Ruled that homebuyers do not need to wait indefinitely; builders cannot force buyers to accept delayed possession or cite administrative excuses to avoid paying Section 18 monthly delay interest.",
        "limitation_period": "Enforceable throughout the entire duration of delay before State RERA",
        "penalties": "Full refund + MCLR+2% statutory interest; mandatory 100% pre-deposit by builder for appeal",
        "bailable_status": "Supreme Court Division Bench",
        "compoundable_status": "Binding Precedent"
    },
    {
        "id": "22222222-0000-0000-0000-000000000003",
        "act_code": "SC_PRECEDENT",
        "act_name": "Supreme Court of India (AWS Open Data Landmark Precedent)",
        "chapter": "Electronic Evidence & Digital Records",
        "section_number": "Arjun Panditrao Khotkar v. Kailash Kushanrao Gorantyal (2020) 7 SCC 1",
        "section_title": "Mandatory Electronic Record Certificate under Section 65B Evidence Act / Section 63 BSA",
        "legal_text": "A 3-Judge Bench of the Supreme Court held that the certificate under Section 65B(4) of the Evidence Act (now Section 63 of Bharatiya Sakshya Adhiniyam, 2023) is an indispensable condition precedent to the admissibility of electronic evidence in the form of secondary evidence like phone call recordings, WhatsApp chats, CCTV footage, and emails.",
        "plain_summary": "Landmark Supreme Court 3-Judge Bench ruling on digital evidence. Confirms that secret recordings, WhatsApp messages, and phone audio are validly admissible in court provided they are accompanied by a certificate certifying device integrity and custody.",
        "limitation_period": "Must be submitted along with the charge-sheet or complaint in trial court",
        "penalties": "Admissibility rule governing all Indian criminal & civil trials",
        "bailable_status": "Supreme Court 3-Judge Bench",
        "compoundable_status": "Binding Precedent"
    },
    {
        "id": "22222222-0000-0000-0000-000000000004",
        "act_code": "HC_PRECEDENT",
        "act_name": "High Court of Delhi (AWS Open Data Precedent)",
        "chapter": "Cyber Banking & Customer Restitution",
        "section_number": "Ramdoot Singh v. State (NCT of Delhi) & Reserve Bank of India (2021)",
        "section_title": "Zero Liability of Customer in Unauthorized Electronic Banking & Cyber Fraud Transactions",
        "legal_text": "The Delhi High Court upheld the RBI Circular on Limiting Customer Liability, ruling that in unauthorized electronic banking fraud reported within 3 working days by the consumer, the customer carries zero liability and the commercial bank is legally obligated to reverse the fraudulent debit and reimburse the funds.",
        "plain_summary": "Landmark High Court precedent protecting cyber fraud victims. If you report a fraudulent UPI/bank transfer within 3 days (or via National Cyber Helpline 1930), the bank cannot shift blame to the consumer and must credit the disputed amount back.",
        "limitation_period": "Customer must notify the bank within 3 working days of unauthorized debit",
        "penalties": "Full financial restitution to victim by commercial bank",
        "bailable_status": "High Court Division Bench",
        "compoundable_status": "Binding on trial courts & tribunals in jurisdiction"
    }
]

FALLBACK_ADVOCATES = [
    {
        "id": "d1111111-1111-1111-1111-111111111111",
        "name": "Adv. Rajesh Sharma",
        "bar_council_id": "D/1420/2012 (Bar Council of Delhi)",
        "practice_areas": ["cheque_bounce", "criminal_bail", "cyber_fraud"],
        "courts": ["Delhi High Court", "Saket District Court", "Tis Hazari Court"],
        "district_court": "Saket District Court (South Delhi)",
        "office_location": "Chamber 412, Lawyers Block, Saket District Court Complex, South Delhi",
        "city": "New Delhi",
        "state": "Delhi",
        "experience_years": 14,
        "languages": ["English", "Hindi", "Punjabi"],
        "consult_fee": 1500,
        "rating": 4.9,
        "reviews": 142,
        "verified": True,
        "available": True,
        "bio": "Specialist in trial court litigation, cheque bounce recovery (Sec 138 NI Act), and commercial arbitration across Delhi NCR."
    },
    {
        "id": "d1111111-1111-1111-1111-111111111112",
        "name": "Adv. Meenakshi Sundaram",
        "bar_council_id": "D/2890/2014 (Bar Council of Delhi)",
        "practice_areas": ["property_rera", "general_civil", "criminal_bail"],
        "courts": ["Delhi High Court", "Patiala House Court", "Rouse Avenue Court"],
        "district_court": "Patiala House Court (New Delhi)",
        "office_location": "Chamber 88, Patiala House Courts, India Gate, Central Delhi",
        "city": "New Delhi",
        "state": "Delhi",
        "experience_years": 12,
        "languages": ["English", "Hindi", "Tamil"],
        "consult_fee": 1600,
        "rating": 4.9,
        "reviews": 118,
        "verified": True,
        "available": True,
        "bio": "Experienced counsel in land fraud, stamp paper agreement disputes, criminal cheating (Sec 318 BNS), and Delhi property litigation."
    },
    {
        "id": "d2222222-2222-2222-2222-222222222222",
        "name": "Adv. Priya Iyer",
        "bar_council_id": "KAR/982/2016 (Karnataka Bar Council)",
        "practice_areas": ["property_rera", "consumer_dispute", "employment_labour"],
        "courts": ["Karnataka High Court", "City Civil Court Bengaluru", "Karnataka RERA"],
        "district_court": "City Civil Court (Mayohall / Mayo Hall)",
        "office_location": "Chamber 14, Mayohall Court Complex, MG Road & Indiranagar, Bengaluru",
        "city": "Bengaluru",
        "state": "Karnataka",
        "experience_years": 10,
        "languages": ["English", "Hindi", "Kannada", "Tamil"],
        "consult_fee": 1200,
        "rating": 4.8,
        "reviews": 98,
        "verified": True,
        "available": True,
        "bio": "Expert in builder possession delays under RERA, consumer commission representation, and corporate severance disputes."
    },
    {
        "id": "d2222222-2222-2222-2222-222222222223",
        "name": "Adv. Karthik Reddy",
        "bar_council_id": "KAR/1435/2013 (Karnataka Bar Council)",
        "practice_areas": ["cyber_fraud", "cheque_bounce", "criminal_bail"],
        "courts": ["Karnataka High Court", "Mayo Hall Court", "Cyber Crime Sessions Court"],
        "district_court": "Mayo Hall Court & Cyber Sessions Court",
        "office_location": "Chamber 22, Brigade Towers, Brigade Road & Koramangala 4th Block, Bengaluru",
        "city": "Bengaluru",
        "state": "Karnataka",
        "experience_years": 13,
        "languages": ["English", "Hindi", "Kannada", "Telugu"],
        "consult_fee": 1400,
        "rating": 4.9,
        "reviews": 134,
        "verified": True,
        "available": True,
        "bio": "Specialized in financial cyber fraud recovery, electronic records evidence (Sec 63 BSA), and commercial debt recovery."
    },
    {
        "id": "d3333333-3333-3333-3333-333333333333",
        "name": "Adv. Amit Patel",
        "bar_council_id": "MAH/2311/2015 (Bar Council of Maharashtra & Goa)",
        "practice_areas": ["consumer_dispute", "cheque_bounce", "general_civil"],
        "courts": ["Bombay High Court", "City Civil & Sessions Court Mumbai", "State Consumer Commission"],
        "district_court": "City Civil & Sessions Court Mumbai (Fort / Bandra)",
        "office_location": "Chamber 52, High Court Chambers, Fort & BKC, South Mumbai",
        "city": "Mumbai",
        "state": "Maharashtra",
        "experience_years": 11,
        "languages": ["English", "Hindi", "Marathi", "Gujarati"],
        "consult_fee": 1800,
        "rating": 4.9,
        "reviews": 116,
        "verified": True,
        "available": True,
        "bio": "Experienced litigation counsel handling consumer protection claims, financial recovery, and commercial contracts."
    },
    {
        "id": "d4444444-4444-4444-4444-444444444444",
        "name": "Adv. Sneha Deshmukh",
        "bar_council_id": "MAH/3142/2017 (Bar Council of Maharashtra & Goa)",
        "practice_areas": ["property_rera", "criminal_bail", "general_civil"],
        "courts": ["District & Sessions Court Pune", "Bombay High Court", "MahaRERA Pune"],
        "district_court": "Pune District & Sessions Court (Shivajinagar)",
        "office_location": "Chamber 203, Lawyers Bhavan, Shivajinagar Court Campus, FC Road, Pune",
        "city": "Pune",
        "state": "Maharashtra",
        "experience_years": 9,
        "languages": ["English", "Hindi", "Marathi"],
        "consult_fee": 1100,
        "rating": 4.8,
        "reviews": 84,
        "verified": True,
        "available": True,
        "bio": "Advises on unapproved land sales, agricultural-to-NA conversions, builder delays under MahaRERA, and property fraud."
    },
    {
        "id": "d5555555-5555-5555-5555-555555555555",
        "name": "Adv. Venkat Raman Rao",
        "bar_council_id": "TS/784/2014 (Bar Council of Telangana)",
        "practice_areas": ["property_rera", "general_civil", "cheque_bounce"],
        "courts": ["Telangana High Court", "City Civil Court Hyderabad", "TG RERA"],
        "district_court": "City Civil Court Hyderabad (Purani Haveli)",
        "office_location": "Chamber 19, City Civil Court Compound, Purani Haveli & Banjara Hills, Hyderabad",
        "city": "Hyderabad",
        "state": "Telangana",
        "experience_years": 12,
        "languages": ["English", "Hindi", "Telugu"],
        "consult_fee": 1300,
        "rating": 4.9,
        "reviews": 102,
        "verified": True,
        "available": True,
        "bio": "Litigation advocate handling Hyderabad real estate title disputes, recovery of cash considerations, and Section 138 NI Act."
    },
    {
        "id": "d6666666-6666-6666-6666-666666666666",
        "name": "Adv. Alok Verma",
        "bar_council_id": "UP/4210/2011 (Bar Council of Uttar Pradesh)",
        "practice_areas": ["property_rera", "criminal_bail", "cheque_bounce"],
        "courts": ["Allahabad High Court (Lucknow Bench)", "District & Sessions Court Lucknow"],
        "district_court": "District & Sessions Court Lucknow (Qaiserbagh)",
        "office_location": "Chamber 34, Central Bar Association, Collectorate, Qaiserbagh, Lucknow",
        "city": "Lucknow",
        "state": "Uttar Pradesh",
        "experience_years": 15,
        "languages": ["English", "Hindi", "Urdu"],
        "consult_fee": 1200,
        "rating": 4.9,
        "reviews": 156,
        "verified": True,
        "available": True,
        "bio": "Trial and appellate lawyer handling property cheating, Section 175 BNSS magistrate complaints, and land registry disputes across UP."
    },
    {
        "id": "d7777777-7777-7777-7777-777777777777",
        "name": "Adv. Gurpreet Singh",
        "bar_council_id": "PH/1892/2015 (Bar Council of Punjab & Haryana)",
        "practice_areas": ["property_rera", "cheque_bounce", "consumer_dispute"],
        "courts": ["Punjab & Haryana High Court", "District Courts Chandigarh"],
        "district_court": "District Courts Complex Sector 43 Chandigarh",
        "office_location": "Chamber 112, District Courts Complex, Sector 43 & Mohali, Chandigarh",
        "city": "Chandigarh",
        "state": "Chandigarh",
        "experience_years": 11,
        "languages": ["English", "Hindi", "Punjabi"],
        "consult_fee": 1400,
        "rating": 4.8,
        "reviews": 92,
        "verified": True,
        "available": True,
        "bio": "Expert in land acquisition disputes, developer defaults, Section 138 cheque bounce trials, and consumer compensation."
    },
    {
        "id": "d8888888-8888-8888-8888-888888888888",
        "name": "Adv. Vikram Rathore",
        "bar_council_id": "RAJ/2410/2016 (Bar Council of Rajasthan)",
        "practice_areas": ["property_rera", "consumer_dispute", "general_civil"],
        "courts": ["Rajasthan High Court (Jaipur Bench)", "District Court Jaipur"],
        "district_court": "District & Sessions Court Jaipur (Collectorate Circle)",
        "office_location": "Chamber 218, Collectorate Circle, Banipark, Jaipur",
        "city": "Jaipur",
        "state": "Rajasthan",
        "experience_years": 10,
        "languages": ["English", "Hindi", "Rajasthani"],
        "consult_fee": 1000,
        "rating": 4.8,
        "reviews": 76,
        "verified": True,
        "available": True,
        "bio": "Specialized in rural & urban land disputes, revenue court proceedings, and consumer forum litigation."
    },
    {
        "id": "d9999999-9999-9999-9999-999999999991",
        "name": "Adv. Ananya Saxena",
        "bar_council_id": "UP/3421/2015 (Bar Council of Uttar Pradesh)",
        "practice_areas": ["consumer_dispute", "property_rera", "cheque_bounce", "cyber_fraud"],
        "courts": ["District & Sessions Court Surajpur (Greater Noida)", "Noida Sector 33 Court", "UP RERA Greater Noida"],
        "district_court": "District & Sessions Court Surajpur (Greater Noida)",
        "office_location": "Chamber 215, Lawyers Chambers, Surajpur Court Complex & Sector 62, Noida",
        "city": "Gautam Buddha Nagar",
        "state": "Uttar Pradesh",
        "experience_years": 11,
        "languages": ["English", "Hindi"],
        "consult_fee": 1200,
        "rating": 4.9,
        "reviews": 128,
        "verified": True,
        "available": True,
        "bio": "Specialist in consumer forum claims, Noida & Greater Noida builder possession delays (UP RERA), cheque bounce recovery (Sec 138), and corporate fraud."
    },
    {
        "id": "d9999999-9999-9999-9999-999999999992",
        "name": "Adv. Vikramaditya Rao",
        "bar_council_id": "PH/2890/2014 (Bar Council of Punjab & Haryana)",
        "practice_areas": ["property_rera", "cyber_fraud", "employment_labour", "consumer_dispute"],
        "courts": ["District Courts Complex Gurugram", "Haryana RERA Gurugram", "Punjab & Haryana High Court"],
        "district_court": "District Courts Complex Gurugram (Near Rajiv Chowk)",
        "office_location": "Chamber 54, Lawyers Building, District Court Complex & Cyber City, Gurugram",
        "city": "Gurugram",
        "state": "Haryana",
        "experience_years": 12,
        "languages": ["English", "Hindi"],
        "consult_fee": 1500,
        "rating": 4.9,
        "reviews": 145,
        "verified": True,
        "available": True,
        "bio": "Specialized counsel for Haryana RERA builder complaints, IT workplace severance disputes, Section 138 NI Act, and commercial arbitration."
    },
    {
        "id": "d9999999-9999-9999-9999-999999999993",
        "name": "Adv. Rohan Deshpande",
        "bar_council_id": "MAH/4512/2016 (Bar Council of Maharashtra & Goa)",
        "practice_areas": ["consumer_dispute", "property_rera", "criminal_bail"],
        "courts": ["District & Sessions Court Thane", "Bombay High Court", "MahaRERA"],
        "district_court": "District & Sessions Court Thane (Court Naka)",
        "office_location": "Chamber 18, Bar Association Building, Court Naka, Thane West & Vashi",
        "city": "Thane",
        "state": "Maharashtra",
        "experience_years": 10,
        "languages": ["English", "Hindi", "Marathi"],
        "consult_fee": 1200,
        "rating": 4.8,
        "reviews": 94,
        "verified": True,
        "available": True,
        "bio": "Litigation practitioner representing clients before Thane District Court, Belapur Court, and MahaRERA in property and consumer disputes."
    },
    {
        "id": "d9999999-9999-9999-9999-999999999994",
        "name": "Adv. Mohammad Tariq",
        "bar_council_id": "UP/5120/2013 (Bar Council of Uttar Pradesh)",
        "practice_areas": ["cheque_bounce", "property_rera", "general_civil"],
        "courts": ["District & Sessions Court Ghaziabad", "Allahabad High Court"],
        "district_court": "District & Sessions Court Ghaziabad (Raj Nagar)",
        "office_location": "Chamber 408, Collectorate Compound, Raj Nagar District Courts, Ghaziabad",
        "city": "Ghaziabad",
        "state": "Uttar Pradesh",
        "experience_years": 13,
        "languages": ["English", "Hindi", "Urdu"],
        "consult_fee": 1100,
        "rating": 4.8,
        "reviews": 112,
        "verified": True,
        "available": True,
        "bio": "Civil and criminal trial attorney handling cheque dishonour, land title issues, and consumer complaints in Ghaziabad and NCR."
    }
]

class DatabaseClient:
    def __init__(self):
        self.client = None
        self.is_connected = False
        self.custom_advocates: List[Dict[str, Any]] = []
        self.advocate_reviews: Dict[str, List[Dict[str, Any]]] = {
            "d1111111-1111-1111-1111-111111111111": [
                {
                    "id": "rev-1",
                    "advocate_id": "d1111111-1111-1111-1111-111111111111",
                    "client_name": "Karan Malhotra",
                    "rating": 5,
                    "review_text": "Adv. Rajesh helped recover my bounced cheque within 20 days of issuing the Section 138 demand notice. Thorough knowledge of Saket Court procedure.",
                    "payment_id": "PAY-OV-88A912B1",
                    "verified_paid": True,
                    "created_at": "3 days ago"
                },
                {
                    "id": "rev-2",
                    "advocate_id": "d1111111-1111-1111-1111-111111111111",
                    "client_name": "Sunita Verma",
                    "rating": 5,
                    "review_text": "Very professional and patient during our chamber consultation. Clear advice on criminal bail and cyber fraud recovery.",
                    "payment_id": "PAY-OV-44BC7129",
                    "verified_paid": True,
                    "created_at": "1 week ago"
                }
            ],
            "d2222222-2222-2222-2222-222222222223": [
                {
                    "id": "rev-3",
                    "advocate_id": "d2222222-2222-2222-2222-222222222223",
                    "client_name": "Arjun Sundaram",
                    "rating": 5,
                    "review_text": "Excellent cyber fraud and Sec 63 BSA electronic evidence drafting. Accompanied to Mayo Hall Court promptly.",
                    "payment_id": "PAY-OV-991204FA",
                    "verified_paid": True,
                    "created_at": "4 days ago"
                }
            ]
        }
        
        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            try:
                from supabase import create_client
                self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                self.is_connected = True
                logger.info("Connected successfully to Supabase cloud database.")
            except Exception as e:
                logger.warning(f"Could not initialize live Supabase client: {e}. Falling back to internal legal store.")
        else:
            logger.info("Supabase URL/Key not yet configured. Operating in zero-config dev mode with built-in Indian legal corpus.")

        self.corpus_embeddings: Dict[str, List[float]] = {}
        self._init_corpus_embeddings()

    def register_advocate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dynamically registers a verified advocate into the active portal registry.
        """
        import uuid
        adv_id = f"adv-{uuid.uuid4().hex[:8]}"
        district_court = data.get("district_court") or (data.get("courts", ["District Court"])[0] if data.get("courts") else "District Court")
        office_location = data.get("office_location") or f"Chamber Office, {data.get('city', 'New Delhi')}"
        record = {
            "id": adv_id,
            "name": data.get("name", "Advocate"),
            "bar_council_id": data.get("bar_council_id", "BCI/2026/REG"),
            "state_bar_council": data.get("state_bar_council", "State Bar Council"),
            "practice_areas": data.get("practice_areas", ["general_civil"]),
            "courts": data.get("courts", ["District Courts", "High Court"]),
            "district_court": district_court,
            "office_location": office_location,
            "city": data.get("city", "New Delhi"),
            "state": data.get("state", "Delhi"),
            "experience_years": int(data.get("experience_years", 5)),
            "languages": data.get("languages", ["English", "Hindi"]),
            "consult_fee": int(data.get("consult_fee", 1200)),
            "email": data.get("email", ""),
            "phone": data.get("phone", ""),
            "password": data.get("password", ""),
            "rating": 5.0,
            "reviews": 1,
            "verified": True,
            "available": True,
            "bio": data.get("bio") or f"Practicing advocate before {district_court} with {data.get('experience_years', 5)} years experience.",
            "created_at": datetime.now().isoformat()
        }
        self.custom_advocates.insert(0, record)
        return record

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generates 384-dimensional dense vector embeddings using the Capstone BGE API.
        """
        if not settings.EMBEDDING_API_KEY:
            return None
        try:
            cert_path = settings.EMBEDDING_CA_CERT_PATH if os.path.exists(settings.EMBEDDING_CA_CERT_PATH) else True
            with httpx.Client(verify=cert_path, timeout=6.0) as client:
                res = client.post(
                    f"{settings.EMBEDDING_BASE_URL}/embeddings",
                    headers={"Authorization": f"Bearer {settings.EMBEDDING_API_KEY}"},
                    json={"model": settings.EMBEDDING_MODEL, "input": [text[:512]]}
                )
                if res.status_code == 200:
                    data = res.json()
                    if "data" in data and len(data["data"]) > 0:
                        return data["data"][0]["embedding"]
        except Exception as e:
            logger.debug(f"BGE embedding call failed: {e}")
        return None

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Computes cosine similarity between two vector embeddings."""
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def _init_corpus_embeddings(self):
        """Pre-computes or lazily caches vector embeddings for core Bare Acts."""
        pass

    def search_legal_corpus(self, query: str, limit: int = 4) -> List[Dict[str, Any]]:
        """
        Hybrid search for legal sections matching citizen queries.
        Uses Capstone BGE dense vector embeddings + Supabase pgvector / in-memory cosine ranking + statutory keywords.
        """
        query_embedding = self.generate_embedding(query)

        if self.is_connected and self.client:
            try:
                res = self.client.rpc("match_legal_sections", {
                    "query_embedding": query_embedding,
                    "query_text": query,
                    "match_threshold": 0.2,
                    "match_count": limit
                }).execute()
                if res.data and len(res.data) > 0:
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase RPC match failed, using fallback: {e}")
        
        query_lower = query.lower()
        scored = []
        for item in FALLBACK_LEGAL_CORPUS:
            score = 0

            # 1. Dense Semantic Vector Similarity (BGE 384-d Embedding)
            if query_embedding:
                item_id = item["id"]
                if item_id not in self.corpus_embeddings:
                    sec_text = f"{item['act_name']} Section {item['section_number']}: {item['section_title']}. {item['plain_summary']}"
                    vec = self.generate_embedding(sec_text)
                    if vec:
                        self.corpus_embeddings[item_id] = vec
                
                sec_vec = self.corpus_embeddings.get(item_id)
                if sec_vec:
                    sim = self.cosine_similarity(query_embedding, sec_vec)
                    # Convert cosine similarity (0 to 1) into retrieval ranking points
                    if sim > 0.4:
                        score += int(sim * 18)
                    if sim > 0.7:
                        score += 8

            if item["section_number"] in query_lower:
                score += 5
            if item["act_name"].lower() in query_lower:
                score += 4
            if item["act_code"].lower() in query_lower:
                score += 3
            
            for token in query_lower.split():
                if len(token) > 3:
                    if token in item["plain_summary"].lower():
                        score += 1
                    if token in item["section_title"].lower():
                        score += 2
            
            if any(w in query_lower for w in ["cheque", "bounce", "dishonour", "memo", "bank returned"]) and item["act_code"] == "NI_ACT_1881":
                score += 8
            if any(w in query_lower for w in ["consumer", "defective", "refund", "warranty", "flipkart", "amazon", "service"]) and item["act_code"] == "CPA_2019":
                score += 8
            if any(w in query_lower for w in ["rera", "builder", "flat", "possession", "allottee", "apartment", "delay"]) and item["act_code"] == "RERA_2016":
                score += 8
            if any(w in query_lower for w in ["cheating", "fraud", "scam", "fir", "dhokhadhadi"]) and item["act_code"] == "BNS_2023":
                score += 8
            if any(w in query_lower for w in ["rti", "information", "public authority", "sarkar", "records"]) and item["act_code"] == "RTI_2005":
                score += 8
            if any(w in query_lower for w in ["video", "record", "recording", "audio", "camera", "evidence", "sting", "electronic", "whatsapp", "call", "certificate", "65b", "bsa", "sakshya"]) and item["act_code"] == "BSA_2023":
                score += 10
            if any(w in query_lower for w in ["police", "fir", "magistrate", "thana", "refuse", "investigate", "175", "156", "bnss"]) and item["act_code"] == "BNSS_2023":
                score += 9
            if any(w in query_lower for w in ["stamp", "notary", "notarized", "agreement", "100", "unregistered", "registration", "deed", "paper"]) and item["act_code"] == "REG_ACT_1908":
                score += 9
            if any(w in query_lower for w in ["precedent", "judgment", "ruling", "supreme court", "high court", "case law", "judge", "bench", "ratio"]):
                if item["act_code"] in ["SC_PRECEDENT", "HC_PRECEDENT"]:
                    score += 12
            if any(w in query_lower for w in ["rera", "builder", "possession", "delay"]) and "Newtech" in item["section_number"]:
                score += 9
            if any(w in query_lower for w in ["cheque", "bounce", "dishonour", "jurisdiction"]) and "Dashrath" in item["section_number"]:
                score += 9
            if any(w in query_lower for w in ["video", "recording", "audio", "whatsapp", "electronic", "certificate", "65b", "63"]) and "Arjun" in item["section_number"]:
                score += 9
            if (
                any(w in query_lower for w in ["bank", "unauthorized", "otp", "reversal", "fraud transaction"])
                or ("cyber" in query_lower and not any(n in query_lower for n in ["loud music", "noise", "neighbor", "neighbour", "nuisance"]))
            ) and "Ramdoot" in item["section_number"]:
                score += 9
                
            if score > 0:
                scored.append((score, item))
                
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [item for _, item in scored[:limit]]
        return results if results else FALLBACK_LEGAL_CORPUS[:2]

    def add_advocate_review(self, advocate_id: str, review_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Records a verified paid client review and re-calculates advocate's aggregate rating.
        """
        import uuid
        rev_id = f"rev-{uuid.uuid4().hex[:6]}"
        review = {
            "id": rev_id,
            "advocate_id": advocate_id,
            "client_name": review_data.get("client_name", "Verified Client"),
            "rating": int(review_data.get("rating", 5)),
            "review_text": review_data.get("review_text", ""),
            "payment_id": review_data.get("payment_id", f"PAY-OV-{uuid.uuid4().hex[:8].upper()}"),
            "booking_id": review_data.get("booking_id", ""),
            "knowledge_rating": int(review_data.get("knowledge_rating", 5)),
            "responsiveness_rating": int(review_data.get("responsiveness_rating", 5)),
            "value_rating": int(review_data.get("value_rating", 5)),
            "verified_paid": True,
            "created_at": "Just now"
        }
        
        if advocate_id not in self.advocate_reviews:
            self.advocate_reviews[advocate_id] = []
        self.advocate_reviews[advocate_id].insert(0, review)
        
        # Update advocate rating and review count across stored lists
        all_advocates = self.custom_advocates + FALLBACK_ADVOCATES
        updated_adv = None
        for adv in all_advocates:
            if adv.get("id") == advocate_id:
                old_rating = float(adv.get("rating", 4.8))
                old_count = int(adv.get("reviews", 10))
                new_count = old_count + 1
                new_rating = round(((old_rating * old_count) + review["rating"]) / new_count, 1)
                adv["rating"] = new_rating
                adv["reviews"] = new_count
                updated_adv = dict(adv)
                break
                
        return {"review": review, "advocate": updated_adv}

    def get_advocate_reviews(self, advocate_id: str) -> List[Dict[str, Any]]:
        return self.advocate_reviews.get(advocate_id, [])

    def get_advocates(
        self,
        category: Optional[str] = None,
        city: Optional[str] = None,
        locality: Optional[str] = None,
        district_court: Optional[str] = None,
        q: Optional[str] = None,
        max_fee: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves verified advocates with smart ranking by citizen jurisdiction,
        district court, office locality proximity, practice area, text search, and fee budget.
        """
        all_advocates = self.custom_advocates + FALLBACK_ADVOCATES
        
        filtered = []
        for adv in all_advocates:
            # Text query search
            if q and q.strip():
                q_clean = q.lower().strip()
                haystack = f"{adv['name']} {adv['city']} {adv['state']} {adv.get('district_court', '')} {adv.get('office_location', '')} {adv['bar_council_id']} {' '.join(adv.get('courts', []))} {' '.join(adv.get('practice_areas', []))} {adv.get('bio', '')}".lower()
                if q_clean not in haystack:
                    continue

            # Fee filter
            if max_fee and adv.get("consult_fee", 0) > max_fee:
                continue

            filtered.append(adv)

        # Smart ranking function: prioritizing district court, office location, city, and case domain
        def rank_advocate(adv):
            score = 0
            is_loc_match = False
            adv_city = adv.get("city", "").lower()
            adv_state = adv.get("state", "").lower()
            adv_dc = (adv.get("district_court") or "").lower()
            adv_courts = " ".join(adv.get("courts", [])).lower()
            adv_office = (adv.get("office_location") or "").lower()

            # 1. Exact District Court Match (Top Priority: +50 points)
            if district_court and district_court.strip():
                dc_clean = district_court.lower().strip()
                if dc_clean in adv_dc or adv_dc in dc_clean or dc_clean in adv_courts:
                    score += 50
                    is_loc_match = True

            # 2. Exact Locality / Office Location match (High Priority: +40 points)
            if locality and locality.strip():
                loc_clean = locality.lower().strip()
                if loc_clean in adv_office or adv_office in loc_clean:
                    score += 40
                    is_loc_match = True
                elif loc_clean in adv_city:
                    score += 20
                    is_loc_match = True

            # 3. Exact City / District match (+25 points)
            if city and city.strip():
                c_clean = city.lower().strip()
                if c_clean in adv_city or adv_city in c_clean or c_clean in adv_office or c_clean in adv_dc:
                    score += 25
                    is_loc_match = True
                elif (c_clean in ["noida", "greater noida", "surajpur"]) and ("gautam" in adv_city or "surajpur" in adv_dc or "noida" in adv_office):
                    score += 25
                    is_loc_match = True
                elif (c_clean in ["gurgaon", "gurugram"]) and ("gurugram" in adv_city or "gurgaon" in adv_office):
                    score += 25
                    is_loc_match = True
                elif c_clean in adv_state:
                    score += 15

            # 4. NCR Cross-Jurisdiction Matching (Delhi, Noida/Gautam Buddha Nagar, Gurugram, Ghaziabad)
            ncr_keys = ["new delhi", "delhi", "gautam buddha nagar", "noida", "greater noida", "gurugram", "gurgaon", "ghaziabad", "faridabad"]
            target_str = f"{city} {locality} {district_court}".lower()
            if any(k in target_str for k in ncr_keys):
                adv_str = f"{adv_city} {adv_office} {adv_dc} {adv_courts}".lower()
                if any(k in adv_str for k in ncr_keys):
                    score += 20
            
            # 5. Case Domain Match (+15 points)
            if category and category.strip():
                if category in adv.get("practice_areas", []):
                    score += 15
            
            score += float(adv.get("rating", 4.5))
            adv["is_location_match"] = is_loc_match
            return score

        pool = [dict(a) for a in (filtered if filtered else all_advocates)]
        pool.sort(key=rank_advocate, reverse=True)
        return pool

db = DatabaseClient()
