"""
Cli interaction.

author: Christopher Prince
license: Apache License 2.0"
"""

import argparse, os, inspect, logging
from .opexManifest import OpexManifestGenerator
from importlib import metadata
from datetime import datetime
from .common import running_time

logger = logging.getLogger(__name__)

def _get_version():
    try:
        return metadata.version("opex_manifest_generator")
    except metadata.PackageNotFoundError:
        return "0.0.0"

def create_parser():

    parser = argparse.ArgumentParser(prog="Opex Manifest Generator", description = "OPEX Manifest Generator for Preservica Uploads")

    parser.add_argument("--version", action = 'version', version = '%(prog)s {version}'.format(version =_get_version())),
    parser.add_argument('root', nargs='?', default = os.getcwd(),
                        help = """The root path to generate Opexes for, will recursively traverse all sub-directories.
                        Generates an Opex for each folder & (depending on options) file in the directory tree.""")

    # Opex Options
    opexgroup = parser.add_argument_group('Opex Options', 'Options that control the generation of Opex Manifests')

    opexgroup.add_argument("-fx", "--fixity", required = False, nargs = '*', default = None,
                        choices = ['SHA-1', 'MD5', 'SHA-256', 'SHA-512'], type = fixity_helper, action=EmptyIsTrueFixity,
                        help="Generates a hash for each file and adds it to the opex.\n" \
                        "Can select one or more algorithms to utilise: {-fx MD5 SHA-1}\n" \
                        "If no algorithm is specified defaults to SHA-1.\n")
    opexgroup.add_argument("-pax", "--pax-flag", required = False, action = 'store_true', default = False,
                        help="""Enables recognition of PAX Folders and use of PAX fixity generation, in line with Preservica's model.
                        "Files / folders ending in .pax or .pax.zip will have individual files in folder / zip added to Opex.""")
    opexgroup.add_argument("--max-workers", required = False, nargs='?', type=int, default = 1,
                        help="""Sets the number of Threads to use for Fixity Generation.""")
    opexgroup.add_argument("-z", "--zip", required = False, action = 'store_true',
                        help="Set to zip files")
    opexgroup.add_argument("--remove-zipped-files", required = False, action = 'store_true',
                        help="Set to remove the original files that have been zipped")
    opexgroup.add_argument("--remove-empty", required = False, action = 'store_true', default = False,
                        help = "Remove and log empty directories from root. Log will be exported to 'meta' / output folder.")
    opexgroup.add_argument("--hidden", required = False, action = 'store_true', default = False,
                        help="Set whether to include hidden files and folders")
    opexgroup.add_argument("-clr", "--clear-opex", required = False, action = 'store_true', default = False,
                        help = """Clears existing opex files from a directory. If set with no further options will only clear opexes;
                        if multiple options are set will clear opexes and then run the program""")
    opexgroup.add_argument("-opt","--options-file", required = False, default=os.path.join(os.path.dirname(__file__),'options','options.properties'),
                        help="Specify a custom Options file, changing the set presets for column headers (Title,Description,etc)")

    # Input Override Options
    inputgroup = parser.add_argument_group('Input Override Options', 'Options that control the Input Override features')

    inputgroup.add_argument("-i", "--input", required = False, nargs='?',
                        help="Set to utilise a CSV / XLSX spreadsheet to import data from")
    inputgroup.add_argument("-mdir","--metadata-dir", required=False, nargs= '?',
                        default = os.path.join(os.path.dirname(os.path.realpath(__file__)), "metadata"),
                        help="Specify the metadata directory to pull XML files from")
    inputgroup.add_argument("-m", "--metadata", required = False, const = 'e', default = None,
                        nargs = '?', choices = ['exact', 'flat'], type = metadata_helper,
                        help="Set whether to include xml metadata fields in the generation of the Opex")
    inputgroup.add_argument("-rm", "--remove", required = False, action = "store_true", default = False,
                        help="Set whether to enable removals of files and folders from a directory. ***Currently in testing")
    inputgroup.add_argument("--print-xmls", required = False, action = "store_true", default = False,
                        help="Prints the elements from your xmls to the consoles")
    inputgroup.add_argument("--convert-xmls", required=False, action ='store_true', default = False,
                         help="Convert XMLs templates files in mdir to spreadsheets/csv files")
    inputgroup.add_argument("--autoref-options", required = False, default = None,
                        help="Specify a custom Auto Reference Options file, changing the set presets for Input Override / Auto Reference Generator")
    inputgroup.add_argument("--column-sensitivity", required = False, action = 'store_false', default = False,
                        help="Set whether to make column header matching for input spreadsheets case sensitive, default is sensitive")

    # Auto Reference Options
    autorefgroup = parser.add_argument_group('Auto Reference Generator Options', 'Options that control the Auto Reference Generator features')

    autorefgroup.add_argument("-r", "--autoref", required = False,
                        choices = ['catalog', 'accession', 'both', 'generic', 'catalog-generic', "accession-generic", "both-generic"],
                        type = autoref_helper,
                        help="""Toggles whether to utilise the auto_reference_generator
                        to generate an on the fly Reference listing.\n
                        There are several options, {catalog} will generate
                        a Archival Reference following an ISAD(G) structure.\n
                        {accession} will create a running number of files.
                        {both} will do both at the same time!
                        {generic} will populate the title and description fields with the folder/file's name,
                        if used in conjunction with one of the above options:
                        {generic-catalog,generic-accession, generic-both} it will do both simultaneously.
                        """)
    autorefgroup.add_argument("-p", "--prefix", required = False, nargs = '+',
                        help= """Assign a prefix when utilising the --autoref option. Prefix will append any text before all generated text.
                        When utilising the {both} option fill in like: [catalog-prefix, accession-prefix] without square brackets.
                        """)
    autorefgroup.add_argument("-s", "--suffix", required = False, nargs = '?', default = '',
                        help= "Assign a suffix when utilising the --autoref option. Suffix will append any text after all generated text.")
    autorefgroup.add_argument("--suffix-option", required = False, choices= ['file', 'directory', 'both'], type = suffix_helper, default = 'files',
                        help = "Set whether to apply the suffix to files, folders or both when utilising the --autoref option.")
    autorefgroup.add_argument("--accession-mode", nargs = '?', required=False, const='file', default=None, choices=["file", 'directory', 'both'], type = suffix_helper,
                        help="""Set the mode when utilising the Accession option in autoref.
                        file - only adds on files, folder - only adds on folders, both - adds on files and folders""")
    autorefgroup.add_argument("-str", "--start-ref", required = False, type=int, nargs = '?', default = 1,
                        help="Set a custom Starting reference for the Auto Reference Generator. The generated reference will")
    autorefgroup.add_argument("-dlm", "--delimiter", required=False,nargs = '?', type = str, default = '/',
                        help="Set a custom delimiter for generated references, default is '/'")
    autorefgroup.add_argument("--sort-by", required=False, nargs = '?', default = 'folders_first', choices = ['folders_first','alphabetical'], type=str.lower,
                        help = "Set the sorting method, 'folders_first' sorts folders first then files alphabetically; 'alphabetically' sorts alphabetically (ignoring folder distinction)")

    # Keywords Options
    keywordsgroup = parser.add_argument_group('Keyword Options', 'Options that control the Keyword features for Auto Reference Generation')

    keywordsgroup.add_argument("-key","--keywords", nargs = '*', default = None,
                        help = "Set to replace reference numbers with given Keywords for folders (only Folders atm). Can be a list of keywords or a JSON file mapping folder names to keywords.")
    keywordsgroup.add_argument("-keym","--keywords-mode", nargs = '?', const = "initialise", choices = ['initialise','firstletters','from_json'], default = 'initialise',
                        help = "Set to alternate keyword mode: 'initialise' will use initials of words; 'firstletters' will use the first letters of the string; 'from_json' will use a JSON file mapping names to keywords")
    keywordsgroup.add_argument("--keywords-case-sensitivity", required = False, action = 'store_false', default = True,
                        help = "Set to change case keyword matching sensitivity. By default keyword matching is insensitive")
    keywordsgroup.add_argument("--keywords-retain-order", required = False, default = False, action = 'store_true',
                        help = "Set when using keywords to continue reference numbering. If not used keywords don't 'count' to reference numbering, e.g. if using initials 'Project Alpha' -> 'PA' then the next folder/file will still be '001' not '003'")
    keywordsgroup.add_argument("--keywords-abbreviation-number", required = False, nargs='+', default = None, type = int,
                        help = "Set to set the number of letters to abbreviate for 'firstletters' mode, does not impact 'initialise' mode.")

    # Export Options
    exportgroup = parser.add_argument_group('Export Options', 'Options that control various export features')

    exportgroup.add_argument("--log-level", required=False, nargs='?', choices=['DEBUG','INFO','WARNING','ERROR'], default=None, type=str.upper,
                        help="Set the logging level (default: INFO)")
    exportgroup.add_argument("--log-file", required=False, nargs='?', default=None,
                        help="Optional path to write logs to a file (default: stdout)")
    exportgroup.add_argument("-v", "--verbose", required = False, action = 'store_false', default = True,
                        help="Set whether to output log stream instead of progress bar during processing, default is True (will not output log stream, will show progress bar)" \
                             "Enable to display log stream but disable progress bar")
    exportgroup.add_argument("-o", "--output", required = False, nargs = '?',
                        help = "Sets the output of the meta folder to send any generated files (Remove Empty, Fixity List, Autoref Export) to. Can be used in conjunction with --disable-meta-dir to set output location without generating meta directory.")
    exportgroup.add_argument("--disable-meta-dir", required = False, action = 'store_false',
                        help = """Set whether to disable the creation of a 'meta' directory for generated files,
                        default behaviour is to always generate this directory""")
    exportgroup.add_argument("--disable-all-exports", required = False, action = 'store_true', default = False,
                        help="Set to prevent all exports (Fixity, Removal, Empty) from being created in the meta directory.")
    exportgroup.add_argument("--disable-fixity-export", required = False, action = 'store_false', default = True,
                        help="""Set whether to export the generated fixity list to a text file in the meta directory.
                        Enabled by default, disable with this flag.""")
    exportgroup.add_argument("--disable-empty-export", required = False, action = 'store_false', default = True,
                        help="""Set whether to export the generated empty list to a text file in the meta directory.
                        Enabled by default, disable with this flag.""")
    exportgroup.add_argument("--disable-removal-export", required = False, action = 'store_false', default = True,
                        help="""Set whether to export the generated removals list to a text file in the meta directory.
                        Enabled by default, disable with this flag.""")
    exportgroup.add_argument("-ex", "--export-autoref", required = False, action = 'store_true', default = False,
                        help="Set whether to export the generated references to an AutoRef spreadsheet")
    exportgroup.add_argument("-fmt", "--output-format", required = False, default = "xlsx", choices = ['xlsx', 'csv','json','ods','xml'], type=fmthelper,
                        help="Set whether to export AutoRef Spreadsheet to: xlsx, csv, json, ods or xml format")

    return parser

