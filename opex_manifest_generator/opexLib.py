from lxml import etree
import logging
from opex_manifest_generator.common import win_256_check, filter_manifest
from opex_manifest_generator.hash import HashGenerator
from typing import Optional, Dict, Union
import os, zipfile

logger = logging.getLogger(__name__)

class OpexReader():
    """
    Don't Use... This is a placeholder class to allow for dynamic assignment of either OpexFileReader or OpexDirReader based on the input path. The __init__ method will attempt to parse the input path as an OPEX file first, and if that fails, it will attempt to parse it as an OPEX directory. If both attempts fail, it will raise an exception.
    """
    def __init__(self, path: str) -> None:
        if path.startswith(u'\\\\?\\'):
            self.path = path.replace(u'\\\\?\\', "")
        else:
            self.path = path
        try:
            self.path_tmp = self.path.removesuffix('.opex')
            if os.path.isfile(self.path_tmp):
                self = OpexFileReader(self.path)
            elif os.path.isdir(self.path_tmp):
                self = OpexDirReader(self.path)
        except etree.ParseError as e:
            logger.exception(f'Failed to parse OPEX XML file: {e}')
            raise
        except FileNotFoundError as e:
            logger.exception(f'OPEX XML file not found: {e}')
            raise

class OpexDirReader():
    def __init__(self, file_path: str) -> None:
        if file_path.startswith(u'\\\\?\\'):
            self.file_path = file_path.replace(u'\\\\?\\', "")
        else:
            self.file_path = file_path
        try:
            self.tree = etree.parse(self.file_path)
            opexnsmap = self.tree.getroot().nsmap
            self.opexns = opexnsmap.get('opex')
            self.tree.getroot()  # Force parsing to catch errors early
            self.manifest_elm = self.tree.findall(f'.//{{{self.opexns}}}Manifest//') if self.tree is not None and self.tree.find(f'.//{{{self.opexns}}}Manifest') is not None else None
            self.manifest = []
            self.folders = []
            self.files = []
            self.files_dict = []
            for elm in self.manifest_elm or []:
                if elm.tag == f"{{{self.opexns}}}Folder":
                    self.manifest.append({'type': 'folder', 'name': elm.text})
                    self.folders.append(elm.text)
                elif elm.tag == f"{{{self.opexns}}}File":
                    self.manifest.append({'type': elm.attrib.get('type'), 'name': elm.text, 'size': elm.attrib.get('size')})
                    self.files.append(elm.text)
                    self.files_dict.append({'type': elm.attrib.get('type'), 'name': elm.text, 'size': elm.attrib.get('size')})
            self.folders_elms = self.tree.findall(f'.//{{{self.opexns}}}Manifest/{{{self.opexns}}}Folders/{{{self.opexns}}}Folder') if self.tree.findall(f'.//{{{self.opexns}}}Manifest/{{{self.opexns}}}Folders/{{{self.opexns}}}Folder') is not None else None
            self.files_elms = self.tree.findall(f'.//{{{self.opexns}}}Manifest/{{{self.opexns}}}Files/{{{self.opexns}}}File') if self.tree.findall(f'.//{{{self.opexns}}}Manifest/{{{self.opexns}}}Files/{{{self.opexns}}}File') is not None else None
            self.title_elm = self.tree.find(f'.//{{{self.opexns}}}Title') if self.tree.find(f'.//{{{self.opexns}}}Title') is not None else None
            self.title = self.title_elm.text if self.title_elm is not None else None
            self.description_elm = self.tree.find(f'.//{{{self.opexns}}}Description') if self.tree.find(f'.//{{{self.opexns}}}Description') is not None else None
            self.description = self.description_elm.text if self.description_elm is not None else None
            self.security_elm = self.tree.find(f'.//{{{self.opexns}}}SecurityDescriptor') if self.tree.find(f'.//{{{self.opexns}}}SecurityDescriptor') is not None else None
            self.security = self.security_elm.text if self.security_elm is not None else None
            self.identifiers_elm = self.tree.findall(f'.//{{{self.opexns}}}Identifiers/{{{self.opexns}}}Identifier') if self.tree.findall(f'.//{{{self.opexns}}}Identifiers/{{{self.opexns}}}Identifier') is not None else None
            self.identifiers = [] if self.identifiers_elm is not None else None
            self.sourceid_elm = self.tree.find(f'.//{{{self.opexns}}}SourceID') if self.tree.find(f'.//{{{self.opexns}}}SourceID') is not None else None
            self.sourceid = self.sourceid_elm.text if self.sourceid_elm is not None else None
            for ident in self.identifiers_elm or []:
                self.identifiers.append({'type': ident.attrib.get('type'), 'value': ident.text})
            self.descriptive_metadata_xml = self.tree.find(f'.//{{{self.opexns}}}DescriptiveMetadata') if self.tree.find(f'.//{{{self.opexns}}}DescriptiveMetadata') is not None else None
            self.descriptive_metadata = etree.tostring(self.descriptive_metadata_xml) if self.descriptive_metadata_xml is not None else None
        except etree.ParseError as e:
            logger.exception(f'Failed to parse OPEX XML file: {e}')
            raise
        except FileNotFoundError as e:
            logger.exception(f'OPEX XML file not found: {e}')
            raise

    def __str__(self, *args, **kwds):
        return f"OPEX Directory Reader for: {self.file_path}" \
        f"\nTitle: {self.title}" \
        f"\nDescription: {self.description}" \
        f"\nSecurity Descriptor: {self.security}" \
        f"\nSourceID: {self.sourceid}" \
        f"\nIdentifiers: {self.identifiers}"

    def __repr__(self):
        return self.__str__()

    def print_files(self):
        for file in self.files_dict:
            print(f'File: {file.get("name")}, Type: {file.get("type")}, Size: {file.get("size")}')

    def print_folders(self):
        for folder in self.folders:
            print(f'Folder: {folder}')

    def get_descriptive_metadata(self) -> str:
        return self.descriptive_metadata

    def get_title(self) -> str:
        return self.title

    def get_description(self) -> str:
        return self.description

    def get_security_descriptor(self) -> str:
        return self.security

    def get_identifiers(self) -> dict:
        return self.identifiers

    def get_sourceid(self) -> str:
        return self.sourceid

    def get_manifest(self) -> list:
        return self.manifest

    def get_folders(self) -> list:
        return self.folders

    def get_files(self) -> list:
        return self.files

    def get_files_dict(self) -> list:
        return self.files_dict

    def verify_opex_version(self, expected_version: str = "1.2") -> bool:
        try:
            opexnsmap = self.tree.getroot().nsmap
            opexns = opexnsmap.get('opex')
            version = opexns.split('/')[-1]
            if version == expected_version:
                return True
            else:
                logger.warning(f'OPEX version mismatch: expected {expected_version}, found {version}')
                return False
        except Exception as e:
            logger.exception(f'Error verifying OPEX version: {e}')
            raise
    def to_string(self) -> str:
        return etree.tostring(self.tree, pretty_print=True, xml_declaration=True, encoding="UTF-8", standalone=True).decode('UTF-8')
    
    def to_element(self) -> etree._Element:
        return self.tree.getroot()
    
    def to_tree(self) -> etree._ElementTree:
        return self.tree
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "security_descriptor": self.security,
            "sourceid": self.sourceid,
            "identifiers": self.identifiers,
            "fixities": self.fixities,
            "descriptive_metadata": str(self.descriptive_metadata)
        }

