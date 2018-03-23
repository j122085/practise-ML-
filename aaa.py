import sys
file = open(sys.argv[1], 'r')
content = file.read()
print(content)
file.close()