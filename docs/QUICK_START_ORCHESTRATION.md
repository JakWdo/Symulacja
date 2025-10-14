# Quick Start - Orchestration System

## Jak zobaczyć nowy system w akcji?

### Krok 1: Uruchom aplikację

```bash
# Z katalogu głównego projektu
docker-compose up -d

# Poczekaj aż wszystko się uruchomi (~30s)
docker-compose logs -f api  # Sprawdź czy API jest ready
```

### Krok 2: Otwórz frontend

1. Otwórz przeglądarkę: http://localhost:5173
2. Zaloguj się (lub zarejestruj nowe konto)

### Krok 3: Utwórz projekt (jeśli nie masz)

1. Kliknij "Nowy Projekt"
2. Wypełnij podstawowe dane
3. Zapisz

### Krok 4: Wygeneruj persony z orchestration

1. Przejdź do panelu "Persony"
2. Kliknij **"Generuj persony"**
3. W wizardzie:
   - Ustaw liczbę person (np. 20)
   - Wybierz rozkład demograficzny
   - **(OPCJONALNE)** W sekcji "Dodatkowy opis grupy" wpisz np:
     ```
     Osoby zainteresowane ekologią i zrównoważonym rozwojem
     ```
   - Kliknij "Generuj"

4. **Poczekaj 2-4 minuty**
   - Zobaczysz progress bar
   - System najpierw wykona orchestration (~30-60s)
   - Potem równolegle wygeneruje wszystkie persony (~1.5-3s każda)

### Krok 5: Zobacz reasoning!

1. Gdy persony są gotowe, zobaczysz je na liście
2. Kliknij **"..." (More)** na dowolnej personie
3. Wybierz **"Zobacz szczegóły"**
4. W dialogu zobaczysz **3 zakładki:**

   **📋 Profil** (default)
   - Podstawowe dane
   - Demografia
   - Psychografia
   - Zainteresowania

   **🧠 Uzasadnienie** ← NOWA ZAKŁADKA!
   - **Orchestration Brief** (2000-3000 znaków)
     - Długi, edukacyjny opis dlaczego ta grupa demograficzna
     - Kontekst zawodowy i życiowy
     - Wartości i aspiracje
     - Typowe wyzwania
   - **Kontekst Społeczny Polski** (500-800 znaków)
   - **Wskaźniki z Grafu Wiedzy**
     - Indicators z raportów (np. "78.4% zatrudnienia")
     - Każdy z wyjaśnieniem "dlaczego to ważne"
     - Badges: confidence, time_period, source
   - **Uzasadnienie Alokacji**
     - Dlaczego X person w tej grupie?

   **📚 Kontekst RAG**
   - Cytowania z dokumentów RAG
   - Relevance scores

### Krok 6: Porównaj różne persony

Otwórz kilka person z różnych grup demograficznych i zobacz jak reasoning się różni!

Przykładowo:
- **Anna, 29 lat, Warszawa** - brief o młodych profesjonalistach w stolicy
- **Jan, 45 lat, Kraków** - brief o doświadczonych specjalistach
- **Maria, 62 lata, wieś** - brief o seniorach na wsi

Każdy brief jest **unikalny** i wyjaśnia społeczno-ekonomiczny kontekst tej grupy!

## Co sprawdzić w reasoning?

✅ **Długość briefu:** 2000-3000 znaków (scroll!)
✅ **Styl:** Konwersacyjny, edukacyjny (jak kolega tłumaczy)
✅ **Wyjaśnienia "dlaczego":** Nie tylko fakty, ale ich znaczenie
✅ **Wskaźniki z danymi:** Magnitude (np. "78.4%"), confidence, source
✅ **Production-ready:** Treść brzmi profesjonalnie i może iść do klienta

## Typowe pytania

**Q: Nie widzę zakładki "Uzasadnienie"**
A: Persona musi mieć orchestration reasoning. Jeśli wygenerowałeś persony przed implementacją tego systemu, wygeneruj nowe.

**Q: Brief jest krótki (< 1000 znaków)**
A: To może być issue z Gemini 2.5 Pro. Sprawdź logi:
```bash
docker-compose logs api | grep -i orchestration
```

**Q: Orchestration trwa bardzo długo (> 2 min)**
A: To normalne przy pierwszym uruchomieniu (zimny start Gemini). Kolejne powinny być szybsze.

**Q: Brak wskaźników z Graph RAG**
A: Upewnij się że:
- Neo4j jest uruchomiony
- Masz zaindeksowane dokumenty RAG
- Uruchom: `python scripts/init_neo4j_indexes.py`

## Debug Mode

Sprawdź logi aby zobaczyć co się dzieje:

```bash
# Orchestration step
docker-compose logs api | grep "🎯 Orchestration"

# Brief generation
docker-compose logs api | grep "✅ Orchestration plan created"

# Brief mapping to personas
docker-compose logs api | grep "📋 Mapped briefs"

# Individual persona generation
docker-compose logs api | grep "Using orchestration brief"
```

## Performance Tips

**Dla szybszego testowania:**
- Wygeneruj mniej person (np. 10 zamiast 20)
- Orchestration time nie zmienia się (zawsze ~30-60s)
- Ale total time będzie krótszy

**Dla lepszej jakości briefów:**
- Dodaj szczegółowy "Dodatkowy opis grupy" w wizardzie
- Gemini 2.5 Pro użyje tego jako dodatkowego kontekstu

## Next Steps

Po przetestowaniu orchestration:

1. **Utwórz Focus Group** z wygenerowanymi personami
2. **Zobacz jak reasoning wpływa** na odpowiedzi person
3. **Porównaj odpowiedzi** person z różnych grup demograficznych
4. **Użyj Graph Analysis** aby zobaczyć insights z dyskusji

Enjoy! 🚀
