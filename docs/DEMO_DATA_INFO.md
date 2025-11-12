# Dane Demonstracyjne Sight - Informacje

## 🎯 Przegląd

Platforma Sight została wypełniona **4 kompleksowymi projektami demonstracyjnymi** z prawdziwymi danymi wygenerowanymi przez AI. Projekty są podzielone na **2 konta** (polskie i międzynarodowe) dla lepszej prezentacji różnych zastosowań platformy.

## 🔑 Konta Demo

### Konto Polskie (2 projekty)
- **Email:** demo@sight.pl
- **Hasło:** Demo2025!Sight
- **Projekty:**
  - Kampania Profilaktyki Zdrowia Psychicznego
  - Rewolucja Transportu Miejskiego 2025

### Konto Międzynarodowe (2 projekty)
- **Email:** demo-intl@sight.pl
- **Hasło:** Demo2025!Sight
- **Projekty:**
  - Mental Health Awareness Campaign (US)
  - Community Safety & Trust Program

## 📊 Statystyki Danych

| Metryka | Wartość |
|---------|---------|
| **Projekty** | 4 (2 PL + 2 INT) |
| **Persony** | 47 (23 PL + 24 INT) |
| **Ankiety** | 5 (3 PL + 2 INT) |
| **Odpowiedzi ankiet** | 80+ |
| **Focus Groups** | 4 (2 PL + 2 INT) |
| **Wiadomości dyskusji** | 120 |

## 🌐 Dostęp do Platformy

- **Frontend:** http://localhost:5173
- **API Docs:** http://localhost:8000/docs
- **Neo4j Browser:** http://localhost:7474

## 📁 Szczegóły Projektów

### 🇵🇱 Projekt 1: Kampania Profilaktyki Zdrowia Psychicznego
**Cel:** Badanie barier w dostępie do pomocy psychologicznej dla młodych dorosłych w Polsce

- **Persony:** 11 (25-40 lat, duże miasta)
- **Ankiety:** 2
  - Postrzeganie zdrowia psychicznego (11 odpowiedzi)
  - Bariery w dostępie do terapii (11 odpowiedzi)
- **Focus Group:** "Jak zachęcić młodych do szukania pomocy?" (30 wiadomości)

### 🇵🇱 Projekt 2: Rewolucja Transportu Miejskiego 2025
**Cel:** Badanie potrzeb mieszkańców dotyczących komunikacji miejskiej i ekologii

- **Persony:** 12 (20-55 lat, użytkownicy transportu publicznego)
- **Ankieta:** "Twoje doświadczenia z komunikacją miejską" (12 odpowiedzi)
- **Focus Group:** "Jak poprawić transport publiczny?" (30 wiadomości)

### 🇺🇸 Projekt 3: Mental Health Awareness Campaign
**Cel:** Understanding barriers and stigma around mental health in American workplaces

- **Persony:** 12 (25-45 lat, professionals, US cities)
- **Ankieta:** "Mental Health in the Workplace Survey" (12 odpowiedzi)
- **Focus Group:** "Building Supportive Workplace Culture" (30 wiadomości)

### 🇺🇸 Projekt 4: Community Safety & Trust Program
**Cel:** Building trust between local communities and government

- **Persony:** 12 (30-60 lat, diverse demographics, urban areas)
- **Ankieta:** "Trust in Local Governance Survey" (12 odpowiedzi)
- **Focus Group:** "Building Community Trust Discussion" (30 wiadomości)

## 🛠️ Narzędzia Pomocnicze

Utworzono serię skryptów Python w `scripts/`:

- `create_demo_data.py` - Automatyczne tworzenie projektów
- `reorganize_demo_data.py` - Reorganizacja na 2 konta (PL/INT)
- `rerun_analyses.py` - Ponowne uruchamianie analiz AI
- `verify_demo_data.py` - Weryfikacja danych
- `final_verification.py` - Finalna weryfikacja

## 🔧 Naprawione Błędy

Podczas tworzenia danych demo naprawiono **3 krytyczne błędy**:

1. ✅ Brak definicji `_rag_service_available` w `persona_generator_langchain.py`
2. ✅ Nieprawidłowa struktura konfiguracji RAG w `rag_hybrid_search_service.py`
3. ✅ Brak importu `logger` w `focus_group_service_langchain.py`

## 🚀 Ponowne Tworzenie Danych

Jeśli chcesz ponownie wygenerować dane demo:

```bash
# Pełna reorganizacja (usuwa stare, tworzy nowe)
docker exec sight_api python3 /app/scripts/reorganize_demo_data.py

# Ponowne uruchomienie analiz (ankiety + focus groups)
docker exec sight_api python3 /app/scripts/rerun_analyses.py

# Weryfikacja danych
docker exec sight_api python3 /app/scripts/verify_demo_data.py
```

## ✨ Charakterystyka Danych

Wszystkie dane są **prawdziwe i wygenerowane przez AI** (Google Gemini 2.5):

- ✅ **Persony** - Realistyczne profile demograficzne z background stories
- ✅ **Ankiety** - Autentyczne odpowiedzi AI oparte na profilach person
- ✅ **Focus Groups** - Naturalne dyskusje między personami z interakcjami
- ✅ **Kontekst kulturowy** - Polskie i międzynarodowe dane demograficzne

## 📝 Uwagi

- Dane są generowane asynchronicznie w tle
- Generowanie pełnego zestawu danych trwa ~10-15 minut
- Wszystkie analizy są gotowe i dostępne w UI
- Projekty używają polskiego kontekstu demograficznego (PL) lub międzynarodowego (INT)

---

**Platforma gotowa do prezentacji demo!** 🎉
