import base64
import hashlib
import urllib

from Crypto.Cipher import AES
from Crypto.Hash import MD5
from Crypto.Hash import SHA256
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes


def md5_hash_file(filename):
    """
    Compute the MD5 hash of a file.

    Args:
    - filename (str): Path to the file.

    Returns:
    - str: MD5 hash of the file.
    """
    hasher = hashlib.md5()

    with open(filename, "rb") as f:
        # Read and update hash in chunks to avoid using too much memory
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def evpkdf(password, key_size, iv_size, salt):
    target_key_size = key_size + iv_size
    derived_bytes = b""
    block = None
    while len(derived_bytes) < target_key_size:
        hasher = MD5.new()
        if block:
            hasher.update(block)
        hasher.update(password)
        hasher.update(salt)
        block = hasher.digest()
        derived_bytes += block
    return derived_bytes[:key_size], derived_bytes[key_size : key_size + iv_size]


def aes_encrypt(data, password):
    key_size = 32  # 256 bits for AES-256
    iv_size = 16  # 128 bits for the AES block size
    salt = get_random_bytes(8)
    #
    key, iv = evpkdf(password.encode("utf-8"), key_size, iv_size, salt)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_content = cipher.encrypt(pad(data, AES.block_size))
    #
    # Concatenate salt, iv, and encrypted content
    combined = b"Salted__" + salt + encrypted_content
    return combined


def aes_decrypt(encrypted_content, password):
    # Extract the salt from the encrypted content
    salt = encrypted_content[8:16]
    encrypted_data = encrypted_content[16:]
    #
    key_size = 32  # 256 bits for AES-256
    iv_size = 16  # 128 bits for the AES block size
    #
    # Derive the key and IV using the evpkdf function
    key, iv = evpkdf(password.encode("utf-8"), key_size, iv_size, salt)
    #
    # Decrypt the content
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_content = unpad(cipher.decrypt(encrypted_data), AES.block_size)
    #
    return decrypted_content


def encrypt_pdf_content(pdf_content, password):
    combined = aes_encrypt(data=pdf_content, password=password)
    return combined


def hash_email(email):
    """Hash the email using SHA256 and return the hexadecimal representation."""
    return SHA256.new(email.encode("utf-8")).hexdigest()


def generate_key(email, password):
    """Encrypt the password using a key derived from the hashed email."""
    hash = hash_email(email)[:32]  # Take the first 32 characters of the hashed email

    combined = aes_encrypt(data=password.encode("utf-8"), password=hash)

    return base64.b64encode(combined)


def generate_url(email, password, base_url, file):
    """Generate the URL to the encrypted file."""
    key = generate_key(email, password)

    # URL encode the email and key
    encoded_email = urllib.parse.quote(email)
    encoded_key = urllib.parse.quote(key)

    # Construct the URL
    url = urllib.parse.urljoin(base_url, file)
    full_url = f"{url}?email={encoded_email}&key={encoded_key}"

    return full_url


def get_password_from_email_and_key(email, key):
    # Derive the key from the hashed email
    hash = hash_email(email)[:32]  # Take the first 32 characters of the hashed email

    # Decode the key from Base64
    encrypted_data = base64.b64decode(key)

    # Decrypt the data using the derived key
    decrypted_content = aes_decrypt(encrypted_data, hash)

    return decrypted_content.decode("utf-8")


def encrypt_pdf_file(input_file, password, output_file=None):
    if output_file is None:
        output_file = "encrypted-{}".format(input_file)
    with open(input_file, "rb") as file:
        pdf_content = file.read()
        encrypted_data = encrypt_pdf_content(pdf_content=pdf_content, password=password)
        with open(output_file, "wb") as out_file:
            out_file.write(encrypted_data)
