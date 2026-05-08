import threading
import subprocess
import os

def run_script(script_name):
    subprocess.run(["python", script_name])

cloudflared_script_path = 'host/cloudflared/cloudflared'

if __name__ == "__main__":
    scripts = ["host/app.py", "host/admin_bot.py", "skin.py"]

    threads = []

    for script in scripts:
        t = threading.Thread(target=run_script, args=(script,))
        t.start()
        subprocess.Popen([cloudflared_script_path, 'tunnel', '--config', 'host/cloudflared/config.yml', 'run', 'host-tunnel'])
        threads.append(t)

    for t in threads:
        t.join()
        
import time
while True:
    time.sleep(60)