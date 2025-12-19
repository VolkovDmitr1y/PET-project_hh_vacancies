# Определение функций

import pandas as pd
import numpy as np
import requests
import time


# парсинг hh

def get_strict_moscow_vacancies():
    """Собирает только строго московские вакансии"""

    url = "https://api.hh.ru/vacancies"
    all_vacancies = []

    # Более строгие параметры
    params = {
        'professional_role': [10, 12, 13, 15, 24, 25, 34],  # data-роли
        'text': 'sql OR spark OR python OR airflow OR hadoop OR R OR oracle '
                'OR kafka OR pyspark OR pandas OR vertica OR postgresql OR sqlite OR git'
                'OR дата аналитик OR стажер OR дата инженер',
        #'text': 'python OR sql OR spark OR airflow OR etl OR dwh',
        'area': 1,  # Москва
        'per_page': 100,
        # Добавляем дополнительные фильтры
        #'search_field': 'name',  # искать только в названиях
        # 'only_with_salary': True,  # только с зарплатой (опционально)
    }

    print("🔍 Сбор строго московских вакансий...")
    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(f"❌ Ошибка: {response.status_code}")
        return pd.DataFrame()

    data = response.json()
    total_found = data['found']
    total_pages = data['pages']

    print(f"🎯 Найдено вакансий (Москва): {total_found}")
    print(f"📄 Страниц: {total_pages}")

    # Собираем все страницы
    for page in range(total_pages):
        params['page'] = page
        response = requests.get(url, params=params)

        if response.status_code == 200:
            page_data = response.json()

            # Фильтруем сразу при сборе
            moscow_vacancies = [v for v in page_data['items'] if v['area']['name'] == 'Москва']
            all_vacancies.extend(moscow_vacancies)

            print(f"✅ Страница {page + 1}/{total_pages}: {len(moscow_vacancies)} московских вакансий")

            time.sleep(0.1)

    print(f"🎉 Собрано московских вакансий: {len(all_vacancies)}")

    #return pd.DataFrame(all_vacancies)
    return {'items': all_vacancies, 'found': len(all_vacancies)}

# Собираем строго московские вакансии
#vacancy_keys = get_strict_moscow_vacancies()


# Создание дата фрэйма

def parse_hh_vacancies_with_status(data):
    vacancies_list = []

    for vacancy in data['items']:
        # Безопасно получаем вложенные данные
        employer = vacancy.get('employer') or {}
        area = vacancy.get('area') or {}
        experience = vacancy.get('experience') or {}
        employment = vacancy.get('employment') or {}
        salary = vacancy.get('salary') or {}
        metro_stations = vacancy.get('metro_stations', [{}])[0] if vacancy.get('metro_stations') else {}
        
        parsed = {
            'id': vacancy.get('id', ''),
            'name': vacancy.get('name', ''),
            'employer_name': employer.get('name', ''),
            'url': vacancy.get('alternate_url', ''),
            'published_at': vacancy.get('published_at', ''),
            'status': vacancy.get('type', {}).get('name', 'Не указано'),
            
            
            # 🔥 ИНФОРМАЦИЯ О СТАТУСЕ
            'archived': vacancy.get('archived', False),
            'response_url': vacancy.get('response_url', ''),
            'has_test': vacancy.get('has_test', False),
            'response_letter_required': vacancy.get('response_letter_required', False),

            # Описание
            'snippet_requirement': vacancy.get('snippet', {}).get('requirement', ''),
            'snippet_responsibility': vacancy.get('snippet', {}).get('responsibility', ''),

            # Работодатель
            #'employer_name': employer.get('name', ''),
            'employer_trusted': employer.get('trusted', False),

            # Локация
            'area_name': area.get('name', ''),

            # Опыт и занятость
            'experience_name': experience.get('name', ''),
            'employment_name': employment.get('name', ''),

            # Зарплата
            'salary_from': salary.get('from'),
            'salary_to': salary.get('to'),
            'salary_currency': salary.get('currency', ''),
            'salary_gross': salary.get('gross'),

            # Метро
            'metro_station_name': metro_stations.get('station_name', ''),
            'metro_line_name': metro_stations.get('line_name', '')
        }

        vacancies_list.append(parsed)

    vacancy_data = pd.DataFrame(vacancies_list)
    
    from datetime import date, datetime

    # Сегодняшняя дата
    today = date.today()

    vacancy_data['report_date'] = today

    cols = vacancy_data.columns.tolist()
    cols = [cols[-1]] + cols[:-1]

    vacancy_data = vacancy_data[cols]

    return vacancy_data

