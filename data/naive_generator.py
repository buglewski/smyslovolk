import sys
import json
from random import randint

#g = open("info.txt", 'r')
#print(g.readline())

try:
    f = open(sys.argv[1], 'r')
    data = json.load(f)
except:
    print("ERROR MEOW!")

ans = ''
for z in data['morphems']:
    ans += z[randint(0, len(z)-1)]

print(ans, end = '')