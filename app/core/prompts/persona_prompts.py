"""
Prompty dla generowania person, JTBD, segmentów i orchestration.

Ten moduł zawiera wszystkie prompty używane w procesie generowania person:
- JTBD_ANALYSIS_PROMPT - Analiza Jobs-to-be-Done
- ORCHESTRATION_PROMPT_TEMPLATE - Orkiestracja alokacji person
- SEGMENT_NAME_PROMPT_TEMPLATE - Generowanie nazw segmentów
- SEGMENT_CONTEXT_PROMPT_TEMPLATE - Kontekst społeczny segmentów
- PERSONA_UNIQUENESS_PROMPT_TEMPLATE - "Dlaczego ta osoba jest wyjątkowa"

Użycie:
    from app.core.prompts.persona_prompts import JTBD_ANALYSIS_PROMPT
    prompt = JTBD_ANALYSIS_PROMPT.format(...)
"""

# ═══════════════════════════════════════════════════════════════════════════════
# JTBD ANALYSIS PROMPT (PersonaNeedsService)
# ═══════════════════════════════════════════════════════════════════════════════

JTBD_ANALYSIS_PROMPT_TEMPLATE = """You are a product strategist using Jobs-to-be-Done methodology.

Extract JTBD insights for:

**Profile:**
- {age}y, {occupation}
- Values: {values}
- Interests: {interests}
- Background: {background}
- Segment: {segment_name}{rag_section}

**Focus Group Insights (latest 10):**
{formatted_responses}

Generate:
1. Jobs-to-be-Done (format: "When [situation], I want [motivation], so I can [outcome]")
   - Ground in REAL problems from RAG context + focus group responses
2. Desired outcomes (importance 1-10, satisfaction 1-10, opportunity score)
   - Based on persona's actual life situation (not generic)
3. Pain points (severity 1-10, frequency, percent affected 0-1, quotes, solutions)
   - Use RAG context to identify REAL challenges (housing, income, career, etc.)

Base on provided data only. DO NOT invent generic problems."""

JTBD_RAG_SECTION_TEMPLATE = """

**Context from RAG (Market Research Data):**
{rag_context}

IMPORTANT: Use RAG context to understand the REAL problems and challenges this persona faces.
Ground your JTBD and pain points in the demographic/economic realities described in RAG context."""


# ═══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATION PROMPT (PersonaOrchestrationService)
# ═══════════════════════════════════════════════════════════════════════════════

