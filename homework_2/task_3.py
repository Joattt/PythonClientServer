"""
3. Задание на закрепление знаний по модулю yaml. Написать скрипт, автоматизирующий сохранение данных в файле
YAML-формата. Для этого:
Подготовить данные для записи в виде словаря, в котором первому ключу соответствует список, второму — целое число,
третьему — вложенный словарь, где значение каждого ключа — это целое число с юникод-символом, отсутствующим в кодировке
ASCII (например, €);
Реализовать сохранение данных в файл формата YAML — например, в файл file.yaml. При этом обеспечить стилизацию файла
с помощью параметра default_flow_style, а также установить возможность работы с юникодом: allow_unicode = True;
Реализовать считывание данных из созданного файла и проверить, совпадают ли они с исходными.
"""

import yaml


def save_to_yaml(data):
    with open('file.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


data_to_yaml = {
    '1€': ['foo', 'bar', 'baz'],
    '2€': 25,
    '3€': {1: {2: 'два', 3: 'три'}}
}
save_to_yaml(data_to_yaml)

with open('file.yaml', encoding='utf-8') as f:
    new_data = yaml.load(f, Loader=yaml.FullLoader)

if data_to_yaml == new_data:
    print('Данные совпадают с исходными.')
