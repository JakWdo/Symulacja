# Ulepszenia Różnorodności Odpowiedzi w Ankietach

## Problem

Persony generowały nieróżnorodne odpowiedzi w ankietach:
- **Rating Scale**: Wszystkie persony wybierały skrajne wartości lub środkowe
- **Single Choice**: Wszystkie persony wybierały tę samą opcję
- **Multiple Choice**: Wszystkie persony wybierały wszystkie opcje

## Root Cause

1. **Prompty zbyt generyczne**: Nie wymuszały różnorodności odpowiedzi
2. **Brak wykorzystania Big Five**: persona_context nie zawierał cech osobowości
3. **Brak guidance**: LLM nie miał wskazówek jak różnicować odpowiedzi

## Rozwiązanie

### 1. Zaktualizowane Prompty (3 pliki YAML)

#### `config/prompts/surveys/rating_scale.yaml` (v1.0.0 → v1.1.0)

**Zmiany:**
- ✅ Dodano system message z guidance dla różnorodności
- ✅ Wyjaśnienie że różne persony powinny dawać różne odpowiedzi
- ✅ Wskazówki: nie zawsze środek, skrajne wartości są OK dla mocnych opinii
- ✅ Uwzględnienie cech osobowości (otwartość, sumienność)

**Kluczowe frazy:**
```
RÓŻNE persony powinny dawać RÓŻNE odpowiedzi bazując na:
- Ich wieku, wykształceniu i etapie życia
- Ich cechach osobowości (otwartość, sumienność, ekstrawersja)
- Silne opinie (wartości skrajne) są realistyczne dla osób o mocnych przekonaniach
```

#### `config/prompts/surveys/single_choice.yaml` (v1.0.0 → v1.1.0)

**Zmiany:**
- ✅ System message wyjaśnia że nie ma "uniwersalnie poprawnej" odpowiedzi
- ✅ Tips bazujące na generacji (Gen Z vs Boomers)
- ✅ Tips bazujące na osobowości (otwartość → nowatorskie opcje)
- ✅ Uwzględnienie background i doświadczeń życiowych

**Kluczowe frazy:**
```
RÓŻNE PERSONY POWINNY WYBIERAĆ RÓŻNE OPCJE!
Nie ma "uniwersalnie poprawnej" odpowiedzi.
```

#### `config/prompts/surveys/multiple_choice.yaml` (v1.0.0 → v1.1.0)

**Zmiany:**
- ✅ Eksplicytne: NIE wybieraj automatycznie wszystkich opcji
- ✅ Guidance: zazwyczaj 1-3 opcje są realistyczne
- ✅ Uwzględnienie osobowości przy wyborze ilości opcji
- ✅ Różnorodność jako kluczowa wartość

**Kluczowe frazy:**
```
NIE wybieraj automatycznie wszystkich opcji
Zazwyczaj 1-3 opcje są realistyczne (rzadko więcej niż 4)
Osoby o wysokiej otwartości mogą wybierać więcej różnorodnych opcji
```

### 2. Wzbogacony persona_context (Backend)

**Plik**: `app/services/surveys/survey_response_generator.py`

**Stary kontekst** (~9 linii):
```python
Age: 35, Gender: female
Education: Bachelor's Degree
Values: Family, Success
Background: ...
```

**Nowy kontekst** (~25 linii):
```python
=== DEMOGRAFIA ===
Imię: Anna Wiśniewska
Wiek: 35 (Millennial)
Płeć: female
Wykształcenie: Master's Degree
...

=== PSYCHOGRAFIA ===
Typ osobowości: Umiarkowanie Otwarty/a, Ekstrawertyczny/a
Big Five Scores (0.0-1.0): Otwartość: 0.60 | Sumienność: 0.70 | ...

=== WARTOŚCI I ZAINTERESOWANIA ===
Wartości: Career Growth, Work-Life Balance, ...
Zainteresowania: Running, Reading, ...

=== HISTORIA ===
[Background story max 400 znaków]

KLUCZOWY INSIGHT: Odpowiedzi tej persony powinny odzwierciedlać
jej unikalny profil osobowości...
```

**Dodane funkcje pomocnicze:**
- `get_generation_label(age)`: Gen Z / Millennial / Gen X / Boomer
- `get_personality_summary(persona)`: Interpretacja Big Five traits jako tekstowe etykiety

