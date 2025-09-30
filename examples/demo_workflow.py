#!/usr/bin/env python3
"""
Demo workflow showing complete platform usage
"""
import asyncio
import httpx
from typing import Dict, Any, List

BASE_URL = "http://localhost:8000/api/v1"


async def create_project() -> str:
    """Step 1: Create a research project"""
    print("\n=== Step 1: Creating Project ===")

    project_data = {
        "name": "Mobile App Launch Research",
        "description": "Market research for new fitness tracking app",
        "target_demographics": {
            "age": {
                "18-24": 0.20,
                "25-34": 0.30,
                "35-44": 0.25,
                "45-54": 0.15,
                "55+": 0.10,
            },
            "gender": {"male": 0.48, "female": 0.52},
            "education": {
                "high_school": 0.25,
                "bachelors": 0.45,
                "masters": 0.20,
                "phd": 0.10,
            },
            "income": {
                "<30k": 0.15,
                "30k-60k": 0.30,
                "60k-100k": 0.35,
                "100k+": 0.20,
            },
            "location": {"urban": 0.65, "suburban": 0.25, "rural": 0.10},
        },
        "target_sample_size": 50,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/projects", json=project_data)
        response.raise_for_status()
        project = response.json()

    print(f"✅ Project created: {project['id']}")
    print(f"   Name: {project['name']}")
    return project["id"]


async def generate_personas(project_id: str, adversarial: bool = False) -> None:
    """Step 2: Generate synthetic personas"""
    print(f"\n=== Step 2: Generating Personas (Adversarial={adversarial}) ===")

    request_data = {"num_personas": 50, "adversarial_mode": adversarial}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/projects/{project_id}/personas/generate", json=request_data
        )
        response.raise_for_status()
        result = response.json()

    print(f"✅ Persona generation started")
    print(f"   Generating {result['num_personas']} personas...")

    # Wait for completion (in production, use webhooks or polling)
    await asyncio.sleep(30)

    # Check results
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/projects/{project_id}/personas")
        personas = response.json()

    print(f"✅ Generated {len(personas)} personas")

    # Show sample persona
    if personas:
        sample = personas[0]
        print(f"\n   Sample Persona:")
        print(f"   - Age: {sample['age']}, Gender: {sample['gender']}")
        print(f"   - Location: {sample['location']}")
        print(f"   - Education: {sample['education_level']}")
        print(f"   - Big Five: O={sample['openness']:.2f}, C={sample['conscientiousness']:.2f}")


async def create_and_run_focus_group(project_id: str) -> str:
    """Step 3: Create and run focus group"""
    print("\n=== Step 3: Running Focus Group ===")

    # Get personas
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/projects/{project_id}/personas")
        personas = response.json()

    persona_ids = [p["id"] for p in personas[:20]]  # Use first 20 personas

    # Create focus group
    focus_group_data = {
        "name": "Initial Product Feedback",
        "description": "Gathering first impressions and concerns",
        "persona_ids": persona_ids,
        "questions": [
            "What is your first impression of a fitness tracking app?",
            "What features would be most important to you?",
            "What concerns would you have about using such an app?",
            "How much would you be willing to pay monthly for this service?",
            "Would you recommend this to friends? Why or why not?",
        ],
        "mode": "normal",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/projects/{project_id}/focus-groups", json=focus_group_data
        )
        response.raise_for_status()
        focus_group = response.json()

    focus_group_id = focus_group["id"]
    print(f"✅ Focus group created: {focus_group_id}")

    # Run focus group
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(f"{BASE_URL}/focus-groups/{focus_group_id}/run")
        response.raise_for_status()

    print(f"✅ Focus group execution started...")

    # Wait for completion
    await asyncio.sleep(45)

    # Get results
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/focus-groups/{focus_group_id}")
        results = response.json()

    print(f"\n   Performance Metrics:")
    metrics = results["metrics"]
    print(f"   - Total execution time: {metrics['total_execution_time_ms']}ms")
    print(f"   - Avg response time: {metrics['avg_response_time_ms']:.1f}ms")
    print(f"   - Consistency error rate: {metrics['consistency_error_rate']:.2%}")

    requirements = metrics["meets_requirements"]
    print(f"\n   Requirements Met:")
    print(f"   - Avg response <3s: {'✅' if requirements['avg_response_time'] else '❌'}")
    print(
        f"   - Total time <30s: {'✅' if requirements['total_execution_time'] else '❌'}"
    )
    print(
        f"   - Error rate <5%: {'✅' if requirements['consistency_error_rate'] else '❌'}"
    )

    return focus_group_id


async def analyze_polarization(focus_group_id: str) -> None:
    """Step 4: Analyze polarization"""
    print("\n=== Step 4: Analyzing Polarization ===")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/focus-groups/{focus_group_id}/analyze-polarization"
        )
        response.raise_for_status()
        analysis = response.json()

    print(f"✅ Polarization Analysis Complete")
    print(f"   Overall Polarization Score: {analysis['overall_polarization_score']:.3f}")
    print(f"   Level: {analysis['polarization_level']}")

    print(f"\n   Question-by-Question Analysis:")
    for i, question_analysis in enumerate(analysis["questions"][:3], 1):
        print(f"\n   Question {i}: {question_analysis['question'][:60]}...")
        print(f"   - Polarization: {question_analysis['polarization_score']:.3f}")
        print(f"   - Clusters: {question_analysis['num_clusters']}")
        print(f"   - Responses: {question_analysis['num_responses']}")


async def show_responses(focus_group_id: str) -> None:
    """Step 5: Show sample responses"""
    print("\n=== Step 5: Sample Responses ===")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/focus-groups/{focus_group_id}/responses")
        data = response.json()

    print(f"✅ Retrieved {data['total_responses']} total responses")

    # Show first question's responses
    responses_by_question = data["responses_by_question"]
    first_question = list(responses_by_question.keys())[0]
    responses = responses_by_question[first_question]

    print(f"\n   Question: {first_question}")
    print(f"   Sample Responses:")

    for i, resp in enumerate(responses[:3], 1):
        print(f"\n   {i}. [{resp['consistency_score']:.2f} consistency]")
        print(f"      {resp['response'][:150]}...")


async def main():
    """Run complete demo workflow"""
    print("=" * 60)
    print("Market Research SaaS Platform - Demo Workflow")
    print("=" * 60)

    try:
        # Step 1: Create project
        project_id = await create_project()

        # Step 2: Generate personas
        await generate_personas(project_id, adversarial=False)

        # Step 3: Run focus group
        focus_group_id = await create_and_run_focus_group(project_id)

        # Step 4: Analyze polarization
        await analyze_polarization(focus_group_id)

        # Step 5: Show sample responses
        await show_responses(focus_group_id)

        print("\n" + "=" * 60)
        print("✅ Demo workflow completed successfully!")
        print("=" * 60)

        print("\nNext Steps:")
        print(f"1. View project details: GET {BASE_URL}/projects/{project_id}")
        print(f"2. View focus group: GET {BASE_URL}/focus-groups/{focus_group_id}")
        print(f"3. Generate adversarial personas for stress testing")
        print(f"4. Run additional focus groups with different questions")

    except httpx.HTTPError as e:
        print(f"\n❌ Error: {e}")
        print(f"   Make sure the API server is running on {BASE_URL}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())