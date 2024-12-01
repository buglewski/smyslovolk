from random import randint
import sys

n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
a = int(sys.argv[2]) if len(sys.argv) > 2 else 1
b = int(sys.argv[3]) if len(sys.argv) > 3 else a+1

for i in range(n):
    print(randint(a,b), end = ' ')