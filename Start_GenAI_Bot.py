from cryptography.fernet import Fernet

# Load the key
with open('key.key', 'rb') as file:
    key = file.read()

# Create a Fernet cipher object
cipher = Fernet(key)

# Read the encrypted content from encrypted_app.py
with open('GenAIBot.py', 'rb') as file:
    encrypted_data = file.read()

# Decrypt the content
decrypted_data = cipher.decrypt(encrypted_data)
exec(decrypted_data)
