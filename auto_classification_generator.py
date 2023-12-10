import os
from pathlib import Path
import pandas as pd
from datetime import datetime
import argparse
import time

class ClassificationGenerator():
    def __init__(self,
                 root,
                 output_path=os.getcwd(),
                 prefix=None,
                 accprefix=None,
                 start_ref=1,
                 empty_flag=False,
                 skip_flag=False,
                 accession_flag=None,
                 meta_dir_flag=True,
                 output_format="xlsx"):
        
        self.root = os.path.abspath(root)
        self.root_level = self.root.count(os.sep)
        self.root_path = os.path.dirname(self.root)         
        self.output_path = output_path
        self.output_format = output_format
        self.empty_flag = empty_flag
        self.skip_flag = skip_flag
        self.prefix = prefix
        self.start_ref = int(start_ref)
        self.reference_list = []
        self.record_list = []
        self.accession_flag = accession_flag
        self.accession_list = []
        self.accession_count = start_ref
        if accprefix: self.accession_prefix = accprefix
        else: self.accession_prefix = prefix
        self.empty_list = []
        self.meta_dir_flag = meta_dir_flag
    
    def remove_empty_directories(self):
        confirm_delete = input('\n***WARNING*** \
                               \n\nYou have selected the Remove Empty Folder\'s Option. \
                               \nThis process is NOT reversible! \
                               \n\nPlease confirm this by typing in "Y" \
                               \nTyping in any other character will cause this program to self destruct... \
                               \n\nPlease confirm your choice: ')
        if not confirm_delete in {"Y","y"}:
            print('Running self destruct program...\n')
            for n in reversed(range(10)):
                print(f'Self destruction in: {n}',end="\r")
                time.sleep(1)
                raise SystemExit()
        walk = list(os.walk(self.root))
        for path, _, _ in walk[::-1]:
            if len(os.listdir(path)) == 0:
                self.empty_list.append(path)
                os.rmdir(path)
                print(f'Removed Directory: {path}')
        if self.empty_list: 
            output_txt = define_output_file(self.output_path,self.root,self.meta_dir_flag,output_suffix="_EmptyDirectoriesRemoved",output_format="txt")
            export_list_totxt(self.empty_list, output_txt)
        else: print('No directories removed!')

    def filter_directories(self,directory):    #Sorts the list Alphabetically and Ignores: 1. Hidden Directories starting with '.', 2. '.opex' files, 3. Folders titled 'meta', 4. Script file 5. Output file. 
        list_directories = sorted([f for f in os.listdir(directory) \
            if not f.startswith('.') \
            and not f.endswith('.opex') \
            and f != 'meta'\
            and f != os.path.basename(__file__) \
            and not f.endswith(f'_AutoClass.{self.output_format}') and not f.endswith(f'_autoclass.{self.output_format}')\
            and not f.endswith('_EmptyDirectoriesRemoved.txt')],key=str.casefold)
        return list_directories
    
    def parse_directory_dict(self,file_path,level,ref):
        full_path = os.path.abspath(file_path)
        file_stats = os.stat(file_path)                                 #Stats
        if self.accession_flag:                                                   #Optional Accession Reference - Archive Reference is always generated. 
            acc_ref = self.accession_running_number(file_path)
            self.accession_list.append(acc_ref)
        if os.path.isdir(file_path): file_type = "Dir"
        else: file_type = "File"
        class_dict = {'RelativeName': str(file_path).replace(self.root_path,""),
                        'FullName':str(full_path),
                        'Basename': os.path.splitext(os.path.basename(file_path))[0],
                        'Extension': os.path.splitext(file_path)[1],
                        'Parent':str(Path(full_path).parent),
                        'Attribute':file_type,
                        'Size':file_stats.st_size,
                        'CreateDate':datetime.fromtimestamp(file_stats.st_ctime),
                        'ModifiedDate': datetime.fromtimestamp(file_stats.st_mtime),
                        'AccessDate':datetime.fromtimestamp(file_stats.st_atime),
                        'Level':level,
                        'Ref_Section':ref}
        self.record_list.append(class_dict)
        return class_dict
        
    def list_directories(self,directory,ref=1):
        ref = int(ref)
        try:
            list_directory = self.filter_directories(directory)
            level = directory.count(os.sep) - self.root_level + 1 # Counts the number of Seperators in the current file and subtracts from rootlevels (giving current level).
            for file in list_directory:
                file_path = os.path.join(directory,file)        
                # Processing and appending the metadata to lists.
                self.parse_directory_dict(file_path,level,ref)
                ref = int(ref) + int(1)
                if os.path.isdir(file_path): self.list_directories(file_path,ref=1)
        except Exception as e:
            print(e)
            print("Error Occured for directory/file: {}".format(list_directory))
            pass
        
    def init_dataframe(self):
        self.parse_directory_dict(file_path=self.root,level=0,ref=0)
        self.list_directories(self.root,self.start_ref) # Lists Directories..
        df = pd.DataFrame(self.record_list)                                                                             # A Dataframe is created from record dictionary IE List of Directories.
        df = df.merge(df[['FullName','Ref_Section']],how='left',left_on='Parent',right_on='FullName')                   # The dataframe is merged on itself, Parent is merged 'left' on FullName
                                                                                                                        # This is in effect looks up and pulls thorugh the Parent row's data to the Child Row 
        df = df.drop(['FullName_y'], axis=1)                                                                            # Fullname_y is dropped - as it's not needed
        df = df.rename(columns={'Ref_Section_x':'Ref_Section','Ref_Section_y':'Parent_Ref','FullName_x':'FullName'})    # Rename occurs to realign columns
        df['Parent_Ref'] = df['Parent_Ref'].fillna(0)                                                                   # Any Blank rows in Parent Ref set to 0                                                      
        df = df.astype({'Parent_Ref': int})                                                                             # Parent Ref is set as Type int
        df.index.name = "Index"
        self.list_loop = df[['Ref_Section','Parent','Level']].values.tolist()                                           # Reference Section, Parent and Levels are exported to lists for iterating in ref_loop
        self.df = df
        if self.skip_flag: pass
        else: self.init_reference_loop()
        return self.df
    
    def init_reference_loop(self):
        c = 0                       
        tot = len(self.list_loop)
        #print(tot)
        for REF,PARENT,LEVEL in self.list_loop:
            #print(REF,PARENT,LEVEL)
            c += 1
            print(f"Generating Auto Classification for: {c} / {tot}",end="\r") # For a simple progress bar....
            TRACK = 1  
            self.reference_loop(REF,PARENT,TRACK,LEVEL)  #Start's Reference Loop - Recursive Function, so operates on it's own!
        print()
        self.df['Archive_Reference'] = self.reference_list
        if self.accession_flag:
            self.df['Accession_Reference'] = self.accession_list
        return self.df
    
    def reference_loop(self, REF, PARENT, TRACK, LEVEL, NEWREF=None):
        '''
        The reference loop works upwards, running an "index lookup" against the parent folder until it reaches the top.
        
        NEWREF is the archive reference constructed during this loop.
        REF is the reference section derived from the list in the list_directories function.
        PARENT is the parent folder of the child. 
        TRACK is an iteration tracker to distinguish between first and later iterations.
        LEVEL is the level of the folder, 0 being the root.
        The reference loop indexes from the dataframe established by listing the directories. The index compares FullName against the Parent
        If the index fails / is 0, then the top has been reached; if LEVEL is also 0 IE the top-most item is being looked at (normally the first thing). NEWREF is REF
        Otherwise the top-most level has been reached: NEWREF is NEWREF.
        If the index matches, then top level has not yet been reached. 
        PARENTREF is looked up, to avoid an error at the 2nd most top-layer. If PARENTREF is 0, then:
        If TRACK is 1, IE the first iteration, NEWREF is NEWREF + REF
        If TRACK isn't one
        '''
        try:
            idx = self.df.index[self.df['FullName'] == PARENT]          # Indexes the Parent of a file against the FullName (Giving the index number of 
            if idx.size == 0:                               # If Index fails / is 0. then the Top-Level of tree has been reached.
                if LEVEL == 0: 
                    NEWREF = str(REF)            # If the Level is 0, (IE it's the top-most reference being Indexed - no ref_loop involved), NEWREF is REF
                    if self.prefix: NEWREF = str(self.prefix)
                else: 
                    NEWREF = str(NEWREF)                       # If the Level is not 0, IE the ref-level has reached the top-most reference, NEWREF is NEWREF (The constructed Reference from the loop.)
                    if self.prefix: NEWREF = str(self.prefix) + "/" + str(NEWREF)                             # If a Prefix is given; add Prefix to the previously given New Reference.
                        
                self.reference_list.append(NEWREF)                               # NEWREF is appended to the new_reference_list.
                        
            else:                                                                       # Else if Index is successful / Top-Level has not been reached.
                PARENTREF = self.df.loc[idx].Ref_Section.item()                         # Indexes / returns the 'Ref_Section' and 'Parent' columns of the Dataframe against idx
                if PARENTREF == 0:
                    if TRACK == 1: NEWREF = str(REF)                 # If TRACK is 1, IE the first iteration, REF is concatenated with PARENTREF 
                    else: NEWREF = str(NEWREF)                       # If TRACK isn't 1, IE any later iteration. NEWREF is concatenated with PARENTREF                    
                else:
                    if TRACK == 1: NEWREF = str(PARENTREF) + "/" + str(REF)                 # If TRACK is 1, IE the first iteration, REF is concatenated with PARENTREF 
                    else: NEWREF = str(PARENTREF) + "/" + str(NEWREF)                       # If TRACK isn't 1, IE any later iteration. NEWREF is concatenated with PARENTREF
                    
                SUBPARENT = self.df.loc[idx].Parent.item() 
                PARENT = SUBPARENT                                                      # PARENT becomes PARENTPARENT, IE Parent of the Parent 
                                                                                        # This is key, as it allows the loop to lookup the ?above? file.  
                TRACK = TRACK+1                                                         # TRACK is advanced 
                self.reference_loop(REF, PARENT, TRACK, LEVEL, NEWREF)                  # Acts as a recursive function - loop is only being activated in else condition

        except Exception as e:
            print('Passed?')
            print(e)
            pass 
        
    def main(self):
        if self.empty_flag: self.remove_empty_directories()
        self.init_dataframe()
        output_file = define_output_file(self.output_path,self.root,meta_dir_flag=self.meta_dir_flag,output_format=self.output_format)
        if self.output_format == "xlsx": export_xl(df=self.df,output_filename=output_file)
        elif self.output_format == "csv": export_csv(df=self.df,output_filename=output_file)
                    
    def accession_running_number(self,file_path):
        if self.accession_flag == "File":
            if os.path.isdir(file_path): accession_ref = self.accession_prefix + "-Dir"
            else: accession_ref = accession_ref = self.accession_prefix + "-" + str(self.accession_count); self.accession_count += 1
        elif self.accession_flag == "Dir":
            if os.path.isdir(file_path): accession_ref = self.accession_prefix + "-" + str(self.accession_count); self.accession_count += 1
            else: accession_ref = accession_ref = self.accession_prefix + "-File"
        elif self.accession_flag == "All":
            accession_ref = self.accession_prefix + "-" + str(self.accession_count); self.accession_count += 1
        return accession_ref

