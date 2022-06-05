import subprocess

process = []
while True:
    action = input('Выберите действие: quit - выйти, start - запустить сервер и клиенты, close - закрыть все окна: ')
    if action == 'quit':
        break
    elif action == 'start':
        process.append(subprocess.Popen('python server.py',
                                        creationflags=subprocess.CREATE_NEW_CONSOLE))
        for i in range(2):
            process.append(subprocess.Popen('python client.py -m send',
                                            creationflags=subprocess.CREATE_NEW_CONSOLE))
        for i in range(2):
            process.append(subprocess.Popen('python client.py -m listen',
                                            creationflags=subprocess.CREATE_NEW_CONSOLE))
    elif action == 'close':
        while process:
            victim = process.pop()
            victim.kill()
