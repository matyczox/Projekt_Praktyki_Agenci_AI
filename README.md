# 🚀 AgileFlow - Autonomiczny Zespół Deweloperski AI

**AgileFlow** to wieloagentowy system AI, który działa jak prawdziwy zespół software'owy. Podajesz pomysł na aplikację, a agenci automatycznie przechodzą przez pełny cykl rozwoju: od wymagań, przez architekturę, implementację, aż po testy jakości.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

---

## 📋 Spis treści

- [Cechy projektu](#-cechy-projektu)
- [Jak to działa](#-jak-to-działa)
- [Wymagania](#-wymagania)
- [Instalacja](#-instalacja)
- [Konfiguracja](#-konfiguracja)
- [Uruchomienie](#-uruchomienie)
- [Architektura](#-architektura)
- [Przykłady użycia](#-przykłady-użycia)
- [Troubleshooting](#-troubleshooting)
- [FAQ](#-faq)
- [Roadmap](#-roadmap)

---

## ✨ Cechy projektu

### 🤖 Czterech wyspecjalizowanych agentów:

| Agent | Rola | Model (domyślny) | Odpowiedzialność |
|-------|------|------------------|------------------|
| **🎩 Product Owner** | Analiza wymagań | Llama 3.3 70B | Tworzy backlog, user stories, kryteria akceptacji |
| **📐 Architekt** | Projektowanie systemu | Llama 3.3 70B | Planuje strukturę plików, wybiera technologie |
| **👨‍💻 Developer** | Implementacja | Qwen 3 Coder 30B | Pisze pełny, działający kod |
| **🕵️ QA Engineer** | Testowanie | Llama 3.3 70B | Sprawdza składnię, logikę, bezpieczeństwo |

### 🔄 Iteracyjny workflow:
- Automatyczne poprawki błędów (max 3 iteracje)
- Pętla feedback: QA → Developer → QA
- Pamięć kontekstu między iteracjami

### 🎨 Nowoczesny interfejs:
- Dark mode w stylu "Deep Space"
- Real-time streaming odpowiedzi
- Podgląd procesu myślowego agentów
- Custom CSS z neonowymi akcentami

### 🔒 Bezpieczeństwo:
- Lokalne modele LLM (zero wysyłania danych do chmury)
- Sandbox dla generowanych plików
- SSL/Token authentication dla Ollama

---

## 🎯 Jak to działa?

```
User: "Stwórz grę Snake w Pythonie z Pygame"
   ↓
┌─────────────────────────────────────────────┐
│  1. 🎩 Product Owner                        │
│     → Tworzy backlog projektu               │
│     → Definiuje funkcje gry                 │
└─────────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────────┐
│  2. 📐 Architekt                            │
│     → Planuje: main.py, game.py, snake.py  │
│     → Wybiera biblioteki: pygame            │
└─────────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────────┐
│  3. 👨‍💻 Developer                           │
│     → Generuje pełny kod                    │
│     → Zapisuje pliki w output_projects/     │
└─────────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────────┐
│  4. 🕵️ QA Engineer                          │
│     → Sprawdza: składnię, logikę, bezp.     │
│     → Decyzja: APPROVED ✅ / REJECTED ❌    │
└─────────────────────────────────────────────┘
   ↓
   ├─ APPROVED → Koniec ✅
   └─ REJECTED → Powrót do Developera (max 3x)
```

---

## 📦 Wymagania

### Wymagania systemowe:
- **Python**: 3.11 lub 3.12 (⚠️ Python 3.13 może mieć problemy z NumPy)
- **RAM**: Minimum 16GB (32GB zalecane dla Llama 70B)
- **Dysk**: ~50GB wolnego miejsca (dla modeli)
- **GPU** (opcjonalnie): NVIDIA z 16GB+ VRAM dla przyspieszenia

### Oprogramowanie:
- [Ollama](https://ollama.com/) - lokalny serwer LLM
- Git
- Edytor kodu (VS Code zalecany)

---

## 🛠️ Instalacja

### Krok 1: Sklonuj repozytorium

```bash
git clone https://github.com/your-username/agileflow.git
cd agileflow
```

### Krok 2: Stwórz środowisko wirtualne

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### Krok 3: Zainstaluj zależności

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**⚠️ Problem z NumPy na Windows?**
```bash
# Użyj pre-compiled wheels
pip install --prefer-binary -r requirements.txt
```

### Krok 4: Zainstaluj Ollama

**Windows/Mac:**
- Pobierz instalator: https://ollama.com/download
- Uruchom instalator

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Krok 5: Pobierz modele AI

```bash
# Model do rozumowania (Product Owner, Architekt, QA)
ollama pull llama3.3:70b

# Model do kodowania (Developer)
ollama pull qwen3-coder:30b

# Model do embeddingów (opcjonalnie)
ollama pull nomic-embed-text
```

**💡 Lżejsze alternatywy (dla 8-16GB RAM):**
```bash
ollama pull llama3.3:latest    # 8B zamiast 70B
ollama pull qwen2.5-coder:14b  # 14B zamiast 30B
```

---

## ⚙️ Konfiguracja

### Krok 1: Stwórz plik `.env`

Skopiuj przykładowy plik:
```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

### Krok 2: Edytuj `.env`

```env
# ============================================
# OLLAMA CONFIGURATION
# ============================================
# Dla lokalnej instalacji:
OLLAMA_BASE_URL=http://127.0.0.1:11434

# Dla zdalnego serwera:
# OLLAMA_BASE_URL=https://your-server.com

# Token (zostaw puste dla lokalnej instalacji)
OLLAMA_TOKEN=

# SSL Verification
OLLAMA_VERIFY_SSL=False

# ============================================
# MODELE AI
# ============================================
MODEL_REASONING=llama3.3:70b
MODEL_CODER=qwen3-coder:30b
MODEL_EMBEDDINGS=nomic-embed-text
```

### Krok 3: Dostosuj `config.toml` (opcjonalnie)

```toml
[project]
session_timeout = 3600  # 1 godzina

[features.spontaneous_file_upload]
enabled = true
max_files = 5
max_size_mb = 500

[UI]
name = "AgileFlow"
default_theme = "dark"
layout = "wide"
```

---

## 🚀 Uruchomienie

### Podstawowe uruchomienie:

```bash
chainlit run app.py
```

Aplikacja dostępna pod: **http://localhost:8000**

### Uruchomienie z auto-reload:

```bash
chainlit run app.py -w
```

### Zmiana portu:

```bash
chainlit run app.py --port 8080
```

---

## 🏗️ Architektura

### Struktura projektu:

```
agileflow/
├── agents/                  # Logika agentów AI
│   ├── product_owner.py    # Analiza wymagań
│   ├── architect.py         # Projektowanie architektury
│   ├── developer.py         # Generowanie kodu
│   └── qa.py                # Testowanie i weryfikacja
│
├── core/                    # Komponenty podstawowe
│   ├── llm_factory.py      # Factory dla modeli LLM
│   └── state.py            # Definicja stanu projektu
│
├── tools/                   # Narzędzia pomocnicze
│   └── file_system.py      # Operacje na plikach
│
├── public/                  # Assety frontendowe
│   ├── style.css           # Custom CSS (Deep Space theme)
│   ├── logo_dark.png       # Logo aplikacji
│   └── favicon.png         # Ikona strony
│
├── output_projects/         # Wygenerowane projekty (auto-tworzone)
│
├── .env                     # Konfiguracja (nie commituj!)
├── config.toml             # Ustawienia Chainlit
├── app.py                  # Entry point aplikacji
├── chainlit.md             # Ekran powitalny
└── requirements.txt        # Zależności Python
```

### Flow danych (LangGraph):

```python
StateGraph(ProjectState)
  ├─ product_owner_node
  ├─ architect_node
  ├─ developer_node
  ├─ qa_node
  └─ should_continue (conditional edge)
       ├─ "fix" → developer_node (retry)
       └─ "end" → END
```

### State schema:

```python
class ProjectState(TypedDict):
    user_request: str              # Pomysł użytkownika
    requirements: str              # Backlog od PO
    tech_stack: str                # Plan architekta
    generated_code: Dict[str, str] # {filename: content}
    qa_feedback: str               # Feedback od QA
    qa_status: str                 # APPROVED / REJECTED
    iteration_count: int           # Licznik iteracji (max 3)
    logs: List[str]                # Historia operacji
```

---

## 💡 Przykłady użycia

### Przykład 1: Prosta gra

**Input:**
```
Stwórz grę Snake w Pythonie używając Pygame
```

**Output (output_projects/):**
```
main.py
snake.py
food.py
requirements.txt
README.md
```

### Przykład 2: Narzędzie CLI

**Input:**
```
Zrób konwerter CSV na JSON z walidacją danych
```

**Output:**
```
converter.py
validator.py
requirements.txt
README.md
```

### Przykład 3: Web scraper

**Input:**
```
Stwórz scraper do pobierania cen z Allegro
```

**Output:**
```
main.py
scraper.py
database.py
requirements.txt
README.md
```

---

## 🐛 Troubleshooting

### Problem: "Model zwrócił 0 znaków"

**Przyczyna:** Developer nie generuje kodu.

**Rozwiązania:**
1. **Test z innym modelem:**
   ```env
   MODEL_CODER=llama3.3:70b  # Zamiast Qwen
   ```

2. **Zwiększ context window:**
   ```python
   # W llm_factory.py
   num_ctx=24000  # Zamiast 8192
   ```

3. **Sprawdź czy model jest załadowany:**
   ```bash
   ollama ps
   ollama run qwen3-coder:30b "test"
   ```

### Problem: "504 DNS look up failed"

**Przyczyna:** Proxy/firewall blokuje `localhost`.

**Rozwiązanie:**
```env
# W .env zmień:
OLLAMA_BASE_URL=http://127.0.0.1:11434  # Zamiast localhost
```

### Problem: "ModuleNotFoundError: langchain_core"

**Przyczyna:** Brak zainstalowanych pakietów.

**Rozwiązanie:**
```bash
pip install -r requirements.txt
```

### Problem: NumPy compilation error (Windows)

**Przyczyna:** Python 3.13 + brak kompilatora C.

**Rozwiązanie:**
```bash
# Opcja A: Downgrade do Python 3.11
py -3.11 -m venv .venv

# Opcja B: Wymuś binary wheels
pip install --prefer-binary numpy
```

### Problem: "Folder output_projects nie istnieje"

**Przyczyna:** Folder w `.gitignore`, nie pulluje się z repo.

**Rozwiązanie:** Folder tworzy się automatycznie - upewnij się że używasz najnowszej wersji `file_system.py`.

---

## ❓ FAQ

**Q: Czy AgileFlow działa offline?**  
A: Tak! Wszystkie modele działają lokalnie przez Ollama. Nie wysyłamy żadnych danych do chmury.

**Q: Jakie języki programowania obsługuje Developer?**  
A: Obecnie głównie Python. Ale potrafi obsługiwać również inne języki.

**Q: Czy mogę użyć modeli z OpenAI/Anthropic?**  
A: Tak, wystarczy zmienić `llm_factory.py` na ChatOpenAI lub ChatAnthropic z LangChain.

**Q: Ile czasu trwa generowanie projektu?**  
A: 2-5 minut dla prostych projektów, 10-15 minut dla złożonych (zależy od hardware).

**Q: Czy AgileFlow może edytować istniejący kod?**  
A: Tak! Developer ma tryb REFACTORING - wczytuje istniejące pliki i modyfikuje je.

**Q: Jak zmienić limit iteracji (max 3)?**  
A: W `app.py`, funkcja `should_continue()`:
```python
if state["iteration_count"] >= 5:  # Zmień 3 na 5
    return "end"
