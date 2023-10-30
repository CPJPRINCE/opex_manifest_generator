import os
from pathlib import Path
import pandas as pd
from datetime import datetime
import argparse
import time

def parse_args():
    parser = argparse.ArgumentParser(description="OPEX Manifest Generator for Preservica Uploads")
    parser.add_argument('root',nargs='?', default=os.getcwd())
    parser.add_argument("-p","--prefix",required=False, nargs='?')
    parser.add_argument("-rm","--empty",required=False,action='store_true')
    parser.add_argument("-acc","--accession",required=False,choices=[None,'Dir','File'],default=None)
    parser.add_argument("-o","--output",required=False,nargs='?')
    parser.add_argument("-s","--start-ref",required=False,nargs='?',default=1)
    parser.add_argument("-m","--meta-flag",required=False,action='store_true',default=True)
    args = parser.parse_args()
    return args

def path_check(path):
    if os.path.exists(path):
        pass
    else: os.makedirs(path)

class ClassificationGenerator():
    def __init__(self, root, output_path=os.getcwd(), prefix=None, start_ref=1, empty_flag=None, accession_flag=None, meta_flag=True):
        self.root = os.path.abspath(root)
        self.root_level = self.root.count(os.sep)
        self.root_path = os.path.dirname(self.root)         
        self.output_path = output_path
        self.empty_flag = empty_flag
        self.prefix = prefix
        self.start_ref = int(start_ref)
        self.reference_list = []
        self.record_list = []
        self.accession_flag = accession_flag
        self.accession_list = []
        self.accession_count = start_ref
        self.accessoin_prefix = self.prefix
        self.empty_list = []
        self.meta_flag = meta_flag
    
    def remove_empty_directories(self):
        confirm_delete = input('You have selected the Remove Empty Folder\'s Option... This process is not reversible \n Please confirm Y to continue: ')
        if not confirm_delete in {"Y","y"}:
            print('You have not selected Y... Running self destruct program...')
            for n in reversed(range(10)):
                print(f'Self In: {n}',end="\r")
                time.sleep(1)
                raise SystemExit()
        walk = list(os.walk(self.root))
        for path, _, _ in walk[::-1]:
            if len(os.listdir(path)) == 0:
                self.empty_list.append(path)
                os.rmdir(path)
                print(f'Removed Directory: {path}')
        if self.empty_list: 
            output_txt = define_output_directory(self.output_path,self.root,self.meta_flag,output_suffix="_EmptyDirectoriesRemoved.txt")
            self.export_txt(self.empty_list, output_txt)
        else: print('No directories removed!')

    def filter_directories(self,directory):    #Sorts the list Alphabetically and Ignores: 1. Hidden Directories starting with '.', 2. '.opex' files, 3. Folders titled 'meta', 4. Script file 5. Output file. 
        list_directories = sorted([f for f in os.listdir(directory) if not f.startswith('.') \
            and not f.endswith('.opex') \
            and f != 'meta'\
            and f != os.path.basename(__file__) \
            and not f.endswith('_AutoClass.xlsx') and not f.endswith('_autoclass.xlsx')\
            and not f.endswith('_EmptyDirectoriesRemoved.txt')])
        return list_directories

    def list_directories(self,directory,ref=1):
        ref = int(ref)
        try:
            list_directory = self.filter_directories(directory)
            level = directory.count(os.sep) - self.root_level  # Counts the number of Seperators in the current file and subtracts from rootlevels (giving current level).
            for file in list_directory:
                # Processing and appending the metadata to lists.
                file_path = os.path.join(directory,file)
                full_path = os.path.abspath(file_path)
                file_stats = os.stat(file_path)                                 #Stats
                if self.accession_flag:                                                   #Optional Accessoin Reference - Archive Reference is always generated. 
                    acc_ref = self.accession_running_number(file_path)
                    self.accession_list.append(acc_ref)
                if os.path.isdir(file_path): file_type = "Dir"
                else: file_type = "File"
                class_dict = {'RelativeName': str(file_path).replace(self.root_path,""),
                              'FullName':str(full_path),
                              'Basename': os.path.basename(file_path),
                              'Extension':os.path.splitext(file_path)[1],
                              'Parent':str(Path(full_path).parent),
                              'Attribute':file_type,
                              'Size':file_stats.st_size,
                              'CreateDate':datetime.fromtimestamp(file_stats.st_ctime),
                              'ModifiedDate': datetime.fromtimestamp(file_stats.st_mtime),
                              'AccessDate':datetime.fromtimestamp(file_stats.st_atime),
                              'Level':level,
                              'Ref_Section':ref}
                self.record_list.append(class_dict)
                ref = int(ref) + int(1)
                if os.path.isdir(file_path): self.list_directories(file_path,ref=1)
                
        except Exception as e:
            print(e)
            print("Error Occured for directory/file: {}".format(list_directory))
            pass
        
    def init_dataframe(self):
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
        self.init_reference_loop()
        return self.df
    
    def init_reference_loop(self):
        c = 1                       
        tot = len(self.list_loop)
        #print(tot)
        for REF,PARENT,LEVEL in self.list_loop:
            #print(REF,PARENT,LEVEL)
            c += 1
            print(f"Generating Auto Classification for: {c} / {tot}",end="\r") # For a simple progress bar....
            TRACK = 1  
            self.reference_loop(REF,PARENT,TRACK,LEVEL)  #Start's Reference Loop - Recursive Function, so operates on it's own!
        self.df['Archive_Reference'] = self.reference_list
        if self.accession_flag:
            self.df['Accession_Reference'] = self.accession_list
        return self.df
    def reference_loop(self, REF, PARENT, TRACK, LEVEL, NEWREF=None):
        try:
            #print(REF,PARENT,LEVEL)
            idx = self.df.index[self.df['FullName'] == PARENT]          # Indexes the Parent of a file against the FullName (Giving the index number of the Parent)
            if idx.size == 0:                               # If Index fails / is 0. then the Top-Level of tree has been reached.
                
                if LEVEL == 0: NEWREF = str(REF)            # If the Level is 0, (IE it's the top-most reference being Indexed - no ref_loop involved), NEWREF is REF
                else: NEWREF = NEWREF                       # If the Level is not 0, IE the ref-level has reached the top-most reference, NEWREF is NEWREF (The constructed Reference from the loop.)
                if self.prefix:                             # If a Prefix is given; add Prefix to the previously given New Reference.
                    PREFIX_NEWREF = str(self.prefix) + "/" + str(NEWREF)
                    self.reference_list.append(PREFIX_NEWREF)                       # PREFIXNEW
                else: self.reference_list.append(NEWREF)                            # NEWREF is appended to the new_reference_list.
                        
            else:                                                                       # Else if Index is successful / Top-Level has not been reached.
                PARENTREF = self.df.loc[idx].Ref_Section.item()                         # Indexes / returns the 'Ref_Section' and 'Parent' columns of the Dataframe against idx
                SUBPARENT = self.df.loc[idx].Parent.item() 
                if TRACK == 1: NEWREF = str(PARENTREF) + "/" + str(REF)                 # If TRACK is 1, IE the first iteration, REF is concatenated with PARENTREF 
                else: NEWREF = str(PARENTREF) + "/" + str(NEWREF)                       # If TRACK isn't 1, IE any later iteration. NEWREF is concatenated with PARENTREF
                PARENT = SUBPARENT                                                      # PARENT becomes PARENTPARENT, IE Parent of the Parent 
                                                                                        # This is key, as it allows the loop to lookup the ?above? file.  
                TRACK = TRACK+1                                                         # TRACK is advanced 
                self.reference_loop(REF, PARENT, TRACK, LEVEL, NEWREF)                  # Acts as a recursive function - loop is only being activated in else condition
                                                                                        # IE when the top-level HASN'T been reached.
        except Exception as e:
            print('Passed?')
            print(e)
            pass 
        
    def main(self):
        if self.empty_flag: self.remove_empty_directories()
        self.init_dataframe()
        output_xl = define_output_directory(self.output_path,self.root,meta_flag=self.meta_flag)
        self.export_xl(output_xl)
                    
    def accession_running_number(self,dir):
        if os.path.isdir(dir):
            if self.accession_flag == "File": accession_ref = self.accessoin_prefix + "-Dir"
            elif self.accession_flag == "Dir": 
                accession_ref = self.accessoin_prefix + "-" + str(self.accession_count)
                self.accession_count += 1
        else:
            if self.accession_flag == "Dir": accession_ref = self.accessoin_prefix + "-File"
            elif self.accession_flag == "File": 
                accession_ref = self.accessoin_prefix + "-" + str(self.accession_count)
                self.accession_count += 1
        return accession_ref

