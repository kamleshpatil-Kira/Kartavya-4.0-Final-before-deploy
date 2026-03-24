export type CatalogCategory =
    | "Information Security"
    | "OSHA Compliance"
    | "HIPAA Compliance"
    | "Healthcare Training"
    | "Diversity & Inclusion"
    | "Joint Commission"
    | "Campus Compliance"
    | "Ethics & Legal"
    | "Food Safety"
    | "Financial & AML"
    | "AI & Tech Ethics"
    | "ESG & Sustainability"
    | "Remote Work & Modern Workplace";

interface CategoryData {
    guidelines: string[];
    keywords: string[];
}

export const CATALOG_DICTIONARY: Record<CatalogCategory, CategoryData> = {
    "Information Security": {
        guidelines: ["ISO 27001", "NIST CSF", "NERC CIP", "SOC 2", "NIST SP 800-53", "CIS Controls"],
        keywords: [
            "information security", "malware", "password", "physical security",
            "secure use", "mobile devices", "surfing", "identity theft",
            "phishing", "social engineering", "fax security", "spyware",
            "social networks", "copyright", "retention and destruction",
            "credit card data", "red flag program", "securing your computer",
            "dealing with documents", "out of the office", "gdpr", "nerc cip",
            "ransomware", "zero trust", "cloud security", "incident response",
            "iot security", "smart device", "cyber", "cybersecurity",
            "data breach", "vulnerability", "endpoint security", "vpn",
            "multi-factor authentication", "mfa", "encryption", "firewall",
            "patch management", "penetration testing", "security awareness",
            "ccpa", "pipeda", "pdpa", "data privacy", "network security"
        ]
    },
    "OSHA Compliance": {
        guidelines: [
            "OSHA 29 CFR 1910", "OSHA General Duty Clause", "ANSI Z87.1",
            "OSHA 29 CFR 1910.1030 (Bloodborne Pathogens)", "NIOSH Guidelines",
            "OSHA Heat Illness Prevention (29 CFR 1910.269)"
        ],
        keywords: [
            "osha", "workplace safety", "basic safety", "hazard communication",
            "bloodborne pathogens", "radiation safety", "exit route",
            "electrical", "emergency action plan", "fire safety",
            "advanced safety", "hand hygiene", "medical and first aid",
            "personal protective equipment", "ppe", "ergonomic hazards",
            "slips, trips", "influenza", "tuberculosis", "emergency response",
            "chemical hazards", "walking/working surfaces", "asbestos",
            "cpr", "hepatitis", "laboratory safety", "respiratory",
            "safety audits", "sharps injury", "covid-19", "pandemic",
            "heat illness", "heat stress", "remote ergonomics", "home office safety",
            "mental health safety", "psychological safety", "workplace wellness",
            "construction safety", "lockout tagout", "confined space",
            "forklift safety", "fall protection", "noise hazard"
        ]
    },
    "HIPAA Compliance": {
        guidelines: [
            "HIPAA Privacy Rule", "HIPAA Security Rule", "HITECH Act",
            "45 CFR Part 164", "HIPAA Breach Notification Rule",
            "HHS Office for Civil Rights (OCR) Guidelines",
            "Telehealth Privacy Guidelines (HHS)"
        ],
        keywords: [
            "hipaa", "privacy rule", "security rule", "business associates",
            "breach notification", "protected health information", "phi",
            "telehealth", "telemedicine", "remote care", "virtual care",
            "electronic health records", "ehr", "patient data", "medical records",
            "covered entity", "minimum necessary", "authorization", "notice of privacy",
            "hipaa training", "hipaa for managers", "hipaa for it", "hipaa audit"
        ]
    },
    "Healthcare Training": {
        guidelines: [
            "State Medical Privacy Laws", "Clinical Guidelines", "ADA (Disability)",
            "CMS Conditions of Participation", "Joint Commission Standards",
            "ANA Code of Ethics"
        ],
        keywords: [
            "healthcare", "medical fields", "uro-nephrology", "ob-gyn",
            "gi-gu", "orthopedic", "neurology", "oncology", "pediatrics",
            "mental health", "dental", "skin", "family care", "cardiology",
            "pulmonary", "respiratory", "clinics", "hospitals", "nursing",
            "ancillary", "volunteers", "patient care", "clinical staff",
            "nurse", "physician", "allied health", "pharmacy", "radiology",
            "infection control", "sterile processing", "medical coding",
            "billing", "healthcare compliance", "patient safety"
        ]
    },
    "Diversity & Inclusion": {
        guidelines: [
            "EEOC Guidelines", "Title VII (Civil Rights Act 1964)", "ADA",
            "Equal Pay Act", "ADEA (Age Discrimination)", "Pregnant Workers Fairness Act",
            "NLRA Section 7 Rights"
        ],
        keywords: [
            "diversity", "inclusion", "cultural sensitivity", "harassment",
            "sexual harassment", "lgbtq", "bias", "workplace violence",
            "abuse", "neglect", "exploitation", "unconscious bias",
            "neurodiversity", "bystander intervention", "ally",
            "equity", "belonging", "microaggressions", "racial equity",
            "gender equity", "disability inclusion", "mental health stigma",
            "accessibility", "accommodation", "inclusive leadership",
            "anti-discrimination", "equal opportunity", "dei", "diversity training",
            "california harassment", "new york harassment", "connecticut harassment",
            "illinois harassment", "texas harassment", "florida harassment"
        ]
    },
    "Joint Commission": {
        guidelines: [
            "The Joint Commission (TJC) Standards", "OSHA 29 CFR 1910",
            "CMS Conditions of Participation", "National Patient Safety Goals (NPSG)"
        ],
        keywords: [
            "joint commission", "patient rights", "patient evacuation",
            "back care", "latex allergy", "lifting and transferring",
            "tjc", "accreditation", "sentinel event", "root cause analysis",
            "patient safety goal", "hand hygiene", "medication safety",
            "fall prevention", "pressure injury", "restraint use",
            "environment of care", "emergency management"
        ]
    },
    "Campus Compliance": {
        guidelines: [
            "Title IX", "Clery Act", "FERPA",
            "Violence Against Women Act (VAWA)",
            "Campus SaVE Act", "34 CFR Part 99"
        ],
        keywords: [
            "campus", "clery act", "campus security authority", "title ix",
            "student", "athletes", "sexual assault", "alcohol risk",
            "drugs risk", "ferpa", "higher education", "university", "college",
            "student records", "campus safety", "vawa", "dating violence",
            "stalking", "bystander", "student conduct", "greek life",
            "residence hall", "campus police", "reporting obligations"
        ]
    },
    "Ethics & Legal": {
        guidelines: [
            "FCPA", "UK Bribery Act", "Sarbanes-Oxley Act (SOX)", "Stark Law",
            "False Claims Act", "Dodd-Frank Whistleblower Protection",
            "Common Rule (45 CFR Part 46)"
        ],
        keywords: [
            "ethics", "fraud", "waste", "abuse", "foreign corrupt practices",
            "fcpa", "bribery act", "human research", "red flags rule", "stark law",
            "whistleblower", "code of conduct", "conflict of interest",
            "anti-bribery", "anti-corruption", "corporate governance",
            "sox", "sarbanes", "false claims", "government contracting",
            "research compliance", "irb", "informed consent",
            "vendor ethics", "gifts and entertainment", "third-party risk"
        ]
    },
    "Food Safety": {
        guidelines: [
            "FDA Food Code", "ServSafe Guidelines", "HACCP",
            "FDA Food Safety Modernization Act (FSMA)",
            "USDA Food Safety Standards", "ISO 22000"
        ],
        keywords: [
            "food safety", "food manager", "food handler", "fda", "haccp", "servsafe",
            "foodborne illness", "contamination", "allergen", "food allergy",
            "temperature control", "cold chain", "hot holding", "sanitation",
            "pest control", "cross contamination", "personal hygiene food",
            "food storage", "food labeling", "fsma", "food recall",
            "restaurant safety", "cafeteria", "catering", "food service"
        ]
    },
    "Financial & AML": {
        guidelines: [
            "Bank Secrecy Act (BSA)", "FinCEN AML Guidelines",
            "FINRA Rules", "SEC Regulations",
            "Know Your Customer (KYC) Standards",
            "FATF Recommendations", "Sarbanes-Oxley Act (SOX)"
        ],
        keywords: [
            "anti-money laundering", "aml", "know your customer", "kyc",
            "bank secrecy act", "bsa", "financial crime", "suspicious activity",
            "sar", "currency transaction report", "ctr", "beneficial owner",
            "customer due diligence", "cdd", "enhanced due diligence", "edd",
            "insider trading", "securities fraud", "market manipulation",
            "financial compliance", "finra", "sec compliance",
            "investment fraud", "ponzi scheme", "embezzlement",
            "financial ethics", "accounting fraud", "sox compliance",
            "wire transfer", "sanctions", "ofac", "treasury compliance"
        ]
    },
    "AI & Tech Ethics": {
        guidelines: [
            "NIST AI Risk Management Framework (AI RMF)",
            "EU AI Act", "IEEE Ethically Aligned Design",
            "FTC AI Guidelines", "OECD AI Principles",
            "White House AI Bill of Rights"
        ],
        keywords: [
            "artificial intelligence", "ai ethics", "responsible ai",
            "machine learning", "algorithm", "algorithmic bias",
            "ai fairness", "deepfake", "synthetic media", "generative ai",
            "large language model", "llm", "chatgpt", "ai in the workplace",
            "automated decision making", "explainable ai", "xai",
            "ai transparency", "data ethics", "privacy by design",
            "facial recognition", "surveillance technology", "biometric data",
            "ai compliance", "tech ethics", "digital ethics",
            "social media", "online safety", "digital literacy",
            "misinformation", "disinformation", "ai risk", "ai governance"
        ]
    },
    "ESG & Sustainability": {
        guidelines: [
            "GRI Standards (Global Reporting Initiative)",
            "SASB Standards", "TCFD Recommendations",
            "UN Sustainable Development Goals (SDGs)",
            "ISO 14001 (Environmental Management)",
            "SEC Climate Disclosure Rules"
        ],
        keywords: [
            "esg", "environmental social governance", "sustainability",
            "carbon footprint", "greenhouse gas", "ghg emissions",
            "climate risk", "climate change", "net zero", "carbon neutral",
            "renewable energy", "energy efficiency", "waste reduction",
            "circular economy", "supply chain sustainability",
            "social responsibility", "corporate social responsibility", "csr",
            "diversity reporting", "pay equity reporting", "board diversity",
            "environmental compliance", "epa regulations", "water conservation",
            "biodiversity", "sustainable procurement", "green building",
            "leed", "scope 1 scope 2 scope 3", "carbon accounting"
        ]
    },
    "Remote Work & Modern Workplace": {
        guidelines: [
            "OSHA Home Office Guidelines", "NIST SP 800-46 (Remote Access)",
            "ADA Telework Accommodations", "IRS Home Office Rules",
            "State Wage and Hour Laws for Remote Workers"
        ],
        keywords: [
            "remote work", "work from home", "telecommute", "hybrid work",
            "home office", "remote ergonomics", "virtual team", "distributed team",
            "video conferencing", "zoom security", "remote collaboration",
            "digital wellness", "screen fatigue", "work life balance",
            "remote onboarding", "virtual meeting etiquette",
            "cloud collaboration", "microsoft teams", "slack security",
            "bring your own device", "byod", "remote access", "vpn",
            "remote worker rights", "expense reimbursement remote",
            "mental health remote", "isolation remote work",
            "productivity remote", "time tracking", "flexible work"
        ]
    }
};

