#!/usr/bin/env python3
"""
Script do weryfikacji/utworzenia testowego projektu

Sprawdza czy projekt ba3c1dbc-ed22-4e31-bf96-ccd7b7edc416 istnieje w DB.
Jeśli nie - tworzy go z demo user.
Jeśli istnieje ale is_active=False - zmienia na True.

Usage:
    python scripts/verify_test_project.py
"""

import asyncio
import os
import sys
from uuid import UUID
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.project import Project
from app.models import User


# Target project UUID
TARGET_PROJECT_ID = UUID("ba3c1dbc-ed22-4e31-bf96-ccd7b7edc416")


async def main():
    """Main function"""
    # Get DATABASE_URL from environment
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://sight:dev_password_change_in_prod@localhost:5433/sight_db"
    )

    print(f"🔌 Connecting to database...")
    print(f"   URL: {database_url.split('@')[1]}")  # Hide credentials

    # Create engine
    engine = create_async_engine(database_url, echo=False)

    # Create async session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as db:
        # 1. Check if project exists
        print(f"\n🔍 Checking if project {TARGET_PROJECT_ID} exists...")

        stmt = select(Project).where(Project.id == TARGET_PROJECT_ID)
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()

        if project:
            print(f"✅ Project found!")
            print(f"   Name: {project.name}")
            print(f"   Owner ID: {project.owner_id}")
            print(f"   Is Active: {project.is_active}")
            print(f"   Created: {project.created_at}")

            # Check if active
            if not project.is_active:
                print(f"\n⚠️  Project is inactive (is_active=False)")
                print(f"   Setting is_active=True...")

                project.is_active = True
                await db.commit()

                print(f"✅ Project activated!")
            else:
                print(f"\n✅ Project is active and ready to use!")

            return

        # 2. Project doesn't exist - need to create
        print(f"❌ Project not found!")
        print(f"\n🔍 Looking for demo user to assign project...")

        # Find demo user (email=demo@sight.pl)
        stmt = select(User).where(User.email == "demo@sight.pl")
        result = await db.execute(stmt)
        demo_user = result.scalar_one_or_none()

        if not demo_user:
            # Try to find any user
            print(f"⚠️  Demo user not found, looking for any active user...")
            stmt = select(User).where(User.is_active == True).limit(1)
            result = await db.execute(stmt)
            demo_user = result.scalar_one_or_none()

        if not demo_user:
            print(f"\n❌ ERROR: No users found in database!")
            print(f"   Please create a user first before creating a project.")
            print(f"\n   You can create a user via API:")
            print(f"   POST /api/v1/auth/register")
            print(f"   {{\"email\": \"demo@sight.pl\", \"password\": \"demo123\"}}")
            return

        print(f"✅ Found user: {demo_user.email} (ID: {demo_user.id})")

        # 3. Create project
        print(f"\n🔨 Creating project {TARGET_PROJECT_ID}...")

        new_project = Project(
            id=TARGET_PROJECT_ID,
            owner_id=demo_user.id,
            name="Test Workflow Project",
            description="Automatically created test project for workflow template instantiation",
            target_audience="Tech-savvy millennials (25-35 years old)",
            research_objectives="Test product research workflow",
            target_demographics={
                "age_group": {
                    "18-24": 0.2,
                    "25-34": 0.4,
                    "35-44": 0.25,
                    "45-54": 0.1,
                    "55+": 0.05
                },
                "gender": {
                    "male": 0.5,
                    "female": 0.5
                },
                "location": {
                    "warszawa": 0.3,
                    "krakow": 0.2,
                    "wroclaw": 0.15,
                    "poznan": 0.15,
                    "gdansk": 0.1,
                    "lodz": 0.1
                }
            },
            target_sample_size=20,
            is_active=True
        )

        db.add(new_project)
        await db.commit()
        await db.refresh(new_project)

        print(f"✅ Project created successfully!")
        print(f"   ID: {new_project.id}")
        print(f"   Name: {new_project.name}")
        print(f"   Owner: {demo_user.email}")
        print(f"   Target Sample Size: {new_project.target_sample_size}")
        print(f"\n🎉 You can now use this project_id in workflow template instantiation!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
