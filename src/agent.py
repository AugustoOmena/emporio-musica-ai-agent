import os
import json
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
import litellm
from src.prompts import build_system_prompt
from src.tools import AVAILABLE_TOOLS, TOOLS_SCHEMA

load_dotenv()


class StoreAgent:
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or os.getenv("DEFAULT_MODEL", "gemini/gemini-3.5-flash-lite")
        self.system_prompt = build_system_prompt()
        self.api_key = os.getenv("GEMINI_API_KEY")

    def _execute_tool(self, tool_name: str, arguments_json: str) -> str:
        handler = AVAILABLE_TOOLS.get(tool_name)
        if not handler:
            return json.dumps({"error": f"Tool '{tool_name}' not found."})

        try:
            params = json.loads(arguments_json) if arguments_json else {}
            return handler(**params)
        except Exception as exc:
            return json.dumps({"error": str(exc)})

    def run_conversation_turn(
        self,
        conversation_history: List[Dict[str, Any]],
        max_turns: int = 5
    ) -> Tuple[str, List[Dict[str, Any]]]:
        messages = [{"role": "system", "content": self.system_prompt}] + conversation_history

        for _ in range(max_turns):
            response = litellm.completion(
                model=self.model_name,
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
                api_key=self.api_key
            )

            assistant_msg = response.choices[0].message
            tool_calls = getattr(assistant_msg, "tool_calls", None)

            if not tool_calls:
                content = assistant_msg.content or ""
                return content, conversation_history + [{"role": "assistant", "content": content}]

            messages.append(assistant_msg.model_dump())

            for tc in tool_calls:
                output = self._execute_tool(tc.function.name, tc.function.arguments)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.function.name,
                    "content": output
                })

        fallback = "Não foi possível concluir o processamento no momento. Como posso ajudar com outra dúvida?"
        return fallback, conversation_history + [{"role": "assistant", "content": fallback}]