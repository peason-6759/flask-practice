import os
import sys

for i in range(10):
    print(i)

currentFile = os.path.abspath(__file__)
print(currentFile)  
print(sys.executable, [sys.executable] + sys.argv)
os.execv(sys.executable, [sys.executable] + sys.argv)

