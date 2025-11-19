import os
from langchain_core.tools import tool

# Folder, gdzie będą lądować projekty (bezpiecznik, żeby nie nadpisał Ci Windowsa)
OUTPUT_DIR = "output_projects"

@tool
def save_file(filename: str, code_content: str):
    """
    Zapisuje kod do pliku o podanej nazwie. 
    Użyj tego narzędzia, aby stworzyć pliki projektu.
    
    Args:
        filename: Ścieżka do pliku (np. 'main.py' lub 'src/utils.py')
        code_content: Pełny kod programu, który ma być w pliku.
    """
    # 1. Budujemy pełną ścieżkę
    full_path = os.path.join(OUTPUT_DIR, filename)
    directory = os.path.dirname(full_path)
    
    # 2. Tworzymy foldery, jeśli ich nie ma (np. dla 'src/utils.py' tworzy 'src')
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        
    # 3. Zapisujemy plik
    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(code_content)
        return f"✅ Zapisano plik: {filename}"
    except Exception as e:
        return f"❌ Błąd zapisu {filename}: {str(e)}"