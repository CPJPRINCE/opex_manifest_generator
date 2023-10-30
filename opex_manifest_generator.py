import lxml.etree as ET
import sys
import hashlib
import os
from auto_classification_generator import ClassificationGenerator as AC
from auto_classification_generator import export_txt, export_xl, define_output_directory
from sys import platform
import argparse
from pathlib import Path
from datetime import datetime
from time import sleep

class OpexManifestGenerator():
    def __init__(self,root,output_path=os.getcwd(),meta_flag=True,autoclass_flag=False,prefix=False,startref=1,fixity_flag=False,algorithm=False,empty_flag=False,force_flag=False,clear_opex_flag=False):
        self.root = os.path.abspath(root)
        self.opexns = "http://www.openpreservationexchange.org/opex/v1.2"        
        self.list_path = []
        self.list_fixity = []
        self.start_time = datetime.now()
        self.fixity_flag = fixity_flag
        self.empty_flag = empty_flag
        self.startref = startref
        self.autoclass_flag = autoclass_flag
        self.force_flag = force_flag
        self.output_path = output_path
        self.clear_opex_flag = clear_opex_flag
        self.meta_flag = meta_flag
        self.prefix = prefix
        self.algorithm = algorithm
        
    def print_running_time(self):
        print(f'Running time: {datetime.now() - self.start_time}')
        sleep(1)
        
    def reference_df_lookup(self,file_path,code_name="code"):
        identifier=ET.SubElement(self.identifiers,"{" + self.opexns + "}Identifier")     
        idx = self.df.index[self.df['FullName'] == file_path]
        if file_path == self.root:
            archive_reference = self.prefix[0]
        else:
            if idx.empty:
                archive_reference = "ERROR"
            else:
                archive_reference = self.df.loc[idx].Archive_Reference.item()
        identifier.text = archive_reference
        identifier.set("type","code")        

    def accession_df_lookup(self,file_path):
        identifier=ET.SubElement(self.identifiers,"{" + self.opexns + "}Identifier")                
        if self.autoclass_flag == "Both":
            type = "AccRef"
        else:
            type = "code"
        idx = self.df.index[self.df['FullName'] == file_path]
        if idx.empty:
            accession_reference = "ERROR"
        else:
            accession_reference = self.df.loc[idx].Accession_Reference.item()
        identifier.text = accession_reference
        identifier.set("type",type)
                        
    def write_opex(self,file_path,opexxml):
        opex_path = str(file_path) + ".opex"
        if os.path.exists(opex_path) and not self.force_flag:
            print(f"Opex exists: {opex_path}, but force option is not set: Avoiding override")
            pass
        else:
            opex = ET.tostring(opexxml,pretty_print=True,xml_declaration=True,encoding="UTF-8",standalone=True)
            with open(f'{opex_path}','w',encoding="UTF-8") as writer:
                writer.write(opex.decode('UTF-8'))
                if self.force_flag and os.path.exists(opex_path): print(f"Force Option Set. Forcing Override to: {opex_path}")
                else: print('Saved Opex File to: ' + opex_path)
        return opex_path

    def init_df(self):
        if self.autoclass_flag:
            if self.autoclass_flag == "Catalog":
                ac = AC(self.root,output_path=self.output_path,prefix=self.prefix,start_ref=self.startref,empty_flag=self.empty_flag,accession_flag=False)
                self.df = ac.init_dataframe()
            elif self.autoclass_flag in ["Accession","Both"]:
                ac = AC(self.root,output_path=self.output_path,prefix=self.prefix,start_ref=self.startref,empty_flag=self.empty_flag,accession_flag=True)
                self.df = ac.init_dataframe()
        else:
            self.df = None
                
    def clear_opex(self):
        walk = list(os.walk(self.root))
        for dir,_,files in walk[::-1]:
            for file in files:
                file_path = win_256_check(os.path.join(dir,file))   
                if str(file_path).endswith('.opex'):
                    os.remove(file_path)
                    print(f'Removed: {file_path}') #fileprint(os.path.join(d,sd,f))
                        
    def generate_opex_properties(self,xmlroot,file_path,title=None,description=None,security=None):
            self.properties = ET.SubElement(xmlroot,"{" + self.opexns + "}Properties")
            self.title = ET.SubElement(self.properties,"{" + self.opexns + "}Title")
            self.description = ET.SubElement(self.properties,"{" + self.opexns + "}Description")
            self.security = ET.SubElement(self.properties,"{" + self.opexns + "}SecurityDescriptor")
            self.identifiers = ET.SubElement(self.properties,"{" + self.opexns + "}Identifiers")
            self.identifier = ET.SubElement(self.identifiers,"{" + self.opexns + "}Identifier")           
            if not title: title = str(os.path.basename(file_path))
            self.title.text = str(os.path.basename(title))
            if not description: description = str(os.path.basename)
            self.description.text = str(os.path.basename(file_path))      
            if not security: security = "Open"         
            self.security.text = security
            if self.autoclass_flag == "Catalog":
                id = self.reference_df_lookup(file_path)
            elif self.autoclass_flag == "Accession":
                self.accession_df_lookup(file_path)
            elif self.autoclass_flag == "Both":
                id = self.reference_df_lookup(file_path)
                if not identifier: print('Identifiers has not been passed... This needs to be set when using "Both" option'); sleep(5); raise SystemExit
                identifier = ET.SubElement(self.identifiers,"{" + self.opexns + "}Identifier")
                id = self.accession_df_lookup(file_path)
                identifier.text = id
                identifier.set("type","code")
            else:
                identifier.text = "None"
                identifier.set("type","code")    
                                    
    def main(self):
        print(f"Start time: {self.start_time}")        
        if self.clear_opex_flag:
            self.clear_opex()
            if self.autoclass_flag or self.fixity_flag or self.force_flag:
                pass
            else: 
                print('Cleared OPEXES. No additional arguments passed, so ending program.'); sleep(1)
                self.print_running_time()
                sleep(3)
                raise SystemExit()
        if self.empty_flag:
            AC(self.root,self.output_path,meta_flag=self.meta_flag).remove_empty_directories()
        if self.autoclass_flag:
            self.init_df()
        self.count = 1
        OpexDir(self,self.root,autoclass_flag=self.autoclass_flag).generate_opex_dirs(self.root)
        if self.fixity_flag:
            output_path = define_output_directory(self.output_path,self.root,self.meta_flag,output_suffix="_Fixities.txt")
            export_txt(self.list_fixity,os.path.join(output_path))
        self.print_running_time()

