# Opex Manifest Generator Tool

The Opex Manifest Generator is a pythom programme for generating OPEX files for use with Preservica and system's compatable with the OPEX standard. It will recursively go through a 'root' directory and generate an OPEX files for each folder or, depending on specified options, files.

## Why use this tool?

This tool was primarily intended to allow users, to undertake larger uploads safetly utilising bulk ingests, utilising the Opex Ingest Workflow, with Folder Manifest's checked to ensure safe transfer. However, it has been tested as functioning with:
- Bulk / Opex Ingest Workflow
- PUT Tool / Auto Ingest Workflows
- Manual Ingest
- Starter/UX2 Ingest uploads (Both File and Folder)

## Additional features

There are a number of additional feature's utilised including:
- Generating Fixities for files, with SHA1, MD5, SHA256, SHA512 (Default is SHA1)
- OPEX's can also be cleared, for repeated / ease of use.
- OPEX's can be zipped with the file, for imports use with Starter/UX2/Manual ingest methods

The Program also Making use of The Auto Classification Generator, a host of other feature's are available.
- Reference's can be automatically generated and embedded into the Opex, with assignable prefixes.
- This can utilise either the Catalog or Accession mode, or both!
- Clear and log empty folders.

A key feature of the program, is that the Auto Class spreadsheet can also act as an input, meaning you can utilise the generated spreadsheet to assign metadata to your files and folders. Currently this allows:
- Assignment of title, description, and security status fields.  
- Assignment of standard and custom xml metadata templates. \**Custom XML's require a small bit of setup*
- These fields are all 'drop-in', so only the fields as they are required need to be added. 

All these features can be combined to create extensive and robust Opex files for transfer.

## Prerequisites

Python Version 3.8+ is recommended; the program is OS independent and should work on Windows, MacOS and Linux.

The following modules are utilised and installed with the package:
- auto_classification_generator
- pandas
- openpyxl
- lxml

## Installation

To install the package, simply run: `pip install -U opex_manifest_generator`

## Usage

### Folder Manifest Generation
The basic version of the program will generate only folder manifests, this acts recursively, so every folder within that folder will have an Opex generated.

To run open up a terminal and run the command:

`opex_generate {path/to/your/folder}`

Replacing `{path/to/your/folder}`; for instance, on Windows this looks like:

`opex_generate "C:\Users\Christopher\Downloads\"`

This is geared towards usage with the Opex Ingest Workflow with Folder Manifest Requirement enabled. By creating these opexes, we can ensure that the workflow will check the .

### Fixity Generation

To generate a fixity for each file within a given folder, we can add the `-fx` option.

`opex_generate "C:\Users\Christopher\Downloads\" -fx`

To utilise a different algorithm:

`opex_generate "C:\Users\Christopher\Downloads\" -fx -alg SHA-256`

This is intended to add an additional check to the Opex Ingest Workflow and other upload methods, ensuring that the content is safely delivered with matching Hashes.

### Zipping 

We can also utilise the zip option to bundle the opex and content into a zip file. For use with manual ingests or for Starter / UX2 users.

`opex_generate "C:\Users\Christopher\Downloads\" -fx -alg SHA-1 -z`

Currently, no files will be removed after the zipping; keep in mind the available space. *Also be aware that running this command multiple times in row will break existing Opex files.

### Clearing Opex's

Mistakes happen! So, the clear option will remove all existing Opex's in a directory.

`opex_generate "C:\Users\Christopher\Downloads\" -clr`

Running this command with no additional options will end the program after clearing the Opex's; if other options are enabled it will proceed with the generation.

## Use with the Auto Classification Generator

Another tool, the Auto Classification Generator, is built-in to this program. While use of this is optional, making use of it allows for some embedding Archival References into the identifer and for Custom imports.

Compared to `auto_class`, see here for details, instead of exporting to a spreadsheet, directly embed the references into the Opex file. To avoid potential conflicts, the behaviour differs when compared to utilising the standalone command.

## Filtering note

Currently a number of filters are applied to certain files / folders.

1) Hidden directories / files and those starting with '.' are not included.
2) Folder's titled 'meta' are not inlcuded.

## Basic Generation

To generate an auto classification code, for a given folder, with prefix `ARCH` simply run:

`opex_generate -c catalog -p "ARCH" C:\Users\Christopher\Downloads`

This will generate Opex's with an identifier "code" added to each of the files. As described in the Auto Class module, the reference codes will take the hierachy of the directories.

To utilise the "Accession" mode of the program:

`opex_generate -c accession -p "2024" C:\Users\Christopher\Downloads`

Or to both:

`opex_generate -c both -p "ARCH" "2024" C:\Users\Christopher\Downloads`

To note: when using the catalog or accession option, the key `"code"` is used as the identifier. When using `both`, the Catalog Reference is given the key `code` and the 'Accession' given the key: `accref`. I will make this adjustable in a future update.

It's possible to also create a 'generic' set of metadata which will take the Title, Description from the basename of the folder/file and set the Security Status to 'Open'. 

`opex_generate -c generic C:\Users\Christopher\Downloads`

Many (but not all) of the options available in Auto Classification are available here:

- Setting Start References
- Clearing Empty Directories

### Use of the Auto Class spreadsheet as an Input 

This program also supports utilising an Auto Class spreadsheet as an input, utilising the data added into said spreadsheet, instead of generating them on command.

In this way, metadata can set: XIP Metadata fields: Title, Description and Security Status; and XML metadata templates on ingest.

#### XIP metadata

To create the spreadsheet base spreadsheet:

`opex_generate -c catalog -p "ARCH" -ex "C:\Users\Christopher\Downloads"` or `auto_class -p "ARCH" "C:\Users\Christopher\Downloads"` to avoid unnecessary OPEX creation.

In the resultant spreadsheet, add in "Title", "Description", and "Security" as new columns. The column header has to match exactly, including captialisation; these fields would then be filled in with the relevant data.

Once filled in; to intialise the generation: `opex_generate -i "{/path/to/your/spreadsheet.xlsx}" "{/path/to/root/directory}"`

Ensure that the root directory matches the original directory of the export. In the above case this would be: `opex_generate -i "C:\Users\Christopher\Downloads\meta\Downloads_AutoClass.xlsx" "C:\Users\Christopher\Downloads"`

Please note, if there are any changes to the hierachy data after the export of the intial spreadsheet, the data may not be assigned correctly.

#### XML Metadata

To utilise an import with XML Metadata templates, first the XML template has to be stord the source 'metadata' directory. DC, MODS, GPDR, and EAD templates come with the package, but custom templates can be added and will work 'out-the-box', as long as they are functioning within Preservica. *I will likely change the destination of this directory for easier use.

After exporting an Auto Class spreadsheet, add in additional columns to the spreadsheet; like the XIP data, all fields are optional, and can added on a 'drop-in' basis. You can add in the column header in two ways: 'exactly' or 'flatly'.

An Exactly match requires that the full path from the XML document is added to the column, with parent to childs seperated by a `/`; 'flatly' requires only a the matching end tag. For example, the below will match to the same `recordIdentifer` field in the mods template:

```
Exactly:
mods:recordInfo/mods:recordIdentifier

Flatly:
mods:recordIdentifier
```

In both cases, the header has to match both namespace and tag and is case sensistive. While using the flat method is easier, be aware that if there's non-unique tags, such as `mods:note`, the flat method will only import to the first match, which might not be it's intended destination. When using the 'exactly' and you havenon-unique tags, again such as `mods:note`, you will need add an index in square brackets `[0]` to indicate which tag to assign the data to, like: `mods:note[1] mods:notes[2] ...` The number of field will simply be the order they appear in the XML.

This is all probably easier done, than said :\). For convience *I've also included* (Note to self: ADD THEM!), spreadsheet templates of DC, MODS, GDPR and EAD, with thier explict names in the headers.

Once the above is setup, and all the data added; to create the OPEX's simply add `-m` with the choosen method of import `flat|exact`, so:
`opex_generate -i "{/path/to/your/spreadsheet.xlsx}" "{/path/to/root/directory}" -m flat` or 
`opex_generate -i "{/path/to/your/spreadsheet.xlsx}" "{/path/to/root/directory}" -m exact`

## Options

The following options are currently avilable to run the program with, and can be utilised in various combinations with each other, although some combinations will clash:

```
Options:
        -h,     --help          Show Help dialog

    Opex Options:

        -fx,  --fixity      Generate a Fixity Check for files.                      [boolean]
        
        -alg  --algorithm   Set to specify which algorithm to use                   {SHA-1,MD5,SHA-256,SHA-512} 
                            for fixity. Defaults to SHA-1.
        
        -clr, --clear-opex  Will remove all existing Opex folders,                  [boolean]
                            When utilised with no other options, will end
                            the program.
        
        -z,   --zip         Will zip the Opex's with the file itself to create      [boolean]
                            a zip file. Existing file's are currently not removed.
                            ***Use with caution, repeating the command multiple 
                            times, will break the Opex's.

    Auto Classification Options:

        -c,  --autoclass    This will utilise the AutoClassification                {catalog, accession, both, generic,
                            module to generate an Auto Class spreadsheet.            catalog-generic, accesison-generic,
                                                                                     both-generic}
                            There are several options, {catalog} will generate
                            a Archival Reference following; {accession}
                            will create a running number of files
                            (Currently this is not configurable).
                            {both} will do Both!
                            {generic} will populate the Title and 
                            Description fields with the folder/file's name,
                            if used in conjunction with one of the above options:
                            {generic-catalog,generic-accession, generic-both}
                            it will do both simutaneously.
                            For more details on these see the 
                            auto_classification_generator page.
        
        -p,   --prefix      Assign a prefix to the Auto Classification,             [string]
                            when utilising {both} fill in like:
                            "catalog-prefix","accession-prefix".            
        
        -rm,  --empty       Remove and log empty directories in a structure         [boolean]
                            Log will bee exported to 'meta' / output folder

        -o,   --output      Set's the output of the 'meta' folder when              [string] 
                            utilising AutoClass.
                                
        -s,   --start-ref   Sets the starting Reference in the Auto Class           [int]
                            process.

        -i    --input       Set whether to use an Auto Class spreadsheet as an      [string]
                            input. The input needs to be the (relative or
                            absolute) path of the spreadsheet.

                            This allows for use of the Auto Class spreadsheet
                            to customise the XIP metadata (and custom xml 
                            metadata).

                            The following fields have to be added to the
                            spreadsheet and titled exactly as:
                            Title, Description, Security.

        -m    --metadata    Toggles use of the metadata import method.              {none,flat,exact}
                            There are two methods utilised by this:
                            {none,exact,flat}. None ignores metadata import
                                
                            Exact requires that the column names in the spread
                            sheet match exactly to the XML:
                            {example:path/example:to/example:thing}
                            Flat only requires the final tag match.
                            IE {example:thing}. However, for more complex sets
                            of metadata, Flat will not function corrrectly. 
                            Enabled -m without specification will use exact,
                            method.
                                
                            Use of metadata requires, an XML document to 
                            be added to the metadata folder, see docs for
                            details (currently in site-packages *may change).

        -dmd, --disable-    Will, disable the creation of the meta.                 [boolean]
                meta-dir    Can also be enabled with output.
  
        -ex     --export    Set whether to export the Auto Class, default
                            behaviour will not create a new spreadsheet.

        -fmt,   --format    Set whether to export as a CSV or XLSX file.           {csv,xlsx}
                            Otherwise defualts to xlsx.
```

## Future Developments

- Adjust Accession so the different modes can utilised from Opex.
- Add SourceID as option for use with Auto Class Spreadsheets.
- Allow for multiple Identifier's to be added with Auto Class Spreadsheets. Currently only 1 or 2 identifers can be added at a time, under "Archive_Reference" or "Accesion_Refernce". These are also tied to be either "code" or "accref". An Option needs to be added to allow cutom setting of identifier...
- Zipping to conform to PAX, 
- Add an option / make it a default for Metadata XML's to be located in a specified directory rather than in the package.
- In theory, this tool should be compatiable with any system that makes use of the OPEX standard. But in theory Communism works, in theory.

## Developers

You should also be able to embed the program into Python a Script. Though be warned I haven't tested this functionally much!

```
from opex_manifest_generator import OpexManifestGenerator as OMG
 
OMG(root="/my/directory/path", fixity_flag= True, algorithm = "SHA-256").main()

```

## Contributing

I welcome further contributions and feedback.
