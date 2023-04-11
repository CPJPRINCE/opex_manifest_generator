import lxml.etree as ET
import pandas as pd
import sys
import hashlib
import os
import auto_classification as AC
from sys import platform
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description="OPEX Manifest Generator for Preservica Uploads")
parser.add_argument('folderpath',default=os.getcwd())
parser.add_argument("-c","--autoclass",required=False,choices=['Catalog','Accession','Both'])
parser.add_argument("-p","--prefix",required=False, nargs='+')
parser.add_argument("-fx","--fixity",required=False,action='store_true')
parser.add_argument("-rm","--empty",required=False,action='store_true')
parser.add_argument("-f","--force",required=False,action='store_true')
parser.add_argument("-o","--output",required=False,nargs='+')
parser.add_argument("--clearopex",required=False,action='store_true')
parser.add_argument("-alg","--algorithm",required=False,default="SHA-1",choices=['SHA-1','MD5','SHA-256','SHA-512'])
args = parser.parse_args()

print('Processing Directory: ' + args.folderpath)

if args.folderpath.endswith("\\"):
    args.folderpath = args.folderpath.removesuffix("\\")

if args.autoclass:
    if not args.prefix:
        print('A prefix must be set when using Auto-Classification, stopping operation')
        raise SystemExit()
        
if args.prefix:
    if args.autoclass == "Both":
        print(len(args.prefix))
        if len(args.prefix) < 2 or len(args.prefix) > 2: print('"Both" option is selected, please pass only two prefixes: [-p CATALOGPREFIX ACCPREFIX]'); raise SystemExit
        for n,a in enumerate(args.prefix):
            if a.endswith("/"): a = str(Path(a).with_suffix(""))
            else: 
                if n == 0: prefix = a
                else: prefixAcc = a
        print(f"Prefixes are set as, Catalog; {prefix}; Acc: {prefixAcc}")
    else:
        for a in args.prefix: prefix = str(Path(a).with_suffix(""))
        print('Prefix is set as: ' + prefix)

if args.fixity:
    print('Fixity is activated')

BUFF_SIZE = 4096

alg = args.algorithm

opex = "http://www.openpreservationexchange.org/opex/v1.2"

def main():
    # for x in ['/home/christopher/Downloads/AlphaBay.txt','/home/christopher/Downloads/AccessionLinking.py']:
    #     HashGen(x)
    # raise SystemExit()
    global PathList
    PathList = []
    global FixityList
    FixityList = []
    root_dir = str(args.folderpath)
    if root_dir.endswith("\\"): root_dir = root_dir.removesuffix("\\")
    if args.clearopex:
        clear_opex(root_dir)
    if args.empty:
        AC.remove_empty_folders(root_dir)
    if args.autoclass == "Catalog" :
        df = AC.auto_class(root_dir,prefix=prefix)
    elif args.autoclass == "Accession":
        df = AC.auto_class(root_dir,accession=prefix)
    elif args.autoclass == "Both":
        df = AC.auto_class(root_dir,prefix=prefix,accession=prefixAcc)
    else: pass
    if args.output: output_path = args.output
    else: output_path = root_dir
    if args.autoclass:
        AC.export_xl(df,output_path)
    global c
    c = 1
    manifest_dirs(root_dir, df)
    if args.fixity:
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        output_filename = os.path.join(output_path,"meta", os.path.basename(root_dir) + "_Fixities.txt", )
        with open(output_filename,'w',encoding="UTF-8") as writer:
            for (path,fixity) in zip(PathList,FixityList):
                writer.write("{0};{1}\n".format(path,fixity))
    print('\nComplete!')

def clear_opex(path):
    walk = list(os.walk(path))
    for d,_,f in walk[::-1]:
        for f in f:
            file = os.path.join(d,f)
            if str(file).endswith('.opex'):
                os.remove(file)
                print(f'Removed: {file}') #fileprint(os.path.join(d,sd,f))

def HashGen(x):
    if alg == "SHA-1": hash = hashlib.sha1(); alglib = "sha1" 
    elif alg == "MD5": hash = hashlib.md5(); alglib = "md5"
    elif alg == "SHA-256": hash = hashlib.sha256(); alglib = "sha256"
    elif alg == "SHA-512": hash = hashlib.sha512(); alglib = "sha512"
    else: hash = hashlib.sha1(); alglib = "sha1"
    print(f'Generating Fixity for: {x}')#,end="\r") 
    h = hashlib.sha1(open(x,'rb').read()).hexdigest()
    with open(x,"rb") as f:
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
    else: path = path
    return path

def fixity_xml_generator(x):
    root = ET.Element("{" + opex + "}OPEXMetadata",nsmap={"opex":"http://www.openpreservationexchange.org/opex/v1.2"})
    transfer = ET.SubElement(root,"{" + opex + "}Transfer")
    fixi = ET.SubElement(transfer,"{" + opex + "}Fixities")
    fix = ET.SubElement(fixi,"{" + opex + "}Fixity")
    hash = HashGen(x)
    fix.set("type", alg)
    fix.set("value",hash)
    PathList.append(x)
    FixityList.append(hash)
    return root

