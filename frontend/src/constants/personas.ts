/**
 * Constants for Personas component - hardcoded labels and mappings
 */

// Helper function for text normalization
function normalizeText(value?: string | null): string {
  if (!value) return '';
  return value
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\s]/g, '')
    .trim();
}

// Gender labels mapping
export const GENDER_LABELS: Record<string, string> = {
  female: 'Kobieta',
  kobieta: 'Kobieta',
  male: 'Mężczyzna',
  mężczyzna: 'Mężczyzna',
  man: 'Mężczyzna',
  woman: 'Kobieta',
  'non-binary': 'Osoba niebinarna',
  nonbinary: 'Osoba niebinarna',
  other: 'Osoba niebinarna',
};

// Education labels mapping
export const EDUCATION_LABELS: Record<string, string> = {
  'high school': 'Średnie ogólnokształcące',
  'some college': 'Policealne',
  "bachelor's degree": 'Wyższe licencjackie',
  "master's degree": 'Wyższe magisterskie',
  "masters degree": 'Wyższe magisterskie',
  doctorate: 'Doktorat',
  phd: 'Doktorat',
  'technical school': 'Średnie techniczne',
  'trade school': 'Zasadnicze zawodowe',
  vocational: 'Zasadnicze zawodowe',
};

// Income labels mapping
export const INCOME_LABELS: Record<string, string> = {
  '< $25k': '< 3 000 zł',
  '$25k-$50k': '3 000 - 5 000 zł',
  '$50k-$75k': '5 000 - 7 500 zł',
  '$75k-$100k': '7 500 - 10 000 zł',
  '$100k-$150k': '10 000 - 15 000 zł',
  '> $150k': '> 15 000 zł',
  '$150k+': '> 15 000 zł',
};

// Polish city names
export const POLISH_CITY_NAMES = [
  'Warszawa',
  'Kraków',
  'Wrocław',
  'Gdańsk',
  'Poznań',
  'Łódź',
  'Katowice',
  'Szczecin',
  'Lublin',
  'Białystok',
  'Bydgoszcz',
  'Gdynia',
  'Częstochowa',
  'Radom',
  'Toruń',
  'Inne miasta',
];

// Polish city lookup (normalized)
export const POLISH_CITY_LOOKUP: Record<string, string> = POLISH_CITY_NAMES.reduce((acc, city) => {
  acc[normalizeText(city)] = city;
  return acc;
}, {} as Record<string, string>);

// Location aliases mapping
export const LOCATION_ALIASES: Record<string, string> = {
  warsaw: 'Warszawa',
  krakow: 'Kraków',
  wroclaw: 'Wrocław',
  poznan: 'Poznań',
  lodz: 'Łódź',
  gdansk: 'Gdańsk',
  gdynia: 'Gdynia',
  szczecin: 'Szczecin',
  lublin: 'Lublin',
  bialystok: 'Białystok',
  bydgoszcz: 'Bydgoszcz',
  katowice: 'Katowice',
  czestochowa: 'Częstochowa',
  torun: 'Toruń',
  radom: 'Radom',
};

// Export normalizeText for use in components
export { normalizeText };
