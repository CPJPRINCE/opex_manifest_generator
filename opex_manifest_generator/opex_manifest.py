"""
Opex Manifest Generator tool

This tool is utilised to recursively generate Opex files for files / directories for use in uploading to Preservica and other OPEX conforming systems.

author: Christopher Prince
license: Apache License 2.0"
"""

from lxml import etree as ET
import pandas as pd
import os, configparser, logging, zipfile
from typing import Optional, Dict, Callable
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
    check_bool,\
    check_opex,\
    write_opex
from datetime import datetime

logger = logging.getLogger(__name__)

class ProgressBar():
    import sys, time, tqdm
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.description = description
        self.progress_bar = self.tqdm.tqdm(total=self.total, desc=self.description, unit="item")
    def update(self, n: int = 1):
        self.progress_bar.update(n)
    def close(self):
        self.progress_bar.close()

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
                 suffix_option: Optional[str] = 'file',
                 acc_prefix: str = None,
                 accession_mode: str = False,
                 start_ref: int = 1,
                 fixity: list[str] = [],
                 pax: bool = False,
                 buffer: int = 4096,
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
                 max_workers: Optional[int] = 1,
                 autoref_options: Optional[str] = None) -> None:

        self.root = os.path.abspath(root)

        # Base Parameters
        self.opexns = "http://www.openpreservationexchange.org/opex/v1.2"
        self.start_time = datetime.now()
        #self.list_path = []
        self.list_fixity = []

        # Parameters for Opex Generation
        self.fixity = fixity
        self.fixity_export_flag = fixity_export_flag
        self.pax_flag = pax
        self.buffer = buffer
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
        self.filter_flag = None

        # Multithreading
        self.max_workers = max_workers
        if self.max_workers == 0:
            self.max_workers = os.cpu_count() or 1

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
        if any(self.HASH_FIELD + ":" in header for header in self.column_headers):
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
                    self.df = pd.read_json(self.input, orient='index')
                elif self.input.endswith('.ods'):
                    self.df = pd.read_excel(self.input, engine='odf')
                elif self.input.endswith('.xml'):
                    self.df = pd.read_xml(self.input)
                self.column_headers = self.df.columns.values.tolist()
                self.set_input_flags()
                logger.debug(f'Input Dataframe initialised with columns: {self.column_headers}')
                return True
            else:
                logger.debug('No Auto Reference or Input file specified, proceeding without Dataframe')
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
                remove = check_bool(self.df.loc[idx,self.REMOVAL_FIELD].item())
                return remove
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
                ignore = check_bool(self.df.loc[idx,self.IGNORE_FIELD].item())
            return ignore
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

    def sourceid_df_lookup(self, idx: pd.Index) -> Optional[str]:
        if getattr(self, 'df', None) is None:
            logger.error('Dataframe not initialised, cannot perform lookup')
            raise RuntimeError('Dataframe not initialised, cannot perform lookup')
        try:
            if idx.empty:
                return None
            else:
                return check_nan(self.df.loc[idx,self.SOURCEID_FIELD].item())
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

    def hash_df_lookup(self, idx: pd.Index, algorithms: list) -> Optional[Dict[str, str]]:
        if getattr(self, 'df', None) is None:
            logger.error('Dataframe not initialised, cannot perform lookup')
            raise RuntimeError('Dataframe not initialised, cannot perform lookup')
        try:
            if idx.empty:
                return
            hash_values = dict()
            for alg in algorithms:
                hash_value = None
                # prefer the algorithm specified in the spreadsheet for this row
                hash_column = f"{self.HASH_FIELD}:{alg}"
                if any(hash_column in header for header in self.column_headers):
                    hash_value = check_nan(self.df.loc[idx, hash_column].item())
                    logger.debug(f'Using Algorithm from Spreadsheet: {alg} with Hash: {hash_value}')
                    hash_values.update({alg: hash_value})
            if hash_values is None or hash_values == {}:
                logger.warning('No Algorithm specified in Spreadsheet for this entry')
                return None
            return hash_values
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

    def ident_df_lookup(self, idx: pd.Index, default_key: str = None) -> Optional[Dict[str, str]]:
        """
        Looks up identifiers in the dataframe for the given index, checking for any column headers that contain the identifier field, arcref field, or accref field.
        If a matching header is found, the corresponding value is retrieved from the dataframe and added to a dictionary of identifiers with the appropriate key name based on the header.
        The resulting dictionary of identifiers is returned for inclusion in the Opex manifest.
        """
        if getattr(self, 'df', None) is None:
            logger.error('Dataframe not initialised, cannot perform lookup')
            raise RuntimeError('Dataframe not initialised, cannot perform lookup')
        try:
            if idx.empty:
                return None
            else:
                identifiers = {}
                for header in self.column_headers:
                    ident = None
                    if any(s in header for s in {self.IDENTIFIER_FIELD,self.ARCREF_FIELD,self.ACCREF_FIELD}):
                        if f'{self.IDENTIFIER_FIELD}:' in header:
                            key_name = str(header).split(':',1)[-1]
                        elif self.ARCREF_FIELD in header:
                            key_name = default_key if default_key else self.ARCREF_FIELD
                        elif self.ACCREF_FIELD in header:
                            key_name = self.ACCREF_CODE
                        elif self.IDENTIFIER_FIELD in header:
                            key_name = default_key if default_key else self.IDENTIFIER_DEFAULT
                        else:
                            key_name = default_key if default_key else self.IDENTIFIER_DEFAULT
                        ident = check_nan(self.df.loc[idx,header].item())
                        logger.debug(f'Adding Identifer: {header}: {ident}')
                        identifiers.update({key_name: ident})
                return identifiers

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

    def init_generate_descriptive_metadata(self) -> list:
        """
        Initialises the descriptive metadata by parsing the XML files in the metadata directory, generating a list of the elements and their namespaces, and comparing them against the column headers in the spreadsheet to filter out non-matching data.
        The resulting list of matching elements is stored in self.xml_files for use in generating the descriptive metadata in the Opex manifest.
        """
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
                    root_element_ns = root_element.namespace
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
                if len(list_xml) > 0:
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

    def generate_descriptive_metadata(self, idx: pd.Index) -> ET._Element:
        """
        Composes the data into an xml file.
        Iterates through the list of matching elements generated in init_generate_descriptive_metadata, looks up the corresponding value in the spreadsheet for each element, and inserts it into the XML file at the correct path.
        The resulting XML element is returned for inclusion in the Opex manifest.
        """
        try:
            xml_desc_elem = ET.Element()
            for xml_file in self.xml_files:
                assert isinstance(list_xml, list)
                assert isinstance(localname, str)
                list_xml = xml_file.get('data')
                localname = xml_file.get('localname')
                localns = xml_file.get('localns')
                if len(list_xml) == 0 or list_xml is None:
                    logger.warning(f'No matching columns found for XML file: {xml_file.get("xmlfile")}, skipping.')
                    return None
                else:
                    xml_new = ET.parse(xml_file.get('xmlfile'))
                    for elem_dict in list_xml:
                        assert isinstance(elem_dict, dict)
                        name = elem_dict.get('Name')
                        path = elem_dict.get('Path')
                        ns = elem_dict.get('Namespace')
                        assert isinstance(path, str)
                        assert isinstance(name, str)
                        assert isinstance(ns, str)
                        if self.metadata_flag in {'exact'}:
                            val_series = self.df.loc[idx,path]
                            val = check_nan(val_series.item())
                        elif self.metadata_flag in {'flat'}:
                            val_series = self.df.loc[idx,name]
                            val = check_nan(val_series.item())
                        if pd.isnull(val) or val is None:
                            continue
                        else:
                            if is_datetime64_any_dtype(val_series):
                                val = pd.to_datetime(val)
                                val = datetime.strftime(val, "%Y-%m-%dT%H:%M:%S.000Z")
                        if self.metadata_flag in {'exact'}:
                            n = path.replace(localname + ":", f"{{{ns}}}")
                            elem = xml_new.find(f'./{n}')
                            if elem is None:
                                logger.warning(f'XML element not found for path: {n} in {xml_file.get("xmlfile")}')
                                continue
                        elif self.metadata_flag in {'flat'}:
                            n = name.split(':')[-1]
                            elem = xml_new.find(f'.//{{{ns}}}{n}')
                            if elem is None:
                                logger.warning(f'XML element not found for name: {name} in {xml_file.get("xmlfile")}')
                                continue
                        if elem is not None:
                            elem.text = str(val)
                    xml_desc_elem.append(xml_new.find('.'))
            return xml_desc_elem
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
        """ Deprecated method for generating Opex Properties, now integrated into generate_opex_manifest."""

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

    def generate_opex_fixity(self, file_path: str, fixity: Optional[list] = None, hash_map: Optional[Dict[str,str]] = None) -> list:
        """Deprecated method. Generate fixities for a file. If algorithm is None, defaults to ['SHA-1']."""
        fixity = fixity or ['SHA-1']
        list_fixity = []
        for algorithm in fixity:
            fixity_xml = ET.SubElement(self.fixities, f"{{{self.opexns}}}Fixity")
            if hash_map is not None and algorithm in hash_map and file_path in hash_map[algorithm]:
                logger.info(f'Using pre-computed hash for {file_path} with algorithm {algorithm} from hash map.')
                hash_value = hash_map.get(algorithm).get(file_path)
            else:
                hash_value = HashGenerator(algorithm, self.buffer).hash_generator(file_path)
            fixity_xml.set("type", algorithm)
            fixity_xml.set("value", hash_value)
            list_fixity.append([algorithm, hash_value, file_path])
        return list_fixity

    def generate_pax_folder_opex_fixity(self, folder_path: str, fixitiesxml: ET._Element, filesxml: ET._Element, fixity: Optional[list] = None, hash_map: Optional[Dict[str,str]] = None) -> list:
        """Deprecated Method. Generate fixities for files inside a pax folder. If algorithm is None, defaults to ['SHA-1']."""
        fixity = fixity or ['SHA-1']
        list_fixity = []
        list_path = []
        for dir,_,files in os.walk(folder_path):
                for filename in files:
                    rel_path = os.path.relpath(dir,folder_path)
                    rel_file = os.path.join(rel_path, filename).replace('\\','/')
                    abs_file = os.path.abspath(os.path.join(dir,filename))
                    list_path.append(abs_file)
                    for algorithm in fixity:
                        fixity_xml = ET.SubElement(fixitiesxml, f"{{{self.opexns}}}Fixity")
                        # This may not be right?
                        if hash_map is not None and algorithm in hash_map and abs_file in hash_map[fixity]:
                            logger.info(f'Using pre-computed hash for {abs_file} with algorithm {algorithm} from hash map.')
                            hash_value = hash_map.get(algorithm).get(abs_file)
                        else:
                            hash_value = HashGenerator(algorithm, self.buffer).hash_generator(abs_file)
                        fixity_xml.set("type", algorithm)
                        fixity_xml.set("value", hash_value)
                        fixity_xml.set("path", rel_file)
                        list_fixity.append([algorithm, hash_value, abs_file])
                    file = ET.SubElement(filesxml, f"{{{self.opexns}}}File")
                    file.set("type", "content")
                    file.set("size", str(os.path.getsize(abs_file)))
                    file.text = str(rel_file)
        return list_fixity

    def generate_pax_zip_opex_fixity(self, file_path: str, fixity: Optional[list] = None, hash_map: Optional[Dict[str, str]] = None) -> list:
        """Deprecated Method. Generate fixities for files inside a pax/zip. If algorithm is None, defaults to ['SHA-1']."""
        fixity = fixity or ['SHA-1']
        list_fixity = []
        for algorithm in fixity:
            with zipfile.ZipFile(file_path, 'r') as z:
                for zfile in z.filelist:
                    fixity_xml = ET.SubElement(self.fixities, f"{{{self.opexns}}}Fixity")
                    if hash_map is not None and algorithm in hash_map and file_path in hash_map[algorithm]:
                        logger.info(f'Using pre-computed hash for {file_path} with algorithm {algorithm} from hash map.')
                        hash_value = hash_map.get(algorithm).get(file_path)
                    else:
                        hash_value = HashGenerator(algorithm = algorithm, buffer = self.buffer).hash_generator_pax_zip(zfile.filename, z)
                    file_replace = zfile.filename.replace('\\', '/')
                    fixity_xml.set("path", file_replace)
                    fixity_xml.set("type", algorithm)
                    fixity_xml.set("value", hash_value)
                    list_fixity.append([algorithm, hash_value, f"{file_path}/{zfile.filename}"])
        return list_fixity

    def old_main(self) -> None:
        if self.clear_opex_flag:
            self.clear_opex()
            if self.autoref_flag or self.fixity or self.input or self.zip_flag or self.export_flag or self.empty_flag or self.removal_flag:
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
        hash_map = None
        OpexDir(self, self.root).generate_opex_dirs(self.root, hash_map)
        if self.fixity:
            output_path = define_output_file(self.output_path, self.root, self.METAFOLDER, self.meta_dir_flag, output_suffix = self.FIXITY_SUFFIX, output_format = "txt")
            if self.fixity_export_flag:
                export_list_txt(self.list_fixity, output_path)
        if self.removal_flag:
            output_path = define_output_file(self.output_path, self.root, self.METAFOLDER, self.meta_dir_flag, output_suffix = self.REMOVALS_SUFFIX, output_format = "txt")
            if self.removal_export_flag:
                export_list_txt(self.removal_list, output_path)

    def _process(self, path) -> None:

        self.title = None
        self.description = None
        self.security_tag = None
        self.source_id = None
        self.identifiers = None
        self.descriptive_metadata = None

        if any([self.input,
            self.autoref_flag in {"c","catalog","a","accession","b","both","cg","catalog-generic","ag","accession-generic","bg","both-generic"},
            self.ignore_flag,
            self.removal_flag,
            self.sourceid_flag,
            self.title_flag,
            self.description_flag,
            self.security_flag]):
            index = self.index_df_lookup(path)

        elif self.autoref_flag in {None, "g","generic"}:
            index = None
        else:
            index = None

        # Handling Fixities for PAX Folders
        # if self.OMG.fixity and self.OMG.pax_fixity_flag is True and self.folder_path.endswith(".pax"):
        #     self.fixities = ET.SubElement(self.transfer, f"{{{self.opexns}}}Fixities")
        #     tmp_list_fixity = self.OMG.generate_pax_folder_opex_fixity(self.folder_path, self.fixities, self.files, self.OMG.fixity)
        #     self.OMG.list_fixity.extend(tmp_list_fixity)

        if self.autoref_flag or self.input:
            if self.title_flag or self.description_flag or self.security_flag:
                self.title, self.description, self.security_tag = self.xip_df_lookup(index)
            if self.autoref_flag not in {"generic", "g"} or self.input:
                self.identifiers = self.ident_df_lookup(index)
            elif self.autoref_flag in {"generic", "g", "catalog-generic", "cg", "accession-generic", "ag", "both-generic", "bg"}:
                if self.title is None:
                    self.title = os.path.basename(path)
                if self.description is None:
                    self.description = os.path.basename(path)
                if self.security_tag is None:
                    self.security_tag = self.GENERIC_DEFAULT_SECURITY
            if self.sourceid_flag:
                self.source_id = self.sourceid_df_lookup(index)
            if self.metadata_flag is not None:
                self.descriptive_metadata = self.generate_descriptive_metadata(index)

    def _process_removal_and_ignore(self, path, index) -> None:

        self.ignore = False
        self.removal = False

        if self.ignore_flag:
            self.ignore = self.ignore_df_lookup(index)
            if self.ignore:
                logger.info(f'Ignoring path as per ignore flag in spreadsheet: {path}')
                return True
        if self.removal_flag:
            self.removal = self.removal_df_lookup(index)
            if self.removal:
                logger.info(f'Removing path as per removal flag in spreadsheet: {path}')
                remove_tree(path, self.removal_list)
                return True
        return False

    def _process_fixity(self, path) -> None:
        # A possible fallback for hash_from_spread could be to check the hash map for the file and algorithm, and if not found, generate the fixity.
        # This would allow users to specify some hashes in the spreadsheet while still benefiting from the performance improvement of the hash map for other files.
        if self.hash_from_spread is True and self.fixity and any(f'{self.HASH_FIELD}:{alg}' in self.column_headers for alg in self.fixity):
            hash_list = []
            if self.index is None:
                self.index = self.index_df_lookup(path)
            generate_fixity = []
            for alg in self.fixity:
                hash_value = self.hash_df_lookup(self.index, [alg])
                hash_list.append({'type': alg, 'value': hash_value})
                if hash_value is None:
                    generate_fixity.append(alg)
            if len(generate_fixity) == 0:
                generate_fixity = None
        elif self.hash_map is not None and len(self.hash_map) > 0:
            hash_list = []
            for alg in self.fixity:
                if isinstance(self.hash_map.get(alg).get(path), list):
                    for zipfile in self.hash_map.get(alg).get(path):
                        hash_list.append({'type': alg, 'value': zipfile.get('value'), 'path': zipfile.get('path')})
                else:
                    hash_list.append({'type': alg, 'value': self.hash_map.get(alg).get(path).get('value')})
            generate_fixity = None
        elif self.fixity:
            hash_list = None
            generate_fixity = self.fixity
        else:
            hash_list = None
            generate_fixity = None
        return hash_list, generate_fixity

    def _process_multithread_fixity(self, path_list) -> None:
        for alg in self.fixity:
            hash_results = HashGenerator(self.fixity, self.buffer).hash_generator_multithread(path_list, self.max_workers, self.pax_flag)
            if alg not in self.hash_map:
                self.hash_map[alg] = {}
            self.hash_map[alg].update(hash_results)

    def _process_loop(self, path) -> None:
        if any([self.removal_flag, self.ignore_flag]):
            if self._process_removal_and_ignore(path, self.index_df_lookup(path)) is True:
                return

        if self.fixity and self.max_workers > 1:
            # Check if Column for Hash{Algorithm} exists in Spreadsheet, if so use that instead of generating new hash values.
            # If not, identify which algorithms are missing and return a list of the file paths.
            if self.hash_from_spread is True:
                missing_algorithms = []
                for alg in self.fixity:
                    if not any(f'{self.HASH_FIELD}:{alg}' in header for header in self.column_headers):
                        missing_algorithms.append(alg)
                if len(missing_algorithms) > 0:
                    logger.warning(f'Hash from spreadsheet enabled but no columns found for algorithms: {missing_algorithms}. Proceeding to generate fixity for these algorithms.')
                    f_list = [f.path for f in os.scandir(path) if f.is_file() and not f.name.endswith('.opex')]
                    self._process_multithread_fixity(f_list)
                else:
                    logger.debug('Hash from spreadsheet enabled and columns found for all algorithms, skipping fixity generation.')
            else:
                f_list = [f.path for f in os.scandir(path) if f.is_file() and not f.name.endswith('.opex')]
                self._process_multithread_fixity(f_list)
                logger.debug('Multithreading enabled for fixity generation, gathering file list.')

        for f in os.scandir(path):
            if f.is_dir():
                self._process_loop(f.path)
            elif f.is_file() and f.name.endswith('.opex'):
                logger.debug(f'Skipping file with .opex extension: {f.path}, prevents opexes generating opexes')
                continue
            elif f.is_file():
                self._process(f.path)
                if self.input \
                    or self.fixity \
                    or self.title_flag \
                    or self.description_flag \
                    or self.security_flag \
                    or self.sourceid_flag \
                    or (self.identifiers is not None and len(self.identifiers) > 0) \
                    or self.metadata_flag is not None:

                    hash_list,generate_fixity = self._process_fixity(f.path)
                    OpexFileWriter(f.path,
                                    title = self.title,
                                    description = self.description,
                                    security_tag = self.security_tag,
                                    source_id = self.source_id,
                                    identifers = self.identifiers,
                                    descriptive_metadata = self.descriptive_metadata,
                                    fixity = hash_list,
                                    generate_fixity = generate_fixity
                                    ).write_opex_file()

        if os.path.isdir(path):
            self._process(path)
            OpexDirWriter(path,
                        title = self.title,
                        description = self.description,
                        security_tag = self.security_tag,
                        source_id = self.source_id,
                        identifers = self.identifiers,
                        descriptive_metadata = self.descriptive_metadata,
                        include_hidden = self.hidden_flag,
                        sort_key = self.sort_key,
                        filter_flag = self.filter_flag
                        ).write_opex_manifest()

    def display_progress(self):
        self.total = len([[dirs,files] for dirs,_,files in os.walk(self.root)])
        ProgressBar(self.total)

    def main(self) -> None:
        if self.clear_opex_flag:
            self.clear_opex()
            if self.autoref_flag or self.fixity or self.input or self.zip_flag or self.export_flag or self.empty_flag or self.removal_flag or self.metadata_flag:
                pass
            else:
                logger.info('Cleared Opexes. No additional arguments passed, so ending program.')
                raise SystemExit()
        if self.empty_flag:
            logger.debug('Removing empty directories as per empty flag.')
            ReferenceGenerator(self.root, self.output_path, meta_dir_flag = self.meta_dir_flag).remove_empty_directories(self.empty_export_flag)
        if not self.autoref_flag in {"g", "generic"}:
            logger.debug('Auto Reference flag not set to generic, checking for Dataframe requirement.')
            self.init_df()

        if self.fixity:
            logger.debug('Fixity flag enabled, preparing for fixity generation.')
        if self.fixity and self.max_workers > 1:
            logger.debug('Multithreading enabled for fixity generation. Hash map will be generated for future use if there are multiple files to process.')
        if self.zip_flag:
            logger.debug('Zip flag enabled, generating zip file manifests.')

        if self.metadata_flag is not None and self.df is None:
            logger.error('Metadata generation requires Auto Reference or Input file to be specified.')
            raise ValueError('Metadata generation requires Auto Reference or Input file to be specified.')
        else:
            self.init_generate_descriptive_metadata()

        self.hash_map: Dict[str,Dict] = {}
        # If Multithreading needs to go at top f (Loses continous runningy)...
        # if self.fixity and self.max_workers > 1:
        #     file_list = [os.path.join(dir, file) for dir, _, files in os.walk(self.root) for file in files if not file.endswith('.opex')]
        #     self._process_multithread_fixity(file_list, hash_map = self.hash_map)
        self._process_loop(self.root)
        if self.fixity:
            output_path = define_output_file(self.output_path, self.root, self.METAFOLDER, self.meta_dir_flag, output_suffix = self.FIXITY_SUFFIX, output_format = "txt")
            if self.fixity_export_flag:
                export_list_txt(self.list_fixity, output_path)
        if self.removal_flag:
            output_path = define_output_file(self.output_path, self.root, self.METAFOLDER, self.meta_dir_flag, output_suffix = self.REMOVALS_SUFFIX, output_format = "txt")
            if self.removal_export_flag:
                export_list_txt(self.removal_list, output_path)

