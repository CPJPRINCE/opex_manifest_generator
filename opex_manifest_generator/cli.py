"""
Cli interaction.

author: Christopher Prince
license: Apache License 2.0"
"""

import argparse, os, inspect, time
from opex_manifest_generator.opex_manifest import OpexManifestGenerator
import importlib.metadata

def parse_args():
    parser = argparse.ArgumentParser(description = "OPEX Manifest Generator for Preservica Uploads")
    parser.add_argument('root', default = os.getcwd(), help = "The root path to generate Opexes for")
    parser.add_argument("-c", "--autoclass", required = False,
                        choices = ['catalog', 'c', 'accession', 'a', 'both', 'b', 'generic', 'g', 'catalog-generic', 'cg', "accession-generic", "ag", "both-generic", "bg"],
                        type = str.lower,
                        help="""Toggles whether to utilise the auto_classification_generator 
                        to generate an on the fly Reference listing.
                        
                        There are several options, {catalog} will generate
                        a Archival Reference following an ISAD(G) sturcutre.
                        {accession} will create a running number of files.
                        {both} will do both at the same time!
                        {generic} will populate the title and description fields with the folder/file's name,
                        if used in conjunction with one of the above options:
                        {generic-catalog,generic-accession, generic-both} it will do both simultaneously.
                        """)
    parser.add_argument("-p", "--prefix", required = False, nargs = '+',
                        help= """Assign a prefix when utilising the --autoclass option. Prefix will append any text before all generated text.
                        When utilising the {both} option fill in like: [catalog-prefix, accession-prefix] without square brackets.                        
                        """)
    parser.add_argument("-fx", "--fixity", required = False, const = "SHA-1", default = None,
                        nargs = '?', choices = ['NONE', 'SHA-1', 'MD5', 'SHA-256', 'SHA-512'], type = str.upper,
                        help="Generates a hash for each file and adds it to the opex, can select the algorithm to utilise.")
    parser.add_argument("-rme", "--remove-empty", required = False, action = 'store_true', default = False,
                        help = "Remove and log empty directories from root. Log will be exported to 'meta' / output folder.")
    parser.add_argument("-o", "--output", required = False, nargs = 1,
                        help = "Sets the output to send any generated files to. Will not affect creation of a meta dir.")
    parser.add_argument("--disable-meta-dir", required = False, action = 'store_false',
                        help = """Set whether to disable the creation of a 'meta' directory for generated files,
                        default behaviour is to always generate this directory""")
    parser.add_argument("-clr", "--clear-opex", required = False, action = 'store_true', default = False,
                        help = """Clears existing opex files from a directory. If set with no further options will only clear opexes; 
                        if multiple options are set will clear opexes and then run the program""")
    parser.add_argument("-opt","--options-file", required = False, default=os.path.join(os.path.dirname(__file__),'options.properties'),
                        help="Specify a custom Options file, changing the set presets for column headers (Title,Description,etc)")
    parser.add_argument("-s", "--start-ref", required = False, nargs = '?', default = 1, 
                        help="Set a custom Starting reference for the Auto Classification generator. The generated reference will")
    parser.add_argument("-mdir","--metadata-dir", required=False, nargs= '?',
                        default = os.path.join(os.path.dirname(os.path.realpath(__file__)), "metadata"),
                        help="Specify the metadata directory to pull XML files from")
    parser.add_argument("-m", "--metadata", required = False, const = 'e', default = 'none',
                        nargs = '?', choices = ['none', 'n', 'exact', 'e', 'flat', 'f'], type = str.lower,
                        help="Set whether to include xml metadata fields in the generation of the Opex")
    parser.add_argument("-ex", "--export", required = False, action = 'store_true', default = False,
                        help="Set whether to export the generated auto classification references to an AutoClass spreadsheet")
    parser.add_argument("-i", "--input", required = False, nargs='?', 
                        help="Set to utilise a CSV / XLSX spreadsheet to import data from")
    parser.add_argument("-rm", "--remove", required = False, action = "store_true", default = False,
                        help="Set whether to enable removals of files and folders from a directory. ***Currently in testing")
    parser.add_argument("-z", "--zip", required = False, action = 'store_true',
                        help="Set to zip files")
    parser.add_argument("-fmt", "--output-format", required = False, default = "xlsx", choices = ['xlsx', 'csv'],
                        help="Set whether to output to an xlsx or csv format")
    parser.add_argument("-v", "--version", action = 'version', version = '%(prog)s {version}'.format(version = importlib.metadata.version("opex_manifest_generator")))
    parser.add_argument("--accession-mode", nargs = '?', required=False, const='file', default=None, choices=["file",'directory','both'],
                        help="""Set the mode when utilising the Accession option in autoclass.
                        file - only adds on files, folder - only adds on folders, both - adds on files and folders""")
    parser.add_argument("--hidden", required = False, action = 'store_true', default = False,
                        help="Set whether to include hidden files and folders")
    parser.add_argument("--print-xmls", required = False, action = "store_true", default = False,
                        help="Prints the elements from your xmls to the consoles")
    parser.add_argument("-key","--keywords", nargs = '*', default = None)
    parser.add_argument("-keym","--keywords-mode", nargs = '?', const = "intialise", default = "intialise", choices = ['intialise','firstletters'])
    parser.add_argument("--keywords-retain-order", required = False, default = False, action = 'store_true')
    parser.add_argument("--keywords-abbreviation-number", required = False, nargs='?', default = -3, type = int)
    parser.add_argument("--sort-by", required=False, nargs = '?', default = 'foldersfirst', choices = ['foldersfirst','alphabetical'], type=str.lower)
    parser.add_argument("-dlm", "--delimiter", required=False,nargs = '?', type = str)
    args = parser.parse_args()
    return args

