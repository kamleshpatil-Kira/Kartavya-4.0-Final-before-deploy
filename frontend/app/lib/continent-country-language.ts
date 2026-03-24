// Continent → Country → Languages (only from existing COURSE_LANGUAGES list)
export const CONTINENT_COUNTRY_LANGUAGE: Record<string, Record<string, string[]>> = {
    Asia: {
        "India": ["Hindi", "English"],
        "China": ["Chinese (Simplified)"],
        "Taiwan": ["Chinese (Traditional)"],
        "Hong Kong": ["Chinese (Traditional)", "English"],
        "Japan": ["Japanese"],
        "South Korea": ["Korean"],
        "Saudi Arabia": ["Arabic"],
        "UAE": ["Arabic", "English"],
        "Jordan": ["Arabic"],
        "Turkey": ["Turkish"],
        "Vietnam": ["Vietnamese"],
        "Thailand": ["Thai"],
        "Indonesia": ["Indonesian"],
        "Singapore": ["English", "Chinese (Simplified)"],
        "Philippines": ["English"],
    },
    Europe: {
        "United Kingdom": ["English"],
        "France": ["French"],
        "Germany": ["German"],
        "Spain": ["Spanish"],
        "Italy": ["Italian"],
        "Netherlands": ["Dutch"],
        "Belgium": ["French", "Dutch"],
        "Portugal": ["Portuguese"],
        "Russia": ["Russian"],
        "Austria": ["German"],
        "Switzerland": ["French", "German", "Italian"],
        "Ireland": ["English"],
        "Turkey": ["Turkish"],
    },
    "North America": {
        "United States": ["English", "Spanish"],
        "Canada": ["English", "French"],
        "Mexico": ["Spanish"],
        "Cuba": ["Spanish"],
        "Guatemala": ["Spanish"],
    },
    "South America": {
        "Brazil": ["Portuguese"],
        "Argentina": ["Spanish"],
        "Colombia": ["Spanish"],
        "Chile": ["Spanish"],
        "Peru": ["Spanish"],
        "Venezuela": ["Spanish"],
        "Ecuador": ["Spanish"],
    },
    Africa: {
        "South Africa": ["English"],
        "Egypt": ["Arabic"],
        "Morocco": ["Arabic", "French"],
        "Algeria": ["Arabic", "French"],
        "Nigeria": ["English"],
        "Senegal": ["French"],
        "Mozambique": ["Portuguese"],
    },
    Oceania: {
        "Australia": ["English"],
        "New Zealand": ["English"],
    },
};

// Helper: get all continents
export const CONTINENTS = Object.keys(CONTINENT_COUNTRY_LANGUAGE);

// Helper: get countries for a continent
export function getCountries(continent: string): string[] {
    return Object.keys(CONTINENT_COUNTRY_LANGUAGE[continent] || {});
}

// Helper: get languages for a country in a continent
export function getLanguagesForCountry(continent: string, country: string): string[] {
    return CONTINENT_COUNTRY_LANGUAGE[continent]?.[country] || [];
}
