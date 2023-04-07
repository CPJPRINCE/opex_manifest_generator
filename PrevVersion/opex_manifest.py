import lxml.etree as ET
import pandas as pd
import sys
import hashlib
import os
from AutoClassification import __main__ as AC
from sys import platform
import argparse
from time import sleep

parser = argparse.ArgumentParser(description="OPEX Manifest Generator for Preservica Uploads")
parser.add_argument('folderpath',default=os.getcwd())
parser.add_argument("-c","--autoclass",required=False,choices=['Catalog','Accession','Both'])
parser.add_argument("-p","--prefix",required=False, nargs='+')
parser.add_argument("-f","--fixity",required=False,action='store_true')
parser.add_argument("-rm","--empty",required=False,action='store_true')
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
        if len(args.prefix) < 2: print('"Both" Option is selected, please pass two prefixes: [-p CATALOGPREFIX ACCPREFIX]'); raise SystemExit
        for n,a in enumerate(args.prefix):
            if a.endswith("/"): a = str(a).removesuffix("/")
            else: 
                if n == 0: prefix = a
                else: prefixAcc = a
        print(f"Prefixes are set as, Catalog; {prefix}; Acc: {prefixAcc}")
    else:
        for a in args.prefix: prefix = str(a).removesuffix("/")
        print('Prefix is set as: ' + prefix)
    class_flag = True
else: class_flag = False


#if args.autoaccession:
#    print('Auto-Accession is activated')

if args.fixity:
    print('Fixity is activated')
    fix_flag = True
else: fix_flag = False

if args.empty:
    print('Will remove empty directories')
    empty_flag = True
else: empty_flag = False

BUF_SIZE = 65536

alg = "SHA-1"

if alg == "SHA-1": hash = hashlib.sha1(); alglib = "sha1" 
elif alg == "MD5": hash = hashlib.md5(); alglib = "md5"
elif alg == "SHA-256": hash = hashlib.sha256(); alglib = "sha256"
elif alg == "SHA-512": hash = hashlib.sha512(); alglib = "sha512"
else: hash = hashlib.sha1()

###Reading Excel for Databases.

#df = pd.read_excel(xl)
#alg_l = []
# fix_l = []
# for i,row in df['FullName']:
#     fix_l.append(HashGen(row))
#     alg_l.append('SHA1')

#print(os.listdir(root_dir))

def HashGen(x):
    print(f'Generating Fixity for: {x}',end="\r") 
    with open(x,'rb') as f:
        d = hashlib.file_digest(f,alglib)
        # while True:
        #     d = f.read(BUF_SIZE)
        #     if not d: break
    return d.hexdigest().upper()

#print(HashGen(r"C:\Users\Chris.Prince\Downloads\Framework USLP Futures For Kees 07 08 18.pptx"))

def WinPathCheck(path):
    if len(path) > 255 and sys.platform == "win32":
        path = "\\\\?\\" + path
        #path = win32api.GetShortPathName(path)
    else: path = path
    return path

def FixityXMLGen(x):
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
    if os.path.exists(x):
        print("File already exists... Avoiding Override")
        pass
    else:
        Opex = ET.tostring(root,pretty_print=True,xml_declaration=True,encoding="UTF-8",standalone=True)
        with open(f'{x}','w',encoding="UTF-8") as writer:
            writer.write(Opex.decode('UTF-8'))
            print('Saved File to: ' + x)

def AutoClassicationIdentifier(x,df,identifier):
    idx = df.index[df['Name'] == x]
    if idx.empty:
        ArcRef = prefix
    else:
        item = df.loc[idx].NRef.item()
        ArcRef = prefix + "/" + item
    identifier.text = ArcRef
    identifier.set("type","code")