class OpexDir(OpexManifestGenerator):
    """
    Deprecated class for generating OPEX manifest for a directory, now integrated into OpexManifestGenerator. May be removed in future versions.
    """
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
        if self.OMG.fixity and self.OMG.pax_fixity_flag is True and self.folder_path.endswith(".pax"):
            self.fixities = ET.SubElement(self.transfer, f"{{{self.opexns}}}Fixities")
            tmp_list_fixity = self.OMG.generate_pax_folder_opex_fixity(self.folder_path, self.fixities, self.files, self.OMG.fixity)
            self.OMG.list_fixity.extend(tmp_list_fixity)
            #self.OMG.list_path.extend(tmp_list_path)
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

    def generate_opex_dirs(self, path: str, hash_map: Optional[Dict[str,str]]) -> None:
        """"
        This function loops recursively through a given directory.

        There are two loops to first generate Opexes for Files; Then Generate the Folder Opex Manifests.
        """
        current = OpexDir(self.OMG, path)
        if current.OMG.fixity and current.OMG.pax_fixity_flag is True and current.folder_path.endswith(".pax"):
            opex_path = os.path.abspath(current.folder_path)
        else:
            opex_path = os.path.join(os.path.abspath(current.folder_path), os.path.basename(current.folder_path))
        #First Loop to Generate Folder Manifest Opexes & Individual File Opexes.
        if current.removal is True:
            #If removal is True for Folder, then it will be removed - Does not need to descend.
            pass
        else:
            #opexes are ignored by default
            file_list = [file for file in current.filter_directories(current.folder_path) if not file.endswith('.opex') and os.path.isfile(file)]
            if self.OMG.pax_fixity_flag is True:
                pax_folders = [f for f in current.filter_directories(current.folder_path) if f.endswith('.pax') and os.path.isdir(f)]
                file_list.extend(pax_folders)
            if self.OMG.fixity and self.OMG.max_workers > 1 and not current.OMG.hash_from_spread:
                hash_map = {}
                for algorithm in self.OMG.fixity:
                    hash_results = HashGenerator(algorithm, self.buffer).hash_generator_multithread(file_list, self.OMG.max_workers, self.OMG.pax_fixity_flag)
                    hash_map.update({algorithm: hash_results})
            for f_path in file_list:
                if os.path.isdir(f_path):
                    if current.ignore is True or \
                    (current.OMG.removal_flag is True and \
                     current.OMG.removal_df_lookup(current.OMG.index_df_lookup(f_path)) is True):
                        #If Ignore is True, or the Folder below is marked for Removal: Don't add to Opex
                        pass
                    else:
                        #Add Folder to OPEX Manifest (doesn't get written yet...)
                        current.folder = ET.SubElement(current.folders, f"{{{self.opexns}}}Folder")
                        current.folder.text = str(os.path.basename(f_path))
                    if current.OMG.fixity and current.OMG.pax_fixity_flag is True and current.folder_path.endswith(".pax"):
                        #If using fixity, but the current folder is a PAX & using PAX Fixity: End descent.
                        pass
                    else:
                        #Recurse Descent.
                        current.generate_opex_dirs(f_path, hash_map)
                elif os.path.isfile(f_path):
                    #Processes OPEXes for individual Files: this gets written.
                    OpexFile(current.OMG, f_path, hash_map=hash_map)
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
    """
    Deprecated class for generating OPEX manifest for a file, now integrated into OpexManifestGenerator. May be removed in future versions.
    """
    def __init__(self, OMG: OpexManifestGenerator, file_path: str, title: str = None, description: str = None, security: str = None, hash_map: Optional[Dict[str,str]] = None) -> None:
        self.OMG = OMG
        self.opexns = self.OMG.opexns
        if file_path.startswith(u'\\\\?\\'):
            self.file_path = file_path.replace(u'\\\\?\\', "")
        else:
            self.file_path = file_path
        if check_opex(self.file_path):
            index = None
            if any([self.OMG.input,
                    self.OMG.autoref_flag in {"catalog","accession","both","catalog-generic","accession-generic","both-generic"},
                    self.OMG.ignore_flag,
                    self.OMG.removal_flag,
                    self.OMG.sourceid_flag,
                    self.OMG.title_flag,
                    self.OMG.description_flag,
                    self.OMG.security_flag]):
                    index = self.OMG.index_df_lookup(self.file_path)
            elif self.OMG.autoref_flag is None or self.OMG.autoref_flag in {"generic"}:
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
            elif self.OMG.autoref_flag in {"generic", "catalog-generic", "accession-generic", "both-generic"}:
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
            if self.OMG.fixity or self.OMG.autoref_flag or self.OMG.input:
                self.xmlroot = ET.Element(f"{{{self.opexns}}}OPEXMetadata", nsmap={"opex":self.opexns})
                self.transfer = ET.SubElement(self.xmlroot, f"{{{self.opexns}}}Transfer")
                if self.OMG.sourceid_flag:
                    self.OMG.sourceid_df_lookup(self.transfer, index)
                if self.OMG.fixity:
                    self.fixities = ET.SubElement(self.transfer, f"{{{self.opexns}}}Fixities")
                    if self.OMG.hash_from_spread:
                        logger.info('Using pre-computed hashes from spreadsheet as per hash_from_spread flag.')
                        self.OMG.hash_df_lookup(self.fixities, index, hash_map)
                    else:
                        #self.OMG.list_path.append(self.file_path)
                        if self.OMG.pax_fixity_flag is True and (self.file_path.endswith("pax.zip") or self.file_path.endswith(".pax")):
                            tmp_list_fixity = self.generate_pax_zip_opex_fixity(self.file_path, self.OMG.fixity, hash_map)
                        else:
                            tmp_list_fixity = self.generate_opex_fixity(self.file_path, self.OMG.fixity, hash_map)
                        self.OMG.list_fixity.extend(tmp_list_fixity)
                #if self.transfer is None:
                #    self.xmlroot.remove(self.transfer)
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

