# Newsjacking Agent — Config

> **Источник истины — routine в claude.ai** (запускается в cloud каждый день в 10:00 МСК). Этот файл — документация и backup для ручного запуска через Claude Code локально.

---

## Telegram Bot

```
BOT_TOKEN=[YOUR_BOT_TOKEN]
CHAT_ID=[YOUR_CHAT_ID]
```

> Токены хранятся только в routine (cloud-сессия не имеет доступа к локальным файлам). В этот файл не вписывать.

Как получить chat_id: написать боту любое сообщение, затем открыть в браузере:
`https://api.telegram.org/bot{BOT_TOKEN}/getUpdates`
Найти поле `"chat": {"id": ...}`.

---

## Расписание

- **Cron:** `0 7 * * *` (UTC) = **10:00 МСК ежедневно**
- **Горизонт выборки:** последние 24 часа от момента запуска
- **Последний запуск / следующий запуск:** см. routine в claude.ai

---

## Параметры дайджеста

```
MAX_STORIES=10        # максимум тем в одном дайджесте
MIN_RELEVANCE=5       # минимальный балл релевантности (из 10)
ANGLES_PER_STORY=3    # количество вариантов угла подачи
```

---

## RSS-ленты (в routine)

```
https://rss.rbc.ru/rbc.ru/mainnews.rss
https://www.kommersant.ru/RSS/news.xml
https://www.vedomosti.ru/rss/news
https://www.forbes.ru/rss
https://vc.ru/rss
https://habr.com/ru/rss/articles/
https://techcrunch.com/feed/
https://venturebeat.com/feed/
```

## RSS-ленты (резерв — пока не в routine)

Дополнительные источники, протестировать на полезность и при необходимости добавить:
- https://feeds.feedburner.com/TechCrunch
- https://www.thenextweb.com/feed/
- https://www.wired.com/feed/rss
- https://edtechdigest.com/feed/
- https://www.edsurge.com/news.rss

---

## Telegram-каналы (через `t.me/s/{channel}`)

```
setters, adindex, ppprompt, whackdoor, exploitex, exfinnnews, vcnews,
theeasterncourier, seniorsoftwarevlogger, cryptoEssay, ru_education,
breakingtrends, AgencySmartRanking, habr_com_news, edtexno, prompt_design,
mikhailumarovpr, seeallochnaya, oestick, openspace_notes, denissexy,
prpioner, b2bjournal, themedia, leadgr, korenev_ai, tired_glebmikheev,
ai_newz, larkinmd07, glavred_izdatel, variantspr, prmaslennikov, ctodaily,
zamesin, sell_me
```

Всего: 35 TG-каналов.

---

## Ключевые слова (фильтр)

```
KEYWORDS_RU=ИИ, нейросеть, искусственный интеллект, ChatGPT, GPT,
            нейросети, автоматизация, EdTech, онлайн-образование,
            вайб-кодинг, цифровизация, рынок труда, навыки будущего
KEYWORDS_EN=AI, artificial intelligence, neural network, GPT,
            automation, EdTech, upskilling, reskilling
```

---

## Как менять параметры

**Если меняешь RSS / каналы / ключевые слова / параметры:**
1. Поправить в этом файле (для документации)
2. Обновить routine через `/schedule` или через RemoteTrigger API
3. Параметры в routine — **источник истины**

Если просто меняешь этот файл — изменения **не повлияют** на ежедневный дайджест.

---

## Как запустить вручную

- Через `/schedule` → `run [YOUR_ROUTINE_ID]` (cloud-сессия)
- Или через локальный скилл `manual-digest` (см. `.claude/skills/manual-digest/SKILL.md`)
