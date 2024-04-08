#from cyni import cyni

#if __name__ == '__main__':
#    cyni()

import subprocess
try:
    subprocess.run(["pip", "install", "--upgrade", "mysql-connector-python"])
    print("mysql-connector-python upgraded successfully.")
except subprocess.CalledProcessError as e:
    print(f"Error: {e}")
