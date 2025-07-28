import os
import time

while True:
    exit_code = os.system("python3 main.py")
    print(f"[AUTORESTART] Bot finalizado com código {exit_code}. Reiniciando em 5s...")
    time.sleep(5)