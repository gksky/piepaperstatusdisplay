


import requests
import json
import sys
import os
from time import sleep
from PIL import Image, ImageDraw, ImageFont
#sys.path.append('lib')  # Укажите путь к библиотеке e-Paper

import epd2in13_V4  # Импортируем драйвер дисплея
import subprocess
import logging

# Параметры экрана Waveshare (например, 250x122 для 2.13-дюймового экрана)
EPD_WIDTH = 250
EPD_HEIGHT = 122

def get_wifi_info():
    try:
        # Выполняем команду nmcli для получения информации о текущем Wi-Fi
        result = subprocess.run(['nmcli', '-t', '-f', 'IP4', 'dev', 'show', 'wlan0'], 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE, 
                                text=True)

        if result.returncode != 0:
            print(f"Error executing nmcli: {result.stderr}")
            return None
        wifi_info = None
        # Разбираем вывод
        wifi_info_list = result.stdout.strip().split('\n')
        connected_networks = []
        
        for line in wifi_info_list:
            fields = line.split(':')
            if fields[0].startswith("IP4.ADDRESS"):
                wifi_info = fields[1]

        return 'IP: ' + wifi_info if wifi_info else "Not connected to any Wi-Fi network."

    except Exception as e:
        print(f"An error occurred: {e}")
        return wifi_info

def get_cpu_usage():
    try:
        result = subprocess.run('grep "cpu " /proc/stat', capture_output=True, shell=True, text=True)
        r1 = result.stdout.split()
        u1 = int(r1[1]) + int(r1[3])
        t1 = int(r1[1]) + int(r1[3]) + int(r1[4])
        sleep(1)
        result = subprocess.run('grep "cpu " /proc/stat', capture_output=True, shell=True, text=True)
        r2 = result.stdout.split()
        u2 = int(r2[1]) + int(r2[3])
        t2 = int(r2[1]) + int(r2[3]) + int(r2[4])
        cpu_usage = str(round((u2 - u1) * 100 / (t2 - t1), 1)) + '%'

        return cpu_usage

    except Exception as e:
        print(f"An error occurred: {e}")

def get_cpu_temp():
    try:
        result = subprocess.run('sensors -j', capture_output=True, shell=True, text=True)
        data = json.loads(result.stdout)
        cpu_temp = round(data['cpu_thermal-virtual-0']['temp1']['temp1_input'], 1)

        return str(cpu_temp) + '°C'

    except Exception as e:
        print(f"An error occurred: {e}")

def get_mem_info():
    try:
        # Выполняем команду nmcli для получения информации о текущем Wi-Fi
        result = subprocess.run(['free -b'], 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE, 
                                shell=True,
                                text=True)

        if result.returncode != 0:
            print(f"Error executing nmcli: {result.stderr}")
            return None
        mem_info = None
        # Разбираем вывод
        mem_info_list = result.stdout.strip().split('\n')
        
        for line in mem_info_list:
            field = line.split()
            if field[0] == 'Mem:':
                mem = str(round(int(field[2]) / int(field[1]) * 100)) + '%'
            if field[0] == 'Swap:':
                swap = str(round(int(field[2]) / int(field[1]) * 100)) + '%'

        return (mem, swap,)

    except Exception as e:
        print(f"An error occurred: {e}")

# Функция для переноса текста по словам
def wrap_text(text, font, max_width):
    """Разбивает текст на строки, чтобы они умещались в указанную ширину"""
    lines = []
    words = text.split(' ')
    current_line = []

    for word in words:
        current_line.append(word)
        # Создаем временную строку с добавленным словом и проверяем её ширину
        temp_line = ' '.join(current_line)
        width, _ = font.getsize(temp_line)
        
        if width > max_width:
            # Если строка выходит за пределы экрана, переносим её
            current_line.pop()  # Убираем последнее слово
            lines.append(' '.join(current_line))  # Добавляем строку в список
            current_line = [word]  # Начинаем новую строку с текущего слова

    # Добавляем оставшиеся слова
    if current_line:
        lines.append(' '.join(current_line))

    return lines

def get_random_quote():
    try:
        ## выполнение запроса get
        response = requests.get("http://api.forismatic.com/api/1.0/?method=getQuote&format=json&lang=ru")
        if response.status_code == 200:
            ## извлечение основных данных
            json_data = response.json()
            return (json_data['quoteText'], json_data['quoteAuthor'],)

        else:
            print("Ошибка при получении цитаты")
    except Exception as e:
        print("Что-то пошло не так! Попробуй еще раз!")
        return (e, e,)

logging.basicConfig(level=logging.DEBUG)
quote_steps = 0
# Инициализируем дисплей
epd = epd2in13_V4.EPD()
epd.init()

# Очищаем дисплей
epd.Clear(0xFF)
# Загружаем шрифт
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
quote_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12)
#firstTime = True
ip_image = Image.new('1', (epd.height, epd.width), 255)
ip_draw = ImageDraw.Draw(ip_image)
epd.displayPartBaseImage(epd.getbuffer(ip_image))
while (True):
    wifi_info = get_wifi_info()
    if wifi_info:
        logging.info(wifi_info)
    ip_draw.rectangle((0, 0, 250, 122), fill = 255)
    ip_draw.text((0, 0), wifi_info, font = font, fill = 0)
    #epd.displayPartial(epd.getbuffer(ip_image))

    cpu_usage = get_cpu_usage()
    logging.info(cpu_usage)
    ip_draw.text((0, 20), 'CPU: ' + cpu_usage, font = font, fill = 0)

    cpu_temp = get_cpu_temp()
    logging.info(cpu_temp)
    ip_draw.text((167, 20), 't: ' + cpu_temp, font = font, fill = 0)

    mem_info = get_mem_info()
    logging.info(mem_info)
    ip_draw.text((0, 40), 'RAM: ' + mem_info[0], font = font, fill = 0)
    ip_draw.text((125, 40), 'Swap: ' + mem_info[1], font = font, fill = 0)

    if quote_steps == 0:
        quote_data = get_random_quote()
        logging.info(quote_data)
        quote_steps = 6
    quote_steps -= 1

    # image = Image.new('2', (EPD_WIDTH, EPD_HEIGHT), 255)  # Белый фон (255)
    # draw = ImageDraw.Draw(image)

    # Получаем список строк с учётом переноса
    wrapped_text = wrap_text(quote_data[0], quote_font, EPD_WIDTH)

    # Рисуем текст построчно
    y_offset = 0
    line_height = quote_font.getsize('A')[1]  # Высота строки
    for line in wrapped_text:
        ip_draw.text((2, y_offset + 60), line, font=quote_font, fill=0)  # fill=0 - черный текст
        y_offset += line_height

    # ip_draw.text((0, 65), quote_data[0], font = quote_font, fill = 0)
    ip_draw.text((0, EPD_HEIGHT - 12), quote_data[1], font = quote_font, fill = 0)

    epd.displayPartial(epd.getbuffer(ip_image))

# Ожидание перед выключением
    sleep(10)

# Выключаем дисплей и очищаем его
epd.sleep()
