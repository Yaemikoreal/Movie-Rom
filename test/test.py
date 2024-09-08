import hashlib
import binascii
import os

# 设置密码和盐值
password = "200212"
salt = os.urandom(16)  # 生成随机盐值

# 使用 PBKDF2 进行加密
key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
key_hex = binascii.hexlify(key)

print("Salt:", binascii.hexlify(salt))
print("PBKDF2 Hash:", key_hex)