def run_cli(args = None):

    # Configure logging early so other modules inherit the settings
    try:
        log_level = getattr(logging, args.log_level.upper()) if args.log_level else logging.INFO
    except Exception:
        log_level = logging.INFO
    log_format = '%(asctime)s %(levelname)-8s [%(name)s] %(message)s'
    handlers = []

    if args.log_file:
        handlers.append(logging.FileHandler(args.log_file, mode='a'))

    if not args.verbose:
        handlers.append(logging.StreamHandler())

    if not handlers:
        handlers.append(logging.NullHandler())

    logging.basicConfig(level=log_level, format=log_format, handlers=handlers)
    logger.debug(
        f'Logging configured (level={logging.getLevelName(log_level)}, '
        f'file={args.log_file or "disabled"}, '
        f'console={not args.verbose})'
    )

    if not os.path.exists(args.root):
        log_msg = (f'Please ensure that root path {args.root} exists. \n'
                   'If you are utilising Windows ensure that the path does not end with \\\' or \\"')
        logger.error(log_msg)
        raise FileNotFoundError(log_msg)

    if isinstance(args.root, str):
        args.root = args.root.strip("\"").rstrip("\\")
    logger.info(f"Running Opex Generation on: {args.root}")

    if not args.output:
        args.output = os.path.abspath(args.root)
        logger.debug(f'Output path set to root directory: {args.output}')
    else:
        args.output = os.path.abspath(args.output)
        logger.info(f'Output path set to {args.output}')

    if args.input and args.autoref:
        log_msg = 'Both Input and Auto ref options have been selected, please use only one...'
        logger.error(log_msg)
        raise ValueError(log_msg)
    if args.remove and not args.input:
        log_msg = 'Removal flag has been given without input, please ensure an input file is utilised when using this option.'
        logger.error(log_msg)
        raise ValueError(log_msg)
    if args.metadata is not None and not args.input:
        logger.warning(f'Warning: Metadata Flag has been given without Input. Metadata won\'t be generated.')

    if args.print_xmls:
        logger.info(f'Printing XMLs in {args.metadata_dir} then ending')
        OpexManifestGenerator(root = args.root, metadata_dir=args.metadata_dir).print_descriptive_xmls()
        raise SystemExit()
    if args.convert_xmls:
        logger.info(f'Converting XMLs in {args.metadata_dir} then ending')
        OpexManifestGenerator(root = args.root, output_format=args.output_format, metadata_dir=args.metadata_dir).convert_descriptive_xmls()
        raise SystemExit()

    if args.disable_all_exports:
        args.fixity_export_flag = False
        args.removal_export_flag = False
        args.empty_export_flag = False
        logger.info('All exports have been prevented via --prevent-all-exports flag.')

    acc_prefix = None
    if args.autoref in {"accession", "accession-generic", "both", "both-generic"} and args.accession_mode is None:
            args.accession_mode = "file"
            logger.debug(f'Accession mode not set, defaulting to "file" mode for accession generation.')

    if args.prefix:
        if args.autoref in {"both", "both-generic"}:
            if len(args.prefix) < 2 or len(args.prefix) > 2:
                log_msg = '"Both" option is selected, please pass only two prefixes: [-p CATALOG_PREFIX ACCESSION_PREFIX]'
                logger.error(log_msg)
                raise ValueError(log_msg)
            for n, a in enumerate(args.prefix):
                if n == 0:
                    args.prefix = str(a)
                elif n == 1:
                    acc_prefix = str(a)
            logger.info(f"Prefixes are set as: \t Catalog: {args.prefix} \t Acc: {acc_prefix}")
        elif args.autoref in {"accession", "accession-generic"}:
            for a in args.prefix:
                acc_prefix = str(a)
            logger.info('Prefix is set as: ' + acc_prefix)
        elif args.autoref in {"catalog", "catalog-generic"}:
            acc_prefix = None
            for a in args.prefix:
                args.prefix = str(a)
            logger.info('Prefix is set as: ' + args.prefix)
        elif args.autoref in {"generic"}:
            logger.info('Using Generic mode')
            pass
        else:
            log_msg = ('An invalid option has been selected, please select a valid option:\n'
                       '{catalog, accession, both, generic, catalog-generic, accession-generic, both-generic}')
            logger.error(log_msg)
            raise ValueError(log_msg)

    if args.fixity:
        logger.info(f'Fixity is activated, using {args.fixity} algorithm')

    sort_key = None
    if args.sort_by:
        if args.sort_by == "folders_first":
            logger.debug('Sorting by folders_first')
            sort_key = lambda x: (os.path.isfile(x), str.casefold(x))
        elif args.sort_by == "alphabetical":
            logger.debug('Sorting by alphabetical')
            sort_key = str.casefold

    if args.remove:
        logger.warning(inspect.cleandoc("\n***WARNING***" \
                                "\nYou have enabled the remove functionality of the program. " \
                                "This action will remove all files and folders listed for removal and any sub-files/sub-folders." \
                                "\nThis process will permanently delete the selected items, with no way recover the items." \
                                "\n***"))
        i = input(inspect.cleandoc("Please type Y if you wish to proceed, otherwise the program will close: "))
        if not i.lower() == "y":
            logger.info("Y not typed, safely aborted...")
            raise SystemExit()
        else:
            logger.info("Confirmation received proceeding to remove files")

    if args.remove_empty:
        logger.warning(inspect.cleandoc("\n***WARNING***" \
                                "\nYou have enabled the remove empty folders functionality of the program. " \
                                "This action will remove all empty folders." \
                                "\nThis process will permanently delete all empty folders, with no way recover the items." \
                                "\n***"))
        i = input(inspect.cleandoc("Please type Y if you wish to proceed, otherwise the program will close: "))
        logger.debug(f'User confirmation for removing empty folders: {i}')
        if not i.lower() == "y":
            logger.info("Y not typed, safely aborted...")
            raise SystemExit()
        else:
            logger.info("Confirmation received proceeding to remove empty folders...")

    start_time = datetime.now()
    OpexManifestGenerator(root = args.root,
                          output_path = args.output,
                          autoref_flag = args.autoref,
                          prefix = args.prefix,
                          suffix = args.suffix,
                          suffix_option = args.suffix_option,
                          accession_mode=args.accession_mode,
                          acc_prefix = acc_prefix,
                          empty_flag = args.remove_empty,
                          empty_export_flag = args.disable_empty_export,
                          removal_flag = args.remove,
                          removal_export_flag = args.disable_removal_export,
                          clear_opex_flag = args.clear_opex,
                          fixity = args.fixity,
                          pax = args.pax_flag,
                          fixity_export_flag = args.disable_fixity_export,
                          start_ref = args.start_ref,
                          export_flag = args.export_autoref,
                          meta_dir_flag = args.disable_meta_dir,
                          metadata_flag = args.metadata,
                          metadata_dir = args.metadata_dir,
                          hidden_flag= args.hidden,
                          zip_flag = args.zip,
                          zip_file_removal= args.remove_zipped_files,
                          input = args.input,
                          output_format = args.output_format,
                          options_file=args.options_file,
                          keywords = args.keywords,
                          keywords_mode = args.keywords_mode,
                          keywords_retain_order = args.keywords_retain_order,
                          keywords_case_sensitivity = args.keywords_case_sensitivity,
                          delimiter = args.delimiter,
                          keywords_abbreviation_number = args.keywords_abbreviation_number,
                          sort_key = sort_key,
                          column_sensitivity= args.column_sensitivity,
                          show_progress_bar = args.verbose,
                          max_workers = args.max_workers
                          ).main()
    logger.info(f"Run Complete! Ran for: {running_time(start_time)}")

