#!/usr/bin/python3

import lxml.etree as ET
import sys
import hashlib
import os
import auto_classification_generator as AC
from sys import platform
import argparse
from pathlib import Path
from datetime import datetime
from time import sleep 

parser = argparse.ArgumentParser(description="OPEX Manifest Generator for Preservica Uploads")
parser.add_argument('folderpath',default=os.getcwd())
parser.add_argument("-c","--autoclass",required=False,choices=['Catalog','Accession','Both'])
parser.add_argument("-p","--prefix",required=False, nargs='+')
parser.add_argument("-fx","--fixity",required=False,action='store_true')
parser.add_argument("-rm","--empty",required=False,action='store_true')
parser.add_argument("-f","--force",required=False,action='store_true')
parser.add_argument("-o","--output",required=False,nargs='+')
parser.add_argument("--clear-opex",required=False,action='store_true')
parser.add_argument("-alg","--algorithm",required=False,default="SHA-1",choices=['SHA-1','MD5','SHA-256','SHA-512'])
args = parser.parse_args()

print('Processing Directory: ' + args.folderpath)

if args.autoclass:
    if not args.prefix:
        print('A prefix must be set when using Auto-Classification, stopping operation')
        raise SystemExit()
        
if args.prefix:
    if args.autoclass == "Both":
        if len(args.prefix) < 2 or len(args.prefix) > 2: print('"Both" option is selected, please pass only two prefixes: [-p CATALOG_PREFIX ACCESSION_PREFIX]'); raise SystemExit
        for n,a in enumerate(args.prefix):
            a = str(Path(a))
            if n == 0: prefix = a
            else: prefixAcc = a
        print(f"Prefixes are set as, Catalog; {prefix}; Acc: {prefixAcc}")
    else:
        for a in args.prefix: 
            prefix = str(Path(a))
        print('Prefix is set as: ' + prefix)
    sleep(2)

if args.fixity:
    print('Fixity is activated')

def print_running_time(start_time):
    print(f'Complete, running time was: {datetime.now() - start_time}')
    sleep(1)

BUFF_SIZE = 4096
OPEXNS = "http://www.openpreservationexchange.org/opex/v1.2"

def main():
    start_time = datetime.now()
    print('Starting Opex Manifest Generator...'); sleep(1)
    print(f'Start at: {start_time}');sleep(2)
    # for x in ['/home/christopher/Downloads/AlphaBay.txt','/home/christopher/Downloads/AccessionLinking.py']:
    #     HashGen(x)
    # raise SystemExit()
    global PathList
    PathList = []
    global FixityList
    FixityList = []
    global root_dir
    root_dir = os.path.abspath(args.folderpath)
    if args.clear_opex:
        clear_opex(root_dir)
        if args.autoclass or args.fixity or args.force or args.output:
            pass
        else: 
            print('Cleared OPEXES. No additional arguments passed, so ending program.'); sleep(1)
            print_running_time(start_time)
            raise SystemExit()
    if args.empty:
        AC.remove_empty_folders(root_dir)
    if args.autoclass == "Catalog" :
        df = AC.auto_class(root_dir,prefix=prefix)
    elif args.autoclass == "Accession":
        df = AC.auto_class(root_dir,accession=prefix)
    elif args.autoclass == "Both":
        df = AC.auto_class(root_dir,prefix=prefix,accession=prefixAcc)
    else: df = None
    if args.output: output_path = args.output
    else: output_path = os.path.abspath(root_dir)
    if args.autoclass:
        #print(root_dir)
        AC.export_xl(df,output_path,tree_root=os.path.relpath(root_dir))
    global c
    c = 1
    generate_manifest_dirs(root_dir, df)

    if args.fixity:
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        if not os.path.exists(os.path.join(output_path,"meta")):
            os.makedirs(os.path.join(output_path,"meta"))
        output_filename = os.path.abspath(os.path.join(output_path,"meta", os.path.basename(root_dir) + "_Fixities.txt"))
        with open(output_filename,'w',encoding="UTF-8") as writer:
            for (path,fixity) in zip(PathList,FixityList):
                #print(path,fixity)
                writer.write(f"{path};{fixity}\n")
        print(f'Saved Fixity File to: {output_filename}')
    print_running_time(start_time)

