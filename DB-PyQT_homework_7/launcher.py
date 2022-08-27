import subprocess


def main():
    process = []
    while True:
        action = input(
            'Выберите действие: quit - выход , start - запустить сервер, '
            'clients - запустить клиенты close - закрыть все окна:')
        if action == 'quit':
            break
        elif action == 'start':
            process.append(
                subprocess.Popen(
                    'python server_script.py.py',
                    creationflags=subprocess.CREATE_NEW_CONSOLE))
        elif action == 'clients':
            print('Убедитесь, что на сервере зарегистрировано необходимо количество клиентов с паролем 123456.')
            print('Первый запуск может быть достаточно долгим из-за генерации ключей!')
            clients_count = int(
                input('Введите количество тестовых клиентов для запуска: '))
            # Запускаем клиентов:
            for i in range(clients_count):
                process.append(
                    subprocess.Popen(
                        f'python client.py -n test{i + 1} -p 123456',
                        creationflags=subprocess.CREATE_NEW_CONSOLE))
        elif action == 'close':
            while process:
                process.pop().kill()


if __name__ == '__main__':
    main()
