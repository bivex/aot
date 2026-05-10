import requests
import time
import subprocess
import os

text = """6. ДІЯ ДОГОВОРУ

 

6.1. Цей Договір вважається укладеним і набирає чинності з моменту його підписання Сторонами та скріплення печатками Сторін.

6.2. Строк цього Договору починає свій перебіг у момент, визначений у п. 6.1 цього Договору та закінчується 31.12.2015 рік. Відповідно до ч.3. ст.631 ЦК України сторони домовилися, що умови цього договору  застосовуються до відносин між ними , які виникли з 01.01.15р.( заповнювати при необхідності)

6.3. Закінчення строку цього Договору не звільняє Сторони від відповідальності за його порушення, яке мало місце під час дії цього Договору.

6.4.Якщо до 31.12.15 р. певна сума договору залишилася невикористаною, договір вважається таким, що втратив чинність без підписання додаткової угоди.

6.5. Зміни до цього Договору набирають чинності з моменту належного оформлення Сторонами відповідної додаткової угоди до цього Договору, якщо інше не встановлено у самій додатковій угоді, цьому Договорі або у чинному законодавстві України.

6.6. Якщо інше прямо не передбачено цим Договором або чинним законодавством України, цей Договір може бути розірваний тільки за домовленістю Сторін, яка оформлюється додатковою угодою до цього Договору.

6.7. Цей Договір вважається розірваним з моменту належного оформлення Сторонами відповідної додаткової угоди до цього Договору, якщо інше не встановлено у самій додатковій угоді, цьому Договорі або у чинному законодавстві України."""

url = "http://localhost:8089/?dummy=1&action=syntax&langua=Ukrainian"

def restart_daemon():
    subprocess.run(["pkill", "-9", "-f", "SynanDaemon"], stderr=subprocess.DEVNULL)
    time.sleep(1)
    env = os.environ.copy()
    env["RML"] = "/Volumes/External/Code/aot"
    subprocess.Popen(["/Volumes/External/Code/aot/build_fast/Source/www/SynanDaemon/SynanDaemon", "--host", "0.0.0.0", "--port", "8089"], 
                     env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)

print("\nSending line by line with restarts...")
for i, line in enumerate(text.split('\n')):
    line = line.strip()
    if not line: continue
    print(f"[{i}] Testing line: {line[:50]}...")
    restart_daemon()
    try:
        response = requests.post(url, data=line.encode('utf-8'), timeout=10)
        print(f"  Result: {response.status_code}")
    except Exception as e:
        print(f"  !!! CRASHED on line: {line}")
        # break