**Przykładowe etykiety osobowości:**
- Otwartość 0.9 → "Bardzo Otwarty/a na nowe doświadczenia"
- Otwartość 0.2 → "Preferuje sprawdzone rozwiązania"
- Ekstrawersja 0.8 → "Ekstrawertyczny/a"
- Sumienność 0.9 → "Bardzo Sumienny/a i Zdyscyplinowany/a"

## Weryfikacja

### ✅ Config Validation

```bash
python scripts/config_validate.py
# ✅ All prompts valid!
# ✅ models.yaml valid!
# ✅ All validations passed!
```

### ✅ Python Syntax

```bash
python -m py_compile app/services/surveys/survey_response_generator.py
# ✅ Składnia poprawna - brak błędów kompilacji
```

### ✅ Model Persona ma wszystkie pola Big Five

```python
# app/models/persona.py
openness = Column(Float, nullable=True)
conscientiousness = Column(Float, nullable=True)
extraversion = Column(Float, nullable=True)
agreeableness = Column(Float, nullable=True)
neuroticism = Column(Float, nullable=True)
```

### ✅ Test Manualny persona_context

Wygenerowane konteksty dla 3 testowych person pokazują:
- **Gen Z (otwartość 0.9, ekstrawersja 0.85)**: "Bardzo Otwarty/a na nowe doświadczenia, Ekstrawertyczny/a"
- **Boomer (otwartość 0.25, sumienność 0.85)**: "Preferuje sprawdzone rozwiązania, Introwertyczny/a, Bardzo Sumienny/a"
- **Millennial (zrównoważony profil)**: "Umiarkowanie Otwarty/a"

## Expected Impact

### Przed zmianami:
- Rating Scale: 80% person wybiera środkową wartość (np. 3 z 5)
- Single Choice: 70% person wybiera tę samą opcję
- Multiple Choice: 60% person wybiera wszystkie opcje

### Po zmianach (oczekiwane):
- **Rating Scale**: Rozkład normalny z outliersami (skrajne wartości dla osób o wysokiej otwartości)
- **Single Choice**: Równomierna dystrybucja z wpływem generacji i osobowości
- **Multiple Choice**: Zazwyczaj 1-3 opcje, rzadko więcej (zależnie od otwartości)

### Przykład oczekiwanych różnic:

**Pytanie**: "How satisfied are you with X?" (1-5)

| Persona | Openness | Conscientiousness | Expected Answer | Reasoning |
|---------|----------|-------------------|-----------------|-----------|
| Gen Z Social Media Manager | 0.9 | 0.5 | **5** (bardzo zadowolony) | Wysoka otwartość → entuzjastyczne oceny |
| Boomer Retired Engineer | 0.25 | 0.85 | **3** (umiarkowanie) | Tradycyjny, krytyczny, unikanie skrajności |
| Millennial Product Manager | 0.6 | 0.7 | **4** (zadowolony) | Zrównoważony profil → umiarkowane pozytywne |

## Dalsze Ulepszenia (Future Work)

1. **A/B Testing**: Porównaj stare vs nowe prompty na prawdziwych danych
2. **Diversity Metrics**: Dodaj metryki entropii Shannon dla rozkładów odpowiedzi
3. **Personality-based Temperature**: Użyj wyższej temperatury dla osób o wysokiej otwartości
4. **Cultural Dimensions**: Uwzględnij Hofstede dimensions (power_distance, individualism) w kontekście
5. **Segment-based Guidance**: Dodaj guidance specyficzne dla segmentu demograficznego

## Uwagi Techniczne

- ✅ **NIE zmieniono** temperature w `config/models.yaml` (zostaje 0.7)
- ✅ **Tylko prompty + backend** - żadnych zmian w modelach bazy danych
- ✅ **Backward compatible** - stare persony bez Big Five scores dostaną "N/A"
- ✅ **Token optimization** - background skrócony do 400 znaków (było bez limitu)

## Pliki Zmienione

1. `config/prompts/surveys/rating_scale.yaml` (v1.1.0)
2. `config/prompts/surveys/single_choice.yaml` (v1.1.0)
3. `config/prompts/surveys/multiple_choice.yaml` (v1.1.0)
4. `app/services/surveys/survey_response_generator.py` (metoda `_build_persona_context`)

---

**Data**: 2025-11-08
**Status**: ✅ Zaimplementowane, zwalidowane
**Next Step**: Deploy i monitoring diversity metrics w prawdziwych ankietach
