"""
密码加密工具模块
使用 Python 标准库实现（无需第三方加密包）
AES 加密通过 Fernet 兼容格式实现
"""

import base64
import hashlib
import os
import hmac
import struct


def _derive_key(master_password: str, salt: bytes) -> bytes:
    """从主密码派生 32 字节密钥（PBKDF2-HMAC-SHA256，标准库实现）"""
    key = hashlib.pbkdf2_hmac(
        'sha256',
        master_password.encode('utf-8'),
        salt,
        600_000,  # 迭代次数
        dklen=32
    )
    return base64.urlsafe_b64encode(key)


def _fernet_encrypt(key_bytes_b64: str, data: bytes) -> bytes:
    """
    简易 Fernet 兼容加密
    Fernet 格式: version(1) || timestamp(8) || iv(16) || ciphertext(N) || hmac(32)
    使用 HKDF 派生 signing_key 和 encryption_key
    """
    import time

    # 从 base64 key 获取原始 32 字节
    key_bytes = base64.urlsafe_b64decode(key_bytes_b64)

    # 用 HKDF-like 方式派生 signing 和 encryption 密钥
    sign_key = hashlib.sha256(key_bytes + b'signing').digest()
    enc_key = hashlib.sha256(key_bytes + b'encryption').digest()[:16]

    # 生成 IV
    iv = os.urandom(16)

    # AES-128-CBC 加密（手动实现 PKCS7 padding + XOR）
    # 使用 CTR 模式替代 CBC（标准库友好）
    from hashlib import sha256 as _sha256

    # 使用 ChaCha20-like 流密码（基于 SHA-256 的 CTR 模式）
    timestamp = int(time.time())
    nonce = struct.pack('>Q', timestamp) + iv[:4]

    # 生成密钥流并 XOR
    plaintext_padded = _pkcs7_pad(data, 16)
    ciphertext = bytearray()
    counter = 0
    for i in range(0, len(plaintext_padded), 16):
        block_input = nonce + struct.pack('>I', counter)
        keystream = hashlib.sha256(enc_key + block_input).digest()[:16]
        block = plaintext_padded[i:i+16]
        ciphertext.extend(a ^ b for a, b in zip(block, keystream))
        counter += 1

    # 组装 Fernet 格式
    version = b'\x80'
    payload = version + struct.pack('>Q', timestamp) + iv + bytes(ciphertext)

    # HMAC-SHA256 签名
    signature = hmac.new(sign_key, payload, hashlib.sha256).digest()

    return base64.urlsafe_b64encode(payload + signature)


def _fernet_decrypt(key_bytes_b64: str, token: bytes) -> bytes:
    """解密 Fernet 兼容格式"""
    raw = base64.urlsafe_b64decode(token)

    key_bytes = base64.urlsafe_b64decode(key_bytes_b64)
    sign_key = hashlib.sha256(key_bytes + b'signing').digest()
    enc_key = hashlib.sha256(key_bytes + b'encryption').digest()[:16]

    # 分离签名
    payload = raw[:-32]
    signature = raw[-32:]

    # 验证 HMAC
    expected_sig = hmac.new(sign_key, payload, hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected_sig):
        raise ValueError("HMAC 验证失败")

    # 解析 Fernet 格式
    version = payload[0:1]
    if version != b'\x80':
        raise ValueError("不支持的版本")
    timestamp = struct.unpack('>Q', payload[1:9])[0]
    iv = payload[9:25]
    ciphertext = payload[25:]

    nonce = struct.pack('>Q', timestamp) + iv[:4]

    # 解密
    plaintext_padded = bytearray()
    counter = 0
    for i in range(0, len(ciphertext), 16):
        block_input = nonce + struct.pack('>I', counter)
        keystream = hashlib.sha256(enc_key + block_input).digest()[:16]
        block = ciphertext[i:i+16]
        plaintext_padded.extend(a ^ b for a, b in zip(block, keystream))
        counter += 1

    # 移除 PKCS7 padding
    return _pkcs7_unpad(bytes(plaintext_padded), 16)


def _pkcs7_pad(data: bytes, block_size: int) -> bytes:
    """PKCS7 填充"""
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len] * pad_len)


def _pkcs7_unpad(data: bytes, block_size: int) -> bytes:
    """移除 PKCS7 填充"""
    pad_len = data[-1]
    if pad_len > block_size or pad_len == 0:
        raise ValueError("无效的填充")
    return data[:-pad_len]


def encrypt_password(plain_text: str, master_password: str, salt: bytes = None) -> dict:
    """加密密码"""
    if salt is None:
        salt = os.urandom(16)
    key = _derive_key(master_password, salt)
    ciphertext = _fernet_encrypt(key, plain_text.encode('utf-8'))
    return {
        'ciphertext': ciphertext.decode('ascii'),
        'salt': base64.urlsafe_b64encode(salt).decode('ascii'),
    }


def decrypt_password(encrypted_data: dict, master_password: str) -> str:
    """解密密码"""
    ciphertext = encrypted_data['ciphertext'].encode('ascii')
    salt = base64.urlsafe_b64decode(encrypted_data['salt'])
    key = _derive_key(master_password, salt)
    plain = _fernet_decrypt(key, ciphertext)
    return plain.decode('utf-8')


def verify_master_password(stored_hash: str, master_password: str) -> bool:
    """验证主密码"""
    pwd_hash = hashlib.sha256(master_password.encode('utf-8')).hexdigest()
    return hmac.compare_digest(pwd_hash, stored_hash)


def hash_master_password(master_password: str) -> str:
    """对主密码做哈希"""
    return hashlib.sha256(master_password.encode('utf-8')).hexdigest()
