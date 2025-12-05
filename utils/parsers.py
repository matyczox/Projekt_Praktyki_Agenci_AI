# utils/parsers.py
"""
Parsery odpowiedzi LLM.
Wyodrębnione z developer.py dla lepszej modularności.
"""

import re
import json
from typing import Dict, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


def parse_code_blocks(text: str) -> Dict[str, str]:
    """
    UNIWERSALNE parsowanie bloków kodu z odpowiedzi LLM.
    Obsługuje różne formaty:
    1. --- filename ---
    2. ### filename
    3. ## filename
    4. **filename**
    5. Filename:
    
    Args:
        text: Surowa odpowiedź z LLM
    
    Returns:
        Dict[filename, code_content]
    """
    code_dict: Dict[str, str] = {}
    
    # STRATEGIA 1: Format --- filename ---
    pattern1 = r'---\s*([^\n]+?)\s*---\s*```(?:\w+)?\n(.*?)```'
    matches1 = re.findall(pattern1, text, re.DOTALL)
    
    for filename, code in matches1:
        filename = filename.strip()
        code = code.strip()
        if filename and code:
            code_dict[filename] = code
    
    if code_dict:
        logger.debug(f"Parsowanie: Format '--- filename ---' → {len(code_dict)} plików")
        return code_dict
    
    # STRATEGIA 2: Format ### filename lub ## filename
    pattern2 = r'#{2,3}\s+([^\n]+?)\s*\n+```(?:\w+)?\n(.*?)```'
    matches2 = re.findall(pattern2, text, re.DOTALL)
    
    for filename, code in matches2:
        filename = filename.strip()
        code = code.strip()
        if filename and code:
            code_dict[filename] = code
    
    if code_dict:
        logger.debug(f"Parsowanie: Format '### filename' → {len(code_dict)} plików")
        return code_dict
    
    # STRATEGIA 3: Format **filename** (bold)
    pattern3 = r'\*\*([^\*]+?)\*\*\s*\n+```(?:\w+)?\n(.*?)```'
    matches3 = re.findall(pattern3, text, re.DOTALL)
    
    for filename, code in matches3:
        filename = filename.strip()
        code = code.strip()
        if filename and code:
            code_dict[filename] = code
    
    if code_dict:
        logger.debug(f"Parsowanie: Format '**filename**' → {len(code_dict)} plików")
        return code_dict
    
    # STRATEGIA 4: Filename: (dwukropek)
    pattern4 = r'([a-zA-Z0-9_\-\.\/]+\.[a-z]+):\s*\n+```(?:\w+)?\n(.*?)```'
    matches4 = re.findall(pattern4, text, re.DOTALL | re.IGNORECASE)
    
    for filename, code in matches4:
        filename = filename.strip()
        code = code.strip()
        if filename and code:
            code_dict[filename] = code
    
    if code_dict:
        logger.debug(f"Parsowanie: Format 'filename:' → {len(code_dict)} plików")
        return code_dict
    
    # STRATEGIA 5 (FALLBACK): Wszystkie bloki kodu + próba zgadnięcia nazwy
    pattern5 = r'```(?:\w+)?\n(.*?)```'
    all_blocks = re.findall(pattern5, text, re.DOTALL)
    
    if all_blocks:
        logger.warning(f"Fallback: Znaleziono {len(all_blocks)} bloków kodu bez nazw")
        
        for i, block in enumerate(all_blocks):
            # Szukamy nazwy pliku w tekście przed blokiem
            block_start = text.find('```' + block[:50] if len(block) > 50 else block)
            text_before = text[:block_start] if block_start > 0 else ""
            lines_before = text_before.split('\n')[-5:]
            
            found_name = False
            for line in reversed(lines_before):
                file_match = re.search(r'([a-zA-Z0-9_\-]+\.[a-z]+)', line)
                if file_match:
                    filename = file_match.group(1)
                    code_dict[filename] = block.strip()
                    logger.debug(f"  Zgadłem nazwę: {filename}")
                    found_name = True
                    break
            
            if not found_name:
                # Generyczna nazwa na podstawie zawartości
                ext = ".py" if "def " in block or "import " in block else ".txt"
                filename = f"file_{i+1}{ext}"
                code_dict[filename] = block.strip()
                logger.warning(f"  Generyczna nazwa: {filename}")
        
        return code_dict
    
    logger.error("Nie znaleziono żadnego kodu w odpowiedzi LLM!")
    return {}


def extract_file_list(tech_stack_response: str) -> List[str]:
    """
    Wyciąga listę plików z JSON-a w odpowiedzi Architekta.
    
    Args:
        tech_stack_response: Odpowiedź od agenta Architekta
    
    Returns:
        Lista nazw plików
    """
    try:
        # Szukamy bloku JSON na końcu tekstu
        json_match = re.search(r'```json\s*(\[.*?\])\s*```', tech_stack_response, re.DOTALL)
        if json_match:
            file_list = json.loads(json_match.group(1))
            logger.debug(f"Wyodrębniono {len(file_list)} plików z JSON")
            return file_list
    except json.JSONDecodeError as e:
        logger.warning(f"Błąd parsowania JSON z listą plików: {e}")
    except Exception as e:
        logger.error(f"Nieoczekiwany błąd przy parsowaniu listy plików: {e}")
    
    return []


def extract_json_from_response(response: str) -> Optional[dict]:
    """
    Wyodrębnia pierwszy blok JSON z odpowiedzi LLM.
    
    Args:
        response: Surowa odpowiedź LLM
    
    Returns:
        Sparsowany JSON lub None
    """
    try:
        # Szukamy bloku ```json ... ```
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # Próbujemy też bez markdown
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
            
    except json.JSONDecodeError:
        pass
    
    return None
