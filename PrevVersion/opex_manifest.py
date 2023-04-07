import lxml.etree as ET
import pandas as pd
import sys
import hashlib
import os
from AutoClassification import __main__ as AC
from sys import platform
import argparse

parser = argparse.ArgumentParser(description="OPEX Manifest Generator for Preservica Uploads")
parser.add_argument("-p", "--prefix")
parser.add_argument("-c","--class")
parser.add_argument("-f","--fixity")
#args, leftovers = parser.parse_known_args

try: root_dir = sys.argv[1]
except: 
    print('No Directory Supplied, defaulting to Current Working Directory')
    root_dir = os.getcwd()

try: 
    prefix = sys.argv[2]
    print("Prefix assigned as: " + sys.argv[2])
    if prefix.endswith("/"): prefix = prefix
    else: prefix = prefix + "/"
except: 
    print('No Prefix will be assigned')
    prefix = ""

# if args.c:
#     print("Arg C!")

fix_flag = True
class_flag = False

BUF_SIZE = 65536

alg = "SHA-1"

if alg == "SHA-1": hash = hashlib.sha1()
elif alg == "MD5": hash = hashlib.md5()
elif alg == "SHA-256": hash = hashlib.sha256()
elif alg == "SHA-256": hash = hashlib.sha512()
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
    #print(f'Generating Fixity for: {x}',end="\r") 
    with open(x,'rb') as f:
        while True:
            d = f.read(BUF_SIZE)
            if not d: break
            hash.update(d)
    return hash.hexdigest()

def WinPathCheck(path):
    if len(path) > 255 and sys.platform == "win32":
        path = "\\\\?\\" + path
        #path = win32api.GetShortPathName(path)
    else: path = path
    return path

def FixityXMLGen(x):
    root = ET.Element("opex:OPEXMetadata",nsmap={None:"http://www.openpreservationexchange.org/opex/v1.2"})
    transfer = ET.SubElement(root,"opex:Transfer")
    fixi = ET.SubElement(transfer,"opex:Fixities")
    fix = ET.SubElement(fixi,"opex:Fixity")
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

def AddPropertiesMetadata(x,root,df):
    try:
        prop = ET.SubElement(root,'opex:Properties')
        title = ET.SubElement(prop,'opex:Title')
        title.text = str(os.path.basename(x))
        desc = ET.SubElement(prop,'opex:Description')
        desc.text = str(os.path.basename(x))
        security = ET.SubElement(prop,'opex:SecurityDescriptor')
        security.text = "open"
        idents = ET.SubElement(prop,'opex:Identifiers')
        ident = ET.SubElement(idents,'opex:Identifier')
        idx = df.index[df['Name'] == x]
        if idx.empty:
            ArcRef = prefix
        else:
            item = df.loc[idx].NRef.item()
            ArcRef = prefix + item
        ident.text = ArcRef
        ident.set("type","code")
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
        r = ET.Element("opex:OPEXMetadata",nsmap={None:"http://www.openpreservationexchange.org/opex/v1.2"})
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
    root = ET.Element("opex:OPEXMetadata",nsmap={None:"http://www.openpreservationexchange.org/opex/v1.2"})
    transfer = ET.SubElement(root,"Transfer")
    mani = ET.SubElement(transfer,"Manifest")
    fold = ET.SubElement(mani,"Folders")
    files = ET.SubElement(mani,"Files")
    if class_flag: 
        AddPropertiesMetadata(x, root, df)
    #print('\n')
    for f in os.listdir(x):
        if not f.startswith('.'):
            Path = os.path.join(rpath,f)
            Path = WinPathCheck(Path)
            if os.path.isdir(Path): pass
            else: 
                if fix_flag and class_flag: FixityIdentifierOpex(Path,df)
                elif class_flag: IdentifierOpex(Path, df)
                elif fix_flag: FixityOpex(Path)
                else: pass
    for f in os.listdir(x):
        print(f"Generating Manifest: {c}",end="\r")
        if not f.startswith('.'):
            Path = os.path.join(rpath,f)
            Path = WinPathCheck(Path)
            if os.path.isdir(Path):
                folder = ET.SubElement(fold,"Folder")
                folder.text = str(f)
            else: 
                file = ET.SubElement(files,"File")
                if Path.endswith('.opex'): file.set("type","metadata")
                else:
                    file.set("type","content")
                    file.set("size",str(os.path.getsize(Path)))
                file.text = str(f)
    c += 1
    Path = f'{os.path.join(x, os.path.basename(x))}.opex'
    Path = WinPathCheck(Path)
    OpexWriter(Path, root)

    # Manifest = ET.tostring(root,pretty_print=True,xml_declaration=True,encoding="UTF-8",standalone=True)
    # with open(Path,'w',encoding="UTF-8") as writer:
    #     writer.write(Manifest.decode('UTF-8'))
    
    for f in os.listdir(x):
        c += 1
        if not f.startswith('.'):
            Path = os.path.join(rpath,f)
            if os.path.isdir(Path): ManifestDirs(Path, c)

PathList = []
FixityList = []

if __name__ == "__main__":
    if class_flag:
        df = AC.AutoClass(root_dir)
        AC.ExportXL(df)
    ManifestDirs(root_dir, 1)
    if fix_flag:
        with open(root_dir + "/" + os.path.basename(root_dir) + "_Fixities.txt", 'w',encoding="UTF-8") as writer:
            for (path,fixity) in zip(PathList,FixityList):
                writer.write("{0};{1}\n".format(path,fixity))
    print('\nComplete!')