class OpexDir(OpexManifestGenerator):
    def __init__(self,OMG,folder_path,autoclass_flag=False,title=None,description=None,security=None):
        self.OMG = OMG
        self.root = self.OMG.root
        self.opexns = self.OMG.opexns        
        self.folder_path = win_256_check(folder_path)
        self.xmlroot = ET.Element("{" + self.opexns + "}OPEXMetadata",nsmap={"opex":self.opexns})
        self.transfer = ET.SubElement(self.xmlroot,"{" + self.opexns + "}Transfer")
        self.manifest = ET.SubElement(self.transfer,"{" + self.opexns + "}Manifest")
        self.folders = ET.SubElement(self.manifest,"{" + self.opexns + "}Folders")
        self.files = ET.SubElement(self.manifest,"{" + self.opexns + "}Files")
        self.autoclass_flag = autoclass_flag
        self.title = title
        self.description = description
        self.security = security
        if self.autoclass_flag:
            self.OMG.generate_opex_properties(self.xmlroot,self.folder_path,title=title,description=description,security=security)        
    
    def filter_directories(self,directory):    #Sorts the list Alphabetically and Ignores: 1. Hidden Directories starting with '.', 2. '.opex' files, 3. Folders titled 'meta', 4. Script file 5. Output file. 
        list_directories = sorted([win_256_check(os.path.join(directory,f)) for f in os.listdir(directory) \
        if not f.startswith('.') \
        and f != 'meta'\
        and f != os.path.basename(__file__) \
        and not f.endswith('_AutoClass.xlsx') and not f.endswith('_autoclass.xlsx')\
        and not f.endswith('_EmptyDirectoriesRemoved.txt')])
        return list_directories
        
    def generate_opex_dirs(self,file_path):
        os.chdir(file_path)
        self = OpexDir(self.OMG,file_path,self.autoclass_flag)
        for f in self.filter_directories(file_path):
            if f.endswith('.opex'):
                pass
            elif os.path.isdir(f):
                self.folder = ET.SubElement(self.folders,"{" + self.opexns + "}Folder")
                self.folder.text = str(f)
                self.generate_opex_dirs(f)
            else: 
                OpexFile(self.OMG,f,fixity_flag=self.OMG.fixity_flag,autoclass_flag=self.OMG.autoclass_flag)
        
        for f in self.filter_directories(file_path):                         # Creates the files element of the Opex Manifest.
                if os.path.isfile(f):
                    file = ET.SubElement(self.files,"{" + self.opexns + "}File")
                    if f.endswith('.opex'): file.set("type","metadata")
                    else:
                        file.set("type","content")
                        file.set("size",str(os.path.getsize(f)))
                    file.text = str(f)
                #self.count += 1
        opex_path = os.path.join(os.path.abspath(self.folder_path),os.path.basename(self.folder_path))
        self.OMG.write_opex(opex_path,self.xmlroot)    
                        