/**
 * Returns a list of suggested guidelines based on the provided title and audience.
 * It searches for keywords within the dictionary mapping.
 */
export function suggestGuidelinesByDictionary(title: string, audience: string): string[] {
    const combinedText = `${title} ${audience}`.toLowerCase();

    const matches = new Set<string>();

    for (const [, data] of Object.entries(CATALOG_DICTIONARY)) {
        if (data.keywords.some((kw) => combinedText.includes(kw.toLowerCase()))) {
            data.guidelines.forEach((g) => matches.add(g));
        }
    }

    // Fallbacks if nothing matched
    if (matches.size === 0) {
        if (combinedText.includes("security") || combinedText.includes("cyber")) {
            matches.add("ISO 27001");
            matches.add("NIST CSF");
        } else if (combinedText.includes("health") || combinedText.includes("medical")) {
            matches.add("HIPAA Privacy Rule");
            matches.add("OSHA 29 CFR 1910.1030 (Bloodborne Pathogens)");
        } else if (combinedText.includes("finance") || combinedText.includes("bank")) {
            matches.add("Bank Secrecy Act (BSA)");
            matches.add("FinCEN AML Guidelines");
        } else if (combinedText.includes("ai") || combinedText.includes("machine learning")) {
            matches.add("NIST AI Risk Management Framework (AI RMF)");
            matches.add("EU AI Act");
        } else {
            matches.add("ISO 9001");
            matches.add("Standard Corporate Policy");
        }
    }

    return Array.from(matches);
}

/**
 * Returns suggested categories (with their guidelines) for a given free-text query.
 * Useful for displaying category-level chips before the user has typed guidelines.
 */
export function suggestCategoriesByText(text: string): CatalogCategory[] {
    const lower = text.toLowerCase();
    const matched: CatalogCategory[] = [];

    for (const [category, data] of Object.entries(CATALOG_DICTIONARY) as [CatalogCategory, CategoryData][]) {
        if (data.keywords.some((kw) => lower.includes(kw.toLowerCase()))) {
            matched.push(category);
        }
    }

    return matched;
}