ORCHESTRATION_PROMPT_TEMPLATE = """
Jesteś ekspertem od socjologii i badań społecznych w Polsce. Twoim zadaniem jest
przeanalizowanie Graph RAG context oraz celu projektu, a następnie stworzenie
szczegółowego, EDUKACYJNEGO planu alokacji {num_personas} syntetycznych person.

KLUCZOWE: SAM zdecydujesz jakie segmenty demograficzne wygenerować, bazując wyłącznie na:
- Celu projektu badawczego (project_description)
- Kontekście Graph RAG o polskim społeczeństwie
- Dodatkowym kontekście od użytkownika

NIE dostajesz z góry określonego rozkładu demograficznego - to TY decydujesz które grupy
są najbardziej relevantne dla badania!

=== STYL KOMUNIKACJI (KRYTYCZNY!) ===

WAŻNE: Twoim outputem będzie używany bezpośrednio przez innych agentów AI oraz
pokazywany użytkownikom w interfejsie. Dlatego MUSISZ:

[OK] **Konwersacyjny ton** - Mówisz jak kolega z zespołu, nie jak suchy raport
[OK] **Wyjaśniaj "dlaczego"** - Nie podawaj tylko faktów, ale ich znaczenie i kontekst
[OK] **Używaj przykładów z życia** - "Wyobraź sobie Annę z Warszawy, która..."
[OK] **Production-ready** - Treść może iść bezpośrednio do użytkownika bez edycji
[OK] **Edukacyjny** - User ma się UCZYĆ o polskim społeczeństwie, nie tylko dostać dane
[OK] **PO POLSKU** - Naturalnie, bez anglicyzmów gdzie niepotrzebne

    DŁUGOŚĆ BRIEFÓW: Każdy brief dla grupy demograficznej ma mieć 900-1200 znaków.
    To ma być edukacyjny mini-esej, który wyjaśnia kontekst społeczny bez lania wody.

=== DANE WEJŚCIOWE ===

**Projekt badawczy:**
{project_description}

**Dodatkowy kontekst od użytkownika:**
{additional_context}

**Liczba person do wygenerowania:** {num_personas}

{graph_context}

=== TWOJE ZADANIE ===

Przeprowadź głęboką socjologiczną analizę i stwórz plan alokacji person który zawiera:

### 1. OGÓLNY KONTEKST SPOŁECZNY (500-800 znaków)

Zrób overview polskiego społeczeństwa bazując na Graph RAG context:
- Jakie są kluczowe trendy demograficzne w Polsce?
- Co pokazują wskaźniki ekonomiczne (zatrudnienie, dochody, housing)?
- Jakie wartości i wyzwania ma polskie społeczeństwo 2025?
- Dlaczego to ma znaczenie dla generowania person?
- Dla kazdej osoby twórz opis dlaczego akurat do niej się to tyczy.

### 2. GRUPY DEMOGRAFICZNE Z DŁUGIMI BRIEFAMI

SAM zdecyduj jakie grupy demograficzne są najbardziej relevantne dla tego badania.
Bazuj na:
- Celu projektu (project_description)
- Trendach społecznych z Graph RAG
- Dodatkowym kontekście od użytkownika

Dla każdej wybranej grupy demograficznej, stwórz:

**Każdy brief MUSI zawierać (900-1200 znaków):**

a) **Dlaczego ta grupa?** (180-220 znaków)
   - Jaki % populacji stanowi ta grupa (z Graph RAG)
   - Dlaczego są ważni dla badania
   - Jak rozkład pasuje do realiów polskiego społeczeństwa
   - Statystyki z Graph RAG (magnitude, confidence)

b) **Kontekst zawodowy i życiowy** (260-320 znaków)
   - Typowe zawody dla tej grupy
   - Zarobki (realne liczby w PLN z Graph RAG jeśli dostępne)
   - Housing situation (własne/wynajem, ceny mieszkań)
   - Wyzwania ekonomiczne (kredyty, oszczędności, koszty życia)
   - Dlaczego tak jest? (społeczno-ekonomiczny kontekst)

c) **Wartości i aspiracje** (260-320 znaków)
   - Jakie wartości są ważne dla tej grupy (z badań społecznych)
   - Aspiracje i life goals
   - Dlaczego te wartości? (kontekst pokoleniowy, historyczny)
   - Jak zmienia się to w czasie (trendy)

d) **Typowe wyzwania i zainteresowania** (180-240 znaków)
   - Realne problemy życiowe tej grupy
   - Typowe hobby i sposób spędzania wolnego czasu
   - Dlaczego te zainteresowania pasują do profilu

e) **Segment Characteristics** (4-6 kluczowych cech tego segmentu)
   - Krótkie, mówiące cechy charakterystyczne dla tej grupy
   - Format: Lista stringów (np. ["Profesjonaliści z wielkich miast", "Wysoko wykształceni", "Stabilna kariera"])
   - Cechy powinny być KONKRETNE dla tej grupy (nie ogólne!)
   - Bazowane na demographics + insights z grafu

f) **Graph Insights** (structured data)
   - Lista 3-5 kluczowych wskaźników z Graph RAG
   - Każdy z wyjaśnieniem "why_matters"

g) **Allocation Reasoning**
   - Dlaczego tyle person w tej grupie (X z {num_personas})?
   - Jak to odnosi się do % populacji vs. relevance dla badania?

### 3. PRZYKŁAD DOBREGO BRIEFU

```
# Grupa: Kobiety 25-34, wyższe wykształcenie, Warszawa (6 person)

## Dlaczego ta grupa?

W polskim społeczeństwie kobiety 25-34 z wyższym wykształceniem stanowią
około 17.3% populacji miejskiej według danych GUS z 2022 roku. To fascynująca
grupa społeczna która znajduje się w momencie życia pełnym zmian - balansują
między budowaniem kariery a decyzjami o rodzinie, między niezależnością finansową
a realiami rynku nieruchomości.

Dla tego badania ta grupa jest kluczowa bo to oni są early adopters nowych
produktów i usług. Wskaźniki pokazują że 78.4% tej grupy jest zatrudnionych
(najwyższa stopa w Polsce!), co oznacza że mają purchasing power. Jednocześnie
63% wykazuje wysoką mobilność zawodową - często zmieniają pracę, co czyni ich
otwartymi na nowe rozwiązania.

## Kontekst zawodowy i życiowy

Warszawa koncentruje 35% polskiego rynku tech, fintech i consulting. Dla młodych
kobiet z wyższym wykształceniem to oznacza szeroki wybór możliwości kariery - od
project managerów przez UX designerów po analityków danych. Typowe zarobki w tej
grupie to 7000-12000 zł netto, co brzmi nieźle, ale...

...ale tu zaczyna się problem. Cena m2 w Warszawie to ~15000 zł. Dla osoby
zarabiającej 9000 zł netto (mediana), zakup 50m2 mieszkania wymaga odłożenia
~750000 zł, co przy oszczędzaniu 2000 zł miesięcznie daje... 31 lat. Nie dziwi
więc że 45% tej grupy wynajmuje mieszkania. To nie wybór stylu życia - to
konieczność ekonomiczna.

[... dalszy tekst 1000+ znaków ...]
```

=== OUTPUT FORMAT ===

Generuj JSON zgodny z tym schematem:

```json
{{
  "total_personas": {num_personas},
  "overall_context": "DŁUGI (500-800 znaków) overview polskiego społeczeństwa...",
  "groups": [
    {{
      "count": 6,
      "demographics": {{
        "age": "25-34",
        "gender": "kobieta",
        "education": "wyższe",
        "location": "Warszawa"
      }},
      "brief": "Edukacyjny brief (900-1200 znaków) jak w przykładzie...",
      "segment_characteristics": [
        "Profesjonaliści z wielkich miast",
        "Wysoko wykształceni",
        "Stabilna kariera",
        "Wysokie zaangażowanie społeczne"
      ],
      "graph_insights": [
        {{
          "type": "Wskaznik",
          "summary": "Stopa zatrudnienia kobiet 25-34 z wyższym",
          "magnitude": "78.4%",
          "confidence": "high",
          "time_period": "2022",
          "source": "GUS",
          "why_matters": "Wysoka stopa zatrudnienia oznacza że ta grupa ma..."
        }}
      ],
      "allocation_reasoning": "Dlaczego 6 z {num_personas}? Bo ta grupa stanowi..."
    }}
  ]
}}
```

KLUCZOWE ZASADY:

1. **Briefe mają być KONKRETNE** (900-1200 znaków każdy) - mini-eseje, nie listy
2. **Wyjaśniaj "dlaczego"** dla WSZYSTKIEGO - user ma się uczyć
3. **Konwersacyjny ton** - jak kolega tłumaczy przy kawie, nie jak raport naukowy
4. **Używaj danych z Graph RAG** - magnitude, confidence, time_period, sources
5. **Production-ready** - ten output idzie bezpośrednio do użytkowników
6. **Realne liczby** - PLN, %, lata, konkretne wskaźniki (nie "wysoki" ale "78.4%")
7. **Kontekst społeczny** - wyjaśniaj TŁO (historia, ekonomia, trendy)

Generuj plan alokacji:
"""


