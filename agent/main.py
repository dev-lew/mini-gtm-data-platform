import os
import sys

from openrouter import OpenRouter
from tools import DUCKDB_TOOL, execute_duckdb_tool_call

if (API_KEY := os.getenv("OPENROUTER_API_KEY")) is None:
    sys.exit("The OPENROUTER_API_KEY env variable must be set")

MODEL = "z-ai/glm-4.5-air:free"
MAX_TOOL_ROUNDS = 25

SYSTEM_PROMPT = """
You are a GTM research and sales outreach agent.

Given an account or prospect, use the query_duckdb tool to pull together relevant
internal context from the local GTM warehouse, then draft a personalized outreach
email. Discover the warehouse schema dynamically before writing detailed queries;
do not assume table or column names.

Gather useful context across these areas when available:
- deal history and opportunity status
- product usage and adoption
- call intelligence, objections, pain points, and next steps
- marketing engagement, campaigns, and lead activity

Keep tool queries read-only, focused, and reasonably small. After researching,
return:
1. A concise context summary with the strongest personalization signals.
2. A personalized outreach email draft.
3. Any important data gaps or assumptions.
""".strip()


def main() -> None:
    target = " ".join(sys.argv[1:]).strip()

    if not target:
        target = input("Account or prospect to research: ").strip()

    if not target:
        sys.exit("Provide an account or prospect name.")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Pull together internal context for this account or prospect: {target}. "
                "Use the DuckDB tool to research the warehouse, then draft a personalized outreach email."
            ),
        },
    ]

    with OpenRouter(api_key=API_KEY) as client:
        for _ in range(MAX_TOOL_ROUNDS):
            response = client.chat.send(
                model=MODEL,
                messages=messages,
                tools=[DUCKDB_TOOL],
                tool_choice="auto",
            )

            assistant_message = response.choices[0].message

            messages.append(
                assistant_message.model_dump(
                    by_alias=True,
                    exclude_none=True,
                    exclude_unset=True,
                )
            )

            tool_calls = assistant_message.tool_calls or []

            if not tool_calls:
                print(assistant_message.content or "")
                return

            for tool_call in tool_calls:
                messages.append(execute_duckdb_tool_call(tool_call))

    sys.exit(f"Stopped after {MAX_TOOL_ROUNDS} tool rounds without a final answer.")


if __name__ == "__main__":
    main()
