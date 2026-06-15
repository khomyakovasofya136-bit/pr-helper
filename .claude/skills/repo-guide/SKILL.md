---
name: repo-guide
description: Помогает Claude Code работать с репозиторием pr-helper: ориентироваться в структуре, запускать сервисы, вносить изменения, обновлять README, диагностировать ошибки и готовить проект к публикации. Триггеры — «разберись в проекте», «как устроен репо», «обнови README», «проверь ошибки», «подготовь к публикации», «что здесь изменить».
---

# Repo Guide — навигатор по pr-helper

Этот скилл нужен, когда задача касается самого репозитория: понять структуру, запустить что-то, поправить конфиг, обновить документацию или подготовить к пушу.

---

## Карта проекта

```
pr-helper/
├── CLAUDE.md                    ← корневой координатор (читать первым)
├── README.md                    ← публичное описание проекта
├── .gitignore                   ← что не пушить (credentials, фото, pdf)
│
├── shared/
│   └── zerocoder-context.md    ← единственный источник правды о бренде
│
├── newsjacking/                 ← автодайджест (cloud routine, 10:00 МСК)
│   ├── CLAUDE.md
│   ├── config.md               ← параметры routine (MAX=10, MIN=5)
│   └── .claude/skills/manual-digest/
│
├── pitch/                       ← питчи в редакции (3 субагента)
│   ├── CLAUDE.md
│   ├── .claude/agents/         ← platform-research / pitch-analyst / pitch-writer
│   ├── .claude/skills/pitch/ и pitch-pipeline/
│   ├── outputs/                ← готовые питчи
│   └── results/                ← результаты касаний
│
├── article-adapter/             ← адаптация статей под издания
│   ├── CLAUDE.md
│   ├── promts/                 ← style-reference, editorial-criteria, brand-block-pattern, mode-*
│   ├── publications/<slug>/    ← rules.md + research/ + examples/
│   ├── inputs/                 ← статьи на адаптацию
│   └── outputs/                ← адаптированные версии
│
├── b2bchat/                     ← посты для TG B2B-канала
│   ├── CLAUDE.md
│   ├── references/top-posts.md ← 5 эталонов + что работает
│   ├── output/                 ← готовые посты (.md + .json)
│   └── .claude/skills/topic-discovery/ и AI-News to Social/
│
└── mediabase/                   ← CRM + shared Python-библиотека
    ├── CLAUDE.md
    ├── sheets.py               ← единственная точка доступа к Google Sheets
    ├── credentials.json        ← НЕ пушить (в .gitignore)
    └── media/                  ← legacy CSV (источник истины — Sheets)
```

---

## Понять структуру

Если нужно быстро разобраться в каком-то агенте:

1. Прочитать `pr-helper/CLAUDE.md` — карта системы и поток данных
2. Прочитать `<agent>/CLAUDE.md` — что делает агент, какие скиллы, связки
3. Прочитать `<agent>/.claude/skills/<skill>/SKILL.md` — алгоритм конкретного скилла

Поток данных между агентами:
```
newsjacking (авто) → дайджест → b2bchat (топик) или pitch (питч) →
  pitch логирует в Sheets через log_touch() →
  статья принята → article-adapter → b2bchat анонсирует
```

Связь через Google Sheets — единый лист «Медиабаза» (206 изданий, 15 колонок).  
Shared-библиотека: `mediabase/sheets.py` — импортируется в article-adapter и pitch.

---

## Запустить сервисы

### Проверить подключение к Google Sheets

```bash
python -c "
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'mediabase')
import sheets
records = sheets.read_tab()
print(f'OK — {len(records)} записей в Медиабазе')
"
```

Ожидаемый вывод: `OK — 206 записей в Медиабазе`

### Проверить зависимости Python

```bash
python -c "import gspread; import google.oauth2; print('OK')"
```

Если ошибка → `pip install gspread google-auth`

### Запустить дайджест вручную

Через Claude Code: вызвать скилл `manual-digest` в папке `newsjacking/`.  
Или напрямую по расписанию: cloud routine `trig_01P3wdTRExUwz67ogztXNi7C` (10:00 МСК).

### Запустить отдельный агент

Все агенты работают через Claude Code — вызвать нужный скилл в рабочей директории агента:
- `pitch/` → скилл `pitch` или `pitch-pipeline`
- `article-adapter/` → скилл `adaptation`, `rewrite`, `editing`, `fragment-edit`
- `b2bchat/` → скилл `topic-discovery` или `AI-News to Social`
- `mediabase/` → скилл `check-touches`, `research-publication`, `update-publication`

---

## Внести изменения

### Изменить инструкции агента

Файл: `<agent>/CLAUDE.md`  
Что содержит: роль агента, что читать при старте, какие скиллы, связки с другими агентами.  
После правки: проверь, не дублируется ли информация из `pr-helper/CLAUDE.md` или `shared/zerocoder-context.md`.

### Изменить скилл

Файл: `<agent>/.claude/skills/<skill>/SKILL.md`  
Структура скилла: триггеры → алгоритм по шагам → что читать → что не делать.  
После правки: проверь, что триггеры не конфликтуют с другими скиллами того же агента.

### Изменить стилевые промты (article-adapter)

Файлы в `article-adapter/promts/`:
- `style-reference.md` — образцы лидов, ритма, крючков
- `editorial-criteria.md` — 8 принципов + 10 критериев + антипаттерны
- `brand-block-pattern.md` — структура обязательного брендового блока
- `mode-*.md` — алгоритм конкретного режима (adaptation / rewrite / editing / fragment)