def fixity_helper(x: str):
    x = x.upper()
    if x in ('MD5', 'M5', 'M', '5'):
        x = 'MD5'
    if x in ('SHA1', 'SHA-1', 'S1', '1'):
        x = 'SHA-1'
    if x in ('SHA256', 'SHA-256', 'S256', '256'):
        x = 'SHA-256'
    if x in ('SHA512', 'SHA-512', 'S512', '512'):
        x = 'SHA-512'
    if x not in ('SHA-1', 'MD5', 'SHA-256', 'SHA-512'):
        raise argparse.ArgumentTypeError(f"Invalid fixity algorithm: {x}. Valid options are: SHA-1, MD5, SHA-256, SHA-512.")
    return x.upper()

def autoref_helper(x: str):
    x = x.lower()
    if x in ('c', 'catalog', 'catalogue', 'cat'):
        x = 'catalog'
    if x == ('a', 'accession', 'acc'):
        x = 'accession'
    if x == ('b', 'both', 'all'):
        x = 'both'
    if x == ('g', 'generic', 'gen'):
        x = 'generic'
    if x == ('cg', 'catalog-generic', 'catalogue-generic', 'cat-generic', 'catalogue-gen', 'cat-gen', 'catalog-gen'):
        x = 'catalog-generic'
    if x == ('ag', 'accession-generic', 'acc-generic', 'accession-gen', 'acc-gen'):
        x = 'accession-generic'
    if x == ('bg', 'both-generic', 'all-generic', 'all-gen'):
        x = 'both-generic'
    if x not in ('catalog', 'accession', 'both', 'generic', 'catalog-generic', 'accession-generic', 'both-generic'):
        raise argparse.ArgumentTypeError(f"Invalid autoref option: {x}. Valid options are: catalog, accession, both, generic, catalog-generic, accession-generic, both-generic.")
    return x.lower()

