"""
Common tools for use throghout program.

author: Christopher Prince
license: Apache License 2.0"
"""

import zipfile, os, sys, stat, shutil, logging, lxml
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

def zip_opex(file_path,opex_path = None) -> str:
    zip_file = f"{file_path}.zip"
    if not os.path.exists(zip_file):
        with zipfile.ZipFile(zip_file,'w') as z:
            if os.path.exists(file_path):
                z.write(file_path,os.path.basename(file_path))
            if opex_path is not None and os.path.exists(opex_path):
                z.write(opex_path,os.path.basename(opex_path))
        logger.debug(f'File has been zipped to: {zip_file}')
    else:
        logger.warning(f'A Zip file already exists for: {zip_file}')
    return zip_file

def remove_tree(path: str, removed_list: list) -> None:
    removed_list.append(path)
    logger.info(f"Removing: {path}")
    if os.path.isdir(path):
        for dp,d,f in os.walk(path):
            for fn in f:
                removed_list.append(win_256_check(dp+win_path_delimiter()+fn))
                logger.info(f'Removing {dp + win_path_delimiter() + fn}')            
            for dn in d:
                removed_list.append(win_256_check(dp+win_path_delimiter()+dn))
                logger.info(f'Removing {dp + win_path_delimiter() + dn}')
        shutil.rmtree(path)
    else:
        if os.path.exists(path):
            os.remove(path)
            logger.info (f'Removing File: {path}')

def win_256_check(path) -> str:
    if len(path) > 255 and sys.platform == "win32":
        logger.debug(f'Path: {path} is greater than 255 Characters')
        if path.startswith(u"\\\\?\\"):
            path = path 
        else:
            path = u"\\\\?\\" + path
    return path

def filter_win_hidden(path: str) -> bool:
    if sys.platform =="win32":
        if bool(os.stat(path).st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN) is True:
            return True
        else:
            return False
    else:
        return False
    
def win_path_delimiter() -> str:
    if sys.platform == "win32":
        return "\\"
    else:
        return "/"

def check_nan(value) -> Optional[str]:
    if str(value).lower() in {"nan","nat"}:
        value = None
    return value

def check_opex(opex_path:str) -> bool:
    opex_path = opex_path + ".opex" 
    if os.path.exists(win_256_check(opex_path)):
        return False
    else: 
        return True

def write_opex(path: str, opexxml: lxml.etree.Element) -> str:
    opex_path = win_256_check(str(path) + ".opex")
    opex = lxml.etree.indent(opexxml, "  ")
    opex = lxml.etree.tostring(opexxml, pretty_print=True, xml_declaration=True, encoding="UTF-8", standalone=True)
    with open(f'{opex_path}', 'w', encoding="UTF-8") as writer:
        writer.write(opex.decode('UTF-8'))
        logger.info('Saved Opex File to: ' + opex_path)
    return opex_path

def running_time(start_time) -> timedelta:
    running_time = datetime.now() - start_time 
    return running_time