#!/usr/bin/env python3
"""
Auto Discovery Engine - Automatyczne wykrywanie nowych technologii

Wykrywa technologie które NIE są w knowledge_base:
- Imports w kodzie (Python, JavaScript, TypeScript)
- Package managers (requirements.txt, package.json, Cargo.toml, go.mod)
- Bash commands (npm install, pip install, cargo build)
- File extensions (.rs, .go, .vue, .svelte)
- Config files (webpack.config.js, nginx.conf, k8s.yaml)
"""
import re
import json
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class AutoDiscoveryEngine:
    """
    Automatyczne wykrywanie nowych technologii z practice log
    """

    def __init__(self):
        """Initialize discovery engine with known patterns"""
        # Known technology patterns
        self.import_patterns = {
            # Python
            r'import\s+(\w+)': 'python_library',
            r'from\s+(\w+)\s+import': 'python_library',

            # JavaScript/TypeScript
            r'import\s+.*\s+from\s+[\'"](\w+)[\'"]': 'js_library',
            r'import\s+[\'"](\w+)[\'"]': 'js_library',
            r'require\([\'"](\w+)[\'"]\)': 'js_library',

            # Rust
            r'use\s+(\w+)::': 'rust_crate',

            # Go
            r'import\s+"(\w+)"': 'go_package',
        }

        # Package manager patterns
        self.package_patterns = {
            'package.json': r'"(\w+)":\s*"[\^~]?[\d\.]+"',  # npm dependencies
            'requirements.txt': r'^(\w+)(?:==|>=|<=)',  # pip packages
            'Cargo.toml': r'(\w+)\s*=\s*"[\d\.]+"',  # Rust crates
            'go.mod': r'require\s+(\S+)\s+v[\d\.]+',  # Go modules
            'Gemfile': r'gem\s+[\'"](\w+)[\'"]',  # Ruby gems
            'composer.json': r'"(\w+/\w+)"',  # PHP packages
        }

        # Bash command patterns
        self.bash_patterns = {
            r'npm\s+install\s+(\w+)': 'npm_package',
            r'pip\s+install\s+(\w+)': 'python_package',
            r'cargo\s+add\s+(\w+)': 'rust_crate',
            r'go\s+get\s+(\S+)': 'go_package',
            r'docker\s+run': 'docker',
            r'kubectl\s+\w+': 'kubernetes',
            r'terraform\s+\w+': 'terraform',
            r'ansible\s+\w+': 'ansible',
        }

        # File extension to technology mapping
        self.file_ext_map = {
            '.rs': 'rust',
            '.go': 'golang',
            '.vue': 'vue',
            '.svelte': 'svelte',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.rb': 'ruby',
            '.php': 'php',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.scala': 'scala',
            '.dart': 'dart',
        }

    def discover_from_practice_log(
        self,
        practice_log: List[Dict[str, Any]],
        existing_concepts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Wykryj nowe technologie z practice log

        Args:
            practice_log: Lista akcji z practice_log.jsonl
            existing_concepts: Dict z istniejącymi konceptami (static + dynamic)

        Returns:
            Dict z nowymi konceptami:
            {
                "svelte_framework": {
                    "name": "Svelte Framework",
                    "category": "Frontend",
                    "auto_discovered": True,
                    "first_seen": "2025-11-02T...",
                    "patterns": [...],
                    "confidence": 0.85,
                    "discovery_source": "import { onMount } from 'svelte'"
                },
                ...
            }
        """
        discovered = {}
        existing_names = set(existing_concepts.keys())

        # Collect all discoveries
        discoveries = []

        for log_entry in practice_log:
            # Discover from file paths
            file_discoveries = self._discover_from_file_path(log_entry, existing_names)
            discoveries.extend(file_discoveries)

            # Discover from bash commands
            bash_discoveries = self._discover_from_bash(log_entry, existing_names)
            discoveries.extend(bash_discoveries)

            # TODO: Discover from code content (when available in future)
            # code_discoveries = self._discover_from_code(log_entry, existing_names)
            # discoveries.extend(code_discoveries)

        # Aggregate discoveries (count frequency, build confidence)
        aggregated = self._aggregate_discoveries(discoveries)

        # Convert to concept format
        for tech_id, data in aggregated.items():
            if tech_id not in existing_names:
                discovered[tech_id] = self._create_concept_from_discovery(tech_id, data)

        return discovered

    def _discover_from_file_path(
        self,
        log_entry: Dict[str, Any],
        existing_names: Set[str]
    ) -> List[Dict[str, Any]]:
        """
        Wykryj technologie z file path (extension-based)

        Args:
            log_entry: Dict z akcją
            existing_names: Set istniejących concept IDs

        Returns:
            Lista discoveries
        """
        discoveries = []

        context = log_entry.get("context", {})
        file_path = context.get("file", "")

        if not file_path:
            return discoveries

        # Check file extension
        file_ext = Path(file_path).suffix.lower()

        if file_ext in self.file_ext_map:
            tech_name = self.file_ext_map[file_ext]
            tech_id = f"{tech_name}_language"

            if tech_id not in existing_names:
                discoveries.append({
                    "tech_id": tech_id,
                    "tech_name": tech_name.title(),
                    "category": self._guess_category(tech_name),
                    "subcategory": "Programming Language",
                    "source": f"File extension: {file_ext}",
                    "file": file_path,
                    "timestamp": log_entry.get("timestamp")
                })

        # Check special filenames
        filename = Path(file_path).name.lower()

        special_files = {
            'dockerfile': ('docker', 'DevOps', 'Containerization'),
            'docker-compose.yml': ('docker_compose', 'DevOps', 'Containerization'),
            'docker-compose.yaml': ('docker_compose', 'DevOps', 'Containerization'),
            'webpack.config.js': ('webpack', 'Frontend', 'Build Tools'),
            'vite.config.js': ('vite', 'Frontend', 'Build Tools'),
            'rollup.config.js': ('rollup', 'Frontend', 'Build Tools'),
            'nginx.conf': ('nginx', 'DevOps', 'Web Server'),
            'k8s.yaml': ('kubernetes', 'DevOps', 'Orchestration'),
            'terraform.tf': ('terraform', 'DevOps', 'Infrastructure as Code'),
        }

        for special_name, (tech_name, category, subcategory) in special_files.items():
            if special_name in filename:
                tech_id = f"{tech_name}_tool"

                if tech_id not in existing_names:
                    discoveries.append({
                        "tech_id": tech_id,
                        "tech_name": tech_name.replace('_', ' ').title(),
                        "category": category,
                        "subcategory": subcategory,
                        "source": f"Config file: {filename}",
                        "file": file_path,
                        "timestamp": log_entry.get("timestamp")
                    })

        return discoveries

    def _discover_from_bash(
        self,
        log_entry: Dict[str, Any],
        existing_names: Set[str]
    ) -> List[Dict[str, Any]]:
        """
        Wykryj technologie z bash commands

        Args:
            log_entry: Dict z akcją
            existing_names: Set istniejących concept IDs

        Returns:
            Lista discoveries
        """
        discoveries = []

        action = log_entry.get("action", "")
        if action != "bash_command":
            return discoveries

        # TODO: W przyszłości będzie context.bash_command
        # Na razie używamy heurystyki z context.file (może zawierać command hints)

        context = log_entry.get("context", {})
        # Placeholder - będzie rozbudowane gdy track_practice zacznie logować bash commands

        return discoveries

    def _discover_from_code(
        self,
        log_entry: Dict[str, Any],
        existing_names: Set[str]
    ) -> List[Dict[str, Any]]:
        """
        Wykryj technologie z code content (imports, etc.)

        Args:
            log_entry: Dict z akcją
            existing_names: Set istniejących concept IDs

        Returns:
            Lista discoveries
        """
        # TODO: To będzie implementowane gdy track_practice zacznie logować code snippets
        return []

    def _aggregate_discoveries(
        self,
        discoveries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Agreguj discoveries (count frequency, build confidence)

        Args:
            discoveries: Lista discoveries

        Returns:
            Dict z zagregowanymi danymi
        """
        aggregated = {}

        for disc in discoveries:
            tech_id = disc["tech_id"]

            if tech_id not in aggregated:
                aggregated[tech_id] = {
                    "tech_name": disc["tech_name"],
                    "category": disc["category"],
                    "subcategory": disc.get("subcategory", ""),
                    "sources": [],
                    "files": set(),
                    "first_seen": disc.get("timestamp"),
                    "last_seen": disc.get("timestamp"),
                    "count": 0
                }

            aggregated[tech_id]["count"] += 1
            aggregated[tech_id]["sources"].append(disc.get("source", ""))
            if disc.get("file"):
                aggregated[tech_id]["files"].add(disc["file"])

            # Update last_seen
            if disc.get("timestamp"):
                aggregated[tech_id]["last_seen"] = max(
                    aggregated[tech_id]["last_seen"] or "",
                    disc["timestamp"]
                )

        # Convert sets to lists
        for tech_id, data in aggregated.items():
            data["files"] = list(data["files"])[:5]  # Max 5 files

        return aggregated

    def _create_concept_from_discovery(
        self,
        tech_id: str,
        discovery_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Utwórz concept definition z discovery data

        Args:
            tech_id: Technology ID
            discovery_data: Aggregated discovery data

        Returns:
            Concept definition (kompatybilny z knowledge_base format)
        """
        # Calculate confidence (based on count and sources diversity)
        count = discovery_data["count"]
        sources_count = len(set(discovery_data["sources"]))

        # Confidence formula: min(count * 0.1 + sources_diversity * 0.2, 1.0)
        confidence = min(count * 0.1 + sources_count * 0.15, 0.95)

        # Build patterns (będą rozbudowane gdy będzie więcej danych)
        patterns = []

        # File-based pattern
        if discovery_data.get("files"):
            # Generalize file path
            file_path = discovery_data["files"][0]
            file_ext = Path(file_path).suffix

            if file_ext:
                patterns.append({
                    "type": "file",
                    "path": f"**/*{file_ext}"
                })

        concept = {
            "name": discovery_data["tech_name"],
            "category": discovery_data["category"],
            "subcategory": discovery_data.get("subcategory", ""),
            "difficulty": 2,  # Default medium difficulty
            "patterns": patterns,
            "prerequisites": [],  # Will be learned over time
            "next_steps": [],  # Will be learned over time
            "resources": [],  # Can be added manually later
            "auto_discovered": True,
            "discovery_metadata": {
                "first_seen": discovery_data.get("first_seen"),
                "last_seen": discovery_data.get("last_seen"),
                "discovery_count": count,
                "sources": discovery_data["sources"][:3],  # Max 3 sources
                "confidence": round(confidence, 2)
            }
        }

        return concept

    def _guess_category(self, tech_name: str) -> str:
        """
        Zgadnij kategorię na podstawie nazwy technologii

        Args:
            tech_name: Nazwa technologii

        Returns:
            Nazwa kategorii
        """
        # Simple heuristics (będzie rozbudowane w tech_classifier)
        frontend_langs = ['vue', 'svelte', 'angular']
        backend_langs = ['rust', 'golang', 'ruby', 'php']
        systems_langs = ['c', 'cpp']

        tech_lower = tech_name.lower()

        if tech_lower in frontend_langs:
            return "Frontend"
        elif tech_lower in backend_langs:
            return "Backend"
        elif tech_lower in systems_langs:
            return "Programming Languages"
        elif tech_lower in ['swift', 'kotlin', 'dart']:
            return "Mobile"
        else:
            return "Other"


# ============================================================================
# CLI for testing
# ============================================================================

if __name__ == "__main__":
    """Test auto discovery"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))

    from data_manager import load_practice_log, load_knowledge_base

    print("Testing auto_discovery.py...")

    # Load data
    logs = load_practice_log()
    kb = load_knowledge_base()
    existing_concepts = kb.get("concepts", {})

    print(f"\n✅ Loaded {len(logs)} log entries")
    print(f"✅ Existing concepts: {len(existing_concepts)}")

    # Discover
    engine = AutoDiscoveryEngine()
    discovered = engine.discover_from_practice_log(logs, existing_concepts)

    print(f"\n🔍 Discovered {len(discovered)} new technologies:")
    for tech_id, concept in discovered.items():
        print(f"  ⭐ {concept['name']} ({concept['category']}) - confidence={concept['discovery_metadata']['confidence']}")
        print(f"     Sources: {', '.join(concept['discovery_metadata']['sources'][:2])}")
