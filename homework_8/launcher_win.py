import subprocess

process = []
while True:
    action = input('Выберите действие: quit - выйти, start - запустить сервер и клиенты, close - закрыть все окна: ')
    if action == 'quit':
        break
    elif action == 'start':
        process.append(subprocess.Popen('python server.py', creationflags=subprocess.CREATE_NEW_CONSOLE))
        process.append(subprocess.Popen('python client.py -n User1', creationflags=subprocess.CREATE_NEW_CONSOLE))
        process.append(subprocess.Popen('python client.py -n User2', creationflags=subprocess.CREATE_NEW_CONSOLE))
        process.append(subprocess.Popen('python client.py -n User3', creationflags=subprocess.CREATE_NEW_CONSOLE))
    elif action == 'close':
        while process:
            victim = process.pop()
            victim.kill()

