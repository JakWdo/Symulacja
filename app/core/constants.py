"""Wspólne stałe dla rozkładów demograficznych i wartości domyślnych."""

# Domyślne rozkłady demograficzne
DEFAULT_AGE_GROUPS = {
    "18-24": 0.15,
    "25-34": 0.25,
    "35-44": 0.20,
    "45-54": 0.18,
    "55-64": 0.12,
    "65+": 0.10,
}

DEFAULT_GENDERS = {
    "male": 0.49,
    "female": 0.49,
    "non-binary": 0.02,
}

DEFAULT_LOCATIONS = {
    "New York, NY": 0.15,
    "Los Angeles, CA": 0.12,
    "Chicago, IL": 0.10,
    "Houston, TX": 0.08,
    "Phoenix, AZ": 0.06,
    "Philadelphia, PA": 0.06,
    "San Antonio, TX": 0.05,
    "San Diego, CA": 0.05,
    "Dallas, TX": 0.05,
    "San Jose, CA": 0.04,
    "Other": 0.24,
}

DEFAULT_EDUCATION_LEVELS = {
    "High school": 0.25,
    "Some college": 0.20,
    "Bachelor's degree": 0.30,
    "Master's degree": 0.15,
    "Doctorate": 0.05,
    "Other": 0.05,
}

DEFAULT_INCOME_BRACKETS = {
    "< $25k": 0.15,
    "$25k-$50k": 0.20,
    "$50k-$75k": 0.22,
    "$75k-$100k": 0.18,
    "$100k-$150k": 0.15,
    "> $150k": 0.10,
}

# Domyślne zawody person – poszerzone dla różnorodności
DEFAULT_OCCUPATIONS = [
    # Technologie i inżynieria
    "Software Engineer", "Data Scientist", "UX Designer", "Product Manager", "DevOps Engineer",
    "Cybersecurity Analyst", "AI/ML Engineer", "Cloud Architect", "QA Engineer", "Technical Writer",
    # Biznes i zarządzanie
    "Business Analyst", "Operations Manager", "Project Manager", "Strategy Consultant", "CFO",
    "Entrepreneur", "Startup Founder", "Business Development Manager", "Account Executive",
    # Marketing i sprzedaż
    "Marketing Manager", "Brand Strategist", "Content Creator", "Social Media Manager", "SEO Specialist",
    "Growth Hacker", "Sales Director", "Customer Success Manager", "PR Specialist",
    # Kreatywność i projektowanie
    "Graphic Designer", "Art Director", "Video Editor", "Photographer", "Illustrator",
    "Copywriter", "Creative Director", "Motion Designer", "UI Designer", "Brand Designer",
    # Zdrowie i nauka
    "Physician", "Nurse Practitioner", "Research Scientist", "Pharmacist", "Physical Therapist",
    "Clinical Psychologist", "Biotech Researcher", "Medical Device Engineer", "Healthcare Administrator",
    # Edukacja i szkolenia
    "University Professor", "High School Teacher", "Corporate Trainer", "Education Consultant",
    "Curriculum Designer", "EdTech Specialist", "School Principal", "Online Course Creator",
    # Finanse i prawo
    "Financial Analyst", "Investment Banker", "Accountant", "Tax Consultant", "Lawyer",
    "Paralegal", "Compliance Officer", "Risk Analyst", "Financial Advisor", "Auditor",
    # Usługi i hotelarstwo
    "Restaurant Manager", "Hotel Manager", "Event Planner", "Chef", "Travel Agent",
    "Customer Service Manager", "Retail Manager", "Personal Trainer", "Life Coach",
    # Zawody techniczne i manualne
    "Electrician", "Plumber", "Carpenter", "Mechanic", "HVAC Technician",
    "Construction Manager", "Landscaper", "Real Estate Agent",
    # Sztuka i rozrywka
    "Musician", "Actor", "Film Producer", "Journalist", "Podcaster", "YouTuber",
    "Gallery Curator", "Fashion Designer", "Interior Designer",
    # Sektor publiczny i organizacje non-profit
    "Social Worker", "Policy Analyst", "Nonprofit Director", "Community Organizer",
    "Urban Planner", "Environmental Scientist", "Public Health Specialist",
]

