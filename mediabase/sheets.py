"""
Shared-библиотека для работы с единым листом 'Медиабаза' в Google Sheets.

Используется агентами pr-helper:
- mediabase (CRM) — управляет листом, ведёт ресёрч редакций, обновляет статусы
- article-adapter — читает параметры для адаптации статей
- pitch — читает состояние касаний, логирует отправленные питчи

Все write-операции требуют подтверждения пользователя на стороне агента.

Структура листа 'Медиабаза' (15 колонок):
1. сайт              — PK, домен (vn.ru / @channel / vk.com/...)
2. slug              — короткое имя папки для article-adapter
3. название          — полное имя издания
4. тип               — маркетинг / HR / региональное / госсектор / деловое / TG-VK / ...
5. приоритет         — цифра 1-5 (по охвату)
6. охват             — конкретное значение
7. редакция          — структура + редакторы + профильные авторы по ИИ (текстом)
8. повестка_ии       — последние материалы + типовой формат (текстом)
9. контакты          — email + tg + телефон + имена (текстом)
10. правила_публикации — ссылки на правила на сайте редакции с описанием в скобках
11. статус_прогрева  — лояльный / тёплый / нейтральный / холодный / новый / отказ
12. история_касаний  — хронология одной ячейкой
13. следующее_касание — дата напоминания (YYYY-MM-DD)
14. последний_ресёрч — дата (YYYY-MM-DD)
15. комментарий      — свободная зона
"""
import gspread
from google.oauth2.service_account import Credentials
from gspread.utils import rowcol_to_a1
from pathlib import Path
from datetime import date, timedelta

SHEET_ID = "[YOUR_GOOGLE_SHEET_ID]"  # Вставь ID своей таблицы из URL Google Sheets
TAB_NAME = "Медиабаза"
CREDS_FILE = Path(__file__).parent / "credentials.json"
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


# ── Базовые операции ──────────────────────────────────────────────────────────

def _client():
    creds = Credentials.from_service_account_file(str(CREDS_FILE), scopes=SCOPES)
    return gspread.authorize(creds)


def get_sheet(tab_name: str = TAB_NAME):
    return _client().open_by_key(SHEET_ID).worksheet(tab_name)


def read_tab(tab_name: str = TAB_NAME) -> list[dict]:
    """Все записи листа в виде списка словарей."""
    return get_sheet(tab_name).get_all_records()


def list_tabs() -> list[str]:
    return [ws.title for ws in _client().open_by_key(SHEET_ID).worksheets()]


# ── Нормализация ──────────────────────────────────────────────────────────────

def _norm_site(s: str) -> str:
    import re
    if not s:
        return ''
    s = str(s).lower().strip()
    s = re.sub(r'^https?://', '', s)
    s = s.rstrip('/').lstrip('@')
    return s


# ── Парсинг охвата + расчёт приоритета (для CRM-агента) ──────────────────────

def parse_reach(raw: str) -> int:
    """
    Извлекает число подписчиков/визитов из строки охвата.
    '68200 / ER 21.4%' → 68200, '2.75M' → 2750000, '355K' → 355000, '24.1 млн' → 24100000.
    """
    import re
    if not raw:
        return 0
    s = str(raw).lower().replace(',', '.').replace('~', '').strip()
    if 'млн' in s or ('m' in s and 'мес' not in s.split('m')[0]):
        m = re.search(r'(\d+\.?\d*)\s*(?:млн|m)', s)
        if m:
            return int(float(m.group(1)) * 1_000_000)
    if 'тыс' in s or 'k' in s:
        m = re.search(r'(\d+\.?\d*)\s*(?:тыс|k)', s)
        if m:
            return int(float(m.group(1)) * 1_000)
    m = re.search(r'(\d{4,})', s.replace(' ', ''))
    if m:
        return int(m.group(1))
    return 0


def calc_priority(reach: int, media_type: str = '') -> int:
    """
    Приоритет 1-5 по охвату.
    TG-каналы (тип содержит TG или VK): 40K+/30K+/20K+/10K+ → 1/2/3/4, иначе 5.
    Сайты: 2M+/1M+/600K+/300K+ → 1/2/3/4, иначе 5.
    """
    is_tg = 'tg' in (media_type or '').lower() or 'vk' in (media_type or '').lower()
    if reach == 0:
        return 5
    if is_tg:
        if reach >= 40_000: return 1
        if reach >= 30_000: return 2
        if reach >= 20_000: return 3
        if reach >= 10_000: return 4
        return 5
    else:
        if reach >= 2_000_000: return 1
        if reach >= 1_000_000: return 2
        if reach >= 600_000: return 3
        if reach >= 300_000: return 4
        return 5


def _find_row(site: str) -> tuple[int, dict] | None:
    """Возвращает (row_number, dict) для записи по полю 'сайт'."""
    ws = get_sheet()
    records = ws.get_all_records()
    site_norm = _norm_site(site)
    for i, row in enumerate(records, start=2):
        if _norm_site(row.get('сайт', '')) == site_norm:
            return i, row
    return None


# ── Универсальное API ─────────────────────────────────────────────────────────

def get_publication(site: str) -> dict | None:
    """Полная запись по изданию. Используют все агенты."""
    result = _find_row(site)
    return result[1] if result else None


