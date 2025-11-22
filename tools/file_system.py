from langchain_core.tools import tool
from pathlib import Path
import os

# Ustawiamy sztywny root dla bezpieczeństwa
PROJECT_ROOT = Path("output_projects")

@tool
def save_file(filename: str, code_content: str):
    """
    Zapisuje kod w bezpiecznym katalogu output_projects.
    """
    try:
        # 1. Rozwiązanie ścieżki
        full_path = (PROJECT_ROOT / filename).resolve()
        root_path = PROJECT_ROOT.resolve()

        # 2. Security Check: Czy nie wychodzimy poza folder?
        if not str(full_path).startswith(str(root_path)):
            return f"❌ SECURITY ERROR: Próba zapisu poza dozwolony katalog: {filename}"

        # 3. Tworzenie folderów
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # 4. Zapis
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(code_content)
            
        return f"✅ Zapisano: {filename}"
    except Exception as e:
        return f"❌ Błąd zapisu {filename}: {str(e)}"