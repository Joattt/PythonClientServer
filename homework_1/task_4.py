# 4. Преобразовать слова «разработка», «администрирование», «protocol», «standard» из строкового представления в
# байтовое и выполнить обратное преобразование (используя методы encode и decode).

str_list = ['разработка', 'администрирование', 'protocol', 'standard']
enc_list = []
dec_list = []
for i in str_list:
    enc_list.append(i.encode('utf-8'))
for i in enc_list:
    dec_list.append(i.decode('utf-8'))
print('\n', str_list, '\n', enc_list, '\n', dec_list)
