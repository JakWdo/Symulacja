# Statistical Validity - Dokumentacja

## 🎯 Co to jest Statistical Validity w tej aplikacji?

**Statistical Validity** (Ważność Statystyczna) oznacza, że wygenerowane persony **statystycznie odpowiadają** zdefiniowanej populacji docelowej.

Używamy **testu chi-kwadrat (χ²)** do weryfikacji, czy rozkład cech demograficznych person odpowiada rozkładowi w docelowej populacji.

---

## 📊 Jak to działa?

### 1. **Definiujesz Populację Docelową** (Target Demographics)

Podczas tworzenia projektu określasz rozkład demograficzny, np.:

```json
{
  "age_group": {
    "18-24": 0.15,  // 15% młodych dorosłych
    "25-34": 0.25,  // 25% millennialsów
    "35-44": 0.20,  // 20% średni wiek
    "45-54": 0.18,  // 18% starsi
    "55-64": 0.12,  // 12% przed emeryturą
    "65+":   0.10   // 10% seniorzy
  },
  "gender": {
    "male":   0.49,
    "female": 0.49,
    "non-binary": 0.02
  },
  "education_level": {
    "High school": 0.25,
    "Bachelor's degree": 0.30,
    "Master's degree": 0.15,
    ...
  }
}
```

### 2. **Generujesz Persony**

System losuje cechy demograficzne zgodnie z tymi rozkładami (używając `numpy.random` z ważonymi prawdopodobieństwami).

### 3. **Test Chi-Kwadrat (χ²)**

Po wygenerowaniu person system wykonuje test chi-kwadrat dla każdej cechy:

**Hipoteza zerowa (H₀)**: Wygenerowane persony mają taki sam rozkład jak populacja docelowa.

**Przykład:**
- Populacja docelowa: `age 18-24: 15%` (z 100 person → oczekujemy 15)
- Wygenerowane persony: 17 osób w wieku 18-24
- Test chi-kwadrat sprawdza czy różnica (17 vs 15) jest **statystycznie istotna**

### 4. **P-value (Wartość p)**

Dla każdej cechy demograficznej otrzymujemy **p-value**:

- **p > 0.05** ✅ → Rozkład jest OK (różnica może być przypadkowa)
- **p ≤ 0.05** ❌ → Rozkład się różni (różnica jest statystycznie istotna)

**Przykład p-values:**
```json
{
  "age": 0.234,      // ✅ OK - nie różni się znacząco
  "gender": 0.891,   // ✅ OK - bardzo dobre dopasowanie
  "education": 0.012 // ❌ Problem - rozkład wykształcenia się różni
}
```

### 5. **Overall Validity**

Projekt jest **statystycznie ważny** gdy **wszystkie p-values > 0.05**.

---

## 🔬 Gdzie to zobaczyć?

### W UI (Dashboard):

Po wygenerowaniu person pojawi się panel **"Statistical Validation"**:

```
┌─────────────────────────────────┐
│ Statistical Validation          │
├─────────────────────────────────┤
│ age          0.234      ✓ Valid │
│ gender       0.891      ✓ Valid │
│ education    0.012      ✗ Invalid│
│ income       0.456      ✓ Valid │
│ location     0.678      ✓ Valid │
└─────────────────────────────────┘
```

### W Header Bar:

Jeśli **wszystkie testy przeszły**, zobaczysz badge:

```
✓ Statistically Valid
```

---

## 🎓 Dlaczego to ważne?

### 1. **Representatywność**
Persony muszą **reprezentować** rzeczywistą populację, inaczej wyniki focus groups będą **bias** (stronnicze).

**Przykład:**
- Chcesz zbadać rynek millennialsów (25-34)
- Ale przez przypadek wygenerował się zbyt dużo osób 55+
- Wyniki focus group będą **niereprezentatywne**

### 2. **Naukowa Rzetelność**
Chi-kwadrat to **uznana metoda statystyczna** używana w badaniach naukowych i komercyjnych.

### 3. **Unikanie Błędów Losowych**
Nawet przy prawidłowym kodzie, losowanie może dać "dziwne" wyniki (np. 20 person to mała próba).

Test chi-kwadrat to **weryfikacja**, czy to normalne fluktuacje, czy rzeczywisty problem.

---

## ⚙️ Implementacja (Backend)

