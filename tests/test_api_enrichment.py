from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_enrich_and_search_vulnerability_through_api():
    vulnerability = {
        "vulnerability_id": "CVE-2024-4242",
        "title": "SQL injection in authentication endpoint",
        "description": "An attacker can bypass authentication using crafted SQL payloads.",
        "severity": "high",
        "cvss_score": 8.1,
        "source": "test",
        "language": "en",
    }

    enrich_response = client.post(
        "/vulnerabilities/enrich",
        json=vulnerability,
    )

    assert enrich_response.status_code == 200
    assert enrich_response.json()["status"] == "enriched"

    search_response = client.post(
        "/vulnerabilities/search",
        json={
            "query": "authentication bypass with SQL injection",
            "limit": 3,
        },
    )

    assert search_response.status_code == 200
    body = search_response.json()

    assert body["query"] == "authentication bypass with SQL injection"
    assert len(body["results"]) >= 1