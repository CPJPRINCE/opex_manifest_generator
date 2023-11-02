import lxml.etree as ET
import sys
import hashlib
import os
from auto_classification_generator import ClassificationGenerator as AC
from auto_classification_generator import export_txt, export_xl, define_output_directory
import argparse
from datetime import datetime
import time
import pandas as pd

class OpexManifestGenerator():
    def __init__(self,
                 root,
                 output_path=os.getcwd(),
                 meta_flag=True,
                 autoclass_flag=False,
                 prefix=False,
                 startref=1,
                 fixity_flag=False,
                 algorithm=False,
                 empty_flag=False,
                 force_flag=False,
                 clear_opex_flag=False,
                 export_flag=False,
                 input=False):
        self.root = os.path.abspath(root)
        self.opexns = "http://www.openpreservationexchange.org/opex/v1.2"        
        self.list_path = []
        self.list_fixity = []
        self.start_time = datetime.now()
        self.fixity_flag = fixity_flag
        self.empty_flag = empty_flag
        self.export_flag = export_flag
        self.startref = startref
        self.autoclass_flag = autoclass_flag
        self.force_flag = force_flag
        self.output_path = output_path
        self.clear_opex_flag = clear_opex_flag
        self.meta_flag = meta_flag
        self.prefix = prefix
        self.algorithm = algorithm
        self.input = input
        self.title_flag = False
        self.description_flag = False
        self.security_flag = False        
        
    def print_running_time(self):
        print(f'Running time: {datetime.now() - self.start_time}')
        time.sleep(1)
    
    def meta_df_lookup(self,file_path):
        idx = self.df.index[self.df['FullName'] == file_path]
        try:
            if self.title_flag: title = self.df.loc[idx].Title.item()
            else: title = False
            if self.description_flag: description = self.df.loc[idx].Description.item()
            else: description = False
            if self.security_flag: security = self.df.loc[idx].Security.item()
            else: security = False
        except Exception as e:
            print(e)
            title = False
            description = False
            security = False
        return title,description,security
    
    def df_lookup(self,file_path,code_name="code",accession_flag=None):
        identifier=ET.SubElement(self.identifiers,"{" + self.opexns + "}Identifier")                
        idx = self.df.index[self.df['FullName'] == file_path]
        if idx.empty: reference = "ERROR"
        else: 
            if accession_flag:
                reference = self.df.loc[idx].Accession_Reference.item()
            else: 
                reference = self.df.loc[idx].Archive_Reference.item()
        identifier.text = reference
        identifier.set("type",code_name)
                        
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
            if self.autoclass_flag in {"catalog","c"}:
                ac = AC(self.root,output_path=self.output_path,prefix=self.prefix,start_ref=self.startref,empty_flag=self.empty_flag,accession_flag=False)
                self.df = ac.init_dataframe()
            elif self.autoclass_flag in {"accession","a","both","b"}:
                ac = AC(self.root,output_path=self.output_path,prefix=self.prefix,accprefix=prefix_acc,start_ref=self.startref,empty_flag=self.empty_flag,accession_flag="File")
                self.df = ac.init_dataframe()
            if self.export_flag:
                output_path = define_output_directory(self.output_path,self.root,self.meta_flag)                
                export_xl(self.df,output_path)
        elif self.input:
            self.df = pd.read_excel(self.input)
            self.parse_input_df()
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
    
    def parse_input_df(self):
        if 'Title' in self.df: self.title_flag = True
        if 'Description' in self.df: self.description_flag = True
        if 'Security' in self.df: self.security_flag = True
                                
    def generate_opex_properties(self,xmlroot,file_path,title=None,description=None,security=None,code="code"):
            self.properties = ET.SubElement(xmlroot,"{" + self.opexns + "}Properties")
            self.titlexml = ET.SubElement(self.properties,"{" + self.opexns + "}Title")
            self.descriptionxml = ET.SubElement(self.properties,"{" + self.opexns + "}Description")
            self.securityxml = ET.SubElement(self.properties,"{" + self.opexns + "}SecurityDescriptor")
            self.identifiers = ET.SubElement(self.properties,"{" + self.opexns + "}Identifiers")
            self.identifier = ET.SubElement(self.identifiers,"{" + self.opexns + "}Identifier")           
            if not title: title = str(os.path.basename(file_path))
            self.titlexml.text = str(title)
            if not description: description = str(os.path.basename(file_path))
            self.descriptionxml.text = str(description)      
            if not security: security = "Open"         
            self.securityxml.text = security
            if self.autoclass_flag in {"catalog","c"}:
                self.df_lookup(file_path,code_name=code)
            elif self.autoclass_flag in {"accession","a"}:
                self.df_lookup(file_path,accession_flag=True)
            elif self.autoclass_flag in {"both","b"}:
                self.df_lookup(file_path,code_name=code)
                self.df_lookup(file_path,code_name="accref",accession_flag=True)
            elif self.autoclass_flag in {"generic","g"}:
                identifier = ET.SubElement(self.identifiers,"{" + self.opexns + "}Identifier")                
                identifier.text = str(os.path.basename(file_path))
                identifier.set("type",code)
            elif self.input:
                self.df_lookup(file_path)                
                                    
    def main(self):
        print(f"Start time: {self.start_time}")        
        if self.clear_opex_flag:
            self.clear_opex()
            if self.autoclass_flag or self.fixity_flag or self.force_flag or self.input:
                pass
            else: 
                print('Cleared OPEXES. No additional arguments passed, so ending program.'); time.sleep(3)
                self.print_running_time()
                raise SystemExit()
        if self.empty_flag:
            AC(self.root,self.output_path,meta_flag=self.meta_flag).remove_empty_directories()
        self.init_df()
        self.count = 1
        OpexDir(self,self.root).generate_opex_dirs(self.root)
        if self.fixity_flag:
            output_path = define_output_directory(self.output_path,self.root,self.meta_flag,output_suffix="_Fixities.txt")
            export_txt(self.list_fixity,os.path.join(output_path))
        self.print_running_time()

