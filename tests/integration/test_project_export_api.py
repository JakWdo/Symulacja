"""
Testy integracyjne dla API eksportu projektów do PDF i DOCX.

Ten moduł testuje:
- Eksport projektu do PDF
- Eksport projektu do DOCX
- Obsługa błędów (404, 403)
- Weryfikacja content-type i załączników
"""

import pytest
from uuid import uuid4

from tests.factories import project_payload


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_project_pdf_success(authenticated_client, test_project):
    """
    Test pomyślnego eksportu projektu do PDF.

    Weryfikuje:
    - Status 200 OK
    - Content-Type: application/pdf
    - Content-Disposition header z filename
    - Plik niepusty
    - Zawiera magiczne bajty PDF
    """
    client, user, headers = await authenticated_client

    response = client.get(
        f"/api/v1/projects/{test_project.id}/export/pdf",
        headers=headers,
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers.get("content-disposition", "")

    # Verify PDF content
    pdf_content = response.content
    assert len(pdf_content) > 0
    assert pdf_content[:4] == b"%PDF", "PDF magic bytes not found"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_project_pdf_with_full_personas(authenticated_client, test_project):
    """
    Test eksportu PDF z parametrem include_full_personas.

    Weryfikuje że query parameter działa poprawnie.
    """
    client, user, headers = await authenticated_client

    response = client.get(
        f"/api/v1/projects/{test_project.id}/export/pdf",
        params={"include_full_personas": True},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    pdf_content = response.content
    assert len(pdf_content) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_project_docx_success(authenticated_client, test_project):
    """
    Test pomyślnego eksportu projektu do DOCX.

    Weryfikuje:
    - Status 200 OK
    - Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document
    - Content-Disposition header
    - Plik niepusty
    - Zawiera ZIP signature (DOCX to zip)
    """
    client, user, headers = await authenticated_client

    response = client.get(
        f"/api/v1/projects/{test_project.id}/export/docx",
        headers=headers,
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in response.headers["content-type"]
    assert "attachment" in response.headers.get("content-disposition", "")

    # Verify DOCX content (DOCX is a ZIP file)
    docx_content = response.content
    assert len(docx_content) > 0
    assert docx_content[:2] == b"PK", "ZIP/DOCX magic bytes not found"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_project_docx_with_full_personas(authenticated_client, test_project):
    """
    Test eksportu DOCX z parametrem include_full_personas.
    """
    client, user, headers = await authenticated_client

    response = client.get(
        f"/api/v1/projects/{test_project.id}/export/docx",
        params={"include_full_personas": True},
        headers=headers,
    )

    assert response.status_code == 200
    docx_content = response.content
    assert len(docx_content) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_project_pdf_not_found(authenticated_client):
    """
    Test eksportu PDF dla nieistniejącego projektu.

    Weryfikuje:
    - Status 404 Not Found
    - Odpowiedź JSON z message
    """
    client, user, headers = await authenticated_client
    non_existent_id = str(uuid4())

    response = client.get(
        f"/api/v1/projects/{non_existent_id}/export/pdf",
        headers=headers,
    )

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_project_docx_not_found(authenticated_client):
    """
    Test eksportu DOCX dla nieistniejącego projektu.
    """
    client, user, headers = await authenticated_client
    non_existent_id = str(uuid4())

    response = client.get(
        f"/api/v1/projects/{non_existent_id}/export/docx",
        headers=headers,
    )

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_project_pdf_unauthorized(client, test_project):
    """
    Test eksportu PDF bez uwierzytelnienia.

    Weryfikuje:
    - Status 401 lub 403 (zależnie od middleware)
    """
    # Request bez headers (bez tokenu)
    response = client.get(f"/api/v1/projects/{test_project.id}/export/pdf")

    # Powinna być odmowa dostępu
    assert response.status_code in [401, 403]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_project_docx_unauthorized(client, test_project):
    """
    Test eksportu DOCX bez uwierzytelnienia.
    """
    response = client.get(f"/api/v1/projects/{test_project.id}/export/docx")

    assert response.status_code in [401, 403]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_project_pdf_filename_sanitized(authenticated_client, test_project):
    """
    Test czy nazwa pliku w Content-Disposition jest poprawnie sanitizowana.

    Weryfikuje że spacje są zastąpione podkreślnikami.
    """
    client, user, headers = await authenticated_client

    response = client.get(
        f"/api/v1/projects/{test_project.id}/export/pdf",
        headers=headers,
    )

    assert response.status_code == 200
    content_disposition = response.headers.get("content-disposition", "")

    # Filename powinien zawierać "projekt_" i kończyć się ".pdf"
    assert "projekt_" in content_disposition
    assert ".pdf" in content_disposition

    # Nie powinno być spacji w filename
    # Format: attachment; filename="projekt_nazwa.pdf"
    if "filename=" in content_disposition:
        filename_part = content_disposition.split("filename=")[1]
        assert " " not in filename_part.replace('"', ''), "Spaces should be replaced with underscores"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_empty_project_pdf(authenticated_client):
    """
    Test eksportu PDF dla projektu bez person, grup fokusowych i ankiet.

    Weryfikuje że eksport działa nawet dla pustych projektów.
    """
    client, user, headers = await authenticated_client

    # Create empty project
    project_data = project_payload(
        name="Empty Project",
        description="Project without data",
        target_demographics={
            "age_group": {"18-24": 0.5, "25-34": 0.5},
            "gender": {"male": 0.5, "female": 0.5},
        },
        target_sample_size=0,
    )

    create_response = client.post(
        "/api/v1/projects",
        json=project_data,
        headers=headers,
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Export empty project
    response = client.get(
        f"/api/v1/projects/{project_id}/export/pdf",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    pdf_content = response.content
    assert len(pdf_content) > 0
    assert pdf_content[:4] == b"%PDF"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_empty_project_docx(authenticated_client):
    """
    Test eksportu DOCX dla projektu bez danych.
    """
    client, user, headers = await authenticated_client

    # Create empty project
    project_data = project_payload(
        name="Empty DOCX Project",
        description="Project without data",
        target_demographics={
            "age_group": {"18-24": 1.0},
            "gender": {"male": 1.0},
        },
        target_sample_size=0,
    )

    create_response = client.post(
        "/api/v1/projects",
        json=project_data,
        headers=headers,
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Export empty project
    response = client.get(
        f"/api/v1/projects/{project_id}/export/docx",
        headers=headers,
    )

    assert response.status_code == 200
    docx_content = response.content
    assert len(docx_content) > 0
    assert docx_content[:2] == b"PK"
