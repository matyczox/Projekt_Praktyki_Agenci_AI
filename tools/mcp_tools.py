from langchain_core.tools import tool
import requests
import os

MCP_SERVERS = os.getenv("MCP_SERVERS", "https://github.com/mcp")  # Przykładowy rejestr

@tool
def call_mcp_tool(tool_name: str, params: dict):
    """
    Wywołuje narzędzie MCP (Model Context Protocol).
    Przykład: tool_name='code_execution', params={'code': 'print("Hello")'}
    """
    # Symulacja – w produkcji połącz z MCP serverem z rejestru GitHub
    try:
        # Przykładowe wywołanie (dostosuj do realnego MCP endpoint)
        response = requests.post(f"{MCP_SERVERS}/tools/{tool_name}", json=params)
        return f"MCP wynik: {response.text}"
    except Exception as e:
        return f"Błąd MCP: {e}"