class OpexReader():
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
        except ET.ParseError as e:
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
            self.tree = ET.parse(self.file_path)
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
            self.identifiers = {} if self.identifiers_elm is not None else None
            self.sourceid_elm = self.tree.find(f'.//{{{self.opexns}}}SourceID') if self.tree.find(f'.//{{{self.opexns}}}SourceID') is not None else None
            self.sourceid = self.sourceid_elm.text if self.sourceid_elm is not None else None
            for ident in self.identifiers_elm or []:
                self.identifiers.update({ident.attrib.get('type'): ident.text})
            self.descriptive_metadata_xml = self.tree.find(f'.//{{{self.opexns}}}DescriptiveMetadata') if self.tree.find(f'.//{{{self.opexns}}}DescriptiveMetadata') is not None else None
            self.descriptive_metadata = ET.tostring(self.descriptive_metadata_xml) if self.descriptive_metadata_xml is not None else None
        except ET.ParseError as e:
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

    def get_descriptive_metadata(self) -> str | ET._ElementTree:
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

class OpexDirWriter():

    def __init__(self, folder_path: str, title: Optional[str] = None, description: Optional[str] = None, security_tag: Optional[str] = None, opexns: Optional[str] = "http://www.openpreservationexchange.org/opex/v1.2", **kwargs) -> None:

        self.DEFAULT_EXCLUSIONS = {'opex_generate.exe', 'opex_generate.cmd', 'meta', 'opex_generate.bin', os.path.basename(__file__)}

        ### Generation Presets
        self.sort_key = kwargs.get('sort_key', str.casefold)
        self.exclusion_set = kwargs.get('exclusion_set', self.DEFAULT_EXCLUSIONS)
        self.include_hidden = kwargs.get('include_hidden', False)
        self.filter_flag = kwargs.get('filter_flag', None)
        if self.filter_flag is not None and self.filter_flag not in {"only_files", "only_dir"}:
            logger.error(f'Invalid filter_flag value: {self.filter_flag}. Must be "only_files", "only_dirs", or None.')
            raise ValueError(f'Invalid filter_flag value: {self.filter_flag}. Must be "only_files", "only_dirs", or None.')

        if folder_path.startswith(u'\\\\?\\'):
            self.folder_path = folder_path.replace(u'\\\\?\\', "")
        else:
            self.folder_path = folder_path
        self.opexns = opexns
        self.opex_root = ET.Element(f"{{{self.opexns}}}OPEXMetadata", nsmap={"opex":self.opexns})
        self.transfer_opex = ET.SubElement(self.opex_root, f"{{{self.opexns}}}Transfer")
        self.manifest_opex = ET.SubElement(self.transfer_opex, f"{{{self.opexns}}}Manifest")
        self.folders_opex = ET.SubElement(self.manifest_opex, f"{{{self.opexns}}}Folders")
        self.files_opex = ET.SubElement(self.manifest_opex, f"{{{self.opexns}}}Files")

        self.sourceid = kwargs.get('sourceid', None)
        if self.sourceid is not None:
            self.sourceid_xml = ET.SubElement(self.transfer_opex, f"{{{self.opexns}}}SourceID")
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

        self.identifiers: dict = kwargs.get('identifiers', None)

        if any([self.title, self.description, self.security_tag, self.identifiers]):
            self.properties_opex = ET.SubElement(self.opex_root, f"{{{self.opexns}}}Properties")
            if self.title:
                self.title_opex = ET.SubElement(self.properties_opex, f"{{{self.opexns}}}Title")
                self.title_opex.text = str(self.title)
            if self.description:
                self.description_opex = ET.SubElement(self.properties_opex, f"{{{self.opexns}}}Description")
                self.description_opex.text = str(self.description)
            if self.security_tag:
                self.security_tag_opex = ET.SubElement(self.properties_opex, f"{{{self.opexns}}}SecurityDescriptor")
                self.security_tag_opex.text = str(self.security_tag)
            if self.identifiers:
                self.identifiers_opex = ET.SubElement(self.properties_opex, f"{{{self.opexns}}}Identifiers")
                for id_type, id_value in self.identifiers.items():
                    ident_opex = ET.SubElement(self.identifiers_opex, f"{{{self.opexns}}}Identifier")
                    ident_opex.set("type", id_type)
                    ident_opex.text = str(id_value)

        self.descriptive_metadata: str | ET._ElementTree = kwargs.get('descriptive_metadata', None)

        if self.descriptive_metadata is not None:
            self.descmeta_opex = ET.SubElement(self.opex_root, f"{{{self.opexns}}}DescriptiveMetadata")
            if isinstance(self.descriptive_metadata, str):
                try:
                    self.descmeta_opex.append(ET.fromstring(self.descriptive_metadata))
                except ET.ParseError as e:
                    logger.exception(f'Failed to parse descriptive metadata XML string: {e}')
                    raise
            elif isinstance(self.descriptive_metadata, str) and self.descriptive_metadata.endswith('.xml'):
                try:
                    tree = ET.parse(self.descriptive_metadata)
                    self.descmeta_opex.append(tree.getroot())
                except (ET.ParseError, FileNotFoundError) as e:
                    logger.exception(f'Failed to parse descriptive metadata XML file: {e}')
                    raise
            elif isinstance(self.descriptive_metadata, ET._ElementTree):
                try:
                    self.descmeta_opex.append(self.descriptive_metadata.getroot())
                except ET.ParseError as e:
                    logger.exception(f'Failed to parse descriptive metadata XML tree: {e}')
                    raise
        # Handling Fixities for PAX Folders
        # if self.OMG.fixity and self.OMG.pax_fixity_flag is True and self.folder_path.endswith(".pax"):
        #     self.fixities = ET.SubElement(self.transfer, f"{{{self.opexns}}}Fixities")
        #     tmp_list_fixity = self.OMG.generate_pax_folder_opex_fixity(self.folder_path, self.fixities, self.files, self.OMG.fixity)
        #     self.OMG.list_fixity.extend(tmp_list_fixity)
        #     #self.OMG.list_path.extend(tmp_list_path)

    def generate_dir_manifest(self, path: str, filter_flag: Optional[str] = None) -> None:
        for f in self._filter_manifest(path, self.include_hidden, self.exclusion_set, self.sort_key):
            f: str
            if os.path.isdir(f):
                if filter_flag is not None and filter_flag == "only_dirs":
                    continue
                folder_opex = ET.SubElement(self.folders_opex, f"{{{self.opexns}}}Folder")
                folder_opex.text = os.path.basename(f)
            elif os.path.isfile(f) and f.endswith('.opex'):
                if filter_flag is not None and filter_flag == "only_files":
                    continue
                file_opex = ET.SubElement(self.files_opex, f"{{{self.opexns}}}File")
                file_opex.set("type", "metadata")
                file_opex.text = os.path.basename(f)
            elif os.path.isfile(f):
                if filter_flag is not None and filter_flag == "only_files":
                    continue
                file_opex = ET.SubElement(self.files_opex, f"{{{self.opexns}}}File")
                file_opex.set("type", "content")
                file_opex.set("size", str(os.path.getsize(f)))
                file_opex.text = os.path.basename(f)
            else:
                logger.warning(f'Unknown file type for: {f}')

    def _filter_manifest(self, path: str, include_hidden: Optional[bool] = False,
                            exclusion_set: Optional[set] = {'opex_generate.exe', 'opex_generate.cmd', 'meta', 'opex_generate.bin', os.path.basename(__file__)},
                            sort_key: Optional[Callable] = str.casefold,
                            include_opex: Optional[bool] = True) -> list:
        try:
            list_directories = []
            for f in os.scandir(path):
                full_path = win_256_check(os.path.join(path, f.name))
                if f.name in exclusion_set:
                    continue
                if include_opex is False and f.name.endswith('.opex'):
                    continue
                if include_hidden is False:
                    if f.name.startswith('.') or filter_win_hidden(full_path):
                        continue
                list_directories.append(full_path)
            return sorted(list_directories, key=sort_key)

        except Exception as e:
            logger.exception(f'Failed to Filter Directories: {e}')
            raise

    def generate_opex(self) -> ET._Element:
        self.generate_dir_manifest(self.folder_path)
        return self.opex_root

    def generate_opex_str(self) -> str:
        self.generate_dir_manifest(self.folder_path)
        return ET.tostring(self.opex_root, pretty_print=True, xml_declaration=True, encoding="UTF-8", standalone=True)

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
            opex = ET.tostring(self.opex_root, pretty_print=True, xml_declaration=True, encoding="UTF-8", standalone=True)
            with open(f'{opex_path}', 'w', encoding="UTF-8") as writer:
                logger.info(f'Writing OPEX manifest to: {opex_path}')
                writer.write(opex.decode('UTF-8'))
            return opex_path

