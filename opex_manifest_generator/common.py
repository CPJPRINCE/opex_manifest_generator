"""
Common tools for use throghout program.

author: Christopher Prince
license: Apache License 2.0"
"""

import zipfile, os, sys

def zip_opex(file_path,opex_path):
    zip_file = f"{file_path}.zip"
    if not os.path.exists(zip_file):
        with zipfile.ZipFile(zip_file,'w') as z:
            z.write(file_path,os.path.basename(file_path))
            z.write(opex_path,os.path.basename(opex_path))
    else: print(f'A zip file already exists for: {zip_file}')

def win_256_check(path: str):
    if len(path) > 255 and sys.platform == "win32":
        if path.startswith(u'\\\\?\\'): path = path
        else: path = u"\\\\?\\" + path
    return path

def check_nan(value):
    if str(value).lower() in {"nan","nat"}:
        value = None
    return value
