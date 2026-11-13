import math
import time
import uuid


def _token_count(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def build_response(model: str, prompt: str, output_text: str) -> dict:
    created_at = int(time.time())
    response_id = f"resp_mock_{uuid.uuid4().hex}"
    message_id = f"msg_mock_{uuid.uuid4().hex}"
    input_tokens = _token_count(prompt)
    output_tokens = _token_count(output_text)

    return {
        "id": response_id,
        "object": "response",
        "created_at": created_at,
        "status": "completed",
        "completed_at": created_at,
        "error": None,
        "incomplete_details": None,
        "instructions": None,
        "max_output_tokens": None,
        "model": model,
        "output": [
            {
                "id": message_id,
                "type": "message",
                "status": "completed",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": output_text,
                        "annotations": [],
                        "logprobs": [],
                    }
                ],
            }
        ],
        "parallel_tool_calls": True,
        "previous_response_id": None,
        "reasoning": {"effort": None, "summary": None},
        "store": True,
        "temperature": 1.0,
        "text": {"format": {"type": "text"}},
        "tool_choice": "auto",
        "tools": [],
        "top_p": 1.0,
        "truncation": "disabled",
        "usage": {
            "input_tokens": input_tokens,
            "input_tokens_details": {"cached_tokens": 0},
            "output_tokens": output_tokens,
            "output_tokens_details": {"reasoning_tokens": 0},
            "total_tokens": input_tokens + output_tokens,
        },
        "metadata": {},
    }