def define_output_file(output_path,output_name,meta_dir_flag=True,output_suffix="_AutoClass",output_format="xlsx"):
    path_check(output_path)
    if meta_dir_flag:
        path_check(os.path.join(output_path,"meta"))
        output_dir = os.path.join(output_path,"meta",str(os.path.basename(output_name)) + output_suffix + "." + output_format)
    else: output_dir = os.path.join(output_path,str(os.path.basename(output_name)) + output_suffix + "." + output_format)
    return output_dir

def export_list_totxt(txt_list,output_filename):
    try: 
        with open(output_filename,'w') as writer:
            for line in txt_list:
                writer.write(f"{line}\n")
    except Exception as e:
        print(e)
        print('Waiting 10 Seconds to try again...')
        time.sleep(10)
        export_list_totxt(txt_list,output_filename)
    finally:
        print(f"Saved to: {output_filename}")

def export_csv(df,output_filename):
    try:
        df['Archive_Reference'] = df['Archive_Reference'].astype('string')
        df.to_csv(output_filename,sep=",",encoding="utf-8")
    except Exception as e:
        print(e)
        print('Waiting 10 Seconds to try again...')
        time.sleep(10)
        export_csv(df,output_filename)
    finally:
        print(f"Saved to: {output_filename}")

def export_xl(df,output_filename):
    try:
        with pd.ExcelWriter(output_filename,mode='w') as writer:
            df.to_excel(writer)
    except Exception as e:
        print(e)
        print('Waiting 10 Seconds to try again...')
        time.sleep(10)
        export_xl(df,output_filename)
    finally:
        print(f"Saved to: {output_filename}")
        
