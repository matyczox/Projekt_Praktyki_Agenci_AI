import os
from langchain_core.tools import tool

# Folder, gdzie będą lądować projekty (bezpiecznik, żeby nie nadpisał Ci Windowsa)
OUTPUT_DIR = "output_projects"

@tool
def save_file(filename: str, code_content: str):
    """
    Zapisuje kod do pliku o podanej nazwie. 
    """
    full_path = os.path.join(OUTPUT_DIR, filename)
    directory = os.path.dirname(full_path)
    
    # === DODAJ DEBUG ===
    print(f"\n💾 [SAVE_FILE DEBUG]")
    print(f"   Filename: {filename}")
    print(f"   Full path: {full_path}")
    print(f"   Content length: {len(code_content)} znaków")
    print(f"   Content is empty: {not code_content or not code_content.strip()}")
    # ===================
    
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        
    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(code_content)
        
        # === WERYFIKACJA PO ZAPISIE ===
        with open(full_path, "r", encoding="utf-8") as f:
            saved_content = f.read()
        
        if len(saved_content) != len(code_content):
            return f"⚠️  UWAGA: Zapisano {len(saved_content)} z {len(code_content)} znaków do {filename}"
        
        return f"✅ Zapisano plik: {filename} ({len(saved_content)} znaków)"
        # ==============================
        
    except Exception as e:
        return f"❌ Błąd zapisu {filename}: {str(e)}"