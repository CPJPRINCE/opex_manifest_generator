# Opex Manifest Generator Tool

[![Supported Versions](https://img.shields.io/pypi/pyversions/opex_manifest_generator.svg)](https://pypi.org/project/opex_manifest_generator)
[![CodeQL](https://github.com/CPJPRINCE/opex_manifest_generator/actions/workflows/codeql.yml/badge.svg)](https://github.com/CPJPRINCE/opex_manifest_generator/actions/workflows/codeql.yml)

The Opex Manifest Generator is a Python programme for generating OPEX files for use with Preservica and system's compatible with the OPEX standard. It will recursively go through a 'root' directory and generate an OPEX files for each folder or, depending on specified options, files.

## Why use this tool?

This tool was primarily intended to allow users, to undertake larger uploads safely utilising bulk ingests, utilising the Opex Ingest Workflow, with Folder Manifest's checked to ensure safe transfer. However, it has been tested as functioning with:
- Bulk / Opex Ingest Workflow
- PUT Tool / Auto Ingest Workflows
- Manual Ingest
- Starter/UX2 Ingest uploads (Both File and Folder)

## Features

There are a number of features including:
- Generating Fixities for files, with SHA1, MD5, SHA256, SHA512 (Default is SHA1).
- Generate Multiple Fixities.
- Generate PAX fixities.
- OPEX's can be cleared out, for repeated / ease of use.
- OPEX's can be zipped with the file, for imports use with Starter/UX2/Manual ingest methods.

The Program also makes use of the Auto Classification Generator, allowing for:
- Reference's can be automatically generated and embedded into the Opex, with assignable prefixes.
- This can be utilised either in Catalog or Accession modes, or both.
- Clear and log empty folders.
- Remove and log Files / Folders.
- Ignore specific Files / Folders.
- Sorting!
- Keyword assignment!

A key feature of the program, is that the Auto Class spreadsheet can also act as an input, meaning you can utilise the generated spreadsheet to assign metadata to your files and folders. Currently this allows:
- Assignment of title, description, and security status fields.  
- Assignment of standard and custom xml metadata templates.
- These fields are all 'drop-in', so only the fields as they are required need to be added. 

All these features can be combined to create extensive and robust Opex files for file transfers.

## Prerequisites

Python Version 3.8+ is recommended; the program is OS independent and works on Windows, MacOS and Linux.

The following modules are utilised and installed with the package:
- auto_classification_generator
- pandas
- openpyxl
- lxml

Please ensure that Python is also added to your System's environmental variables.

## Installation / Updates

To install the package, simply run: `pip install -U opex_manifest_generator`. To update it simply run the same command.

## Usage

Useage of the program is from a command line interface / terminal program, such as PowerShell on Windows, Terminal on Mac, or one of the many terminal programs on Linux. 

### Folder Manifest Generation

The basic version of the program will generate only folder manifests, this acts recursively, so every folder within that folder will have an Opex generated.

To run open up a terminal and run the command:

`opex_generate "{path/to/your/folder}"`

Replacing `{path/to/your/folder}` with your folder path in quotations; for instance, on Windows this looks like:

`opex_generate "C:\Users\Christopher\Downloads"`

### Fixity Generation

To generate a fixity for each file within a given folder and create an opex file. this also creates a text document of Fixities. To use the `-fx` option to enable this.

`opex_generate "C:\Users\Christopher\Downloads\" -fx`

By default this will run with the SHA-1 algorithm. You can also utilise MD5, SHA-1, SHA-256, SHA-512 algorithms. Specify it like so:

`opex_generate "C:\Users\Christopher\Downloads\" -fx SHA-256`

You can also generate multiple fixities, by comma seperation - Shoutout to Andrew Doty for adding this:

`opex_generate "C:\Users\Christopher\Downloads\" -fx SHA-256,SHA-1`

You can also enable PAX Fixity generation to generate fixity checks for individual files in PAXes. This is done, as detailed [here (see PAX section)](https://developers.preservica.com/documentation/open-preservation-exchange-opex#opex-sections):

`opex_generate "C:\Users\Christopher\Downloads\" -fx SHA-256 --pax-fixity`

*Sidenote, you can also generate multiple fixites for PAX files*

### Continuous Generation

If dealing with a large amount of files / large sized files the program is in built with the ability to continue where you left off.

By default, the program won't override any previously generated OPEXes. This means you can end the program (using Ctrl + C) and rerun the same (or a different) command and not worry about losing any progress.

### Clearing Opex's

Of course if you do make a mistake you or wish to start over, can utilise the clear option will remove all existing Opex's in a directory.

`opex_generate "C:\Users\Christopher\Downloads\" -clr`

Running this command with no additional options will end the program after clearing the Opex's; if other options are enabled it will proceed with a new generation.

### Zipping 

You can also utilise the zip option to bundle the opex and content into a zip file. For use with manual ingests or for Starter / UX2 users.

`opex_generate "C:\Users\Christopher\Downloads\" -fx SHA-1 -z`

Currently, no files will be removed after the zipping. **Be aware that because of this running this command multiple times in row can lead to lots of zips... Ensure you're at an end point before running this, as there's no easy way to undo this!**

### Removing Empty Directories

You can also clear any empty directories by using the `-rme` or `--remove-empty` option. This will remove any empty directories and generate a simple text document listing the directories that were removed. This process is not reversible and you will be asked to confirm your choice.

### Filtering

Currently 2 filters are applied across all generations.

1) Hidden directories / files, either by the hidden attribute in Windows or by a starting '.' in MacOS / Linux, are not included.
2) Folder's titled `meta` are not included.

Hidden files and directories can be included by utilising the `--hidden` option. `meta` folders currently can not be included except by changing their name.

## Note on 'meta' folders

Meta folders will be generated automatically when used with the `--fixity` and `-rme` options, as well as when some options from the Auto Classification Generator. You can redirect the path of the generated folder using the `-o` option: `-fx -o {/path/to/meta/output}`. Or you can also disable the generation of 'meta' folder using the `-dmd` option.  

## Use with the Auto Classification Generator

The Opex Manifest generator becomes much more powerful when utilised with another tool: the Auto Classification Generator, see [here](https://github.com/CPJPRINCE/auto_classification_generator) for further details.

This is built-in to the Opex Manifest Generator and can be utilised to embed identifiers and metadata directly to an Opex or through the use of an Excel spreadsheet or CSV file.

The Opex Manifest Generator makes use of the auto_class_generator as a module, therefore it's behaviour differs a little different when compared to utilising the standalone command `auto_class.exe`.

### Identifier Generation

To generate an auto classification code, call on `-c` option with `catalog` choice. You can also assign a prefix using `-p "ARCH"`:

`opex_generate -c catalog -p "ARCH" C:\Users\Christopher\Downloads`

This will generate Opex's with an identifier `code` for each of the files / folders. As described in the Auto Class module, the reference codes will take the hierarchy of the directories. You can also use the `-s` option to set a starting reference.

You can alternatively utilise the "Accession" / running number mode of generating a code using `-c accession` with the prefix "2024". You can also utilise the `--accession-mode` option to determine whether to have a running number for `file, folder, both`.

`opex_generate -c accession -p "2024" C:\Users\Christopher\Downloads --accession-mode file`

To note: when using the `catalog` option, the key `code` is set by default, when using `accession` the default key is `accref`. *The default identifier can be set by the options.property file (accref cannot be changes)*

There are also options to generate `both` (Accession and Catalog references); or generate a `generic` set of metadata which will take the XIP metadata for the Title and Description fields, from the basename of the folder/file. It will also set the Security Status to "open": `opex_generate -c generic C:\Users\Christopher\Downloads`

You can also combine the generic options, like so: `catalog-generic, accession-generic, both-generic` to generate an identifier alongside generic data: `opex_generate -c catalog-generic C:\Users\Christopher\Downloads`

## Use of Input Override option.

This program also supports utilising an Auto Class spreadsheet as an 'input override', utilising the data added into said spreadsheet instead of generating them ad hoc like above.

Using this method XIP Metadata fields can be set on Ingest, including:

 - Title
 - Description
 - Security Status
 - Identifiers
 - SourceID

XML metadata template data, from both the default templates and custom templates can also be set.

<details>
<summary>
Click to find out more!
</summary>

### XIP metadata - Title, Description and Security Status

To use an input override, we need to first create a spreadsheet with the path of. You can utilise the `auto_class` tool installed alongside the Opex Generator, like so:

`auto_class -p "ARCH" "C:\Users\Christopher\Downloads"`

In the resultant spreadsheet, add in "Title", "Description", and "Security" as new columns. The column headers are case-sensistive and have to match exactly. These fields would then be filled in with the relevant data.

![ScreenshotXIPColumns](assets/Column%20Headers.png)

Once the cells are filled in with data, run a generation like so: `opex_generate -i "{/path/to/your/spreadsheet.xlsx}" "{/path/to/root/directory}"`

Ensure that the root directory matches the original directory of the export. In the above case this would be: `opex_generate -i "C:\Users\Christopher\Downloads\meta\Downloads_AutoClass.xlsx" "C:\Users\Christopher\Downloads"`

### Headers Note

The column headers are drop-in, drop-out, meaning you can the columns as and when you need them. You can also leave cell's blank if you don't want them to have any data in that field.

To note: When assigning the `Security` field, the tag must be a match to an existing tag in your system. This is case-sensitive, so "Closed" will NOT match to a tag called "closed".

### Another Important Note

If there are any changes to the hierarchy data, such as a file/folder (not including a 'meta' folder) being removed or added after the export of the spreadsheet, the data may not be assigned correctly, or it may be assigned as "ERROR", or the program may simply fail.

### XIP Metadata - Identifiers

Custom Identifiers can be added by adding the columns: `"Archive_Reference", "Accession_Reference", "Identifier", or "Identifer:Keyname"`.

![Identifier Screenshot](assets/Identifiers%20Headers.png)

`Archive_Reference` or `Identifier` will default to the keyname `code`; `Accession_Reference` will default to `accref`. When using the Auto Classification Generator it will always generate a column called `Archive_Reference`, but you can simply rename or remove this column as neccessary. 

To add a custom identifier import, do so like: `Identifier:{YourIdentifierName}`, without the curly brackets IE: `Identifier:MyCode`. Mulitple identifiers can be added as needed.

No additional parameter's need to be set in the command line when using Identifier's, addition is enabled by default. Leaving a cell blank will not add an identifer.

### XIP Metadata - Hashes

If you utilise the Auto Classification's tool for generating Hashes; when utilising the `-fx` option in combination with `-i`, if both the columns `Hash` and `Algorithm` are present, the program will read the hashes from the spreadsheet instead of generating them.

![Hash Screenshot](assets/Hash%20Headers.png)

*Be aware that interruption / resuming is not currently supported with the Auto Class Tool; also doesn't support multiple hashes*

### XML Metadata - Basic Templates

DC, MODS, GPDR, and EAD templates are supported alongside installation of the package.

After exporting an Auto Class spreadsheet, you can add in additional columns to the spreadsheet and fill it out with data for an import. Like the XIP data, all fields are optional, and can added on a 'drop-in' basis. 

![XML Headers](assets/XML%20Headers.png)

The column header's can be added in either of two ways, what I term: `exactly` or `flatly`. (There are probably better words to describe this).

An `exactly` match requires that the full path of the tag in the XML document is added to the column header. With each parent and child separated by a `/`; 'flatly' requires only the matching end tag.

To give an example, from the mods template:

```
Exactly:
mods:recordInfo/mods:recordIdentifier

Flatly:
mods:recordIdentifier
```

Both cases match to the field `recordIdentifer`. Note that header includes both the namespace and tag, and is also case sensitive.

While using the `flatly` method is easier, be aware that if there's non-unique tags, such as `mods:note` in the Mods template. This method will only import to the first match, which might not be it's intended destination. Using the `exactly` method resolves this issue.


Once you have added in your headers and the necessary data to create the OPEX's simply add the `-m` option, with the chosen method of import `flat|exact`, so:
`opex_generate -i "{/path/to/your/spreadsheet.xlsx}" "{/path/to/root/directory}" -m flat` or 
`opex_generate -i "{/path/to/your/spreadsheet.xlsx}" "{/path/to/root/directory}" -m exact`

### XML Metadata - Quick Note 

When you have non-unique tags, again, such as `mods:note`, you will need add an index in square brackets `[0]` to indicate which tag to assign the data to, like: `mods:note[1] mods:notes[2] ...` The number of field will simply be the order they appear in the XML.

For convenience I've included the full templates for DC, MODS, GDPR and EAD, with the `exact` names in the headers [here](https://github.com/CPJPRINCE/opex_manifest_generator/tree/master/samples/spreads). I also created the `--print-xmls` function to display this info (including square bracket placement).

Also be aware that when using `-m` option and column headers for that XML document are present in the spreadsheet, it will add a metadata template to the OPEX, even if all the cells are left blank. As this is a useful function (adding blank templates to your import), I will leave this for now, but may adjust this in the future.

### XML Metadata Templates - Custom Templates

Any custom XML template, that is functioning in Preservica will work with this method. All XML's in a given `metadata` directory are checked when enabling the `-m` option.

The default location will be in the installation path of the program, typically under `/path/to/ptyhoninstall/Lib/site-packages/opex_manifest_generator/metadata`. However, you can also utilise the `-mdir` option to set this to a specific folder, to have a dedicated section.

After the xml is added to that directory, all that's required is to add the matching column headers into your spreadsheet. You can also utilise `--print-xmls` to obtian this.

### Additional Information for Auto Classification
#### SourceID

A SourceID can also be set by adding a `SourceID` header. The behaviour of this is not fully tested, likely won't be as I don't really utilise SourceIDs in my work :\).

#### Ignore

Ignoring Files can also be set by adding an `Ignore` header. When this is set to `TRUE` this will skip the generation of an Opex for the specified File or Folder; when done for folder's, the folder Opex will still include any ignored file's in its manifest.

#### Removals

Removing Files or Folders is also possible, by adding a `Removals` header. When this is set to `TRUE`, the specified File or Folder will be removed from the system. As a safeguard this must be enabled by adding the parameter `-rm, --remove`, and confirming the deletion when prompted.

#### Keywords

You can utilise keywords to replace reference numbers with abbreviated characters for instance: `--keywords "Secret Metadata Folder"` will replace the reference number with `"SMF"`. You can also set different modes with `--keywords-mode`. `intialise` will take the intials of each letter like in the previous example; `firstletters` will take the first x number of letters. So the above becomes `"SEC"`. You can set multiple keywords with by comma seperation. If `--keywords` is set without any set strings it will be applied to every word.

There are further details in the Options Section.

#### Sorting

You can also sort utilisiing `--sort-by`. There are currently two options: `foldersfirst` and `alphabetical`. Folders first sorts folders first, then files (both alphabetically); alphabetically sorts both folders and files alphabetically.

#### Options File

You can utilise your own option-file to change the default column headers for the Input override method. See the option `--option-file path/to/file`. Defaults are:

```[options]

INDEX_FIELD = FullName
TITLE_FIELD = Title
DESCRIPTION_FIELD = Description
SECUIRTY_FIELD = Security
IDENTIFIER_FIELD = Identifier
IDENTIFIER_DEFAULT = code
REMOVAL_FIELD = Removals
IGNORE_FIELD = Ignore
SOURCEID_FIELD = SourceID
HASH_FIELD = Hash
ALGORITHM_FIELD = Algorithm
```
#### Custom Spreadsheets - Quick Note

You technically don't have to utilise the AutoClass tool at all. Any old spreadsheet will do!

The only requirement to use the input override, is the presence of the `FullName` column. With an accurate list of paths.

![FullName Column](assets/FullName%20Column.png)

</details>

## Further Options

The full options are given below; also see `opex_generate --help`

<details>
<summary>
Click here
</summary>

```
Options:
        -h,     --help          Show Help dialog                                        [boolean flag]

        -v,     --version       Display version information                             [boolean flag]

    Opex Options:

        -fx,  --fixity          Generate a Fixity Check for files.                      [SHA-1,MD5, SHA-256, SHA-512
                                Can set multiple fixies with comma.                     | boolean flag]
                                IE MD5,SHA-1.                            
                                [Defaults to SHA-1 if not specified]                    

        --pax-fixity            Generates a Fixity Check for PAX files / Folders        [boolean flag]
                                If not set PAX files / folders will be treated 
                                as standard.
                
        -clr, --clear-opex      Will remove all existing Opex folders,                  [boolean flag]
                                When utilised with no other options, will end
                                the program.
        
        -z,   --zip             Will zip the Opex's with the file itself to create      [boolean flag]
                                a zip file. Existing file's are currently not removed.
                                ***Use with caution, repeating the command multiple 
                                times in a row, will break the Opex's.
        
        --hidden                Will generate Opex's for hidden files and directories   [boolean flag]

        -rm,  --remove          Will enable removals from a spreadsheet import          [boolean flag]
                        
        -opt  --options-file    Specify an 'options.properties' file to change set      [PATH/TO/FILE]
                                presets for column headers for input.

    Auto Classification Options:

        -c,  --autoclass        This will utilise the AutoClassification                [{catalog, accession,both,
                                module to generate an Auto Class spreadsheet.           generic, catalog-generic,
                                                                                        accesison-generic,
                                There are several options, {catalog} will generate      both-generic}]
                                a Archival Reference following; {accession}
                                will create a running number of files
                                (Currently this is not configurable).
                                {both} will do Both!
                                {generic} will populate the Title and 
                                Description fields with the folder/file's name,
                                if used in conjunction with one of the above options:
                                {generic-catalog,generic-accession, generic-both}
                                it will do both simultaneously.
        
        --accession-mode        Sets whether to have the runnig tally be for            {file,folder,both}
                                files, folders or both,
                                when utilising the Accession option with 
                                autoclass. Default is file.
        
        -p,   --prefix          Assign a prefix to the Auto Classification,             [PREFIX]
                                when utilising {both} fill in like:
                                "catalog-prefix","accession-prefix".            
        
        -rme, --remove-         Remove and log empty directories in a structure         [boolean flag]
                empty           Log will bee exported to 'meta' / output folder
       
        -o,   --output          Set's the output of the 'meta' folder when              [PATH/TO/FOLDER] 
                                utilising AutoClass.
                                
        -s,   --start-ref       Sets the starting Reference in the Auto Class           [int]
                                process.

        -i    --input           Set whether to use an Auto Class spreadsheet as an      [PATH/TO/FILE]
                                input. The input needs to be the (relative or
                                absolute) path of the spreadsheet.

                                This allows for use of the Auto Class spreadsheet
                                to customise the XIP metadata (and custom xml 
                                metadata).

                                The following fields have to be added to the
                                spreadsheet and titled exactly as:
                                Title, Description, Security.

        -m    --metadata        Toggles use of the metadata import method.              [{none,flat,exact} 
                                                                                        | boolean flag]
                                There are two methods utilised by this:
                                'exact',or 'flat'.

                                Exact requires that the column names in the spread
                                sheet match exactly to the XML:
                                {example:path/example:to/example:thing}

                                Flat only requires the final tag match.
                                IE {example:thing}. However, for more complex sets
                                of metadata, Flat will not function correctly.

                                Enabled with -m. 
                                [Defaults to 'exact' method if not
                                specificed]
                                
                                Use of metadata requires, XML documents to 
                                be added to the metadata folder, see docs for
                                details.

        -mdir   --metadata      Specify the metadata directroy to pull the XMLs files   [PATH/TO/FOLDER]
                -dir            from.
                                [Defaults to lib folder if not set]

        -dmd,   --disable       Will disable the creation of the 'meta' folder.         [boolean flag]
                -meta-dir       Can also be enabled with output.
  
        -ex     --export        Set whether to export any Auto Class generation         [boolean flag] 
                                to a spreadsheet

        -fmt,   --format        Set whether to export as a CSV or XLSX file.            {csv,xlsx}
                                [Default is to xlsx].

        -dlm    --delimiter     Set to specify the delimiter between References         [DELIMITER STRING]
        
        -key    --keywords      Specify which keywords to look for and replace the      [KEYWORDS ... | boolean flag]
                                 generated reference with an abbreviation of the 
                                word (depending on mode). For instance:
                                "A list Strings" will be abbreviated ALS. 
                                
                                Has to be an exact match to files / folders
                                names. Can set multiple strings to look for with
                                commas like so: "My Strings,I wish,to replace"
                                
                                Can also be set without specifying any words to
                                apply to everything.

        --keym  --keywords      Specify the mode to use for keywords                    {intialise,firstletters}
                -mode           Either 'intialise' taking the first letter of each
                                word between spaces IE "Department of Justice" becomes
                                "DOJ".

                                'firstletters' takes the first n amount of letters.
                                The aforementioned becomes "DEP"

        --keywords-retain-      Specify if you wish continue or reset reference         [boolean flag]
        -order                  numbering for references not in keywords. 
                                
                                IE By default if a keyword is found and replaced,
                                where it would normally be reference number '3'. 
                                The next reference down would be given the number 3.

                                Using this option, the next reference would be given
                                4.

        --keywords-abbreviation Set the number of characters to abbreviate to for       [int]
        -number                 keywords option
                                [Default is 3 first letters, -1 for intialise]
        
        --sort-by               Set the method to sort. Can either utilise              {foldersfirst,alphabetical}
                                'foldersfirst' to sort folders first then
                                alphabetically or 'alphabetical to sort
                                both folders and files alphabetically
                                [Default is foldersfirst.]
```
</details>

## Future Developments

- ~~Customisable Filtering~~ *Added!*
- ~~Adjust Accession so the different modes can utilised from Opex.~~ *Added!*
- ~~Add SourceID as option for use with Auto Class Spreadsheets.~~ *Added!*
- ~~Allow for multiple Identifier's to be added with Auto Class Spreadsheets. Currently only 1 or 2 identifiers can be added at a time, under "Archive_Reference" or "Accesion_Refernce". These are also tied to be either "code" or "accref". An Option needs to be added to allow custom setting of identifier...~~ *Added!*
- ~~Add an option / make it a default for Metadata XML's to be located in a specified directory rather than in the package.~~ *Added!*
- Zipping to conform to PAX - Last on the check list; it techincally does...
- In theory, this tool should be compatible with any system that makes use of the OPEX standard... But in theory Communism works, in theory...

## Developers

For Developers you can also embed / use the program directly in Python. Though be warned I haven't tested this functionally much!

```
from opex_manifest_generator import OpexManifestGenerator as OMG
 
OMG(root="/my/directory/path", algorithm = "SHA-256").main()

```

## Contributing

I welcome further contributions and feedback! If there any issues please raise them [here](https://github.com/CPJPRINCE/opex_manifest_generator/issues)