# ═══════════════════════════════════════════════════════════════════════════════
# SEGMENT NAME GENERATION (PersonaOrchestrationService)
# ═══════════════════════════════════════════════════════════════════════════════

SEGMENT_NAME_PROMPT_TEMPLATE = """Stwórz trafną, MÓWIĄCĄ nazwę dla poniższego segmentu demograficznego.

DANE SEGMENTU:
- Wiek: {age_range}
- Płeć: {gender}
- Wykształcenie: {education}
- Dochód: {income}

INSIGHTS Z GRAFU:
{insights_text}

CYTATY Z RAG:
{citations_text}

ZASADY:
1. Nazwa powinna być 2-4 słowa (np. "Młodzi Prekariusze", "Aspirujące Profesjonalistki 35-44")
2. Oddaje kluczową charakterystykę grupy (wiek + status społeczno-ekonomiczny)
3. Używa polskiego języka, brzmi naturalnie
4. Bazuje na insightach (np. jeśli grupa ma niskie dochody + młody wiek → "Młodzi Prekariusze")
5. Unikaj ogólników ("Grupa A", "Segment 1")
6. Jeśli wiek jest istotny, włącz go (np. "35-44")

PRZYKŁADY DOBRYCH NAZW:
- "Młodzi Prekariusze" (18-24, niskie dochody)
- "Aspirujące Profesjonalistki 35-44" (kobiety, wyższe wykształcenie, średnie dochody)
- "Dojrzali Eksperci" (45-54, wysokie dochody, stabilna kariera)
- "Początkujący Profesjonaliści" (25-34, pierwsze kroki w karierze)

ZWRÓĆ TYLKO NAZWĘ (bez cudzysłowów, bez dodatkowych wyjaśnień):"""


