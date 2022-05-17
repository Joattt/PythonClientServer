"""
1. Задание на закрепление знаний по модулю CSV. Написать скрипт, осуществляющий выборку определенных данных из
файлов info_1.txt, info_2.txt, info_3.txt и формирующий новый «отчетный» файл в формате CSV. Для этого:
Создать функцию get_data(), в которой в цикле осуществляется перебор файлов с данными, их открытие и считывание данных.
В этой функции из считанных данных необходимо с помощью регулярных выражений извлечь значения параметров
«Изготовитель системы», «Название ОС», «Код продукта», «Тип системы». Значения каждого параметра поместить в
соответствующий список. Должно получиться четыре списка — например, os_prod_list, os_name_list, os_code_list,
os_type_list. В этой же функции создать главный список для хранения данных отчета — например, main_data — и
поместить в него названия столбцов отчета в виде списка: «Изготовитель системы», «Название ОС», «Код продукта»,
«Тип системы». Значения для этих столбцов также оформить в виде списка и поместить в файл main_data (также для
каждого файла);
Создать функцию write_to_csv(), в которую передавать ссылку на CSV-файл. В этой функции реализовать получение данных
через вызов функции get_data(), а также сохранение подготовленных данных в соответствующий CSV-файл;
Проверить работу программы через вызов функции write_to_csv().
"""

import re
import csv
from chardet import detect


def get_data(categories, files):
    os_prod_list = []
    os_name_list = []
    os_code_list = []
    os_type_list = []
    for file in files:
        with open(file, 'rb') as f_n:
            content = f_n.read()
        encoding = detect(content)['encoding']
        with open(file, encoding=encoding) as f:
            text = f.read()
        re_code = fr'({categories[0]}:[ ]+)(\b[-\w ]+)'
        match = re.search(re_code, text)
        os_prod_list.append(match[2])
        re_code = fr'({categories[1]}:[ ]+)(\b[-\w ]+)'
        match = re.search(re_code, text)
        os_name_list.append(match[2])
        re_code = fr'({categories[2]}:[ ]+)(\b[-\w ]+)'
        match = re.search(re_code, text)
        os_code_list.append(match[2])
        re_code = fr'({categories[3]}:[ ]+)(\b[-\w ]+)'
        match = re.search(re_code, text)
        os_type_list.append(match[2])
    matrix = [os_prod_list, os_name_list, os_code_list, os_type_list]
    trans_matrix = [[matrix[i][j] for i in range(len(matrix))] for j in range(len(matrix[0]))]
    main_data = [categories] + trans_matrix
    return main_data


def write_to_csv(data):
    with open('data_file.csv', 'w', encoding='utf-8') as f:
        f_writer = csv.writer(f)
        f_writer.writerows(data)


os_prod = 'Изготовитель системы'
os_name = 'Название ОС'
os_code = 'Код продукта'
os_type = 'Тип системы'
categories = [os_prod, os_name, os_code, os_type]

file_1 = 'info_1.txt'
file_2 = 'info_2.txt'
file_3 = 'info_3.txt'
files = [file_1, file_2, file_3]

data = get_data(categories, files)
write_to_csv(data)
