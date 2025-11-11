"""
Moduł zawierający szablony promptów dla generowania person

Zawiera:
- create_persona_prompt() - pełny prompt z Big Five, few-shot examples, RAG context
- create_segment_persona_prompt() - prompt dla person z segmentów z enforce demographics
- _format_rag_context() - helper do formatowania kontekstu RAG
"""

import numpy as np
from typing import Dict, Any, Optional, List


def create_persona_prompt(
    demographic: dict[str, Any],
    psychological: dict[str, Any],
    demographics_config,
    rng: np.random.Generator,
    rag_context: str | None = None,
    target_audience_description: str | None = None,
    orchestration_brief: str | None = None
) -> str:
    """
    Utwórz prompt dla LLM do generowania persony - WERSJA POLSKA

    Tworzy szczegółowy prompt zawierający:
    - Dane demograficzne i psychologiczne
    - Interpretację cech Big Five i Hofstede PO POLSKU
    - 3 przykłady few-shot z polskimi personami
    - Opcjonalny kontekst RAG z bazy wiedzy o polskim społeczeństwie
    - Opcjonalny dodatkowy opis grupy docelowej od użytkownika
    - Opcjonalny orchestration brief (900-1200 znaków) od Gemini 2.5 Pro
    - Instrukcje jak stworzyć unikalną polską personę

    Args:
        demographic: Profil demograficzny (wiek, płeć, edukacja, etc.)
        psychological: Profil psychologiczny (Big Five + Hofstede)
        demographics_config: Obiekt demographics z config (dla imion/nazwisk)
        rng: NumPy random generator
        rag_context: Opcjonalny kontekst z RAG (fragmenty z dokumentów)
        target_audience_description: Opcjonalny dodatkowy opis grupy docelowej
        orchestration_brief: Opcjonalny DŁUGI brief od orchestration agent (Gemini 2.5 Pro)

    Returns:
        Pełny tekst prompta gotowy do wysłania do LLM (po polsku)
    """

    # Generuj unikalny seed dla tej persony (do różnicowania)
    persona_seed = rng.integers(1000, 9999)

    # Losuj polskie imię i nazwisko dla większej różnorodności
    gender_lower = demographic.get('gender', 'male').lower()
    if 'female' in gender_lower or 'kobieta' in gender_lower:
        suggested_first_name = rng.choice(demographics_config.poland.female_names)
    else:
        suggested_first_name = rng.choice(demographics_config.poland.male_names)
    suggested_surname = rng.choice(demographics_config.poland.surnames)

    if demographic.get('age'):
        headline_age_rule = f"• HEADLINE: Musi zawierać liczbę {demographic['age']} lat i realną motywację tej osoby.\n"
    elif demographic.get('age_group'):
        headline_age_rule = (
            f"• HEADLINE: Podaj konkretną liczbę lat zgodną z przedziałem {demographic['age_group']} "
            "i pokaż realną motywację tej osoby.\n"
        )
    else:
        headline_age_rule = "• HEADLINE: Podaj konkretny wiek w latach i realną motywację tej osoby.\n"

    # Pobierz wartości Big Five (interpretację robi LLM)
    openness_val = psychological.get('openness', 0.5)
    conscientiousness_val = psychological.get('conscientiousness', 0.5)
    extraversion_val = psychological.get('extraversion', 0.5)
    agreeableness_val = psychological.get('agreeableness', 0.5)
    neuroticism_val = psychological.get('neuroticism', 0.5)

    # Unified context section (merge RAG + Target Audience + Orchestration Brief)
    unified_context = ""
    if rag_context or target_audience_description or orchestration_brief:
        context_parts = []

        if rag_context:
            context_parts.append(f"📊 KONTEKST RAG:\n{rag_context}")
        if orchestration_brief and orchestration_brief.strip():
            context_parts.append(f"📋 ORCHESTRATION BRIEF:\n{orchestration_brief.strip()}")
        if target_audience_description and target_audience_description.strip():
            context_parts.append(f"🎯 GRUPA DOCELOWA:\n{target_audience_description.strip()}")

        unified_context = f"""
═══════════════════════════════════════════
KONTEKST (RAG + Brief + Audience):
═══════════════════════════════════════════

{chr(10).join(context_parts)}

⚠️ KLUCZOWE ZASADY:
• Użyj kontekstu jako TŁA życia persony (nie cytuj statystyk!)
• Stwórz FASCYNUJĄCĄ historię - kontekst to fundament, nie lista faktów
• Wskaźniki → konkretne detale życia (housing crisis → wynajmuje, oszczędza)
• Trendy → doświadczenia życiowe (mobilność → zmiana 3 prac w 5 lat)
• Naturalność: "Jak wielu rówieśników..." zamiast "67% absolwentów..."

═══════════════════════════════════════════

"""

    return f"""Expert: Syntetyczne persony dla polskiego rynku - UNIKALNE, REALISTYCZNE, SPÓJNE.

{unified_context}PERSONA #{persona_seed}: {suggested_first_name} {suggested_surname}

PROFIL:
• Wiek: {demographic.get('age_group')} | Płeć: {demographic.get('gender')} | Lokalizacja: {demographic.get('location')}
• Wykształcenie: {demographic.get('education_level')} | Dochód: {demographic.get('income_bracket')}

OSOBOWOŚĆ (Big Five - wartości 0-1):
• Otwartość (Openness): {openness_val:.2f}
• Sumienność (Conscientiousness): {conscientiousness_val:.2f}
• Ekstrawersja (Extraversion): {extraversion_val:.2f}
• Ugodowość (Agreeableness): {agreeableness_val:.2f}
• Neurotyzm (Neuroticism): {neuroticism_val:.2f}

Interpretacja Big Five: <0.4 = niskie, 0.4-0.6 = średnie, >0.6 = wysokie.
Wykorzystaj te wartości do stworzenia spójnej osobowości i historii życiowej.

HOFSTEDE (wartości 0-1): PD={psychological.get('power_distance', 0.5):.2f} | IND={psychological.get('individualism', 0.5):.2f} | UA={psychological.get('uncertainty_avoidance', 0.5):.2f}

ZASADY:
• Zawód = wykształcenie + dochód
• Osobowość → historia (O→podróże, S→planowanie)
• Detale: dzielnice, marki, konkretne hobby
• UNIKALNOŚĆ: Każda persona MUSI mieć RÓŻNĄ historię życiową - nie kopiuj opisów!
• Background_story NIE może kopiować briefu segmentu ani powtarzać całych akapitów z kontekstu
{headline_age_rule}• Pokaż codzienne wybory i motywacje tej osoby - zero ogólników

⚠️ CATCHY SEGMENT NAME (2-4 słowa):
Wygeneruj krótką, chwytliwą nazwę marketingową dla segmentu tej persony.
• Powinna odzwierciedlać wiek, wartości, styl życia, status ekonomiczny
• Przykłady: "Pasywni Liberałowie", "Młodzi Prekariusze", "Aktywni Seniorzy", "Cyfrowi Nomadzi", "Stabilni Tradycjonaliści"
• UNIKAJ długich opisów technicznych jak "Kobiety 35-44 wyższe wykształcenie"
• Polski język, kulturowo relevantne, konkretne

PRZYKŁAD (z rozbudowanym background_story):
{{"full_name": "Marek Kowalczyk", "catchy_segment_name": "Stabilni Tradycjonaliści", "persona_title": "Główny Księgowy", "headline": "Poznański księgowy (56) planujący emeryturę", "background_story": "Marek zaczął swoją karierę w latach 90., kiedy polska gospodarka przechodziła transformację. Po ukończeniu ekonomii na UAM w Poznaniu, dostał pracę w lokalnej firmie produkcyjnej jako młodszy księgowy. Przez 28 lat z zaangażowaniem budował struktury finansowe firmy, przechodząc od ręcznych ksiąg rachunkowych do nowoczesnych systemów ERP. Pamięta czasy hiperinflacji, kiedy ceny zmieniały się z dnia na dzień - to ukształtowało jego konserwatywne podejście do finansów.\\n\\nW życiu prywatnym stabilność była dla niego priorytetem. Ożenił się z Anną, koleżanką ze studiów, i razem wychowali dwoje dzieci - córkę Kasię (dziś prawniczkę w Warszawie) i syna Tomka (inżyniera we Wrocławiu). Trzy lata temu, po latach oszczędzania, spełnił marzenie i kupił działkę pod Poznaniem. Każdy weekend spędza tam, budując dom na emeryturę - to jego sposób na relaks i ucieczkę od codziennych obowiązków.\\n\\nMarek jest również skarbnikiem parafii w swojej dzielnicy. Pilnuje każdego grosza w budżecie kościoła, co czasami prowadzi do konfliktów z proboszczem, który ma bardziej 'wizjonerskie' podejście do wydatków. Ale Marek nie ustępuje - wie, że jego konserwatywne podejście chroni wspólnotę przed nieprzemyślanymi decyzjami.\\n\\nTeraz, na rok przed emeryturą, Marek czuje mieszankę ulgi i niepokoju. Z jednej strony cieszy się na czas dla siebie, wędkowanie i dokończenie domu. Z drugiej martwi się, czy jego emerytura (około 3500 zł netto) wystarczy na godne życie, zwłaszcza przy rosnącej inflacji. Obserwuje też z niepokojem, jak zmienia się świat - digitalizacja, którą wspierał w firmie, teraz wydaje mu się obca. Często zastanawia się, czy jego dzieci poradzą sobie w tym szybko zmieniającym się świecie.", "values": ["Stabilność", "Lojalność", "Rodzina", "Odpowiedzialność", "Oszczędność"], "interests": ["Wędkarstwo", "Majsterkowanie", "Grillowanie", "Historia Polski", "Budowa domu"], "communication_style": "formalny, face-to-face, ceni bezpośrednie rozmowy", "decision_making_style": "metodyczny, analityczny, unika ryzyka, bazuje na doświadczeniu", "typical_concerns": ["Wysokość emerytury i inflacja", "Zdrowie i dostęp do opieki medycznej", "Przyszłość dzieci", "Zakończenie budowy domu", "Cyfryzacja i nowe technologie"]}}

⚠️ KRYTYCZNE: Generuj KOMPLETNIE INNĄ personę z UNIKALNĄ historią życiową!
• NIE kopiuj ogólnych opisów segmentu do background_story
• Fokus na TEJ KONKRETNEJ OSOBY, jej specyficznych doświadczeniach
• Użyj persona_seed #{persona_seed} jako źródło różnorodności

WYŁĄCZNIE JSON (bez markdown):
{{
  "full_name": "<polskie imię+nazwisko>",
  "catchy_segment_name": "<2-4 słowa, krótka marketingowa nazwa segmentu>",
  "persona_title": "<zawód/etap życia>",
  "headline": "<1 zdanie: wiek, zawód, UNIKALNE motywacje>",
  "background_story": "<3-5 akapitów (400-600 słów): SZCZEGÓŁOWA historia TEJ OSOBY - jej życie, kariera, wyzwania, aspiracje, konkretne wydarzenia. Pokaż jej drogę życiową, kluczowe decyzje, obecną sytuację i marzenia. Każdy akapit powinien pokazywać inny aspekt jej życia (przeszłość, praca, relacje, wyzwania, cele). Pisz jak storyteller - używaj konkretnych detali, emocji, wewnętrznych dylemotów.>",
  "values": ["<5-7 wartości>"],
  "interests": ["<5-7 hobby/aktywności>"],
  "communication_style": "<jak się komunikuje>",
  "decision_making_style": "<jak podejmuje decyzje>",
  "typical_concerns": ["<3-5 SPECYFICZNYCH zmartwień/priorytetów>"]
}}"""