class OpexFileReader():
    def __init__(self, file_path: str) -> None:
        if file_path.startswith(u'\\\\?\\'):
            self.file_path = file_path.replace(u'\\\\?\\', "")
        else:
            self.file_path = file_path
        try:
            self.tree = ET.parse(self.file_path)
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
            self.identifiers = {} if self.identifiers_elm is not None else None
            self.sourceid_elm = self.tree.find(f'.//{{{self.opexns}}}SourceID') if self.tree.find(f'.//{{{self.opexns}}}SourceID') is not None else None
            self.sourceid = self.sourceid_elm.text if self.sourceid_elm is not None else None
            if self.identifiers_elm is not None:
                for ident in self.identifiers_elm or []:
                    self.identifiers.update({ident.attrib.get('type'): ident.text})
            self.fixities_elm = self.tree.findall(f'.//{{{self.opexns}}}Fixities/{{{self.opexns}}}Fixity') if self.tree.findall(f'.//{{{self.opexns}}}Fixities/{{{self.opexns}}}Fixity') is not None else None
            self.fixities = {} if self.fixities_elm is not None else None
            if self.fixities_elm is not None:
                for fix in self.fixities_elm:
                    self.fixities.update({fix.attrib.get('type'): fix.attrib.get('value')})
                    if fix.attrib.get('path') is not None:
                        self.fixities.update({f"path": fix.attrib.get('path')})
            self.descriptive_metadata_elm = self.tree.find(f'.//{{{self.opexns}}}DescriptiveMetadata') if self.tree.find(f'.//{{{self.opexns}}}DescriptiveMetadata') is not None else None
            self.descriptive_metadata = ET.tostring(self.descriptive_metadata_elm) if self.descriptive_metadata_elm is not None else None
        except ET.ParseError as e:
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

    def get_descriptive_metadata(self) -> str | ET._ElementTree:
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