def parse_args():
    parser = argparse.ArgumentParser(description="OPEX Manifest Generator for Preservica Uploads")
    parser.add_argument('rootpath',nargs='?', default=os.getcwd())
    parser.add_argument("-p","--prefix",required=False, nargs='?')
    parser.add_argument("-accp", "--acc-prefix",required=False, nargs='?')
    parser.add_argument("-rm","--empty",required=False,action='store_true')
    parser.add_argument("-acc","--accession",required=False,choices=['None','Dir','File','All'],default=None)
    parser.add_argument("-o","--output",required=False,nargs='?')
    parser.add_argument("-s","--start-ref",required=False,nargs='?',default=1)
    parser.add_argument("-m","--meta-dir",required=False,action='store_true',default=True)
    parser.add_argument("--skip",required=False,action='store_true',default=False)
    parser.add_argument("-fmt","--output-format",required=False,default="xlsx",choices=['xlsx','csv'])
    
    args = parser.parse_args()
    return args

def path_check(path):
    if os.path.exists(path):
        pass
    else: os.makedirs(path)

if __name__ == "__main__":
    args = parse_args()
    if isinstance(args.rootpath,str): args.rootpath = args.rootpath.strip("\"").rstrip("\\")
    if not args.output:
        args.output = os.path.abspath(args.rootpath)
        print(f'No output path selected, defaulting to root Directory: {args.output}')
    else:
        args.output = os.path.abspath(args.output)
        print(f'Output path set to: {args.output}')
        
    ClassificationGenerator(args.rootpath,
                            output_path=args.output,
                            prefix=args.prefix,
                            accprefix=args.acc_prefix,
                            empty_flag=args.empty,
                            accession_flag=args.accession,
                            start_ref=args.start_ref,
                            meta_dir_flag=args.meta_dir,
                            skip_flag=args.skip,
                            output_format=args.output_format).main()
    print('Complete!')