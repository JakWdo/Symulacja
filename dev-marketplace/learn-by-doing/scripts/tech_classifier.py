#!/usr/bin/env python3
"""
Tech Classifier - Klasyfikacja technologii do kategorii

Zawiera bazę ~200+ znanych technologii i ich klasyfikację.
Pomaga auto-discovery w przypisywaniu kategorii do nowych technologii.
"""
import re
from typing import Dict, List, Any, Optional, Tuple

# Baza znanych technologii
KNOWN_TECHNOLOGIES = {
    # Frontend Frameworks
    "react": ("Frontend", "Framework", "JavaScript library for building UIs"),
    "vue": ("Frontend", "Framework", "Progressive JavaScript framework"),
    "angular": ("Frontend", "Framework", "Platform for building web applications"),
    "svelte": ("Frontend", "Framework", "Cybernetically enhanced web apps"),
    "solid": ("Frontend", "Framework", "Reactive JavaScript library"),
    "preact": ("Frontend", "Framework", "Fast 3kB alternative to React"),
    "ember": ("Frontend", "Framework", "Framework for ambitious web developers"),

    # Frontend Libraries
    "axios": ("Frontend", "HTTP Library", "Promise based HTTP client"),
    "fetch": ("Frontend", "HTTP Library", "Native fetch API"),
    "lodash": ("Frontend", "Utility Library", "Utility library"),
    "moment": ("Frontend", "Date Library", "Parse, validate, manipulate dates"),
    "dayjs": ("Frontend", "Date Library", "2KB immutable date library"),
    "d3": ("Frontend", "Visualization", "Data visualization library"),
    "chart": ("Frontend", "Visualization", "Simple charting library"),
    "three": ("Frontend", "3D Graphics", "JavaScript 3D library"),

    # State Management
    "redux": ("Frontend", "State Management", "Predictable state container"),
    "mobx": ("Frontend", "State Management", "Simple, scalable state management"),
    "zustand": ("Frontend", "State Management", "Bear necessities for state management"),
    "recoil": ("Frontend", "State Management", "Experimental React state management"),
    "jotai": ("Frontend", "State Management", "Primitive and flexible state management"),

    # Backend Frameworks
    "fastapi": ("Backend", "Web Framework", "Modern, fast web framework for Python"),
    "flask": ("Backend", "Web Framework", "Lightweight WSGI web application framework"),
    "django": ("Backend", "Web Framework", "High-level Python web framework"),
    "express": ("Backend", "Web Framework", "Fast, unopinionated web framework for Node"),
    "nestjs": ("Backend", "Web Framework", "Progressive Node.js framework"),
    "koa": ("Backend", "Web Framework", "Expressive middleware for Node.js"),
    "hapi": ("Backend", "Web Framework", "Rich framework for building applications"),
    "spring": ("Backend", "Web Framework", "Java framework for enterprise applications"),
    "laravel": ("Backend", "Web Framework", "PHP framework for web artisans"),
    "rails": ("Backend", "Web Framework", "Ruby web application framework"),
    "gin": ("Backend", "Web Framework", "HTTP web framework written in Go"),
    "echo": ("Backend", "Web Framework", "High performance, minimalist Go framework"),

    # Python Libraries
    "pandas": ("Data Science", "Data Analysis", "Data manipulation and analysis"),
    "numpy": ("Data Science", "Numerical Computing", "Fundamental package for numerical computing"),
    "scipy": ("Data Science", "Scientific Computing", "Scientific and technical computing"),
    "scikit": ("AI/ML", "Machine Learning", "Machine learning library"),
    "sklearn": ("AI/ML", "Machine Learning", "Machine learning library"),
    "tensorflow": ("AI/ML", "Deep Learning", "Open source machine learning platform"),
    "pytorch": ("AI/ML", "Deep Learning", "Open source machine learning framework"),
    "keras": ("AI/ML", "Deep Learning", "Deep learning API"),
    "matplotlib": ("Data Science", "Visualization", "Comprehensive library for visualizations"),
    "seaborn": ("Data Science", "Visualization", "Statistical data visualization"),
    "requests": ("Backend", "HTTP Library", "HTTP library for Python"),
    "aiohttp": ("Backend", "Async HTTP", "Asynchronous HTTP client/server"),
    "httpx": ("Backend", "HTTP Library", "Next generation HTTP client"),

    # Databases
    "postgresql": ("Database", "SQL", "Powerful, open source object-relational database"),
    "postgres": ("Database", "SQL", "Powerful, open source object-relational database"),
    "mysql": ("Database", "SQL", "Open-source relational database management system"),
    "sqlite": ("Database", "SQL", "C-language library that implements SQL database"),
    "mongodb": ("Database", "NoSQL", "Source-available cross-platform document-oriented database"),
    "redis": ("Database", "Cache/NoSQL", "In-memory data structure store"),
    "cassandra": ("Database", "NoSQL", "Distributed wide-column store"),
    "elasticsearch": ("Database", "Search Engine", "Distributed search and analytics engine"),
    "neo4j": ("Database", "Graph", "Graph database management system"),

    # ORMs & Database Tools
    "sqlalchemy": ("Database", "ORM", "Python SQL toolkit and ORM"),
    "prisma": ("Database", "ORM", "Next-generation ORM for Node.js & TypeScript"),
    "typeorm": ("Database", "ORM", "ORM for TypeScript and JavaScript"),
    "sequelize": ("Database", "ORM", "Promise-based Node.js ORM"),
    "mongoose": ("Database", "ODM", "MongoDB object modeling for Node.js"),
    "alembic": ("Database", "Migrations", "Database migration tool for SQLAlchemy"),

    # Testing
    "pytest": ("Testing", "Unit Tests", "Testing framework for Python"),
    "jest": ("Testing", "Unit Tests", "Delightful JavaScript testing"),
    "mocha": ("Testing", "Unit Tests", "Feature-rich JavaScript test framework"),
    "jasmine": ("Testing", "Unit Tests", "Behavior-driven development framework"),
    "cypress": ("Testing", "E2E Tests", "Fast, easy and reliable testing for web"),
    "playwright": ("Testing", "E2E Tests", "Cross-browser end-to-end testing"),
    "selenium": ("Testing", "E2E Tests", "Browser automation framework"),
    "puppeteer": ("Testing", "E2E Tests", "Headless Chrome Node.js API"),

    # DevOps & Cloud
    "docker": ("DevOps", "Containerization", "Platform for developing, shipping, and running applications"),
    "kubernetes": ("DevOps", "Orchestration", "Production-grade container orchestration"),
    "kubectl": ("DevOps", "Orchestration", "Kubernetes command-line tool"),
    "terraform": ("DevOps", "Infrastructure as Code", "Infrastructure as Code software tool"),
    "ansible": ("DevOps", "Configuration Management", "Automation tool for IT tasks"),
    "jenkins": ("DevOps", "CI/CD", "Automation server for building, testing, deploying"),
    "gitlab": ("DevOps", "CI/CD", "DevOps lifecycle tool"),
    "github": ("DevOps", "Version Control", "Development platform"),
    "aws": ("DevOps", "Cloud", "Amazon Web Services"),
    "gcp": ("DevOps", "Cloud", "Google Cloud Platform"),
    "azure": ("DevOps", "Cloud", "Microsoft Azure"),

    # Build Tools & Bundlers
    "webpack": ("Frontend", "Build Tools", "Static module bundler"),
    "vite": ("Frontend", "Build Tools", "Next generation frontend tooling"),
    "rollup": ("Frontend", "Build Tools", "Module bundler for JavaScript"),
    "parcel": ("Frontend", "Build Tools", "Zero configuration build tool"),
    "esbuild": ("Frontend", "Build Tools", "Extremely fast JavaScript bundler"),
    "turbopack": ("Frontend", "Build Tools", "Incremental bundler optimized for JavaScript and TypeScript"),

    # CSS Frameworks & Tools
    "tailwind": ("Frontend", "Styling", "Utility-first CSS framework"),
    "bootstrap": ("Frontend", "Styling", "Popular CSS Framework"),
    "material": ("Frontend", "Styling", "Material Design components"),
    "sass": ("Frontend", "CSS Preprocessor", "CSS preprocessor"),
    "less": ("Frontend", "CSS Preprocessor", "CSS preprocessor"),
    "styled": ("Frontend", "CSS-in-JS", "Visual primitives for component age"),

    # Programming Languages
    "python": ("Programming Languages", "Scripting", "High-level programming language"),
    "javascript": ("Programming Languages", "Scripting", "Programming language of the Web"),
    "typescript": ("Programming Languages", "Scripting", "Typed superset of JavaScript"),
    "rust": ("Programming Languages", "Compiled", "Systems programming language"),
    "golang": ("Programming Languages", "Compiled", "Statically typed, compiled language"),
    "go": ("Programming Languages", "Compiled", "Statically typed, compiled language"),
    "java": ("Programming Languages", "Compiled", "Class-based, object-oriented programming language"),
    "kotlin": ("Mobile", "Native Android", "Modern programming language for Android"),
    "swift": ("Mobile", "Native iOS", "Powerful and intuitive programming language for iOS"),
    "ruby": ("Programming Languages", "Scripting", "Dynamic, open source programming language"),
    "php": ("Programming Languages", "Scripting", "Popular general-purpose scripting language"),
    "cpp": ("Programming Languages", "Compiled", "General-purpose programming language"),
    "c": ("Programming Languages", "Compiled", "General-purpose programming language"),
    "csharp": ("Programming Languages", "Compiled", "Modern, object-oriented language"),
    "scala": ("Programming Languages", "Compiled", "Combines OOP and functional programming"),
    "elixir": ("Programming Languages", "Functional", "Dynamic, functional language"),
    "haskell": ("Programming Languages", "Functional", "Purely functional programming language"),

    # Mobile
    "react-native": ("Mobile", "Cross-platform", "Framework for building native apps using React"),
    "flutter": ("Mobile", "Cross-platform", "UI toolkit for building natively compiled applications"),
    "ionic": ("Mobile", "Cross-platform", "Open source mobile UI toolkit"),
    "xamarin": ("Mobile", "Cross-platform", "Build native apps with .NET"),

    # LLM & AI Tools
    "langchain": ("AI/ML", "LLM", "Framework for developing LLM applications"),
    "openai": ("AI/ML", "LLM", "OpenAI API"),
    "anthropic": ("AI/ML", "LLM", "Anthropic Claude API"),
    "huggingface": ("AI/ML", "ML Models", "Platform for ML models"),
    "transformers": ("AI/ML", "NLP", "State-of-the-art NLP library"),

    # Miscellaneous
    "graphql": ("Backend", "API", "Query language for APIs"),
    "grpc": ("Backend", "RPC", "High performance RPC framework"),
    "rabbitmq": ("Backend", "Message Queue", "Message broker software"),
    "kafka": ("Backend", "Message Queue", "Distributed event streaming platform"),
    "nginx": ("DevOps", "Web Server", "HTTP and reverse proxy server"),
    "apache": ("DevOps", "Web Server", "HTTP Server Project"),
}