Эти файлы читаются при каждой задаче — изменения влияют на все адаптации сразу.

### Добавить новое издание в article-adapter

1. Создать папку `article-adapter/publications/<slug>/`
2. Добавить `rules.md` (параметры: длина, формат, тональность, спикер, рубрика)
3. Добавить `research/YYYY-MM_initial.md` (редакция, авторы по ИИ, контакты)
4. Опционально: `examples/` с образцами публикаций Зерокодера
5. Добавить запись в Google Sheets через скилл `update-publication`

### Обновить общий контекст бренда

Файл: `shared/zerocoder-context.md`  
Это единственный источник правды о компании — не дублировать в папках агентов.  
Что хранится: метрики, спикеры, клиенты, риск-зоны, TOV.

---

## Обновить README

README описывает проект для внешней аудитории (GitHub). Обновлять когда:
- Добавлен новый агент или скилл
- Изменилась технология или интеграция
- Изменился поток данных
- Добавлены новые издания или источники

### Что проверить при обновлении

| Секция | Источник актуальных данных |
|---|---|
| Основная функция (таблица агентов) | `pr-helper/CLAUDE.md` → Карта агентов |
| Функционал | `<agent>/CLAUDE.md` → описание режимов |
| Технологии | `mediabase/sheets.py` → импорты; `newsjacking/config.md` → инструменты |
| Структура проекта | реальные папки (Glob `**`) |
| Поток данных | `pr-helper/CLAUDE.md` → «Как агенты связаны» |
| Запуск / зависимости | `mediabase/sheets.py` заголовок + credentials |

### Что НЕ писать в README

- Статусы готовности («85%», «в процессе», «осталось проверить»)
- Внутренние TODO и заметки
- Детали реализации, интересные только разработчику (ID routine, внутренние пути)
- Упоминание конкретных паролей, токенов, email

---

## Проверить ошибки

### Ошибка: `credentials.json` не найден

```
FileNotFoundError: credentials.json
```

Решение: файл должен быть в `mediabase/credentials.json`. Не коммитится в git (в `.gitignore`). Получить у Сони или создать новый сервисный аккаунт в Google Cloud Console.

### Ошибка: Google Auth / API quota

```
google.auth.exceptions.TransportError
gspread.exceptions.APIError: {'code': 429}
```

Решение 429: подождать 60 секунд, Google Sheets API имеет лимит 60 запросов/минуту.  
Решение TransportError: проверить интернет-соединение и валидность `credentials.json`.

### Ошибка: кириллица в выводе bash (Windows)

```
������ ������������
```

Решение — добавить в начало Python-скрипта:
```python
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

### Ошибка: издание не найдено в Sheets

```python
sheets.get_publication('vn.ru')  # → None
```

Возможные причины:
- Сайт записан с `https://` или завершающим `/` → `sheets._norm_site()` нормализует, но проверь формат
- Опечатка в домене
- Запись ещё не создана → добавить через скилл `update-publication`

### Ошибка: вложенный git-репозиторий

```
hint: You've added another git repository inside your current repository
```

Решение: удалить `.git` внутри вложенной папки (уже сделано для `mediabase/` при первом пуше).

### Ошибка: `credentials.json` попал в git

```bash
git status  # показывает credentials.json как staged
```

Немедленно:
```bash
git rm --cached mediabase/credentials.json
git commit -m "fix: remove credentials from tracking"
```

Убедиться, что строка `mediabase/credentials.json` есть в `.gitignore`.

---

## Подготовить к публикации (git push)

### Чеклист перед пушем

```
[ ] credentials.json не в staging (git status)
[ ] .gitignore содержит: credentials.json, photos/, stickers/, analytics.html, analytics.pdf
[ ] README.md актуален (нет статусов «в разработке», внутренних TODO)
[ ] Нет незакоммиченных изменений, которые не должны уйти
[ ] В CLAUDE.md не утекли токены, пароли, личные данные
```

### Команды перед пушем

```bash
# Проверить статус
git status

# Проверить, что не попало в staged нечего лишнего
git diff --staged --name-only

# Проверить .gitignore
cat .gitignore
```

### Нейминг коммитов

Формат: `тип: короткое описание на русском`

Типы:
- `feat:` — новый агент, скилл, режим
- `fix:` — исправление ошибки
- `docs:` — обновление README, CLAUDE.md
- `refactor:` — реструктуризация без изменения функции
- `data:` — обновление баз данных, досье изданий

Примеры:
```
feat: добавить скилл repo-guide для навигации по проекту
docs: обновить README — добавить секцию про поток данных
fix: исправить кодировку в sheets.py для Windows
data: добавить досье hrlogia — rules + research
```

### Что включать в репо, что нет

| Включать | Не включать |
|---|---|
| CLAUDE.md всех агентов | `credentials.json` |
| SKILL.md всех скиллов | `b2bchat/posts/photos/` |
| `sheets.py` (без токенов) | `b2bchat/posts/stickers/` |
| `promts/` и `publications/` | `analytics.html`, `analytics.pdf` |
| `shared/zerocoder-context.md` | `.claude/settings.local.json` |
| Примеры статей в `examples/` | Файлы с личными данными |

---

## Что НЕ делать

- Не трогать `shared/zerocoder-context.md` без явного запроса — это shared-источник для всех агентов
- Не дублировать контекст бренда в папках агентов — только ссылка на `shared/`
- Не коммитить `credentials.json` ни при каких условиях
- Не удалять файлы из `outputs/` и `results/` — это история работы агентов
- Не переписывать `sheets.py` без теста подключения после правки
- Не создавать новые листы в Google Sheets — всё в едином «Медиабаза»
