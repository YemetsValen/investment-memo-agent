# Investment Memo Agent — Описание проекта

## Зачем создан

Investment Memo Agent — это AI-ассистент для инвестиционного due-diligence, который автоматизирует процесс анализа публичных компаний. Вместо того чтобы вручную собирать финансовые данные, считать метрики и писать аналитические записки, агент делает это за секунды: принимает на вход тикер компании (например `AAPL`, `TSLA`, `NVDA`) и выдаёт структурированное инвестиционное memo с рекомендацией.

Проект демонстрирует:
- **Мульти-агентную AI-архитектуру** (LangGraph) — пайплайн из 4 специализированных агентов
- **Human-in-the-loop паттерн** — автоматическая маршрутизация сомнительных результатов на ручную проверку
- **Гибридный подход** — детерминированные правила + LLM-анализ для надёжности
- **AI-native интеграции** — MCP-сервер для работы с Claude Desktop и Cursor

---

## Какой функционал выполняет

### 1. Автоматический сбор данных (Researcher)
- Загружает финансовые метрики через **yfinance** (бесплатно, без API-ключа): P/E, market cap, margins, ROE, debt/equity, free cash flow и ещё 15+ показателей
- Получает текущую цену и 52-недельный диапазон
- Собирает новостной фон по компании

### 2. Инвестиционный анализ (Analyst)
- LLM генерирует **краткое резюме** по финансовому профилю компании
- Формирует **инвестиционный тезис** — аргументы за и против инвестирования
- Выдаёт первичную **рекомендацию**: BUY / HOLD / SELL / AVOID

### 3. Оценка рисков (Risk)
Двухуровневая система:

**Rule-based (без LLM):**
| Правило | Порог | Уровень |
|---------|-------|---------|
| P/E > 40 | Переоценка | MEDIUM |
| P/B > 10 | Переоценка | MEDIUM |
| Debt/Equity > 200 | Долговая нагрузка | HIGH |
| Profit Margin < 0 | Убыточность | HIGH |
| Current Ratio < 0.5 | Ликвидность | CRITICAL |
| Beta > 2 | Волатильность | MEDIUM |
| Revenue Growth < -20% | Падение выручки | HIGH |
| Earnings Growth < -50% | Обвал прибыли | CRITICAL |
| Free Cash Flow < 0 | Отрицательный FCF | HIGH |

**LLM-based:** дополнительный качественный анализ контекстных рисков (регуляторные, конкурентные, макро).

### 4. Генерация отчёта (Writer)
Создаёт **структурированное инвестиционное memo** в Markdown:
- Рекомендация и уровень уверенности
- Резюме и инвестиционный тезис
- Таблица ключевых финансовых метрик
- Таблица риск-флагов с уровнями (LOW / MEDIUM / HIGH / CRITICAL)
- Последние новости

