"""
Hash Generator class for generating Fixities for files.

author: Christopher Prince
license: Apache License 2.0"
"""

import hashlib, logging, os
from opex_manifest_generator.common import win_256_check
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
from typing import Iterable, Optional, Dict
import zipfile
logger = logging.getLogger(__name__)

import time


class HashGenerator():
    def __init__(self, algorithm: str = "SHA-1", buffer: int = 4096):
        self.algorithm = algorithm
        self.buffer = buffer

    def hash_generator(self, file_path: str) -> str:
        file_path = win_256_check(file_path)
        if "SHA-1" in self.algorithm:
            hash = hashlib.sha1()
        elif "MD5" in self.algorithm:
            hash = hashlib.md5()
        elif "SHA-256" in self.algorithm:
            hash = hashlib.sha256()
        elif "SHA-512" in self.algorithm:
            hash = hashlib.sha512()
        else:
            hash = hashlib.sha1()
        logger.info(f'Generating Fixity using {self.algorithm} for: {file_path}')
        try:
            with open(file_path, 'rb') as f:
                while True:
                    buff = f.read(self.buffer)
                    if not buff:
                        break
                    hash.update(buff)
                f.close()
            logger.debug(f'Generated Hash: {hash.hexdigest().upper()}')
            return hash.hexdigest().upper()
        except FileNotFoundError as e:
            logger.exception(f'File Not Found generating Hash: {e}')
            raise
        except IOError as e:
            logger.exception(f'I/O Error generating Hash: {e}')
            raise
        except Exception as e:
            logger.exception(f'Error Generating Hash: {e}')
            raise

    def hash_generator_pax_zip(self, filename: str, z: zipfile.ZipFile) -> str:
        filename = win_256_check(filename)
        if "SHA-1" in self.algorithm:
            hash = hashlib.sha1()
        elif "MD5" in self.algorithm:
            hash = hashlib.md5()
        elif "SHA-256" in self.algorithm:
            hash = hashlib.sha256()
        elif "SHA-512" in self.algorithm:
            hash = hashlib.sha512()
        else:
            hash = hashlib.sha1()
        logger.info(f'Generating Fixity using {self.algorithm} for: {filename}')
        try:
            with z.open(filename, 'r') as data:
                while True:
                    buff = data.read(self.buffer)
                    if not buff:
                        break
                    hash.update(buff)
                data.close()
        except FileNotFoundError as e:
            logger.exception(f'File Not Found generating Hash: {e}')
            raise
        except IOError as e:
            logger.exception(f'I/O Error generating Hash: {e}')
            raise
        except Exception as e:
            logger.exception(f'Error Generating Hash: {e}')
            raise
        return str(hash.hexdigest().upper())

    def hash_generator_multithread(self, files_list: Iterable[str], max_workers: Optional[int] = 1, pax_flag: Optional[bool] = False) -> Dict[str, str]:
        if max_workers is None or int(max_workers) == 0:
            logger.warning(f'Max workers set to None. Defaulting to number of CPU cores: {os.cpu_count()}')
            max_workers = os.cpu_count() or 1
        else:
            max_workers = int(max_workers)

        def process_future(future_to_hash):
            for future in as_completed(future_to_hash):
                file = future_to_hash[future]
                try:
                    hash = future.result()
                    logger.debug(f'Hash generated via multithread for {file}: {hash}')
                    return hash
                except Exception as e:
                    logger.exception(f'Error generating hash for {file}: {e}')
                    return None

        # IF pax flag is set and there are .pax.zip files, process those files in multithreaded function
        hash_results = {}
        if pax_flag and any(file.endswith('.pax.zip') and os.path.isfile(file) for file in files_list):
            pax_files_list = [file for file in files_list if file.endswith('.pax.zip')]
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                for file in pax_files_list:
                    with zipfile.ZipFile(file, 'r') as z:
                        pax_results = []
                        for zf in z.filelist:
                            future_to_hash = {executor.submit(self.hash_generator_pax_zip, zf.filename, z): zf.filename}
                            hash = process_future(future_to_hash)
                            pax_results.append({'path': zf.filename.replace('\\','/'), 'value': hash, 'type': self.algorithm})
                    hash_results.update({file: pax_results})
        # If pax flag is set but there are no .pax.zip files, process all files as normal in multithreaded function

        if pax_flag and any(os.path.isfile(file) for file in files_list if not file.endswith('.pax.zip')):
            normal_files_list = [file for file in files_list if os.path.isfile(file) and not file.endswith('.pax.zip')]
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                for file in normal_files_list:
                    future_to_hash = {executor.submit(self.hash_generator, file): file}
                    hash = process_future(future_to_hash)
                    hash_results.update({file: {'value': hash, 'type': self.algorithm}})

        # If pax flag is set and there are .pax folders, process those folders in multithreaded function
        if pax_flag and any(dir.endswith('.pax') and os.path.isdir(dir) for dir in files_list):
            pax_folder_list = [f for f in files_list if f.endswith('.pax') and os.path.isdir(f)]
            # Needs to be Different... See PAX Zip files but with folders. Also see older version os.walk...
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                for folder in pax_folder_list:
                    future_to_hash = {executor.submit(self.hash_generator, os.path.join(root, file)): os.path.join(root, file) for root, _, files in os.walk(pax_folder_list) for file in files}
                    hash = process_future(future_to_hash)
                    hash_results.update({file: {'value': hash, 'type': self.algorithm}})

        # If pax flag is not set, process all files as normal
        if pax_flag is False:
            file_list = [file for file in files_list if os.path.isfile(file)]
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                for file in file_list:
                    future_to_hash = {executor.submit(self.hash_generator, file): file}
                    hash = process_future(future_to_hash)
                    hash_results.update({file: {'value': hash, 'type': self.algorithm}})
        return hash_results