class OpexDirWriter():

    def __init__(self, folder_path: str, title: Optional[str] = None, description: Optional[str] = None, security_tag: Optional[str] = None, opexns: Optional[str] = "http://www.openpreservationexchange.org/opex/v1.2", **kwargs) -> None:

        self.DEFAULT_EXCLUSIONS = {'opex_generate.exe', 'opex_generate.cmd', 'meta', 'opex_generate.bin', os.path.basename(__file__)}

        ### Generation Presets
        self.sort_key = kwargs.get('sort_key', str.casefold)
        self.exclusion_set = kwargs.get('exclusion_set', self.DEFAULT_EXCLUSIONS)
        self.include_hidden = kwargs.get('include_hidden', False)
        self.filter_flag = kwargs.get('filter_flag', None)
        self.pax_flag = kwargs.get('pax_flag', False)

        if self.filter_flag is not None and self.filter_flag not in {"only_files", "only_dir"}:
            log_msg = f'Invalid filter_flag value: {self.filter_flag}. Must be "only_files", "only_dirs", or None.'
            logger.error(log_msg)
            raise ValueError(log_msg)

        if folder_path.startswith(u'\\\\?\\'):
            self.folder_path = folder_path.replace(u'\\\\?\\', "")
        else:
            self.folder_path = folder_path

        self.opexns = opexns
        self.opex_root = etree.Element(f"{{{self.opexns}}}OPEXMetadata", nsmap={"opex":self.opexns})
        self.transfer_opex = etree.SubElement(self.opex_root, f"{{{self.opexns}}}Transfer")

        if self.pax_flag is True and self.folder_path.endswith('.pax'):
            logger.debug(f'PAX flag is set to True and folder path ends with .pax, enabling PAX-specific fixity generation for files within this folder.')
            self.generate_pax_manifest(generate_fixity=kwargs.get('generate_fixity', None), fixity_list=kwargs.get('fixity_list', None), buffer=kwargs.get('buffer', 4096))
        else:
            self.manifest_opex = etree.SubElement(self.transfer_opex, f"{{{self.opexns}}}Manifest")
            self.folders_opex = etree.SubElement(self.manifest_opex, f"{{{self.opexns}}}Folders")
            self.files_opex = etree.SubElement(self.manifest_opex, f"{{{self.opexns}}}Files")

        self.sourceid = kwargs.get('sourceid', None)
        if self.sourceid is not None:
            self.sourceid_xml = etree.SubElement(self.transfer_opex, f"{{{self.opexns}}}SourceID")
            self.sourceid_xml.text = str(self.sourceid)

        if title is not None:
            self.title = title
        else:
            self.title = None
        if description is not None:
            self.description = description
        else:
            self.description = None
        if security_tag is not None:
            self.security_tag = security_tag
        else:
            self.security_tag = None

        self.identifiers: list = kwargs.get('identifiers', None)

        if any([self.title, self.description, self.security_tag, self.identifiers]):
            self.properties_opex = etree.SubElement(self.opex_root, f"{{{self.opexns}}}Properties")
            if self.title:
                self.title_opex = etree.SubElement(self.properties_opex, f"{{{self.opexns}}}Title")
                self.title_opex.text = str(self.title)
            if self.description:
                self.description_opex = etree.SubElement(self.properties_opex, f"{{{self.opexns}}}Description")
                self.description_opex.text = str(self.description)
            if self.security_tag:
                self.security_tag_opex = etree.SubElement(self.properties_opex, f"{{{self.opexns}}}SecurityDescriptor")
                self.security_tag_opex.text = str(self.security_tag)
            if self.identifiers is not None and isinstance(self.identifiers, list) and len(self.identifiers) > 0:
                self.identifiers_opex = etree.SubElement(self.properties_opex, f"{{{self.opexns}}}Identifiers")
                for ident in self.identifiers:
                    self.ident_opex = etree.SubElement(self.identifiers_opex, f"{{{self.opexns}}}Identifier")
                    hash_type = ident.get("type", None)
                    hash_value = ident.get("value", None)
                    if hash_type is not None and hash_value is not None:
                        self.ident_opex.set("type", hash_type)
                        self.ident_opex.text = str(hash_value)


        self.descriptive_metadata: Union[str, etree._ElementTree, etree._Element] = kwargs.get('descriptive_metadata', None)

        if self.descriptive_metadata is not None:
            self.descmeta_opex = etree.SubElement(self.opex_root, f"{{{self.opexns}}}DescriptiveMetadata")
            if isinstance(self.descriptive_metadata, str):
                try:
                    self.descmeta_opex.append(etree.fromstring(self.descriptive_metadata))
                except etree.ParseError as e:
                    logger.exception(f'Failed to parse descriptive metadata XML string: {e}')
                    raise
            elif isinstance(self.descriptive_metadata, str) and self.descriptive_metadata.endswith('.xml'):
                try:
                    tree = etree.parse(self.descriptive_metadata)
                    self.descmeta_opex.append(tree.getroot())
                except (etree.ParseError, FileNotFoundError) as e:
                    logger.exception(f'Failed to parse descriptive metadata XML file: {e}')
                    raise
            elif isinstance(self.descriptive_metadata, (etree._Element, etree._ElementTree)):
                try:
                    self.descmeta_opex.append(self.descriptive_metadata)
                except etree.ParseError as e:
                    logger.exception(f'Failed to parse descriptive metadata XML tree: {e}')
                    raise

    def generate_dir_manifest(self, path: str, filter_flag: Optional[str] = None) -> None:
        if self.pax_flag is True and self.folder_path.endswith('.pax'):
            logger.debug(f'PAX flag is set to True and folder path ends with .pax, skipping standard manifest generation for this folder and relying on PAX-specific fixity generation method to populate manifest with file entries and fixities.')
            return
        for f in filter_manifest(path, self.include_hidden, self.exclusion_set, self.sort_key):
            f: str
            if os.path.isdir(f):
                if filter_flag is not None and filter_flag == "only_dirs":
                    continue
                folder_opex = etree.SubElement(self.folders_opex, f"{{{self.opexns}}}Folder")
                folder_opex.text = os.path.basename(f)
            elif os.path.isfile(f) and f.endswith('.opex'):
                if filter_flag is not None and filter_flag == "only_files":
                    continue
                file_opex = etree.SubElement(self.files_opex, f"{{{self.opexns}}}File")
                file_opex.set("type", "metadata")
                file_opex.text = os.path.basename(f)
            elif os.path.isfile(f):
                if filter_flag is not None and filter_flag == "only_files":
                    continue
                file_opex = etree.SubElement(self.files_opex, f"{{{self.opexns}}}File")
                file_opex.set("type", "content")
                file_opex.set("size", str(os.path.getsize(f)))
                file_opex.text = os.path.basename(f)
            else:
                logger.warning(f'Unknown file type for: {f}')

    def generate_pax_manifest(self, generate_fixity: list, fixity_list: list, **kwargs) -> None:
        self.generate_fixity = generate_fixity
        self.fixity_list = fixity_list
        pax_list = [os.path.join(root,filename) for root,_,files in os.walk(self.folder_path) for filename in files]
        if self.generate_fixity is not None and self.fixity_list is not None:
            logger.warning('Both generate_fixity and fixity arguments provided. Will use fixitity_list and ignore generation.')
            self.generate_fixity = None
        if self.generate_fixity is not None and len(self.generate_fixity) > 0 and self.folder_path.endswith('.pax') and os.path.isdir(self.folder_path):
            self.fixities_opex = etree.SubElement(self.transfer_opex, f"{{{self.opexns}}}Fixities")
            for filename in pax_list:
                for fix in self.generate_fixity:
                    hash_value = HashGenerator(algorithm = fix, buffer = kwargs.get('buffer', 4096)).hash_generator(filename)
                    self.fixity_opex = etree.SubElement(self.fixities_opex, f"{{{self.opexns}}}Fixity")
                    self.fixity_opex.set("path", os.path.relpath(filename, self.folder_path).replace('\\','/'))
                    self.fixity_opex.set("type", fix)
                    self.fixity_opex.set("value", hash_value)
        if self.fixity_list is not None and len(self.fixity_list) > 0:
            self.fixities_opex = etree.SubElement(self.transfer_opex, f"{{{self.opexns}}}Fixities")
            for filename in pax_list:
                for fix in self.fixity_list:
                    if isinstance(fix, dict):
                        self.fixity_opex = etree.SubElement(self.fixities_opex, f"{{{self.opexns}}}Fixity")
                        if fix.get("path") is not None:
                            self.fixity_opex.set("path", fix.get("path", None))
                        self.fixity_opex.set("type", fix.get("type", None))
                        self.fixity_opex.text = fix.get("value", None)


    def generate_opex(self) -> etree._Element:
        self.generate_dir_manifest(self.folder_path)
        return self.opex_root

    def generate_opex_str(self) -> str:
        self.generate_dir_manifest(self.folder_path)
        return etree.tostring(self.opex_root, pretty_print=True, xml_declaration=True, encoding="UTF-8", standalone=True)

    def write_opex_manifest(self, opex_path: str = None, file_override: bool = False) -> str:
        self.generate_dir_manifest(self.folder_path, filter_flag=self.filter_flag)
        if opex_path is None:
            opex_path = win_256_check(os.path.join(self.folder_path, os.path.basename(self.folder_path) + ".opex"))
        else:
            opex_path = win_256_check(opex_path)
        if os.path.exists(opex_path) and file_override is False:
            logger.warning(f"Opex manifest already exists at: {opex_path}, skipping write.")
            return None
        else:
            opex = etree.tostring(self.opex_root, pretty_print=True, xml_declaration=True, encoding="UTF-8", standalone=True)
            try:
                with open(f'{opex_path}', 'w', encoding="UTF-8") as writer:
                    logger.info(f'Writing OPEX manifest to: {opex_path}')
                    writer.write(opex.decode('UTF-8'))
                return opex_path
            except (PermissionError, OSError) as e:
                logger.exception(f'Failed to write OPEX file: {e}')
                raise

