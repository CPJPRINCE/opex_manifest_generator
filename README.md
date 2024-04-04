# Opex Manifest Generator Tool

The Opex Manifest Generator is a Python programme for generating OPEX files for use with Preservica and system's compatible with the OPEX standard. It will recursively go through a 'root' directory and generate an OPEX files for each folder or, depending on specified options, files.

## Why use this tool?

This tool was primarily intended to allow users, to undertake larger uploads safely utilising bulk ingests, utilising the Opex Ingest Workflow, with Folder Manifest's checked to ensure safe transfer. However, it has been tested as functioning with:
- Bulk / Opex Ingest Workflow
- PUT Tool / Auto Ingest Workflows
- Manual Ingest
- Starter/UX2 Ingest uploads (Both File and Folder)

## Additional features

There are a number of additional feature's utilised including:
- Generating Fixities for files, with SHA1, MD5, SHA256, SHA512 (Default is SHA1)
- OPEX's can also be cleared, for repeated / ease of use.
- OPEX's can be zipped with the file, for imports use with Starter/UX2/Manual ingest methods

The Program also makes use of the Auto Classification Generator, allowing for:
- Reference's can be automatically generated and embedded into the Opex, with assignable prefixes.
- This can utilise either the Catalog or Accession mode, or both!
- Clear and log empty folders.

A key feature of the program, is that the Auto Class spreadsheet can also act as an input, meaning you can utilise the generated spreadsheet to assign metadata to your files and folders. Currently this allows:
- Assignment of title, description, and security status fields.  
- Assignment of standard and custom xml metadata templates. \**Custom XML's require a small bit of setup*
- These fields are all 'drop-in', so only the fields as they are required need to be added. 

All these features can be combined to create extensive and robust Opex files for transfer.

## Prerequisites

Python Version 3.8+ is recommended; the program is OS independent and works on Windows, MacOS and Linux.

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

`opex_generate "{path/to/your/folder}"`

Replacing `{path/to/your/folder}` with your folder path in quotations; for instance, on Windows this looks like:

`opex_generate "C:\Users\Christopher\Downloads"`

### Fixity Generation

To generate a fixity for each file within a given folder and add it to the Opex, you can use the `-fx` option.

`opex_generate "C:\Users\Christopher\Downloads\" -fx`

By default this will run with the SHA-1 algorithm. To utilise a different algorithm, specify it like so:

`opex_generate "C:\Users\Christopher\Downloads\" -fx SHA-256`

You can utilise MD5, SHA-1, SHA-256, SHA-512 algorithms.

### Zipping 

You can also utilise the zip option to bundle the opex and content into a zip file. For use with manual ingests or for Starter / UX2 users.

`opex_generate "C:\Users\Christopher\Downloads\" -fx SHA-1 -z`

Currently, no files will be removed after the zipping. Be aware that running this command multiple times in row will break existing Opex's.

### Clearing Opex's

Mistakes happen! So, the clear option will remove all existing Opex's in a directory.

`opex_generate "C:\Users\Christopher\Downloads\" -clr`

Running this command with no additional options will end the program after clearing the Opex's; if other options are enabled it will proceed with the generation of those Opex's.

## Filtering note

Currently a number of filters are applied to certain files / folders.

1) Hidden directories / files and those starting with '.' are not included.
2) Folder's titled 'meta' are not included.

Hidden files and directories can be included by utilising the `--hidden` option.

## Use with the Auto Classification Generator