def create_segment_persona_prompt(
    demographic: dict[str, Any],
    psychological: dict[str, Any],
    segment_name: str,
    segment_context: str,
    demographics_config,
    rng: np.random.Generator,
    graph_insights: list[Any] = None,
    rag_citations: list[Any] = None
) -> str:
    """
    Utwórz prompt dla persony generowanej z segmentu

    Args:
        demographic: Profil demograficzny (ENFORCE - nie losowany!)
        psychological: Profil psychologiczny (Big Five + Hofstede)
        segment_name: Nazwa segmentu (np. "Młodzi Prekariusze")
        segment_context: Kontekst społeczny segmentu
        demographics_config: Obiekt demographics z config (dla imion/nazwisk)
        rng: NumPy random generator
        graph_insights: Insights filtrowane dla segmentu
        rag_citations: High-quality RAG citations

    Returns:
        Pełny tekst prompta gotowy do wysłania do LLM
    """

    # Suggest Polish name
    gender_lower = demographic.get('gender', 'kobieta').lower()
    if 'female' in gender_lower or 'kobieta' in gender_lower:
        suggested_first_name = rng.choice(demographics_config.poland.female_names)
    else:
        suggested_first_name = rng.choice(demographics_config.poland.male_names)
    suggested_surname = rng.choice(demographics_config.poland.surnames)

    age = demographic.get('age', 30)

    # Generate unique persona seed for diversity
    persona_seed = rng.integers(1000, 9999)

    # Format insights
    insights_text = ""
    if graph_insights:
        insights_text = "\n".join([
            f"- {ins.get('summary', ins.get('streszczenie', 'N/A'))}"
            for ins in graph_insights[:5]
        ])

    return f"""Wygeneruj realistyczną personę dla segmentu "{segment_name}".

CONSTRAINTS (MUSISZ PRZESTRZEGAĆ!):
• Wiek: {age} lat
• Płeć: {demographic.get('gender')}
• Wykształcenie: {demographic.get('education_level')}
• Dochód: {demographic.get('income_bracket')}
• Lokalizacja: {demographic.get('location')}

KONTEKST SEGMENTU:
{segment_context}

INSIGHTS:
{insights_text or "Brak insights"}

OSOBOWOŚĆ (Big Five):
• Otwartość: {psychological.get('openness', 0.5):.2f}
• Sumienność: {psychological.get('conscientiousness', 0.5):.2f}
• Ekstrawersja: {psychological.get('extraversion', 0.5):.2f}

ZASADY:
• Persona MUSI pasować do constraints
• Zawód = wykształcenie + dochód
• Używaj kontekstu jako tła (nie cytuj statystyk!)
• UNIKALNOŚĆ: Każda persona w segmencie MUSI mieć RÓŻNĄ historię życiową!
• HEADLINE: Musi zawierać liczbę {age} lat i realną motywację tej osoby
• Background_story NIE może kopiować briefu segmentu ani powtarzać całych akapitów z kontekstu
• Pokaż codzienne wybory i motywacje tej osoby - zero ogólników

⚠️ CATCHY SEGMENT NAME (2-4 słowa):
Wygeneruj krótką, chwytliwą nazwę marketingową dla tego segmentu.
• Powinna odzwierciedlać wiek, wartości, styl życia, status ekonomiczny
• Przykłady: "Pasywni Liberałowie", "Młodzi Prekariusze", "Aktywni Seniorzy", "Cyfrowi Nomadzi"
• UNIKAJ długich opisów technicznych jak "Kobiety 35-44 wyższe wykształcenie"
• Polski język, kulturowo relevantne

⚠️ KRYTYCZNE: Generuj UNIKALNĄ personę (Persona #{persona_seed})!
• NIE kopiuj ogólnych opisów segmentu do background_story
• Fokus na TEJ KONKRETNEJ OSOBY, jej specyficznych doświadczeniach
• Każda persona w segmencie ma INNĄ historię życiową, inne detale, różne zainteresowania

ZWRÓĆ JSON:
{{
  "full_name": "{suggested_first_name} {suggested_surname}",
  "catchy_segment_name": "<2-4 słowa, krótka marketingowa nazwa segmentu>",
  "persona_title": "<zawód>",
  "headline": "<{age} lat, zawód, UNIKALNE motywacje>",
  "background_story": "<2-3 zdania: KONKRETNA historia TEJ OSOBY - nie ogólny opis segmentu!>",
  "values": ["<5-7 wartości>"],
  "interests": ["<5-7 hobby>"],
  "communication_style": "<styl>",
  "decision_making_style": "<styl>",
  "typical_concerns": ["<3-5 SPECYFICZNYCH zmartwień>"]
}}"""


def _format_rag_context(rag_context: str) -> str:
    """
    Formatuj kontekst RAG dla lepszej czytelności w promptach

    Args:
        rag_context: Raw kontekst z RAG service

    Returns:
        Sformatowany kontekst gotowy do wstawienia w prompt
    """
    if not rag_context:
        return ""

    # Dodaj prefix i formatowanie
    return f"""
═══════════════════════════════════════════
KONTEKST Z BAZY WIEDZY (RAG):
═══════════════════════════════════════════

{rag_context.strip()}

⚠️ KLUCZOWE ZASADY:
• Użyj kontekstu jako TŁA życia persony (nie cytuj statystyk!)
• Stwórz FASCYNUJĄCĄ historię - kontekst to fundament, nie lista faktów
• Wskaźniki → konkretne detale życia (housing crisis → wynajmuje, oszczędza)
• Trendy → doświadczenia życiowe (mobilność → zmiana 3 prac w 5 lat)
• Naturalność: "Jak wielu rówieśników..." zamiast "67% absolwentów..."

═══════════════════════════════════════════
"""