def clear_opex(root_path):
    walk = list(os.walk(root_path))
    for dir,_,file in walk[::-1]:
        for file in file:
            file_path = os.path.join(dir,file)
            if str(file_path).endswith('.opex'):
                os.remove(file_path)
                print(f'Removed: {file_path}') #fileprint(os.path.join(d,sd,f))

def hash_generator(file_path):
    if args.algorithm == "SHA-1": hash = hashlib.sha1(); alglib = "sha1" 
    elif args.algorithm == "MD5": hash = hashlib.md5(); alglib = "md5"
    elif args.algorithm == "SHA-256": hash = hashlib.sha256(); alglib = "sha256"
    elif args.algorithm == "SHA-512": hash = hashlib.sha512(); alglib = "sha512"
    else: hash = hashlib.sha1(); alglib = "sha1"
    print(f'Generating Fixity for: {file_path}')#,end="\r") 
    #h = hashlib.sha1(open(file_path,'rb').read()).hexdigest()
    with open(file_path,"rb") as f:
        while True:
            buff = f.read(BUFF_SIZE)
            if not buff:
                break
            hash.update(buff)
        f.close()
    return hash.hexdigest().upper()

#Checks if OS is windows and if chacter length is 256 characters or more. If longer uses "\\\\?\\" to resolve path.
def win_256_check(path):
    if len(path) > 255 and sys.platform == "win32":
        path = "\\\\?\\" + path
    else: pass
    return path

def fixity_xml_generator(x):
    root = ET.Element("{" + OPEXNS + "}OPEXMetadata",nsmap={"opex":OPEXNS})
    transfer = ET.SubElement(root,"{" + OPEXNS + "}Transfer")
    fixi = ET.SubElement(transfer,"{" + OPEXNS + "}Fixities")
    fix = ET.SubElement(fixi,"{" + OPEXNS + "}Fixity")
    hash = hash_generator(x)
    fix.set("type", args.algorithm)
    fix.set("value",hash)
    PathList.append(x)
    FixityList.append(hash)
    return root

def write_opex(x,root):
    if x.endswith('.opex'): pass
    else: x = str(x) + ".opex"
    if os.path.exists(x) and not args.force:
        print(f"Opex exists: {x}, but force option is not set: Avoiding override")
        pass
    else:
        opex = ET.tostring(root,pretty_print=True,xml_declaration=True,encoding="UTF-8",standalone=True)
        with open(f'{x}','w',encoding="UTF-8") as writer:
            writer.write(opex.decode('UTF-8'))
            if args.force and os.path.exists(x): print(f"Force Option Set. Forcing Override to: {x}")
            else: print('Saved Opex File to: ' + x)

def auto_classification_lookup(x,df,identifier):
    idx = df.index[df['Name'] == x]
    global root_dir
    if x == root_dir:
        ArcRef = prefix
    else:
        if idx.empty:
            ArcRef = "ERROR"
        else:
            ArcRef = df.loc[idx].Archive_Reference.item()
    identifier.text = ArcRef
    identifier.set("type","code")

def auto_accession_counter(x,df,identifer):
    if args.autoclass == "Both":
        type = "AccRef"
    else:
        type = "code"
    idx = df.index[df['Name'] == x]
    if idx.empty:
        AccRef = "ERROR"
        print(AccRef)
    else:
        AccRef = df.loc[idx].Accession_Reference.item()
    identifer.text = AccRef
    identifer.set("type",type)

def add_metadata_properties(x,rootxml,df=None):
    try:
        prop = ET.SubElement(rootxml,"{" + OPEXNS + "}Properties")
        title = ET.SubElement(prop,"{" + OPEXNS + "}Title")
        title.text = str(os.path.basename(x))
        desc = ET.SubElement(prop,"{" + OPEXNS + "}Description")
        desc.text = str(os.path.basename(x))
        security = ET.SubElement(prop,"{" + OPEXNS + "}SecurityDescriptor")
        security.text = "open"
        identifers = ET.SubElement(prop,"{" + OPEXNS + "}Identifiers")
        identifer = ET.SubElement(identifers,"{" + OPEXNS + "}Identifier")
        if args.autoclass == "Catalog":
            auto_classification_lookup(x,df,identifer)
        elif args.autoclass == "Accession":
            auto_accession_counter(x,df,identifer)
        elif args.autoclass == "Both":
            print('Running AutoClass')
            auto_classification_lookup(x,df,identifer)
            identifer = ET.SubElement(identifers,"{" + OPEXNS + "}Identifier")
            auto_accession_counter(x,df,identifer)
        else: print('Unknown Option... I dunno what\'s goin\' on?')
    except Exception as e:
        print(e)