def suffix_helper(x: str):
    x = x.lower()
    if x in ('f', 'file', 'files'):
        x = 'file'
    if x in ('d', 'dir', 'dirs', 'folders', 'folder', 'directory'):
        x = 'directory'
    if x in ('b', 'both'):
        x = 'both'
    if x not in ('file', 'directory', 'both'):
        raise argparse.ArgumentTypeError(f"Invalid suffix option: {x}. Valid options are: file, directory, both.")
    return x.lower()

def metadata_helper(x: str):
    x = x.lower()
    if x in ('e', 'exact'):
        x = 'exact'
    if x in ('f', 'flat'):
        x = 'flat'
    if x not in ('exact', 'flat'):
        raise argparse.ArgumentTypeError(f"Invalid metadata option: {x}. Valid options are: exact, flat.")
    return x.lower()

def fmthelper(x: str):
    x = x.lower()
    if x in ('xlsx', 'xlsm', 'xltx', 'xltm', 'xlsb', 'xls', 'excel', 'xl'):
        x = 'xlsx'
    if x in ('csv', 'txt', 'comma', 'comma_separated', 'c'):
        x = 'csv'
    if x in ('json', 'jsn', 'j'):
        x = 'json'
    if x in ('ods', 'open_document_spreadsheet', 'o'):
        x = 'ods'
    if x in ('xml', 'html', 'htm'):
        x = 'xml'
    if x in ('dict','dictionary', 'd'):
        x = 'dict'
    if x not in ('xlsx', 'csv', 'json', 'ods', 'xml', 'dict'):
        raise argparse.ArgumentTypeError(f"Invalid output format: {x}. Valid options are: xlsx, csv, json, ods, xml, dict.")
    return x.lower()


class EmptyIsTrueFixity(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if len(values) == 0:
            values = ["SHA-1"]
        setattr(namespace, self.dest, values)

def main():
    try:
        parser = create_parser()
        args = parser.parse_args()
        run_cli(args)
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user, exiting...")

if __name__ == "__main__":
    main()