class OpexFileWriter():
    def __init__(self, file_path: str, title: str = None, description: str = None, security_tag: str = None, opexns: str = "http://www.openpreservationexchange.org/opex/v1.2", **kwargs) -> None:

        self.opexns = opexns

        if file_path.startswith(u'\\\\?\\'):
            self.file_path = file_path.replace(u'\\\\?\\', "")
        else:
            self.file_path = file_path

        self.opex_root = ET.Element(f"{{{self.opexns}}}OPEXMetadata", nsmap={"opex":self.opexns})
        self.transfer_opex = ET.SubElement(self.opex_root, f"{{{self.opexns}}}Transfer")

        self.sourceid = kwargs.get('sourceid', None)
        if self.sourceid is not None:
            self.sourceid_opex = ET.SubElement(self.transfer_opex,f"{{{self.opexns}}}SourceID")
            self.sourceid_opex.text = self.sourceid

        self.generate_fixity: list = kwargs.get('generate_fixity', None)

        self.fixity_list: list[Dict] = kwargs.get('fixity', None)

        if self.generate_fixity is not None and self.fixity_list is not None:
            logger.warning('Both generate_fixity and fixity arguments provided. Will use fixitity_list and ignore generation.')
            self.generate_fixity = None
        if self.generate_fixity is not None and len(self.generate_fixity) > 0 and (not self.file_path.endswith('.pax') and not self.file_path.endswith('pax.zip')):
            self.fixities_opex = ET.SubElement(self.transfer_opex, f"{{{self.opexns}}}Fixities")
            for fix in self.generate_fixity:
                hash_value = HashGenerator(algorithm = fix, buffer = kwargs.get('buffer')).hash_generator(self.file_path)
                self.fixity_opex = ET.SubElement(self.fixities_opex, f"{{{self.opexns}}}Fixity")
                self.fixity_opex.set("type", fix)
                self.fixity_opex.set("value", hash_value)
        elif kwargs.get('pax_flag', False) is True and self.generate_fixity is not None and len(self.generate_fixity) > 0 and (self.file_path.endswith('.pax') or self.file_path.endswith('pax.zip')):
            self.fixities_opex = ET.SubElement(self.transfer_opex, f"{{{self.opexns}}}Fixities")
            for fix in self.generate_fixity:
                with zipfile.ZipFile(self.file_path, 'r') as z:
                    for zfile in z.filelist:
                        hash_value = HashGenerator(algorithm = fix, buffer = kwargs.get('buffer')).hash_generator_pax_zip(self.file_path, zfile)
                        self.fixity_opex = ET.SubElement(self.fixities_opex, f"{{{self.opexns}}}Fixity")
                        self.fixity_opex.set("path", zfile.filename.replace('\\', '/'))
                        self.fixity_opex.set("type", fix)
                        self.fixity_opex.set("value", hash_value)
        if self.fixity_list is not None and len(self.fixity_list) > 0:
            self.fixities_opex = ET.SubElement(self.transfer_opex, f"{{{self.opexns}}}Fixities")
            for fix in self.fixity_list:
                if isinstance(fix, dict):
                    self.fixity_opex = ET.SubElement(self.fixities_opex, f"{{{self.opexns}}}Fixity")
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

        self.identifiers: dict = kwargs.get('identifiers', None)

        if any([self.title, self.description, self.security_tag, self.identifiers]):
            self.properties_opex = ET.SubElement(self.opex_root, f"{{{self.opexns}}}Properties")
            if self.title is not None:
                self.title_opex = ET.SubElement(self.properties_opex, f"{{{self.opexns}}}Title")
                self.title_opex.text = str(self.title)
            if self.description is not None:
                self.description_opex = ET.SubElement(self.properties_opex, f"{{{self.opexns}}}Description")
                self.description_opex.text = str(self.description)
            if self.security_tag is not None:
                self.security_tag_opex = ET.SubElement(self.properties_opex, f"{{{self.opexns}}}SecurityDescriptor")
                self.security_tag_opex.text = str(self.security_tag)
            if self.identifiers is not None and isinstance(self.identifiers, dict) and len(self.identifiers) > 0:
                self.identifiers_opex = ET.SubElement(self.properties_opex, f"{{{self.opexns}}}Identifiers")
                for key, value in self.identifiers.items():
                    self.ident_opex = ET.SubElement(self.identifiers_opex, f"{{{self.opexns}}}Identifier")
                    self.ident_opex.set("type", key)
                    self.ident_opex.text = str(value)

        self.descriptive_metadata: str | ET._ElementTree = kwargs.get('descriptive_metadata', None)
        if self.descriptive_metadata is not None:
            self.descmeta_opex = ET.SubElement(self.opex_root, f"{{{self.opexns}}}DescriptiveMetadata")
            if isinstance(self.descriptive_metadata, str):
                try:
                    self.descmeta_opex.append(ET.fromstring(self.descriptive_metadata))
                except ET.ParseError as e:
                    logger.exception(f'Failed to parse descriptive metadata XML string: {e}')
                    raise
            elif isinstance(self.descriptive_metadata, str) and self.descriptive_metadata.endswith('.xml'):
                try:
                    tree = ET.parse(self.descriptive_metadata)
                    self.descmeta_opex.append(tree.getroot())
                except (ET.ParseError, FileNotFoundError) as e:
                    logger.exception(f'Failed to parse descriptive metadata XML file: {e}')
                    raise
            elif isinstance(self.descriptive_metadata, ET._ElementTree):
                try:
                    self.descmeta_opex.append(self.descriptive_metadata.getroot())
                except ET.ParseError as e:
                    logger.exception(f'Failed to parse descriptive metadata XML tree: {e}')
                    raise

    def generate_opex(self) -> ET._Element:
        return self.opex_root

    def generate_opex_str(self) -> str:
        return ET.tostring(self.opex_root, pretty_print=True, xml_declaration=True, encoding="UTF-8", standalone=True)

    def write_opex_file(self, opex_path: str = None, file_override: bool = False) -> str:
        if opex_path is None:
            opex_path = win_256_check(self.file_path + ".opex")
        else:
            opex_path = win_256_check(opex_path)
        if os.path.exists(opex_path) and file_override is False:
            logger.warning(f"Opex file already exists at: {opex_path}, skipping write.")
            return None
        else:
            opex = ET.tostring(self.opex_root, pretty_print=True, xml_declaration=True, encoding="UTF-8", standalone=True)
            with open(f'{opex_path}', 'w', encoding="UTF-8") as writer:
                logger.info(f'Writing OPEX manifest to: {opex_path}')
                writer.write(opex.decode('UTF-8'))
            return opex_path

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
