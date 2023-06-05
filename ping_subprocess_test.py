import subprocess as sp

proc = sp.run(['ping','-n', '1', 'www.bbc.co.uk'])
print(proc.returncode)
print(proc.stdout)