class OpexFileReader():
    def __init__(self, file_path: str) -> None:
        if file_path.startswith(u'\\\\?\\'):
            self.file_path = file_path.replace(u'\\\\?\\', "")
        else:
            self.file_path = file_path
        try:
            self.tree = etree.parse(self.file_path)
            opexnsmap = self.tree.getroot().nsmap
            self.opexns = opexnsmap.get('opex')
            self.tree.getroot()  # Force parsing to catch errors early
            self.title_elm = self.tree.find(f'.//{{{self.opexns}}}Title') if self.tree.find(f'.//{{{self.opexns}}}Title') is not None else None
            self.title = self.title_elm.text if self.title_elm is not None else None
            self.description_elm = self.tree.find(f'.//{{{self.opexns}}}Description') if self.tree.find(f'.//{{{self.opexns}}}Description') is not None else None
            self.description = self.description_elm.text if self.description_elm is not None else None
            self.security_elm = self.tree.find(f'.//{{{self.opexns}}}SecurityDescriptor') if self.tree.find(f'.//{{{self.opexns}}}SecurityDescriptor') is not None else None
            self.security = self.security_elm.text if self.security_elm is not None else None
            self.identifiers_elm = self.tree.findall(f'.//{{{self.opexns}}}Identifiers/{{{self.opexns}}}Identifier') if self.tree.findall(f'.//{{{self.opexns}}}Identifiers/{{{self.opexns}}}Identifier') is not None else None
            self.identifiers = [] if self.identifiers_elm is not None else None
            self.sourceid_elm = self.tree.find(f'.//{{{self.opexns}}}SourceID') if self.tree.find(f'.//{{{self.opexns}}}SourceID') is not None else None
            self.sourceid = self.sourceid_elm.text if self.sourceid_elm is not None else None
            if self.identifiers_elm is not None:
                for ident in self.identifiers_elm or []:
                    self.identifiers.append({'type': ident.attrib.get('type'), 'value': ident.text})
            self.fixities_elm = self.tree.findall(f'.//{{{self.opexns}}}Fixities/{{{self.opexns}}}Fixity') if self.tree.findall(f'.//{{{self.opexns}}}Fixities/{{{self.opexns}}}Fixity') is not None else None
            self.fixities = [] if self.fixities_elm is not None else None
            if self.fixities_elm is not None:
                for fix in self.fixities_elm:
                    self.fixities.append({'type': fix.attrib.get('type'), 'value': fix.text})
                    if fix.attrib.get('path') is not None:
                        self.fixities[-1].update({'path': fix.attrib.get('path')})
            self.descriptive_metadata_elm = self.tree.find(f'.//{{{self.opexns}}}DescriptiveMetadata') if self.tree.find(f'.//{{{self.opexns}}}DescriptiveMetadata') is not None else None
            self.descriptive_metadata = etree.tostring(self.descriptive_metadata_elm) if self.descriptive_metadata_elm is not None else None
        except etree.ParseError as e:
            logger.exception(f'Failed to parse OPEX XML file: {e}')
            raise
        except FileNotFoundError as e:
            logger.exception(f'OPEX XML file not found: {e}')
            raise

    def verify_opex_version(self, expected_version: str = "1.2") -> bool:
        try:
            opexnsmap = self.tree.getroot().nsmap
            opexns = opexnsmap.get('opex')
            version = opexns.split('/')[-1]
            if version == expected_version:
                return True
            else:
                logger.warning(f'OPEX version mismatch: expected {expected_version}, found {version}')
                return False
        except Exception as e:
            logger.exception(f'Error verifying OPEX version: {e}')
            raise

    def __str__(self, *args, **kwds):
        return f"OPEX File Reader for: {self.file_path}" \
        f"\nTitle: {self.title}" \
        f"\nDescription: {self.description}" \
        f"\nSecurity Descriptor: {self.security}" \
        f"\nSourceID: {self.sourceid}" \
        f"\nIdentifiers: {self.identifiers}"

    def __repr__(self):
        return self.__str__()

    def get_fixities(self) -> dict:
        return self.fixities

    def get_descriptive_metadata(self) -> str:
        return str(self.descriptive_metadata)

    def get_title(self) -> str:
        return self.title

    def get_description(self) -> str:
        return self.description

    def get_security_descriptor(self) -> str:
        return self.security

    def get_identifiers(self) -> dict:
        return self.identifiers

    def get_sourceid(self) -> str:
        return self.sourceid

    def to_string(self) -> str:
        return etree.tostring(self.tree, pretty_print=True, xml_declaration=True, encoding="UTF-8", standalone=True).decode('UTF-8')
    
    def to_element(self) -> etree._Element:
        return self.tree.getroot()
    
    def to_tree(self) -> etree._ElementTree:
        return self.tree
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "security_descriptor": self.security,
            "sourceid": self.sourceid,
            "identifiers": self.identifiers,
            "fixities": self.fixities,
            "descriptive_metadata": str(self.descriptive_metadata)
        }

