# utils/logger.py
"""
Konfiguracja logowania dla projektu AgileFlow.
Kolorowe logi w konsoli zamiast print().
"""

import logging
import sys
from typing import Optional

# Kolory ANSI dla terminala
COLORS = {
    "DEBUG": "\033[36m",     # Cyan
    "INFO": "\033[32m",      # Zielony
    "WARNING": "\033[33m",   # Żółty
    "ERROR": "\033[31m",     # Czerwony
    "CRITICAL": "\033[35m",  # Magenta
    "RESET": "\033[0m",
}

# Emoji dla różnych typów logów
EMOJI = {
    "DEBUG": "🔧",
    "INFO": "✅",
    "WARNING": "⚠️",
    "ERROR": "❌",
    "CRITICAL": "💥",
}


class ColoredFormatter(logging.Formatter):
    """Formatter z kolorami i emoji dla lepszej czytelności."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Dodaj kolor i emoji
        color = COLORS.get(record.levelname, "")
        reset = COLORS["RESET"]
        emoji = EMOJI.get(record.levelname, "")
        
        # Formatuj wiadomość
        record.levelname = f"{color}{record.levelname}{reset}"
        record.msg = f"{emoji} {record.msg}"
        
        return super().format(record)


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Tworzy logger z kolorowym formatowaniem.
    
    Args:
        name: Nazwa loggera (zazwyczaj __name__)
        level: Poziom logowania (domyślnie INFO)
    
    Returns:
        Skonfigurowany logger
    """
    logger = logging.getLogger(name)
    
    # Unikaj duplikowania handlerów
    if logger.handlers:
        return logger
    
    level = level or logging.INFO
    logger.setLevel(level)
    
    # Handler dla konsoli
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Format: [LEVEL] nazwa_modułu - wiadomość
    formatter = ColoredFormatter(
        fmt="[%(levelname)s] %(name)s - %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.propagate = False
    
    return logger


# Predefiniowane loggery dla głównych modułów
def get_agent_logger(agent_name: str) -> logging.Logger:
    """Logger specjalnie dla agentów."""
    return get_logger(f"agent.{agent_name}")


def get_service_logger(service_name: str) -> logging.Logger:
    """Logger dla serwisów."""
    return get_logger(f"service.{service_name}")
