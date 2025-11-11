#!/bin/bash
# Cache cleanup script for Sight platform
# Removes Python cache files, macOS system files, and build artifacts
#
# Usage: ./scripts/cleanup_cache.sh

set -e

echo "🧹 Cleaning cache files..."

# Count before
BEFORE=$(find . -name "*.pyc" -o -name "__pycache__" -o -name ".DS_Store" -o -name "*.egg-info" | wc -l)
echo "Found $BEFORE cache files/directories"

# Clean Python cache
echo "Removing *.pyc files..."
find . -name "*.pyc" -delete

echo "Removing __pycache__ directories..."
find . -name "__pycache__" -type d -delete

# Clean macOS files
echo "Removing .DS_Store files..."
find . -name ".DS_Store" -delete

# Clean egg-info (optional - uncomment if needed)
# echo "Removing *.egg-info directories..."
# find . -name "*.egg-info" -type d -exec rm -rf {} +

# Clean pytest cache (optional)
echo "Removing .pytest_cache directories..."
find . -name ".pytest_cache" -type d -exec rm -rf {} +

# Clean ruff cache (optional)
echo "Removing .ruff_cache directories..."
find . -name ".ruff_cache" -type d -exec rm -rf {} +

# Count after
AFTER=$(find . -name "*.pyc" -o -name "__pycache__" -o -name ".DS_Store" -o -name "*.egg-info" | wc -l)
echo ""
echo "✅ Cleanup completed!"
echo "   Before: $BEFORE files/directories"
echo "   After:  $AFTER files/directories"
echo "   Removed: $((BEFORE - AFTER)) files/directories"
