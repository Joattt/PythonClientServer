# 3. Определить, какие из слов «attribute», «класс», «функция», «type» невозможно записать в байтовом типе. Важно:
# решение должно быть универсальным, т.е. не зависеть от того, какие конкретно слова мы исследуем.

def words_to_bytes_check(word):
    try:
        print(eval(f"b'{word}'"))
    except SyntaxError:
        print(f"'{word}' невозможно записать в байтовом типе")


words_list = ['attribute', 'класс', 'функция', 'type']

for el in words_list:
    words_to_bytes_check(el)
