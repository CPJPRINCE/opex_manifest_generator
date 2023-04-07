import lxml.etree as ET
import pandas as pd
import sys
import hashlib
import os

root_dir = sys.argv[1]

fix_flag = True

BUF_SIZE = 65536

alg = "SHA-1"

if alg == "SHA-1": hash = hashlib.sha1()
elif alg == "MD5": hash = hashlib.md5()
elif alg == "SHA-256": hash = hashlib.sha256()
elif alg == "SHA-256": hash = hashlib.sha512()
else: hash = hashlib.sha1()

def HashGen(x):
    with open(x,'rb') as f:
        while True:
            d = f.read(BUF_SIZE)
            if not d: break
            hash.update(d)
    return hash.hexdigest()

#df = pd.read_excel(xl)
#alg_l = []
# fix_l = []
# for i,row in df['FullName']:
#     fix_l.append(HashGen(row))
#     alg_l.append('SHA1')

#print(os.listdir(root_dir))

def FixityManifest(x):
    root = ET.Element("OPEXMetadata",nsmap={None:"http://www.openpreservationexchange.org/opex/v1.2"})
    transfer = ET.SubElement(root,"Transfer")
    fixi = ET.SubElement(transfer,"Fixities")
    fix = ET.SubElement(fixi,"Fixity")
    hash = HashGen(x)
    fix.set("type", alg)
    fix.set("value",hash)
    FixManifest = ET.tostring(root,pretty_print=True,xml_declaration=True,encoding="UTF-8",standalone=True)
    with open(f'{x}.opex','w',encoding="UTF-8") as writer:
            writer.write(FixManifest.decode('UTF-8'))
    if fix_flag: 
        PathList.append(x)
        FixityList.append(hash)

def ManifestDirs(x, c):
    os.chdir(x)
    rpath = os.getcwd()
    root = ET.Element("OPEXMetadata",nsmap={None:"http://www.openpreservationexchange.org/opex/v1.2"})
    transfer = ET.SubElement(root,"Transfer")
    mani = ET.SubElement(transfer,"Manifest")
    fold = ET.SubElement(mani,"Folders")
    files = ET.SubElement(mani,"Files")
    for f in os.listdir(x):
        print(f"Processing: {c}",end="\r")
        if not f.startswith('.') and f != (os.path.join(x,os.path.basename(x)) + '.opex'):
            Path = os.path.join(rpath,f)
            if os.path.isdir(Path):
                folder = ET.SubElement(fold,"Folder")
                folder.text = str(f)
            else: 
                file = ET.SubElement(files,"File")
                if Path.endswith('.opex'): file.set("type","metadata")
                else:
                    if fix_flag:
                        FixityManifest(Path)
                    file.set("type","content")
                    file.set("size",str(os.path.getsize(Path)))
                file.text = str(f)
        c += 1
        result = ET.tostring(root,pretty_print=True,xml_declaration=True,encoding="UTF-8",standalone=True)
        with open(f'{os.path.join(x, os.path.basename(x))}.opex','w',encoding="UTF-8") as writer:
            writer.write(result.decode('UTF-8'))
    for f in os.listdir(x):
        c += 1
        if not f.startswith('.'):
            Path = os.path.join(rpath,f)
            if os.path.isdir(Path): ManifestDirs(Path, c)

PathList = []
FixityList = []
if __name__ == "__main__":
    ManifestDirs(root_dir, 1)
    if fix_flag:
        with open(root_dir + "/" + os.path.basename(root_dir) + "Fixities.txt", 'w') as writer:
            for (path,fixity) in zip(PathList,FixityList):
                writer.write("{0};{1}\n".format(path,fixity))