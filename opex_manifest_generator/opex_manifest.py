"""
Opex Manifest Generator tool

This tool is utilised to recursively generate Opex files for files / directories for use in uploading to Preservica and other OPEX conforming systems.

author: Christopher Prince
license: Apache License 2.0"
"""

from lxml import etree as ET
import pandas as pd
import os, configparser, logging, zipfile
from typing import Optional
from auto_reference_generator import ReferenceGenerator
from auto_reference_generator.common import export_list_txt, \
    export_xl, \
    export_csv, \
    export_json, \
    export_ods, \
    export_xml, \
    define_output_file
from pandas.api.types import is_datetime64_any_dtype
from opex_manifest_generator.hash import HashGenerator
from opex_manifest_generator.common import zip_opex,\
    remove_tree,\
    win_256_check,\
    filter_win_hidden,\
    check_nan,\
    check_opex,\
    write_opex
from datetime import datetime

logger = logging.getLogger(__name__)

class OpexManifestGenerator():
    """
    A tool for recursively generating Opex files for files / directories for use in uploading to Preservica and other OPEX conforming systems.

    :param root: the directory to generate opexes for
    :param output_path: set the output path for generated metadata (not opexes)
    :param meta_dir_flag: set whether to generate a 'meta' directory
    :param metadata_flag: set whether to incorporate metadata into opex
    :param metadata_dir: set the metadata directory to pull xml data from
    :param autoref_flag: set whether to generate an auto reference reference using autoref. Has a number of 'modes' {catalog, accession, both, generic}
    :param prefix: set a prefix to append to generated references
    :param accession_mode: if using accession in autoref_flag set the mode to count {file, folder, both}
    :param acc_prefix: set an accession prefix
    :param start_ref: set to set the starting reference number
    :param algorithm: set whether to generate fixities and the algorithm to use {MD5, SHA-1, SHA-256, SHA-512}
    :param empty_flag: set whether to delete and log empty directories
    :param removal_flag: set whether to enable removals; data must also contain removals column and cell be set to True 
    :param clear_opex_flag: set whether clear existing opexes
    :param export_flag: set whether to export the spreadsheet when using autoref
    :param output_format: set output format when using autoref {xlsx, csv,ods,json,lxml}
    :param input: set whether to use an autoref spreadsheet / dataframe to establish data.
    :param zip_flag: set whether to zip files and opexes together
    :param hidden_flag: set to include hidden files/directories
    :param print_xmls_flag: set to print all 
    :param options_file: set to specify options file
    :param keywords: set to replace numbers in reference with alphabetical characters, specified in list or all if unset
    :param keywords_mode: set to specify keywords mode [initialise, firstletters,from_json] 
    :param keywords_retain_order: set to continue counting reference, if keyword is used, skips numbers if not
    :param keywords_abbreviation: set int for number of characters to abbreviate to for keywords mode
    :param sort_key: set the sort key, can be any valid function for sorted
    """
    def __init__(self,
                 root: str,
                 output_path: str = os.getcwd(),
                 meta_dir_flag: bool = True,
                 metadata_dir: str = os.path.join(os.path.dirname(os.path.realpath(__file__)), "metadata"),
                 metadata_flag: Optional[str] = None,
                 autoref_flag: str = None,
                 prefix: str = None,
                 suffix: str = None,
                 suffix_option: Optional[str] = 'apply_to_files',
                 acc_prefix: str = None,
                 accession_mode: str = False,
                 start_ref: int = 1,
                 algorithm: list[str] = None,
                 pax_fixity: bool = False,
                 fixity_export_flag: bool = True,
                 empty_flag: bool = False,
                 empty_export_flag: bool = True,
                 removal_flag: bool = False,
                 removal_export_flag: bool = True,
                 clear_opex_flag: bool = False,
                 export_flag: bool = False,
                 input: str = None,
                 zip_flag: bool = False,
                 zip_file_removal: bool = False,
                 hidden_flag: bool = False,
                 output_format: str = "xlsx",
                 options_file: str = os.path.join(os.path.dirname(__file__),'options','options.properties'),
                 keywords: list = None,
                 keywords_mode: str = "initialise",
                 keywords_retain_order: bool = False,
                 keywords_case_sensitivity: bool = False,
                 keywords_abbreviation_number: int = 3,
                 sort_key = lambda x: (os.path.isfile(x), str.casefold(x)),
                 delimiter = "/",
                 autoref_options: Optional[str] = None) -> None:
        
        self.root = os.path.abspath(root)
        # Base Parameters
        self.opexns = "http://www.openpreservationexchange.org/opex/v1.2"      
        self.start_time = datetime.now()
        self.list_path = []
        self.list_fixity = []

        # Parameters for Opex Generation
        self.algorithm = algorithm
        self.fixity_export_flag = fixity_export_flag
        self.pax_fixity_flag = pax_fixity
        self.output_path = output_path
        self.clear_opex_flag = clear_opex_flag
        self.meta_dir_flag = meta_dir_flag
        self.hidden_flag = hidden_flag
        self.zip_flag = zip_flag
        self.zip_file_removal = zip_file_removal

        self.empty_flag = empty_flag
        self.empty_export_flag = empty_export_flag

        # Parameters for Input Option
        self.input = input
        self.removal_flag = removal_flag
        if self.removal_flag:
            self.removal_list = []
        self.removal_export_flag = removal_export_flag
        self.export_flag = export_flag
        self.metadata_flag = metadata_flag
        self.metadata_dir = metadata_dir

        # Parameters for Auto Reference
        self.autoref_flag = autoref_flag     
        self.autoref_options = autoref_options
        self.prefix = prefix
        self.suffix = suffix
        self.suffix_option = suffix_option
        self.start_ref = start_ref
        self.acc_prefix = acc_prefix
        self.accession_mode = accession_mode        
        self.keywords_list = keywords
        self.keywords_mode = keywords_mode
        self.keywords_retain_order = keywords_retain_order
        self.keywords_case_sensitivity = keywords_case_sensitivity
        self.keywords_abbreviation_number = keywords_abbreviation_number
        self.sort_key = sort_key
        self.delimiter = delimiter
        self.output_format = output_format

        # Input Flags
        self.title_flag = False
        self.description_flag = False
        self.security_flag = False
        self.ignore_flag = False
        self.sourceid_flag = False
        self.hash_from_spread = False

        self.parse_config(options_file=os.path.abspath(options_file))
    
    def parse_config(self, options_file: str = os.path.join('options','options.properties')) -> None:
        config = configparser.ConfigParser()
        read_config = config.read(options_file, encoding='utf-8')
        if not read_config:
            logger.warning(f"Options files not found or not reable: {options_file}. Using defaults.")
        
        section = config['options'] if 'options' in config else {}

        self.INDEX_FIELD = section.get('INDEX_FIELD', "FullName")
        self.TITLE_FIELD = section.get('TITLE_FIELD', "Title")
        self.DESCRIPTION_FIELD = section.get('DESCRIPTION_FIELD', "Description")
        self.SECURITY_FIELD = section.get('SECURITY_FIELD', "Security")
        self.IDENTIFIER_FIELD = section.get('IDENTIFIER_FIELD', "Identifier")
        self.IDENTIFIER_DEFAULT = section.get('IDENTIFIER_DEFAULT', "code")
        self.REMOVAL_FIELD = section.get('REMOVAL_FIELD', "Removals")
        self.IGNORE_FIELD = section.get('IGNORE_FIELD', "Ignore")
        self.SOURCEID_FIELD = section.get('SOURCEID_FIELD', "SourceID")
        self.HASH_FIELD = section.get('HASH_FIELD', "Hash")
        self.ALGORITHM_FIELD = section.get('ALGORITHM_FIELD', "Algorithm")
        self.ARCREF_FIELD = section.get('ARCREF_FIELD', "Archive_Reference")
        self.ACCREF_CODE = section.get('ACCREF_CODE', "Accession_Reference")
        self.ACCREF_FIELD = section.get('ACCREF_FIELD', "accref")
        self.FIXITY_SUFFIX = section.get('FIXITY_SUFFIX', "_Fixity")
        self.REMOVALS_SUFFIX = section.get('REMOVALS_SUFFIX', "_Removals")
        self.METAFOLDER = section.get('METAFOLDER', "meta")
        self.GENERIC_DEFAULT_SECURITY = section.get('GENERIC_DEFAULT_SECURITY', "open")
        logger.debug(f'Configuration set to: {[{k,v} for k,v in (section.items())]}')

    def print_descriptive_xmls(self) -> None:
        try:
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
        except Exception as e:
            logger.exception(f'Failed to print Descriptive metadta files, ensure correct path {e}')
            raise
    
    def convert_descriptive_xmls(self) -> None:
        try:
            for file in os.scandir(self.metadata_dir):
                path = os.path.join(self.metadata_dir, file.name)
                xml_file = ET.parse(path)
                root_element = ET.QName(xml_file.find('.'))
                root_element_ln = root_element.localname
                column_list = []
                for elem in xml_file.findall(".//"):
                    if elem.getchildren():
                        pass
                    else:
                        elem_path = xml_file.getelementpath(elem)
                        elem = ET.QName(elem)
                        elem_lnpath = elem_path.replace(f"{{{elem.namespace}}}", root_element_ln + ":")
                        column_list.append(elem_lnpath)
                df = pd.DataFrame(columns=column_list,index=None)
                if self.output_format == 'xlsx':
                    export_xl(df,file.name.replace('.xml','.xlsx'))
                elif self.output_format == 'ods':
                    export_ods(df,file.name.replace('.xml','.ods'))
                elif self.output_format == 'csv':
                    export_csv(df,file.name.replace('.xml','.csv'))
                elif self.output_format == 'json':
                    export_json(df,file.name.replace('.xml','.json'))
                else:
                    export_xl(df, file.name.replace('.xml','.xlsx'))
        except Exception as e:
            logger.exception(f'Failed to print Descriptive metadta files, ensure correct path {e}')
            raise

    def set_input_flags(self) -> None:
        if self.TITLE_FIELD in self.column_headers:
            self.title_flag = True
        if self.DESCRIPTION_FIELD in self.column_headers:
            self.description_flag = True
        if self.SECURITY_FIELD in self.column_headers:
            self.security_flag = True
        if self.SOURCEID_FIELD in self.column_headers:
            self.sourceid_flag = True
        if self.IGNORE_FIELD in self.column_headers:
            self.ignore_flag = True
        if self.HASH_FIELD in self.column_headers and self.ALGORITHM_FIELD in self.column_headers:
            self.hash_from_spread = True
            logger.info("Hash detected in Spreadsheet; taking hashes from spreadsheet")
        logger.debug("Flags set")

    def init_df(self) -> None:
        try:
            if self.autoref_flag:
                ar = ReferenceGenerator(self.root,
                                                output_path = self.output_path,
                                                prefix = self.prefix,
                                                accprefix = self.acc_prefix,
                                                suffix = self.suffix,
                                                suffix_options = self.suffix_option,
                                                start_ref = self.start_ref,
                                                empty_flag = self.empty_flag,
                                                accession_flag=self.accession_mode,
                                                keywords = self.keywords_list,
                                                keywords_mode = self.keywords_mode,
                                                keywords_retain_order = self.keywords_retain_order,
                                                keywords_abbreviation_number = self.keywords_abbreviation_number,
                                                keywords_case_sensitivity = self.keywords_case_sensitivity,
                                                delimiter = self.delimiter,
                                                sort_key = self.sort_key)
                self.df = ar.init_dataframe()
                if self.autoref_flag in {"accession", "a", "accession-generic", "ag"}:
                    self.df = self.df.drop(self.ARCREF_FIELD, axis=1)
                self.column_headers = self.df.columns.values.tolist()
                self.set_input_flags()
                if self.export_flag:
                    output_path = define_output_file(self.output_path, self.root, self.METAFOLDER, meta_dir_flag = self.meta_dir_flag, output_format = self.output_format)                
                    if self.output_format == "xlsx":
                        export_xl(self.df, output_path)
                    elif self.output_format == "csv":
                        export_csv(self.df, output_path)
                    elif self.output_format == "json":
                        export_json(self.df.to_dict(orient='records'), output_path)
                    elif self.output_format == "ods":
                        export_ods(self.df, output_path)
                    elif self.output_format == "xml":
                        export_xml(self.df, output_path)
                logger.debug(f'Auto Reference Dataframe initialised with columns: {self.column_headers}')
                return True
            elif self.input:
                if self.input.endswith(('.xlsx','.xls','.xlsm')):
                    self.df = pd.read_excel(self.input)
                elif self.input.endswith('.csv'):
                    self.df = pd.read_csv(self.input)
                elif self.input.endswith('.json'):
                    self.df = pd.read_json(self.input)
                elif self.input.endswith('.ods'):
                    self.df = pd.read_excel(self.input, engine='odf')
                elif self.input.endswith('.xml'):
                    self.df = pd.read_xml(self.input)
                self.column_headers = self.df.columns.values.tolist()
                self.set_input_flags()
                logger.debug(f'Input Dataframe initialised with columns: {self.column_headers}')
                return True
            else:
                logger.warning('No Auto Reference or Input file specified, proceeding without Dataframe')
                self.df = None
                self.column_headers = None
                return False
        except Exception as e:
            logger.exception(f'Failed to intialise Dataframe: {e}')       
            raise 

    def clear_opex(self) -> None:
        try:
            walk = list(os.walk(self.root))
            for dir, _, files in walk[::-1]:
                for file in files:
                    file_path = win_256_check(os.path.join(dir, file))   
                    if str(file_path).endswith('.opex'):
                        os.remove(file_path)
                        logger.info(f'Cleared Opex: {file_path}')
        except Exception as e:
            logger.exception(f'Error looking up Clearing Opex: {e}')
            raise
    
    def index_df_lookup(self, path: str) -> pd.Index:
        if getattr(self, 'df', None) is None:
            logger.error('Dataframe not initialised, cannot perform lookup')
            raise RuntimeError('Dataframe not initialised, cannot perform lookup')
        try:
            idx = self.df.loc[self.df[self.INDEX_FIELD] == path, self.INDEX_FIELD].index
            return idx
        except KeyError as e:
            logger.exception(f'Key Error in Index Lookup: {e}' \
            '\n Please ensure column header\'s are an exact match.')
            raise
        except IndexError as e:
            logger.warning(f'Index Error in Index Lookup: {e}. Proceeding...' \
            '\nIt is likely you have removed or added a file/folder to the directory' \
            '\nafter generating your input spreadsheet. An opex will still be generated but information may be missing.' \
            '\nTo ensure metadata match up please regenerate the spreadsheet.')
        except Exception as e:
            logger.exception(f'Error looking up Index from Dataframe: {e}')
            raise

    def xip_df_lookup(self, idx: pd.Index) -> tuple:
        if getattr(self, 'df', None) is None:
            logger.error('Dataframe not initialised, cannot perform lookup')
            raise RuntimeError('Dataframe not initialised, cannot perform lookup')
        try:
            title = None
            description = None
            security = None
            if idx.empty:
                pass
            else:
                if self.title_flag:
                    title = check_nan(self.df.loc[idx,self.TITLE_FIELD].item())
                if self.description_flag:
                    description = check_nan(self.df.loc[idx,self.DESCRIPTION_FIELD].item())
                if self.security_flag:
                    security = check_nan(self.df.loc[idx,self.SECURITY_FIELD].item())
            return title,description,security
        except KeyError as e:
            logger.exception(f'Key Error in Removal Lookup: {e}'
            '\n Please ensure column header\'s are an exact match.')
            raise
        except IndexError as e:
            logger.warning(f'Index Error in Removal Lookup: {e}. Proceeding...'
            '\nIt is likely you have removed or added a file/folder to the directory'
            '\nafter generating your input spreadsheet. An opex will still be generated, but information may be missing.'
            '\nTo ensure metadata match up please regenerate the spreadsheet.')
        except Exception as e:
            logger.exception(f'Error looking up XIP from Dataframe: {e}')
            raise
    
    def removal_df_lookup(self, idx: pd.Index) -> bool:
        if getattr(self, 'df', None) is None:
            logger.error('Dataframe not initialised, cannot perform lookup')
            raise RuntimeError('Dataframe not initialised, cannot perform lookup')        
        try:
            if idx.empty:
                return False
            else:
                remove = check_nan(self.df.loc[idx,self.REMOVAL_FIELD].item())
                if remove is not None:
                    return True
                else:
                    return False
        except KeyError as e:
            logger.exception(f'Key Error in Removal Lookup: {e}'
            '\n Please ensure column header\'s are an exact match.')
            raise
        except IndexError as e:
            logger.warning(f'Index Error in Removal Lookup: {e}. Proceeding...'
            '\nIt is likely you have removed or added a file/folder to the directory'
            '\nafter generating your input spreadsheet. An opex will still be generated, but information may be missing.'
            '\nTo ensure metadata match up please regenerate the spreadsheet.')
        except Exception as e:
            logger.exception(f'Error looking up Removals from Dataframe: {e}')
            raise

    def ignore_df_lookup(self, idx: pd.Index) -> bool:
        if getattr(self, 'df', None) is None:
            logger.error('Dataframe not initialised, cannot perform lookup')
            raise RuntimeError('Dataframe not initialised, cannot perform lookup')        
        try:
            if idx.empty:
                return False
            else:
                ignore = check_nan(self.df.loc[idx,self.IGNORE_FIELD].item())
            return bool(ignore)
        except KeyError as e:
            logger.exception(f'Key Error in Ignore Lookup: {e}'
            '\n Please ensure column header\'s are an exact match.')
            raise
        except IndexError as e:
            logger.warning(f'Index Error in Ignore Lookup: {e}. Proceeding...'
            '\nIt is likely you have removed or added a file/folder to the directory'
            '\nafter generating your input spreadsheet. An opex will still be generated but information may be missing.'
            '\nTo ensure metadata match up please regenerate the spreadsheet.')
        except Exception as e:
            logger.exception(f'Error looking up Ignore from Dataframe: {e}')
            return False

    def sourceid_df_lookup(self, xml_element: ET.SubElement, idx: pd.Index) -> None:
        if getattr(self, 'df', None) is None:
            logger.error('Dataframe not initialised, cannot perform lookup')
            raise RuntimeError('Dataframe not initialised, cannot perform lookup')        
        try:
            if idx.empty:
                pass
            else:
                sourceid = check_nan(self.df.loc[idx,self.SOURCEID_FIELD].item())
                if sourceid:
                    source_xml = ET.SubElement(xml_element,f"{{{self.opexns}}}SourceID")
                    source_xml.text = str(sourceid)
        except KeyError as e:
            logger.exception(f'Key Error in SourceID Lookup: {e}'
            '\n Please ensure column header\'s are an exact match.')
            raise
        except IndexError as e:
            logger.warning(f'Index Error in SourceID Lookup: {e}. Proceeding...'
            '\nIt is likely you have removed or added a file/folder to the directory'
            '\nafter generating your input spreadsheet. An opex will still be generated but information may be missing.'
            '\nTo ensure metadata match up please regenerate the spreadsheet.')
        except Exception as e:
            logger.exception(f'Error looking up SourceID from Dataframe: {e}')
            raise

    def hash_df_lookup(self, xml_fixities: ET.SubElement, idx: pd.Index) -> None:
        if getattr(self, 'df', None) is None:
            logger.error('Dataframe not initialised, cannot perform lookup')
            raise RuntimeError('Dataframe not initialised, cannot perform lookup')        
        try:
            hash_value = None
            algo_value = None
            file_path = None
            
            if idx.empty:
                return
            else:
                # prefer the algorithm specified in the spreadsheet for this row
                if not self.column_headers or (self.HASH_FIELD not in self.column_headers and self.ALGORITHM_FIELD not in self.column_headers):
                   return
                hash_value = check_nan(self.df.loc[idx, self.HASH_FIELD].item())
                algo_value = check_nan(self.df.loc[idx, self.ALGORITHM_FIELD].item())
                file_path = check_nan(self.df.loc[idx, self.INDEX_FIELD].item()) if self.INDEX_FIELD in self.column_headers else None

            if algo_value is not None:
                self.fixity = ET.SubElement(xml_fixities, f"{{{self.opexns}}}Fixity")
                self.fixity.set('type', algo_value)
                self.fixity.set('value', str(hash_value))
                logger.debug(f'Using Algorithm from Spreadsheet: {algo_value} with Hash: {hash_value}')

            else:
                if file_path is not None:
                    # fallback to configured algorithms
                    logger.debug('No Algorithm specified in Spreadsheet for this entry; ')
                    if file_path.endswith('.pax.zip') or file_path.endswith('.pax'):
                        self.generate_pax_zip_opex_fixity(file_path, self.algorithm, self.list_fixity)
                    else:
                        self.generate_opex_fixity(file_path, self.algorithm, self.list_fixity)
        except KeyError as e:
            logger.exception(f'Key Error in Hash Lookup: {e}'
            '\n Please ensure column header\'s are an exact match.')
            raise
        except IndexError as e:
            logger.warning(f'Index Error in Hash Lookup: {e}. Proceeding...'
            '\nIt is likely you have removed or added a file/folder to the directory'
            '\nafter generating your input spreadsheet. An opex will still be generated but information may be missing.'
            '\nTo ensure metadata match up please regenerate the spreadsheet.')
        except Exception as e:
            logger.exception(f'Error looking up Hash from Dataframe: {e}')
            raise

    def ident_df_lookup(self, idx: pd.Index, default_key: str = None) -> None:
        if getattr(self, 'df', None) is None:
            logger.error('Dataframe not initialised, cannot perform lookup')
            raise RuntimeError('Dataframe not initialised, cannot perform lookup')        
        try:
            if idx.empty:
                pass
            else:
                for header in self.column_headers:
                    ident = None
                    if any(s in header for s in {self.IDENTIFIER_FIELD,self.ARCREF_FIELD,self.ACCREF_FIELD}):
                        if f'{self.IDENTIFIER_FIELD}:' in header:
                            key_name = str(header).split(':',1)[-1]
                        elif self.IDENTIFIER_FIELD in header:
                            key_name = self.IDENTIFIER_DEFAULT    
                        elif self.ARCREF_FIELD in header:
                            key_name = self.IDENTIFIER_DEFAULT
                        elif self.ACCREF_FIELD in header:
                            key_name = self.ACCREF_CODE
                        else:
                            key_name = self.IDENTIFIER_DEFAULT
                        ident = check_nan(self.df.loc[idx,header].item())                    
                        if ident:
                            self.identifier = ET.SubElement(self.identifiers, f"{{{self.opexns}}}Identifier") 
                            self.identifier.set("type", key_name)
                            self.identifier.text = str(ident)
                        logger.debug(f'Adding Identifer: {header}: {ident}')
        except KeyError as e:
            logger.exception(f'Key Error in Identifer Lookup: {e}' \
            '\n Please ensure column header\'s are an exact match.')            
            raise
        except IndexError as e:
            logger.warning(f'Index Error in Identifier Lookup: {e}. Proceeding...' \
            '\nIt is likely you have removed or added a file/folder to the directory' \
            '\nafter generating your input spreadsheet. An opex will still be generated but xml information may be missing.' \
            '\nTo ensure metadata match up please regenerate the spreadsheet.')
        except Exception as e:
            logger.exception(f'Error looking up Identifiers: {e}')    
            raise

    def init_generate_descriptive_metadata(self) -> None:
        try:
            self.xml_files = []
            for file in os.scandir(self.metadata_dir):
                list_xml = []
                if file.name.endswith('xml'):
                    """
                    Generates info on the elements of the XML Files placed in the Metadata directory.
                    Composed as a list of dictionaries.
                    """
                    path = os.path.join(self.metadata_dir, file.name)
                    try:
                        xml_file = ET.parse(path)
                    except ET.XMLSyntaxError as e:
                        logger.exception(f'XML Syntax Error parsing file {file.name}: {e}')
                        raise
                    except FileNotFoundError as e:
                        logger.exception(f'XML file not found {file.name}: {e}')
                        raise
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
                    try:
                        for elem_dict in elements_list:
                            if elem_dict.get('Name') in self.column_headers or elem_dict.get('Path') in self.column_headers:
                                list_xml.append({"Name": elem_dict.get('Name'), "Namespace": elem_dict.get('Namespace'), "Path": elem_dict.get('Path')})
                    except Exception as e:
                        logger.exception(f'Failed comparing Column headers in XML: {e}')
                        raise
                if len(list_xml) != 0:
                    self.xml_files.append({'data': list_xml, 'localname': root_element_ln, 'xmlfile': path})
                    logger.debug(f'XML file: {file.name} with matching columns added for descriptive metadata.')
                else:
                    logger.warning(f'No matching columns found in XML file: {file.name}, skipping.')
            return self.xml_files
        except FileNotFoundError as e:
            logger.exception(f'Metadata directory not found: {e}')
            raise
        except Exception as e:
            logger.exception(f'Failed to intialise XML Metadata: {e}')
            raise
    def generate_descriptive_metadata(self, xml_desc_elem: ET.Element, idx: pd.Index) -> None:
        """
        Composes the data into an xml file.
        """
        try:
            for xml_file in self.xml_files:
                list_xml = xml_file.get('data')
                localname = xml_file.get('localname')
                if len(list_xml) == 0 or idx.empty:
                    pass
                else:
                    xml_new = ET.parse(xml_file.get('xmlfile'))
                    for elem_dict in list_xml:
                        name = elem_dict.get('Name')
                        path = elem_dict.get('Path')
                        ns = elem_dict.get('Namespace')
                        if self.metadata_flag in {'e', 'exact'}:
                            val_series = self.df.loc[idx,path]
                            val = check_nan(val_series.item())
                        elif self.metadata_flag in {'f', 'flat'}:
                            val_series = self.df.loc[idx,name]
                            val = check_nan(val_series.item())
                        if val is None:
                            continue
                        else:
                            if is_datetime64_any_dtype(val_series):
                                val = pd.to_datetime(val)
                                val = datetime.strftime(val, "%Y-%m-%dT%H:%M:%S.000Z")
                        if self.metadata_flag in {'e','exact'}:
                            n = path.replace(localname + ":", f"{{{ns}}}")
                            elem = xml_new.find(f'./{n}')
                            if elem is None:
                                logger.warning(f'XML element not found for path: {n} in {xml_file.get("xmlfile")}')
                                continue
                        elif self.metadata_flag in {'f', 'flat'}:
                            n = name.split(':')[-1]
                            elem = xml_new.find(f'.//{{{ns}}}{n}')
                            if elem is None:
                                logger.warning(f'XML element not found for name: {name} in {xml_file.get("xmlfile")}')
                                continue
                        elem.text = str(val)
                    xml_desc_elem.append(xml_new.find('.'))
        except KeyError as e:
            logger.exception(f'Key Error in XML Lookup: {e}' \
            '\n please ensure column header\'s are an exact match.')            
            raise
        except IndexError as e:
            logger.warning(f'Index Error: {e}' \
            '\nIt is likely you have removed or added a file/folder to the directory' \
            'after generating your input spreadsheet. An opex will still be generated but with no xml metadata.' \
            '\nTo ensure metadata match up please regenerate the spreadsheet.')
        except Exception as e:
            logger.exception(f'General Error in XML Lookup: {e}')
            raise

    def generate_opex_properties(self, xmlroot: ET.Element, idx: int, title: str = None,
                                  description: str = None, security: str = None) -> None:
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
        if self.autoref_flag not in {"generic", "g"} or self.input:
            self.identifiers = ET.SubElement(self.properties, f"{{{self.opexns}}}Identifiers")
            self.ident_df_lookup(idx)
        # remove Properties element if no children were added
        if len(self.properties) == 0:
            xmlroot.remove(self.properties)

    def generate_opex_fixity(self, file_path: str, algorithm: Optional[list] = None) -> list:
        """Generate fixities for a file. If algorithm is None, defaults to ['SHA-1']."""
        algorithm = algorithm or ['SHA-1']
        list_fixity = []
        for algorithm_type in algorithm:
            self.fixity = ET.SubElement(self.fixities, f"{{{self.opexns}}}Fixity")
            hash_value = HashGenerator(algorithm = algorithm_type).hash_generator(file_path)
            self.fixity.set("type", algorithm_type)
            self.fixity.set("value", hash_value)
            list_fixity.append([algorithm_type, hash_value, file_path])
        return list_fixity
    
    def generate_pax_folder_opex_fixity(self, folder_path: str, fixitiesxml: ET._Element, filesxml: ET._Element, algorithm: Optional[list] = None) -> list:
        """Generate fixities for files inside a pax folder. If algorithm is None, defaults to ['SHA-1']."""
        algorithm = algorithm or ['SHA-1']
        list_fixity = []
        list_path = []
        for dir,_,files in os.walk(folder_path):
                for filename in files:
                    rel_path = os.path.relpath(dir,folder_path)
                    rel_file = os.path.join(rel_path, filename).replace('\\','/')
                    abs_file = os.path.abspath(os.path.join(dir,filename))
                    list_path.append(abs_file)
                    for algorithm_type in algorithm:
                        self.fixity = ET.SubElement(fixitiesxml, f"{{{self.opexns}}}Fixity")
                        hash_value = HashGenerator(algorithm = algorithm_type).hash_generator(abs_file)
                        self.fixity.set("type", algorithm_type)
                        self.fixity.set("value", hash_value)
                        self.fixity.set("path", rel_file)
                        list_fixity.append([algorithm_type, hash_value, abs_file])
                    file = ET.SubElement(filesxml, f"{{{self.opexns}}}File")
                    file.set("type", "content")
                    file.set("size", str(os.path.getsize(abs_file)))
                    file.text = str(rel_file)
        return list_fixity, list_path


    def generate_pax_zip_opex_fixity(self, file_path: str, algorithm: Optional[list] = None) -> list:
        """Generate fixities for files inside a pax/zip. If algorithm is None, defaults to ['SHA-1']."""
        algorithm = algorithm or ['SHA-1']
        list_fixity = []
        for algorithm_type in algorithm:
            with zipfile.ZipFile(file_path, 'r') as z:
                for file in z.filelist:
                    self.fixity = ET.SubElement(self.fixities, f"{{{self.opexns}}}Fixity")
                    hash_value = HashGenerator(algorithm = algorithm_type).hash_generator_pax_zip(file.filename, z)
                    file_replace = file.filename.replace('\\', '/')
                    self.fixity.set("path", file_replace)
                    self.fixity.set("type", algorithm_type)
                    self.fixity.set("value", hash_value)
                    list_fixity.append([algorithm_type, hash_value, f"{file_path}/{file.filename}"])
        return list_fixity
    
    def main(self) -> None:
        if self.clear_opex_flag:
            self.clear_opex()
            if self.autoref_flag or self.algorithm or self.input or self.zip_flag or self.export_flag or self.empty_flag or self.removal_flag:
                pass
            else:
                logger.info('Cleared Opexes. No additional arguments passed, so ending program.')
                raise SystemExit()
        if self.empty_flag:
            logger.debug('Removing empty directories as per empty flag.')
            ReferenceGenerator(self.root, self.output_path, meta_dir_flag = self.meta_dir_flag).remove_empty_directories(self.empty_export_flag)
        df_flag = False
        if not self.autoref_flag in {"g", "generic"}:
            logger.debug('Auto Reference flag not set to generic, checking for Dataframe requirement.')
            df_flag = self.init_df()
        self.count = 1
        if self.metadata_flag is not None:
            if not df_flag:
                logger.error('Metadata generation requires Auto Reference or Input file to be specified.')
                raise ValueError('Metadata generation requires Auto Reference or Input file to be specified.')
            self.init_generate_descriptive_metadata()
        OpexDir(self, self.root).generate_opex_dirs(self.root)
        if self.algorithm:
            output_path = define_output_file(self.output_path, self.root, self.METAFOLDER, self.meta_dir_flag, output_suffix = self.FIXITY_SUFFIX, output_format = "txt")
            if self.fixity_export_flag:
                export_list_txt(self.list_fixity, output_path)
        if self.removal_flag:
            output_path = define_output_file(self.output_path, self.root, self.METAFOLDER, self.meta_dir_flag, output_suffix = self.REMOVALS_SUFFIX, output_format = "txt")
            if self.removal_export_flag:
                export_list_txt(self.removal_list, output_path)