# Используем
#vacancy_data = parse_hh_vacancies_with_status(vacancy_keys)





# Получение новых вакансий
def link_data_base(data):
    import sqlite3
    
    link = '/mnt/d/Data engineer/SQLite/vacancy_new.db'
    conn = sqlite3.connect(link)

    # ИСПОЛЬЗУЕМ НОВОЕ ИМЯ ТАБЛИЦЫ
    table_name = 'hh_vacancies_new'  

    try:
        # Читаем существующие данные
        vacancy_data_total = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        
        # Если в БД нет новых столбцов, добавляем их с NaN значениями
        for col in data.columns:
            if col not in vacancy_data_total.columns:
                vacancy_data_total[col] = None
                
    except Exception as e:
        print(f"Ошибка при чтении таблицы: {e}")
        # Если таблицы нет, создаем пустой DataFrame с нужной структурой
        vacancy_data_total = pd.DataFrame(columns=data.columns)
    
    # Удаление дубликатов
    vacancy_data_total = vacancy_data_total.drop_duplicates(subset=['id'], keep='last')

    vacancy_current = set(data['id'])
    vacancy_old = set(vacancy_data_total['id'])

    # новые вакансии, которых нет в БД
    vacancy_new = vacancy_current.difference(vacancy_old)

    # датасет с новыми вакансиями
    vacancy_data_new = data[data['id'].isin(vacancy_new)].copy(deep=True)
    
    conn.close()
    return vacancy_data_new

#vacancy_data_new = link_data_base(vacancy_data)


############################################################################

# Отправка сообщений в телеграмм
def telegram_bot(df):
    import requests
    
    BOT_TOKEN = "указать токен"
    CHAT_ID = "id"
    
    # Проверяем, есть ли новые вакансии
    if df.empty:
        print("Нет новых вакансий для отправки")
        
        # Отправляем сообщение что вакансий нет
        message = "📭 На сегодня новых вакансий не найдено"
    else:
        # Создание словаря с новыми вакансиями
        key_vacancy = df.apply(
            lambda row: {
                'title': f"{row['name']}, ({row['employer_name']})",
                'url': row['url']
            }, 
            axis=1
        ).tolist()

        # Формируем сообщение с вакансиями
        message = "💼🔥💲 Новые вакансии:\n\n"
        for vacancy in key_vacancy:
            message += f"• {vacancy['title']}\n{vacancy['url']}\n\n"
        
        if len(message) > 4000:
            message = message[:4000] + "..."
    
    # Отправляем сообщение в любом случае
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': CHAT_ID,
        'text': message
    }
    
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            result_msg = f"✅ Сообщение отправлено: {len(df) if not df.empty else 0} вакансий"
            print(result_msg)
            return result_msg
        else:
            error_msg = f"❌ Ошибка {response.status_code}: {response.text}"
            print(error_msg)
            return error_msg
    except Exception as e:
        error_msg = f"❌ Ошибка подключения: {e}"
        print(error_msg)
        return error_msg

############################################################################




# загрузка вакансий в новую


import sqlite3
import pandas as pd


