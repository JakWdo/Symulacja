#!/usr/bin/env python3
"""
Example script for testing Market Research SaaS API using Python
Run this script to create a project and generate personas programmatically
"""

import requests
import json
import time
from typing import Dict, List, Optional

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"


class MarketResearchAPI:
    """Client for Market Research SaaS API"""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    # ==================== Projects ====================

    def create_project(
        self,
        name: str,
        description: Optional[str],
        target_demographics: Dict,
        target_sample_size: int = 100
    ) -> Dict:
        """Create a new research project"""
        payload = {
            "name": name,
            "description": description,
            "target_demographics": target_demographics,
            "target_sample_size": target_sample_size
        }

        response = self.session.post(f"{self.base_url}/projects", json=payload)
        response.raise_for_status()
        return response.json()

    def list_projects(self) -> List[Dict]:
        """Get all projects"""
        response = self.session.get(f"{self.base_url}/projects")
        response.raise_for_status()
        return response.json()

    def get_project(self, project_id: str) -> Dict:
        """Get project details"""
        response = self.session.get(f"{self.base_url}/projects/{project_id}")
        response.raise_for_status()
        return response.json()

    # ==================== Personas ====================

    def generate_personas(
        self,
        project_id: str,
        num_personas: int = 10,
        adversarial_mode: bool = False
    ) -> Dict:
        """Generate personas for a project"""
        payload = {
            "num_personas": num_personas,
            "adversarial_mode": adversarial_mode
        }

        response = self.session.post(
            f"{self.base_url}/projects/{project_id}/personas/generate",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def list_personas(self, project_id: str) -> List[Dict]:
        """Get all personas for a project"""
        response = self.session.get(f"{self.base_url}/projects/{project_id}/personas")
        response.raise_for_status()
        return response.json()

    def get_persona(self, persona_id: str) -> Dict:
        """Get persona details"""
        response = self.session.get(f"{self.base_url}/personas/{persona_id}")
        response.raise_for_status()
        return response.json()

    # ==================== Focus Groups ====================

    def create_focus_group(
        self,
        project_id: str,
        name: str,
        persona_ids: List[str],
        questions: List[str],
        description: Optional[str] = None,
        mode: str = "normal"
    ) -> Dict:
        """Create a focus group"""
        payload = {
            "name": name,
            "description": description,
            "persona_ids": persona_ids,
            "questions": questions,
            "mode": mode
        }

        response = self.session.post(
            f"{self.base_url}/projects/{project_id}/focus-groups",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def run_focus_group(self, focus_group_id: str) -> Dict:
        """Run a focus group simulation"""
        response = self.session.post(f"{self.base_url}/focus-groups/{focus_group_id}/run")
        response.raise_for_status()
        return response.json()

    def get_focus_group_responses(self, focus_group_id: str) -> Dict:
        """Get focus group responses"""
        response = self.session.get(f"{self.base_url}/focus-groups/{focus_group_id}/responses")
        response.raise_for_status()
        return response.json()

    # ==================== Analysis ====================

    def analyze_polarization(self, focus_group_id: str) -> Dict:
        """Analyze polarization in focus group"""
        response = self.session.post(
            f"{self.base_url}/focus-groups/{focus_group_id}/analyze-polarization"
        )
        response.raise_for_status()
        return response.json()


def example_workflow():
    """Complete example workflow"""

    # Initialize API client
    api = MarketResearchAPI()

    print("🚀 Market Research SaaS API Example")
    print("=" * 50)

    # 1. Create a project
    print("\n1️⃣  Creating project...")
    project = api.create_project(
        name="Consumer Electronics Study 2025",
        description="Understanding smartphone buying behavior across demographics",
        target_demographics={
            "age_group": {
                "18-24": 0.20,
                "25-34": 0.30,
                "35-44": 0.25,
                "45-54": 0.15,
                "55+": 0.10
            },
            "gender": {
                "male": 0.48,
                "female": 0.48,
                "non_binary": 0.04
            },
            "location": {
                "urban": 0.60,
                "suburban": 0.30,
                "rural": 0.10
            }
        },
        target_sample_size=20
    )

    project_id = project["id"]
    print(f"✅ Project created: {project['name']} (ID: {project_id})")

    # 2. Generate personas
    print("\n2️⃣  Generating personas...")
    print("   ⏳ This takes ~2-3 seconds per persona with Gemini API...")

    generation_response = api.generate_personas(
        project_id=project_id,
        num_personas=10,
        adversarial_mode=False
    )

    print(f"✅ Persona generation started: {generation_response['num_personas']} personas")

    # 3. Wait for personas to be generated (polling)
    print("\n3️⃣  Waiting for personas to be generated...")
    max_wait = 120  # 2 minutes max
    start_time = time.time()

    while time.time() - start_time < max_wait:
        personas = api.list_personas(project_id)

        if len(personas) >= 10:
            print(f"✅ All {len(personas)} personas generated!")
            break

        print(f"   ⏳ {len(personas)}/10 personas ready...")
        time.sleep(5)
    else:
        print("⚠️  Timeout waiting for personas")
        return

    # 4. Display persona details
    print("\n4️⃣  Persona examples:")
    for i, persona in enumerate(personas[:3], 1):
        print(f"\n   Persona #{i}:")
        print(f"   • Age: {persona['age']}, Gender: {persona['gender']}")
        print(f"   • Location: {persona['location']}")
        print(f"   • Education: {persona['education_level']}")
        print(f"   • Income: {persona['income_bracket']}")
        print(f"   • Values: {', '.join(persona['values'][:3])}")

    # 5. Create a focus group
    print("\n5️⃣  Creating focus group...")

    # Select random personas
    selected_persona_ids = [p["id"] for p in personas[:5]]

    focus_group = api.create_focus_group(
        project_id=project_id,
        name="Smartphone Feature Preferences",
        description="Understanding which features matter most",
        persona_ids=selected_persona_ids,
        questions=[
            "What factors are most important when buying a new smartphone?",
            "How do you feel about foldable phone screens?",
            "What would make you switch smartphone brands?"
        ],
        mode="normal"
    )

    focus_group_id = focus_group["id"]
    print(f"✅ Focus group created: {focus_group['name']} (ID: {focus_group_id})")

    # 6. Run focus group simulation
    print("\n6️⃣  Running focus group simulation...")
    print("   ⏳ This may take 30-60 seconds...")

    run_response = api.run_focus_group(focus_group_id)
    print(f"✅ {run_response['message']}")

    # Wait for completion
    print("\n7️⃣  Waiting for simulation to complete...")
    start_time = time.time()

    while time.time() - start_time < 120:
        try:
            responses = api.get_focus_group_responses(focus_group_id)

            if responses.get("responses"):
                print(f"✅ Focus group completed!")
                break
        except:
            pass

        print("   ⏳ Still running...")
        time.sleep(5)

    # 8. Display some responses
    if responses.get("responses"):
        print("\n8️⃣  Sample responses:")

        first_question = responses["responses"][0]
        print(f"\n   Question: {first_question['question']}")

        for i, response in enumerate(first_question["persona_responses"][:3], 1):
            print(f"\n   Response #{i}:")
            print(f"   {response['response_text'][:150]}...")

    # 9. Analyze polarization
    print("\n9️⃣  Analyzing polarization...")

    try:
        analysis = api.analyze_polarization(focus_group_id)
        print(f"✅ Polarization score: {analysis.get('overall_polarization_score', 'N/A')}")
        print(f"   Number of clusters: {len(analysis.get('clusters', []))}")
    except Exception as e:
        print(f"⚠️  Polarization analysis failed: {e}")

    print("\n" + "=" * 50)
    print("🎉 Example workflow completed successfully!")
    print(f"\n📊 View results at: http://localhost:5173")
    print(f"📖 API docs at: http://localhost:8000/docs")


def simple_test():
    """Simple test to check API connectivity"""

    api = MarketResearchAPI()

    try:
        projects = api.list_projects()
        print(f"✅ API is working! Found {len(projects)} existing projects.")
        return True
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        print("\n💡 Make sure the backend is running:")
        print("   docker compose up -d")
        return False


if __name__ == "__main__":
    print("Testing API connectivity...")

    if simple_test():
        print("\nStarting example workflow...\n")
        example_workflow()
    else:
        print("\nPlease start the services and try again.")
