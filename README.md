# ScheduleBot
Реализация чат-бота в рамках выполнения проекта второго отборочного этапа в Сириус.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.x-green.svg)](https://docs.aiogram.dev/en/v3.21.0/)

Бот помогает управлять расписанием занятий, добавлять события и получать напоминания.


## Возможности
- Просмотр расписаний на сегодня(`/today`), завтра(`/tomorrow`), неделю(`/week`)
- Добавление событий командой `/add`
- Умные напоминания за один час до начала
- Простое управление через интерактивное меню


## Установка
- Python 3.9+
- Аккаунт Telegram и токен бота от [@BotFather](https://t.me/botfather)


### 1. Установка Python
#### Windows
1. Скачайте установщик с [официального сайта](https://www.python.org/downloads/)
2. Запустите установщик и:
   - Отметьте "Add Python to PATH"
   - Выберите "Custom installation"
   - Установите все компоненты (особенно pip)

#### Linux/macOS
```bash
# Проверьте версию Python 
python --version

# Если не установлен:
# (Ubuntu/Debian)
sudo apt update
sudo apt install python3 python3-pip python3-venv

# macOS 
brew install python
```
### 2. Установка Git

#### Windows
1. Скачайте установщик [официальный сайт Git](https://git-scm.com/downloads)
2. Запустите установщик
3. Проверка установки 
```bash
git --version
```

#### Linux (Ubuntu/Debian)
1. Обновите пакеты:
```bash
sudo apt update
```

2. Установите Git:
```bash
sudo apt install git
```

3. Проверка установки:
```bash
git --version
```

#### macOS
```bash
brew install git
```

### 3. Клонирование репозитория 
```bash
git clone https://github.com/flitchendly/ScheduleBot.git
cd ScheduleBot
```

### 4. Установка окружения
```bash
python -m venv venv 

# Linux/macOS
source venv/bin/activate
```

### 5. Установка зависимостей
```bash
pip install aiogram
```

### 6. Запуск бота
```bash
python chat_bot.py
```

## Пример использования
### Добавление события
```bash
/add Олимпиада 2025-07-14 10:00
```
### Просмотр расписания
```bash
/today
```
Пример вывода расписания:
![today](https://github.com/flitchendly/ScheduleBot/blob/main/examples/command_today.png)

Пример получения уведомления за час до события:
![event](https://github.com/flitchendly/ScheduleBot/blob/main/examples/event.png)