### Kod w: `app/services/persona_generator_langchain.py`

```python
def validate_distribution(
    self,
    generated_personas: List[Dict[str, Any]],
    target_distribution: DemographicDistribution,
) -> Dict[str, Any]:
    """
    Validate using chi-square test
    Returns p-values for each demographic variable
    """
    results = {}

    # Test age distribution
    if target_distribution.age_groups:
        results["age"] = self._chi_square_test(
            generated_personas, "age_group", target_distribution.age_groups
        )

    # ... similar for gender, education, income, location

    # Overall validation
    all_p_values = [r["p_value"] for r in results.values()]
    results["overall_valid"] = all(
        p > 0.05 for p in all_p_values  # Threshold: 0.05 (95% confidence)
    )

    return results
```

### Wzór Chi-Kwadrat:

```
χ² = Σ [(Observed - Expected)² / Expected]

gdzie:
- Observed = faktyczna liczba person w kategorii
- Expected = oczekiwana liczba (target % × total count)
```

**Scipy** liczy to za nas:
```python
chi2_stat, p_value = stats.chisquare(f_obs=observed, f_exp=expected)
```

---

## 🛠️ Co zrobić gdy test się NIE powiedzie?

### Opcja 1: Wygeneruj więcej person
- Małe próby (10-20 person) częściej failują
- **Zalecane minimum: 30 person** dla reliable results
- Optymalne: **50-100 person**

### Opcja 2: Sprawdź Target Demographics
- Może rozkład jest zbyt "egzotyczny"?
- Upewnij się że prawdopodobieństwa sumują się do 1.0

### Opcja 3: Re-generate
- Czasem to po prostu pech (losowe fluktuacje)
- Wygeneruj persony ponownie

---

## 📈 Przykład Real-World

### Scenariusz: Badanie rynku smartfonów

**Target Demographics (US Market 2024):**
```json
{
  "age_group": {
    "18-24": 0.12,  // Gen Z
    "25-34": 0.22,  // Młodzi millennials
    "35-44": 0.20,  // Starsi millennials
    "45-54": 0.18,  // Gen X
    "55-64": 0.14,  // Baby boomers
    "65+":   0.14   // Seniorzy
  },
  "income_bracket": {
    "< $25k": 0.15,
    "$25k-$50k": 0.20,
    "$50k-$75k": 0.22,
    "$75k-$100k": 0.18,
    "$100k-$150k": 0.15,
    "> $150k": 0.10
  }
}
```

**Generated 100 personas:**
```
Age distribution:
  18-24: 14 (expected 12) → χ² = 0.33, p = 0.565 ✅
  25-34: 19 (expected 22) → χ² = 0.41, p = 0.522 ✅
  ... etc

Income distribution:
  < $25k: 18 (expected 15) → χ² = 0.60, p = 0.439 ✅
  ... etc

Overall: ✅ Statistically Valid (all p > 0.05)
```

**Interpretacja:**
Możesz teraz **ufać** wynikom focus groups, bo persony reprezentują rzeczywisty rynek US.

---

## ❓ FAQ

**Q: Dlaczego threshold to 0.05?**
A: To standard w statystyce (95% confidence level). Oznacza: "Jest 5% szansy że różnica to przypadek".

**Q: Co jeśli mam tylko 10 person?**
A: Test może być unreliable. Chi-kwadrat wymaga "expected count ≥ 5" w każdej kategorii.

**Q: Czy mogę zmienić threshold?**
A: Tak, w `app/core/config.py` zmień `STATISTICAL_SIGNIFICANCE_THRESHOLD`.

**Q: Dlaczego to się nazywa "chi-kwadrat"?**
A: Symbol χ² (chi-squared) pochodzi od greckiej litery χ (chi). Rozkład testowy ma kształt "kwadratowy".

---

## 📚 Więcej Informacji

- [Wikipedia: Chi-squared test](https://en.wikipedia.org/wiki/Chi-squared_test)
- [SciPy Documentation: chisquare](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chisquare.html)
- [Goodness of Fit Test](https://www.statisticshowto.com/goodness-of-fit-test/)

---

**Podsumowanie:** Statistical Validity daje Ci pewność, że Twoje persony są **reprezentatywne** i wyniki badań są **wiarygodne**. 🎯
