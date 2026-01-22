"""
Cli interaction.

author: Christopher Prince
license: Apache License 2.0"
"""

import argparse, os, inspect, time, logging
from opex_manifest_generator.opex_manifest import OpexManifestGenerator
import importlib.metadata
from datetime import datetime
from opex_manifest_generator.common import running_time 

logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description = "OPEX Manifest Generator for Preservica Uploads")
    parser.add_argument('root', nargs='?', default = os.getcwd(),
                        help = """The root path to generate Opexes for, will recursively traverse all sub-directories.
                        Generates an Opex for each folder & (depending on options) file in the directory tree.""")
    parser.add_argument("-fx", "--fixity", required = False, nargs = '*', default = None,
                        choices = ['SHA-1', 'MD5', 'SHA-256', 'SHA-512'], type = fixity_helper, action=EmptyIsTrueFixity,
                        help="Generates a hash for each file and adds it to the opex, can select one or more algorithms to utilise. -fx SHA-1 MD5")
    parser.add_argument("--pax-fixity", required = False, action = 'store_true', default = False,
                        help="""Enables use of PAX fixity generation, in line with Preservica's Recommendation.
                        "Files / folders ending in .pax or .pax.zip will have individual files in folder / zip added to Opex.""")
    parser.add_argument("--fixity-export", required = False, action = 'store_false', default = True,
                        help="""Set whether to export the generated fixity list to a text file in the meta directory.
                        Enabled by default, disable with this flag.""")
    parser.add_argument("--prevent-all-exports", required = False, action = 'store_true', default = False,
                        help="Set to prevent all exports (Fixity, Removal, Empty) from being created in the meta directory.")
    parser.add_argument("-z", "--zip", required = False, action = 'store_true',
                        help="Set to zip files")
    parser.add_argument("--zip-remove-files", required = False, action = 'store_true',
                        help="Set to remove the files that have been zipped")
    parser.add_argument("--remove-empty", required = False, action = 'store_true', default = False,
                        help = "Remove and log empty directories from root. Log will be exported to 'meta' / output folder.")
    parser.add_argument("--empty-export", required = False, action = 'store_false', default = True,
                        help="""Set whether to export the generated empty list to a text file in the meta directory.
                        Enabled by default, disable with this flag.""")
    parser.add_argument("--hidden", required = False, action = 'store_true', default = False,
                        help="Set whether to include hidden files and folders")
    parser.add_argument("-o", "--output", required = False, nargs = '?',
                        help = "Sets the output to send any generated files (Remove Empty, Fixity List, Autoref Export) to. Will not affect creation of a meta dir.")
    parser.add_argument("-clr", "--clear-opex", required = False, action = 'store_true', default = False,
                        help = """Clears existing opex files from a directory. If set with no further options will only clear opexes; 
                        if multiple options are set will clear opexes and then run the program""")
    parser.add_argument("-opt","--options-file", required = False, default=os.path.join(os.path.dirname(__file__),'options','options.properties'),
                        help="Specify a custom Options file, changing the set presets for column headers (Title,Description,etc)")
    parser.add_argument("--autoref-options", required = False, default = None,
                        help="Specify a custom Auto Reference Options file, changing the set presets for Auto Reference Generator")
    parser.add_argument("--disable-meta-dir", required = False, action = 'store_false',
                        help = """Set whether to disable the creation of a 'meta' directory for generated files,
                        default behaviour is to always generate this directory""")
    # Input Options
    parser.add_argument("-i", "--input", required = False, nargs='?', 
                        help="Set to utilise a CSV / XLSX spreadsheet to import data from")
    parser.add_argument("-rm", "--remove", required = False, action = "store_true", default = False,
                        help="Set whether to enable removals of files and folders from a directory. ***Currently in testing")    
    parser.add_argument("--removal-export", required = False, action = 'store_false', default = True,
                        help="""Set whether to export the generated removals list to a text file in the meta directory.
                        Enabled by default, disable with this flag.""")
    parser.add_argument("-mdir","--metadata-dir", required=False, nargs= '?',
                        default = os.path.join(os.path.dirname(os.path.realpath(__file__)), "metadata"),
                        help="Specify the metadata directory to pull XML files from")
    parser.add_argument("-m", "--metadata", required = False, const = 'e', default = None,
                        nargs = '?', choices = ['exact', 'e', 'flat', 'f'], type = str.lower,
                        help="Set whether to include xml metadata fields in the generation of the Opex")
    parser.add_argument("--print-xmls", required = False, action = "store_true", default = False,
                        help="Prints the elements from your xmls to the consoles")
    parser.add_argument("--convert-xmls", required=False, action ='store_true', default = False,
                         help="Convert XMLs templates files in mdir to spreadsheets/csv files")
    
    # Auto Reference Options
    parser.add_argument("-r", "--autoref", required = False,
                        choices = ['catalog', 'c', 'accession', 'a', 'both', 'b', 'generic', 'g', 'catalog-generic', 'cg', "accession-generic", "ag", "both-generic", "bg"],
                        type = str.lower,
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
    parser.add_argument("-p", "--prefix", required = False, nargs = '+',
                        help= """Assign a prefix when utilising the --autoref option. Prefix will append any text before all generated text.
                        When utilising the {both} option fill in like: [catalog-prefix, accession-prefix] without square brackets.                        
                        """)
    parser.add_argument("-s", "--suffix", required = False, nargs = '?', default = '',
                        help= "Assign a suffix when utilising the --autoref option. Suffix will append any text after all generated text.")
    parser.add_argument("--suffix-option", required = False, choices= ['apply_to_files','apply_to_folders','apply_to_both'], default = 'apply_to_files',
                        help = "Set whether to apply the suffix to files, folders or both when utilising the --autoref option.")
    parser.add_argument("--accession-mode", nargs = '?', required=False, const='file', default=None, choices=["file",'directory','both'],
                        help="""Set the mode when utilising the Accession option in autoref.
                        file - only adds on files, folder - only adds on folders, both - adds on files and folders""")
    parser.add_argument("-str", "--start-ref", required = False, type=int, nargs = '?', default = 1, 
                        help="Set a custom Starting reference for the Auto Reference Generator. The generated reference will")
    parser.add_argument("-ex", "--export-autoref", required = False, action = 'store_true', default = False,
                        help="Set whether to export the generated references to an AutoRef spreadsheet")
    parser.add_argument("-fmt", "--output-format", required = False, default = "xlsx", choices = ['xlsx', 'csv','json','ods','xml'],
                        help="Set whether to export AutoRef Spreadsheet to: xlsx, csv, json, ods or xml format")
    parser.add_argument("-dlm", "--delimiter", required=False,nargs = '?', type = str, default = '/',
                        help="Set a custom delimiter for generated references, default is '/'")    
    parser.add_argument("-key","--keywords", nargs = '*', default = None,
                        help = "Set to replace reference numbers with given Keywords for folders (only Folders atm). Can be a list of keywords or a JSON file mapping folder names to keywords.")
    parser.add_argument("-keym","--keywords-mode", nargs = '?', const = "initialise", choices = ['initialise','firstletters','from_json'], default = 'initialise',
                        help = "Set to alternate keyword mode: 'initialise' will use initials of words; 'firstletters' will use the first letters of the string; 'from_json' will use a JSON file mapping names to keywords")
    parser.add_argument("--keywords-case-sensitivity", required = False, action = 'store_false', default = True,
                        help = "Set to change case keyword matching sensitivity. By default keyword matching is insensitive")
    parser.add_argument("--keywords-retain-order", required = False, default = False, action = 'store_true', 
                        help = "Set when using keywords to continue reference numbering. If not used keywords don't 'count' to reference numbering, e.g. if using initials 'Project Alpha' -> 'PA' then the next folder/file will still be '001' not '003'")
    parser.add_argument("--keywords-abbreviation-number", required = False, nargs='+', default = None, type = int,
                        help = "Set to set the number of letters to abbreviate for 'firstletters' mode, does not impact 'initialise' mode.")
    parser.add_argument("--sort-by", required=False, nargs = '?', default = 'folders_first', choices = ['folders_first','alphabetical'], type=str.lower,
                        help = "Set the sorting method, 'folders_first' sorts folders first then files alphabetically; 'alphabetically' sorts alphabetically (ignoring folder distinction)")
    parser.add_argument("--log-level", required=False, nargs='?', choices=['DEBUG','INFO','WARNING','ERROR'], default=None, type=str.upper,
                        help="Set the logging level (default: INFO)")
    parser.add_argument("--log-file", required=False, nargs='?', default=None,
                        help="Optional path to write logs to a file (default: stdout)")
    parser.add_argument("-v", "--version", action = 'version', version = '%(prog)s {version}'.format(version = importlib.metadata.version("opex_manifest_generator")))

    args = parser.parse_args()
    return args

def run_cli():
    args = parse_args()

    # Configure logging early so other modules inherit the settings
    try:
        log_level = getattr(logging, args.log_level.upper()) if args.log_level else logging.INFO
    except Exception:
        log_level = logging.INFO
    log_format = '%(asctime)s %(levelname)-8s [%(name)s] %(message)s'
    if args.log_file:
        logging.basicConfig(level=log_level, filename=args.log_file, filemode='a', format=log_format)
    else:
        logging.basicConfig(level=log_level, format=log_format)
    logger.debug(f'Logging configured (level={logging.getLevelName(log_level)}, file={args.log_file or "stdout"})')

    if not os.path.exists(args.root):
        logger.error(f'Please ensure that root path {args.root} exists. \n' \
        'If you are utilising Windows ensure that the path does not end with \\\' or \\"')
        raise FileNotFoundError(f'Please ensure that root path {args.root} exists. \n' \
        'If you are utilising Windows ensure that the path does not end with \\\' or \\" ')
    
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
        logger.error(f'Both Input and Auto ref options have been selected, please use only one...')
        raise ValueError('Both Input and Auto ref options have been selected, please use only one...')
    if args.remove and not args.input:
        logger.error('Removal flag has been given without input, please ensure an input file is utilised when using this option.')
        raise ValueError('Removal flag has been given without input, please ensure an input file is utilised when using this option.')
    if args.metadata is not None and not args.input:
        logger.warning(f'Warning: Metadata Flag has been given without Input. Metadata won\'t be generated.')
  
    if args.print_xmls:
        logger.info(f'Printing xmls in {args.metadata_dir} then ending')
        OpexManifestGenerator(root = args.root, metadata_dir=args.metadata_dir).print_descriptive_xmls()
        raise SystemExit()
    if args.convert_xmls:
        logger.info(f'Converting XMLs in {args.metadata_dir} then ending')
        OpexManifestGenerator(root = args.root, output_format=args.output_format, metadata_dir=args.metadata_dir).convert_descriptive_xmls()
        raise SystemExit()

    if args.prevent_all_exports:
        args.fixity_export_flag = False
        args.removal_export_flag = False
        args.empty_export_flag = False
        logger.info('All exports have been prevented via --prevent-all-exports flag.')

    acc_prefix = None
    if args.autoref in {"accession", "a", "accession-generic", "ag", "both", "b", "both-generic", "bg"} and args.accession_mode is None:
            args.accession_mode = "file"
            logger.debug(f'Accession mode not set, defaulting to "file" mode for accession generation.')

    if args.prefix:
        if args.autoref in {"both", "b", "both-generic", "bg"}:
            if len(args.prefix) < 2 or len(args.prefix) > 2:
                logger.error('"Both" option is selected, please pass only two prefixes: [-p CATALOG_PREFIX ACCESSION_PREFIX]'); 
                raise ValueError('"Both" option is selected, please pass only two prefixes: [-p CATALOG_PREFIX ACCESSION_PREFIX]')
            for n, a in enumerate(args.prefix):
                if n == 0:
                    args.prefix = str(a)
                elif n == 1:
                    acc_prefix = str(a)
            logger.info(f"Prefixes are set as: \t Catalog: {args.prefix} \t Acc: {acc_prefix}")
        elif args.autoref in {"accession", "a", "accession-generic", "ag"}:
            for a in args.prefix:
                acc_prefix = str(a)
            logger.info('Prefix is set as: ' + acc_prefix)                        
        elif args.autoref in {"catalog", "c", "catalog-generic", "cg"}:
            acc_prefix = None
            for a in args.prefix: 
                args.prefix = str(a)
            logger.info('Prefix is set as: ' + args.prefix)
        elif args.autoref in {"generic", "g"}:
            logger.info('Using Generic mode')
            pass
        else:
            logger.error('''An invalid option has been selected, please select a valid option: 
                  {c, catalog
                   a, accession
                   b, both
                   g, generic
                   cg, catalog-generic
                   ag, accession-generic
                   bg, both-generic}''')    
            raise ValueError('An invalid option has been selected, please select a valid option.')   
    
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
            logger.info("Y not typed, safetly aborted...")
            raise SystemExit()
        else:
            logger.info("Confirmation recieved proceeding to remove files")

    if args.remove_empty:
        logger.warning(inspect.cleandoc("\n***WARNING***" \
                                "\nYou have enabled the remove empty folders functionality of the program. " \
                                "This action will remove all empty folders." \
                                "\nThis process will permanently delete all empty folders, with no way recover the items." \
                                "\n***"))
        i = input(inspect.cleandoc("Please type Y if you wish to proceed, otherwise the program will close: "))
        if not i.lower() == "y":
            logger.info("Y not typed, safetly aborted...")
            raise SystemExit()
        else:
            logger.info("Confirmation recieved proceeding to remove empty folders...")

    start_time = datetime.now()
    OpexManifestGenerator(root = args.root, 
                          output_path = args.output, 
                          autoref_flag = args.autoref, 
                          prefix = args.prefix, 
                          accession_mode=args.accession_mode,
                          acc_prefix = acc_prefix, 
                          empty_flag = args.remove_empty, 
                          empty_export_flag = args.empty_export,
                          removal_flag = args.remove, 
                          removal_export_flag = args.removal_export,
                          clear_opex_flag = args.clear_opex, 
                          algorithm = args.fixity,
                          pax_fixity= args.pax_fixity,
                          fixity_export_flag = args.fixity_export,
                          start_ref = args.start_ref, 
                          export_flag = args.export_autoref, 
                          meta_dir_flag = args.disable_meta_dir, 
                          metadata_flag = args.metadata,
                          metadata_dir = args.metadata_dir,
                          hidden_flag= args.hidden,
                          zip_flag = args.zip, 
                          zip_file_removal= args.zip_remove_files,
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
                          ).main()
    logger.info(f"Run Complete! Ran for: {running_time(start_time)}")    

def fixity_helper(x: str):
    x = x.upper()
    if x == 'SHA1':
        x = 'SHA-1'
    if x == 'SHA256':
        x = 'SHA-256'
    if x == 'SHA512':
        x = 'SHA-512'
    return x.upper()

class EmptyIsTrueFixity(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if len(values) == 0:
            values = ["SHA-1"]
        setattr(namespace, self.dest, values)

if __name__ == "__main__":
    try:
        run_cli()
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user, exiting...")