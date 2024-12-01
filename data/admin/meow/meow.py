from random import randint

f = open('meow.txt', 'r')

meow = f.read()

print(meow * randint(1, 5))