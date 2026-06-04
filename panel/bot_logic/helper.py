import random
import string
import time

def generate_unique_credentials():
    """
    Generates dynamic usernames, passwords, and default emails for registration.
    """
    timestamp = str(int(time.time()))
    username = f"user_{timestamp}_{random.randint(1000, 9999)}"
    # Generate strong random alphanumeric password
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    # Default placeholder; AccountCreator overrides this with a real temp-mail from 1secmail
    email = f"{username}@tempmail.dev"
    return username, password, email
