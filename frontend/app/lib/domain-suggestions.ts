/**
 * Domain-aware law/standard suggestions for the Relevant Laws field.
 * Covers 13 industries. Add new domains here — StepCourseInfo picks them up automatically.
 */

export type DomainKey =
  | "nerc" | "healthcare" | "food_safety" | "workplace_safety"
  | "diversity" | "construction" | "finance" | "cybersecurity"
  | "privacy" | "environmental" | "hr_employment" | "fda" | "manufacturing";

// Keywords that trigger each domain (checked against uppercased course title)
const DOMAIN_KEYWORDS: Record<DomainKey, string[]> = {
  nerc:             ["NERC", "CIP", "TRANSMISSION OPERATOR", "BES CYBER"],
  healthcare:       ["HIPAA", "HEALTH", "HOSPITAL", "MEDICAL", "CLINICAL", "PATIENT", "NURSING", "HEALTHCARE"],
  food_safety:      ["FOOD", "HACCP", "SERVSAFE", "RESTAURANT", "KITCHEN", "FOOD HANDLER", "FOOD SAFETY"],
  workplace_safety: ["OSHA", "HAZARD", "PPE", "LOCKOUT", "FORKLIFT", "ERGONOMICS", "FIRE SAFETY"],
  diversity:        ["DIVERSITY", "INCLUSION", "LGBTQ", "HARASSMENT", "DISCRIMINATION", "EQUITY", "BIAS", "CULTURAL COMPETENCY", "DEI"],
  construction:     ["CONSTRUCTION", "SCAFFOLD", "FALL PROTECTION", "EXCAVATION", "CONTRACTOR"],
  finance:          ["FINANCE", "BANKING", "AML", "FRAUD", "INVESTMENT", "SOX", "TRADING", "FINANCIAL"],
  cybersecurity:    ["CYBERSECURITY", "INFOSEC", "DATA SECURITY", "ISO 27001", "NETWORK SECURITY", "CYBER THREAT"],
  privacy:          ["PRIVACY", "GDPR", "DATA PROTECTION", "FERPA", "PERSONAL DATA"],
  environmental:    ["ENVIRONMENTAL", "HAZARDOUS WASTE", "EMISSIONS", "SPILL RESPONSE", "POLLUTION"],
  hr_employment:    ["HUMAN RESOURCES", "EMPLOYMENT LAW", "HIRING", "FMLA", "WORKPLACE RIGHTS"],
  fda:              ["PHARMACEUTICAL", "DRUG SAFETY", "MEDICAL DEVICE", "GMP", "CLINICAL TRIAL", "BIOLOGICS"],
  manufacturing:    ["MANUFACTURING", "ISO 9001", "LEAN", "SIX SIGMA", "PRODUCTION QUALITY"],
};

export const DOMAIN_LABELS: Record<DomainKey, string> = {
  nerc:             "NERC CIP",
  healthcare:       "Healthcare",
  food_safety:      "Food Safety",
  workplace_safety: "Workplace Safety",
  diversity:        "Diversity & Inclusion",
  construction:     "Construction",
  finance:          "Finance & Banking",
  cybersecurity:    "Cybersecurity",
  privacy:          "Privacy & Data Protection",
  environmental:    "Environmental",
  hr_employment:    "HR & Employment",
  fda:              "FDA & Pharmaceuticals",
  manufacturing:    "Manufacturing & Quality",
};

export const DOMAIN_SUGGESTIONS: Record<DomainKey, string[]> = {
  nerc: [
    "CIP-002", "CIP-003", "CIP-004", "CIP-005", "CIP-006", "CIP-007",
    "CIP-008", "CIP-009", "CIP-010", "CIP-011", "CIP-012", "CIP-013",
    "CIP-014", "CIP-015", "FERC Order 791", "FERC Order 822", "FERC Order 887",
  ],
  healthcare: [
    "HIPAA", "HITECH", "45 CFR Part 164", "ADA (Disability)", "State Medical Privacy Laws",
  ],
  food_safety: [
    "FDA FSMA", "HACCP", "21 CFR Part 117", "21 CFR Part 110",
    "ServSafe Guidelines", "ISO 22000", "FDA Food Code",
  ],
  workplace_safety: [
    "29 CFR 1910", "29 CFR 1926", "OSHA General Duty Clause",
    "NFPA 70E", "NFPA 101", "ANSI Z87.1",
  ],
  diversity: [
    "Title VII (Civil Rights Act 1964)", "ADA", "ADEA",
    "EEOC Guidelines", "Equal Pay Act", "Civil Rights Act 1991",
  ],
  construction: [
    "29 CFR 1926", "OSHA 1926 Subpart M", "OSHA 1926 Subpart P",
    "NFPA 70E", "ANSI A10",
  ],
  finance: [
    "Sarbanes-Oxley Act (SOX)", "BSA/AML", "PCI DSS",
    "Dodd-Frank Act", "GLBA", "SEC Rule 17a-4",
  ],
  cybersecurity: [
    "NIST CSF", "ISO 27001", "SOC 2", "GDPR", "CCPA",
    "NIST SP 800-53", "NIST SP 800-171",
  ],
  privacy: [
    "GDPR", "CCPA", "FERPA", "COPPA", "GLBA Privacy Rule", "PIPEDA",
  ],
  environmental: [
    "Clean Air Act", "Clean Water Act", "RCRA", "CERCLA", "EPA Standards (40 CFR)",
  ],
  hr_employment: [
    "FMLA", "ADA", "FLSA", "Title VII", "NLRA", "Equal Pay Act", "WARN Act",
  ],
  fda: [
    "21 CFR Part 11", "cGMP (21 CFR Part 211)", "ISO 13485", "FDA 510(k)", "ICH Q10",
  ],
  manufacturing: [
    "ISO 9001", "ISO 45001", "ISO 14001", "29 CFR 1910", "OSHA PSM (29 CFR 1910.119)",
  ],
};

