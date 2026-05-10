import requests
import time
import subprocess
import os

line_6_2 = "6.2. Строк цього Договору починає свій перебіг у момент, визначений у п. 6.1 цього Договору та закінчується 31.12.2015 рік. Відповідно до ч.3. ст.631 ЦК України сторони домовилися, що умови цього договору  застосовуються до відносин між ними , які виникли з 01.01.15р.( заповнювати при необхідності)"

url = "http://localhost:8089/?dummy=1&action=syntax&langua=Ukrainian"

def restart_daemon():
    subprocess.run(["pkill", "-9", "-f", "SynanDaemon"], stderr=subprocess.DEVNULL)
    time.sleep(1)
    env = os.environ.copy()
    env["RML"] = "/Volumes/External/Code/aot"
    subprocess.Popen(["/Volumes/External/Code/aot/build_fast/Source/www/SynanDaemon/SynanDaemon", "--host", "0.0.0.0", "--port", "8089"], 
                     env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)

parts = [
    "6.2. Строк цього Договору починає свій перебіг у момент, визначений у п. 6.1 цього Договору та закінчується 31.12.2015 рік.",
    "Відповідно до ч.3. ст.631 ЦК України сторони домовилися,",
    "що умови цього договору  застосовуються до відносин між ними , які виникли з 01.01.15р.",
    "( заповнювати при необхідності)"
]

print("\nTesting parts of line 6.2...")
for i, part in enumerate(parts):
    print(f"[{i}] Testing: {part[:50]}...")
    restart_daemon()
    try:
        response = requests.post(url, data=part.encode('utf-8'), timeout=10)
        print(f"  Result: {response.status_code}")
    except Exception as e:
        print(f"  !!! CRASHED on part: {part}")
