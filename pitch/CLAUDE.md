# Pitch-maker — агент создания питчей в СМИ

Главная функция: **берёт тему/черновик питча + ссылку на издание и формирует питч** с обоснованием темы, тезисами, рекомендациями по подаче и стратегией контакта.

> Корневой контекст `pr-helper/CLAUDE.md` и `pr-helper/shared/zerocoder-context.md` уже подгружены автоматически. Здесь — специфика этого агента.

---

## Структура агента

```
pitch/
  CLAUDE.md                          ← этот файл
  
  .claude/
    agents/
      platform-research.md           ← субагент: ресёрч медиаплощадки
      pitch-analyst.md               ← субагент: анализ темы + площадки
      pitch-writer.md                ← субагент: написание питча
    skills/
      pitch/skill.md                 ← базовый скилл
      pitch-pipeline/skill.md        ← связка всех 3 субагентов
    agent-memory/                    ← локальная память субагентов (личные feedback'и)
  
  outputs/                           ← готовые питчи
  results/                           ← результаты отправки (что вышло)
```

## Цепочка работы (3 субагента)

1. **platform-research** — собирает редакционные данные о площадке (структура, авторы, форматы, политика, контакты)
2. **pitch-analyst** — анализирует тему + сопоставляет с данными площадки → стратегические рекомендации
3. **pitch-writer** — пишет финальный питч

См. `.claude/skills/pitch-pipeline/skill.md` для оркестрации.

---

## Подключение к Google Sheets

Pitch использует shared-библиотеку `pr-helper/mediabase/sheets.py` — **один лист `Медиабаза`** (15 колонок) для всех агентов.

**Что читает:**
- `sheets.get_touch_state(сайт)` — статус прогрева, контакты, история, следующее касание
- `sheets.get_publication(сайт)` — полная карточка издания (тип, охват, редакция, повестка_ии, правила_публикации, комментарий) — для понимания формата при формулировке питча

**Что пишет (с подтверждения Сони):**
- `sheets.log_touch(сайт, date_str, тема, результат, next_touch_days=7)` — после отправки питча: добавляет запись в `история_касаний` + ставит `следующее_касание` через N дней
- `sheets.update_publication(сайт, статус_прогрева=..., следующее_касание=...)` — точечные изменения

Параметры `next_touch_days`: **7** для 2-го касания, **14** для 3-го касания (по согласованной с Соней логике напоминаний).

### Пример чтения

```bash
python -c "
import sys; sys.path.insert(0, 'C:/Users/sofit/клодик/pr-helper/mediabase')
import sheets, json
state = sheets.get_touch_state('e1.ru')
print(json.dumps(state, ensure_ascii=False, indent=2))
"
```

### Пример записи (после отправки питча)

```python
import sheets
sheets.log_touch(
    site='vn.ru',
    date='2026-06-13',
    тема='метрикократия — колонка Кирилла',
    результат='на рассмотрении',
)
```

---

## Длинный контент по площадкам

**Раньше:** в `pitch/.claude/agent-memory/platform-research/*.md` лежали детальные досье (74ru, e1ru, ura-news).

**Теперь:** длинные ресёрчи живут в `pr-helper/article-adapter/publications/<slug>/research/`. Короткие поля прогрева — в Sheets, лист `Касания`.

Маппинг slug ↔ сайт берётся из листа `Адаптация`:

| сайт | slug | Папка |
|---|---|---|
| 74.ru | 74ru | `article-adapter/publications/74ru/` |
| e1.ru | e1ru | `article-adapter/publications/e1ru/` |
| ura.news | ura-news | `article-adapter/publications/ura-news/` |
| vn.ru | vn | `article-adapter/publications/vn/` |
| secrets.tbank.ru | t-business | `article-adapter/publications/t-business/` |
| hrlogia.ru | hrlogia | `article-adapter/publications/hrlogia/` |

Pitch читает оттуда `rules.md` и последние `research/*.md`, чтобы понимать профиль издания.

---

## Принципы работы

- **Любая запись в Sheets — с подтверждения Сони.** Никаких автоматических обновлений.
- **Контакт с редактором** в питче — брать из `Касания.контактное_лицо`. Если устарел — спросить Соню.
- **Степень прогрева** влияет на стратегию: «холодный» — мягкий вход, «лояльный» — прямое предложение.
- **История касаний** — учитывать при формировании темы (не дублировать то, что уже отправляли).

---

## Связки с другими агентами

- **CRM (mediabase)** — общая Sheets через `sheets.py`. Pitch читает `Касания`, пишет с подтверждения.
- **article-adapter** — pitch и адаптер не связаны напрямую. Питч прошёл → Соня сама вызывает адаптер для подготовки финального материала. Общая Sheets — единственная связь.
- **B2BChat, newsjacking** — не связаны напрямую.

---

## Текущий статус

- ✅ 3 субагента описаны (platform-research, pitch-analyst, pitch-writer)
- ✅ Pipeline-скилл собран
- ✅ Подключение к Google Sheets через `mediabase/sheets.py`
- ✅ Лист `Касания` создан с начальными данными по 6 изданиям
- ✅ Длинные досье мигрированы в `article-adapter/publications/<slug>/research/`
- ⏳ Pipeline-скилл нужно проверить с реальной задачей после миграции
