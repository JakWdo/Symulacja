"""
Skrypt do znajdowania wszystkich błędów importu w projekcie.
Próbuje zaimportować app.main i wyświetla wszystkie ImportError.
"""

import sys
import traceback

def find_import_errors():
    """Znajdź wszystkie błędy importu w projekcie."""
    print("🔍 Szukam błędów importu w app.main...")
    print("-" * 80)

    try:
        import app.main
        print("✅ Wszystkie importy działają poprawnie!")
        return 0
    except ImportError as e:
        print("❌ Znaleziono błąd importu:")
        print()

        # Wyświetl pełny traceback
        print(traceback.format_exc())

        # Wyciągnij szczegóły
        tb = traceback.extract_tb(e.__traceback__)

        print()
        print("📝 Podsumowanie błędu:")
        print(f"   Moduł: {e.name if hasattr(e, 'name') else 'unknown'}")
        print(f"   Błąd: {str(e)}")
        print()
        print("📂 Ścieżka importu (gdzie szukać problemu):")
        for frame in tb:
            if '/app/' in frame.filename:
                print(f"   {frame.filename}:{frame.lineno}")

        return 1
    except Exception as e:
        print(f"❌ Inny błąd: {type(e).__name__}: {e}")
        print()
        print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(find_import_errors())