### 5. REVIEW Queue (Human-in-the-loop)
Паттерн из [strict-moderator](https://github.com/YemetsValen/strict-moderator) — если результат вызывает сомнения, memo не публикуется автоматически, а уходит на ручную проверку:

| Условие | Действие |
|---------|----------|
| Уверенность < 0.7 (70%) | → Очередь на проверку |
| Есть CRITICAL риск-флаг | → Очередь на проверку |
| ≥ 3 HIGH риск-флагов | → Очередь на проверку |
| Всё остальное | → Авто-публикация |

Аналитик может **одобрить** или **отклонить** memo через API.

### 6. MCP-сервер
Экспонирует 4 инструмента для использования в **Claude Desktop** или **Cursor**:
- `get_financials` — получить финансовые метрики по тикеру
- `generate_memo` — запустить полный анализ
- `screen_company` — быстрый скрининг (только правила, без LLM)
- `list_review_queue` — посмотреть очередь на проверку

### 7. REST API
7 эндпоинтов через FastAPI:
- `POST /api/v1/analyze` — запуск полного анализа
- `GET /api/v1/memo/{id}` — получить memo по ID
- `GET /api/v1/memos` — список всех memo
- `GET /api/v1/review-queue` — очередь на проверку
- `POST /api/v1/review-queue/{id}/approve` — одобрить memo
- `POST /api/v1/review-queue/{id}/reject` — отклонить memo
- `GET /api/v1/health` — health check

---

## Для каких бизнес-задач пригодится

### Инвестиционные фонды и аналитики
- **Ускорение pre-screening**: вместо 30–60 минут на первичный анализ компании — результат за 30 секунд
- **Стандартизация отчётов**: все memo в одном формате, легко сравнивать
- **Фильтрация**: REVIEW queue автоматически выделяет компании, требующие углублённого анализа

### Wealth Management и Private Banking
- **Быстрый ответ клиенту**: «Что думаете про Tesla?» — memo за минуту, а не за день
- **Compliance**: автоматическое выявление рисков (долговая нагрузка, убыточность, волатильность) до принятия решения
- **Audit trail**: все memo сохраняются с timestamps, рекомендациями и уровнем уверенности

### Финтех-продукты
- **Встраиваемый модуль**: REST API позволяет интегрировать анализ в любую платформу
- **Robo-advisor backend**: автоматическая оценка компаний для формирования портфелей
- **Скрининг вселенной акций**: eval runner на 47+ компаниях, масштабируется на тысячи

### Образование и исследования
- **Обучение инвестиционному анализу**: студенты видят структурированный подход к due diligence
- **Бэктестинг правил**: eval dataset позволяет проверять и настраивать пороги риск-флагов
- **Демонстрация AI-native архитектуры**: мульти-агентный пайплайн как учебный пример

### AI/ML Engineering
- **Портфолио-проект**: демонстрирует LangGraph, MCP, structured output, human-in-the-loop
- **Шаблон для мульти-агентных систем**: паттерн Researcher → Analyst → Risk → Writer переносится на другие домены
- **Eval-driven development**: встроенный датасет для оценки качества rule-based детекции

---

## Как запустить

### Требования
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — менеджер пакетов (рекомендуется)
- API-ключ Anthropic или OpenAI (для полного пайплайна с LLM)

### Установка

```bash
# Клонировать репозиторий
git clone https://github.com/YemetsValen/investment-memo-agent.git
cd investment-memo-agent

# Установить зависимости
uv sync

# Скопировать шаблон .env и добавить API-ключ
cp .env.example .env
# Отредактировать .env — указать ANTHROPIC_API_KEY или OPENAI_API_KEY
```

### Запуск API-сервера

```bash
uv run uvicorn src.main:app --port 8000
```

После запуска:
- **Swagger UI**: http://localhost:8000/docs — интерактивная документация
- **API**: http://localhost:8000/api/v1/

### Пример запроса

```bash
# Запустить анализ Apple
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'

# Ответ:
# {"memo_id": "abc123", "status": "COMPLETED", "message": "Analysis complete. Recommendation: HOLD"}

# Получить полное memo
curl http://localhost:8000/api/v1/memo/abc123
```

### Запуск MCP-сервера (для Claude Desktop / Cursor)

```bash
uv run memo-mcp
```

Добавить в конфиг Claude Desktop (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "investment-memo-agent": {
      "command": "uv",
      "args": ["run", "memo-mcp"],
      "cwd": "/path/to/investment-memo-agent"
    }
  }
}
```

### Запуск без LLM (только rule-based)

Без API-ключа работают:
- `GET /health` — проверка работоспособности
- `GET /memos`, `GET /review-queue` — просмотр данных
- Все unit-тесты и eval runner (rule-based детекция рисков)

```bash
# Тесты (22 штуки, без LLM)
uv run pytest -v

# Eval runner (rule-based risk detection, 47 компаний)
uv run python -m evals.run_evals

