#!/usr/bin/env python
"""
Download required NLTK data for Polish NLP support.

This script downloads:
- stopwords corpus (Polish and English stopwords)
- punkt tokenizer (sentence tokenization)

Run during Docker build or manually:
    python scripts/download_nltk_data.py
"""

import nltk
import sys


def download_nltk_data():
    """Download required NLTK data packages."""
    packages = [
        'stopwords',  # Polish and English stopwords
        'punkt',      # Sentence tokenization
    ]

    print("Downloading NLTK data packages...")

    for package in packages:
        try:
            print(f"  Downloading {package}...", end=' ')
            nltk.download(package, quiet=True)
            print("✓")
        except Exception as e:
            print(f"✗ Error: {e}")
            sys.exit(1)

    print("All NLTK data packages downloaded successfully!")

    # Verify download
    try:
        from nltk.corpus import stopwords
        polish_stopwords = stopwords.words('polish')
        english_stopwords = stopwords.words('english')
        print(f"\nVerification:")
        print(f"  Polish stopwords: {len(polish_stopwords)} words")
        print(f"  English stopwords: {len(english_stopwords)} words")
    except Exception as e:
        print(f"\n⚠ Warning: Could not verify download: {e}")
        sys.exit(1)


if __name__ == "__main__":
    download_nltk_data()