DEFAULT_VALUES = [
    # Rozwój osobisty
    "Personal Growth", "Self-Improvement", "Continuous Learning", "Curiosity", "Authenticity",
    "Self-Expression", "Independence", "Autonomy", "Creativity", "Innovation",
    # Relacje i wspólnota
    "Family", "Friendship", "Love", "Community", "Belonging", "Connection", "Empathy",
    "Compassion", "Kindness", "Generosity", "Collaboration", "Teamwork",
    # Osiągnięcia i sukces
    "Ambition", "Success", "Excellence", "Achievement", "Recognition", "Status",
    "Wealth", "Career Advancement", "Power", "Leadership", "Competition",
    # Etyka i moralność
    "Integrity", "Honesty", "Fairness", "Justice", "Equality", "Diversity",
    "Inclusion", "Respect", "Trust", "Loyalty", "Responsibility",
    # Styl życia i dobrostan
    "Health", "Wellness", "Fitness", "Balance", "Work-Life Balance", "Happiness",
    "Joy", "Fun", "Adventure", "Freedom", "Flexibility", "Simplicity",
    # Społeczeństwo i środowisko
    "Sustainability", "Environmentalism", "Social Justice", "Activism", "Philanthropy",
    "Volunteering", "Making a Difference", "Legacy", "Impact",
    # Sfera intelektualna i duchowa
    "Wisdom", "Knowledge", "Truth", "Spirituality", "Mindfulness", "Peace",
    "Tradition", "Heritage", "Culture", "Art", "Beauty",
    # Praktyczność i bezpieczeństwo
    "Security", "Stability", "Predictability", "Efficiency", "Productivity",
    "Organization", "Planning", "Pragmatism", "Resourcefulness",
]

DEFAULT_INTERESTS = [
    # Sport i aktywność
    "Running", "Yoga", "Weightlifting", "Cycling", "Swimming", "Hiking", "Rock Climbing",
    "Martial Arts", "CrossFit", "Dance", "Team Sports", "Tennis", "Golf",
    # Sztuka i kreatywność
    "Painting", "Drawing", "Photography", "Videography", "Music", "Playing Instruments",
    "Singing", "Writing", "Poetry", "Creative Writing", "Journaling", "Calligraphy",
    "Sculpture", "Pottery", "Crafting", "Knitting", "Sewing",
    # Technologia i gry
    "Gaming", "Video Games", "Board Games", "Virtual Reality", "Coding", "Programming",
    "3D Modeling", "Robotics", "Drones", "Smart Home Tech", "Cryptocurrency", "NFTs",
    # Jedzenie i gotowanie
    "Cooking", "Baking", "Grilling", "Wine Tasting", "Coffee", "Tea", "Craft Beer",
    "Food Blogging", "Recipe Development", "Meal Prep", "Vegetarian Cooking", "International Cuisine",
    # Podróże i przygoda
    "Travel", "Backpacking", "Road Trips", "International Travel", "Solo Travel",
    "Adventure Travel", "Camping", "RV Life", "Digital Nomad Lifestyle",
    # Nauka i sfera intelektualna
    "Reading", "Audiobooks", "Podcasts", "Online Courses", "Language Learning",
    "History", "Philosophy", "Science", "Astronomy", "Psychology", "Economics",
    # Społeczność i zaangażowanie
    "Volunteering", "Community Service", "Mentoring", "Networking", "Public Speaking",
    "Activism", "Politics", "Debate", "Social Causes",
    # Rozrywka i media
    "Movies", "TV Shows", "Streaming", "Theater", "Concerts", "Live Music",
    "Festivals", "Stand-up Comedy", "Opera", "Ballet",
    # Natura i aktywność na świeżym powietrzu
    "Gardening", "Bird Watching", "Fishing", "Hunting", "Kayaking", "Surfing",
    "Skiing", "Snowboarding", "Nature Photography", "Wildlife Conservation",
    # Biznes i finanse
    "Investing", "Stock Market", "Real Estate", "Entrepreneurship", "Side Hustles",
    "Personal Finance", "Budgeting", "Startups", "Business Books",
    # Dobrostan i dbanie o siebie
    "Meditation", "Mindfulness", "Spa Days", "Massage", "Aromatherapy",
    "Holistic Health", "Natural Remedies", "Mental Health Advocacy",
    # Do-it-yourself i tworzenie
    "DIY Projects", "Home Improvement", "Woodworking", "Electronics", "Car Restoration",
    "3D Printing", "Model Building", "Home Brewing",
    # Moda i styl
    "Fashion", "Sustainable Fashion", "Thrifting", "Vintage Shopping", "Makeup",
    "Skincare", "Haircare", "Personal Styling",
    # Kolekcjonowanie i hobby
    "Collecting", "Antiques", "Coins", "Stamps", "Vinyl Records", "Sneakers",
    "Action Figures", "Comic Books", "Trading Cards",
]

