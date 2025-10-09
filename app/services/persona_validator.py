"""
Walidator Person - sprawdza różnorodność, unikalność i jakość

Ten moduł zapewnia że wygenerowane persony są:
1. Unikalne (nie duplikują się historie życiowe)
2. Różnorodne demograficznie (różne grupy wiekowe, płcie, etc.)
3. Różnorodne psychologicznie (różne profile Big Five)
"""
import difflib
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class PersonaValidator:
    """
    Walidator jakości i różnorodności person

    Przeprowadza trzy główne testy:
    1. Unikalność - sprawdza czy historie życiowe nie są zbyt podobne
    2. Różnorodność demograficzna - czy są różne grupy wiekowe, płcie, etc.
    3. Różnorodność psychologiczna - czy są różne profile Big Five
    """

    def __init__(self, similarity_threshold: float = 0.7):
        """
        Inicjalizuj walidator

        Args:
            similarity_threshold: Maksymalne podobieństwo (0-1) przed oflagowaniem duplikatów
                                 Domyślnie 0.7 = jeśli historie są podobne w >70%, to duplikat
        """
        self.similarity_threshold = similarity_threshold

    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Oblicz podobieństwo między dwoma tekstami używając difflib

        Używa algorytmu SequenceMatcher który oblicza longest common subsequence
        i konwertuje to na ratio podobieństwa.

        Args:
            text1: Pierwszy tekst
            text2: Drugi tekst

        Returns:
            Float od 0 do 1:
            - 1.0 = teksty identyczne
            - 0.5 = teksty w połowie podobne
            - 0.0 = teksty całkowicie różne
        """
        if not text1 or not text2:
            return 0.0

        # Normalizujemy tekst (małe litery, bez zbędnych spacji)
        t1 = text1.lower().strip()
        t2 = text2.lower().strip()

        # Używamy SequenceMatcher do obliczenia współczynnika podobieństwa
        return difflib.SequenceMatcher(None, t1, t2).ratio()

    def check_background_uniqueness(
        self, personas: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Sprawdź czy historie życiowe person są wystarczająco unikalne

        Porównuje każdą parę person (wszystkie kombinacje) i sprawdza
        czy similarity score nie przekracza threshold. Jeśli tak, oznacza
        parę jako potencjalny duplikat.

        Args:
            personas: Lista person jako słowniki (z kluczem "background_story")

        Returns:
            Słownik z metrykami unikalności:
            {
                "is_unique": bool,  # Wartość True oznacza brak duplikatów
                "avg_similarity": float,  # Średnie podobieństwo (0-1)
                "max_similarity": float,  # Najwyższe odnotowane podobieństwo (0-1)
                "duplicate_pairs": [  # Lista par podejrzanych o duplikację
                    {
                        "index_1": int,
                        "index_2": int,
                        "similarity": float,
                        "story_1_snippet": str (pierwsze 100 znaków),
                        "story_2_snippet": str
                    }
                ],
                "total_comparisons": int  # Liczba porównań (n*(n-1)/2)
            }
        """
        if len(personas) < 2:
            return {
                "is_unique": True,
                "avg_similarity": 0.0,
                "max_similarity": 0.0,
                "duplicate_pairs": [],
            }

        similarities = []
        duplicate_pairs = []

        # Porównujemy każdą parę person (wszystkie kombinacje)
        for i in range(len(personas)):
            for j in range(i + 1, len(personas)):
                story1 = personas[i].get("background_story", "")
                story2 = personas[j].get("background_story", "")

                # Wyliczamy poziom podobieństwa (0-1)
                similarity = self.calculate_text_similarity(story1, story2)
                similarities.append(similarity)

                # Jeżeli podobieństwo przekracza próg, zaznaczamy duplikat
                if similarity > self.similarity_threshold:
                    duplicate_pairs.append({
                        "index_1": i,
                        "index_2": j,
                        "similarity": similarity,
                        "story_1_snippet": story1[:100],  # Pierwsze 100 znaków
                        "story_2_snippet": story2[:100],
                    })

        return {
            "is_unique": len(duplicate_pairs) == 0,
            "avg_similarity": sum(similarities) / len(similarities) if similarities else 0.0,
            "max_similarity": max(similarities) if similarities else 0.0,
            "duplicate_pairs": duplicate_pairs,
            "total_comparisons": len(similarities),
        }

    def check_diversity_score(self, personas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Oblicz ogólny score różnorodności na podstawie demografii i osobowości

        Różnorodność jest mierzona w trzech wymiarach:
        1. Demograficzna - różnorodność wieku, płci, lokalizacji, edukacji, dochodów
        2. Psychologiczna - wariancja cech Big Five (więcej wariancji = bardziej różnorodne)
        3. Wartości - różnorodność wartości życiowych

        Formuła:
        diversity_score = demographic_diversity * 0.4 + personality_diversity * 0.4 + value_diversity * 0.2

        Args:
            personas: Lista person jako słowniki

        Returns:
            Słownik z metrykami różnorodności:
            {
                "diversity_score": float (0-1),  # Ogólny score (>0.5 = akceptowalne)
                "demographic_diversity": float (0-1),  # Różnorodność demograficzna
                "personality_diversity": float (0-1),  # Wariancja Big Five
                "value_diversity": float (0-1)  # Różnorodność wartości
            }
        """
        if len(personas) < 2:
            return {
                "diversity_score": 1.0,
                "demographic_diversity": 1.0,
                "personality_diversity": 1.0,
                "value_diversity": 1.0,
            }

        # Zbieramy wartości demograficzne
        ages = [p.get("age") for p in personas if p.get("age")]
        genders = [p.get("gender") for p in personas if p.get("gender")]
        locations = [p.get("location") for p in personas if p.get("location")]
        educations = [p.get("education_level") for p in personas if p.get("education_level")]
        incomes = [p.get("income_bracket") for p in personas if p.get("income_bracket")]

        def calc_unique_ratio(items: List[Any]) -> float:
            """Oblicz ratio unikalnych wartości (ile różnych / wszystkie)"""
            if not items:
                return 0.0
            return len(set(items)) / len(items)

        # Różnorodność demograficzna = średnia ważona z udziału unikalnych wartości
        demographic_diversity = (
            calc_unique_ratio(ages) * 0.2 +
            calc_unique_ratio(genders) * 0.2 +
            calc_unique_ratio(locations) * 0.2 +
            calc_unique_ratio(educations) * 0.2 +
            calc_unique_ratio(incomes) * 0.2
        )

        # Różnorodność osobowości = wariancja cech Big Five
        trait_keys = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
        trait_variances = []

        for key in trait_keys:
            values = [p.get(key) for p in personas if p.get(key) is not None]
            if len(values) > 1:
                mean = sum(values) / len(values)
                variance = sum((x - mean) ** 2 for x in values) / len(values)
                trait_variances.append(variance)

        # Większa wariancja oznacza większą różnorodność (normalizujemy do maks. 1.0)
        personality_diversity = min(1.0, sum(trait_variances) / len(trait_variances)) if trait_variances else 0.5

        # Różnorodność wartości = udział unikalnych elementów w całej puli
        all_values = []
        for p in personas:
            values = p.get("values", [])
            if values:
                all_values.extend(values)

        value_diversity = len(set(all_values)) / len(all_values) if all_values else 0.5

        # Ogólny score = średnia ważona (demografia 40%, osobowość 40%, wartości 20%)
        diversity_score = (
            demographic_diversity * 0.4 +
            personality_diversity * 0.4 +
            value_diversity * 0.2
        )

        return {
            "diversity_score": diversity_score,
            "demographic_diversity": demographic_diversity,
            "personality_diversity": personality_diversity,
            "value_diversity": value_diversity,
        }

    def validate_personas(self, personas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Uruchom pełny zestaw testów walidacyjnych dla person

        Przeprowadza:
        1. Test unikalności (check_background_uniqueness)
        2. Test różnorodności (check_diversity_score)
        3. Generuje rekomendacje jeśli coś jest nie tak

        Kryteria akceptacji:
        - Brak duplikatów (similarity < threshold)
        - diversity_score >= 0.5

        Args:
            personas: Lista person jako słowniki

        Returns:
            Słownik z pełnymi wynikami walidacji:
            {
                "is_valid": bool,  # True jeśli wszystkie testy przeszły
                "uniqueness": {...},  # Wyniki check_background_uniqueness
                "diversity": {...},  # Wyniki check_diversity_score
                "recommendations": [str]  # Lista rekomendacji co poprawić
            }
        """
        # Uruchom testy
        uniqueness_results = self.check_background_uniqueness(personas)
        diversity_results = self.check_diversity_score(personas)

        # Sprawdź czy persony są akceptowalne
        is_valid = (
            uniqueness_results["is_unique"] and
            diversity_results["diversity_score"] >= 0.5
        )

        results = {
            "is_valid": is_valid,
            "uniqueness": uniqueness_results,
            "diversity": diversity_results,
            "recommendations": [],
        }

        # Wygeneruj rekomendacje jeśli są problemy
        if not uniqueness_results["is_unique"]:
            results["recommendations"].append(
                f"Znaleziono {len(uniqueness_results['duplicate_pairs'])} podobnych par person. "
                "Rozważ regenerację z wyższą temperaturą lub bardziej różnorodnymi promptami."
            )

        if diversity_results["diversity_score"] < 0.5:
            results["recommendations"].append(
                f"Niski score różnorodności ({diversity_results['diversity_score']:.2f}). "
                "Upewnij się że rozkłady demograficzne mają wystarczającą różnorodność."
            )

        if diversity_results["personality_diversity"] < 0.3:
            results["recommendations"].append(
                "Niska różnorodność osobowości. Persony mają podobne profile Big Five."
            )

        logger.info(
            "Walidacja person zakończona",
            extra={
                "total_personas": len(personas),
                "is_valid": is_valid,
                "diversity_score": diversity_results["diversity_score"],
                "duplicates": len(uniqueness_results["duplicate_pairs"]),
            }
        )

        return results
