"""
Hash Generator class for generating Fixities for files.

author: Christopher Prince
license: Apache License 2.0"
"""

import hashlib

class HashGenerator():
    def __init__(self,algorithm="SHA-1"):
        self.algorithm = algorithm
        self.buffer = 4096

    def hash_generator(self,file_path: str):
        if self.algorithm == "SHA-1":
            hash = hashlib.sha1()
        elif self.algorithm == "MD5":
            hash = hashlib.md5()
        elif self.algorithm == "SHA-256":
            hash = hashlib.sha256()
        elif self.algorithm == "SHA-512":
            hash = hashlib.sha512()
        else:
            hash = hashlib.sha1()
        print(f'Generating Fixity using {self.algorithm} for: {file_path}')
        with open(file_path, "rb") as f:
            while True:
                buff = f.read(self.buffer)
                if not buff:
                    break
                hash.update(buff)
            f.close()
        return hash.hexdigest().upper()