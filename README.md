# Opex Manifest Generator Tool

The Opex Manifest Generator is a Python programme for generating OPEX files for use with Preservica and system's compatible with the OPEX standard. It will recursively go through a 'root' directory and generate an OPEX files for each folder or, depending on specified options, files.

## Why use this tool?

This tool was primarily intended to allow users, to undertake larger uploads safely utilising bulk ingests, utilising the Opex Ingest Workflow, with Folder Manifest's checked to ensure safe transfer. However, it has been tested as functioning with:
- Bulk / Opex Ingest Workflow
- PUT Tool / Auto Ingest Workflows
- Manual Ingest
- Starter/UX2 Ingest uploads (Both File and Folder)

## Features

There are a number of features including:
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

Mistakes happen! The clear option will remove all existing Opex's in a directory.

`opex_generate "C:\Users\Christopher\Downloads\" -clr`

Running this command with no additional options will end the program after clearing the Opex's; if other options are enabled it will proceed with the generation of those Opex's.

### Removing Empty Directories

You can also clear any empty directories from the  by using `--remove-empty` option. This will remove any empty directories and generate a simple text document with a list of all the directories that were removed. This process is not reversible and you will be asked to confirm your choice.

## Filtering

Currently 2 filters are applied to certain files / folders:

1) Hidden directories / files, either by Flag in Windows or starting with '.' in MacOS / Linux, are not included.
2) Folder's titled 'meta' are not included.

Hidden files and directories can be included by utilising the `--hidden` option.

meta folders will always be generated automatically when used with the Fixity and Clearing Empty Directories options; meta directories are also created when using the Auto Classification Generator. You can redirect the path using the `-o` option:

`-o {/path/to/meta/output}`

## Use with the Auto Classification Generator

