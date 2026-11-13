from fastapi.testclient import TestClient

from app.main import create_app
from app.settings import Settings

PROMPT = """Eres una lectora de tarot clara, compasiva y practica.

Pregunta: ¿Qué necesito entender sobre esta decisión?
Tipo de mazo seleccionado: major
Carta: El Mago
Tipo de carta: Arcano mayor (major)
Significado base: Voluntad, recursos y acción enfocada.
"""


def client(**overrides) -> TestClient:
    settings = Settings(mock_api_key="test-key", **overrides)
    return TestClient(create_app(settings))


def request_payload(**overrides) -> dict:
    payload = {"model": "gpt-4.1-mini", "input": PROMPT}
    payload.update(overrides)
    return payload


def test_health_endpoints():
    test_client = client()

    assert test_client.get("/health").json() == {"status": "ok"}
    assert test_client.get("/health/live").json() == {"status": "alive"}
    assert test_client.get("/health/ready").json() == {
        "status": "ready",
        "mode": "success",
    }


def test_responses_endpoint_returns_openai_shape():
    test_client = client()
    response = test_client.post(
        "/v1/responses",
        headers={"Authorization": "Bearer test-key"},
        json=request_payload(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["object"] == "response"
    assert payload["status"] == "completed"
    assert payload["model"] == "gpt-4.1-mini"
    assert payload["output"][0]["type"] == "message"
    text = payload["output"][0]["content"][0]["text"]
    assert "El Mago" in text
    assert "¿Qué necesito entender sobre esta decisión?" in text
    assert payload["usage"]["total_tokens"] > 0


def test_generation_is_deterministic():
    test_client = client()
    headers = {"Authorization": "Bearer test-key"}

    first = test_client.post(
        "/v1/responses", headers=headers, json=request_payload()
    ).json()
    second = test_client.post(
        "/v1/responses", headers=headers, json=request_payload()
    ).json()

    first_text = first["output"][0]["content"][0]["text"]
    second_text = second["output"][0]["content"][0]["text"]
    assert first_text == second_text


def test_requires_valid_bearer_token():
    response = client().post("/v1/responses", json=request_payload())

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_api_key"


def test_validation_errors_use_openai_error_envelope():
    response = client().post(
        "/v1/responses",
        headers={"Authorization": "Bearer test-key"},
        json={"model": "gpt-4.1-mini"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["type"] == "invalid_request_error"
    assert response.json()["error"]["param"] == "input"


def test_streaming_is_rejected_explicitly():
    response = client().post(
        "/v1/responses",
        headers={"Authorization": "Bearer test-key"},
        json=request_payload(stream=True),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "unsupported_parameter"


def test_rate_limit_scenario():
    response = client(mock_scenario="rate_limit").post(
        "/v1/responses",
        headers={"Authorization": "Bearer test-key"},
        json=request_payload(),
    )

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "rate_limit_exceeded"


def test_empty_scenario_has_no_output_text():
    response = client(mock_scenario="empty").post(
        "/v1/responses",
        headers={"Authorization": "Bearer test-key"},
        json=request_payload(),
    )

    assert response.status_code == 200
    assert response.json()["output"][0]["content"][0]["text"] == ""


def test_scenario_header_is_opt_in():
    response = client(allow_scenario_header=True).post(
        "/v1/responses",
        headers={
            "Authorization": "Bearer test-key",
            "X-Mock-Scenario": "server_error",
        },
        json=request_payload(),
    )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "server_error"
