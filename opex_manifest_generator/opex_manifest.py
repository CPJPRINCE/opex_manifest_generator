"""
Opex Manifest Generator tool

This tool is utilised to recusrively generate Opex files for files / directories for use in uploading to Preservica and other OPEX conformin systems.

author: Christopher Prince
license: Apache License 2.0"
"""

import lxml.etree as ET
import pandas as pd
import os, time, datetime
from auto_classification_generator import ClassificationGenerator
from auto_classification_generator.common import export_list_txt, export_xl, export_csv, define_output_file
from pandas.api.types import is_datetime64_any_dtype
from opex_manifest_generator.hash import HashGenerator
from opex_manifest_generator.common import *
import configparser

class OpexManifestGenerator():
    """
    A tool for recusrively generating Opex files for files / directories for use in uploading to Preservica and other OPEX conformin systems.

    :param root: the directory to generate opexes for
    :param output_path: set the output path for geerated metadata (not opexes)
    :param meta_dir_flag: set whether to generate a 'meta' directory
    :param metadata_flag: set whether to incorporate metadata into opex
    :param metadata_dir: set the metadata directory to pull xml data from
    :param autoclass_flag: set whether to generate an auto classification reference using auto_class. Has a number of 'modes' {catalog, accession, both, generic}
    :param prefix: set a prefix to append to generated references
    :param accession_mode: if using accession in autoclass_flag set the mode to count {file, folder, both}
    :param acc_prefix: set an accession prefix
    :param startref: set to set the starting reference number
    :param algorithm: set whether to generate fixities and the algorithm to use {MD5, SHA-1, SHA-256, SHA-512}
    :param empty_flag: set whether to delete and log empty directories
    :param removal_flag: set whether to enable removals; data must also contain removals column and cell be set to True 
    :param clear_opex_flag: set whether clear existing opexes
    :param export_flag: set whether to export the spreadsheet when using autoclass
    :param output_format: set output format when using autoclass {xlsx, csv}
    :param input: set whether to use an AutoClass spreadsheet / dataframe to establish data.
    :param zip_flag: set whether to zip files and opexes together
    :param hidden_flag: set to include hidden files/directories
    :param print_xmls_flag: set to print all 
    :param options_file: set to specify options file
    :param keywords: set to replace numbers in reference with alphabetical characters, specified in list or all if unset
    :param keywords_mode: set to specify keywords mode [intialise, firstletters] 
    :param keywords_retain_order: set to continue counting reference, if keyword is used, skips numbers if not
    :param sort_key: set the sort key, can be any valid function for sorted
    :param keywords_abbreviation: set int for number of characters to abbreviate to for keywords mode
    """
    def __init__(self,
                 root: str,
                 output_path: str = os.getcwd(),
                 meta_dir_flag: bool = True,
                 metadata_dir: str = os.path.join(os.path.dirname(os.path.realpath(__file__)), "metadata"),
                 metadata_flag: str = 'none',
                 autoclass_flag: str = None,
                 prefix: str = None,
                 acc_prefix: str = None,
                 accession_mode: str = False,
                 startref: int = 1,
                 algorithm: list[str] = None,
                 pax_fixity: bool = False,
                 empty_flag: bool = False,
                 removal_flag: bool = False,
                 clear_opex_flag: bool = False,
                 export_flag: bool = False,
                 input: str = None,
                 zip_flag: bool = False,
                 hidden_flag: bool = False,
                 output_format: str = "xlsx",
                 print_xmls_flag: bool = False,
                 options_file: str = os.path.join(os.path.dirname(__file__),'options.properties'),
                 keywords: list = None,
                 keywords_mode: str = "intitalise",
                 keywords_retain_order: bool = False,
                 sort_key = lambda x: (os.path.isfile(x), str.casefold(x)),
                 keywords_abbreviation_number: int = 3,
                 delimiter = "/"):
        
        self.root = os.path.abspath(root)
        self.opexns = "http://www.openpreservationexchange.org/opex/v1.2"        
        self.list_path = []
        self.list_fixity = []
        self.start_time = datetime.datetime.now()
        self.algorithm = algorithm
        self.pax_fixity_flag = pax_fixity
        self.empty_flag = empty_flag
        self.removal_flag = removal_flag
        if self.removal_flag:
            self.removal_list = []
        self.export_flag = export_flag
        self.startref = startref
        self.autoclass_flag = autoclass_flag
        self.output_path = output_path
        self.clear_opex_flag = clear_opex_flag
        self.meta_dir_flag = meta_dir_flag
        self.prefix = prefix
        self.acc_prefix = acc_prefix
        self.accession_mode = accession_mode
        self.input = input
        self.hidden_flag = hidden_flag
        self.zip_flag = zip_flag
        self.output_format = output_format
        self.metadata_flag = metadata_flag
        self.metadata_dir = metadata_dir
        self.print_xmls_flag = print_xmls_flag
        self.parse_config(options_file=os.path.abspath(options_file))
        self.keywords_list = keywords
        self.keywords_mode = keywords_mode
        self.keywords_retain_order = keywords_retain_order
        self.sort_key = sort_key
        self.keywords_abbreviation_number = keywords_abbreviation_number
        self.delimiter = delimiter

        self.title_flag = False
        self.description_flag = False
        self.security_flag = False
        self.ignore_flag = False
        self.sourceid_flag = False
        self.hash_from_spread = False
    
    def parse_config(self, options_file: str = 'options.properties'):
        config = configparser.ConfigParser()
        config.read(options_file, encoding='utf-8')
        global INDEX_FIELD
        INDEX_FIELD = config['options']['INDEX_FIELD']
        global TITLE_FIELD
        TITLE_FIELD = config['options']['TITLE_FIELD']
        global DESCRIPTION_FIELD
        DESCRIPTION_FIELD = config['options']['DESCRIPTION_FIELD']
        global SECUIRTY_FIELD
        SECUIRTY_FIELD = config['options']['SECUIRTY_FIELD']
        global IDENTIFIER_FIELD
        IDENTIFIER_FIELD = config['options']['IDENTIFIER_FIELD']
        global IDENTIFIER_DEFAULT
        IDENTIFIER_DEFAULT = config['options']['IDENTIFIER_DEFAULT']
        global REMOVAL_FIELD
        REMOVAL_FIELD = config['options']['REMOVAL_FIELD']
        global IGNORE_FIELD
        IGNORE_FIELD = config['options']['IGNORE_FIELD']
        global SOURCEID_FIELD
        SOURCEID_FIELD = config['options']['SOURCEID_FIELD']
        global HASH_FIELD
        HASH_FIELD = config['options']['HASH_FIELD']
        global ALGORITHM_FIELD
        ALGORITHM_FIELD = config['options']['ALGORITHM_FIELD']

    def print_descriptive_xmls(self):
        for file in os.scandir(self.metadata_dir):
            path = os.path.join(self.metadata_dir, file.name)
            print(path)
            xml_file = ET.parse(path)
            root_element = ET.QName(xml_file.find('.'))
            root_element_ln = root_element.localname
            for elem in xml_file.findall(".//"):
                if elem.getchildren():
                    pass
                else:
                    elem_path = xml_file.getelementpath(elem)
                    elem = ET.QName(elem)
                    elem_lnpath = elem_path.replace(f"{{{elem.namespace}}}", root_element_ln + ":")
                    print(elem_lnpath)
    
    def set_input_flags(self):
        if TITLE_FIELD in self.column_headers:
            self.title_flag = True
        if DESCRIPTION_FIELD in self.column_headers:
            self.description_flag = True
        if SECUIRTY_FIELD in self.column_headers:
            self.security_flag = True
        if SOURCEID_FIELD in self.column_headers:
            self.sourceid_flag = True
        if IGNORE_FIELD in self.column_headers:
            self.ignore_flag = True
        if HASH_FIELD in self.column_headers and ALGORITHM_FIELD in self.column_headers:
            self.hash_from_spread = True
            print("Hash detected in Spreadsheet; taking hashes from spreadsheet")
            time.sleep(3)

    def init_df(self):
        if self.autoclass_flag:
            ac = ClassificationGenerator(self.root,
                                            output_path = self.output_path,
                                            prefix = self.prefix,
                                            accprefix = self.acc_prefix,
                                            start_ref = self.startref,
                                            empty_flag = self.empty_flag,
                                            accession_flag=self.accession_mode,
                                            keywords = self.keywords_list,
                                            keywords_mode = self.keywords_mode,
                                            keywords_retain_order = self.keywords_retain_order,
                                            sort_key = self.sort_key,
                                            keywords_abbreviation_number = self.keywords_abbreviation_number,
                                            delimiter = self.delimiter)
            self.df = ac.init_dataframe()
            if self.autoclass_flag in {"accession", "a", "accesion-generic", "ag"}:
                self.df = self.df.drop('Archive_Reference', axis=1)
            self.column_headers = self.df.columns.values.tolist()
            self.set_input_flags()
            if self.export_flag:
                output_path = define_output_file(self.output_path, self.root, meta_dir_flag = self.meta_dir_flag, output_format = self.output_format)                
                if self.output_format == "xlsx":
                    export_xl(self.df, output_path)
                elif self.output_format == "csv":
                    export_csv(self.df, output_path)
        elif self.input:
            if self.input.endswith('xlsx'):
                self.df = pd.read_excel(self.input)
            elif self.input.endswith('csv'):
                self.df = pd.read_csv(self.input)
            self.column_headers = self.df.columns.values.tolist()
            self.set_input_flags()
        else:
            self.df = None
            self.column_headers = None
                
    def clear_opex(self):
        walk = list(os.walk(self.root))
        for dir, _, files in walk[::-1]:
            for file in files:
                file_path = win_256_check(os.path.join(dir, file))   
                if str(file_path).endswith('.opex'):
                    os.remove(file_path)
                    print(f'Cleared Opex: {file_path}')
    
    def index_df_lookup(self, path: str):
        idx = self.df[INDEX_FIELD].index[self.df[INDEX_FIELD] == path]
        return idx

    def xip_df_lookup(self, idx: pd.Index):
        try:
            title = None
            description = None
            security = None
            if idx.empty:
                pass
            else:
                if self.title_flag:
                    title = check_nan(self.df[TITLE_FIELD].loc[idx].item())
                if self.description_flag:
                    description = check_nan(self.df[DESCRIPTION_FIELD].loc[idx].item())
                if self.security_flag:
                    security = check_nan(self.df[SECUIRTY_FIELD].loc[idx].item())
            return title,description,security
        except Exception as e:
            print('Error Looking up XIP Metadata')
            print(e)
    
    def removal_df_lookup(self, idx: pd.Index):
        try:
            if idx.empty:
                return False
            else:
                remove = check_nan(self.df[REMOVAL_FIELD].loc[idx].item())
                if remove is not None:
                    return True
                else:
                    return False
        except Exception as e:
            print('Error looking up Removals')
            print(e)

    def ignore_df_lookup(self, idx: pd.Index):
        try:
            if idx.empty:
                return False
            else:
                ignore = check_nan(self.df[IGNORE_FIELD].loc[idx].item())
            return bool(ignore)
        except Exception as e:
            print('Error looking up Ignore')
            print(e)

    def sourceid_df_lookup(self, xml_element: ET.SubElement, idx: pd.Index):
        try:
            if idx.empty:
                pass
            else:
                sourceid = check_nan(self.df[SOURCEID_FIELD].loc[idx].item())
                if sourceid:
                    source_xml = ET.SubElement(xml_element,f"{{{self.opexns}}}SourceID")
                    source_xml.text = str(sourceid)
        except Exception as e:
            print('Error looking up SourceID')
            print(e)

    def hash_df_lookup(self, xml_fixities: ET.SubElement, idx: pd.Index):
        try:
            if idx.empty:
                pass
            else:
                for algorithm_type in self.algorithm:
                    self.fixity = ET.SubElement(xml_fixities,f"{{{self.opexns}}}Fixity")  
                    self.hash = self.df[HASH_FIELD].loc[idx].item()
                    self.algorithm = self.df[ALGORITHM_FIELD].loc[idx].item()
                    self.fixity.set('type', algorithm_type)
                    self.fixity.set('value',self.hash)
        except Exception as e:
            print('Error looking up Hash')
            print(e)

    def ident_df_lookup(self, idx: pd.Index, default_key: str = None):
        try:
            if idx.empty:
                pass
            else:
                for header in self.column_headers:
                    ident = None
                    if any(s in header for s in {IDENTIFIER_FIELD,'Archive_Reference','Accession_Reference'}):
                        if f'{IDENTIFIER_FIELD}:' in header:
                            key_name = str(header).split(':',1)[-1]
                        elif IDENTIFIER_FIELD in header:
                            key_name = IDENTIFIER_DEFAULT    
                        elif 'Archive_Reference' in header:
                            key_name = IDENTIFIER_DEFAULT
                        elif 'Accession_Reference' in header:
                            key_name = "accref"
                        else:
                            key_name = IDENTIFIER_DEFAULT
                        ident = check_nan(self.df[header].loc[idx].item())                    
                        if ident:
                            self.identifier = ET.SubElement(self.identifiers, f"{{{self.opexns}}}Identifier") 
                            self.identifier.set("type", key_name)
                            self.identifier.text = str(ident)
        except Exception as e:
            print('Error looking up Identifiers')
            print(e)            

    def init_generate_descriptive_metadata(self):
        self.xml_files = []
        for file in os.scandir(self.metadata_dir):
            if file.name.endswith('xml'):
                """
                Generates info on the elements of the XML Files placed in the Metadata directory.
                Composed as a list of dictionaries.
                """
                path = os.path.join(self.metadata_dir, file)
                xml_file = ET.parse(path)
                root_element = ET.QName(xml_file.find('.'))
                root_element_ln = root_element.localname
                #root_element_ns = root_element.namespace
                elements_list = []
                for elem in xml_file.findall('.//'):
                    elem_path = xml_file.getelementpath(elem)
                    elem = ET.QName(elem)
                    elem_ln = elem.localname
                    elem_ns = elem.namespace
                    elem_lnpath = elem_path.replace(f"{{{elem_ns}}}", root_element_ln + ":")
                    elements_list.append({"Name": root_element_ln + ":" + elem_ln, "Namespace": elem_ns, "Path": elem_lnpath})

                """
                Compares the column headers in the Spreadsheet against the headers. Filters out non-matching data.
                """
                list_xml = []
                for elem_dict in elements_list:
                    if elem_dict.get('Name') in self.column_headers or elem_dict.get('Path') in self.column_headers:
                        list_xml.append({"Name": elem_dict.get('Name'), "Namespace": elem_dict.get('Namespace'), "Path": elem_dict.get('Path')})
            if len(list_xml) > 0:
                self.xml_files.append({'data': list_xml, 'localname': root_element_ln, 'xmlfile': path})

    def generate_descriptive_metadata(self, xml_desc_elem: ET.Element, idx: pd.Index):
        """
        Composes the data into an xml file.
        """
        for xml_file in self.xml_files:
            list_xml = xml_file.get('data')
            localname = xml_file.get('localname')
            if len(list_xml) == 0:
                pass
            else:
                if idx.empty:
                    pass
                else:
                    xml_new = ET.parse(xml_file.get('xmlfile'))
                    for elem_dict in list_xml:
                        name = elem_dict.get('Name')
                        path = elem_dict.get('Path')
                        ns = elem_dict.get('Namespace')
                        try:
                            if self.metadata_flag in {'e', 'exact'}:
                                val_series = self.df[path].loc[idx]
                                val = check_nan(val_series.item())
                            elif self.metadata_flag in {'f', 'flat'}:
                                val_series = self.df[name].loc[idx]
                                val = check_nan(val_series.item())
                            if val is None:
                                continue
                            else:
                                if is_datetime64_any_dtype(val_series):
                                    val = pd.to_datetime(val)
                                    val = datetime.datetime.strftime(val, "%Y-%m-%dT%H:%M:%S.000Z")
                            if self.metadata_flag in {'e','exact'}:
                                n = path.replace(localname + ":", f"{{{ns}}}")
                                elem = xml_new.find(f'./{n}')
                            elif self.metadata_flag in {'f', 'flat'}:
                                n = name.split(':')[-1]
                                elem = xml_new.find(f'.//{{{ns}}}{n}')
                            elem.text = str(val)
                        except KeyError as e:
                            print('Key Error: please ensure column header\'s are an exact match...')
                            print(f'Missing Column: {e}')
                            print('Alternatively use flat mode...')
                            time.sleep(3)
                            raise SystemExit()
                        except IndexError as e:
                            print("""Index Error; it is likely you have removed or added a file/folder to the directory \
                                after generating the spreadsheet. An opex will still be generated but with no xml metadata. \
                                To ensure metadata match up please regenerate the spreadsheet...""")
                            print(f'Error: {e}')
                            time.sleep(3)
                            break
                    xml_desc_elem.append(xml_new.find('.'))

    def generate_opex_properties(self, xmlroot: ET.Element, idx: int, title: str = None,
                                  description: str = None, security: str = None):
        self.properties = ET.SubElement(xmlroot, f"{{{self.opexns}}}Properties")
        if title:
            self.titlexml = ET.SubElement(self.properties, f"{{{self.opexns}}}Title")
            self.titlexml.text = str(title)
        if description:
            self.descriptionxml = ET.SubElement(self.properties, f"{{{self.opexns}}}Description")
            self.descriptionxml.text = str(description)      
        if security:
            self.securityxml = ET.SubElement(self.properties, f"{{{self.opexns}}}SecurityDescriptor")
            self.securityxml.text = str(security)
        if self.autoclass_flag not in {"generic", "g"} or self.input:
            self.identifiers = ET.SubElement(self.properties, f"{{{self.opexns}}}Identifiers")
            self.ident_df_lookup(idx)
        if self.properties is None:
            xmlroot.remove(self.properties)

    def generate_opex_fixity(self, file_path: str):
        for algorithm_type in self.OMG.algorithm:
            self.fixity = ET.SubElement(self.fixities, f"{{{self.opexns}}}Fixity")
            self.hash = HashGenerator(algorithm = algorithm_type).hash_generator(file_path)
            self.fixity.set("type", algorithm_type)
            self.fixity.set("value", self.hash)
            self.OMG.list_fixity.append([algorithm_type, self.hash, file_path])
            self.OMG.list_path.append(file_path)

    def generate_pax_zip_opex_fixity(self, file_path):
        for algorithm_type in self.OMG.algorithm:
            z = zipfile.ZipFile(file_path,'r')
            for file in z.filelist:
                self.fixity = ET.SubElement(self.fixities, f"{{{self.opexns}}}Fixity")        
                self.hash = HashGenerator(algorithm = algorithm_type).hash_generator_pax_zip(file.filename, z)
                self.fixity.set("path", file.filename)
                self.fixity.set("type", algorithm_type)
                self.fixity.set("value", self.hash)
                self.OMG.list_fixity.append([algorithm_type, self.hash, file_path + file.filename])
            self.OMG.list_path.append(file_path)

    def main(self):
        if self.print_xmls_flag:
            self.print_descriptive_xmls()
            input("Press Key to Close")
            raise SystemExit()
        print(f"Start time: {self.start_time}")        
        if self.clear_opex_flag:
            self.clear_opex()
            if self.autoclass_flag or self.algorithm or self.input:
                pass
            else:
                print_running_time(self.start_time)
                print('Cleared OPEXES. No additional arguments passed, so ending program.'); time.sleep(3)
                raise SystemExit()
        if self.empty_flag:
            ClassificationGenerator(self.root, self.output_path, meta_dir_flag = self.meta_dir_flag).remove_empty_directories()
        if not self.autoclass_flag in {"g", "generic"}:
            self.init_df()
        self.count = 1
        if not self.metadata_flag in {'none', 'n'}:
            self.init_generate_descriptive_metadata()
        OpexDir(self, self.root).generate_opex_dirs(self.root)
        if self.algorithm:
            output_path = define_output_file(self.output_path, self.root, self.meta_dir_flag, output_suffix = "_Fixities", output_format = "txt")
            export_list_txt(self.list_fixity, output_path)
        if self.removal_flag:
            output_path = define_output_file(self.output_path, self.root, self.meta_dir_flag, output_suffix = "_Removals", output_format = "txt")
            export_list_txt(self.removal_list, output_path)
        print_running_time(self.start_time)