# Style komunikacji używane przy generowaniu person
DEFAULT_COMMUNICATION_STYLES = [
    "direct and concise", "warm and empathetic", "analytical and data-driven",
    "enthusiastic and energetic", "calm and measured", "humorous and lighthearted",
    "formal and professional", "casual and friendly", "thoughtful and reflective",
    "passionate and intense", "diplomatic and tactful", "blunt and honest",
    "storytelling-focused", "question-driven", "visual and metaphorical",
    "collaborative and inclusive", "assertive and confident", "humble and modest",
    "expressive and animated", "reserved and observant",
]

# Style podejmowania decyzji
DEFAULT_DECISION_STYLES = [
    "data-driven and analytical", "intuition-based and spontaneous",
    "consensus-seeking and collaborative", "decisive and quick",
    "cautious and risk-averse", "bold and risk-taking",
    "research-heavy and thorough", "experience-based and practical",
    "values-driven and principled", "outcome-focused and pragmatic",
    "consultative with trusted advisors", "independent and self-reliant",
    "deliberate and methodical", "flexible and adaptive",
]

# Sytuacje życiowe używane jako kontekst
DEFAULT_LIFE_SITUATIONS = [
    "single and career-focused", "married without children", "married with young children",
    "single parent", "empty nester", "recently divorced", "engaged and planning wedding",
    "living with roommates", "living alone", "living with parents",
    "recently moved cities", "remote worker", "digital nomad",
    "caregiver for elderly parent", "starting a business", "career transition",
    "recent graduate", "mid-career professional", "approaching retirement",
    "semi-retired", "pursuing further education", "sabbatical",
]

# ═══════════════════════════════════════════════════════════════════════════════
# POLSKIE STAŁE DLA RAG SYSTEM
# Używane przy generowaniu person odzwierciedlających polskie społeczeństwo
# ═══════════════════════════════════════════════════════════════════════════════

# Rozkład lokalizacji w Polsce (na podstawie danych demograficznych)
POLISH_LOCATIONS = {
    "Warszawa": 0.20,
    "Kraków": 0.10,
    "Wrocław": 0.08,
    "Gdańsk": 0.06,
    "Poznań": 0.06,
    "Łódź": 0.05,
    "Katowice": 0.05,
    "Szczecin": 0.04,
    "Lublin": 0.04,
    "Białystok": 0.03,
    "Bydgoszcz": 0.03,
    "Gdynia": 0.02,
    "Częstochowa": 0.02,
    "Radom": 0.02,
    "Toruń": 0.02,
    "Inne miasta": 0.18,
}

