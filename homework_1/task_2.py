# 2. Каждое из слов «class», «function», «method» записать в байтовом типе. Сделать это необходимо в автоматическом,
# а не ручном режиме, с помощью добавления литеры b к текстовому значению, (т.е. ни в коем случае не используя методы
# encode, decode или функцию bytes) и определить тип, содержимое и длину соответствующих переменных.

def words_to_bytes(word):
    return eval(f"b'{word}'")


words_list = ['class', 'function', 'method']

for el in words_list:
    print(type(words_to_bytes(el)), words_to_bytes(el), len(words_to_bytes(el)))
