import json
import csv

f = open("large3.js", "w")
f.write('let WORDS = [\n')
with open('egg.csv', 'r') as file:
    reader = csv.reader(file)
    print
    for row in reader:
        f.write('    [\"'+row[0]+'\",\"'+row[1]+'\"],\n')
f.write('];')
f.close()