class OpexDir(OpexManifestGenerator):
    def __init__(self,OMG,folder_path,title=None,description=None,security=None):
        self.OMG = OMG
        self.root = self.OMG.root
        self.opexns = self.OMG.opexns        
        self.folder_path = win_256_check(folder_path)
        self.xmlroot = ET.Element("{" + self.opexns + "}OPEXMetadata",nsmap={"opex":self.opexns})
        self.transfer = ET.SubElement(self.xmlroot,"{" + self.opexns + "}Transfer")
        self.manifest = ET.SubElement(self.transfer,"{" + self.opexns + "}Manifest")
        self.folders = ET.SubElement(self.manifest,"{" + self.opexns + "}Folders")
        self.files = ET.SubElement(self.manifest,"{" + self.opexns + "}Files")
        self.title = title
        self.description = description
        self.security = security
        if self.OMG.autoclass_flag or self.OMG.input:
            self.OMG.generate_opex_properties(self.xmlroot,self.folder_path,title=self.title,description=self.description,security=self.security)
    
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
        if self.OMG.title_flag or self.OMG.description_flag or self.OMG.security_flag: self.title,self.description,self.security = self.OMG.meta_df_lookup(file_path) 
        self = OpexDir(self.OMG,file_path,title=self.title,description=self.description,security=self.security)
        for f in self.filter_directories(file_path):
            if f.endswith('.opex'):
                pass
            elif os.path.isdir(f):
                self.folder = ET.SubElement(self.folders,"{" + self.opexns + "}Folder")
                self.folder.text = str(f)
                self.generate_opex_dirs(f)
            else:
                OpexFile(self.OMG,f,self.OMG.algorithm)
        
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
    def __init__(self,OMG,file_path,algorithm="SHA-1",title=None,description=None,security=None):
        self.OMG = OMG
        self.opexns = self.OMG.opexns  
        self.file_path = win_256_check(file_path)
        self.algorithm = algorithm
        self.title = title
        self.description = description
        self.security = security
        if self.OMG.fixity_flag or self.OMG.autoclass_flag or self.OMG.input:
            self.xmlroot = ET.Element("{" + self.opexns + "}OPEXMetadata",nsmap={"opex":self.opexns})
            if self.OMG.fixity_flag:
                self.transfer = ET.SubElement(self.xmlroot,"{" + self.opexns + "}Transfer")
                self.fixities = ET.SubElement(self.transfer,"{" + self.opexns + "}Fixities")
                self.genererate_opex_fixity()            
            if self.OMG.autoclass_flag or self.OMG.input:
                if self.OMG.title_flag or self.OMG.description_flag or self.OMG.security_flag: self.title,self.description,self.security = self.OMG.meta_df_lookup(file_path) 
                self.OMG.generate_opex_properties(self.xmlroot,self.file_path,title=self.title,description=self.description,security=self.security)
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
        print(f'Generating Fixity using {self.algorithm} for: {file_path}')#,end="\r") 
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
    parser.add_argument("-c","--autoclass",required=False,choices=['catalog','c','accession','a','both','b','generic','g'],type=str.lower)
    parser.add_argument("-p","--prefix",required=False, nargs='+')
    parser.add_argument("-fx","--fixity",required=False,action='store_true',default=False)
    parser.add_argument("-rm","--empty",required=False,action='store_true',default=False)
    parser.add_argument("-f","--force",required=False,action='store_true',default=False)
    parser.add_argument("-o","--output",required=False,nargs='+')
    parser.add_argument("-clr","--clear-opex",required=False,action='store_true',default=False)
    parser.add_argument("-alg","--algorithm",required=False,default="SHA-1",choices=['SHA-1','MD5','SHA-256','SHA-512'])
    parser.add_argument("-s","--start-ref",required=False,nargs='?',default=1)
    parser.add_argument("-meta","--meta-flag",required=False,action='store_true',default=True) 
    parser.add_argument("-ex","--export-xl",required=False,action='store_true',default=False)
    parser.add_argument("-i","--input",required=False)
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
    if args.input and args.autoclass:
        print(f'Both Input and Auto-Class options have been selected, please use only one...')
        time.sleep(3); raise SystemExit() 
    if args.autoclass:
        if not args.prefix:
            print('A prefix must be set when using Auto-Classification, stopping operation')
            time.sleep(3); raise SystemExit()
    if args.prefix:
        if args.autoclass == "both":
            if len(args.prefix) < 2 or len(args.prefix) > 2:
                print('"Both" option is selected, please pass only two prefixes: [-p CATALOG_PREFIX ACCESSION_PREFIX]');
                time.sleep(3); raise SystemExit
            for n,a in enumerate(args.prefix):
                if n == 0: args.prefix = str(a)
                else: prefix_acc = str(a)
            print(f"Prefixes are set as: \t Catalog: {args.prefix} \t Acc: {prefix_acc}")
        else:
            prefix_acc = None
            for a in args.prefix: 
                args.prefix = str(a)
            print('Prefix is set as: ' + args.prefix)                        
    if args.fixity:
        print(f'Fixity is activated, using {args.algorithm} algorithm')
    time.sleep(3)    
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
                          export_flag=args.export_xl,
                          meta_flag=args.meta_flag,
                          input=args.input).main()