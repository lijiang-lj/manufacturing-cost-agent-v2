# agent_helpers.py
import json
from typing import Any, Dict, Optional

def safe_invoke(llm, prompt: str, *, expect_json: bool = False) -> Dict[str, Any]:
    """
    统一的 LLM 安全调用：
      - 成功：{"ok": True, "text": "...", "data": <dict or None>}
      - 失败：{"ok": False, "error": "message"}
    """
    try:
        resp = llm.invoke(prompt)
        text = getattr(resp, "content", None)
        if text is None:
            return {"ok": False, "error": "Empty response"}

        if expect_json:
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                return {"ok": False, "error": "Invalid JSON", "text": text}
            return {"ok": True, "text": text, "data": data}
        else:
            return {"ok": True, "text": text, "data": None}
    except Exception as e:
        # 这里不要再抛，让上层根据 error 决定兜底
        return {"ok": False, "error": str(e)}