The Opex Manifest generator becomes much more powerful when utilised with another tool: the Auto Classification Generator, see [here](https://github.com/CPJPRINCE/auto_classification_generator) for further details.

This is built-in to the Opex Manifest Generator and can be utilised to embed identifiers and metadata directly to an Opex or through use of a spreadsheet / CSV file.

The Opex Manifest Generator makes use of the auto_class_generator as a module. It's behaviour differs somewhat when compared to utilising the standalone command `auto_class.exe`.

### Auto Classification - Code Generation

To generate an auto classification code, call on `-c` option with `catalog` choice. You can also assign a prefix using `-p ARCH`:

`opex_generate -c catalog -p "ARCH" C:\Users\Christopher\Downloads`

This will generate Opex's with an identifier `code` for each of the files / folders. As described in the Auto Class module, the reference codes will take the hierarchy of the directories. You can use the `-s` option to set a starting reference.

You can alternatively utilise the "Accession" / running number mode of generating a code using `-c accession` with prefix `2024`. *To note Accession is currently hard-coded to use "File" mode*:

`opex_generate -c accession -p "2024" C:\Users\Christopher\Downloads`

Alternatively you can do both Catalogue / Accession at the same time:

`opex_generate -c both -p "ARCH" "2024" C:\Users\Christopher\Downloads`

To note: when using the `catalog` option, the key `code` is always used by default. When using `accession` the default key is `accref`. This is currently not adjustable, see [here](### XIP Metadata - Identifiers) for utilising other keys. 

It's possible to also create a `generic` set of metadata which will take the XIP metadata for Title, Description from the basename of the folder/file and will set the Security Status to `open`. 

`opex_generate -c generic C:\Users\Christopher\Downloads`

You can combine generic options with catalog, accession, both to also generate an identifer.

You can also clear Empty Directory by using `--remove-empty` option. This will also generate 

## Auto Classification - Spreadsheet as Input 

This program also supports utilising an Auto Class spreadsheet as an input, utilising the data added into said spreadsheet, instead of generating them on command.

In this way, metadata can be set on XIP Metadata fields, including:
 - Title
 - Description
 - Security Status
 - Identifiers
 - SourceID

As well as XML metadata templates, including the default templates and custom templates.

### XIP metadata - Title, Description and Security Status

To create the spreadsheet base spreadsheet:

`opex_generate -c catalog -p "ARCH" -ex "C:\Users\Christopher\Downloads"` or `auto_class -p "ARCH" "C:\Users\Christopher\Downloads"` to avoid unnecessary OPEX creation.

In the resultant spreadsheet, add in "Title", "Description", and "Security" as new columns. The column headers have to match exactly, including capitalisation; these fields would then be filled in with the relevant data.

Once the cells are filled in with data; to initialise the generation run: `opex_generate -i "{/path/to/your/spreadsheet.xlsx}" "{/path/to/root/directory}"`

Ensure that the root directory matches the original directory of the export. In the above case this would be: `opex_generate -i "C:\Users\Christopher\Downloads\meta\Downloads_AutoClass.xlsx" "C:\Users\Christopher\Downloads"`

To note, the column headers are drop-in, drop-out, meaning you can the columns as and when you need them. You can also leave blank data,the cell you leave blank will simply not these will not be assigned.

To also note, the `Security` must match an existing tag in your system, exactly by it's name.

To also also note, if there are any changes to the hierarchy data, such as a file/folder (not including a 'meta' folder) being removed or added, after the export of the initial spreadsheet, the data may not be assigned correctly.

### XIP Metadata - Identifiers

Custom Identifiers can be added by naming columns: `"Archive_Reference", "Accession_Reference", "Identifier", or "Identifer:Keyname"`.

If named `Archive_Reference` or `Identifier` the keyname will default to `code`, if named `Accession_Reference` the keyname will default to `accref`. Using the Auto Classification Generator will always generate a column called `Archive_Reference`, you can simply rename or remove this column if not needed. 

To add a custom identifier import, do so like so: `Identifier:MyCodeName`. As many identifier's as needed can be added.

No additional parameter's need to be set in the command line when using Identifier's, addition is detected by default.

### XML Metadata - Basic Templates

To utilise an import with XML Metadata templates, first the XML template has to be stored in the source 'metadata' directory. DC, MODS, GPDR, and EAD templates come with the package.

After exporting an Auto Class spreadsheet, add in additional columns to the spreadsheet; like the XIP data, all fields are optional, and can added on a 'drop-in' basis. You can add in the column header in two ways: 'exactly' or 'flatly'.

An Exactly match requires that the full path from the XML document is added to the column, with parent to child separated by a `/`; 'flatly' requires only a the matching end tag. For example, the below will match to the same `recordIdentifer` field in the mods template:

```
Exactly:
mods:recordInfo/mods:recordIdentifier

Flatly:
mods:recordIdentifier
```

In both cases, the header has to match both namespace and tag and isI case sensitive. While using the flat method is easier, be aware that if there's non-unique tags, such as `mods:note`, the flat method will only import to the first match, which might not be it's intended destination.

When using the 'exactly' and you have non-unique tags, again such as `mods:note`, you will need add an index in square brackets `[0]` to indicate which tag to assign the data to, like: `mods:note[1] mods:notes[2] ...` The number of field will simply be the order they appear in the XML.

This is all probably easier done, than said :\). For convenience I've also included *(Note to self: ADD THEM!)*, spreadsheet templates of DC, MODS, GDPR and EAD, with their explicit names in the headers.

Once the above is setup, and all the data added; to create the OPEX's simply add `-m` with the chosen method of import `flat|exact`, so:
`opex_generate -i "{/path/to/your/spreadsheet.xlsx}" "{/path/to/root/directory}" -m flat` or 
`opex_generate -i "{/path/to/your/spreadsheet.xlsx}" "{/path/to/root/directory}" -m exact`

To note: when you add an XML Metadata column to the XL spreadsheet, it will always add this to the OPEX - even if the cell is left blank... This may be configurable in the future, but for now please be aware of it.

### XML Metadata Templates - Custom Templates

Any custom template can be added to the metadata folder and it will work 'out of the box', as long as they are functioning within Preservica.

All that is necessary to do, is add the XML Template document and then add it to the 'metadata' folder within the site-package files within the program. Then in the spreadsheet you simply need to add neccesary column headers - you can utilise either flat or exact methods as described above. You can then save this as a template for reuse.

*In the future I will likely allow the destination of this directory to be set by an option or adjustable in one way or aanother, for use without having to go into the Site-Packages.*

#### Additional Information

A SourceID can also be set by adding a `SourceID` header. The behaviour of this is not fully tested yet.

Ignoring Files can also be set by adding an `Ignore` header. When this is set to `TRUE` this will skip the generation of an Opex for the specified File or Folder; when done for folder's, the folder Opex will still include any ignored file's in its manifest.

Removing Files or Folders is also possible, by adding a `Removals` header. When this is set to `TRUE`, the specified File or Folder will be removed from the system. As a safeguard this must be enabled by adding the parameter `-rm, --remove`, and confirming. *Currently this process is failing...* 

To note when importing a column for an XML Metadata template that needs to be a boolean IE `TRUE/FALSE`. Please ensure that none are left blank, otherwise these may be imported inaccurately as `1.0` or `0.0`. This is a pandas issue, that I'm not sure how to fix... :/

## Options

The following options are currently available to run the program with, and can be utilised in various combinations with each other, although some combinations will clash:

```
Options:
        -h,     --help          Show Help dialog

        -v,     --version   Display version information                             [boolean]

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
                            times in a row, will break the Opex's.
        
        --hidden            Will generate Opex's for hidden files and directories   [boolean]

        -rm,  --remove      Will enable removals from a spreadsheet import          [boolean]
                            *Currently Failing do not use*

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
                            it will do both simultaneously.
                            For more details on these see [here](https://github.com/CPJPRINCE/auto_classification_generator).
        
        -p,   --prefix      Assign a prefix to the Auto Classification,             [string]
                            when utilising {both} fill in like:
                            "catalog-prefix","accession-prefix".            
        
        -rme, --remove-     Remove and log empty directories in a structure         [boolean]
                empty       Log will bee exported to 'meta' / output folder
       
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
                            of metadata, Flat will not function correctly. 
                            Enabled -m without specification will use exact,
                            method.
                                
                            Use of metadata requires, an XML document to 
                            be added to the metadata folder, see docs for
                            details (currently in site-packages *may change).

        -dmd, --disable-    Will, disable the creation of the meta.                 [boolean]
                meta-dir    Can also be enabled with output.
  
        -ex     --export    Set whether to export the Auto Class, default           [boolean]
                            behaviour will not create a new spreadsheet.

        -fmt,   --format    Set whether to export as a CSV or XLSX file.            {csv,xlsx}
                            Otherwise defaults to xlsx.

```

## Future Developments

- Adjust Accession so the different modes can utilised from Opex.
- Add SourceID as option for use with Auto Class Spreadsheets.
- Allow for multiple Identifier's to be added with Auto Class Spreadsheets. Currently only 1 or 2 identifiers can be added at a time, under "Archive_Reference" or "Accesion_Refernce". These are also tied to be either "code" or "accref". An Option needs to be added to allow custom setting of identifier...
- Zipping to conform to PAX, 
- Add an option / make it a default for Metadata XML's to be located in a specified directory rather than in the package.
- In theory, this tool should be compatible with any system that makes use of the OPEX standard. But in theory Communism works, in theory.

## Developers

You should also be able to embed the program into Python a Script. Though be warned I haven't tested this functionally much!

```
from opex_manifest_generator import OpexManifestGenerator as OMG
 
OMG(root="/my/directory/path", fixity_flag= True, algorithm = "SHA-256").main()

```

## Contributing

I welcome further contributions and feedback.
