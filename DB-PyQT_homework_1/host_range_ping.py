"""
2. Написать функцию host_range_ping() (возможности которой основаны на функции из примера 1) для перебора ip-адресов из
заданного диапазона. Меняться должен только последний октет каждого адреса. По результатам проверки должно выводиться
соответствующее сообщение.
"""

from host_ping import host_ping, check_address


def host_range_ping(get_list=False):
    while True:
        start_address = input('Введите исходный адрес: ')
        try:
            ipv4_start = check_address(start_address)
            last_octet = int(start_address.split('.')[3])
            break
        except Exception as e:
            print(e)
    while True:
        address_quantity = input('Введите количество проверяемых адресов: ')
        if (last_octet + int(address_quantity)) > 255:
            print('Превышено максимальное число хостов.')
        else:
            break
    host_list = []
    [host_list.append(str(ipv4_start + x)) for x in range(int(address_quantity))]
    if not get_list:
        host_ping(host_list)
    else:
        return host_ping(host_list, True)


if __name__ == '__main__':
    host_range_ping()
