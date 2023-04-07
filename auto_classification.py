#! /usr/bin/env python3
import os
from pathlib import Path
import pandas as pd
from datetime import datetime
import argparse


parser = argparse.ArgumentParser(description="OPEX Manifest Generator for Preservica Uploads")
parser.add_argument('tree_root',nargs='?', default=os.getcwd())
parser.add_argument("-p","--prefix",required=False, nargs='?')
parser.add_argument("-rm","--empty",required=False,action='store_true')
parser.add_argument("-acc","--accession",required=False,nargs='?')
args = parser.parse_args()

output_filename = os.path.basename(args.tree_root) + "_AutoClass.xlsx"

path_root = os.path.dirname(args.tree_root)

def accession_numbering(dir,prefix_accession):
    global acc_count 
    if os.path.isdir(dir):
        accession_ref = prefix_accession + "-DIG-Dir"
    else:
        accession_ref = prefix_accession + "-DIG-" + str(acc_count)
    acc_count += 1
    return accession_ref

acc_count = 1

def list_dirs(CWD,ROOTLEVEL):
    ref = 1
    try:
        listdir = os.listdir(CWD)
        #Sorts the list Alphabetically and Ignores: 1. Hidden Directories starting with '.', 2. '.opex' files, 3. Folders titled 'meta', 4. Script file 5. Output file. 
        listdir = sorted([f for f in listdir if not f.startswith('.') \
                        and not f.endswith('.opex') and f != 'meta' \
                        and f != os.path.basename(__file__) \
                        and f != os.path.basename(output_filename)])
        # Counts the number of Seperators in the current file.
        level = CWD.count(os.sep)
        # Subracts the previous count from ROOTLEVEL to give the current level (For reference).
        level = level-ROOTLEVEL
        for file in listdir:
            # Processing and appending all the data to lists.
            dir = os.path.join(CWD,file)
            listPath.append(str(dir))
            rel_path = dir.replace(path_root,"")
            listRelPath.append(rel_path)
            parent = Path(dir).parent
            listParent.append(str(parent))
            listLevel.append(level)
            stat = os.stat(dir)
            listSize.append(stat.st_size)
            listCreateDate.append(datetime.fromtimestamp(stat.st_ctime))
            listModDate.append(datetime.fromtimestamp(stat.st_mtime))
            listAccessDate.append(datetime.fromtimestamp(stat.st_atime))
            basename = os.path.basename(dir)
            listBasename.append(basename)
            extension = os.path.splitext(dir)[1]
            listExtension.append(extension)
            listRef.append(ref)
            if os.path.isdir(dir):
                type = "Dir"
                listType.append(type)
                list_dirs(dir,ROOTLEVEL)
            else:
                type = "Arc"
                listType.append(type)
            if args.accession:
                listAccession.append(accession_numbering(dir,args.accession))
            ref = ref+1

    except Exception as e:
        print(e)
        print("Error Occured for directory/file: {}".format(listdir))
        pass

# ref_loop will loop...

def ref_loop(REF, PARENT, TRACK, LEVEL, NEWREF, df):
    # Indexes the Parent of a file against the Name (Giving the Loc of the Parent)
    idx = df.index[df['Name'] == PARENT]
    # If top-level has been reached, IE Index fails to match...
    if idx.size == 0:
        # If the Level is 0, (IE it's the top-most reference being Indexed - no ref_loop involved), NEWREF is REF
        if LEVEL == 0:
            NEWREF = str(REF)
        # If the Level is not 0, IE the ref-level has reached the top-most reference, NEWREF is NEWREF (The constructed Reference from the loop.)
        else:
            NEWREF = NEWREF
        if args.prefix:
            PREFIX_NEWREF = str(args.prefix) + "/" + NEWREF
            listNewRef.append(PREFIX_NEWREF)
        else:
            #NEWREF is appended to the NewRef list.
            listNewRef.append(NEWREF)
    # Action if the top-level has not been reached. IE The loop, will iterate over itself.
    # Parent Reference and Parent of Parent are retrieved to continue the loop.
    else:
        PARENTREF = df.loc[idx].Ref.item()
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
        #Loop iterates
        ref_loop(REF, PARENT, TRACK, LEVEL, NEWREF, df)

def auto_class():
    # ROOTLEVEL gives an intial count of the Root Directories Seperators.
    rootlevel = cwd.count(os.sep)
    list_dirs(cwd,rootlevel)

    # Creating the Dataframe.
    # The Dataframe matches the Parent against it's Name. It then drops the additional columns as these are not necessary.  

    df = pd.DataFrame({'Level':listLevel,'Ref':listRef,'RelName': listRelPath, 'Name':listPath, \
                    'Basename': listBasename,'Extension':listExtension,'Parent':listParent,\
                    'Att':listType,'Size':listSize,'CreateDate':listCreateDate,\
                    'ModifiedDate': listModDate,'AccessDate':listAccessDate})
    df = df.merge(df[['Name','Parent','Ref','RelName']],how='left',left_on='Parent',right_on='Name')
    df = df.drop(['Name_y','Parent_y','RelName_y'], axis=1)
    df = df.rename(columns={'Ref_x':'Ref','Ref_y':'PRef','Name_x':'Name','Parent_x':'Parent','RelName_x':'RelName'})
    df['PRef'] = df['PRef'].fillna(0).astype(int)
    df = df.astype({'PRef': int})

    ListRef = df['Ref'].values.tolist()
    ListParent = df['Parent'].values.tolist()
    ListLevel = df['Level'].values.tolist()
    c = 0
    tot = len(ListRef)
    for R,P,L in zip(ListRef,ListParent,ListLevel):
        c += 1
        print(f"Generating Auto Classification for: {c} / {tot}",end="\r")
        T = 1
        #### Set NR to a different starting point.
        NR = 1
        ref_loop(R,P,T,L,NR,df)
    df['NRef'] = listNewRef
    if args.accession:
        df['Accession Reference'] = listAccession

    return df

def export_xl(df):
    df.to_excel(os.path.join(args.tree_root,output_filename))

def remove_empty_folders(path_abs):
    elist = []
    walk = list(os.walk(path_abs))
    for path, _, _ in walk[::-1]:
        if len(os.listdir(path)) == 0:
            elist.append(path)
            os.rmdir(path)
    if elist: 
        with open(os.path.join(args.tree_root, str(os.path.basename(args.tree_root)) + "_EmptyDirectoriesRemoved.txt"),'w') as writer:
            for line in elist:
                writer.write(f"{line}\n")

if __name__ == "__main__":
    
    #Blank Lists created
    listPath = []
    listRef = []
    listParent = []
    listType = []
    listLevel = []
    listRelPath = []
    listSize = []
    listCreateDate = []
    listModDate = []
    listAccessDate = []
    listExtension = []
    listBasename = []
    listAccession = []
    listNewRef = []

    acc_count = 1

    if args.empty:
        print('Removing Empty Directories\n')
        remove_empty_folders(args.tree_root)
    cwd = r"{}".format(args.tree_root)
    df = auto_class()
    export_xl(df)
    print('Complete!')
