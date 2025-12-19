# 📊 Daily HH.ru Vacancy Parser & Telegram Notifier

**Автоматический сбор IT-вакансий с HeadHunter и уведомления в Telegram**

[![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)](https://python.org)
[![Airflow](https://img.shields.io/badge/Apache%20Airflow-2.5+-darkcyan?logo=apacheairflow&logoColor=white)](https://airflow.apache.org)
[![SQLite](https://img.shields.io/badge/SQLite-3.40+-teal?logo=sqlite&logoColor=white)](https://sqlite.org)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram)](https://core.telegram.org/bots)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![HH.ru API](https://img.shields.io/badge/HH.ru-API-orange)](https://api.hh.ru/)

## 🎯 О проекте

Ежедневный автоматизированный сборщик IT-вакансий из Москвы с платформы HeadHunter с интеллектуальной фильтрацией, хранением в SQLite и мгновенными уведомлениями в Telegram о новых предложениях.

### ✨ Основные возможности

- **🤖 Ежедневный автоматический парсинг** – DAG в Airflow запускается каждый день в 19:00
- **🎯 Смарт-фильтрация вакансий** – Только строго московские вакансии по data-специальностям
- **💾 Умное хранение SQLite** – Автоматическое обнаружение и исключение дубликатов
- **📱 Telegram-уведомления** – Мгновенные оповещения о новых вакансиях
- **📊 Структурированные данные** – 20+ параметров по каждой вакансии для анализа
- **⚡ Высокая производительность** – Параллельная обработка и оптимизированные запросы

## 🏗️ Архитектура проекта

```mermaid
graph TB
    A[🕐 Airflow DAG<br>Ежедневно в 19:00] --> B[🌐 HH.ru API<br>Парсинг вакансий]
    B --> C[🎯 Фильтрация<br>Москва + Data-роли]
    C --> D[🔄 Обработка<br>Парсинг JSON → DataFrame]
    D --> E[🔍 Сравнение<br>Поиск новых вакансий]
    E --> F{Есть новые?}
    F -->|Да| G[📱 Telegram Bot<br>Отправка уведомлений]
    F -->|Нет| H[📭 Сообщение<br>"Нет новых вакансий"]
    G --> I[💾 SQLite DB<br>Сохранение новых записей]
    H --> I



📁 Структура проекта



hh_vacancy_parser/
├── dags/
│   └── vacancy_dag_telegram.py    # Основной DAG Airflow
├── src/
│   ├── hh_parser.py              # Функции парсинга HH.ru
│   ├── database_handler.py       # Работа с SQLite
│   └── telegram_notifier.py      # Отправка в Telegram
├── data/
│   └── vacancy_new.db            # SQLite база данных
├── config/
│   ├── settings.py               # Конфигурационные параметры
│   └── queries.py                # SQL-запросы
├── tests/
│   ├── test_parser.py
│   └── test_database.py
├── requirements.txt              # Зависимости Python
├── README.md                     # Эта документация
└── .env.example                  # Пример переменных окружения











