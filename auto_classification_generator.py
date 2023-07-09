#! /usr/bin/env python3
import os
from pathlib import Path
import pandas as pd
from datetime import datetime
import argparse

record_list = []
acc_count = 1
ListNewRef = []
ListAccession = []
def main():
    parser = argparse.ArgumentParser(description="OPEX Manifest Generator for Preservica Uploads")
    parser.add_argument('tree_root',nargs='?', default=os.getcwd())
    parser.add_argument("-p","--prefix",required=False, nargs='?')
    parser.add_argument("-rm","--empty",required=False,action='store_true')
    parser.add_argument("-acc","--accession",required=False,nargs='?')
    parser.add_argument("-o","--output",required=False,nargs='?')
    args = parser.parse_args()
    cwd = os.path.abspath(args.tree_root)
    global output_path
    if not args.output:
        output_path = os.path.abspath(args.tree_root)
        print(f'No output path selected, defaulting to root Directory: {output_path}')
    else:
        output_path = os.path.abspath(args.output)
        print(f'Output path set to: {output_path}')

    if args.empty:
        print('Removing Empty Directories\n')
        remove_empty_folders(os.path.abspath(cwd))
    
    df = auto_class(cwd,prefix=args.prefix,accession=args.accession)
    export_xl(df,output_path,tree_root=cwd)
    print('Complete!')


def accession_numbering(dir,prefix_accession):
    global acc_count 
    if os.path.isdir(dir):
        accession_ref = prefix_accession + "-Dir"
    else:
        accession_ref = prefix_accession + "-" + str(acc_count)
        acc_count += 1
    return accession_ref


def list_dirs(CWD,ROOTLEVEL,accession=None):
    ref = 1
    try:
        listdir = os.listdir(CWD)
        #Sorts the list Alphabetically and Ignores: 1. Hidden Directories starting with '.', 2. '.opex' files, 3. Folders titled 'meta', 4. Script file 5. Output file. 
        listdir = sorted([f for f in listdir if not f.startswith('.') \
                        and not f.endswith('.opex') \
                        and f != 'meta'\
                        and f != os.path.basename(__file__) \
                        and not f.endswith('_AutoClass.xlsx') and not f.endswith('_autoclass.xlsx')\
                        and not f.endswith('_EmptyDirectoriesRemoved.txt')])
        # Counts the number of Seperators in the current file.
        level = CWD.count(os.sep)
        # Subracts the previous count from ROOTLEVEL to give the current level of the file (USed to compose the Archive reference).
        level = level-ROOTLEVEL
        for file in listdir:
            # Processing and appending the metadata to lists.
            fpath = os.path.join(CWD,file)
            full_path = os.path.abspath(fpath)
            #Stats
            stat = os.stat(fpath)
            #Optional Accessoin Reference - Currently the Archive Reference
            if accession:
                ListAccession.append(accession_numbering(fpath,accession))
            if os.path.isdir(fpath): type = "Dir"
            else: type = "File"
            class_dict = {'RelativeName': str(fpath).replace(path_root,""), 'FullName':str(full_path), \
                    'Basename': os.path.basename(fpath),'Extension':os.path.splitext(fpath)[1],'Parent':str(Path(full_path).parent),\
                    'Attribute':type,'Size':stat.st_size,'CreateDate':datetime.fromtimestamp(stat.st_ctime),\
                    'ModifiedDate': datetime.fromtimestamp(stat.st_mtime),'AccessDate':datetime.fromtimestamp(stat.st_atime), \
                    'Level':level,'Ref_Section':ref}
            record_list.append(class_dict)
            ref = ref+1
            if os.path.isdir(fpath): list_dirs(fpath,ROOTLEVEL,accession)
            
            

    except Exception as e:
        print(e)
        print("Error Occured for directory/file: {}".format(listdir))
        pass

# ref_loop function loops through the.

