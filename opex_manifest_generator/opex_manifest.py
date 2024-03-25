"""
Opex Manifest Generator tool

This tool is utilised to recusrively generate Opex files for files / directories for use in uploading to Preservica and other OPEX conformin systems.

author: Christopher Prince
license: Apache License 2.0"
"""

import lxml.etree as ET
import os
from auto_classification_generator import ClassificationGenerator
from auto_classification_generator.common import export_list_txt, export_xl, export_csv, define_output_file
from datetime import datetime
import time
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype
from opex_manifest_generator.hash import HashGenerator
from opex_manifest_generator.common import *
import stat

class OpexManifestGenerator():
    def __init__(self,
                 root,
                 output_path=os.getcwd(),
                 meta_dir_flag=True,
                 metadata_dir=os.path.join(os.path.dirname(os.path.realpath(__file__)), "metadata"),
                 metadata_flag='none',
                 autoclass_flag=False,
                 prefix=False,
                 startref=1,
                 fixity_flag=False,
                 algorithm=False,
                 empty_flag=False,
                 force_flag=False,
                 clear_opex_flag=False,
                 export_flag=False,
                 input=False,
                 zip_flag=False,
                 output_format="xlsx"):
        
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
        self.meta_dir_flag = meta_dir_flag
        self.prefix = prefix
        self.algorithm = algorithm
        self.input = input
        self.title_flag = False
        self.description_flag = False
        self.security_flag = False
        self.zip_flag = zip_flag
        self.output_format = output_format
        self.metadata_flag = metadata_flag
        self.metadata_dir = metadata_dir
        
    def print_running_time(self):
        print(f'Running time: {datetime.now() - self.start_time}')
        time.sleep(1)
    
    def meta_df_lookup(self,file_path: str):
        idx = self.df.index[self.df['FullName'] == file_path]
        try:
            if self.title_flag:
                title = self.df.loc[idx].Title.item()
                if str(title) == "nan": title = None
            else: title = None
            if self.description_flag: 
                description = self.df.loc[idx].Description.item()
                if str(description) == "nan": description = None
            else: description = None
            if self.security_flag: 
                security = self.df.loc[idx].Security.item()
                if str(security) == "nan": security = None
            else: security = None
        except Exception as e:
            print(e)
            title = None
            description = None
            security = None
        return title,description,security
    
    def ignore_remove_df_lookup(self,file_path):
        pass

    def ident_df_lookup(self,file_path,code_name="code",accession_flag=None):
        idx = self.df.index[self.df['FullName'] == file_path]
        if idx.empty: reference = "ERROR"
        else: 
            if accession_flag:
                reference = self.df.loc[idx].Accession_Reference.item()
            else: 
                reference = self.df.loc[idx].Archive_Reference.item()
        if isinstance(reference,float): pass
        else:
            self.identifier.text = reference
            self.identifier.set("type",code_name)

        column_headers = self.df.columns.values.tolist()
        for header in column_headers:
            if 'Identifier' in header:
                self.identifier = ET.SubElement(self.identifiers,f"{{{self.opexns}}}Identifier") 
                reference = self.df.at[idx, header.rsplit[':'][-1]].item()         
                print(reference)

    def write_opex(self,file_path,opexxml):
        opex_path = str(file_path) + ".opex"
        if os.path.exists(opex_path) and not self.force_flag:
            print(f"Opex exists: {opex_path}, but force option is not set: Avoiding override")
            pass
        else:
            opex = ET.indent(opexxml,"  ")
            opex = ET.tostring(opexxml,pretty_print=True,xml_declaration=True,encoding="UTF-8",standalone=True)
            with open(f'{opex_path}','w',encoding="UTF-8") as writer:
                writer.write(opex.decode('UTF-8'))
                if self.force_flag and os.path.exists(opex_path): print(f"Force Option Set. Forcing Override to: {opex_path}")
                else: print('Saved Opex File to: ' + opex_path)
        return opex_path

    def init_df(self):
        if self.autoclass_flag:
            if self.autoclass_flag in {"catalog","c","catalog-generic","cg"}:
                ac = ClassificationGenerator(self.root,output_path=self.output_path,prefix=self.prefix,start_ref=self.startref,empty_flag=self.empty_flag,accession_flag=False)
                self.df = ac.init_dataframe()
            elif self.autoclass_flag in {"accession","a","accession-generic","ag","both","b","both-generic","bg"}:
                ac = ClassificationGenerator(self.root,output_path=self.output_path,prefix=self.prefix,accprefix=prefix_acc,start_ref=self.startref,empty_flag=self.empty_flag,accession_flag="File")
                self.df = ac.init_dataframe()
            if self.export_flag:
                output_path = define_output_file(self.output_path,self.root,meta_dir_flag=self.meta_dir_flag,output_format=self.output_format)                
                if self.output_format == "xlsx": export_xl(self.df,output_path)
                elif self.output_format == "csv": export_csv(self.df,output_path)
        elif self.input:
            if self.input.endswith('xlsx'): self.df = pd.read_excel(self.input)
            elif self.input.endswith('csv'): self.df = pd.read_csv(self.input)
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
        
    def generate_descriptive_metadata(self,xml_descmeta,file_path):
        for file in os.listdir(self.metadata_dir):
            if file.endswith('xml'):
                """
                Generates info on the elements of the XML Files placed in the Metadata directory.
                Composed as a list of dictionaries.
                """
                path = os.path.join(self.metadata_dir,file)
                xml_file = ET.parse(path)
                root_element = ET.QName(xml_file.find('.'))
                root_element_ln = root_element.localname
                root_element_ns = root_element.namespace
                elements_list = []
                for elem in xml_file.findall('.//'):
                    elem_path = xml_file.getelementpath(elem)
                    elem = ET.QName(elem)
                    elem_ln = elem.localname
                    elem_ns = elem.namespace
                    elem_lnpath = elem_path.replace(f"{{{elem_ns}}}",root_element_ln + ":")
                    elements_list.append({"Name":root_element_ln + ":" + elem_ln,"Namespace":elem_ns,"Path":elem_lnpath})
                list_xml = []

                """
                Compares the column headers in the Spreadsheet against the headers. Filters out non-matching data.
                """
                column_headers = self.df.columns.values.tolist()
                for elem_dict in elements_list:
                    if elem_dict.get('Name') in column_headers or elem_dict.get('Path') in column_headers:
                        list_xml.append({"Name":elem_dict.get('Name'),"Namespace":elem_dict.get('Namespace'),"Path":elem_dict.get('Path')})
                """
                Composes the data into an xml file.
                """
                if len(list_xml):
                    idx = self.df.index[self.df['FullName'] == file_path]
                    xml_new = xml_file
                    for elem_dict in list_xml:
                        name = elem_dict.get('Name')
                        path = elem_dict.get('Path')
                        ns = elem_dict.get('Namespace')
                        if self.metadata_flag in {'e','exact'}:
                            try: 
                                val = self.df.loc[idx,path].values[0]
                            except KeyError as e:
                                print('Key Error: please ensure column header\'s are an exact match...')
                                print(f'Missing Column: {e}')
                                print('Alternatively use flat mode...')
                                time.sleep(5)
                                raise SystemError()
                            if str(val) == "nan": val = ""
                            n = path.replace(root_element_ln + ":", f"{{{ns}}}")
                            elem = xml_new.find(f'/{n}')
                            elem.text = str(val)
                        elif self.metadata_flag in {'f','flat'}:
                            val = self.df.loc[idx,name].values[0]
                            if pd.isnull(val): val = ""
                            else:
                                if is_datetime64_any_dtype(val):
                                    val = pd.to_datetime(val)
                                    val = datetime.strftime(val,"%Y-%m-%dT%H-%M-%S.00Z")
                            if str(val) == "nan": val = ""
                            n = name.split(':')[-1]
                            elem = xml_new.find(f'//{{{ns}}}{n}')
                            elem.text = str(val)
                    xml_descmeta.append(xml_new.find('.'))

    def generate_opex_properties(self,xmlroot,file_path,title=None,description=None,security=None,code="code"):
            self.properties = ET.SubElement(xmlroot,f"{{{self.opexns}}}Properties")
            self.identifiers = ET.SubElement(self.properties,f"{{{self.opexns}}}Identifiers")
            self.identifier = ET.SubElement(self.identifiers,f"{{{self.opexns}}}Identifier")           
            if title:
                self.titlexml = ET.SubElement(self.properties,f"{{{self.opexns}}}Title")
                self.titlexml.text = str(title)
            if description:
                self.descriptionxml = ET.SubElement(self.properties,f"{{{self.opexns}}}Description")
                self.descriptionxml.text = str(description)      
            if security:
                self.securityxml = ET.SubElement(self.properties,f"{{{self.opexns}}}SecurityDescriptor")
                self.securityxml.text = str(security)
            if self.autoclass_flag in {"catalog","c","catalog-generic","cg"}:
                self.ident_df_lookup(file_path,code_name=code)
            elif self.autoclass_flag in {"accession","a","accession-generic","ag"}:
                self.ident_df_lookup(file_path,accession_flag=True)
            elif self.autoclass_flag in {"both","b","both-generic","bg"}:
                self.ident_df_lookup(file_path,code_name=code)
                self.identifier = ET.SubElement(self.identifiers,f"{{{self.opexns}}}Identifier")           
                self.ident_df_lookup(file_path,code_name="accref",accession_flag=True)
            elif self.autoclass_flag in {"generic","g"}:
                self.properties.remove(self.identifiers)
            elif self.input:
                self.ident_df_lookup(file_path)                

    def genererate_opex_fixity(self):
        self.fixity = ET.SubElement(self.fixities,f"{{{self.opexns}}}Fixity")        
        self.hash = HashGenerator(algorithm=self.algorithm).hash_generator(self.file_path) # Double Check...
        self.fixity.set("type", self.algorithm)
        self.fixity.set("value",self.hash)
        self.OMG.list_fixity.append([self.algorithm,self.hash,self.file_path])
        self.OMG.list_path.append(self.file_path)        

    def main(self):
        print(f"Start time: {self.start_time}")        
        if self.clear_opex_flag:
            self.clear_opex()
            if self.autoclass_flag or self.fixity_flag or self.force_flag or self.input: pass
            else: 
                self.print_running_time()
                print('Cleared OPEXES. No additional arguments passed, so ending program.'); time.sleep(3)
                raise SystemExit()
        if self.empty_flag:
            ClassificationGenerator(self.root,self.output_path,meta_dir_flag=self.meta_dir_flag).remove_empty_directories()
        self.init_df()
        self.count = 1
        OpexDir(self,self.root).generate_opex_dirs(self.root)
        if self.fixity_flag:
            output_path = define_output_file(self.output_path,self.root,self.meta_dir_flag,output_suffix="_Fixities",output_format="txt")
            export_list_txt(self.list_fixity,output_path)
        self.print_running_time()


