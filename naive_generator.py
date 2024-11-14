import sys
import json
from random import randint

f = open(sys.argv[1], 'r')
data = json.load(f)

ans = ''
for z in data['morphems']:
    ans += z[randint(0, len(z)-1)]

print(ans, end = '')