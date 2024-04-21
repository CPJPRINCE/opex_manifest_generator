"""
Cli interaction.

author: Christopher Prince
license: Apache License 2.0"
"""

import argparse
import os
import time
from opex_manifest_generator.opex_manifest import OpexManifestGenerator
import importlib.metadata

def parse_args():
    parser = argparse.ArgumentParser(description="OPEX Manifest Generator for Preservica Uploads")
    parser.add_argument('root',default=os.getcwd())
    parser.add_argument("-c","--autoclass",required=False,choices=['catalog','c','accession','a','both','b','generic','g','catalog-generic','cg',"accession-generic","ag","both-generic","bg"],type=str.lower)
    parser.add_argument("-p","--prefix",required=False, nargs='+')
    parser.add_argument("-fx","--fixity",required=False,const="SHA-1",default=None, nargs='?', choices=['NONE','SHA-1','MD5','SHA-256','SHA-512'],type=str.upper)
    parser.add_argument("-rme","--remove-empty",required=False,action='store_true',default=False)
    parser.add_argument("-o","--output",required=False,nargs=1)
    parser.add_argument("-clr","--clear-opex",required=False,action='store_true',default=False)
    parser.add_argument("-s","--start-ref",required=False,nargs='?',default=1)
    parser.add_argument("-m","--metadata",required=False,const='e',default='none',nargs='?',choices=['none','n','exact','e','flat','f'],type=str.lower)
    parser.add_argument("-dmd", "--disable-meta-dir",required=False,action='store_false')
    parser.add_argument("-ex","--export",required=False,action='store_true',default=False)
    parser.add_argument("-i","--input",required=False)
    parser.add_argument("-rm","--remove",required=False,action="store_true",default=False)
    parser.add_argument("-z","--zip", required=False,action='store_true')
    parser.add_argument("-fmt", "--output-format",required=False,default="xlsx", choices=['xlsx','csv'])
    parser.add_argument("-v", "--version",action='version',version='%(prog)s {version}'.format(version=importlib.metadata.version("opex_manifest_generator")))
    parser.add_argument("--hidden",required=False,action='store_true',default=False)
    args = parser.parse_args()
    return args

def run_cli():
    args = parse_args()
    os.chdir(args.root)
    
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
    if not args.metadata in {'none','n'} and not args.input:
        print(f'Warning: Metadata Flag has been given without Input. Metadata won\'t be generated.')
        time.sleep(5)
    if args.autoclass:
        pass
        # if not args.prefix:
        #     print('A prefix must be set when using Auto-Classification, stopping operation')
        #     time.sleep(3); raise SystemExit()
    acc_prefix = None
    if args.prefix:
        if args.autoclass in {"both","b","both-generic","bg"}:
            if len(args.prefix) < 2 or len(args.prefix) > 2:
                print('"Both" option is selected, please pass only two prefixes: [-p CATALOG_PREFIX ACCESSION_PREFIX]');
                time.sleep(3); raise SystemExit
            for n,a in enumerate(args.prefix):
                if n == 0: args.prefix = str(a)
                elif n == 1: acc_prefix = str(a)
            print(f"Prefixes are set as: \t Catalog: {args.prefix} \t Acc: {acc_prefix}")
        elif args.autoclass in {"accession","a","accession-generic","ag"}:
            for a in args.prefix:
                acc_prefix = str(a)
            print('Prefix is set as: ' + acc_prefix)                        
        elif args.autoclass in {"catalog","c","catalog-generic","cg"}:
            acc_prefix = None
            for a in args.prefix: 
                args.prefix = str(a)
            print('Prefix is set as: ' + args.prefix)
        elif args.autoclass in {"generic","g"}:
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
    if args.remove:
        i = "y"
        # i = input(inspect.cleandoc("""You have enabled the remove functionality.
        #                         This action will remove files listed for removal, it is irreversible.
        #                         Please type Y to confirm, otherwise program will close: """))
        if not i.lower() == "y": print("Closing program..."); time.sleep(3); raise SystemExit()
    time.sleep(3)
    OpexManifestGenerator(root=args.root,
                          output_path=args.output,
                          autoclass_flag=args.autoclass,
                          prefix=args.prefix,
                          acc_prefix=acc_prefix,
                          empty_flag=args.remove_empty,
                          remove_flag=args.remove,
                          clear_opex_flag=args.clear_opex,
                          algorithm = args.fixity,
                          startref=args.start_ref,
                          export_flag=args.export,
                          meta_dir_flag=args.disable_meta_dir,
                          metadata_flag = args.metadata,
                          zip_flag = args.zip,
                          input=args.input,
                          output_format=args.output_format).main()
