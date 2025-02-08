# 🎙 Televoicer

**Ваш голосовой архив** — сохраняйте и отправляйте шаблоны!


## 🌟 Функционал

- ✅ **Сохраняйте аудио как шаблоны**: загружайте голосовые сообщения и храните их для повторного использования.
- 💫 **Волшебный инлайн-режим**:  доступ к шаблонам в любом чате через `@televoicerbot гшаб название`.
- 🚀 **Молниеносная отправка**: частые приветствия, шутки, напоминания — отправляйте их в пару кликов!

💡 Идеально для быстрых ответов, мемов, напоминаний или персональных аудиозаметок.


## 🛠 Технологии

- **Python 3.13**
- [Aiogram](https://aiogram.dev/) (асинхронный фреймворк для Telegram ботов)
- [Tortoise ORM](https://tortoise.github.io/) (для работы с базой данных)
- Poetry (управление зависимостями)
  

## ⚙️ Установка

1. Установите Poetry (если не установлен):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Клонируйте репозиторий:
```bash
git clone https://github.com/lordralinc/televoicer.git
cd televoicer
```

3. Установите зависимости:
```bash
poetry install --without dev
```

4. Создайте файл конфигурации .env:
```ini
TELEGRAM_API_KEY="ваш_telegram_bot_token"
DATABASE_URL="sqlite://db.sqlite3"
```

5. Запустите бота:
```bash
bash ./manage.sh compile
poetry run python -m televoicer
```

### Создано с ❤️ для удобного общения в Telegram
🚀 Вопросы и предложения: открывайте Issues в репозитории