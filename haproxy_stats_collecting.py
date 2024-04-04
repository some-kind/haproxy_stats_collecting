import requests  # pip3 install requests
import time
import sys
from openpyxl import Workbook  # pip3 install openpyxl
from openpyxl import load_workbook
from datetime import datetime, timedelta


def fetch_data(url):
    """
    Получение данных
    :param url: URL строки
    :return: текст запроса при успехе и ничего при ошибке
    """
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Ошибка: Не удалось получить данные. Status code: {response.status_code}")
    except requests.exceptions.RequestException as error:
        print(f"Ошибка: {error}")
    return None


def parse_data(data):
    """
    Парсинг данных haproxy
    :param data: данные из csv haproxy в виде кучи строк
    :return: список данных парами
    """
    parsed_data = []
    lines = data.split('\n')  # сплитим на строки
    for line in lines:
        if line.startswith("front::Thin_Client:88"):  # ориентир интересующих нас данных (фронтент ТК)
            parts = line.split(',')  # сплитим по запятым на элементы
            if len(parts) >= 34 and len(parts) >= 17:  # доп. проверка, чтобы не прочитать корявую строку
                servers = 8  # количество серверов
                parsed_data.append([int(parts[33]),
                                    int(parts[-17]),
                                    round(int(parts[33])/servers, 2),
                                    round(int(parts[-17])/servers, 2)])  # сохраняем результаты
                # rate (33 элемент) - количество сессий в секунду
                # req_rate (-17 элемент) - количество запросов в секунду
                # делим на кол-во серверов, потому что собираем данные общие по балансеру,
                # а нам нужно среднее кол-во на сервере
            else:
                print("Ошибка: Неправлиьный формат данных (строка не соответствует затребованным данных).")
    return parsed_data


def write_to_excel(data):
    """
    Запись данных в таблицу excel
    :param data: список распарсенных данных
    :return:
    """
    try:
        wb = load_workbook("haproxy_stats.xlsx")  # открываем таблицу
        ws = wb.active
    except FileNotFoundError:   # если её ещё нет - создаём
        wb = Workbook()
        ws = wb.active
        # Заголовки столбцов
        ws.append(['Time', 'Sessions/sec', 'Requests/sec', 'Sessions/sec 1 server', 'Requests/sec 1 server'])

    for row in data:
        row.insert(0, datetime.now().strftime("%H:%M:%S"))  # Вставка времени в начало каждой строки
        ws.append(row)

    wb.save("haproxy_stats.xlsx")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Формат команды: python3 haproxy_collecting_stats.py <время_сбора_данных_в_минутах> <время_шага_в_секундах>")
        sys.exit(1)

    duration_in_minutes = int(sys.argv[1])  # параметр времени работы
    # duration_in_minutes = 10  # тест

    sleep_time = int(sys.argv[2])  # параметр времени задержки (шага между считываниями)

    end_time = datetime.now() + timedelta(minutes=duration_in_minutes)  # расчёт времени завершения скрипта

    # адрес csv статистики haproxy
    url = "http://10.10.130.103:81/stats;csv"

    while datetime.now() < end_time:
        data = fetch_data(url)  # получаем данные

        # data = input()  # тест

        if data:
            parsed_data = parse_data(data)  # парсинг данных
            write_to_excel(parsed_data)  # запись в таблицу
            print(f"Данные записаны ... {datetime.now().strftime('%H:%M:%S')}")
        time.sleep(sleep_time)

    print(" - - - Сбор данных завершён - - - ")

