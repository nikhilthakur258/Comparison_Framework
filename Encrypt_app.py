from cryptography.fernet import Fernet

# Generate a key
key = Fernet.generate_key()

# Create a Fernet cipher object
cipher = Fernet(key)

# Read the content of app.py
with open('app_temp.py', 'rb') as file:
    plaintext = file.read()

# Encrypt the content
encrypted_data = cipher.encrypt(plaintext)

# Write the encrypted content to encrypted_app.py
with open('GenAIBot.py', 'wb') as file:
    file.write(encrypted_data)

# Save the key to a file
with open('key.key', 'wb') as file:
    file.write(key)