class OpexFileWriter():
    def __init__(self, file_path: str, title: str = None, description: str = None, security_tag: str = None, opexns: str = "http://www.openpreservationexchange.org/opex/v1.2", **kwargs) -> None:

        self.opexns = opexns

        if file_path.startswith(u'\\\\?\\'):
            self.file_path = file_path.replace(u'\\\\?\\', "")
        else:
            self.file_path = file_path

        self.opex_root = etree.Element(f"{{{self.opexns}}}OPEXMetadata", nsmap={"opex":self.opexns})
        self.transfer_opex = etree.SubElement(self.opex_root, f"{{{self.opexns}}}Transfer")

        self.sourceid = kwargs.get('sourceid', None)
        if self.sourceid is not None:
            self.sourceid_opex = etree.SubElement(self.transfer_opex,f"{{{self.opexns}}}SourceID")
            self.sourceid_opex.text = self.sourceid

        self.generate_fixity: list = kwargs.get('generate_fixity', None)
        self.fixity_list: list[Dict] = kwargs.get('fixity', None)

        if self.generate_fixity is not None and self.fixity_list is not None:
            logger.warning('Both generate_fixity and fixity arguments provided. Will use fixity_list and ignore generation.')
            self.generate_fixity = None
        if self.generate_fixity is not None and len(self.generate_fixity) > 0 and (not self.file_path.endswith('.pax') and not self.file_path.endswith('pax.zip')):
            self.fixities_opex = etree.SubElement(self.transfer_opex, f"{{{self.opexns}}}Fixities")
            for fix in self.generate_fixity:
                hash_value = HashGenerator(algorithm = fix, buffer = kwargs.get('buffer', 4096)).hash_generator(self.file_path)
                self.fixity_opex = etree.SubElement(self.fixities_opex, f"{{{self.opexns}}}Fixity")
                self.fixity_opex.set("type", fix)
                self.fixity_opex.set("value", hash_value)
        elif kwargs.get('pax_flag', False) is True and self.generate_fixity is not None and len(self.generate_fixity) > 0 and (self.file_path.endswith('.pax') or self.file_path.endswith('pax.zip')):
            self.fixities_opex = etree.SubElement(self.transfer_opex, f"{{{self.opexns}}}Fixities")
            for fix in self.generate_fixity:
                with zipfile.ZipFile(self.file_path, 'r') as z:
                    for zfile in z.filelist:
                        hash_value = HashGenerator(algorithm = fix, buffer = kwargs.get('buffer', 4096)).hash_generator_pax_zip(zfile, z)
                        self.fixity_opex = etree.SubElement(self.fixities_opex, f"{{{self.opexns}}}Fixity")
                        self.fixity_opex.set("path", zfile.filename.replace('\\', '/'))
                        self.fixity_opex.set("type", fix)
                        self.fixity_opex.set("value", hash_value)
        if self.fixity_list is not None and len(self.fixity_list) > 0:
            self.fixities_opex = etree.SubElement(self.transfer_opex, f"{{{self.opexns}}}Fixities")
            for fix in self.fixity_list:
                if isinstance(fix, dict):
                    self.fixity_opex = etree.SubElement(self.fixities_opex, f"{{{self.opexns}}}Fixity")
                    if fix.get("path") is not None:
                        self.fixity_opex.set("path", fix.get("path", None))
                    self.fixity_opex.set("type", fix.get("type", None))
                    self.fixity_opex.text = fix.get("value", None)

        if title is not None:
            self.title = title
        else:
            self.title = None
        if description is not None:
            self.description = description
        else:
            self.description = None
        if security_tag is not None:
            self.security_tag = security_tag
        else:
            self.security_tag = None

        self.identifiers: list = kwargs.get('identifiers', None)

        if any([self.title, self.description, self.security_tag, self.identifiers]):
            self.properties_opex = etree.SubElement(self.opex_root, f"{{{self.opexns}}}Properties")
            if self.title is not None:
                self.title_opex = etree.SubElement(self.properties_opex, f"{{{self.opexns}}}Title")
                self.title_opex.text = str(self.title)
            if self.description is not None:
                self.description_opex = etree.SubElement(self.properties_opex, f"{{{self.opexns}}}Description")
                self.description_opex.text = str(self.description)
            if self.security_tag is not None:
                self.security_tag_opex = etree.SubElement(self.properties_opex, f"{{{self.opexns}}}SecurityDescriptor")
                self.security_tag_opex.text = str(self.security_tag)
            if self.identifiers is not None and isinstance(self.identifiers, list) and len(self.identifiers) > 0:
                self.identifiers_opex = etree.SubElement(self.properties_opex, f"{{{self.opexns}}}Identifiers")
                for ident in self.identifiers:
                    self.ident_opex = etree.SubElement(self.identifiers_opex, f"{{{self.opexns}}}Identifier")
                    hash_type = ident.get("type", None)
                    hash_value = ident.get("value", None)
                    if hash_type is not None and hash_value is not None:
                        self.ident_opex.set("type", hash_type)
                        self.ident_opex.text = str(hash_value)

        self.descriptive_metadata: Union[str, etree._ElementTree, etree._Element] = kwargs.get('descriptive_metadata', None)
        if self.descriptive_metadata is not None:
            self.descmeta_opex = etree.SubElement(self.opex_root, f"{{{self.opexns}}}DescriptiveMetadata")
            if isinstance(self.descriptive_metadata, str):
                try:
                    self.descmeta_opex.append(etree.fromstring(self.descriptive_metadata))
                except etree.ParseError as e:
                    logger.exception(f'Failed to parse descriptive metadata XML string: {e}')
                    raise
            elif isinstance(self.descriptive_metadata, str) and self.descriptive_metadata.endswith('.xml'):
                try:
                    tree = etree.parse(self.descriptive_metadata)
                    self.descmeta_opex.append(tree.getroot())
                except (etree.ParseError, FileNotFoundError) as e:
                    logger.exception(f'Failed to parse descriptive metadata XML file: {e}')
                    raise
            elif isinstance(self.descriptive_metadata, (etree._Element, etree._ElementTree)):
                try:
                    self.descmeta_opex.append(self.descriptive_metadata)
                except etree.ParseError as e:
                    logger.exception(f'Failed to parse descriptive metadata XML tree: {e}')
                    raise

    def generate_opex(self) -> etree._Element:
        return self.opex_root

    def generate_opex_str(self) -> str:
        return etree.tostring(self.opex_root, pretty_print=True, xml_declaration=True, encoding="UTF-8", standalone=True)

    def write_opex_file(self, opex_path: str = None, file_override: bool = False) -> str:
        if opex_path is None:
            opex_path = win_256_check(self.file_path + ".opex")
        else:
            opex_path = win_256_check(opex_path)
        if os.path.exists(opex_path) and file_override is False:
            logger.warning(f"Opex file already exists at: {opex_path}, skipping write.")
            return None
        else:
            opex = etree.tostring(self.opex_root, pretty_print=True, xml_declaration=True, encoding="UTF-8", standalone=True)
            try:
                with open(f'{opex_path}', 'w', encoding="UTF-8") as writer:
                    logger.info(f'Writing OPEX manifest to: {opex_path}')
                    writer.write(opex.decode('UTF-8'))
                return opex_path
            except (PermissionError, OSError) as e:
                logger.exception(f'Failed to write OPEX file: {e}')
                raise

    def zip_opex_file(self, compression = zipfile.ZIP_STORED, remove_files: bool = False) -> str:
        zip_file = f"{self.file_path}.zip"
        if not os.path.exists(zip_file):
            with zipfile.ZipFile(zip_file,'w',compression=compression) as z:
                if os.path.exists(self.file_path):
                    z.write(self.file_path, os.path.basename(self.file_path))
                opex_path = self.write_opex_file()
                if opex_path is not None and os.path.exists(opex_path):
                    z.write(opex_path, os.path.basename(opex_path), )
            logger.debug(f'File has been zipped to: {zip_file}')
        else:
            logger.warning(f'A Zip file already exists for: {zip_file}')
        if remove_files:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
                logger.debug(f'Zip Removed file: {self.file_path}')
            opex_path = str(self.file_path) + ".opex"
            if os.path.exists(opex_path):
                os.remove(opex_path)
                logger.debug(f'Zip Removed opex: {opex_path}')
        return zip_file
