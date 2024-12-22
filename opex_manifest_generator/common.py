"""
Common tools for use throghout program.

author: Christopher Prince
license: Apache License 2.0"
"""

import zipfile, os, sys, time, stat
import datetime
from lxml import etree

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

def filter_win_hidden(path: str):
    if sys.platform =="win32":
        if bool(os.stat(path).st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN) is True:
            return True
        else:
            return False
    else:
        return False
    
def win_path_delimiter():
    if sys.platform == "win32":
        return "\\"
    else:
        return "/"

def check_nan(value):
    if str(value).lower() in {"nan","nat"}:
        value = None
    return value

def check_opex(opex_path:str):
    opex_path = opex_path + ".opex" 
    if os.path.exists(win_256_check(opex_path)):
        return False
    else: 
        return True

def write_opex(path: str, opexxml: etree.Element):
    opex_path = win_256_check(str(path) + ".opex")
    opex = etree.indent(opexxml, "  ")
    opex = etree.tostring(opexxml, pretty_print=True, xml_declaration=True, encoding="UTF-8", standalone=True)
    with open(f'{opex_path}', 'w', encoding="UTF-8") as writer:
        writer.write(opex.decode('UTF-8'))
        print('Saved Opex File to: ' + opex_path)
    return opex_path

def print_running_time(start_time):
    print(f'Running time: {datetime.datetime.now() - start_time}')
    time.sleep(5)
