"""
1. Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться доступность сетевых узлов.
Аргументом функции является список, в котором каждый сетевой узел должен быть представлен именем хоста или ip-адресом.
В функции необходимо перебирать ip-адреса и проверять их доступность с выводом соответствующего сообщения
(«Узел доступен», «Узел недоступен»). При этом ip-адрес сетевого узла должен создаваться с помощью функции ip_address().
(Внимание! Аргументом сабпроцеса должен быть список, а не строка!!! Для уменьшения времени работы скрипта при проверке
нескольких ip-адресов, решение необходимо выполнить с помощью потоков)
"""

import subprocess
import threading
import platform
from ipaddress import ip_address

result = {'Доступные узлы': '', 'Недоступные узлы': ''}


def check_address(address):
    try:
        ipv4 = ip_address(address)
    except ValueError:
        raise Exception('Некорректный адрес!')
    return ipv4


def ping(ipv4, result, get_list):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    response = subprocess.Popen(['ping', param, '1', '-w', '1', str(ipv4)], stdout=subprocess.PIPE)
    if response.wait() == 0:
        result['Доступные узлы'] += f'{ipv4}\n'
        res = f'{ipv4} - Узел доступен'
        if not get_list:
            print(res)
        return res
    else:
        result['Недоступные узлы'] += f'{ipv4}\n'
        res = f'{str(ipv4)} - Узел недоступен'
        if not get_list:
            print(res)
        return res


def host_ping(host_list, get_list=False):
    threads = []
    for host in host_list:
        try:
            ipv4 = check_address(host)
        except Exception as e:
            print(f'{host} - {e} воспринимается как доменное имя')
            ipv4 = host
        thread = threading.Thread(target=ping, args=(ipv4, result, get_list), daemon=True)
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    if get_list:
        return result


if __name__ == '__main__':
    host_list = ['192.168.0.1', '8.8.8.8', 'yandex.ru', 'google.com',
                  '0.0.0.1', '0.0.0.2', '0.0.0.3', '0.0.0.4', '0.0.0.5',
                  '0.0.0.6', '0.0.0.7', '0.0.0.8', '0.0.0.9', '0.0.1.0']
    host_ping(host_list)
