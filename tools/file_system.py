import os

# Katalog roboczy - automatycznie tworzony
WORKSPACE_DIR = "./output_projects"

# Tworzymy folder przy imporcie modułu
if not os.path.exists(WORKSPACE_DIR):
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    print(f"✅ Utworzono folder: {WORKSPACE_DIR}")

def write_file(filename: str, content: str) -> str:
    """
    Zapisuje treść do pliku, tworząc niezbędne podkatalogi.
    (Kompatybilne z kodem kolegi)
    """
    try:
        filename = filename.strip().replace("\\", "/")
        if filename.startswith("/"): 
            filename = filename[1:]
        
        full_path = os.path.abspath(os.path.join(WORKSPACE_DIR, filename))
        workspace_abs = os.path.abspath(WORKSPACE_DIR)
        
        # Security check
        if not full_path.startswith(workspace_abs):
            return f"Error: Próba zapisu poza workspace: {filename}"
        
        # Tworzenie katalogów
        directory = os.path.dirname(full_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"   📁 Utworzono katalog: {directory}")
        
        # Zapis pliku
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return f"Successfully wrote to {filename}"
    
    except Exception as e:
        return f"Error writing file: {str(e)}"

def read_file(filename: str) -> str:
    """
    Odczytuje treść pliku z workspace.
    Jeśli plik nie istnieje, zwraca pusty string.
    """
    try:
        full_path = os.path.abspath(os.path.join(WORKSPACE_DIR, filename))
        workspace_abs = os.path.abspath(WORKSPACE_DIR)
        
        if not full_path.startswith(workspace_abs):
            return "Error: Security violation."
        
        # Jeśli plik nie istnieje, zwracamy pusty tekst
        if not os.path.exists(full_path):
            return ""
        
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    
    except Exception as e:
        return f"Error reading file: {str(e)}"

def list_files(startpath=WORKSPACE_DIR) -> str:
    """Zwraca sformatowany string dla człowieka (do UI)."""
    files = get_all_file_paths(startpath)
    return ", ".join(files) if files else "No files in workspace."

def get_all_file_paths(startpath=WORKSPACE_DIR) -> list:
    """
    Zwraca czystą listę ścieżek dla Agentów.
    Używane przez Developera do skanowania projektu.
    """
    file_list = []
    try:
        if not os.path.exists(startpath): 
            return []
        
        for root, dirs, files in os.walk(startpath):
            for name in files:
                if name == ".gitkeep": 
                    continue  # Ignorujemy pliki systemowe
                
                absolute_path = os.path.join(root, name)
                relative_path = os.path.relpath(absolute_path, startpath)
                file_list.append(relative_path.replace("\\", "/"))
        
        return file_list
    
    except Exception:
        return []

# ============================================
# BACKWARD COMPATIBILITY - dla Twojego kodu
# ============================================
# Jeśli używasz save_file jako @tool, możesz to zachować:
from langchain_core.tools import tool

@tool
def save_file(filename: str, code_content: str):
    """
    Langchain tool wrapper dla write_file.
    Zachowuje kompatybilność z Twoim obecnym kodem.
    """
    result = write_file(filename, code_content)
    
    # Debug info
    if "Successfully" in result:
        # Sprawdź czy plik się zapisał
        full_path = os.path.join(WORKSPACE_DIR, filename)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            return f"✅ Zapisano plik: {filename} ({size} bajtów)"
    
    return result