# Typowe polskie wartości życiowe
POLISH_VALUES = [
    # Wartości rodzinne i społeczne
    "Rodzina",
    "Tradycja",
    "Lojalność",
    "Szacunek dla starszych",
    "Wierność",
    "Uczciwość",
    "Gościnność",
    "Solidarność",
    # Wartości zawodowe
    "Ciężka praca",
    "Stabilność zawodowa",
    "Oszczędność",
    "Zaradność",
    "Rzetelność",
    "Punktualność",
    # Wartości duchowe i kulturowe
    "Wiara religijna",
    "Patriotyzm",
    "Historia Polski",
    "Kultura narodowa",
    # Wartości współczesne
    "Bezpieczeństwo",
    "Edukacja",
    "Zdrowie",
    "Rozwój osobisty",
    "Niezależność",
    "Przedsiębiorczość",
]

# Typowe polskie zainteresowania i hobby
POLISH_INTERESTS = [
    # Sport i aktywność
    "Piłka nożna",
    "Siatkówka",
    "Jazda na rowerze",
    "Turystyka górska",
    "Spacery po lesie",
    "Bieganie",
    "Pływanie",
    "Narty",
    # Aktywności domowe i hobby
    "Majsterkowanie",
    "Gotowanie",
    "Pieczenie ciast",
    "Hodowla ogródka działkowego",
    "Grzybobranie",
    "Zbieranie jagód",
    "Wędkarstwo",
    # Kultura i rozrywka
    "Oglądanie filmów",
    "Czytanie książek",
    "Słuchanie muzyki",
    "Disco polo",
    "Polska muzyka rockowa",
    "Kabaret",
    "Filmy polskie",
    # Technologia i media
    "Gry komputerowe",
    "Media społecznościowe",
    "YouTube",
    "Podcasty",
    # Społeczność i tradycje
    "Ognisko i spotkania towarzyskie",
    "Wieczory przy grillu",
    "Spotkania rodzinne",
    "Wycieczki do zabytków",
    # Historia i kultura
    "Historia Polski",
    "Muzea",
    "Zamki i pałace",
    "Kuchnia regionalna",
    # Motoryzacja
    "Motoryzacja",
    "Tuning samochodów",
    "Mechanika samochodowa",
    # Rękodzieło i twórczość
    "Rękodzieło",
    "Haftowanie",
    "Szydełkowanie",
    "Decoupage",
]

# Rozkład polskich zawodów (proporcje przybliżone)
POLISH_OCCUPATIONS = {
    # IT i technologie (rosnący sektor)
    "Programista/ka": 0.05,
    "Tester/ka oprogramowania": 0.01,
    "Administrator/ka systemów": 0.01,
    # Edukacja (duży sektor publiczny)
    "Nauczyciel/ka": 0.06,
    "Pedagog/Pedagożka": 0.01,
    "Wykładowca akademicki/a": 0.01,
    # Służba zdrowia (duże zatrudnienie)
    "Pielęgniarka/Pielęgniarz": 0.04,
    "Lekarz/Lekarka": 0.02,
    "Ratownik medyczny": 0.01,
    "Farmaceuta/Farmaceutka": 0.01,
    # Handel i sprzedaż
    "Sprzedawca/Sprzedawczyni": 0.08,
    "Kasjer/Kasjerka": 0.03,
    "Przedstawiciel handlowy": 0.02,
    # Transport i logistyka
    "Kierowca zawodowy": 0.05,
    "Kurier": 0.02,
    "Magazynier": 0.02,
    # Usługi i gastronomia
    "Kelner/Kelnerka": 0.02,
    "Kucharz": 0.02,
    "Fryzjer/Fryzjerka": 0.02,
    "Kosmetyczka": 0.01,
    # Administracja i biuro
    "Księgowa/Księgowy": 0.03,
    "Urzędnik/Urzędniczka": 0.04,
    "Sekretarka/Sekretarz": 0.02,
    "Specjalista ds. HR": 0.01,
    # Produkcja i przemysł
    "Pracownik produkcji": 0.06,
    "Operator maszyn": 0.02,
    # Zawody techniczne
    "Elektryk": 0.02,
    "Hydraulik": 0.01,
    "Mechanik samochodowy": 0.02,
    "Stolarz": 0.01,
    # Budownictwo
    "Budowlaniec": 0.03,
    "Brygadzista": 0.01,
    # Przedsiębiorczość
    "Przedsiębiorca/Przedsiębiorczyni": 0.06,
    "Właściciel małej firmy": 0.03,
    # Bezpieczeństwo
    "Strażak": 0.01,
    "Policjant/Policjantka": 0.02,
    "Ochroniarz": 0.02,
    # Inne zawody
    "Inne": 0.18,
}

