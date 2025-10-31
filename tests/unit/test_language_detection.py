"""
Unit tests dla detect_input_language w discussion_summarizer.

Testuje:
- Wykrywanie języka polskiego z tekstu
- Wykrywanie języka angielskiego z tekstu
- Edge cases (pusty tekst, mixed language, unclear)
- Fallback do domyślnego języka (pl)

Pokrycie:
- Polskie pytania z różnymi formułowaniami
- Angielskie pytania z różnymi formułowaniami
- Mixed content (polski + angielski)
- Tekst bez wyraźnych wskaźników języka
"""
import pytest

from app.services.focus_groups.discussion_summarizer import detect_input_language


class TestDetectInputLanguage:
    """Testy dla funkcji detect_input_language"""

    # Polish language detection
    # ========================

    def test_detect_polish_simple_question(self):
        """Test wykrycia polskiego z prostego pytania"""
        text = "Jak oceniasz ten produkt?"
        assert detect_input_language(text) == 'pl'

    def test_detect_polish_what_question(self):
        """Test wykrycia polskiego z pytaniem 'co'"""
        text = "Co myślisz o tym rozwiązaniu?"
        assert detect_input_language(text) == 'pl'

    def test_detect_polish_why_question(self):
        """Test wykrycia polskiego z pytaniem 'dlaczego'"""
        text = "Dlaczego uważasz, że to jest ważne?"
        assert detect_input_language(text) == 'pl'

    def test_detect_polish_where_question(self):
        """Test wykrycia polskiego z pytaniem 'gdzie'"""
        text = "Gdzie najczęściej korzystasz z tego produktu?"
        assert detect_input_language(text) == 'pl'

    def test_detect_polish_longer_text(self):
        """Test wykrycia polskiego z dłuższego tekstu"""
        text = """
        Jakie są Twoje główne potrzeby związane z tym produktem?
        Czy jest coś, co możemy poprawić?
        W jaki sposób korzystasz z naszej aplikacji?
        """
        assert detect_input_language(text) == 'pl'

    def test_detect_polish_with_sentiment(self):
        """Test wykrycia polskiego z tekstem emocjonalnym"""
        text = "Bardzo mi się podoba ta funkcja, ale czy można dodać więcej opcji?"
        assert detect_input_language(text) == 'pl'

    def test_detect_polish_formal(self):
        """Test wykrycia polskiego z formalnym językiem"""
        text = "W jakim stopniu produkt spełnia Pani oczekiwania?"
        assert detect_input_language(text) == 'pl'

    def test_detect_polish_with_polish_characters(self):
        """Test wykrycia polskiego z polskimi znakami diakrytycznymi"""
        text = "Jaką wartość dodaje dla Ciebie ta usługa? Czy łatwo się nią posługujesz?"
        assert detect_input_language(text) == 'pl'

    # English language detection
    # ==========================

    def test_detect_english_simple_question(self):
        """Test wykrycia angielskiego z prostego pytania"""
        text = "What do you think about this product?"
        assert detect_input_language(text) == 'en'

    def test_detect_english_how_question(self):
        """Test wykrycia angielskiego z pytaniem 'how'"""
        text = "How would you rate this feature?"
        assert detect_input_language(text) == 'en'

    def test_detect_english_why_question(self):
        """Test wykrycia angielskiego z pytaniem 'why'"""
        text = "Why do you think this is important?"
        assert detect_input_language(text) == 'en'

    def test_detect_english_where_question(self):
        """Test wykrycia angielskiego z pytaniem 'where'"""
        text = "Where do you usually use this product?"
        assert detect_input_language(text) == 'en'

    def test_detect_english_longer_text(self):
        """Test wykrycia angielskiego z dłuższego tekstu"""
        text = """
        What are your main needs related to this product?
        Is there anything we can improve?
        How do you use our application?
        """
        assert detect_input_language(text) == 'en'

    def test_detect_english_with_sentiment(self):
        """Test wykrycia angielskiego z tekstem emocjonalnym"""
        text = "I really like this feature, but could you add more options?"
        assert detect_input_language(text) == 'en'

    def test_detect_english_formal(self):
        """Test wykrycia angielskiego z formalnym językiem"""
        text = "To what extent does the product meet your expectations?"
        assert detect_input_language(text) == 'en'

    def test_detect_english_with_multiple_questions(self):
        """Test wykrycia angielskiego z wieloma pytaniami"""
        text = """
        What would you change about the product?
        How often do you use it?
        Would you recommend it to others?
        """
        assert detect_input_language(text) == 'en'

    # Edge cases
    # ==========

    def test_detect_empty_string(self):
        """Test pustego stringu (fallback do 'pl')"""
        assert detect_input_language('') == 'pl'

    def test_detect_whitespace_only(self):
        """Test samych białych znaków (fallback do 'pl')"""
        assert detect_input_language('   \n\t  ') == 'pl'

    def test_detect_numbers_only(self):
        """Test samych cyfr (fallback do 'pl')"""
        assert detect_input_language('123 456 789') == 'pl'

    def test_detect_unclear_text(self):
        """Test niejasnego tekstu bez wyraźnych wskaźników (fallback do 'pl')"""
        # Tekst bez polskich ani angielskich stopwords
        text = "Lorem ipsum dolor sit amet"
        assert detect_input_language(text) == 'pl'

    def test_detect_mixed_language_polish_dominant(self):
        """Test mixed language z przewagą polskiego"""
        # Zmień tekst aby polski miał wyraźną przewagę
        text = "Jak oceniasz ten produkt? Co myślisz o tej funkcji? What do you think?"
        # Polski powinien wygrać (więcej polskich stopwords)
        assert detect_input_language(text) == 'pl'

    def test_detect_mixed_language_english_dominant(self):
        """Test mixed language z przewagą angielskiego"""
        text = "What do you think about this? Jak oceniasz?"
        # Angielski powinien wygrać (więcej angielskich słów)
        assert detect_input_language(text) == 'en'

    def test_detect_single_word_polish(self):
        """Test pojedynczego polskiego słowa"""
        assert detect_input_language('jak') == 'pl'

    def test_detect_single_word_english(self):
        """Test pojedynczego angielskiego słowa"""
        assert detect_input_language('what') == 'en'

    def test_detect_short_polish_sentence(self):
        """Test krótkiego polskiego zdania"""
        assert detect_input_language('To jest test') == 'pl'

    def test_detect_short_english_sentence(self):
        """Test krótkiego angielskiego zdania"""
        assert detect_input_language('This is a test') == 'en'

    # Real-world scenarios
    # ====================

    def test_detect_polish_focus_group_questions(self):
        """Test wykrycia polskiego z rzeczywistych pytań focus group"""
        text = """
        Jakie są Twoje główne potrzeby związane z zakupem samochodu elektrycznego?
        Czy bezpieczeństwo jest dla Ciebie ważnym czynnikiem?
        W jaki sposób korzystasz z funkcji autopilota?
        Dlaczego zdecydowałeś się na ten model?
        """
        assert detect_input_language(text) == 'pl'

    def test_detect_english_focus_group_questions(self):
        """Test wykrycia angielskiego z rzeczywistych pytań focus group"""
        text = """
        What are your main needs when purchasing an electric car?
        Is safety an important factor for you?
        How do you use the autopilot feature?
        Why did you choose this model?
        """
        assert detect_input_language(text) == 'en'

    def test_detect_polish_responses(self):
        """Test wykrycia polskiego z odpowiedzi uczestników"""
        text = """
        Uważam, że to bardzo dobry produkt.
        Ale możemy poprawić interfejs użytkownika.
        Jest zbyt skomplikowany dla początkujących.
        """
        assert detect_input_language(text) == 'pl'

    def test_detect_english_responses(self):
        """Test wykrycia angielskiego z odpowiedzi uczestników"""
        text = """
        I think this is a great product.
        But we could improve the user interface.
        It's too complicated for beginners.
        """
        assert detect_input_language(text) == 'en'

    def test_detect_polish_long_discussion(self):
        """Test wykrycia polskiego z długiej dyskusji"""
        text = """
        Uczestnik 1: Jak oceniasz funkcję wyszukiwania?
        Uczestnik 2: Myślę, że działa dobrze, ale mogłaby być szybsza.
        Uczestnik 3: Zgadzam się, czasami muszę czekać zbyt długo.
        Uczestnik 4: Czy możemy dodać filtry?
        Uczestnik 5: To byłoby bardzo pomocne dla użytkowników.
        """
        assert detect_input_language(text) == 'pl'

    def test_detect_english_long_discussion(self):
        """Test wykrycia angielskiego z długiej dyskusji"""
        text = """
        Participant 1: How would you rate the search function?
        Participant 2: I think it works well, but it could be faster.
        Participant 3: I agree, sometimes I have to wait too long.
        Participant 4: Can we add filters?
        Participant 5: That would be very helpful for users.
        """
        assert detect_input_language(text) == 'en'

    def test_detect_case_insensitive(self):
        """Test case-insensitive detection"""
        # Polski
        assert detect_input_language('JAK OCENIASZ TEN PRODUKT?') == 'pl'
        assert detect_input_language('Jak Oceniasz Ten Produkt?') == 'pl'

        # Angielski
        assert detect_input_language('WHAT DO YOU THINK?') == 'en'
        assert detect_input_language('What Do You Think?') == 'en'

    def test_detect_with_punctuation(self):
        """Test detection z różną interpunkcją"""
        # Polski
        assert detect_input_language('Jak oceniasz ten produkt? Co myślisz?!') == 'pl'

        # Angielski
        assert detect_input_language('What do you think? How would you rate it?!') == 'en'

    def test_detect_with_special_characters(self):
        """Test detection z znakami specjalnymi"""
        # Polski
        text_pl = "Jak oceniasz ten produkt @version2.0? #feedback"
        assert detect_input_language(text_pl) == 'pl'

        # Angielski
        text_en = "What do you think about @version2.0? #feedback"
        assert detect_input_language(text_en) == 'en'

    def test_detect_with_urls(self):
        """Test detection z URLami"""
        # Polski
        text_pl = "Jak oceniasz https://example.com? Co myślisz o tej stronie?"
        assert detect_input_language(text_pl) == 'pl'

        # Angielski
        text_en = "What do you think about https://example.com? How would you rate this site?"
        assert detect_input_language(text_en) == 'en'
