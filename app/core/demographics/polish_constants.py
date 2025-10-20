"""
Polskie stałe demograficzne dla Sight.

Wszystkie wartości bazują na danych GUS (Główny Urząd Statystyczny) oraz
badaniach społecznych przeprowadzonych w Polsce (2022-2024).

Użycie:
    from app.core.demographics.polish_constants import POLISH_MALE_NAMES, POLISH_LOCATIONS
"""

# ═══════════════════════════════════════════════════════════════════════════════
# ROZKŁAD GEOGRAFICZNY
# ═══════════════════════════════════════════════════════════════════════════════

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

# ═══════════════════════════════════════════════════════════════════════════════
# WARTOŚCI I CECHY KULTUROWE
# ═══════════════════════════════════════════════════════════════════════════════

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

# ═══════════════════════════════════════════════════════════════════════════════
# ZAINTERESOWANIA I HOBBY
# ═══════════════════════════════════════════════════════════════════════════════

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

# ═══════════════════════════════════════════════════════════════════════════════
# ZAWODY (rozkład proporcjonalny)
# ═══════════════════════════════════════════════════════════════════════════════

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
    "Magazynier": 0.02,
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

# ═══════════════════════════════════════════════════════════════════════════════
# IMIONA (mix pokoleń)
# ═══════════════════════════════════════════════════════════════════════════════

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

# ═══════════════════════════════════════════════════════════════════════════════
# NAZWISKA (100+ najpopularniejszych)
# ═══════════════════════════════════════════════════════════════════════════════

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

# ═══════════════════════════════════════════════════════════════════════════════
# DOCHODY (netto miesięcznie, PLN, na podstawie GUS 2024)
# ═══════════════════════════════════════════════════════════════════════════════

POLISH_INCOME_BRACKETS = {
    "< 3 000 zł": 0.15,      # Najniższe zarobki, minimalna krajowa ~2800 zł netto
    "3 000 - 5 000 zł": 0.25, # Poniżej średniej krajowej
    "5 000 - 7 500 zł": 0.25, # Wokół średniej krajowej (~6500 zł netto)
    "7 500 - 10 000 zł": 0.18, # Powyżej średniej
    "10 000 - 15 000 zł": 0.12, # Wyższe zarobki (specjaliści, menedżerowie)
    "> 15 000 zł": 0.05,     # Najwyższe zarobki (kadra zarządzająca, eksperci IT)
}

# ═══════════════════════════════════════════════════════════════════════════════
# WYKSZTAŁCENIE (na podstawie GUS)
# ═══════════════════════════════════════════════════════════════════════════════

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

# ═══════════════════════════════════════════════════════════════════════════════
# STYLE KOMUNIKACJI I DECYZYJNOŚCI (polskie cechy)
# ═══════════════════════════════════════════════════════════════════════════════

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
