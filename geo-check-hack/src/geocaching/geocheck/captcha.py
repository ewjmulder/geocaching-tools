import hashlib

captcha_hashes = {}
for number in range(0, 100000):
    number_str = str(number).zfill(5)
    md5 = hashlib.md5(bytes(number_str, 'utf-8')).hexdigest()
    captcha_hashes[md5] = number


def lookup_captcha(captcha_hash):
    return captcha_hashes[captcha_hash]