def define_output_directory(output_path,root_name,meta_flag=True,output_suffix="_AutoClass.xlsx"):
    path_check(output_path)
    if meta_flag:
        path_check(os.path.join(output_path,"meta"))
        output_dir = os.path.join(output_path,"meta",str(os.path.basename(root_name)) + output_suffix)
    else: output_dir = os.path.join(output_path,str(os.path.basename(root_name)) + output_suffix)
    return output_dir

def export_txt(txt_list,output_filename):
    try: 
        with open(output_filename,'w') as writer:
            for line in txt_list:
                writer.write(f"{line}\n")
    except Exception as e:
        print(e)
        print('Waiting 10 Seconds to try again...')
        time.sleep(10)
        export_txt(txt_list,output_filename)
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

if __name__ == "__main__":
    args = parse_args()
    if isinstance(args.root,str): args.root = args.root.strip("\"").rstrip("\\")
    if not args.output:
        args.output = os.path.abspath(args.root)
        print(f'No output path selected, defaulting to root Directory: {args.output}')
    else:
        args.output = os.path.abspath(args.output)
        print(f'Output path set to: {args.output}')
    ClassificationGenerator(args.root,output_path=args.output,prefix=args.prefix,empty_flag=args.empty,accession_flag=args.accession,start_ref=args.start_ref,meta_flag=args.meta_flag).main()
    print('Complete!')