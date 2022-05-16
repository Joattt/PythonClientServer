# 6. Создать текстовый файл test_file.txt, заполнить его тремя строками: «сетевое программирование», «сокет»,
# «декоратор». Далее забыть о том, что мы сами только что создали этот файл и исходить из того, что перед нами файл в
# неизвестной кодировке. Задача: открыть этот файл БЕЗ ОШИБОК вне зависимости от того, в какой кодировке он был создан.

from chardet import detect

f = open('test_file.txt', 'w', encoding='utf-8')
f.write('сетевое программирование\nсокет\nдекоратор')
f.close()

with open('test_file.txt', 'rb') as f:
    content = f.read()
encoding = detect(content)['encoding']

with open('test_file.txt', encoding=encoding) as f_n:
    for el in f_n:
        print(el, end='')
