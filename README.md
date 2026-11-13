# OpenAI Mock Service

FastAPI microservice implementing the subset of the OpenAI Responses API used
by the Tarot Interpretation Service. It produces deterministic readings without
network access, API billing, or a real OpenAI key. It is intended for local
development, integration tests, demos, and non-production environments.

## Request flow

```text
Browser
  -> tarot-frontend:80
  -> tarot-backend:8000/api/tarot/interpretations
  -> openai-mock:8080/v1/responses
```

The backend needs no code change. It uses:

```text
OPENAI_BASE_URL=http://openai-mock:8080/v1
OPENAI_API_KEY=sk-mock-local
```

## Project structure

```text
app/
├── main.py                         # FastAPI routes, auth, and scenarios
├── settings.py                     # Environment configuration
├── schemas.py                      # Request and error models
├── errors.py                       # OpenAI-style error responses
└── services/
    ├── prompt_parser.py            # Normalizes input and extracts tarot fields
    ├── tarot_response_generator.py # Deterministic two-paragraph reading
    └── response_factory.py         # OpenAI Responses API envelope
tests/                              # API and behavior tests
k8s/                                # ConfigMap, Deployment, Service, Kustomize
.github/workflows/main.yml           # Lint, test, build, and GHCR publication
```

## API input and output

```http
POST /v1/responses
Authorization: Bearer sk-mock-local
Content-Type: application/json
```

Minimal input:

```json
{
  "model": "gpt-4.1-mini",
  "input": "Pregunta: ¿Qué necesito entender hoy?\nCarta: El Mago\nSignificado base: Voluntad y acción."
}
```

`input` may be a string or a Responses-style list of messages. The tarot
backend sends a string. Additional fields are accepted and ignored so the
backend can evolve without breaking the mock. Streaming is not implemented;
`stream: true` returns HTTP `400`.

Successful output excerpt:

```json
{
  "id": "resp_mock_...",
  "object": "response",
  "status": "completed",
  "model": "gpt-4.1-mini",
  "output": [
    {
      "type": "message",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "El Mago aparece como una invitación...",
          "annotations": [],
          "logprobs": []
        }
      ]
    }
  ],
  "usage": {
    "input_tokens": 25,
    "output_tokens": 54,
    "total_tokens": 79
  }
}
```

The backend reads `output[].content[].text`, matching the Responses API wire
shape. Token counts are approximations.

## Health endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Basic service response |
| `GET /health/live` | Kubernetes liveness probe |
| `GET /health/ready` | Kubernetes and Compose readiness probe |
| `GET /docs` | Interactive OpenAPI documentation |

## Configuration and failure simulation

| Variable | Default | Purpose |
| --- | --- | --- |
| `MOCK_API_KEY` | `sk-mock-local` | Required bearer token |
| `MOCK_SCENARIO` | `success` | Global response scenario |
| `MOCK_DELAY_MS` | `0` | Artificial latency before every response |
| `MOCK_TIMEOUT_SECONDS` | `30` | Delay used by `timeout` |
| `ALLOW_SCENARIO_HEADER` | `false` | Accept `X-Mock-Scenario` per request |
| `LOG_PROMPTS` | `false` | Log full prompts; keep disabled for privacy |

| Scenario | Mock response | Backend result |
| --- | --- | --- |
| `success` | HTTP `200`, generated text | HTTP `200` |
| `unauthorized` | HTTP `401` | HTTP `503` |
| `rate_limit` | HTTP `429` | HTTP `503` |
| `server_error` | HTTP `500` | HTTP `503` |
| `empty` | HTTP `200`, empty text | HTTP `503` |
| `timeout` | Sleeps for configured duration | Backend timeout, then `503` |

When `ALLOW_SCENARIO_HEADER=true`, a test may select a scenario without a
restart:

```bash
curl -X POST http://localhost:8080/v1/responses \
  -H 'Authorization: Bearer sk-mock-local' \
  -H 'Content-Type: application/json' \
  -H 'X-Mock-Scenario: rate_limit' \
  -d '{"model":"gpt-4.1-mini","input":"hello"}'
```

## Run directly with Python

```bash
cp .env.example .env
make install
make run
```

The API listens on <http://localhost:8080> and its docs are at
<http://localhost:8080/docs>.

Quality commands:

```bash
make format
make lint
make test
make docker-build
```

## Run the complete application locally

From `tarot/infra`:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up --build
```

Open <http://localhost:5174>, reveal a card, enter a question, and press
**Interpretar**. The request passes through frontend and backend to this mock.
No real OpenAI key is needed.

Useful checks:

```bash
curl http://localhost:8080/health/ready
curl http://localhost:8000/health/ready
docker compose -f docker-compose.yml -f docker-compose.local.yml logs -f \
  openai-mock backend
```

Stop the stack:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml down
```

## GitHub Actions and GHCR

The workflow runs for pull requests and pushes to `main`. It installs Python
3.13 dependencies, runs Black and Flake8, runs Pytest, builds the image, and on
a push publishes `latest` and the commit SHA to GHCR.

For the image referenced by Kubernetes, create this GitHub repository:

```text
arcane-tarot/openai-mock-service
```

The workflow uses `GITHUB_TOKEN`. Ensure GitHub Actions may write packages. If
the package is private, Kubernetes also needs the existing `ghcr-credentials`
image pull secret.

## Kubernetes

After publishing the image:

```bash
kubectl apply -f ../infra/k8s/namespace.yaml
kubectl apply -k k8s
kubectl apply -f ../infra/k8s/backend-config.yaml
kubectl apply -k ../tarot-interpretation-service/k8s
kubectl apply -k ../tarot-frontend/k8s
```

The mock remains internal at `http://openai-mock:8080`. The existing backend
Secret must contain the matching non-production key:

```bash
kubectl -n tarot create secret generic tarot-backend-secrets \
  --from-literal=OPENAI_API_KEY=sk-mock-local \
  --dry-run=client -o yaml | kubectl apply -f -
```

Verify deployment:

```bash
kubectl -n tarot rollout status deployment/openai-mock
kubectl -n tarot get pods,services
kubectl -n tarot logs deployment/openai-mock
```

## Limitations

- Non-streaming text responses only.
- No tools, images, audio, stored responses, or conversation state.
- The generated reading is a deterministic template, not AI inference.
- Do not expose this mock publicly or reuse its default key as a real secret.
