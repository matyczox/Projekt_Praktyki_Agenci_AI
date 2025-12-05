# services/file_service.py
"""
Serwis do operacji na plikach.
Ujednolicony zapis z walidacją bezpieczeństwa.
"""

from pathlib import Path
from typing import Optional, Dict
from config import settings
from utils.logger import get_service_logger

logger = get_service_logger("file")


class FileService:
    """
    Serwis do bezpiecznych operacji na plikach w projekcie.
    Zapobiega zapisom poza dozwolony katalog.
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or settings.output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self) -> None:
        """Tworzy folder output jeśli nie istnieje."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _validate_path(self, filename: str) -> Optional[Path]:
        """
        Waliduje ścieżkę pliku pod kątem bezpieczeństwa.
        
        Args:
            filename: Nazwa pliku (może zawierać podkatalogi)
        
        Returns:
            Bezpieczna ścieżka lub None jeśli nieprawidłowa
        """
        try:
            full_path = (self.output_dir / filename).resolve()
            root_path = self.output_dir.resolve()
            
            # Sprawdź czy nie wychodzimy poza dozwolony katalog
            if not str(full_path).startswith(str(root_path)):
                logger.error(f"SECURITY: Próba zapisu poza dozwolony katalog: {filename}")
                return None
            
            return full_path
        except Exception as e:
            logger.error(f"Błąd walidacji ścieżki {filename}: {e}")
            return None
    
    def save_file(self, filename: str, content: str) -> bool:
        """
        Bezpiecznie zapisuje plik.
        
        Args:
            filename: Nazwa pliku (może zawierać podkatalogi)
            content: Zawartość pliku
        
        Returns:
            True jeśli zapis się powiódł
        """
        full_path = self._validate_path(filename)
        if not full_path:
            return False
        
        try:
            # Twórz katalogi nadrzędne jeśli potrzeba
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            logger.debug(f"Zapisano: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Błąd zapisu {filename}: {e}")
            return False
    
    def save_files(self, files: Dict[str, str]) -> Dict[str, bool]:
        """
        Zapisuje wiele plików naraz.
        
        Args:
            files: Słownik {filename: content}
        
        Returns:
            Słownik {filename: success}
        """
        results = {}
        for filename, content in files.items():
            results[filename] = self.save_file(filename, content)
        
        success_count = sum(results.values())
        logger.info(f"Zapisano {success_count}/{len(files)} plików")
        
        return results
    
    def read_file(self, filename: str) -> Optional[str]:
        """
        Odczytuje plik z projektu.
        
        Args:
            filename: Nazwa pliku
        
        Returns:
            Zawartość pliku lub None
        """
        full_path = self._validate_path(filename)
        if not full_path or not full_path.exists():
            return None
        
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Błąd odczytu {filename}: {e}")
            return None
    
    def list_files(self) -> list:
        """
        Lista wszystkich plików w katalogu output.
        
        Returns:
            Lista ścieżek względnych
        """
        files = []
        for path in self.output_dir.rglob("*"):
            if path.is_file():
                files.append(str(path.relative_to(self.output_dir)))
        return files
    
    def clear_output(self) -> bool:
        """
        Czyści katalog output (przed nowym projektem).
        
        Returns:
            True jeśli operacja się powiodła
        """
        import shutil
        
        try:
            if self.output_dir.exists():
                shutil.rmtree(self.output_dir)
                logger.info("Wyczyszczono katalog output")
            
            self.output_dir.mkdir(parents=True, exist_ok=True)
            return True
            
        except Exception as e:
            logger.error(f"Błąd czyszczenia katalogu output: {e}")
            return False


# Singleton
file_service = FileService()