# Polskie imiona męskie (rozszerzona lista - mix pokoleń)
POLISH_MALE_NAMES = [
    # Popularne we wszystkich grupach wiekowych
    "Jan", "Piotr", "Andrzej", "Krzysztof", "Stanisław", "Tomasz", "Paweł",
    "Józef", "Marcin", "Marek", "Michał", "Grzegorz", "Jerzy", "Tadeusz",
    "Adam", "Wojciech", "Zbigniew", "Ryszard", "Dariusz", "Henryk", "Mariusz",
    "Kazimierz", "Waldemar", "Mirosław", "Mateusz", "Rafał", "Robert",
    "Łukasz", "Jakub", "Szymon", "Filip", "Kamil", "Dawid", "Bartosz",
    # Dodatkowe imiona starszych pokoleń
    "Władysław", "Zdzisław", "Czesław", "Bolesław", "Edward", "Roman",
    "Leszek", "Bogdan", "Stefan", "Wiesław", "Eugeniusz", "Zenon",
    # Dodatkowe imiona młodszych pokoleń
    "Kacper", "Mikołaj", "Wiktor", "Igor", "Maksymilian", "Dominik",
    "Sebastian", "Oskar", "Antoni", "Maciej", "Patryk", "Adrian",
    "Daniel", "Karol", "Damian", "Hubert", "Konrad", "Artur",
    "Radosław", "Przemysław", "Norbert", "Emil", "Kuba", "Tymoteusz",
]

# Polskie imiona żeńskie (rozszerzona lista - mix pokoleń)
POLISH_FEMALE_NAMES = [
    # Popularne we wszystkich grupach wiekowych
    "Maria", "Anna", "Katarzyna", "Małgorzata", "Agnieszka", "Barbara", "Ewa",
    "Elżbieta", "Zofia", "Krystyna", "Teresa", "Joanna", "Magdalena", "Monika",
    "Jadwiga", "Danuta", "Irena", "Halina", "Helena", "Beata", "Aleksandra",
    "Natalia", "Karolina", "Paulina", "Justyna", "Ewelina", "Agata",
    "Izabela", "Wiktoria", "Julia", "Zuzanna", "Martyna", "Oliwia",
    # Dodatkowe imiona starszych pokoleń
    "Janina", "Genowefa", "Stanisława", "Wanda", "Stefania", "Henryka",
    "Bronisława", "Władysława", "Marianna", "Bożena", "Grażyna", "Urszula",
    # Dodatkowe imiona młodszych pokoleń
    "Maja", "Lena", "Alicja", "Amelia", "Nikola", "Gabriela",
    "Emilia", "Klaudia", "Kinga", "Dorota", "Patrycja", "Sylwia",
    "Renata", "Marta", "Aneta", "Jolanta", "Iwona", "Lucyna",
    "Kamila", "Weronika", "Milena", "Angelika", "Laura", "Kornelia",
    "Natasza", "Sara", "Hanna", "Lidia", "Adrianna", "Natalia",
]

