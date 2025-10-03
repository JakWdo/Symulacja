#!/usr/bin/env python3
"""Test script to verify focus group response generation"""

import asyncio
import httpx
import time

BASE_URL = "http://localhost:8000/api/v1"

async def test_focus_group():
    async with httpx.AsyncClient(timeout=120.0) as client:
        # 1. Get project
        print("🔍 Getting project...")
        projects = await client.get(f"{BASE_URL}/projects")
        projects_data = projects.json()

        if not projects_data:
            print("❌ No projects found")
            return

        project_id = projects_data[0]["id"]
        print(f"✅ Project ID: {project_id}")

        # 2. Get personas
        print("\n🔍 Getting personas...")
        personas_resp = await client.get(f"{BASE_URL}/projects/{project_id}/personas")
        personas = personas_resp.json()

        if not personas:
            print("❌ No personas found")
            return

        persona_ids = [p["id"] for p in personas[:3]]  # Use first 3 personas
        print(f"✅ Using {len(persona_ids)} personas: {persona_ids}")

        # 3. Create focus group
        print("\n🔍 Creating focus group...")
        fg_data = {
            "name": "Test Focus Group - Response Verification",
            "description": "Testing LLM response generation",
            "persona_ids": persona_ids,
            "questions": [
                "What do you think about remote work?",
                "How has technology changed your daily life?"
            ],
            "mode": "normal"
        }

        fg_resp = await client.post(
            f"{BASE_URL}/projects/{project_id}/focus-groups",
            json=fg_data
        )
        focus_group = fg_resp.json()
        print(f"Focus group response: {focus_group}")

        if "id" not in focus_group:
            print(f"❌ Error creating focus group: {focus_group}")
            return False

        fg_id = focus_group["id"]
        print(f"✅ Focus group created: {fg_id}")

        # 4. Run focus group
        print("\n🚀 Running focus group...")
        run_resp = await client.post(f"{BASE_URL}/focus-groups/{fg_id}/run")
        print(f"✅ Focus group started: {run_resp.json()}")

        # 5. Wait for completion
        print("\n⏳ Waiting for completion...")
        for i in range(30):  # Max 30 seconds
            await asyncio.sleep(1)
            status_resp = await client.get(f"{BASE_URL}/focus-groups/{fg_id}")
            status = status_resp.json()

            if status["status"] == "completed":
                print(f"✅ Focus group completed in {status['metrics']['total_execution_time_ms']}ms")
                break
            elif status["status"] == "failed":
                print(f"❌ Focus group failed")
                return

            print(f"   Status: {status['status']} ({i+1}s)")

        # 6. Get responses
        print("\n🔍 Fetching responses...")
        resp_data = await client.get(f"{BASE_URL}/focus-groups/{fg_id}/responses")
        responses = resp_data.json()

        print(f"Response data: {responses}")

        print(f"\n📊 Results:")
        if "total_responses" in responses:
            print(f"Total responses: {responses['total_responses']}")
        else:
            print(f"Response structure: {list(responses.keys())}")

        # Check each question
        for q_data in responses["questions"]:
            print(f"\n❓ Question: {q_data['question']}")
            print(f"   Responses: {len(q_data['responses'])}")

            for i, resp in enumerate(q_data['responses'], 1):
                response_text = resp['response']
                print(f"   {i}. Persona {resp['persona_id'][:8]}...")

                if response_text and response_text.strip():
                    print(f"      ✅ Response: {response_text[:100]}...")
                else:
                    print(f"      ❌ EMPTY RESPONSE!")

        # Summary
        empty_count = sum(
            1 for q in responses["questions"]
            for r in q["responses"]
            if not r["response"] or not r["response"].strip()
        )
        total_count = responses["total_responses"]

        print(f"\n📈 Summary:")
        print(f"   Total responses: {total_count}")
        print(f"   Empty responses: {empty_count}")
        print(f"   Valid responses: {total_count - empty_count}")

        if empty_count > 0:
            print(f"\n❌ TEST FAILED: {empty_count} empty responses found!")
            return False
        else:
            print(f"\n✅ TEST PASSED: All responses generated successfully!")
            return True

if __name__ == "__main__":
    result = asyncio.run(test_focus_group())
    exit(0 if result else 1)
