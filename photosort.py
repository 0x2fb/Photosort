import os

for (path, dirs, files) in os.walk(os.getcwd()):
    for f in files:
        print(f"{path}\\{f}")