// Terms that clearly signal input from the wrong domain
const MISMATCH_SIGNALS: Record<DomainKey, string[]> = {
  nerc:             ["FDA", "HIPAA", "HITECH", "GDPR", "HACCP", "FMLA", "SOX", "TITLE VII"],
  healthcare:       ["CIP-", "NERC", "HACCP", "SOX", "29 CFR 1926"],
  food_safety:      ["CIP-", "NERC", "SOX", "HIPAA", "GDPR", "29 CFR 1926"],
  workplace_safety: ["CIP-", "NERC", "HACCP", "SOX", "GDPR", "HIPAA"],
  diversity:        ["CIP-", "NERC", "HACCP", "29 CFR 1926", "SOX", "HIPAA"],
  construction:     ["CIP-", "NERC", "HIPAA", "SOX", "GDPR", "HACCP"],
  finance:          ["CIP-", "NERC", "HACCP", "HIPAA", "29 CFR"],
  cybersecurity:    ["HACCP", "29 CFR", "FMLA", "TITLE VII", "ADEA"],
  privacy:          ["CIP-", "NERC", "HACCP", "29 CFR", "FMLA"],
  environmental:    ["CIP-", "NERC", "HIPAA", "SOX", "HACCP"],
  hr_employment:    ["CIP-", "NERC", "HACCP", "29 CFR 1926", "SOX"],
  fda:              ["CIP-", "NERC", "GDPR", "HACCP", "29 CFR 1926", "SOX"],
  manufacturing:    ["CIP-", "NERC", "HIPAA", "SOX", "GDPR"],
};

// Broad keyword list — used to identify genuinely unrecognized input
const RECOGNIZED_KEYWORDS = [
  // Regulatory bodies & acronyms
  "osha", "hipaa", "hitech", "gdpr", "ccpa", "ferpa", "coppa", "epa", "fda", "ferc",
  "sec", "eeoc", "nlrb", "nist", "iso", "ansi", "iec", "astm", "ieee", "nfpa", "nerc",
  // Standard codes
  "cfr", "cip", "sox", "pci", "bsa", "aml", "glba", "rcra", "cercla", "fmla", "ada",
  "adea", "flsa", "nlra", "haccp", "fsma", "gmp", "ich", "pipeda", "servsafe",
  // Generic legal/compliance terms
  "act", "order", "regulation", "rule", "standard", "guideline", "code", "policy",
  "law", "directive", "framework", "protocol", "compliance", "safety", "protection",
  "rights", "reform", "statute", "amendment", "title", "part", "section", "subpart",
];

/** Detect which industry domain a course title belongs to. Returns null if unknown. */
export function detectDomain(courseTitle: string): DomainKey | null {
  const upper = courseTitle.toUpperCase();
  for (const [domain, keywords] of Object.entries(DOMAIN_KEYWORDS) as [DomainKey, string[]][]) {
    if (keywords.some((k) => upper.includes(k))) return domain;
  }
  return null;
}

/**
 * Returns a warning if the relevantLaws field contains terms that clearly
 * belong to a different domain than the detected one.
 */
export function getMismatchWarning(domain: DomainKey, relevantLaws: string): string | null {
  if (!relevantLaws.trim()) return null;
  const upper = relevantLaws.toUpperCase();
  const matched = (MISMATCH_SIGNALS[domain] ?? []).find((s) => upper.includes(s));
  if (!matched) return null;
  const topSuggestions = DOMAIN_SUGGESTIONS[domain].slice(0, 3).join(", ");
  return `"${matched}" is not a ${DOMAIN_LABELS[domain]} standard. Suggested: ${topSuggestions}.`;
}

/**
 * Returns a list of unrecognized terms — input that doesn't match any known
 * regulatory keyword, standard code, or numeric pattern.
 * These are flagged as potentially random/incorrect.
 */
export function getUnknownTerms(relevantLaws: string): string[] {
  if (!relevantLaws.trim()) return [];

  return relevantLaws
    .split(",")
    .map((t) => t.trim())
    .filter((t) => t.length >= 3)
    .filter((term) => {
      const lower = term.toLowerCase();
      // Recognized if it contains a known keyword
      if (RECOGNIZED_KEYWORDS.some((k) => lower.includes(k))) return false;
      // Recognized if it looks like a standard code: letters + separator + digits (e.g. "CIP-002", "ISO 9001", "21 CFR 110")
      if (/[a-z]+[\s-]\d+/i.test(term) || /\d+[\s-][a-z]+/i.test(term)) return false;
      // Otherwise unrecognized
      return true;
    });
}