# ═══════════════════════════════════════════════════════════════════════════════
# SEGMENT CONTEXT GENERATION (PersonaOrchestrationService)
# ═══════════════════════════════════════════════════════════════════════════════

SEGMENT_CONTEXT_PROMPT_TEMPLATE = """Stwórz kontekst społeczny dla segmentu "{segment_name}".

DEMOGRAFIA SEGMENTU:
- Wiek: {age_range}
- Płeć: {gender}
- Wykształcenie: {education}
- Dochód: {income}

INSIGHTS Z GRAFU WIEDZY:
{insights_text}

CYTATY Z RAG:
{citations_text}

CEL PROJEKTU:
{project_goal}

WYTYCZNE:
1. Długość: 500-800 znaków (WAŻNE!)
2. Kontekst SPECYFICZNY dla KONKRETNEJ GRUPY (nie ogólny opis Polski!)
3. Zacznij od opisu charakterystyki grupy (jak w przykładzie)
4. Struktura:
   a) Pierwsza część (2-3 zdania): KIM są te osoby, co ich charakteryzuje
   b) Druga część (2-3 zdania): Ich WARTOŚCI i ASPIRACJE
   c) Trzecia część (2-3 zdania): WYZWANIA i kontekst ekonomiczny z konkretnymi liczbami
5. Ton: konkretny, praktyczny, opisujący TYCH ludzi (nie teoretyczny!)
6. Używaj konkretnych liczb z insights tam gdzie dostępne
7. Unikaj: ogólników ("polska społeczeństwo"), teoretyzowania

PRZYKŁAD DOBREGO KONTEKSTU (na wzór Figmy):
"Tech-Savvy Profesjonaliści to osoby w wieku 28 lat, pracujące jako Marketing Manager w dużych miastach jak Warszawa czy Kraków. Charakteryzują się wysokim wykształceniem (licencjat lub wyżej), stabilną karierą w branży technologicznej i dochodami 8k-12k PLN netto. Są early adopters nowych technologii i cenią sobie work-life balance. Ich główne wartości to innovation, ciągły rozwój i sustainability. Aspirują do awansu na wyższe stanowiska (senior manager, director), własnego mieszkania w atrakcyjnej lokalizacji (co przy cenach 15-20k PLN/m2 wymaga oszczędzania przez 10+ lat) i rozwoju kompetencji w digital marketing oraz AI tools. Wyzwania: rosnąca konkurencja na rynku pracy (według GUS 78% osób z tej grupy ma wyższe wykształcenie), wysokie koszty życia w dużych miastach (średni czynsz ~3500 PLN), presja na ciągły rozwój i keeping up with tech trends."

WAŻNE: Pisz o KONKRETNEJ grupie ludzi, używaj przykładów zawodów, konkretnych liczb, opisuj ICH życie.

ZWRÓĆ TYLKO KONTEKST (bez nagłówków, bez komentarzy, 500-800 znaków):"""


# ═══════════════════════════════════════════════════════════════════════════════
# SEGMENT BRIEF GENERATION (NEW - SegmentBriefService)
# Długi, ciekawy, personalny opis segmentu (400-800 słów)
# ═══════════════════════════════════════════════════════════════════════════════

