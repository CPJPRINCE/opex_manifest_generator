# Opex Manifest Generator Tool

[![Supported Versions](https://img.shields.io/pypi/pyversions/opex_manifest_generator.svg)](https://pypi.org/project/opex_manifest_generator)
[![CodeQL](https://github.com/CPJPRINCE/opex_manifest_generator/actions/workflows/codeql.yml/badge.svg)](https://github.com/CPJPRINCE/opex_manifest_generator/actions/workflows/codeql.yml)

A small Python programme for generating opex manifest files. Used for safe transfer of files and metadata ingests into opex compatable systems (Preservica). The program will recurse through a given hierarchy and generate manifests for all folders/files (depending on option).

## Quick Start

### Option 1: Using pip (Recemmend for Python users / long-term use) 
```bash
pip install -U opex_manifest_generator
opex_generate /path/to/root
```
### Option 2: Using Portable Executable (No Python Required)

Download the latest portable executable for your platform from [Releases](https://github.com/CPJPRINCE/opex_manifest_generator/releases)

Extract and run:
```bash
# Windows
cd opex_generate\bin
.\opex_generate.cmd .\path\to\root -fx SHA-256

# Linux\macOS
./opex_generate /path/to/root -fx SHA-256
```
On Windows you can also use the install.cmd with admin priviledges to install and run the command, without navigating to the .cmd directory (see Option 1 for use) 

## Version & Package info

Python Version:

Python Version 3.10+ is recommended. Earlier version my work but are not tested.

Additional Packages:
- auto_reference_generator (required)
- pandas (required)
- tqdm (required)
- openpyxl (required)
- lxml (required)
- odfpy (optional - ods export)

To install using Python:

```bash
pip install pandas openpyxl pyodf lxml tqdm
```

If using Python ensure it is added to Environment. 

### Output
Will generate an `.opex` manifest file for each of your directories. This manifest will contain a list of all files/folders in that directory.

File manifests may also be generated if using additional options. When file manifests are active the folder manifest automatically accounts for additional opexes. 

## Why use this tool?

This tool was primarily intended to allow users, to undertake larger uploads safely utilising bulk ingests. 

It's functional will all methods of Opex Ingests. For Preservica this includes:
- **Opex Incremental Workflow**
- **PUT Tool**
- **Starter Drag 'n' Drop**
- **Manual Ingest**

## Additional Features

- **Hash generation (MD5, SHA1, SHA256, SH512) - for additional security checks.**
- **Generate multiple algorithm hashes**
- **Generate hashes for PAX files**
- **Continous running by default - allowing closure / crashes to pick up where left off**
- **Opex removal**
- **Zip functionality**

The Program also includes the [Auto Reference Generator](https://github.com/CPJPRINCE/auto_reference_generator), built in allowing for:
- **Automated Reference generation straight to Opex files**
- **Clearing and log empty folders**
- **A Removal mode to delete and log files / folders**
- **Sorting - by alphabetically or 'folders first'**
- **Keyword assignment - replacing numericals with specified keywords (intials, first letter, JSON map)**
- **And more! See the github page for details**

A key function built off ARG is the `--input` mode, allowing you to utilise a spreadsheet to assign XIP/XML metadata to your files and folders. Currently this allows:
- **Assignment of XIP title, description, and security status fields**
- **Assignment of standard and custom xml metadata templates**
- **'Drop-in/drop-out' operationso only needed columns are added** 

All these options can be combined to create extensive and robust Opex files for file transfers.

## Expected Output

At a basic level: `opex_generate`, the program will only generate folder manifests.

![Opex in Folder](assets/Opex%20Folder.png)

Which will contain a simple list of files/folders in that directory:

![Opex Folder Manifest](assets/Opex%20Manifest.png)

When using an option that effects files, you will generate indvidual Opexes for files:

![Opex Files](assets/Opex%20Files.png)

These will contain the data about the files (which will vary based selected options).

![Opex File Manifest](assets/Opex%20File%20Manifest.png)

When individual opex files are generated the folder manifest will include these as ***metadata*** files.

![Opex Folder Manifest](assets/Opex%20Manifest%20with%20files.png)

## Advanced Usage

**Important Notes**

- The term `meta` is hard coded to always be ignored. This is case sensitive.
- A meta folder will only be created using `--fixity`, `--remove-empty` or `-rm` options. You can disable this using the `--disable-meta-dir` option or `-o` option to relocate it.

### Fixity Generation

```bash
# Generate with SHA-256 Hash
opex_generate "/path/to/folder" -fx SHA-256

# Generate with MD5 and SHA-256 Hash
opex_generate "/path/to/folder" -fx MD5 SHA-256

# Generate with SHA-512 for PAX - PAXes can be zipped or a folder titled '.pax'
opex_generate "/path/to/paxfolders" -fx SHA-1 --pax-fixity

# Generate with MD5 and SHA1 for PAX
opex_generate "/path/to/paxfolders" -fx MD5 SHA-1  
```

### Continuous Operation

By default the program won't override an existing opex. If an opex is present it will state

```
Avoiding override, Opex exists at: /path/to/opex
```

This allows for continous operation, as long generations - particuarly if you have large files, can be cancelled at any point, then picked up later. To halt the program, simply: `ctrl + C` in the console.

There is no way to force an override, doing so also makes things more complicated than need be. If you need to rerun a generation, use the `-clr` option. 

### Clearing Opex's

```bash
# Will clear existing opexes recursively then end
opex_generate /path/to/folder -clr

# If other options are enabled will clear and rerun generation
opex_generate /path/to/folder -clr -fx SHA1
```

### Zipping 

```bash
# Will zip opex and file into a zip file
opex_generate /path/to/folder -fx SHA-1 -z`

# Will zip opex and file and remove the original files
 opex_generate /path/to/folder -fx SHA-1 -z --remove-zipped-files`

```
**Use zipping with caution, repeated use can get quite messy... fast.**

### Removing Empty Directories

```bash
# Remove and generate a text log to the 'meta' folder of removed directories
opex_generate /path/to/folder --remove-empty

# You will be asked to give confirmation that you want to proceed
```

### Hidden Directories

```bash
# By default hidden directories/files are not included. Adding --hidden include hidden files
opex_generate /path/to/folder --hidden
```

## Auto Reference Usage

As mentioned, built into the OMG is the Auto Reference Generator, allowing archival references to be assigned directly to Opexes. By default codes generated using this method are hard coded to the identifer `code`.

If you want to understand what these Reference will look like, plese see [here](https://github.com/CPJPRINCE/auto_reference_generator?tab=readme-ov-file#structure-of-references).

```bash
# Will generate a reference code for the heirachy with the prefix "ARCH"
opex_generate /path/to/folder -r catalog -p ARCH

# Will generate a reference code with prefix "ARCH-1-2-3", suffix "Z" and delimiter "-"
opex_generate /path/to/folder -r catalog -p "ARCH-1-2-3" -s Z -dlm "-"

# Will generate a reference code without a prefix - this will only be the numericals.

opex_generate /path/to/folder -r catalog

# Will generate an accession code / 'running number' with the prefix "2026-X"
opex_generate /path/to/folder -r accession -p 2026-X

# Will fill in title, description and secuirty tag data based upon file and folder names and sets to the default security tag 'open'
opex_generate -c generic /path/to/folder
```

## Input Option

This program also supports utilising a spreadsheet as an `input`. This allows the data to be prefilled in and set on ingest. The following XIP Metadata fields can be set:

 - Title
 - Description
 - Security Status
 - Identifiers
 - SourceID

XML metadata data is also supported for both default and custom XMLs.

### XIP metadata - Title, Description and Security Tags

To use an input override, we need to first create a spreadsheet with the path of. It's not necessary, but for convience, I'd recommend using the `auto_ref` tool. Like so: 
```bash
auto_ref -p "ARCH" /path/to/root
```

The column headers are all 'drop-in/drop-out`, simply add new columns for the data you'd like to edit. The column headers are case-sensitive and have to match exactly. For Reference, these are the following:

```
- Title
- Description
- Security
```
These fields would then be filled in with the relevant data. **For Security Tags** ensure they are an exact match to the tag on your system, which are also case-sensistive.

![ScreenshotXIPColumns](assets/Column%20Headers.png)

Once the cells are filled in with respective data, run a generation using the `-i` option and input the full path to your spreadsheet. Ensure that the `/path/to/root` is the same root as you generated the spreadsheet for.

```bash
# Will use the 'spreadsheet.xlsx' as an input. 
opex_generate -i /path/to/your/spreadsheet.xlsx /path/to/root

# These can still be combined with the above options.
opex_generate -i /path/to/your/spreadsheet.xlsx -fx SHA-1 /path/to/root
```

**To note** 
- If you leave blank cells it will simply skip the details.
- If you rearrange the hierachy after your spreadsheet generation you may recieve errors or mismatches, due to the folders/files being incorrectly looked up - in these cases you may need to regenerate your list and migrate the data to it.
- Assignment is not specific to Folders/Files.

### XIP Metadata - Identifiers

Identifers are also supported and can be added to the column header following this convention:
```
- Identifier:Key
```
The `Key` will determine the identifer name and cells the value.

![Identifier Screenshot](assets/Identifiers%20Headers.png)

You can also utilise the following columns headers:
```
# Defaults to 'code` key
- Identifier 
- Archive_Reference
# Defaults to 'accref' key
- Accession_Reference
```

### Samples

A completed Opex based on this data:

![Sample Spreadsheet input](assets/Spreadsheet%20Input%20Sample.png)

Using the command: `opex_generate /home/chris/dev/opex_manifest_generator -i /home/chris/Dev/opex_manifest_generator/meta/opex_manifest_generator_AutoRef.xlsx`

Will generate the following for folder manifest:

![Folder Manifest](assets/Folder%20Opex%20Input%20Sample.png)

For file manifest:

![File Manifest](assets/File%20Opex%20Input%20Sample.png)

### Custom Spreadsheets

The OMG is only dependent on the `FullName` header being present for correct functionality. You can utilise any spreadsheet as long as the `FullName` header is present and correctly matches the hierachy. Additional headers can be dropped in/out without interferring.

![FullName Column](assets/FullName%20Column.png)

### XML Metadata - Basic Templates

DC, MODS, GPDR, and EAD templates are supported out of the box. This works in the same way as XIP data and column headers are 'drop-in/drop-out'

XML Column Headers do need to written as: `ns:tagname`. `ns` being the xmls namespace and tagname the tagname.

![XML Headers](assets/XML%20Headers.png)

There are two ways to enter the column header: `exactly` or `flatly`(There are probably better words to describe this). When entering in `exact`, you must enter in all parents of the tag seperated by `/`. Flatly only requires the end tag be present. In both cases, case-sensistivity matters. `exact` is the default method.

```
# Exactly:
mods:recordInfo/mods:recordIdentifier

# Flatly:
mods:recordIdentifier
```

In both cases these match to the same `recordIdentifier` field. 

While using the `flatly` method is easier, if non-unique tags are present, such as in `mods:note`, this will match to the first match, which might not be it's intended destination. For complex XMLs I'd recommend sticking with the `exact` method.

Once you have added in your headers and data you can run like so:

```bash
# Run with flat method
opex_generate -i "/path/to/your/spreadsheet.xlsx" "/path/to/root/directory" -m flat

# Run with exact method
opex_generate -i "/path/to/your/spreadsheet.xlsx" "/path/to/root/directory" -m exact
```

### XML Metadata - Quick Notes

- You can utilise `--print-xmls` to display the correct header names of your XMLs to the console.
- Or you can utilise `--convert-xmls` to automatically conver them into spreadsheets with the right headers.
- I've included samples for DC, MODS, GDPR and EAD templates, with the `exact` headers [here](https://github.com/CPJPRINCE/opex_manifest_generator/tree/master/samples/spreads). 

- When you have multiple non-unique tags, such as `mods:note`, you will need add an index in square brackets `[0]` like so: `mods:note[1] mods:notes[2] ...` The number should correspond to the order they appear in the XML tree.
- When using the -m option if you have headers present a 'blank XML' for the corresponding headers will be added to the Opex, regardless of if data is filled out.

### XML Metadata Templates - Custom Templates

Any custom XML template, that is functioning will work! All XML's in the assigned `metadata` (not to be confused with `meta`) directory are checked when enabling the `-m` option.

By default this location is on the install path of python. To use your own folder, you can use the `-mdir` option to point the source of XMLs to a specific folder and then place your Template XMLs in this folder. You can also utilise `--print-xmls` and `--convert-xmls` in conjunction with this.

```bash
# Will use /path/to/metadata as source for files.
opex_generate /path/to/root -mdir /path/to/metadata

```

### Input Hashes

You add in the columns headers `Hash` and `Algorithm` with hash data. When utilising the `-fx` option in combination with `-i`, the program will read the hashes from the spreadsheet instead of generating them.

![Hash Screenshot](assets/Hash%20Headers.png)

### Removals & Ignore

You can set the column header `Removals`, and when the cell is marked TRUE, the specified folder/file will be deleted. to activate use the option `-rm` and confirm when prompted. A text log will be generated for the deleted files to `meta`.

Similarly, you can set the column header `Ignore` and when the cell is marked `TRUE` it will skip the generation of an Opex for the specified file / folder.
 
### Options File

You can utilise your own `options.properties` file to change the default column headers, and some other settings. 
Like so 
```bash
opex_generate --options-file path/to/options.properties /path/to/root
```
The default options look like:

```[options]

INDEX_FIELD = FullName
TITLE_FIELD = Title
DESCRIPTION_FIELD = Description
SECURITY_FIELD = Security
IDENTIFIER_FIELD = Identifier
IDENTIFIER_DEFAULT = code
REMOVAL_FIELD = Removals
IGNORE_FIELD = Ignore
SOURCEID_FIELD = SourceID
HASH_FIELD = Hash
ALGORITHM_FIELD = Algorithm

ACCREF_CODE = accref
ARCREF_FIELD = Archive_Reference
ACCREF_FIELD = Accession_Reference

METAFOLDER = meta
FIXITY_SUFFIX = _Fixity
REMOVALS_SUFFIX = _Removals
GENERIC_DEFAULT_SECURITY = open
```

#### Custom Spreadsheets - Quick Note

You technically don't have to utilise the AutoRef tool at all. Any old spreadsheet will do!

The only requirement to use the input override, is the presence of the `FullName` column. With an accurate list of paths.


## Full Options

The below covers the full range of options. Use `-h` option to show this dialong.

```
<!-- argparse_to_md:opex_manifest_generator:create_parser -->
<!-- argparse_to_md_end -->

```

## Future Developments

- ~~Customisable Filtering~~ *Added!*
- ~~Adjust Accession so the different modes can utilised from Opex.~~ *Added!*
- ~~Add SourceID as option for use with Auto Ref Spreadsheets.~~ *Added!*
- ~~Allow for multiple Identifier's to be added with Auto Ref Spreadsheets. Currently only 1 or 2 identifiers can be added at a time, under "Archive_Reference" or "Accession_Reference". These are also tied to be either "code" or "accref". An Option needs to be added to allow custom setting of identifier...~~ *Added!*
- ~~Add an option / make it a default for Metadata XML's to be located in a specified directory rather than in the package.~~ *Added!*
- Zipping to conform to PAX - Last on the check list; it technically does...
- In theory, this tool should be compatible with any system that makes use of the OPEX standard... But in theory Communism works, in theory...

## Troubleshooting

- On Windows ensure that when you enter the root folder it does not end in a `\`. This is slightly annoying as it adds it by default when tabbing.
- In the examples above I've used linux paths. If your on Windows don't forgot to change these to backslashes `\`
- There are a number of helpers when entering options: use SHA1 instead of SHA-1, c for catalog, acc for accession.

## Developers

For Developers you can also use the tool as a module
```python
from opex_manifest_generator import OpexManifestGenerator

omg = OpexManifestGenerator(root="/my/directory/path", algorithm = "SHA-256").main()

```

## Contributing

I welcome further contributions and feedback! If there any issues please raise them [here](https://github.com/CPJPRINCE/opex_manifest_generator/issues)