class OpexDir(OpexManifestGenerator):
    def __init__(self,OMG,folder_path,title=None,description=None,security=None):
        self.OMG = OMG
        self.root = self.OMG.root
        self.opexns = self.OMG.opexns        
        self.folder_path = win_256_check(folder_path)
        self.xmlroot = ET.Element(f"{{{self.opexns}}}OPEXMetadata",nsmap={"opex":self.opexns})
        self.transfer = ET.SubElement(self.xmlroot,f"{{{self.opexns}}}Transfer")
        self.manifest = ET.SubElement(self.transfer,f"{{{self.opexns}}}Manifest")
        self.folders = ET.SubElement(self.manifest,f"{{{self.opexns}}}Folders")
        self.files = ET.SubElement(self.manifest,f"{{{self.opexns}}}Files")
        if self.OMG.autoclass_flag in {"generic","g","catalog-generic","cg","accession-generic","ag","both-generic","bg"}:
            self.title = os.path.basename(self.folder_path)
            self.description = os.path.basename(self.folder_path)
            self.security = "open"
        else:
            self.title = title
            self.description = description
            self.security = security
        if self.OMG.autoclass_flag or self.OMG.input:
            self.OMG.generate_opex_properties(self.xmlroot,self.folder_path,title=self.title,description=self.description,security=self.security)
            if not self.OMG.metadata_flag in {'none','n'}:
                self.xml_descmeta = ET.SubElement(self.xmlroot,f"{{{self.opexns}}}DescriptiveMetadata")
                self.OMG.generate_descriptive_metadata(self.xml_descmeta,self.folder_path)
    
    def filter_directories(self,directory):    #Sorts the list Alphabetically and Ignores: 1. Hidden Directories starting with '.', 2. '.opex' files, 3. Folders titled 'meta', 4. Script file 5. Output file. 
        list_directories = sorted([win_256_check(os.path.join(directory,f)) for f in os.listdir(directory) \
        if not f.startswith('.') \
        or (stat(os.stat(f).st_file_attributes) & stat.FILE_ATTRIBUTE_HIDDEN) \
        and f != 'meta'\
        and f != os.path.basename(__file__) \
        and not f.endswith('_AutoClass.xlsx') and not f.endswith('_autoclass.xlsx')\
        and not f.endswith('_EmptyDirectoriesRemoved.txt')],key=str.casefold)
        return list_directories
        
    def generate_opex_dirs(self,file_path):
        os.chdir(file_path)
        if self.OMG.title_flag or self.OMG.description_flag or self.OMG.security_flag: self.title,self.description,self.security = self.OMG.meta_df_lookup(file_path) 
        self = OpexDir(self.OMG,file_path,title=self.title,description=self.description,security=self.security)
        for f in self.filter_directories(file_path):
            if f.endswith('.opex'):
                pass
            elif os.path.isdir(f):
                self.folder = ET.SubElement(self.folders,f"{{{self.opexns}}}Folder")
                self.folder.text = str(os.path.basename(f))
                self.generate_opex_dirs(f)
            else:
                OpexFile(self.OMG,f,self.OMG.algorithm)
        
        for f in self.filter_directories(file_path):                         # Creates the files element of the Opex Manifest.
                if os.path.isfile(f):
                    file = ET.SubElement(self.files,f"{{{self.opexns}}}File")
                    if f.endswith('.opex'): file.set("type","metadata")
                    else:
                        file.set("type","content")
                        file.set("size",str(os.path.getsize(f)))
                    file.text = str(os.path.basename(f))
                #self.count += 1
        opex_path = os.path.join(os.path.abspath(self.folder_path),os.path.basename(self.folder_path))
        self.OMG.write_opex(opex_path,self.xmlroot)