SEGMENT_BRIEF_PROMPT_TEMPLATE = """Stwórz fascynujący opis segmentu społecznego, z którym czytający może się utożsamić.

DEMOGRAFIA SEGMENTU:
- Nazwa segmentu: {segment_name}
- Wiek: {age_range}
- Płeć: {gender}
- Wykształcenie: {education}
- Lokalizacja: {location}
- Dochód: {income}

KONTEKST RAG (dane społeczne z Polski):
{rag_context}

PRZYKŁADOWE PERSONY Z TEGO SEGMENTU (jeśli istnieją):
{example_personas}

ZADANIE:
Napisz DŁUGI (400-800 słów), CIEKAWY, PERSONALNY opis tego segmentu społecznego.

STRUKTURA (4 sekcje):

1. **Kim są ci ludzie?** (100-150 słów)
   - W jakim momencie życia się znajdują?
   - Co jest dla nich typowe? (praca, życie, relacje)
   - Jakie mają wykształcenie i doświadczenie?
   - Napisz tak, żeby czytelnik pomyślał "Znam takich ludzi!" lub "To ja!"

2. **Kontekst zawodowy i ekonomiczny** (150-200 słów)
   - Jakie zawody wykonują? (konkretne przykłady)
   - Ile zarabiają? (realne liczby w PLN)
   - Jak wygląda ich sytuacja mieszkaniowa? (własne/wynajem, ceny)
   - Jakie mają wyzwania finansowe? (kredyty, oszczędności, koszty życia)
   - Dlaczego tak jest? (kontekst społeczno-ekonomiczny)
   - Używaj KONKRETNYCH LICZB z RAG context!

3. **Wartości i aspiracje** (100-150 słów)
   - Co jest dla nich ważne w życiu?
   - Do czego dążą? (career goals, life goals)
   - Dlaczego te wartości? (kontekst pokoleniowy)
   - Jak się to zmienia w czasie? (trendy)
   - Pisz o EMOCJACH i MOTIVACJACH, nie tylko faktach!

4. **Typowe wyzwania i zainteresowania** (50-100 słów)
   - Jakie mają realne problemy życiowe?
   - Co robią w wolnym czasie?
   - Dlaczego te zainteresowania pasują do profilu?

TON I STYL:
- Pisz jak storyteller, nie jak statystyk!
- Używaj przykładów z życia (imiona, sytuacje, dialogi wewnętrzne)
- Używaj KONKRETNYCH LICZB (nie "wysokie zarobki" ale "8-12k PLN netto")
- Pisz tak, żeby czytelnik mógł się UTOŻSAMIĆ lub ROZPOZNAĆ tych ludzi
- Unikaj: ogólników, suchych statystyk, teoretyzowania
- To ma być HISTORIA tego segmentu, nie raport demograficzny!

PRZYKŁAD DOBREGO STYLU:
"Wiktor ma 29 lat i właśnie skończył historię sztuki na UAM. Marzył o karierze w świecie kultury, ale rzeczywistość okazała się trudna. Po serii bezpłatnych staży znalazł pracę jako asystent w małej fundacji – 3200 zł netto ledwo pokrywa pokój na Jeżycach (1400 zł) i podstawowe koszty. Ta niestabilność finansowa, mimo wyższego wykształcenia, to źródło ciągłego stresu. Czuje się zagubiony w oczekiwaniach rówieśników, którzy mają stabilne etaty i własne mieszkania..."

ZWRÓĆ TYLKO OPIS SEGMENTU (400-800 słów, bez nagłówków sekcji, płynny tekst):"""


# ═══════════════════════════════════════════════════════════════════════════════
# PERSONA UNIQUENESS (NEW - SegmentBriefService)
# "Dlaczego ta osoba jest wyjątkowa w swoim segmencie"
# ═══════════════════════════════════════════════════════════════════════════════