# Polskie nazwiska (rozszerzona lista - 100+ najpopularniejszych)
POLISH_SURNAMES = [
    # Top 50 najczęstszych nazwisk
    "Nowak", "Kowalski", "Wiśniewski", "Wójcik", "Kowalczyk", "Kamiński",
    "Lewandowski", "Zieliński", "Szymański", "Woźniak", "Dąbrowski",
    "Kozłowski", "Jankowski", "Mazur", "Wojciechowski", "Kwiatkowski",
    "Krawczyk", "Kaczmarek", "Piotrowski", "Grabowski", "Pawłowski",
    "Michalski", "Król", "Nowakowski", "Wieczorek", "Majewski", "Olszewski",
    "Jaworski", "Wróbel", "Malinowski", "Adamczyk", "Dudek", "Stępień",
    "Górski", "Rutkowski", "Witkowski", "Walczak", "Sikora", "Baran",
    "Zawadzki", "Chmielewski", "Borkowski", "Sokołowski", "Sawicki",
    "Maciejewski", "Szczepański", "Kubiak", "Kalinowski", "Wysocki",
    # Dodatkowe 50+ nazwisk
    "Tomaszewski", "Marciniak", "Zalewski", "Jakubowski", "Pietrzak",
    "Włodarczyk", "Laskowski", "Laskowska", "Czarnecki", "Wilk",
    "Przybylski", "Ostrowski", "Błaszczyk", "Andrzejewski", "Wasilewski",
    "Kołodziej", "Cieślak", "Sadowski", "Markiewicz", "Gajewski",
    "Ziółkowski", "Czerwiński", "Zakrzewski", "Kowal", "Jabłoński",
    "Sobczak", "Urbaniak", "Krupa", "Kucharski", "Głowacki",
    "Szewczyk", "Krajewski", "Mróz", "Lisowski", "Adamski",
    "Lis", "Piątek", "Borowska", "Jasiński", "Kowalska",
    "Bednarek", "Tomczyk", "Kasprzak", "Makowski", "Baranowski",
    "Urbański", "Przybysz", "Nowicki", "Kuchta", "Szymczak",
    "Bielecki", "Wróblewski", "Konieczny", "Lewicki", "Mucha",
]

# Polskie style komunikacji
POLISH_COMMUNICATION_STYLES = [
    "bezpośredni i szczery",
    "ciepły i serdeczny",
    "powściągliwy i formalny",
    "humorystyczny i sarkastyczny",
    "emocjonalny i ekspresyjny",
    "rzeczowy i konkretny",
    "grzeczny i uprzejmy",
    "krytyczny i wymagający",
    "opiekuńczy i wspierający",
    "stanowczy i asertywny",
]

# Polskie style podejmowania decyzji
POLISH_DECISION_STYLES = [
    "ostrożny i przemyślany",
    "kieruje się doświadczeniem",
    "konsultuje się z rodziną",
    "bazuje na tradycji",
    "praktyczny i pragmatyczny",
    "impulsywny ale intuicyjny",
    "analizuje wszystkie opcje",
    "kieruje się emocjami",
    "szuka bezpiecznych rozwiązań",
    "odważny gdy ma pewność",
]

# Polskie przedziały dochodowe (netto miesięcznie, na podstawie danych GUS 2024)
POLISH_INCOME_BRACKETS = {
    "< 3 000 zł": 0.15,      # Najniższe zarobki, minimalna krajowa ~2800 zł netto
    "3 000 - 5 000 zł": 0.25, # Poniżej średniej krajowej
    "5 000 - 7 500 zł": 0.25, # Wokół średniej krajowej (~6500 zł netto)
    "7 500 - 10 000 zł": 0.18, # Powyżej średniej
    "10 000 - 15 000 zł": 0.12, # Wyższe zarobki (specjaliści, menedżerowie)
    "> 15 000 zł": 0.05,     # Najwyższe zarobki (kadra zarządzająca, eksperci IT)
}

# Polskie poziomy wykształcenia (na podstawie danych GUS)
POLISH_EDUCATION_LEVELS = {
    "Podstawowe": 0.08,                    # Wykształcenie podstawowe
    "Gimnazjalne": 0.05,                   # Gimnazjum (stary system)
    "Zasadnicze zawodowe": 0.18,          # Szkoła zawodowa
    "Średnie ogólnokształcące": 0.15,     # Liceum ogólnokształcące
    "Średnie techniczne": 0.20,           # Technikum
    "Policealne": 0.04,                   # Szkoła policealna
    "Wyższe licencjackie": 0.12,          # Licencjat
    "Wyższe magisterskie": 0.18,          # Magisterium
}
