"""
Hash Generator class for generating Fixities for files.

author: Christopher Prince
license: Apache License 2.0"
"""

import hashlib
from opex_manifest_generator.common import win_256_check 
import os, io

class HashGenerator():
    def __init__(self, algorithm: str = "SHA-1", buffer: int = 4096):
        self.algorithm = algorithm
        self.buffer = buffer

    def hash_generator(self, file_path: str):
        file_path = win_256_check(file_path)
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
        try:
            with open(file_path, 'rb', buffering = 0) as f:
                while True:
                    buff = f.read(self.buffer)
                    if not buff:
                        break
                    hash.update(buff)
                f.close()
        except Exception as e:
            print(e)
            raise SystemError()
        return hash.hexdigest().upper()
        
    def hash_generator_pax_zip(self, filename, z):
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
        print(f'Generating Fixity using {self.algorithm} for: {filename}')
        try:
            with z.open(filename, 'r') as data:            
                while True:
                    buff = data.read(self.buffer)
                    if not buff:
                        break
                    hash.update(buff)
        except Exception as e:
            print(e)
            raise SystemError()
        return hash.hexdigest().upper()