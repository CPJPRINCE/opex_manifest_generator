"""
Opex Manifest Generator tool

This tool is utilised to recursively generate Opex files for files / directories for use in uploading to Preservica and other OPEX conforming systems.

author: Christopher Prince
license: Apache License 2.0"
"""

from lxml import etree
import pandas as pd
import os, configparser, logging
from typing import Optional, Dict, List, Any
from auto_reference_generator import ReferenceGenerator
from auto_reference_generator.common import export_list_txt, \
    export_xl, \
    export_csv, \
    export_json, \
    export_ods, \
    export_xml, \
    define_output_file
from pandas.api.types import is_datetime64_any_dtype
from .hash import HashGenerator
from .common import remove_tree,\
    win_256_check,\
    filter_win_hidden,\
    check_nan,\
    check_bool
from datetime import datetime
from .opexLib import OpexDirWriter, OpexFileWriter

logger = logging.getLogger(__name__)

class ProgressBar():
    import tqdm
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.description = description
        self.progress_bar = self.tqdm.tqdm(total=self.total, desc=self.description, unit="item")
    def start(self):
        return self
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
    :param delimiter: set the delimiter for auto_ref, default is "/".
    :param max_workers: set the number of workers for multithreading, default is 1 to use single thread, set to 0 to use all available cores
    :param column_sensitivity: set whether column header matching should be case sensitive, default is False
    :param show_progress_bar: set whether to show a progress bar during generation, default is False
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
                 column_sensitivity: bool = False,
                 show_progress_bar: bool = False,
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

        self.show_progress_bar = show_progress_bar
        self.column_sensitivity = column_sensitivity,

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
        self.progress = None

    def parse_config(self, options_file: str = os.path.join('options','options.properties')) -> None:
        config = configparser.ConfigParser()
        read_config = config.read(options_file, encoding='utf-8')
        if not read_config:
            logger.warning(f"Options files not found or not reable: {options_file}. Using defaults.")

        section = config['options'] if 'options' in config else {}

        if self.column_sensitivity:
            section = {k.lower(): v for k, v in section.items()}

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
                xml_file = etree.parse(path)
                root_element = etree.QName(xml_file.find('.'))
                root_element_ln = root_element.localname
                for elem in xml_file.findall(".//"):
                    if elem.getchildren():
                        pass
                    else:
                        elem_path = xml_file.getelementpath(elem)
                        elem = etree.QName(elem)
                        elem_lnpath = elem_path.replace(f"{{{elem.namespace}}}", root_element_ln + ":")
                        print(elem_lnpath)
        except Exception as e:
            logger.exception(f'Failed to print Descriptive metadta files, ensure correct path {e}')
            raise

    def convert_descriptive_xmls(self) -> None:
        try:
            for file in os.scandir(self.metadata_dir):
                path = os.path.join(self.metadata_dir, file.name)
                xml_file = etree.parse(path)
                root_element = etree.QName(xml_file.find('.'))
                root_element_ln = root_element.localname
                column_list = []
                for elem in xml_file.findall(".//"):
                    if elem.getchildren():
                        pass
                    else:
                        elem_path = xml_file.getelementpath(elem)
                        elem = etree.QName(elem)
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

    def _set_input_flags(self) -> None:
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
                self._set_input_flags()
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

                if self.column_sensitivity:
                    self.column_headers = [header.lower() for header in self.column_headers]
                    self.df.columns = self.column_headers

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
            log_msg = 'Dataframe not initialised, cannot perform lookup'
            logger.error(log_msg)
            raise RuntimeError(log_msg)
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
            '\nafter generating your input spreadsheetree. An opex will still be generated but information may be missing.' \
            '\nTo ensure metadata match up please regenerate the spreadsheetree.')
        except Exception as e:
            logger.exception(f'Error looking up Index from Dataframe: {e}')
            raise

    def xip_df_lookup(self, idx: pd.Index) -> tuple:
        if getattr(self, 'df', None) is None:
            log_msg = 'Dataframe not initialised, cannot perform lookup'
            logger.error(log_msg)
            raise RuntimeError(log_msg)
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
            '\nafter generating your input spreadsheetree. An opex will still be generated, but information may be missing.'
            '\nTo ensure metadata match up please regenerate the spreadsheetree.')
        except Exception as e:
            logger.exception(f'Error looking up XIP from Dataframe: {e}')
            raise

    def removal_df_lookup(self, idx: pd.Index) -> bool:
        if getattr(self, 'df', None) is None:
            log_msg = 'Dataframe not initialised, cannot perform lookup'
            logger.error(log_msg)
            raise RuntimeError(log_msg)
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
            '\nafter generating your input spreadsheetree. An opex will still be generated, but information may be missing.'
            '\nTo ensure metadata match up please regenerate the spreadsheetree.')
            return False
        except Exception as e:
            logger.exception(f'Error looking up Removals from Dataframe: {e}')
            raise

    def ignore_df_lookup(self, idx: pd.Index) -> bool:
        if getattr(self, 'df', None) is None:
            log_msg = 'Dataframe not initialised, cannot perform lookup'
            logger.error(log_msg)
            raise RuntimeError(log_msg)
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
            '\nafter generating your input spreadsheetree. An opex will still be generated but information may be missing.'
            '\nTo ensure metadata match up please regenerate the spreadsheetree.')
            return False
        except Exception as e:
            logger.exception(f'Error looking up Ignore from Dataframe: {e}')
            raise

    def sourceid_df_lookup(self, idx: pd.Index) -> Optional[str]:
        if getattr(self, 'df', None) is None:
            log_msg = 'Dataframe not initialised, cannot perform lookup'
            logger.error(log_msg)
            raise RuntimeError(log_msg)
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
            '\nafter generating your input spreadsheetree. An opex will still be generated but information may be missing.'
            '\nTo ensure metadata match up please regenerate the spreadsheetree.')
            return None
        except Exception as e:
            logger.exception(f'Error looking up SourceID from Dataframe: {e}')
            raise

    def hash_df_lookup(self, idx: pd.Index, algorithms: list) -> Optional[Dict[str, str]]:
        if getattr(self, 'df', None) is None:
            log_msg = 'Dataframe not initialised, cannot perform lookup'
            logger.error(log_msg)
            raise RuntimeError(log_msg)
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
            '\nafter generating your input spreadsheetree. An opex will still be generated but information may be missing.'
            '\nTo ensure metadata match up please regenerate the spreadsheetree.')
            return None
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
            log_msg = 'Dataframe not initialised, cannot perform lookup'
            logger.error(log_msg)
            raise RuntimeError(log_msg)
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
            '\nafter generating your input spreadsheetree. An opex will still be generated but xml information may be missing.' \
            '\nTo ensure metadata match up please regenerate the spreadsheetree.')
            return None
        except Exception as e:
            logger.exception(f'Error looking up Identifiers: {e}')
            raise

    def init_generate_descriptive_metadata(self) -> List[Dict[str, Any]]:
        """
        Initialises the descriptive metadata by parsing the XML files in the metadata directory, generating a list of the elements and their namespaces, and comparing them against the column headers in the spreadsheet to filter out non-matching data.
        The resulting list of matching elements is stored in self.xml_files for use in generating the descriptive metadata in the Opex manifest.
        """
        try:
            self.xml_files: List[Dict[str, Any]] = []
            for file in os.scandir(self.metadata_dir):
                list_xml: List[Dict[str,Any]] = []
                if file.name.endswith('xml'):
                    path = os.path.join(self.metadata_dir, file.name)
                    """
                    Generates info on the elements of the XML Files placed in the Metadata directory.
                    Composed as a list of dictionaries.
                    """
                    try:
                        xml_file = etree.parse(path)
                    except etree.XMLSyntaxError as e:
                        logger.exception(f'XML Syntax Error parsing file {file.name}: {e}')
                        raise
                    except FileNotFoundError as e:
                        logger.exception(f'XML file not found {file.name}: {e}')
                        raise
                    root_element = etree.QName(xml_file.find('.'))
                    root_element_ln = root_element.localname
                    root_element_ns = root_element.namespace
                    elements_list = []
                    for elem in xml_file.findall('.//'):
                        elem_path = xml_file.getelementpath(elem)
                        elem = etree.QName(elem)
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
                    except KeyError as e:
                        logger.exception(f'Key Error comparing XML elements to column headers for file {file.name}: {e}')
                        raise
                    except IndexError as e:
                        log_msg = f'Index Error comparing XML elements to column headers for file {file.name}: {e}'
                        logger.warning(log_msg)
                        continue
                    except Exception as e:
                        logger.exception(f'Error comparing XML elements to column headers for file {file.name}: {e}')
                        raise
                if len(list_xml) > 0:
                    self.xml_files.append({'data': list_xml, 'localname': root_element_ln, 'xmlfile': path})
                    logger.info(f'Matching columns found in spreadsheet for XML file: {file.name}, added to metadata generation list.')
                else:
                    logger.debug(f'No matching columns found in spreadsheet for XML file: {file.name}, skipping this file for metadata generation.')
            return self.xml_files
        except FileNotFoundError:
            logger.exception(f'Metadata directory not found at path: {self.metadata_dir}')
            raise
        except Exception as e:
            logger.exception(f'Failed to intialise XML Metadata: {e}')
            raise

    def generate_descriptive_metadata(self, idx: pd.Index) -> etree._Element:
        """
        Composes the data into an xml file.
        Iterates through the list of matching elements generated in init_generate_descriptive_metadata, looks up the corresponding value in the spreadsheet for each element, and inserts it into the XML file at the correct path.
        The resulting XML element is returned for inclusion in the Opex manifest.

        This version returns an XML element containing the descriptive metadata, which can be included in the Opex manifest. It iterates through the list of matching elements generated in init_generate_descriptive_metadata, looks up the corresponding value in the spreadsheet for each element, and inserts it into the XML file at the correct path. If any issues are encountered during this process, such as missing columns or invalid data, appropriate warnings are logged and the function continues processing the remaining elements. If a critical error occurs, such as a KeyError or IndexError, it is logged and raised to ensure that the issue can be addressed.
        """
        try:
            xml_desc_elem = etree.Element()
            for xml_file in self.xml_files:
                xml_file: Dict[str, Any]
                xml_data = xml_file.get('data')
                #xnames: list[Optional[str]] = []
                #xnames = [x.get('XName') for x in xml_data if isinstance(x, dict)] if xml_data is not None else []
                localname = xml_file.get('localname')
                localns = xml_file.get('localns')
                if localname is None or localns is None:
                    logger.warning(f'Missing localname or localns for XML file: {xml_file.get("xmlfile")}, skipping XML Generation for this file.')
                    continue
                if len(xml_data) == 0 or xml_data is None:
                    logger.warning(f'No matching columns found for XML file: {xml_file.get("xmlfile")}, skipping XML Generation for this file.')
                    continue
                else:
                    xml_new = etree.parse(xml_file.get('xmlfile'))
                    for elem_dict in xml_data:
                        if not isinstance(elem_dict, dict):
                            logger.warning(f'Invalid element data for {elem_dict} in file {xml_file.get("xmlfile")}, skipping this element.')
                            continue
                        name = elem_dict.get('Name')
                        path = elem_dict.get('Path')
                        elmns = elem_dict.get('Namespace')
                        if not isinstance(name, str) or not isinstance(path, str) or not isinstance(elmns, str):
                            logger.warning(f'Missing Name or Path or Namespace for element {elem_dict} in file {xml_file.get("xmlfile")}, skipping this element.')
                            continue
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
                            n = path.replace(localname + ":", f"{{{elmns}}}")
                            elem = xml_new.find(f'./{n}')
                            if elem is None:
                                logger.warning(f'XML element not found for path: {n, path} in {xml_file}')
                                continue
                        elif self.metadata_flag in {'flat'}:
                            n = name.split(':')[-1]
                            elem = xml_new.find(f'.//{{{elmns}}}{n}')
                            if elem is None:
                                logger.warning(f'XML element not found for name: {name, path} in {xml_file}')
                                continue
                        if elem is not None:
                            elem.text = str(val)
                    xml_desc_elem.append(xml_new.find('.'))
            return xml_desc_elem
        except KeyError as e:
            logger.exception(f'Key Error in XML Lookup: {e}' \
            '\n Please ensure column header\'s are an exact match.')
            raise
        except IndexError as e:
            logger.warning(f'Index Error: {e}' \
            '\nIt is likely you have removed or added a file/folder to the directory' \
            'after generating your input spreadsheetree. An opex will still be generated but with no xml metadata.' \
            '\nTo ensure metadata match up please regenerate the spreadsheetree.')
            return None
        except Exception as e:
            logger.exception(f'General Error in XML Lookup: {e}')
            raise

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
                    if self.pax_flag:
                        logger.debug('PAX fixity enabled, generating fixity for all files in directory and subdirectories.')
                        f_list.extend([f.path for f in os.scandir(path) if f.is_dir() and f.name.endswith('.pax')])
                    self._process_multithread_fixity(f_list)
                else:
                    logger.debug('Hash from spreadsheet enabled and columns found for all algorithms, skipping fixity generation.')
            else:
                f_list = [f.path for f in os.scandir(path) if f.is_file() and not f.name.endswith('.opex')]
                if self.pax_flag:
                    logger.debug('PAX fixity enabled, generating fixity for all files in directory and subdirectories.')
                    f_list.extend([f.path for f in os.scandir(path) if f.is_dir() and f.name.endswith('.pax')])
                self._process_multithread_fixity(f_list)
                logger.debug('Multithreading enabled for fixity generation, gathering file list.')

        for f in os.scandir(path):
            if f.is_dir():
                if self.pax_flag and f.name.endswith('.pax'):
                    hash_list,generate_fixity = self._process_fixity(f.path)
                    OpexDirWriter(f.path,
                                title = self.title,
                                description = self.description,
                                security_tag = self.security_tag,
                                source_id = self.source_id,
                                identifers = self.identifiers,
                                descriptive_metadata = self.descriptive_metadata,
                                include_hidden = self.hidden_flag,
                                sort_key = self.sort_key,
                                filter_flag = self.filter_flag,
                                generate_fixity = generate_fixity if self.pax_flag else None,
                                fixity_list = hash_list if self.pax_flag else None,
                                pax_flag = self.pax_flag
                                ).write_opex_manifest(f.path + '.opex')
                    continue
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
                                    generate_fixity = generate_fixity,
                                    pax_flag = self.pax_flag
                                    ).write_opex_file()
                if self.progress:
                    self.progress.update()

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
                        filter_flag = self.filter_flag,
                        pax_flag = self.pax_flag
                        ).write_opex_manifest()
            if self.progress:
                self.progress.update()

    def display_progress(self) -> None:
        directory_count = 0
        file_count = 0
        for _, _, files in os.walk(self.root):
            directory_count += 1
            file_count += len([name for name in files if not name.endswith('.opex')])
        total = directory_count + file_count
        self.progress = ProgressBar(total, "Processing Opex Manifests").start()

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
            log_msg = 'Metadata generation requires Auto Reference or Input file to be specified.'
            logger.error(log_msg)
            raise ValueError(log_msg)
        elif self.metadata_flag is not None and self.df is not None:
            self.init_generate_descriptive_metadata()
        else:
            pass
        self.hash_map: Dict[str,Dict] = {}

        # If Multithreading goes at top will lose continous running...
        # if self.fixity and self.max_workers > 1:
        #     file_list = [os.path.join(dir, file) for dir, _, files in os.walk(self.root) for file in files if not file.endswith('.opex')]
        #     self._process_multithread_fixity(file_list, hash_map = self.hash_map)

        if self.show_progress_bar:
            self.display_progress()
        try:
            self._process_loop(self.root)
        finally:
            if self.progress:
                self.progress.close()
        if self.fixity:
            output_path = define_output_file(self.output_path, self.root, self.METAFOLDER, self.meta_dir_flag, output_suffix = self.FIXITY_SUFFIX, output_format = "txt")
            if self.fixity_export_flag:
                export_list_txt(self.list_fixity, output_path)
        if self.removal_flag:
            output_path = define_output_file(self.output_path, self.root, self.METAFOLDER, self.meta_dir_flag, output_suffix = self.REMOVALS_SUFFIX, output_format = "txt")
            if self.removal_export_flag:
                export_list_txt(self.removal_list, output_path)
