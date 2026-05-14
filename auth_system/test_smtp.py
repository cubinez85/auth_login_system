# /home/cubinez85/auth_login_system/auth_system/test_smtp.py
#!/usr/bin/env python3
"""
Тест подключения к почтовому серверу
"""
import smtplib
import sys
import os

# Добавляем проект в path
sys.path.insert(0, '/home/cubinez85/auth_login_system/auth_system')

from dotenv import load_dotenv
load_dotenv('/home/cubinez85/auth_login_system/auth_system/.env')

def test_smtp_connection():
    """Проверка подключения к SMTP серверу"""
    
    server = os.environ.get('MAIL_SERVER', 'localhost')
    port = int(os.environ.get('MAIL_PORT', 25))
    use_tls = os.environ.get('MAIL_USE_TLS', 'false').lower() in ('true', '1', 'yes')
    use_ssl = os.environ.get('MAIL_USE_SSL', 'false').lower() in ('true', '1', 'yes')
    username = os.environ.get('MAIL_USERNAME')
    password = os.environ.get('MAIL_PASSWORD')
    
    print(f"🔌 Testing SMTP connection to {server}:{port}")
    print(f"   TLS: {use_tls}, SSL: {use_ssl}")
    print(f"   Auth: {'Yes' if username else 'No'}")
    print()
    
    try:
        if use_ssl:
            conn = smtplib.SMTP_SSL(server, port, timeout=10)
            print(f"✅ Connected via SMTP_SSL")
        else:
            conn = smtplib.SMTP(server, port, timeout=10)
            print(f"✅ Connected via SMTP")
            
            if use_tls:
                conn.starttls()
                print(f"✅ STARTTLS enabled")
        
        # Приветствие сервера
        code, msg = conn.ehlo() if not use_ssl else conn.ehlo()
        print(f"📡 Server response: {code} {msg.decode() if isinstance(msg, bytes) else msg}")
        
        # Аутентификация если есть учётные данные
        if username and password:
            conn.login(username, password)
            print(f"✅ Authenticated as {username}")
        
        conn.quit()
        print(f"\n🎉 SMTP connection test PASSED!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("   Check MAIL_USERNAME and MAIL_PASSWORD")
        return False
    except smtplib.SMTPConnectError as e:
        print(f"❌ Connection failed: {e}")
        print("   Check firewall, server address, and that SMTP is running")
        return False
    except ConnectionRefusedError:
        print(f"❌ Connection refused on port {port}")
        print("   Check firewall rules: sudo ufw allow 25/tcp (или ваш порт)")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        return False


if __name__ == '__main__':
    success = test_smtp_connection()
    sys.exit(0 if success else 1)