class OpexDir(OpexManifestGenerator):
    def __init__(self, OMG: OpexManifestGenerator, folder_path: str, title: str = None, description: str = None, security: str = None):
        self.OMG = OMG
        self.root = self.OMG.root
        self.opexns = self.OMG.opexns
        if folder_path.startswith(u'\\\\?\\'):
            self.folder_path = folder_path.replace(u'\\\\?\\', "")
        else:
            self.folder_path = folder_path
        if any([self.OMG.input,
                self.OMG.autoclass_flag in {"c","catalog","a","accession","b","both","cg","catalog-generic","ag","accession-generic","bg","both-generic"},
                self.OMG.ignore_flag,
                self.OMG.removal_flag,
                self.OMG.sourceid_flag,
                self.OMG.title_flag,
                self.OMG.description_flag,
                self.OMG.security_flag]):
                index = self.OMG.index_df_lookup(self.folder_path)
        elif self.OMG.autoclass_flag in {None, "g","generic"}:
            index = None
        else:
            index = None
        self.ignore = False
        self.removal = False
        if self.OMG.ignore_flag:
            self.ignore = self.OMG.ignore_df_lookup(index)
            if self.ignore:
                return
        if self.OMG.removal_flag:
            self.removal = self.OMG.removal_df_lookup(index)
            if self.removal:
                remove_tree(self.folder_path, self.OMG.removal_list)
                return
        self.xmlroot = ET.Element(f"{{{self.opexns}}}OPEXMetadata", nsmap={"opex":self.opexns})
        self.transfer = ET.SubElement(self.xmlroot, f"{{{self.opexns}}}Transfer")
        self.manifest = ET.SubElement(self.transfer, f"{{{self.opexns}}}Manifest")
        self.folders = ET.SubElement(self.manifest, f"{{{self.opexns}}}Folders")
        self.files = ET.SubElement(self.manifest, f"{{{self.opexns}}}Files")
        if self.OMG.title_flag or self.OMG.description_flag or self.OMG.security_flag:
            self.title, self.description, self.security = self.OMG.xip_df_lookup(index) 
        elif self.OMG.autoclass_flag in {"generic", "g", "catalog-generic", "cg", "accession-generic", "ag", "both-generic", "bg"}:
            self.title = os.path.basename(self.folder_path)
            self.description = os.path.basename(self.folder_path)
            self.security = "open"
        else:
            self.title = title
            self.description = description
            self.security = security
        if self.OMG.sourceid_flag:
            self.OMG.sourceid_df_lookup(self.transfer, self.folder_path, index)
        if self.OMG.algorithm and self.OMG.pax_fixity_flag is True and self.folder_path.endswith(".pax"):
            self.fixities = ET.SubElement(self.transfer, f"{{{self.opexns}}}Fixities")
            for dir,_,files in os.walk(folder_path):
                for filename in files:
                    rel_path = os.path.relpath(dir,folder_path)
                    rel_file = os.path.join(rel_path, filename)
                    abs_file = os.path.abspath(os.path.join(dir,filename))
                    self.generate_opex_fixity(abs_file)
                    self.fixity.set("path",rel_file)
                    file = ET.SubElement(self.files, f"{{{self.opexns}}}File")
                    file.set("type", "content")
                    file.set("size", str(os.path.getsize(abs_file)))
                    file.text = str(rel_file)
        if self.OMG.autoclass_flag or self.OMG.input:
            self.OMG.generate_opex_properties(self.xmlroot, index, 
                                              title = self.title,
                                              description = self.description,
                                              security = self.security)
            if not self.OMG.metadata_flag in {'none', 'n'}:
                self.xml_descmeta = ET.SubElement(self.xmlroot,f"{{{self.opexns}}}DescriptiveMetadata")
                self.OMG.generate_descriptive_metadata(self.xmlroot, idx = index)

    def filter_directories(self, directory: str, sort_key: str = str.casefold):
        try:
            if self.OMG.hidden_flag is False:
                list_directories = sorted([win_256_check(os.path.join(directory, f.name)) for f in os.scandir(directory)
                                        if not f.name.startswith('.')
                                        and filter_win_hidden(win_256_check(os.path.join(directory, f.name))) is False
                                        and f.name != 'meta'
                                        and f.name != os.path.basename(__file__)],
                                        key=sort_key)
            elif self.OMG.hidden_flag is True:
                list_directories = sorted([os.path.join(directory, f.name) for f in os.scandir(directory) \
                                        if f.name != 'meta'
                                        and f.name != os.path.basename(__file__)],
                                        key=sort_key)
            return list_directories
        except Exception as e:
            print('Failed to Filter')
            print(e)
            raise SystemError()
        
    def generate_opex_dirs(self, path: str):
        """"
        This function loops recursively through a given directory.
        
        There are two loops to first generate Opexes for Files; 
        """    
        self = OpexDir(self.OMG, path)
        if self.OMG.algorithm and self.OMG.pax_fixity_flag is True and self.folder_path.endswith(".pax"):
            opex_path = os.path.abspath(self.folder_path)
        else:
            opex_path = os.path.join(os.path.abspath(self.folder_path), os.path.basename(self.folder_path))
        #First Loop to Generate Folder Manifest Opexes & Individual File Opexes.
        if self.removal is True:
            #If removal is True for Folder, then it will be removed - Does not need to descend.
            pass
        else:
            for f_path in self.filter_directories(path):
                if f_path.endswith('.opex'):
                    #Ignores OPEX files / directories...
                    pass
                elif os.path.isdir(f_path):
                    if self.ignore is True or \
                    (self.OMG.removal_flag is True and \
                     self.OMG.removal_df_lookup(self.OMG.index_df_lookup(f_path)) is True):
                        #If Ignore is True, or the Folder below is marked for Removal: Don't add to Opex 
                        pass
                    else:
                        #Add Folder to OPEX Manifest (doesn't get written yet...)
                        self.folder = ET.SubElement(self.folders, f"{{{self.opexns}}}Folder")
                        self.folder.text = str(os.path.basename(f_path))
                    if self.OMG.algorithm and self.OMG.pax_fixity_flag is True and self.folder_path.endswith(".pax"):
                        #If using fixity, but the folder is a PAX & using PAX Fixity: End descent. 
                        pass
                    else:
                        #Recurse Descent.
                        self.generate_opex_dirs(f_path)
                elif os.path.isfile(f_path):
                    #Processes OPEXes for individual Files: this gets written.
                    OpexFile(self.OMG, f_path)
                else:
                    print('Unknown File Type?')
                    pass
        #Second Loop to add previously generated Opexes to Folder Manifest.
        if self.removal is True or self.ignore is True:
            pass
        else:
            if check_opex(opex_path):
                #Only processing Opexes.
                for f_path in self.filter_directories(path):
                    if os.path.isfile(f_path):
                        file = ET.SubElement(self.files, f"{{{self.opexns}}}File")
                        if f_path.endswith('.opex'):
                            file.set("type", "metadata")
                        else:
                            file.set("type", "content")
                            file.set("size", str(os.path.getsize(f_path)))
                        file.text = str(os.path.basename(f_path))
                #Writes Folder OPEX 
                write_opex(opex_path, self.xmlroot)
            else:
                #Avoids Override if exists, lets you continue where left off. 
                print(f"Avoiding override, Opex exists at: {opex_path}")