class TechClassifier:
    """
    Klasyfikuje nieznane technologie do kategorii
    """

    def __init__(self):
        """Initialize with known technologies database"""
        self.known_tech = KNOWN_TECHNOLOGIES

    def classify(self, tech_name: str) -> Tuple[str, str, float]:
        """
        Klasyfikuj technologię

        Args:
            tech_name: Nazwa technologii (np. "react", "fastapi", "kubernetes")

        Returns:
            Tuple (category, subcategory, confidence)
        """
        tech_lower = tech_name.lower().strip()

        # Exact match
        if tech_lower in self.known_tech:
            category, subcategory, _ = self.known_tech[tech_lower]
            return category, subcategory, 0.95

        # Partial match (fuzzy)
        for known_name, (category, subcategory, _) in self.known_tech.items():
            if known_name in tech_lower or tech_lower in known_name:
                return category, subcategory, 0.75

        # Heuristic matching
        category, subcategory, confidence = self._heuristic_classification(tech_name)

        return category, subcategory, confidence

    def _heuristic_classification(self, tech_name: str) -> Tuple[str, str, float]:
        """
        Klasyfikuj używając heurystyk

        Args:
            tech_name: Nazwa technologii

        Returns:
            Tuple (category, subcategory, confidence)
        """
        tech_lower = tech_name.lower()

        # Framework patterns
        if any(keyword in tech_lower for keyword in ['js', 'react', 'vue', 'angular', 'ui', 'component']):
            return "Frontend", "Framework", 0.60

        # Backend patterns
        if any(keyword in tech_lower for keyword in ['api', 'server', 'http', 'web', 'framework']):
            return "Backend", "Web Framework", 0.55

        # Database patterns
        if any(keyword in tech_lower for keyword in ['db', 'sql', 'database', 'orm', 'query']):
            return "Database", "Unknown", 0.50

        # DevOps patterns
        if any(keyword in tech_lower for keyword in ['docker', 'k8s', 'deploy', 'cloud', 'infra']):
            return "DevOps", "Unknown", 0.50

        # Testing patterns
        if any(keyword in tech_lower for keyword in ['test', 'mock', 'assert', 'spec']):
            return "Testing", "Unknown", 0.50

        # AI/ML patterns
        if any(keyword in tech_lower for keyword in ['ai', 'ml', 'model', 'neural', 'learn']):
            return "AI/ML", "Unknown", 0.50

        # Default
        return "Other", "Unknown", 0.30

    def get_description(self, tech_name: str) -> Optional[str]:
        """
        Pobierz opis technologii

        Args:
            tech_name: Nazwa technologii

        Returns:
            Opis lub None
        """
        tech_lower = tech_name.lower().strip()

        if tech_lower in self.known_tech:
            _, _, description = self.known_tech[tech_lower]
            return description

        return None

    def is_known(self, tech_name: str) -> bool:
        """
        Sprawdź czy technologia jest znana

        Args:
            tech_name: Nazwa technologii

        Returns:
            True jeśli znana
        """
        return tech_name.lower().strip() in self.known_tech


# ============================================================================
# CLI for testing
# ============================================================================

if __name__ == "__main__":
    """Test tech classifier"""
    print("Testing tech_classifier.py...")

    classifier = TechClassifier()

    # Test known technologies
    test_cases = [
        "react",
        "fastapi",
        "docker",
        "pytest",
        "unknown-framework-xyz",
        "my-custom-api-tool",
    ]

    print(f"\n🔍 Classifying {len(test_cases)} technologies:")
    for tech in test_cases:
        category, subcategory, confidence = classifier.classify(tech)
        known = "✅" if classifier.is_known(tech) else "🆕"
        print(f"  {known} {tech}: {category} → {subcategory} (confidence={confidence:.0%})")

    print(f"\n📚 Known technologies: {len(KNOWN_TECHNOLOGIES)}")
