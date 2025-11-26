# 🚀 AgileFlow – Autonomiczny Zespół Deweloperski AI

**Najlepszy lokalny system multi-agentowy do generowania pełnych aplikacji w 2025 roku**

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Ollama](https://img.shields.io/badge/Ollama-Required-orange.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

**Tech Stack:** Qwen3-Coder 30B + Llama 3.3 70B + RAG + LangGraph + Chainlit

---

## 🎯 Co to jest AgileFlow?

**AgileFlow** to autonomiczny zespół AI składający się z **4 wyspecjalizowanych agentów** o różnych rolach i osobowościach, który na podstawie **jednego zdania od użytkownika** potrafi stworzyć **pełną, działającą aplikację** – od backlogu po gotowy kod.

### ✨ Kluczowe funkcje:

✅ **Generuje kompletne aplikacje** (Python, .NET 8 + Angular 17, Blazor, FastAPI, itd.)  
✅ **Pełny cykl Agile:** Backlog → Plan → Kod → QA → Iteracje (do 5)  
✅ **RAG z ChromaDB** – agenci pamiętają cały kontekst projektu  
✅ **Automatyczne czyszczenie workspace** przy każdym uruchomieniu  
✅ **Interfejs webowy (Chainlit)** – wszystko widzisz na żywo  
✅ **100% lokalny** – zero chmury, zero API keyów, pełna prywatność  

---

## 🤖 Zespół AI

| Agent | Model używany | Rola | Kontekst | Odpowiedzialność |
|-------|--------------|------|----------|------------------|
| **🎩 Product Owner** | `llama3.3:70b` | Tworzy backlog i user stories | 128k | Analiza wymagań, definiowanie funkcji |
| **📐 Architekt** | `llama3.3:70b` | Projektuje strukturę i tech stack | 128k | Plan plików, wybór technologii |
| **👨‍💻 Developer** | `qwen3-coder:30b` | Pisze i naprawia kod | 256k | Implementacja, refactoring, debugging |
| **🕵️ QA Engineer** | `llama3.3:70b` | Sprawdza poprawność i kompletność kodu | 128k | Testy, weryfikacja logiki, bezpieczeństwo |

### 🧠 RAG (Retrieval-Augmented Generation)

Dzięki **ChromaDB** agenci **pamiętają wymagania, backlog i plan** przez wszystkie iteracje – to znaczy, że Developer wie co Product Owner powiedział, a QA pamięta co Architekt zaplanował.

---

## 🔄 Jak to działa?

```
User: "Stwórz REST API dla systemu rezerwacji biletów lotniczych"
   ↓
┌─────────────────────────────────────────────────────────┐
│  1. 🎩 Product Owner (llama3.3:70b)                     │
│     → Tworzy backlog z user stories                     │
│     → Zapisuje do RAG (ChromaDB)                        │
└─────────────────────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────────────────────┐
│  2. 📐 Architekt (llama3.3:70b)                         │
│     → Czyta backlog z RAG                               │
│     → Planuje: main.py, models.py, routes.py, db.py    │
│     → Zapisuje plan do RAG                              │
└─────────────────────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────────────────────┐
│  3. 👨‍💻 Developer (qwen3-coder:30b)                     │
│     → Czyta plan + backlog z RAG                        │
│     → Generuje pełny kod (FastAPI + SQLAlchemy)        │
│     → Format: ### FILE: nazwa.py ... ### ENDFILE       │
│     → Zapisuje do workspace/                            │
└─────────────────────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────────────────────┐
│  4. 🕵️ QA Engineer (llama3.3:70b)                       │
│     → Sprawdza: składnię, logikę, security              │
│     → Decyzja: APPROVED ✅ / REJECTED ❌                │
└─────────────────────────────────────────────────────────┘
   ↓
   ├─ APPROVED → Koniec ✅ Gotowa aplikacja!
   └─ REJECTED → Powrót do Developera (max 5 iteracji)
```

---

## 🛠️ Wymagania

### System:
- **Python**: 3.11 lub nowszy
- **RAM**: Minimum **32 GB** (zalecane **64 GB** przy dużych projektach)
- **Dysk**: ~50 GB wolnego miejsca (modele Ollama)
- **GPU** (opcjonalnie): NVIDIA z 16GB+ VRAM dla przyspieszenia

### Oprogramowanie:
- **Ollama** ([ollama.com](https://ollama.com/))
- Git

### Modele Ollama (wymagane):
```bash
ollama pull qwen3-coder:30b      # Developer (30 GB)
ollama pull llama3.3:70b         # PO, Architekt, QA (40 GB)
ollama pull nomic-embed-text     # RAG embeddings (274 MB)
```

---

## 📦 Instalacja

### Krok 1: Sklonuj repozytorium

```bash
git clone https://github.com/twoj-login/AgileFlow.git
cd AgileFlow
```

### Krok 2: Stwórz środowisko wirtualne

**Windows:**
```bash
python -m venv .venv
.\.venv\Scripts\activate
```

**Linux/Mac:**
```bash
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
pip install --prefer-binary -r requirements.txt
```

### Krok 4: Zainstaluj Ollama i modele

**Windows/Mac:**
- Pobierz z: https://ollama.com/download
- Uruchom instalator

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Pobierz modele:**
```bash
ollama pull qwen3-coder:30b
ollama pull llama3.3:70b
ollama pull nomic-embed-text
```

### Krok 5: Konfiguracja

Stwórz plik `.env`:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Edytuj `.env`:

```env
# ============================================
# OLLAMA CONFIGURATION
# ============================================
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_TOKEN=
OLLAMA_VERIFY_SSL=False

# ============================================
# MODELE AI
# ============================================
MODEL_REASONING=llama3.3:70b
MODEL_CODER=qwen3-coder:30b
MODEL_EMBEDDINGS=nomic-embed-text
```

---

## 🚀 Uruchomienie

### Podstawowe uruchomienie:

```bash
chainlit run app.py
```

Aplikacja dostępna pod: **http://localhost:8000**

### Uruchomienie z auto-reload (dla development):

```bash
chainlit run app.py -w
```

### Zmiana portu:

```bash
chainlit run app.py --port 8080
```

---

## 💡 Przykłady użycia

### Przykład 1: REST API

**Input:**
```
Stwórz REST API do zarządzania biblioteką używając FastAPI
```

**Output (workspace/):**
```
main.py              # Entry point
models.py            # SQLAlchemy models
routes.py            # API endpoints
database.py          # Database config
requirements.txt     # Dependencies
README.md            # Documentation
```

### Przykład 2: .NET + Angular

**Input:**
```
Stwórz aplikację TODO z backendem w .NET 8 i frontendem w Angular 17
```

**Output:**
```
backend/
  ├── Controllers/
  ├── Models/
  ├── Program.cs
  └── appsettings.json
frontend/
  ├── src/app/
  ├── angular.json
  └── package.json
README.md
```

### Przykład 3: Blazor WebAssembly

**Input:**
```
Stwórz aplikację pogodową w Blazor WebAssembly z API
```

**Output:**
```
BlazorWeatherApp/
  ├── Pages/
  ├── Services/
  ├── Program.cs
  └── wwwroot/
README.md
```

---

## 🏗️ Architektura

### Struktura projektu:

```
AgileFlow/
├── agents/                  # Logika agentów AI
│   ├── product_owner.py    # Backlog i user stories
│   ├── architect.py         # Plan techniczny
│   ├── developer.py         # Generowanie kodu
│   └── qa.py                # Testowanie
│
├── core/                    # Komponenty podstawowe
│   ├── llm_factory.py      # Factory dla modeli LLM
│   └── state.py            # Stan projektu (TypedDict)
│
├── tools/                   # Narzędzia pomocnicze
│   └── file_system.py      # Operacje na plikach (workspace/)
│
├── public/                  # Assety UI
│   ├── style.css           # Deep Space theme
│   ├── logo_dark.png
│   └── favicon.png
│
├── output_projects/              # Wygenerowane projekty
│                           # (czyszczone automatycznie)
├── chroma_db_store/        # RAG - ChromaDB storage
│
├── .env                    # Konfiguracja (nie commituj!)
├── config.toml             # Ustawienia Chainlit
├── app.py                  # Entry point
├── chainlit.md             # Ekran powitalny
└── requirements.txt        # Zależności Python
```

### LangGraph Flow:

```python
StateGraph(AgentState)
  ├─ planner_node      (Product Owner)
  ├─ architect_node    (Architekt)
  ├─ coder_node        (Developer)
  ├─ reviewer_node     (QA Engineer)
  └─ should_continue   (conditional edge)
       ├─ "fix" → coder_node (retry, max 5x)
       └─ "end" → END
```

### State Schema:

```python
class AgentState(TypedDict):
    messages: List[BaseMessage]       # Historia konwersacji
    plan: str                         # Plan od Architekta
    current_files: List[str]          # Pliki w workspace
    feedback: str                     # Feedback od QA
    revision_count: int               # Licznik iteracji (max 5)
    model_names: Dict[str, str]       # Nazwy modeli do użycia
```

---

## 🎨 Interfejs UI

### Deep Space Theme

AgileFlow ma nowoczesny **dark mode** inspirowany estetyką kosmiczną:

- **Tło:** Głęboka czerń (#050507) z subtelną siatką
- **Akcenty:** Indigo neon (#6366f1) z efektem glow
- **Dymki czatu:** Gradient (użytkownik) / ciemny panel (AI)
- **Fonty:** Inter (tekst) + JetBrains Mono (kod)

### Funkcje UI:

✅ **Real-time streaming** – widzisz odpowiedzi AI na żywo  
✅ **Process visibility** – każdy agent pokazuje co robi  
✅ **File preview** – podgląd generowanych plików  
✅ **Dark scrollbar** – custom design nawet dla paska przewijania  

---

## 🧠 RAG (Retrieval-Augmented Generation)

### Jak działa pamięć?

1. **Product Owner** tworzy backlog → zapisuje do ChromaDB
2. **Architekt** czyta backlog z ChromaDB → tworzy plan → zapisuje plan
3. **Developer** czyta backlog + plan z ChromaDB → pisze kod
4. **QA** czyta wszystko z ChromaDB → sprawdza spójność

### Co daje RAG?

- ✅ Agenci **nie gubią kontekstu** między iteracjami
- ✅ Developer **wie dokładnie** co ma zaimplementować
- ✅ QA **weryfikuje** czy kod spełnia backlog
- ✅ **Konsystencja** w całym projekcie

### Baza danych:

```
chroma_db_store/
├── chroma.sqlite3       # Metadata
└── [embeddings]         # Wektory (nomic-embed-text)
```

---

## 🐛 Troubleshooting

### Problem: "Model zwrócił 0 znaków"

**Rozwiązanie 1:** Test z innym modelem
```env
MODEL_CODER=llama3.3:70b  # Zamiast Qwen
```

**Rozwiązanie 2:** Sprawdź czy model jest loaded
```bash
ollama ps
ollama run qwen3-coder:30b "test"
```

**Rozwiązanie 3:** Zwiększ timeout
```python
# W llm_factory.py
timeout=600.0  # 10 minut zamiast 5
```

### Problem: "504 Gateway Timeout"

**Przyczyna:** Proxy/firewall blokuje `localhost`

**Rozwiązanie:**
```env
# W .env użyj IP zamiast hostname:
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

### Problem: "Workspace nie czyści się"

**Przyczyna:** Brak uprawnień do usuwania plików

**Rozwiązanie:**
```bash
# Ręczne czyszczenie
rm -rf workspace/*        # Linux/Mac
rmdir /s /q workspace     # Windows
```

### Problem: "ChromaDB nie działa"

**Rozwiązanie 1:** Usuń bazę i stwórz od nowa
```bash
rm -rf chroma_db_store/
```

**Rozwiązanie 2:** Sprawdź model embeddings
```bash
ollama pull nomic-embed-text
```

### Problem: "Out of Memory"

**Przyczyna:** Za mało RAM dla 70B modelu

**Rozwiązanie:** Użyj mniejszych modeli
```env
MODEL_REASONING=llama3.3:latest  # 8B zamiast 70B
MODEL_CODER=qwen2.5-coder:14b    # 14B zamiast 30B
```

---

## ❓ FAQ

**Q: Czy AgileFlow działa offline?**  
A: **Tak!** Wszystko działa lokalnie przez Ollama. Zero połączenia z internetem po instalacji.

**Q: Jakie języki programowania obsługuje?**  
A: Python, .NET (C#), JavaScript/TypeScript, Blazor, FastAPI, Angular, React. Można dodać więcej przez modyfikację promptów.

**Q: Ile czasu trwa generowanie projektu?**  
A: 3-7 minut dla prostych projektów, 10-20 minut dla złożonych (zależy od hardware i liczby iteracji).

**Q: Czy mogę użyć modeli z OpenAI/Anthropic?**  
A: Tak, wystarczy zmienić `llm_factory.py` na `ChatOpenAI` lub `ChatAnthropic`.

**Q: Czy Developer może edytować istniejący kod?**  
A: **Tak!** Developer ma tryb REFACTORING – wczytuje pliki z `workspace/` i modyfikuje je. RAG pamięta poprzednie iteracje.

**Q: Co to znaczy "automatyczne czyszczenie workspace"?**  
A: Przy każdym nowym zadaniu folder `workspace/` jest czyszczony, żeby nie mieszać projektów. Stare projekty możesz skopiować gdzie indziej przed uruchomieniem.

**Q: Jak zmienić limit iteracji (max 5)?**  
A: W `app.py`, funkcja `should_continue()`:
```python
if state["revision_count"] >= 10:  # Zmień 5 na 10
    return "end"
```

---