The Opex Manifest generator becomes much more powerful when utilised with another tool: the Auto Classification Generator, see [here](https://github.com/CPJPRINCE/auto_classification_generator) for further details.

This is built-in to the Opex Manifest Generator and can be utilised to embed identifiers and metadata directly to an Opex or through the use of an Excel spreadsheet or CSV file.

The Opex Manifest Generator makes use of the auto_class_generator as a module, therefore it's behaviour differs somewhat when compared to utilising the standalone command `auto_class.exe`.

### Auto Classification - Code Generation

To generate an auto classification code, call on `-c` option with `catalog` choice. You can also assign a prefix using `-p "ARCH"`:

`opex_generate -c catalog -p "ARCH" C:\Users\Christopher\Downloads`

This will generate Opex's with an identifier `code` for each of the files / folders. As described in the Auto Class module, the reference codes will take the hierarchy of the directories. You can also use the `-s` option to set a starting reference.

You can alternatively utilise the "Accession" / running number mode of generating a code using `-c accession` with the prefix "2024". *Accession is currently hard-coded to use the "File" mode*:

`opex_generate -c accession -p "2024" C:\Users\Christopher\Downloads`

Alternatively you can do both Catalogue / Accession at the same time:

`opex_generate -c both -p "ARCH" "2024" C:\Users\Christopher\Downloads`

To note: when using the `catalog` option, the key `code` is always used by default. When using `accession` the default key is `accref`. This is currently not adjustable, see [here](#XIP-Metadata---Identifiers) for utilising other keys. 

It's possible to also create a `generic` set of metadata which will take the XIP metadata for the Title and Description fields, from the basename of the folder/file. It will also set the Security Status to "open".

`opex_generate -c generic C:\Users\Christopher\Downloads`

You can combine the generic options with `catalog, accession, both` to generate an identifier alongside generic data.

## Auto Classification - Spreadsheet as an Input Override 

This program also supports utilising an Auto Class spreadsheet as an input override, utilising the data added into said spreadsheet, instead of generating them ad hoc.

In this way, metadata can be set on XIP Metadata fields, including:
 - Title
 - Description
 - Security Status
 - Identifiers
 - SourceID

As well as XML metadata templates, including the default templates and custom templates.

### XIP metadata - Title, Description and Security Status

To use an input override, we need to first create a spreadsheet with the path of. You can utilise the `auto_class` tool installed alongside the Opex Generator.

`auto_class -p "ARCH" "C:\Users\Christopher\Downloads"`

In the resultant spreadsheet, add in "Title", "Description", and "Security" as new columns. The column headers have to match exactly, and are case-sensitive; these fields would then be filled in with the relevant data.

![ScreenshotXIPColumns](assets/Column%20Headers.png)

Once the cells are filled in with data; to initialise the generation run: `opex_generate -i "{/path/to/your/spreadsheet.xlsx}" "{/path/to/root/directory}"`

Ensure that the root directory matches the original directory of the export. In the above case this would be: `opex_generate -i "C:\Users\Christopher\Downloads\meta\Downloads_AutoClass.xlsx" "C:\Users\Christopher\Downloads"`

The column headers are drop-in, drop-out, meaning you can the columns as and when you need them. You can also leave blank data,the cell you leave blank will simply not these will not be assigned.

When assigning the `Security` field, the tag must be a match to an existing tag in your system. This is case-sensitive, so "Closed" will NOT match to a tag called "closed".

### Important Note

If there are any changes to the hierarchy data, such as a file/folder (not including a 'meta' folder) being removed or added after the export of the spreadsheet, the data may not be assigned correctly, or it may be assigned as "ERROR", or the program may simply fail.

### XIP Metadata - Identifiers

Custom Identifiers can be added by adding the columns: `"Archive_Reference", "Accession_Reference", "Identifier", or "Identifer:Keyname"`.

![Identifier Screenshot](assets/Identifiers%20Headers.png)

`Archive_Reference` or `Identifier` will default to the keyname `code`; `Accession_Reference` will default to `accref`. When using the Auto Classification Generator it will always generate a column called `Archive_Reference`, but you can simply rename or remove this column as neccessary. 

To add a custom identifier import, do so like: `Identifier:MyCodeName`. As many identifier's as needed can be added.

No additional parameter's need to be set in the command line when using Identifier's, addition is enabled by default. Leaving a cell blank will use Preservica's defaults.

### XIP Metadata - Hashes

If you utilise the Auto Classification's tool for generating Hashes; when utilising the `-fx` option in combination with `-i`, if the columns `Hash` and `Algorithm` are both present the program will read the hashes from the spreadsheet instead of generating them.

![Hash Screenshot](assets/Hash%20Headers.png)

*Be aware that interruption / resuming is not currently supported with the Auto Class Tool.

### XML Metadata - Basic Templates

DC, MODS, GPDR, and EAD templates are supported alongside installation of the package.

After exporting an Auto Class spreadsheet, add in additional columns to the spreadsheet; like the XIP data, all fields are optional, and can added on a 'drop-in' basis. 

![XML Headers](assets/XML%20Headers.png)

You can add in the column header in two ways: *'exactly'* or *'flatly'*. (There are probably better words to describe this behaviour)

An Exactly match requires that the full path from the XML document is added to the column, with parent to child separated by a `/`; 'flatly' requires only the matching end tag.

To give an example, the below will match to the same `recordIdentifer` field in the mods template:

```
Exactly:
mods:recordInfo/mods:recordIdentifier

Flatly:
mods:recordIdentifier
```

In both cases, the header has to match both the namespace and tag. This is also case sensitive.

While using the flat method is easier, be aware that if there's non-unique tags, such as `mods:note`, the flat method will only import to the first match, which might not be it's intended destination.

When using the 'exactly' and you have non-unique tags, again such as `mods:note`, you will need add an index in square brackets `[0]` to indicate which tag to assign the data to, like: `mods:note[1] mods:notes[2] ...` The number of field will simply be the order they appear in the XML.

This is all probably easier done, than said :\). For convenience I've also included full templates for DC, MODS, GDPR and EAD, with their explicit names in the headers [here](opex_manifest_generator/samples/spreads).

Once you have added in your headers and the necessary data to create the OPEX's simply add `-m` with the chosen method of import `flat|exact`, so:
`opex_generate -i "{/path/to/your/spreadsheet.xlsx}" "{/path/to/root/directory}" -m flat` or 
`opex_generate -i "{/path/to/your/spreadsheet.xlsx}" "{/path/to/root/directory}" -m exact`

Be aware that when you add an XML Metadata column to the spreadsheet, it will always add the entire metadata template to the OPEX - even if all the cells are left blank. As this is a useful function (adding blank templates to your import), I will leave this for now, but may adjust this in the future.

### XML Metadata Templates - Custom Templates

Any custom XML template can be added to the 'metadata' folder in the installation directory. As long as the XML template is functioning in Preservica, it will work 'out of the box'. All XML's in the directory are checked when enabling the `-m` option.

The location of this will depend on the install path utilising by Python; typically it will be under `/path/to/ptyhoninstall/Lib/site-packages/opex_manifest_generator/metadata`

*In the future I will likely allow the destination of this directory to be set by an option or adjustable, for ease of use.*

Then in the spreadsheet you simply need to add matching column headers - you can utilise either flat or exact methods as described above.

### Custom Spreadsheets - Quick Note

You technically don't have to utilise the AutoClass tool at all. Any old spreadsheet will do!

The only requirement to use the input override, is the presence of the `FullName` column. With an accurate list of paths.

![FullName Column](assets/FullName%20Column.png)

Other columns can be added or removed as needed.

#### Additional Information

A SourceID can also be set by adding a `SourceID` header. The behaviour of this is not fully tested yet.

Ignoring Files can also be set by adding an `Ignore` header. When this is set to `TRUE` this will skip the generation of an Opex for the specified File or Folder; when done for folder's, the folder Opex will still include any ignored file's in its manifest.

Removing Files or Folders is also possible, by adding a `Removals` header. When this is set to `TRUE`, the specified File or Folder will be removed from the system. As a safeguard this must be enabled by adding the parameter `-rm, --remove`, and confirming. *Currently this process is failing...* 

To note when importing a column for an XML Metadata template that needs to be a boolean IE `TRUE/FALSE`. Please ensure that no cells are left blank, otherwise these may be imported inaccurately as `1.0` or `0.0`. This is a pandas issue, that I'm not sure how to fix... :/

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

- Customisable Filtering
- Adjust Accession so the different modes can utilised from Opex.
- Add SourceID as option for use with Auto Class Spreadsheets. *Added!*
- Allow for multiple Identifier's to be added with Auto Class Spreadsheets. Currently only 1 or 2 identifiers can be added at a time, under "Archive_Reference" or "Accesion_Refernce". These are also tied to be either "code" or "accref". An Option needs to be added to allow custom setting of identifier... *Added!*
- Zipping to conform to PAX
- Add an option / make it a default for Metadata XML's to be located in a specified directory rather than in the package.
- In theory, this tool should be compatible with any system that makes use of the OPEX standard. But in theory Communism works, in theory.

## Developers

You should also be able to embed the program directly in Python. Though be warned I haven't tested this functionally much!

```
from opex_manifest_generator import OpexManifestGenerator as OMG
 
OMG(root="/my/directory/path", algorithm = "SHA-256").main()

```

## Contributing

I welcome further contributions and feedback.