def OpexWriter(x,root):
    if x.endswith('.opex'): x = x
    else: x = str(x) + ".opex"
    if os.path.exists(x) and not args.force:
        print("Opex exists. Avoiding Override")
        pass
    else:
        Opex = ET.tostring(root,pretty_print=True,xml_declaration=True,encoding="UTF-8",standalone=True)
        with open(f'{x}','w',encoding="UTF-8") as writer:
            writer.write(Opex.decode('UTF-8'))
            if args.force and os.path.exists(x): print(f"Forcing Override to: {x}")
            else: print('Saved File to: ' + x)

def AutoClassicationIdentifier(x,df,identifier):
    idx = df.index[df['Name'] == x]
    if idx.empty:
        ArcRef = "ERROR"
    else:
        ArcRef = df.loc[idx].Archive_Reference.item()
    identifier.text = ArcRef
    identifier.set("type","code")

def AutoAccessionIdentifier(x,df,identifer):
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

def AddPropertiesMetadata(x,root,df=None):
    try:
        prop = ET.SubElement(root,"{" + opex + "}Properties")
        title = ET.SubElement(prop,"{" + opex + "}Title")
        title.text = str(os.path.basename(x))
        desc = ET.SubElement(prop,"{" + opex + "}Description")
        desc.text = str(os.path.basename(x))
        security = ET.SubElement(prop,"{" + opex + "}SecurityDescriptor")
        security.text = "open"
        idents = ET.SubElement(prop,"{" + opex + "}Identifiers")
        ident = ET.SubElement(idents,"{" + opex + "}Identifier")
        if args.autoclass == "Catalog":
            AutoClassicationIdentifier(x,df,ident)
        elif args.autoclass == "Accession":
            AutoAccessionIdentifier(x,df,ident)
        elif args.autoclass == "Both":
            print('Running AutoClass')
            AutoClassicationIdentifier(x,df,ident)
            ident = ET.SubElement(idents,"{" + opex + "}Identifier")
            AutoAccessionIdentifier(x,df,ident)
        else: print('Unknown Option... I dunno what\'s goin\' on?')
    except Exception as e:
        print(e)

def FixityOpex(x):
    try:
        r = fixity_xml_generator(x)
        OpexWriter(x,r)
    except Exception as e:
        print(e)

def IdentifierOpex(x,df):
    try: 
        r = ET.Element("{" + opex + "}OPEXMetadata",nsmap={"opex":"http://www.openpreservationexchange.org/opex/v1.2"})
        AddPropertiesMetadata(x,r,df)
        OpexWriter(x,r)
    except Exception as e:
        print(e)

def FixityIdentifierOpex(x,df):
    try:
        r = fixity_xml_generator(x)
        AddPropertiesMetadata(x,r,df)
        OpexWriter(x,r)
    except Exception as e:
        print(e)

def manifest_dirs(x,df):
    os.chdir(x)
    rpath = os.getcwd()
    root = ET.Element("{" + opex + "}OPEXMetadata",nsmap={"opex":"http://www.openpreservationexchange.org/opex/v1.2"})
    transfer = ET.SubElement(root,"{" + opex + "}Transfer")
    mani = ET.SubElement(transfer,"{" + opex + "}Manifest")
    fold = ET.SubElement(mani,"{" + opex + "}Folders")
    files = ET.SubElement(mani,"{" + opex + "}Files")
    if args.autoclass: 
        AddPropertiesMetadata(x, root, df)

    #1st For Loop is Create File Level Opex's, if Fixity or Auto-Classification options are selected. If no options are selected, no action is taken in loop.
     
    for f in os.listdir(x):
        if not f.startswith('.') and not f.endswith('_AutoClass.xlsx') \
            and not f.endswith('_Fixities.txt') \
            and not f.endswith('_EmptyDirsRemoved.txt')\
            and not f == 'meta':
            Path = os.path.join(rpath,f)
            Path = win_256_check(Path)
            if os.path.isdir(Path): pass
            else: 
                if args.fixity and args.autoclass: FixityIdentifierOpex(Path,df)
                elif args.autoclass: IdentifierOpex(Path, df)
                elif args.fixity: FixityOpex(Path)
                else: pass
    
    #2nd For Loop is to create folder level manifests.
    global c
    for f in os.listdir(x):
        print(f"Generating Manifest: {c}")#, end="\r)"
        if not f.startswith('.') and not f.endswith('_AutoClass.xlsx') \
            and not f.endswith('_Fixities.txt')\
            and not f.endswith('_EmptyDirsRemoved.txt')\
            and not f == 'meta':
            Path = os.path.join(rpath,f)
            Path = win_256_check(Path)
            if os.path.isdir(Path):
                folder = ET.SubElement(fold,"{" + opex + "}Folder")
                folder.text = str(f)
            else: 
                file = ET.SubElement(files,"{" + opex + "}File")
                if Path.endswith('.opex'): file.set("type","metadata")
                else:
                    file.set("type","content")
                    file.set("size",str(os.path.getsize(Path)))
                file.text = str(f)
        else: pass
        c += 1
    c +=1
    Path = f'{os.path.join(x, os.path.basename(x))}.opex'
    Path = win_256_check(Path)
    OpexWriter(Path, root)
    
    #3rd For Loop is iterate recurively through folders.
    for f in os.listdir(x):
        if not f.startswith('.') and not f == 'meta':
            Path = os.path.join(rpath,f)
            if os.path.isdir(Path): manifest_dirs(Path, df)

if __name__ == "__main__":
    main()