def ref_loop(REF, PARENT, TRACK, LEVEL, df,NEWREF=None, PREFIX=None):
    # Indexes the Parent of a file against the Name (Giving the Loc of the Parent)
    idx = df.index[df['FullName'] == PARENT]
    # If top-level has been reached, IE Index fails to match...
    if idx.size == 0:
        # If the Level is 0, (IE it's the top-most reference being Indexed - no ref_loop involved), NEWREF is REF
        if LEVEL == 0:
            NEWREF = str(REF)
        # If the Level is not 0, IE the ref-level has reached the top-most reference, NEWREF is NEWREF (The constructed Reference from the loop.)
        else:
            NEWREF = NEWREF
        if PREFIX:
            PREFIX_NEWREF = str(PREFIX) + "/" + str(NEWREF)
            ListNewRef.append(PREFIX_NEWREF)
        else:
            PREFIX=None
            #NEWREF is appended to the NewRef list.
            ListNewRef.append(NEWREF)
    # Action if the top-level has not been reached.
    # Parent Reference and the Name of Parent (PARENTPARENT) are retrieved to continue the loop 
    else:
        PARENTREF = df.loc[idx].Ref_Section.item()
        PARENTPARENT = df.loc[idx].Parent.item()
        # If TRACK is 1, IE the first iteration, it will append, REF 
        if TRACK == 1:
            NEWREF = str(PARENTREF) + "/" + str(REF)
        # If TRACK isn't 1, IE any 'below' iteration, it will append NEWREF to PARENT. 
        else:
            NEWREF = str(PARENTREF) + "/" + str(NEWREF)
        #PARENT of PARENT becomes PARENT, for lookup, this allows the loop to lookup the next file.  
        PARENT = PARENTPARENT
        TRACK = TRACK+1
        #Loop iterates over itself - note that the loop is only being activated in else condition
        # IE when the top-level HASN'T been reached. 
        ref_loop(REF, PARENT, TRACK, LEVEL, df, NEWREF, PREFIX)

def auto_class(cwd,prefix=None,accession=None):
    cwd = os.path.abspath(cwd)
    # ROOTLEVEL gives an intial count of the Root Directories Seperators.
    rootlevel = cwd.count(os.sep)
    global path_root
    path_root = os.path.dirname(cwd)
    list_dirs(cwd,rootlevel,accession)

    # A Dataframe is created from the various lists appended in the list_dirs function.
    # A merge on Parent agasint Name (Path) then occurs. Pulling through the Parent's details to that row. 
    # Duplicate data dropped and / Parent_Ref requires data to be to be filled in..  

    df = pd.DataFrame(record_list)
    
    df = df.merge(df[['FullName','Ref_Section']],how='left',left_on='Parent',right_on='FullName')
    df = df.drop(['FullName_y'], axis=1)
    df = df.rename(columns={'Ref_Section_x':'Ref_Section','Ref_Section_y':'Parent_Ref','FullName_x':'FullName'})
    df['Parent_Ref'] = df['Parent_Ref'].fillna(0).astype(int)
    df = df.astype({'Parent_Ref': int})
    df.index.name = "Index"

    #Lists of References, Parent and Levels are exported to lists for iterating in ref_loop
    ListRef = df['Ref_Section'].values.tolist()
    ListParent = df['Parent'].values.tolist()
    ListLevel = df['Level'].values.tolist()
    
    #c is a count / total of items in ListRef, for a simple progress bar.
    c = 0
    tot = len(ListRef)

    for R,P,L in zip(ListRef,ListParent,ListLevel):
        c += 1
        print(f"Generating Auto Classification for: {c} / {tot}",end="\r")
        # T is Track
        T = 1
        ref_loop(R,P,T,L,df,PREFIX=prefix)
    df['Archive_Reference'] = ListNewRef
    if accession:
        df['Accession_Reference'] = ListAccession
    return df

def path_check(path):
    if os.path.exists(path):
        pass
    else: os.makedirs(path)

def export_xl(df,output_path,output_suffix="_AutoClass.xlsx",tree_root=None):
    if not tree_root: tree_root = os.path.abspath(output_path)
    else: tree_root = os.path.abspath(tree_root)
    output_path = os.path.abspath(output_path)
    path_check(output_path)
    path_check(os.path.join(output_path,"meta"))
    output_filename = os.path.join(output_path,"meta",str(os.path.basename(tree_root)) + output_suffix)
    with pd.ExcelWriter(output_filename,mode='w') as writer:
        df.to_excel(writer)
    print(f"Saved to: {output_filename}")
    return output_filename

def export_txt_list(list,output_path,output_suffix="_EmptyDirsRemoved.txt",tree_root=None):
    if not tree_root: tree_root = output_path
    else: tree_root = os.path.abspath(tree_root)
    path_check(output_path)
    path_check(os.path.join(output_path,"meta"))
    output_filename = os.path.join(output_path, "meta", str(os.path.basename(tree_root)) + output_suffix)
    with open(output_filename,'w') as writer:
        for line in list:
            writer.write(f"{line}\n")

def remove_empty_folders(remove_path):
    elist = []
    walk = list(os.walk(remove_path))
    for path, _, _ in walk[::-1]:
        if len(os.listdir(path)) == 0:
            elist.append(path)
            os.rmdir(path)
    if elist: 
        global output_path
        export_txt_list(elist, output_path)
    else: print('No directories removed!')

if __name__ == "__main__":
    main()