class OpexDir(OpexManifestGenerator):
    def __init__(self, OMG: OpexManifestGenerator, folder_path: str, title: str = None, description: str = None, security: str = None) -> None:
        self.OMG = OMG
        self.root = self.OMG.root
        self.opexns = self.OMG.opexns
        if folder_path.startswith(u'\\\\?\\'):
            self.folder_path = folder_path.replace(u'\\\\?\\', "")
        else:
            self.folder_path = folder_path
        if any([self.OMG.input,
                self.OMG.autoref_flag in {"c","catalog","a","accession","b","both","cg","catalog-generic","ag","accession-generic","bg","both-generic"},
                self.OMG.ignore_flag,
                self.OMG.removal_flag,
                self.OMG.sourceid_flag,
                self.OMG.title_flag,
                self.OMG.description_flag,
                self.OMG.security_flag]):
                index = self.OMG.index_df_lookup(self.folder_path)
        elif self.OMG.autoref_flag in {None, "g","generic"}:
            index = None
        else:
            index = None
        self.ignore = False
        self.removal = False
        if self.OMG.ignore_flag:
            self.ignore = self.OMG.ignore_df_lookup(index)
            if self.ignore:
                logger.info(f'Ignoring folder as per ignore flag in spreadsheet: {self.folder_path}')
                return
        if self.OMG.removal_flag:
            self.removal = self.OMG.removal_df_lookup(index)
            if self.removal:
                logger.info(f'Removing folder as per removal flag in spreadsheet: {self.folder_path}')
                remove_tree(self.folder_path, self.OMG.removal_list)
                return
        self.xmlroot = ET.Element(f"{{{self.opexns}}}OPEXMetadata", nsmap={"opex":self.opexns})
        self.transfer = ET.SubElement(self.xmlroot, f"{{{self.opexns}}}Transfer")
        self.manifest = ET.SubElement(self.transfer, f"{{{self.opexns}}}Manifest")
        self.folders = ET.SubElement(self.manifest, f"{{{self.opexns}}}Folders")
        self.files = ET.SubElement(self.manifest, f"{{{self.opexns}}}Files")
        if self.OMG.title_flag or self.OMG.description_flag or self.OMG.security_flag:
            self.title, self.description, self.security = self.OMG.xip_df_lookup(index) 
        elif self.OMG.autoref_flag in {"generic", "g", "catalog-generic", "cg", "accession-generic", "ag", "both-generic", "bg"}:
            if title is not None:
                self.title = title
            else:
                self.title = os.path.basename(self.folder_path)
            if description is not None:
                self.description = description
            else:
                self.description = os.path.basename(self.folder_path)
            if security is not None:
                self.security = security
            else:
                self.security = self.GENERIC_DEFAULT_SECURITY
        else:
            self.title = title
            self.description = description
            self.security = security
        if self.OMG.sourceid_flag:
            self.OMG.sourceid_df_lookup(self.transfer, index)
        # Handling Fixities for PAX Folders
        if self.OMG.algorithm and self.OMG.pax_fixity_flag is True and self.folder_path.endswith(".pax"):
            self.fixities = ET.SubElement(self.transfer, f"{{{self.opexns}}}Fixities")
            tmp_list_fixity,tmp_list_path = self.OMG.generate_pax_folder_opex_fixity(self.folder_path, self.fixities, self.files, self.OMG.algorithm)
            self.OMG.list_fixity.extend(tmp_list_fixity)
            self.OMG.list_path.extend(tmp_list_path)
        if self.OMG.autoref_flag or self.OMG.input:
            self.OMG.generate_opex_properties(self.xmlroot, index, 
                                              title = self.title,
                                              description = self.description,
                                              security = self.security)
            if self.OMG.metadata_flag is not None:
                self.xml_descmeta = ET.SubElement(self.xmlroot,f"{{{self.opexns}}}DescriptiveMetadata")
                self.OMG.generate_descriptive_metadata(self.xml_descmeta, idx = index)

    def filter_directories(self, directory: str, sort_key: str = str.casefold) -> list:
        try:
            if self.OMG.hidden_flag is False:
                list_directories = sorted([win_256_check(os.path.join(directory, f.name)) for f in os.scandir(directory)
                                        if not f.name.startswith('.')
                                        and filter_win_hidden(win_256_check(os.path.join(directory, f.name))) is False
                                        and not f.name in ('opex_generate.exe','opex_generate.bin') 
                                        and f.name != self.OMG.METAFOLDER
                                        and f.name != os.path.basename(__file__)],
                                        key=sort_key)
            elif self.OMG.hidden_flag is True:
                list_directories = sorted([win_256_check(os.path.join(directory, f.name)) for f in os.scandir(directory) \
                                        if f.name != self.OMG.METAFOLDER
                                        and not f.name in ('opex_generate.exe','opex_generate.bin') 
                                        and f.name != os.path.basename(__file__)],
                                        key=sort_key)
            return list_directories
        except Exception as e:
            logger.exception(f'Failed to Filter Directories: {e}')
            raise
        
    def generate_opex_dirs(self, path: str) -> None:
        """"
        This function loops recursively through a given directory.
        
        There are two loops to first generate Opexes for Files; Then Generate the Folder Opex Manifests.
        """    
        current = OpexDir(self.OMG, path)
        if current.OMG.algorithm and current.OMG.pax_fixity_flag is True and current.folder_path.endswith(".pax"):
            opex_path = os.path.abspath(current.folder_path)
        else:
            opex_path = os.path.join(os.path.abspath(current.folder_path), os.path.basename(current.folder_path))
        #First Loop to Generate Folder Manifest Opexes & Individual File Opexes.
        if current.removal is True:
            #If removal is True for Folder, then it will be removed - Does not need to descend.
            pass
        else:
            for f_path in current.filter_directories(path):
                if f_path.endswith('.opex'):
                    #Ignores OPEX files / directories...
                    pass
                elif os.path.isdir(f_path):
                    if current.ignore is True or \
                    (current.OMG.removal_flag is True and \
                     current.OMG.removal_df_lookup(current.OMG.index_df_lookup(f_path)) is True):
                        #If Ignore is True, or the Folder below is marked for Removal: Don't add to Opex 
                        pass
                    else:
                        #Add Folder to OPEX Manifest (doesn't get written yet...)
                        current.folder = ET.SubElement(self.folders, f"{{{self.opexns}}}Folder")
                        current.folder.text = str(os.path.basename(f_path))
                    if current.OMG.algorithm and current.OMG.pax_fixity_flag is True and current.folder_path.endswith(".pax"):
                        #If using fixity, but the current folder is a PAX & using PAX Fixity: End descent. 
                        pass
                    else:
                        #Recurse Descent.
                        current.generate_opex_dirs(f_path)
                elif os.path.isfile(f_path):
                    #Processes OPEXes for individual Files: this gets written.
                    OpexFile(current.OMG, f_path)
                else:
                    logger.warning(f'Unknown File Type at: {f_path}')
                    pass
        #Second Loop to add previously generated Opexes to Folder Manifest.
        if current.removal is True or current.ignore is True:
            logger.debug(f'Skipping Opex generation for: {current.folder_path}')
            pass
        else:
            if check_opex(opex_path):
                #Only processing Opexes.
                for f_path in current.filter_directories(path):
                    if os.path.isfile(f_path):
                        file = ET.SubElement(current.files, f"{{{current.opexns}}}File")
                        if f_path.endswith('.opex'):
                            file.set("type", "metadata")
                        else:
                            file.set("type", "content")
                            file.set("size", str(os.path.getsize(f_path)))
                        file.text = str(os.path.basename(f_path))
                        logger.debug(f'Adding File to Opex Manifest: {f_path}')
                #Writes Folder OPEX 
                write_opex(opex_path, current.xmlroot)
            else:
                #Avoids Override if exists, lets you continue where left off. 
                logger.info(f"Avoiding override, Opex exists at: {opex_path}")