def AutoAccessionIdentifier(path,identifer):
    if args.autoclass == "Both":
        type = "AccRef"
    else:
        type = "code"
    if not os.path.isdir(path):
        global AccCount
        if args.autoclass == "Both":
            AccRef = str(prefixAcc) + "-0-" + str(AccCount)
        else: AccRef = str(prefix) + "-0-" + str(AccCount)
        AccCount += 1
    else:
        AccRef = "Dir"
    identifer.text = AccRef
    identifer.set("type",type)

def AddPropertiesMetadata(x,root,df):
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
            AutoAccessionIdentifier(x,ident)
        elif args.autoclass == "Both":
            print('Running AutoClass')
            AutoClassicationIdentifier(x,df,ident)
            ident = ET.SubElement(idents,"{" + opex + "}Identifier")
            AutoAccessionIdentifier(x,ident)
        else: print('Unknown Option... I dunno what\'s goin\' on?')
    except Exception as e:
        print(e)

def FixityOpex(x):
    try:
        r = FixityXMLGen(x)
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
        r = FixityXMLGen(x)
        AddPropertiesMetadata(x,r,df)
        OpexWriter(x,r)
    except Exception as e:
        print(e)

def ManifestDirs(x, c):
    os.chdir(x)
    rpath = os.getcwd()
    root = ET.Element("{" + opex + "}OPEXMetadata",nsmap={"opex":"http://www.openpreservationexchange.org/opex/v1.2"})
    transfer = ET.SubElement(root,"{" + opex + "}Transfer")
    mani = ET.SubElement(transfer,"{" + opex + "}Manifest")
    fold = ET.SubElement(mani,"{" + opex + "}Folders")
    files = ET.SubElement(mani,"{" + opex + "}Files")
    if class_flag: 
        AddPropertiesMetadata(x, root, df)

    #First For Loop is Create File Level Opex's, if Fixity or Auto-Classification options are selected. If no Options are selected, this section is ignored.
     
    for f in os.listdir(x):
        if not f.startswith('.') and not f.endswith('_AutoClass.xlsx') and not f.endswith('_Fixities.txt'):
            Path = os.path.join(rpath,f)
            Path = WinPathCheck(Path)
            if os.path.isdir(Path): pass
            else: 
                if fix_flag and class_flag: FixityIdentifierOpex(Path,df)
                elif class_flag: IdentifierOpex(Path, df)
                elif fix_flag: FixityOpex(Path)
                else: pass
    
    #Second For Loop is to Create Folder Level Manifests' of the folders.

    for f in os.listdir(x):
        print(f"Generating Manifest: {c}",end="\r")
        if not f.startswith('.') and not f.endswith('AutoClass.xlsx') and not f.endswith('_Fixities.txt'):
            Path = os.path.join(rpath,f)
            Path = WinPathCheck(Path)
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
    c += 1
    Path = f'{os.path.join(x, os.path.basename(x))}.opex'
    Path = WinPathCheck(Path)
    OpexWriter(Path, root)

    #3rd For Loop is iterate recurively through folders.

    for f in os.listdir(x):
        c += 1
        if not f.startswith('.'):
            Path = os.path.join(rpath,f)
            if os.path.isdir(Path): ManifestDirs(Path, c)

PathList = []
FixityList = []

if __name__ == "__main__":
    opex = "http://www.openpreservationexchange.org/opex/v1.2"
    root_dir = str(args.folderpath)
    if root_dir.endswith("\\"): root_dir = root_dir.removesuffix("\\")
    if empty_flag:
        AC.remove_empty_folders(root_dir)
    if class_flag:
        df = AC.AutoClass(root_dir)
        AC.ExportXL(df)
    if args.autoclass == "Accession" or args.autoclass =="Both":
        AccCount = 1
    else: AccCount = None
    ManifestDirs(root_dir, 1)
    if fix_flag:
        with open(root_dir + "/" + os.path.basename(root_dir) + "_Fixities.txt", 'w',encoding="UTF-8") as writer:
            for (path,fixity) in zip(PathList,FixityList):
                writer.write("{0};{1}\n".format(path,fixity))

    print('\nComplete!')