def chek_data_base_load(data, db_link, table_name='hh_vacancies_new'):

    conn = sqlite3.connect(db_link)

    try:
        # 1. Читаем существующие ID из БД
        existing_ids = pd.read_sql(f"SELECT id FROM {table_name}", conn)['id'].tolist()
        
        # 2. Фильтруем новые данные - оставляем только те, которых нет в БД
        data = data[~data['id'].isin(existing_ids)]
        
        print(f"📊 Всего новых записей: {len(data)}")
        print(f"✅ Уникальных записей: {len(data)}")
        print(f"🚫 Дубликатов: {len(data) - len(data)}")
        
        # 3. Добавляем только уникальные записи
        if not data.empty:
            data.to_sql(table_name, conn, if_exists='append', index=False)
            print(f"💾 Добавлено {len(data)} записей в БД")
        else:
            print("ℹ️ Нет новых данных для добавления")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        conn.close()

#db_link = 'D:/Data engineer/SQLite/vacancy.db'

#chek_data_base_load(data = vacancy_data_new, db_link = db_link, table_name='hh_vacancies')


from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# Ваши функции определены выше в этом же файле
# (предполагается, что get_strict_moscow_vacancies, parse_hh_vacancies_with_status, 
# link_data_base, chek_data_base_load уже определены выше)

# Определение DAG

from airflow.providers.standard.operators.python import PythonOperator  # Новый импорт

# Определение DAG
with DAG(
    'vacancy_dag_telegram',
    start_date=datetime(2024, 11, 18),
    schedule='0 19 * * *',
    catchup=False,
    default_args={
        'owner': 'airflow',
        'retries': 1,
        'retry_delay': timedelta(minutes=5),
    },
    description='Ежедневное обновление данных о вакансиях'
) as dag:
    
    # Задача 1: Парсинг данных
    task_parcing_data = PythonOperator(
        task_id='task_parcing_data',
        python_callable=get_strict_moscow_vacancies
    )

    # Задача 2: Создание DataFrame
    def parse_hh_vacancies_with_status_wrapper(**kwargs):
        ti = kwargs['ti']
        vacancy_keys = ti.xcom_pull(task_ids='task_parcing_data')

        # Вызов вашей оригинальной функции
        return parse_hh_vacancies_with_status(vacancy_keys)

    task_create_Data_Frame = PythonOperator(
        task_id='task_create_Data_Frame',
        python_callable = parse_hh_vacancies_with_status_wrapper
    )

    # Задача 3: Обработка новых вакансий
    def link_data_base_wrapper(**kwargs):

        ti = kwargs['ti']
        vacancy_data = ti.xcom_pull(task_ids='task_create_Data_Frame')
        return link_data_base(vacancy_data)

    task_new_vacancies = PythonOperator(
        task_id='task_new_vacancies',
        python_callable = link_data_base_wrapper
    )


    # Задача 4: Отправка сообщений в Телеграмм
    def send_telegram_message(**kwargs):
        ti = kwargs['ti']
        
        # получение данных из предыдущей задачи
        df =ti.xcom_pull(task_ids = 'task_new_vacancies')

        # Вызов функции
        return telegram_bot(df)
    
    task_send_telegram = PythonOperator(
        task_id = 'task_send_telegram',
        python_callable = send_telegram_message
    )


    # Задача 5: Загрузка в базу данных
    def chek_data_base_load_wrapper(**kwargs):
        ti = kwargs['ti']
        data = ti.xcom_pull(task_ids='task_new_vacancies')
        return chek_data_base_load(data, '/mnt/d/Data engineer/SQLite/vacancy_new.db', 'hh_vacancies_new') # директория с файлом для SQLite

    task_load_data_to_database = PythonOperator(
        task_id='task_load_data_to_database',
        python_callable=chek_data_base_load_wrapper
    )

    # Последовательность выполнения
    task_parcing_data >> task_create_Data_Frame >> task_new_vacancies >> task_send_telegram  >> task_load_data_to_database