def update_publication(site: str, **updates) -> int | None:
    """
    Обновляет указанные поля для издания.

    Пример: update_publication('vn.ru', статус_прогрева='тёплый', последний_ресёрч='2026-06-14')

    Возвращает номер строки или None.
    Все изменения требуют подтверждения Сони на стороне агента.
    """
    result = _find_row(site)
    if not result:
        return None

    row_num, _ = result
    ws = get_sheet()
    headers = ws.row_values(1)

    batch = []
    for col_name, value in updates.items():
        if col_name not in headers:
            raise ValueError(f"Колонка '{col_name}' не найдена. Доступные: {headers}")
        col_idx = headers.index(col_name) + 1
        batch.append({'range': rowcol_to_a1(row_num, col_idx), 'values': [[value]]})

    if batch:
        ws.batch_update(batch)
    return row_num


def add_publication(row_data: dict) -> None:
    """Добавляет новое издание в конец листа."""
    ws = get_sheet()
    headers = ws.row_values(1)
    row = [row_data.get(h, '') for h in headers]
    ws.append_row(row, value_input_option='USER_ENTERED')


# ── Helper'ы для конкретных агентов ───────────────────────────────────────────

# === article-adapter ===

def get_adaptation_params(site: str) -> dict | None:
    """
    Для article-adapter. Возвращает поля, нужные для адаптации:
    slug, название, тип, рубрики/правила (через 'правила_публикации'),
    спикер (через 'комментарий' или 'редакция'), последний_ресёрч.
    Детальные параметры адаптации (стиль/лимит/ЦА/спикер) лежат в
    локальном publications/<slug>/rules.md, не в Sheets.
    """
    pub = get_publication(site)
    if not pub:
        return None
    return {
        'сайт': pub.get('сайт'),
        'slug': pub.get('slug'),
        'название': pub.get('название'),
        'тип': pub.get('тип'),
        'редакция': pub.get('редакция'),
        'правила_публикации': pub.get('правила_публикации'),
        'последний_ресёрч': pub.get('последний_ресёрч'),
        'комментарий': pub.get('комментарий'),
    }


# === pitch + CRM ===

def get_touch_state(site: str) -> dict | None:
    """
    Для pitch. Состояние касаний и контактов.
    """
    pub = get_publication(site)
    if not pub:
        return None
    return {
        'сайт': pub.get('сайт'),
        'название': pub.get('название'),
        'статус_прогрева': pub.get('статус_прогрева'),
        'контакты': pub.get('контакты'),
        'история_касаний': pub.get('история_касаний'),
        'следующее_касание': pub.get('следующее_касание'),
        'комментарий': pub.get('комментарий'),
    }


def log_touch(site: str, date_str: str, тема: str, результат: str = '',
              next_touch_days: int = 7) -> int | None:
    """
    Добавляет запись в 'история_касаний' + ставит 'следующее_касание'.

    Формат записи: 'YYYY-MM-DD: тема → результат'
    next_touch_days — через сколько дней напомнить о следующем касании (7 для 2-го, 14 для 3-го).
    """
    pub = get_publication(site)
    if not pub:
        return None

    existing = (pub.get('история_касаний') or '').strip()
    entry = f"{date_str}: {тема}"
    if результат:
        entry += f" → {результат}"
    new_history = (existing + '\n' + entry).strip() if existing else entry

    # Парсим дату и считаем следующее касание
    try:
        d = date.fromisoformat(date_str)
        next_touch = (d + timedelta(days=next_touch_days)).isoformat()
    except ValueError:
        next_touch = ''

    updates = {'история_касаний': new_history}
    if next_touch:
        updates['следующее_касание'] = next_touch

    return update_publication(site, **updates)


# === CRM (для напоминаний) ===

def find_overdue_touches(today: str | None = None) -> list[dict]:
    """
    Возвращает все издания, у которых 'следующее_касание' <= сегодня
    и статус_прогрева не 'отказ' и не пустое.
    Использует CRM-агент при команде 'проверь касания'.
    """
    if today is None:
        today = date.today().isoformat()

    overdue = []
    for row in read_tab():
        next_str = str(row.get('следующее_касание', '')).strip()
        status = str(row.get('статус_прогрева', '')).strip()
        if not next_str or status == 'отказ':
            continue
        try:
            if next_str <= today:
                overdue.append(row)
        except Exception:
            continue
    return overdue


# === Smoke-test ===

if __name__ == "__main__":
    import sys, io, json
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print('=== Все листы ===')
    print(json.dumps(list_tabs(), ensure_ascii=False, indent=2))

    print(f'\n=== Всего записей в "{TAB_NAME}" ===')
    rows = read_tab()
    print(f'{len(rows)} строк')

    print('\n=== Параметры адаптации для vn.ru ===')
    print(json.dumps(get_adaptation_params('vn.ru'), ensure_ascii=False, indent=2))

    print('\n=== Состояние касаний для e1.ru ===')
    print(json.dumps(get_touch_state('e1.ru'), ensure_ascii=False, indent=2))

    print('\n=== Просроченные касания (сегодня) ===')
    overdue = find_overdue_touches()
    print(f'Найдено: {len(overdue)}')
    for row in overdue[:5]:
        print(f'  • {row.get("название")} → {row.get("следующее_касание")}')