# Lint
uv run ruff check src/ tests/ evals/
```

---

## Стек технологий

| Компонент | Технология | Зачем |
|-----------|-----------|-------|
| API | **FastAPI** + Pydantic v2 | Асинхронный REST API с автоматической валидацией и документацией |
| Агенты | **LangGraph** (StateGraph) | Оркестрация мульти-агентного пайплайна с условными переходами |
| LLM | Anthropic Claude / OpenAI | Генерация тезисов и качественный анализ рисков |
| Данные | **yfinance** | Бесплатные финансовые данные без API-ключа |
| MCP | `mcp` SDK | Интеграция с Claude Desktop и Cursor как набор инструментов |
| Storage | In-memory (заменяемо на SQLite/Postgres) | Хранение memo и очереди на проверку |
| Тесты | **pytest** + pytest-asyncio | 22 unit-теста на модели, правила и логику очереди |
| Lint | **ruff** | Линтинг и форматирование |
| Package Manager | **uv** | Быстрая установка зависимостей |

---

## Архитектура пайплайна

```
Пользователь                    LangGraph Pipeline
     │                               │
     │  POST /analyze {"ticker":"AAPL"}
     │──────────────────────────────▶│
     │                               │
     │                    ┌──────────▼──────────┐
     │                    │    Researcher Node   │
     │                    │                      │
     │                    │  • yfinance API      │
     │                    │  • Финансовые метрики │
     │                    │  • Новости           │
     │                    └──────────┬──────────┘
     │                               │
     │                    ┌──────────▼──────────┐
     │                    │    Analyst Node      │
     │                    │                      │
     │                    │  • LLM: резюме       │
     │                    │  • LLM: тезис        │
     │                    │  • Рекомендация       │
     │                    └──────────┬──────────┘
     │                               │
     │                    ┌──────────▼──────────┐
     │                    │     Risk Node        │
     │                    │                      │
     │                    │  • 9 rule-based      │
     │                    │    проверок          │
     │                    │  • LLM: качественные │
     │                    │    риски             │
     │                    │  • Confidence score   │
     │                    └──────────┬──────────┘
     │                               │
     │                    ┌──────────▼──────────┐
     │                    │    Writer Node       │
     │                    │                      │
     │                    │  • Markdown отчёт    │
     │                    │  • Таблицы метрик    │
     │                    │  • Risk assessment   │
     │                    └──────────┬──────────┘
     │                               │
     │                    ┌──────────▼──────────┐
     │                    │   Review Queue       │
     │                    │                      │
     │                    │  confidence < 0.7?   │──▶ REVIEW (ждёт проверки)
     │                    │  CRITICAL flags?     │
     │                    │  ≥3 HIGH flags?      │
     │                    │                      │
     │                    │  Нет → COMPLETED     │──▶ Авто-публикация
     │                    └─────────────────────┘
     │                               │
     │  {"memo_id":"...", "status":"COMPLETED", "message":"..."}
     │◀──────────────────────────────│
```

---

## Пример сгенерированного memo

```markdown
# Investment Memo — Apple Inc. (AAPL)

> **Recommendation:** **HOLD**
> **Confidence:** 75%
> **Generated:** 2026-06-03 04:51 UTC

## Summary
Apple Inc. is a dominant technology company with a $4.6 trillion market cap,
trading near 52-week highs with strong profitability metrics including
27% profit margins and exceptional ROE of 141%.

## Investment Thesis
Apple's exceptional profitability (27% margins, 141% ROE) and massive
free cash flow generation ($101B) justify premium valuation, but current
P/E of 38x suggests limited upside at current levels.

## Key Financial Metrics
| Metric         | Value     |
|----------------|-----------|
| Market Cap     | $4.63T    |
| P/E Ratio      | 38.16     |
| Profit Margin  | 27.2%     |
| ROE            | 141.5%    |
| Free Cash Flow | $101.09B  |

## Risk Assessment
| Level    | Category   | Description                          |
|----------|------------|--------------------------------------|
| 🟡 MEDIUM | Valuation | Price-to-book ratio very high (43.4x) |

**Total flags:** 1 | **Critical:** 0 | **High:** 0
```

---

## Лицензия

MIT
