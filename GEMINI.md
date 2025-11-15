# Project Overview

This is a market research SaaS platform called "Sight" that uses AI to simulate focus groups. It allows users to create research projects, generate AI-powered personas based on specific demographics, and then run virtual focus groups and surveys with these personas. The platform also provides analysis of the results, including graph-based analysis of concepts using Neo4j.

## Architecture

The application is built with a modern web stack:

*   **Frontend:** A React single-page application (SPA) built with Vite. It uses TypeScript, TanStack Query for data fetching, Zustand for state management, and Radix UI for headless UI components.
*   **Backend:** A Python-based API built with the FastAPI framework. It uses a PostgreSQL database for primary data storage, Redis for caching, and a Neo4j graph database for knowledge graph analysis.
*   **AI:** The AI capabilities are powered by Google Gemini, orchestrated through the LangChain library.
*   **Infrastructure:** The entire application is containerized using Docker and can be run locally with Docker Compose. It's also designed for deployment on Google Cloud Run.

## Key Features

*   **AI-powered Persona Generation:** Creates realistic user personas based on defined demographic targets.
*   **Virtual Focus Groups:** Simulates discussions between AI personas to gather qualitative feedback.
*   **Surveys:** Allows for quantitative data collection from the generated personas.
*   **Graph-based Analysis:** Extracts key concepts and relationships from the collected data and visualizes them as a knowledge graph in Neo4j.
*   **RAG (Retrieval-Augmented Generation):** Utilizes a hybrid search approach for advanced data retrieval.

# Building and Running

## Prerequisites

*   Docker and Docker Compose
*   A Google API key with access to the Gemini models.

## Local Development

1.  **Set up environment variables:**
    *   Copy the `.env.example` file to `.env`.
    *   Open the `.env` file and add your Google API key to the `GOOGLE_API_KEY` variable.
    *   Generate a secret key by running `openssl rand -hex 32` in your terminal and add it to the `SECRET_KEY` variable.

2.  **Start the application:**
    ```bash
    docker-compose up -d
    ```

3.  **Access the application:**
    *   **Frontend:** [http://localhost:5173](http://localhost:5173)
    *   **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

# Development Conventions

## Backend

*   The backend code is located in the `app` directory.
*   The main application entry point is `app/main.py`.
*   API endpoints are organized into modules within the `app/api` directory.
*   Database models are defined in `app/models`.
*   The application uses a centralized configuration system located in the `config` directory.
*   Tests are written using `pytest` and are located in the `tests` directory. To run the tests, use the following command:
    ```bash
    pytest -v
    ```

## Frontend

*   The frontend code is located in the `frontend` directory.
*   The main application entry point is `frontend/src/main.tsx`.
*   The frontend uses Vite for development and building.
*   To run the frontend in development mode, you can use the `npm run dev` command from within the `frontend` directory.
*   To build the frontend for production, use the `npm run build` command from within the `frontend` directory.
