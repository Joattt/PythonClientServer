# 5. Написать код, который выполняет пинг веб-ресурсов yandex.ru, youtube.com и преобразовывает результат из
# байтовового типа данных в строковый без ошибок для любой кодировки операционной системы.

import chardet
import subprocess
import platform


def ping_to_str(website, pings):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    args = ['ping', param, pings, website]
    process = subprocess.Popen(args, stdout=subprocess.PIPE)
    for line in process.stdout:
        result = chardet.detect(line)
        line = line.decode(result['encoding']).encode('utf-8')
        print(line.decode('utf-8'))


ping_to_str('yandex.ru', '2')
ping_to_str('youtube.com', '3')