def generate_opex_fixity(x):
    try:
        root = fixity_xml_generator(x)
        write_opex(x,root)
    except Exception as e:
        print(e)

def generate_opex_identifer(x,df):
    try: 
        root = ET.Element("{" + OPEXNS + "}OPEXMetadata",nsmap={"opex":OPEXNS})
        add_metadata_properties(x,root,df)
        write_opex(x,root)
    except Exception as e:
        print(e)

def generate_opex_identifierandfixity(x,df):
    try:
        root = fixity_xml_generator(x)
        add_metadata_properties(x,root,df)
        write_opex(x,root)
    except Exception as e:
        print(e)

def generate_manifest_dirs(root_path,df=None):
    os.chdir(root_path)
    root_path = os.getcwd()
    root = ET.Element("{" + OPEXNS + "}OPEXMetadata",nsmap={"opex":OPEXNS})
    transfer = ET.SubElement(root,"{" + OPEXNS + "}Transfer")
    mani = ET.SubElement(transfer,"{" + OPEXNS + "}Manifest")
    fold = ET.SubElement(mani,"{" + OPEXNS + "}Folders")
    files = ET.SubElement(mani,"{" + OPEXNS + "}Files")
    if args.autoclass: 
        add_metadata_properties(root_path, root, df)
    """
    Below Loop was previously three loops, condensed for speed and because looping three times was unneccessary.
    Loop is only triggered if Fixity or Auto-Classification options are selected. If no options are selected, no action is taken in loop.
    """
    global c 
    for f in os.listdir(root_path):
        print(f"Generating Manifest: {c}", end="\r")

        """
        ***TWO LOOPS ARE NECCESSARY TO GENERATE OPEXES FOR FILES THEN INCLUDE THEM IN FOLDER OPEXES,
        ***UNLESS A BETTER WAY?

        If Condition to determine whether to account for File /  
        Currently ignore conditions are:
            File is Hidden / starts with '.'
            Has _AutoClass.xlsx in name
            Has _Fixities.xlsx in name
            Has _EmptyDirsRemoved.xlsx in name
            Or is titled 'Meta'
        Looking to make ignore conditions more dynamic and customizable."""
        
        if not f.startswith('.') and not f.endswith('_AutoClass.xlsx') \
            and not f.endswith('_Fixities.txt') \
            and not f.endswith('_EmptyDirsRemoved.txt')\
            and not 'meta' in f:
                file_path = os.path.join(root_path,f)
                file_path = win_256_check(file_path)
                if os.path.isdir(file_path):
                    folder = ET.SubElement(fold,"{" + OPEXNS + "}Folder")
                    folder.text = str(f)
                    #Recursive Function - Iterates through rest of directories until meeting a file. 
                    if not f.startswith('.') and not f == 'meta': generate_manifest_dirs(file_path, df)                  
                else: 
                    # Option Conditions - If Fixity and/or Identifer are enabled. 
                    if args.fixity and args.autoclass: generate_opex_identifierandfixity(file_path,df)
                    elif args.autoclass: generate_opex_identifer(file_path, df)
                    elif args.fixity: generate_opex_fixity(file_path)
                    else: pass
                    # Creates the files element of the Opex Manifest.
    for f in os.listdir(root_path):
        file_path = os.path.join(root_path,f)
        file_path = win_256_check(file_path)
        if not os.path.isdir(file_path) and not f.startswith('.') and not f.endswith('_AutoClass.xlsx') \
            and not f.endswith('_Fixities.txt') \
            and not f.endswith('_EmptyDirsRemoved.txt')\
            and not 'meta' in f:
                file = ET.SubElement(files,"{" + OPEXNS + "}File")
                if file_path.endswith('.opex'): file.set("type","metadata")
                else:
                    file.set("type","content")
                    file.set("size",str(os.path.getsize(file_path)))
                file.text = str(f)
                c += 1
    opex_path = f'{os.path.join(root_path, os.path.basename(root_path))}.opex'
    opex_path = win_256_check(opex_path)
    write_opex(opex_path, root)

if __name__ == "__main__":
    main()