import asyncio
import logging
import secrets
import time

from fastapi import FastAPI, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.errors import openai_error
from app.schemas import ResponseRequest
from app.services.prompt_parser import normalize_input, parse_tarot_prompt
from app.services.response_factory import build_response
from app.services.tarot_response_generator import generate_interpretation
from app.settings import MockScenario, Settings

logger = logging.getLogger("openai_mock")


def create_app(settings: Settings | None = None) -> FastAPI:
    service_settings = settings or Settings()
    application = FastAPI(
        title="OpenAI Mock Service",
        version="1.0.0",
        description="Deterministic subset of the OpenAI Responses API.",
    )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        first_error = exc.errors()[0] if exc.errors() else {}
        location = first_error.get("loc", [])
        param = str(location[-1]) if location else None
        return openai_error(
            400,
            first_error.get("msg", "Invalid request"),
            "invalid_request_error",
            "invalid_request",
            param,
        )

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/health/live")
    async def liveness() -> dict[str, str]:
        return {"status": "alive"}

    @application.get("/health/ready")
    async def readiness() -> dict[str, str]:
        return {"status": "ready", "mode": service_settings.mock_scenario}

    @application.post("/v1/responses")
    async def create_response(
        payload: ResponseRequest,
        authorization: str | None = Header(default=None),
        x_mock_scenario: str | None = Header(default=None),
    ):
        started_at = time.monotonic()
        if not _authorized(authorization, service_settings.mock_api_key):
            return _unauthorized()

        scenario = _select_scenario(
            service_settings,
            x_mock_scenario,
        )
        scenario_error = await _apply_scenario(scenario, service_settings)
        if scenario_error is not None:
            return scenario_error

        if payload.stream:
            return openai_error(
                400,
                "Streaming is not supported by this mock",
                "invalid_request_error",
                "unsupported_parameter",
                "stream",
            )

        prompt = normalize_input(payload.input)
        if not prompt:
            return openai_error(
                400,
                "Input must contain text",
                "invalid_request_error",
                "invalid_value",
                "input",
            )

        if service_settings.log_prompts:
            logger.info("mock prompt model=%s input=%r", payload.model, prompt)

        if scenario == "empty":
            output_text = ""
        else:
            tarot_prompt = parse_tarot_prompt(prompt)
            output_text = generate_interpretation(
                tarot_prompt,
                f"{payload.model}\n{prompt}",
            )

        response = build_response(payload.model, prompt, output_text)
        elapsed_ms = round((time.monotonic() - started_at) * 1000, 2)
        logger.info(
            "response completed model=%s scenario=%s latency_ms=%s",
            payload.model,
            scenario,
            elapsed_ms,
        )
        return response

    return application


def _authorized(authorization: str | None, expected_key: str) -> bool:
    if not authorization or not authorization.startswith("Bearer "):
        return False
    supplied_key = authorization.removeprefix("Bearer ")
    return secrets.compare_digest(supplied_key, expected_key)


def _select_scenario(settings: Settings, header: str | None) -> MockScenario:
    allowed = {
        "success",
        "unauthorized",
        "rate_limit",
        "server_error",
        "empty",
        "timeout",
    }
    if settings.allow_scenario_header and header in allowed:
        return header  # type: ignore[return-value]
    return settings.mock_scenario


async def _apply_scenario(
    scenario: MockScenario,
    settings: Settings,
) -> JSONResponse | None:
    if settings.mock_delay_ms:
        await asyncio.sleep(settings.mock_delay_ms / 1000)
    if scenario == "timeout":
        await asyncio.sleep(settings.mock_timeout_seconds)
        return None
    if scenario == "unauthorized":
        return _unauthorized()
    if scenario == "rate_limit":
        return openai_error(
            429,
            "Rate limit reached for mock model",
            "rate_limit_error",
            "rate_limit_exceeded",
        )
    if scenario == "server_error":
        return openai_error(
            500,
            "The mock service encountered an internal error",
            "server_error",
            "server_error",
        )
    return None


def _unauthorized() -> JSONResponse:
    return openai_error(
        401,
        "Incorrect API key provided",
        "invalid_request_error",
        "invalid_api_key",
    )


app = create_app()