PERSONA_UNIQUENESS_PROMPT_TEMPLATE = """Opisz, czym {persona_name} wyróżnia się w segmencie "{segment_name}".

PROFIL PERSONY:
- Imię i nazwisko: {persona_name}
- Wiek: {age}
- Zawód: {occupation}
- Background: {background_story}
- Wartości: {values}
- Zainteresowania: {interests}

TYPOWY PRZEDSTAWICIEL SEGMENTU (Brief):
{segment_brief_summary}

ZADANIE:
Napisz 3-4 akapity (250-400 słów) szczegółowo opisujące:
- Co czyni {persona_name} NIETYPOWĄ/NIETYPOWYM dla tego segmentu?
- Jakie ma unikalne doświadczenia, perspektywy lub życiowe wybory?
- Dlaczego jest ciekawym case study?
- Co go/ją wyróżnia spośród innych osób w tym segmencie?
- Jakie konkretne wydarzenia, decyzje lub wartości czynią tę osobę wyjątkową?

STRUKTURA (3-4 akapity):
1. **Główny kontrast** (60-80 słów): Zacznij od jasnego pokazania, czym {persona_name} różni się od typowego przedstawiciela segmentu. Użyj konkretnych przykładów z jej/jego życia.
2. **Życiowa droga i wybory** (80-120 słów): Opisz kluczowe decyzje życiowe, które uczyniły tę osobę wyjątkową. Dlaczego podjęła te decyzje? Jakie były konsekwencje?
3. **Wartości i motywacje** (60-80 słów): Pokaż, jakie wartości lub przekonania wyróżniają tę osobę. Jak wpływają one na jej codzienne życie i wybory?
4. **Perspektywa przyszłości** (opcjonalnie, 40-60 słów): Jak ta unikalność może wpłynąć na przyszłe decyzje czy reakcje tej osoby?

ZASADY:
1. Bądź BARDZO KONKRETNY - używaj faktów z profilu, dat, liczb, konkretnych wydarzeń
2. Pisz jak storyteller - pokaż EMOCJE, wewnętrzne dylematy, motywacje
3. Porównuj z TYPOWYM przedstawicielem segmentu ("Podczas gdy większość..., {persona_name}...")
4. Używaj imienia persony w każdym akapicie (nie "ta osoba")
5. Pisz PO POLSKU, naturalnie, konwersacyjnie
6. 250-400 słów (3-4 rozwinięte akapity)

PRZYKŁAD DOBREGO OPISU (3-4 akapity):
"Wiktor wyróżnia się w grupie Młodych Prekariuszy swoją determinacją do pozostania w sektorze kultury pomimo chronicznych trudności finansowych. Podczas gdy 73% jego rówieśników z wykształceniem humanistycznym ostatecznie przechodzi do korporacji lub sektora IT dla stabilności, Wiktor świadomie wybiera pracę w małej fundacji za 3200 zł netto. Ta decyzja nie wynika z braku alternatyw - wielokrotnie dostawał oferty z większym wynagrodzeniem w marketingu czy corporate communications, ale za każdym razem odmawiał.

Kluczowym momentem w życiu Wiktora był rok 2022, kiedy po serii bezpłatnych staży w galeriach sztuki stanął przed wyborem: przyjąć stabilną posadę w banku (oferta od znajomego z uczelni, 8500 zł na start) czy kontynuować niepewną ścieżkę w sektorze kultury. Zdecydował się na to drugie, mimo że właśnie zaczął wynajmować pokój na Jeżycach za 1400 zł i miał ledwo 200 zł oszczędności. Rodzice nie rozumieli tej decyzji, co prowadziło do wielomiesięcznego napięcia w relacjach. Wiktor jednak twierdzi, że nie wyobraża sobie robienia czegoś 'tylko dla pieniędzy' - jego praca nad projektami edukacyjnymi w galerii daje mu poczucie sensu, którego nie zastąpi żadna pensja.

Ta niezwykła konsekwencja w podążaniu za pasją wpływa na każdy aspekt życia Wiktora. Rezygnuje z wyjść z przyjaciółmi, bo nie stać go na restauracje. Nie myśli o własnym mieszkaniu czy założeniu rodziny, co dla większości 29-latków z wyższym wykształceniem jest już realnym planem. Ale jednocześnie czuje głęboką satysfakcję z tego, co robi - ostatni projekt edukacyjny dotarł do 500 dzieci z warszawskich szkół podstawowych. Wiktor mówi, że to jest jego 'prawdziwe bogactwo'.

Patrząc w przyszłość, Wiktor nie planuje zmian - chce rozwijać sektor kultury od środka, walczyć o lepsze finansowanie, może kiedyś założyć własną fundację. Jest świadomy, że ta droga może oznaczać lata finansowej niepewności, ale wierzy, że wartości i pasja są ważniejsze niż material security. To podejście czyni go nietypowym przedstawicielem swojego pokolenia - idealistą w czasach, gdy większość wybrała pragmatyzm."

ZWRÓĆ TYLKO OPIS (250-400 słów, 3-4 akapity, bez nagłówków sekcji):"""


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def build_jtbd_prompt(
    age: int,
    occupation: str,
    values: str,
    interests: str,
    background: str,
    segment_name: str,
    formatted_responses: str,
    rag_context: str = None
) -> str:
    """Helper do budowania JTBD analysis prompt."""
    rag_section = ""
    if rag_context:
        truncated_rag = (rag_context[:800] + "...") if len(rag_context) > 800 else rag_context
        rag_section = JTBD_RAG_SECTION_TEMPLATE.format(rag_context=truncated_rag)

    return JTBD_ANALYSIS_PROMPT_TEMPLATE.format(
        age=age,
        occupation=occupation,
        values=values,
        interests=interests,
        background=background,
        segment_name=segment_name,
        rag_section=rag_section,
        formatted_responses=formatted_responses
    )