class OpexFile(OpexManifestGenerator):
    def __init__(self, OMG: OpexManifestGenerator, file_path: str, title: str = None, description: str = None, security: str = None):
        self.OMG = OMG
        self.opexns = self.OMG.opexns  
        if file_path.startswith(u'\\\\?\\'):
            self.file_path = file_path.replace(u'\\\\?\\', "")
        else:
            self.file_path = file_path
        if check_opex(self.file_path):
            if any([self.OMG.input,
                    self.OMG.autoclass_flag in {"c","catalog","a","accession","b","both","cg","catalog-generic","ag","accession-generic","bg","both-generic"},
                    self.OMG.ignore_flag,
                    self.OMG.removal_flag,
                    self.OMG.sourceid_flag,
                    self.OMG.title_flag,
                    self.OMG.description_flag,
                    self.OMG.security_flag]):
                    index = self.OMG.index_df_lookup(self.file_path)
            elif self.OMG.autoclass_flag is None or self.OMG.autoclass_flag in {"g","generic"}:
                index = None
            else:
                index = None
            self.ignore = False
            self.removal = False
            if self.OMG.ignore_flag:
                self.ignore = self.OMG.ignore_df_lookup(index)
                if self.ignore:
                    return                    
            if self.OMG.removal_flag:
                self.removal = self.OMG.removal_df_lookup(index)
                if self.removal:
                    return
            if self.OMG.title_flag or self.OMG.description_flag or self.OMG.security_flag:
                self.title, self.description, self.security = self.OMG.xip_df_lookup(index) 
            elif self.OMG.autoclass_flag in {"generic", "g", "catalog-generic", "cg", "accession-generic", "ag", "both-generic", "bg"}:
                self.title = os.path.splitext(os.path.basename(self.file_path))[0]
                self.description = os.path.splitext(os.path.basename(self.file_path))[0]
                self.security = "open"
            else:
                self.title = title
                self.description = description
                self.security = security
            if self.OMG.algorithm or self.OMG.autoclass_flag or self.OMG.input:
                self.xmlroot = ET.Element(f"{{{self.opexns}}}OPEXMetadata", nsmap={"opex":self.opexns})
                self.transfer = ET.SubElement(self.xmlroot, f"{{{self.opexns}}}Transfer")
                if self.OMG.sourceid_flag:
                    self.OMG.sourceid_df_lookup(self.transfer, self.file_path)
                if self.OMG.algorithm:
                    self.fixities = ET.SubElement(self.transfer, f"{{{self.opexns}}}Fixities")
                    if self.OMG.hash_from_spread:
                        self.OMG.hash_df_lookup(self.fixities, index)  
                    else:
                        if self.OMG.pax_fixity_flag is True and (self.file_path.endswith("pax.zip") or self.file_path.endswith(".pax")):
                            self.generate_pax_zip_opex_fixity(self.file_path)
                        else:
                            self.generate_opex_fixity(self.file_path)
                if self.transfer is None:
                    self.xmlroot.remove(self.transfer)
                if self.OMG.autoclass_flag or self.OMG.input:
                    self.OMG.generate_opex_properties(self.xmlroot, index,
                                                      title = self.title,
                                                      description = self.description,
                                                      security = self.security)
                    if not self.OMG.metadata_flag in {'none','n'}:
                        self.xml_descmeta = ET.SubElement(self.xmlroot, f"{{{self.opexns}}}DescriptiveMetadata")
                        self.OMG.generate_descriptive_metadata(self.xml_descmeta, index)
                opex_path = write_opex(self.file_path, self.xmlroot)
                if self.OMG.zip_flag:
                    zip_opex(self.file_path, opex_path)
        else:
            print(f"Avoiding override, Opex exists at: {self.file_path}: ")