def run_cli():
    args = parse_args()    
    print(f"Running Opex Generation on: {args.root}")
    if not args.output:
        args.output = os.path.abspath(args.root)
        print(f'Output path defaulting to root directory: {args.output}')
    else:
        args.output = os.path.abspath(args.output[0])
        print(f'Output path set to: {args.output}')    
    if args.input and args.autoclass:
        print(f'Both Input and Auto-Class options have been selected, please use only one...')
        time.sleep(5); raise SystemExit()
    if not args.metadata in {'none', 'n'} and not args.input:
        print(f'Warning: Metadata Flag has been given without Input. Metadata won\'t be generated.')
        time.sleep(5)
    if args.print_xmls:
        OpexManifestGenerator.print_descriptive_xmls()
    acc_prefix = None
    if args.autoclass in {"accession", "a", "accession-generic", "ag", "both", "b", "both-generic", "bg"} and args.accession_mode is None:
            args.accession_mode = "file"
    if args.prefix:
        if args.autoclass in {"both", "b", "both-generic", "bg"}:
            if len(args.prefix) < 2 or len(args.prefix) > 2:
                print('"Both" option is selected, please pass only two prefixes: [-p CATALOG_PREFIX ACCESSION_PREFIX]');
                time.sleep(3); raise SystemExit
            for n, a in enumerate(args.prefix):
                if n == 0:
                    args.prefix = str(a)
                elif n == 1:
                    acc_prefix = str(a)
            print(f"Prefixes are set as: \t Catalog: {args.prefix} \t Acc: {acc_prefix}")
        elif args.autoclass in {"accession", "a", "accession-generic", "ag"}:
            for a in args.prefix:
                acc_prefix = str(a)
            print('Prefix is set as: ' + acc_prefix)                        
        elif args.autoclass in {"catalog", "c", "catalog-generic", "cg"}:
            acc_prefix = None
            for a in args.prefix: 
                args.prefix = str(a)
            print('Prefix is set as: ' + args.prefix)
        elif args.autoclass in {"generic", "g"}:
            pass
        else:
            print('''An invalid option has been selected, please select a valid option: 
                  {c, catalog
                   a, accession
                   b, both
                   g, generic
                   cg, catalog-generic
                   ag, accesion-generic
                   bg, both-generic}''')    
            time.sleep(3)
            raise SystemExit               
    if args.fixity:
        print(f'Fixity is activated, using {args.fixity} algorithm')
    if args.sort_by:
        if args.sort_by == "foldersfirst":
            sort_key = lambda x: (os.path.isfile(x), str.casefold(x))
        elif args.sort_by == "alphabetical":
            sort_key = str.casefold
    if args.remove:
        print(inspect.cleandoc("""****
                                    You have enabled the remove functionality of the program. This action will remove all files and folders listed for removal and any sub-files/sub-folders.
                            
                                    This process will permanently delete the selected items, with no way recover the items. 
                                
                                    ****"""))
        time.sleep(2)
        i = input(inspect.cleandoc("Please type Y if you wish to proceed, otherwise the program will close: "))
        if not i.lower() == "y":
            print("Closing program..."); time.sleep(3); raise SystemExit()
    time.sleep(3)
    OpexManifestGenerator(root = args.root, 
                          output_path = args.output, 
                          autoclass_flag = args.autoclass, 
                          prefix = args.prefix, 
                          accession_mode=args.accession_mode,
                          acc_prefix = acc_prefix, 
                          empty_flag = args.remove_empty, 
                          remove_flag = args.remove, 
                          clear_opex_flag = args.clear_opex, 
                          algorithm = args.fixity, 
                          startref = args.start_ref, 
                          export_flag = args.export, 
                          meta_dir_flag = args.disable_meta_dir, 
                          metadata_flag = args.metadata,
                          metadata_dir = args.metadata_dir,
                          hidden_flag= args.hidden,
                          zip_flag = args.zip, 
                          input = args.input, 
                          output_format = args.output_format,
                          options_file=args.options_file,
                          keywords = args.keywords,
                          keywords_mode = args.keywords_mode,
                          keywords_retain_order = args.keywords_retain_order,
                          sort_key = sort_key,
                          delimiter = args.delimiter,
                          keywords_abbreviation_number = args.keywords_abbreviation_number).main()
    
if __name__ == "__main__":
    run_cli()