class OpexFile(OpexManifestGenerator):
    def __init__(self, OMG: OpexManifestGenerator, file_path: str, title: str = None, description: str = None, security: str = None) -> None:
        self.OMG = OMG
        self.opexns = self.OMG.opexns  
        if file_path.startswith(u'\\\\?\\'):
            self.file_path = file_path.replace(u'\\\\?\\', "")
        else:
            self.file_path = file_path
        if check_opex(self.file_path):
            index = None
            if any([self.OMG.input,
                    self.OMG.autoref_flag in {"c","catalog","a","accession","b","both","cg","catalog-generic","ag","accession-generic","bg","both-generic"},
                    self.OMG.ignore_flag,
                    self.OMG.removal_flag,
                    self.OMG.sourceid_flag,
                    self.OMG.title_flag,
                    self.OMG.description_flag,
                    self.OMG.security_flag]):
                    index = self.OMG.index_df_lookup(self.file_path)
            elif self.OMG.autoref_flag is None or self.OMG.autoref_flag in {"g","generic"}:
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
            elif self.OMG.autoref_flag in {"generic", "g", "catalog-generic", "cg", "accession-generic", "ag", "both-generic", "bg"}:
                if title is not None:
                    self.title = title
                else:
                    self.title = os.path.splitext(os.path.basename(self.file_path))[0]
                if description is not None:
                    self.description = description
                else:
                    self.description = os.path.splitext(os.path.basename(self.file_path))[0]
                if security is not None:
                    self.security = security
                else:
                    self.security = self.GENERIC_DEFAULT_SECURITY
            else:
                self.title = title
                self.description = description
                self.security = security
            opex_path = None
            if self.OMG.algorithm or self.OMG.autoref_flag or self.OMG.input:
                self.xmlroot = ET.Element(f"{{{self.opexns}}}OPEXMetadata", nsmap={"opex":self.opexns})
                self.transfer = ET.SubElement(self.xmlroot, f"{{{self.opexns}}}Transfer")
                if self.OMG.sourceid_flag:
                    self.OMG.sourceid_df_lookup(self.transfer, index)
                if self.OMG.algorithm:
                    self.fixities = ET.SubElement(self.transfer, f"{{{self.opexns}}}Fixities")
                    if self.OMG.hash_from_spread:
                        self.OMG.hash_df_lookup(self.fixities, index)  
                    else:
                        self.OMG.list_path.append(self.file_path)
                        if self.OMG.pax_fixity_flag is True and (self.file_path.endswith("pax.zip") or self.file_path.endswith(".pax")):
                            tmp_list_fixity = self.generate_pax_zip_opex_fixity(self.file_path, self.OMG.algorithm)
                        else:
                            tmp_list_fixity = self.generate_opex_fixity(self.file_path, self.OMG.algorithm)
                        self.OMG.list_fixity.extend(tmp_list_fixity)
                if self.transfer is None:
                    self.xmlroot.remove(self.transfer)
                if self.OMG.autoref_flag or self.OMG.input:
                    self.OMG.generate_opex_properties(self.xmlroot, index,
                                                      title = self.title,
                                                      description = self.description,
                                                      security = self.security)
                    if self.OMG.metadata_flag is not None:
                        self.xml_descmeta = ET.SubElement(self.xmlroot, f"{{{self.opexns}}}DescriptiveMetadata")
                        self.OMG.generate_descriptive_metadata(self.xml_descmeta, index)
                opex_path = write_opex(self.file_path, self.xmlroot)
                # Zip cannot be activated unless another flag - which 
            if self.OMG.zip_flag:
                zip_opex(self.file_path, opex_path)
                if self.OMG.zip_file_removal:
                    os.remove(self.file_path)
                    if os.path.exists(opex_path):
                        os.remove(opex_path)
                        logger.debug(f'Removed file: {opex_path}')
                    logger.debug(f'Removed file: {self.file_path}')
        else:
            logger.info(f"Avoiding override, Opex exists at: {self.file_path}: ")