class OpexFile(OpexManifestGenerator):
    def __init__(self,OMG,file_path,algorithm="SHA-1",title=None,description=None,security=None):
        self.OMG = OMG
        self.opexns = self.OMG.opexns  
        self.file_path = win_256_check(file_path)
        self.algorithm = algorithm
        if self.OMG.autoclass_flag in {"generic","g","catalog-generic","cg","accession-generic","ag","both-generic","bg"}:
            self.title = os.path.splitext(os.path.basename(self.file_path))[0]
            self.description = os.path.splitext(os.path.basename(self.file_path))[0]
            self.security = "open"
        else:
            self.title = title
            self.description = description
            self.security = security
        if self.OMG.fixity_flag or self.OMG.autoclass_flag or self.OMG.input:
            self.xmlroot = ET.Element(f"{{{self.opexns}}}OPEXMetadata",nsmap={"opex":self.opexns})
            if self.OMG.fixity_flag:
                self.transfer = ET.SubElement(self.xmlroot,f"{{{self.opexns}}}Transfer")
                self.fixities = ET.SubElement(self.transfer,f"{{{self.opexns}}}Fixities")
                self.genererate_opex_fixity()            
            if self.OMG.autoclass_flag or self.OMG.input:
                if self.OMG.title_flag or self.OMG.description_flag or self.OMG.security_flag: self.title,self.description,self.security = self.OMG.meta_df_lookup(file_path) 
                self.OMG.generate_opex_properties(self.xmlroot,self.file_path,title=self.title,description=self.description,security=self.security)
                if not self.OMG.metadata_flag in {'none','n'}:
                    self.xml_descmeta = ET.SubElement(self.xmlroot,f"{{{self.opexns}}}DescriptiveMetadata")
                    self.OMG.generate_descriptive_metadata(self.xml_descmeta,self.file_path)
            opex_path = self.OMG.write_opex(self.file_path,self.xmlroot)
            if self.OMG.zip_flag:
                zip_opex(self.file_path,opex_path)