class OpexFile(OpexManifestGenerator):
    def __init__(self,OMG,file_path,fixity_flag=False,algorithm="SHA-1",autoclass_flag=False,title=None,description=None,security=None):
        self.OMG = OMG
        self.opexns = self.OMG.opexns  
        self.file_path = win_256_check(file_path)
        self.fixity_flag = fixity_flag
        self.algorithm = algorithm
        self.autoclass_flag = autoclass_flag
        if self.fixity_flag or self.autoclass_flag:
            self.xmlroot = ET.Element("{" + self.opexns + "}OPEXMetadata",nsmap={"opex":self.opexns})
            if self.fixity_flag:
                self.transfer = ET.SubElement(self.xmlroot,"{" + self.opexns + "}Transfer")
                self.fixities = ET.SubElement(self.transfer,"{" + self.opexns + "}Fixities")
                self.genererate_opex_fixity()            
            if self.autoclass_flag:
                self.OMG.generate_opex_properties(self.xmlroot,self.file_path,title=title,description=description,security=security)
            self.OMG.write_opex(self.file_path,self.xmlroot)
        
    def genererate_opex_fixity(self):
        self.fixity = ET.SubElement(self.fixities,"{" + self.opexns + "}Fixity")        
        self.hash = HashGenerator(algorithm=self.algorithm).hash_generator(self.file_path) # Double Check...
        self.fixity.set("type", self.algorithm)
        self.fixity.set("value",self.hash)
        self.OMG.list_fixity.append([self.hash,self.file_path])
        self.OMG.list_path.append(self.file_path)        
        
class HashGenerator():
    def __init__(self,algorithm="SHA-1"):
        self.algorithm = algorithm
        self.buffer = 4096

    def hash_generator(self,file_path):
        if self.algorithm == "SHA-1": hash = hashlib.sha1()
        elif self.algorithm == "MD5": hash = hashlib.md5()
        elif self.algorithm == "SHA-256": hash = hashlib.sha256()
        elif self.algorithm == "SHA-512": hash = hashlib.sha512()
        else: hash = hashlib.sha1()
        print(f'Generating Fixity for: {file_path}')#,end="\r") 
        with open(file_path,"rb") as f:
            while True:
                buff = f.read(self.buffer)
                if not buff:
                    break
                hash.update(buff)
            f.close()
        return hash.hexdigest().upper()

#Checks if OS is windows and if chacter length is 256 characters or more. If longer uses "\\\\?\\" to resolve path.
def win_256_check(path):
    if len(path) > 255 and sys.platform == "win32":
        path = "\\\\?\\" + path
    return path

def parse_args():
    parser = argparse.ArgumentParser(description="OPEX Manifest Generator for Preservica Uploads")
    parser.add_argument('root',default=os.getcwd())
    parser.add_argument("-c","--autoclass",required=False,choices=['Catalog','Accession','Both',None])
    parser.add_argument("-p","--prefix",required=False, nargs='+')
    parser.add_argument("-fx","--fixity",required=False,action='store_true',default=False)
    parser.add_argument("-rm","--empty",required=False,action='store_true',default=False)
    parser.add_argument("-f","--force",required=False,action='store_true',default=False)
    parser.add_argument("-o","--output",required=False,nargs='+')
    parser.add_argument("-clr","--clear-opex",required=False,action='store_true',default=False)
    parser.add_argument("-alg","--algorithm",required=False,default="SHA-1",choices=['SHA-1','MD5','SHA-256','SHA-512'])
    parser.add_argument("-s","--start-ref",required=False,nargs='?',default=1)
    parser.add_argument("-meta","--meta-flag",required=False,action='store_true',default=True)    
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    os.chdir(args.root)
    print(args.root)
    if not args.output:
        args.output = os.path.abspath(args.root)
        print(f'No output path selected, defaulting to root Directory: {args.output}')
    else:
        args.output = os.path.abspath(args.output)
        print(f'Output path set to: {args.output}')    
    if args.autoclass:
        if not args.prefix:
            print('A prefix must be set when using Auto-Classification, stopping operation')
            sleep(3); raise SystemExit()
    if args.prefix:
        if args.autoclass == "Both":
            if len(args.prefix) < 2 or len(args.prefix) > 2:
                print('"Both" option is selected, please pass only two prefixes: [-p CATALOG_PREFIX ACCESSION_PREFIX]');
                sleep(5); raise SystemExit
            for n,a in enumerate(args.prefix):
                a = str(a)
                if n == 0: args.prefix = a
                else: prefix_acc = a
            print(f"Prefixes are set as, Catalog; {prefix}; Acc: {prefix_acc}")
        else:
            for a in args.prefix: 
                args.prefix = str(a)
            print('Prefix is set as: ' + args.prefix)                        
    if args.fixity:
        print(f'Fixity is activated, using {args.algorithm} algorithm')
    sleep(2)
        
    OpexManifestGenerator(root=args.root,
                          output_path=args.output,
                          autoclass_flag=args.autoclass,
                          prefix=args.prefix,
                          force_flag=args.force,
                          empty_flag=args.empty,
                          clear_opex_flag=args.clear_opex,
                          fixity_flag= args.fixity,
                          algorithm = args.algorithm,
                          startref=args.start_ref,
                          meta_flag=args.meta_flag).main()