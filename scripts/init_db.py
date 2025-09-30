#!/usr/bin/env python3
"""
Initialize database with tables and pgvector extension
"""
import asyncio
from sqlalchemy import text
from app.db import engine, Base
from app.models import Project, Persona, PersonaEvent, PersonaResponse, FocusGroup


async def init_db():
    """Initialize database"""
    print("Creating database tables...")

    async with engine.begin() as conn:
        # Enable pgvector extension
        print("Enabling pgvector extension...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # Create all tables
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)

    print("Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(init_db())