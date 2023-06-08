import re

result = re.findall('(.*)Average = ([0-9]*)ms', "Approximate round trip times in milli-seconds: \n Minimum = 2233ms, Maximum = 27ms, Average = 27ms")
print(result[0][-1])