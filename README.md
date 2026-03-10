# Opex Manifest Generator Tool

[![Supported Versions](https://img.shields.io/pypi/pyversions/opex_manifest_generator.svg)](https://pypi.org/project/opex_manifest_generator)
[![CodeQL](https://github.com/CPJPRINCE/opex_manifest_generator/actions/workflows/codeql.yml/badge.svg)](https://github.com/CPJPRINCE/opex_manifest_generator/actions/workflows/codeql.yml)

A small Python programme for generating opex manifest files. Used for safe transfer of files and metadata ingests into opex compatible systems (Preservica). The program will recurse through a given hierarchy and generate manifests for all folders/files (depending on option).

## Table of Contents

- [Quick Start](#quick-start)
- [Version & Package Info](#version--package-info)
- [Recent Changes](#recent-changes)
- [Why Use This Tool?](#why-use-this-tool)
- [Additional Features](#additional-features)
- [Expected Output](#expected-output)
- [Advanced Usage](#advanced-usage)
  - [Fixity Generation](#fixity-generation)
  - [Continuous Operation](#continuous-operation)
  - [Clearing Opex Files](#clearing-opex-files)
  - [Zipping](#zipping)
  - [Removing Empty Directories](#removing-empty-directories)
  - [Hidden Directories](#hidden-directories)
- [Auto Reference Usage](#auto-reference-usage)
- [Input Option](#input-option)
  - [XIP Metadata - Title, Description and Security Tags](#xip-metadata---title-description-and-security-tags)
  - [XIP Metadata - Identifiers](#xip-metadata---identifiers)
  - [Samples](#samples)
  - [Custom Spreadsheets](#custom-spreadsheets)
  - [XML Metadata - Basic Templates](#xml-metadata---basic-templates)
  - [XML Metadata - Quick Notes](#xml-metadata---quick-notes)
  - [XML Metadata Templates - Custom Templates](#xml-metadata-templates---custom-templates)
  - [Input Hashes](#input-hashes)
  - [Removals & Ignore](#removals--ignore)
  - [Options File](#options-file)
- [Full Options](#full-options)
- [Future Developments](#future-developments)
- [Troubleshooting](#troubleshooting)
- [Developers](#developers)
  - [opexLib Developer Guide](docs/opexLib.md)
- [Contributing](#contributing)

## Quick Start

### Option 1: Using pip (Recommended for Python users / long-term use)
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

# Linux/macOS
./opex_generate /path/to/root -fx SHA-256
```

On Windows you can also use the install.cmd with admin privileges to install and run the command without navigating to the bin folder (see Option 1 for use).

## Version & Package Info

**Python Version:**

Python Version 3.10+ is recommended. Earlier versions may work but are not tested.

**Additional Packages:**
- auto_reference_generator (required)
- pandas (required)
- tqdm (required)
- openpyxl (required)
- lxml (required)
- odfpy (optional - ods export)

To install using Python:

```bash
pip install pandas openpyxl odfpy lxml tqdm
```

If using Python, ensure it is added to your Environment variables.

## Recent Changes

- Improved PAX support and naming consistency: use `-pax` / `--pax-flag` for PAX-aware processing.
- Added `--max-workers` to control fixity threading (`0` uses all available CPU cores).
- Default output is now set to a Progress Bar, use `-v` to run the old way.
- Added logging controls: `--log-level`, `--log-file`, and `-v` (verbose stream output, progress bar off).
- Improved CLI behavior and validation around conflicting options (`--input` with `--autoref`, and `-rm` without `--input`).
- Improved Windows root-path handling: trailing `\` is normalized automatically.
- opexLib Added!

### Output

Will generate an `.opex` manifest file for each of your directories. This manifest will contain a list of all files/folders in that folder.

File manifests may also be generated if using additional options. When file manifests are active, the folder manifest automatically accounts for additional opexes.

## Why Use This Tool?

This tool was primarily intended to allow users to undertake larger uploads safely using bulk ingests.

It functions with all methods of Opex Ingests. For Preservica this includes:
- **Opex Incremental Workflow**
- **PUT Tool**
- **Starter Drag 'n' Drop**
- **Manual Ingest**

## Additional Features

- **Hash generation (MD5, SHA1, SHA256, SHA512) - for additional security checks.**
- **Generate multiple algorithm hashes**
- **Generate hashes for PAX files**
- **Continuous Operation - allowing closure/crashes of the program to occur and then picking up where you left off**
- **Opex removal**
- **Zip functionality**

The Program also includes the [Auto Reference Generator](https://github.com/CPJPRINCE/auto_reference_generator), built in allowing for:
- **Automated Reference generation straight to Opex files**
- **Clearing and logging empty folders**
- **A Removal mode to delete and log files/folders**
- **Sorting - by alphabetically or 'folders first'**
- **Keyword assignment - replacing numerals with specified keywords (initials, first letter, JSON map)**
- **And more! See the github page for details**

A key function built on ARG is the `--input` mode, allowing you to use a spreadsheet to assign XIP/XML metadata to your files and folders. Currently this allows:
- **Assignment of XIP title, description, and security status fields**
- **Assignment of standard and custom XML metadata templates**
- **'Drop-in/drop-out' operations, so only needed columns are added**

All these options can be combined to create extensive and robust Opex files for file transfers.

## Expected Output

At a basic level, using `opex_generate`, the program will only generate folder manifests.

![Opex in Folder](assets/Opex%20Folder.png)

Which will contain a simple list of files/folders in that folder:

![Opex Folder Manifest](assets/Opex%20Manifest.png)

When using an option that affects files, you will generate individual Opexes for files:

![Opex Files](assets/Opex%20Files.png)

These will contain the data about the files (which will vary based on selected options).

![Opex File Manifest](assets/Opex%20File%20Manifest.png)

When individual opex files are generated, the folder manifest will include these as **metadata** files.

![Opex Folder Manifest](assets/Opex%20Manifest%20with%20files.png)

## Advanced Usage

**Important Notes**

- The term `meta` is hard-coded to always be ignored. This is case-sensitive.
- A meta folder will only be created using `--fixity`, `--remove-empty` or `-rm` options. You can disable this using the `--disable-meta-dir` option or `-o` option to relocate it.

### Fixity Generation

```bash
# Generate with SHA-256 Hash
opex_generate "/path/to/folder" -fx SHA-256

# Generate with MD5 and SHA-256 Hash
opex_generate "/path/to/folder" -fx MD5 SHA-256

# Generate with SHA-1 for PAX-aware processing (-pax / --pax-flag)
opex_generate "/path/to/paxfolders" -fx SHA-1 --pax-flag

# Generate with MD5 and SHA1 for PAX
opex_generate "/path/to/paxfolders" -fx MD5 SHA-1

# Using -fx without specifying will default to SHA-1
```

### Continuous Operation

The program won't override an existing opex when generating a new Opex. If an opex is present it will state:

```
Avoiding override, Opex exists at: /path/to/opex
```

This allows for continuous operation, as long generations - particularly if you have large files - can be cancelled at any point, then picked up later. To halt the program, simply press `Ctrl + C` in the console.

There is no way to force an override. If you need to rerun a generation, use the `-clr` option.

### Clearing Opex Files

```bash
# Will clear existing opexes recursively then end
opex_generate /path/to/folder -clr

# If other options are enabled will clear and rerun generation
opex_generate /path/to/folder -clr -fx SHA1
```

### Zipping

```bash
# Will zip opex and file into a zip file
opex_generate /path/to/folder -fx SHA-1 -z

# Will zip opex and file and remove the original files
opex_generate /path/to/folder -fx SHA-1 -z --remove-zipped-files
```

**Use zipping with caution, repeated use can get quite messy fast.**

### Removing Empty Directories

```bash
# Remove and generate a text log to the 'meta' folder of removed directories
opex_generate /path/to/folder --remove-empty

# You will be asked to give confirmation that you want to proceed
```

### Hidden Directories

```bash
# By default hidden directories/files are not included. Adding --hidden will include hidden files
opex_generate /path/to/folder --hidden
```

## Auto Reference Usage

As mentioned, built into the OMG is the Auto Reference Generator, allowing archival references to be assigned directly to Opexes. By default, codes generated using this method are hard-coded to the identifier `code`.

If you want to understand what these References will look like, please see [here](https://github.com/CPJPRINCE/auto_reference_generator?tab=readme-ov-file#structure-of-references).

```bash
# Will generate a reference code for the hierarchy with the prefix "ARCH"
opex_generate /path/to/folder -r catalog -p ARCH

# Will generate a reference code with prefix "ARCH-1-2-3", suffix "Z" and delimiter "-"
opex_generate /path/to/folder -r catalog -p "ARCH-1-2-3" -s Z -dlm "-"

# Will generate a reference code without a prefix - this will only be the numerals
opex_generate /path/to/folder -r catalog

# Will generate an accession code / 'running number' with the prefix "2026-X"
opex_generate /path/to/folder -r accession -p 2026-X

# Will fill in title, description and security tag data based upon file and folder names and sets to the default security tag 'open'
opex_generate -r generic /path/to/folder
```

## Input Option

This program also supports using a spreadsheet as an `input`. This allows the data to be prefilled in and set on ingest. The following XIP Metadata fields can be set:

- Title
- Description
- Security Status
- Identifiers
- SourceID

XML metadata data is also supported for both default and custom XMLs.

### XIP Metadata - Title, Description and Security Tags

To use an input override, you first need to create a spreadsheet folder listing. It's not necessary, but for convenience, I'd recommend using the `auto_ref` tool. Like so:

```bash
auto_ref -p "ARCH" /path/to/root
```

The column headers are all 'drop-in/drop-out'. Simply add new columns for the data you'd like to edit. The column headers are case-sensitive and have to match exactly. For reference, these are the following:

```
Title
Description
Security
```

These fields would then be filled in with the relevant data. **For Security Tags**, ensure they are an exact match to the tag on your system, which are also case-sensitive.

![ScreenshotXIPColumns](assets/Column%20Headers.png)

Once the cells are filled in with the respective data, run a generation using the `-i` option and input the full path to your spreadsheet. Ensure that the `/path/to/root` is the same root as you generated the spreadsheet for.

```bash
# Will use the 'spreadsheet.xlsx' as an input
opex_generate -i /path/to/your/spreadsheet.xlsx /path/to/root

# These can still be combined with the above options
opex_generate -i /path/to/your/spreadsheet.xlsx -fx SHA-1 /path/to/root
```

**To Note:**
- If you leave blank cells, it will simply skip those details.
- If you rearrange the hierarchy after your spreadsheet generation, you may receive errors or mismatches due to folders/files being incorrectly looked up. In these cases, you may need to regenerate your list and migrate the data to it.
- Assignment is not specific to Folders/Files.

### XIP Metadata - Identifiers

Identifiers are also supported and can be added to the column header following this convention:

```
Identifier:Key
```

The `Key` will determine the identifier name and the cells will contain the value.

![Identifier Screenshot](assets/Identifiers%20Headers.png)

You can also use the following column headers:

```
# Defaults to 'code' key
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

The OMG is only dependent on the `FullName` header being present for correct functionality. You can use any spreadsheet as long as the `FullName` header is present and correctly matches the hierarchy. Additional headers can be dropped in/out without interfering.

![FullName Column](assets/FullName%20Column.png)

### XML Metadata - Basic Templates

DC, MODS, GDPR, and EAD templates are supported out of the box. The column headers are also 'drop-in/drop-out'.

XML Column Headers need to be written as: `ns:tagname` with `ns` being the XML's namespace and `tagname` the tag name.

![XML Headers](assets/XML%20Headers.png)

There are two ways to enter the column header: `exactly` or `flatly` (also known as 'nested' vs 'flat' mode). When entering `exact`, you must enter all parents of the tag separated by `/`. Flatly only requires the end tag to be present. In both cases, case-sensitivity matters. `exact` is the default method.

If you enter a non-matching header (such as a misspelling), it won't match to the field.

```
# Exactly:
mods:recordInfo/mods:recordIdentifier

# Flatly:
mods:recordIdentifier
```

In both cases, these match to the same `recordIdentifier` field.

While using the `flatly` method is easier, if non-unique tags are present, such as `mods:note`, it will match to the first occurrence in the XML, which might not be its intended destination. For complex XMLs, I'd recommend sticking with the `exact` method.

Once you have added your headers and data, you can run like so:

```bash
# Run with flat method
opex_generate -i "/path/to/your/spreadsheet.xlsx" "/path/to/root/dir" -m flat

# Run with exact method
opex_generate -i "/path/to/your/spreadsheet.xlsx" "/path/to/root/dir" -m exact
```

### XML Metadata - Quick Notes

- You can use `--print-xmls` and `--convert-xmls` to return XMLs to the console or generate spreadsheet templates.

```bash
# You can use `--print-xmls` to display the correct header names of your XMLs to the console
opex_generate /path/to/root --print-xmls

# You can also use `--convert-xmls` to create spreadsheets with all the right headers. Will be output to the cwd of your terminal
opex_generate /path/to/root --convert-xmls
```

- When you have multiple non-unique tags, such as `mods:note`, you will need to add an index in square brackets `[0]` like so: `mods:note[1] mods:note[2] ...` The number should correspond to the order they appear in the XML tree.
- If you use `-m` option without adding any data, a blank XML template will be added to the opex.
- I've also included sample spreadsheets for DC, MODS, GDPR and EAD templates with the `exact` headers [here](https://github.com/CPJPRINCE/opex_manifest_generator/tree/master/samples/spreads).

### XML Metadata Templates - Custom Templates

Any custom XML template that is functioning in your system will work!

To use custom XMLs, place your XMLs in a specific folder, then use the `-mdir` option with `/path/to/metadata`. You can also use `--print-xmls` and `--convert-xmls` in conjunction with this to generate.

```bash
# Will use /path/to/metadata as source for files
opex_generate /path/to/root -mdir /path/to/metadata
```

### Input Hashes

~~If you use the column headers `Hash` and `Algorithm` with hash data, when using the `-fx` option in combination with `-i`, the program will read the hashes from the spreadsheet instead of generating them.~~ *Replaced in v1.3.8*

Using the columns header `Hash:{alg}` with hash data in the cell in conjunction with `-fx` and `-i` options the program will read the hashes from the spreadsheet. This allows for multiple Hashes to be added.

![Hash Screenshot](assets/Hash%20Headers.png)

**Does not currently support multiple hashes**

### Removals & Ignore

You can set the column header `Removals`, and when the cell is marked TRUE, the specified folder/file will be deleted. To activate, use the option `-rm` and confirm when prompted. A text log will be generated for the deleted files in the `meta` folder.

Similarly, you can set the column header `Ignore`, and when the cell is marked `TRUE` it will skip the generation of an Opex for the specified file/folder.

### Options File

You can use your own `options.properties` file to change the default column headers and some other defaults. Like so:

```bash
opex_generate --options-file path/to/options.properties /path/to/root
```

The default options look like:

```
[options]

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

## Full Options

The below covers the full range of options. Use `-h` option to show this dialog.

<!-- argparse_to_md:opex_manifest_generator:create_parser -->
Usage:
```
Opex Manifest Generator [-h] [--version] [-fx [{SHA-1,MD5,SHA-256,SHA-512} ...]] [-pax]
                                   [--max-workers [MAX_WORKERS]] [-z] [--remove-zipped-files]
                                   [--remove-empty] [--hidden] [-clr] [-opt OPTIONS_FILE]
                                   [-i [INPUT]] [-mdir [METADATA_DIR]] [-m [{exact,flat}]] [-rm]
                                   [--print-xmls] [--convert-xmls]
                                   [--autoref-options AUTOREF_OPTIONS] [--column-sensitivity]
                                   [-r {catalog,accession,both,generic,catalog-generic,accession-generic,both-generic}]
                                   [-p PREFIX [PREFIX ...]] [-s [SUFFIX]]
                                   [--suffix-option {file,directory,both}]
                                   [--accession-mode [{file,directory,both}]] [-str [START_REF]]
                                   [-dlm [DELIMITER]] [--sort-by [{folders_first,alphabetical}]]
                                   [-key [KEYWORDS ...]]
                                   [-keym [{initialise,firstletters,from_json}]]
                                   [--keywords-case-sensitivity] [--keywords-retain-order]
                                   [--keywords-abbreviation-number KEYWORDS_ABBREVIATION_NUMBER [KEYWORDS_ABBREVIATION_NUMBER ...]]
                                   [--log-level [{DEBUG,INFO,WARNING,ERROR}]]
                                   [--log-file [LOG_FILE]] [-v] [-o [OUTPUT]] [--disable-meta-dir]
                                   [--disable-all-exports] [--disable-fixity-export]
                                   [--disable-empty-export] [--disable-removal-export] [-ex]
                                   [-fmt {xlsx,csv,json,ods,xml}]
                                   [root]
```
OPEX Manifest Generator for Preservica Uploads

Positional arguments:
- `root`: The root path to generate Opexes for, will recursively traverse all sub-directories.
                        Generates an Opex for each folder & (depending on options) file in the directory tree.

Optional arguments:
- `--version`: show program's version number and exit

Opex Options:
  Options that control the generation of Opex Manifests

- `-fx [{SHA-1`, `MD5`, `SHA-256`, `SHA-512} ...]`, `--fixity [{SHA-1`, `MD5`, `SHA-256`, `SHA-512} ...]`: Generates a hash for each file and adds it to the opex.
Can select one or more algorithms to utilise: {-fx MD5 SHA-1}
If no algorithm is specified defaults to SHA-1.

- `-pax`, `--pax-flag`: Enables recognition of PAX Folders and use of PAX fixity generation, in line with Preservica's model.
                        "Files / folders ending in .pax or .pax.zip will have individual files in folder / zip added to Opex.
- `--max-workers [MAX_WORKERS]`: Sets the number of Threads to use for Fixity Generation.
- `-z`, `--zip`: Set to zip files
- `--remove-zipped-files`: Set to remove the original files that have been zipped
- `--remove-empty`: Remove and log empty directories from root. Log will be exported to 'meta' / output folder.
- `--hidden`: Set whether to include hidden files and folders
- `-clr`, `--clear-opex`: Clears existing opex files from a directory. If set with no further options will only clear opexes;
                        if multiple options are set will clear opexes and then run the program
- `-opt OPTIONS_FILE`, `--options-file OPTIONS_FILE`: Specify a custom Options file, changing the set presets for column headers (Title,Description,etc)

Input Override Options:
  Options that control the Input Override features

- `-i [INPUT]`, `--input [INPUT]`: Set to utilise a CSV / XLSX spreadsheet to import data from
- `-mdir [METADATA_DIR]`, `--metadata-dir [METADATA_DIR]`: Specify the metadata directory to pull XML files from
- `-m [{exact`, `flat}]`, `--metadata [{exact`, `flat}]`: Set whether to include xml metadata fields in the generation of the Opex
- `-rm`, `--remove`: Set whether to enable removals of files and folders from a directory. ***Currently in testing
- `--print-xmls`: Prints the elements from your xmls to the consoles
- `--convert-xmls`: Convert XMLs templates files in mdir to spreadsheets/csv files
- `--autoref-options AUTOREF_OPTIONS`: Specify a custom Auto Reference Options file, changing the set presets for Input Override / Auto Reference Generator
- `--column-sensitivity`: Set whether to make column header matching for input spreadsheets case sensitive, default is sensitive

Auto Reference Generator Options:
  Options that control the Auto Reference Generator features

- `-r {catalog`, `accession`, `both`, `generic`, `catalog-generic`, `accession-generic`, `both-generic}`, `--autoref {catalog`, `accession`, `both`, `generic`, `catalog-generic`, `accession-generic`, `both-generic}`: Toggles whether to utilise the auto_reference_generator
                        to generate an on the fly Reference listing.

                        There are several options, {catalog} will generate
                        a Archival Reference following an ISAD(G) structure.

                        {accession} will create a running number of files.
                        {both} will do both at the same time!
                        {generic} will populate the title and description fields with the folder/file's name,
                        if used in conjunction with one of the above options:
                        {generic-catalog,generic-accession, generic-both} it will do both simultaneously.
                        
- `-p PREFIX [PREFIX ...]`, `--prefix PREFIX [PREFIX ...]`: Assign a prefix when utilising the --autoref option. Prefix will append any text before all generated text.
                        When utilising the {both} option fill in like: [catalog-prefix, accession-prefix] without square brackets.
                        
- `-s [SUFFIX]`, `--suffix [SUFFIX]`: Assign a suffix when utilising the --autoref option. Suffix will append any text after all generated text.
- `--suffix-option {file`, `directory`, `both}`: Set whether to apply the suffix to files, folders or both when utilising the --autoref option.
- `--accession-mode [{file`, `directory`, `both}]`: Set the mode when utilising the Accession option in autoref.
                        file - only adds on files, folder - only adds on folders, both - adds on files and folders
- `-str [START_REF]`, `--start-ref [START_REF]`: Set a custom Starting reference for the Auto Reference Generator. The generated reference will
- `-dlm [DELIMITER]`, `--delimiter [DELIMITER]`: Set a custom delimiter for generated references, default is '/'
- `--sort-by [{folders_first`, `alphabetical}]`: Set the sorting method, 'folders_first' sorts folders first then files alphabetically; 'alphabetically' sorts alphabetically (ignoring folder distinction)

Keyword Options:
  Options that control the Keyword features for Auto Reference Generation

- `-key [KEYWORDS ...]`, `--keywords [KEYWORDS ...]`: Set to replace reference numbers with given Keywords for folders (only Folders atm). Can be a list of keywords or a JSON file mapping folder names to keywords.
- `-keym [{initialise`, `firstletters`, `from_json}]`, `--keywords-mode [{initialise`, `firstletters`, `from_json}]`: Set to alternate keyword mode: 'initialise' will use initials of words; 'firstletters' will use the first letters of the string; 'from_json' will use a JSON file mapping names to keywords
- `--keywords-case-sensitivity`: Set to change case keyword matching sensitivity. By default keyword matching is insensitive
- `--keywords-retain-order`: Set when using keywords to continue reference numbering. If not used keywords don't 'count' to reference numbering, e.g. if using initials 'Project Alpha' -> 'PA' then the next folder/file will still be '001' not '003'
- `--keywords-abbreviation-number KEYWORDS_ABBREVIATION_NUMBER [KEYWORDS_ABBREVIATION_NUMBER ...]`: Set to set the number of letters to abbreviate for 'firstletters' mode, does not impact 'initialise' mode.

Export Options:
  Options that control various export features

- `--log-level [{DEBUG`, `INFO`, `WARNING`, `ERROR}]`: Set the logging level (default: INFO)
- `--log-file [LOG_FILE]`: Optional path to write logs to a file (default: stdout)
- `-v`, `--verbose`: Set whether to output log stream instead of progress bar during processing, default is True (will not output log stream, will show progress bar)Enable to display log stream but disable progress bar
- `-o [OUTPUT]`, `--output [OUTPUT]`: Sets the output of the meta folder to send any generated files (Remove Empty, Fixity List, Autoref Export) to. Can be used in conjunction with --disable-meta-dir to set output location without generating meta directory.
- `--disable-meta-dir`: Set whether to disable the creation of a 'meta' directory for generated files,
                        default behaviour is to always generate this directory
- `--disable-all-exports`: Set to prevent all exports (Fixity, Removal, Empty) from being created in the meta directory.
- `--disable-fixity-export`: Set whether to export the generated fixity list to a text file in the meta directory.
                        Enabled by default, disable with this flag.
- `--disable-empty-export`: Set whether to export the generated empty list to a text file in the meta directory.
                        Enabled by default, disable with this flag.
- `--disable-removal-export`: Set whether to export the generated removals list to a text file in the meta directory.
                        Enabled by default, disable with this flag.
- `-ex`, `--export-autoref`: Set whether to export the generated references to an AutoRef spreadsheet
- `-fmt {xlsx`, `csv`, `json`, `ods`, `xml}`, `--output-format {xlsx`, `csv`, `json`, `ods`, `xml}`: Set whether to export AutoRef Spreadsheet to: xlsx, csv, json, ods or xml format
<!-- argparse_to_md_end -->

## Future Developments

- ~~Customizable Filtering~~ *Added!*
- ~~Adjust Accession so the different modes can use from Opex~~ *Added!*
- ~~Add SourceID as option for use with Auto Ref Spreadsheets~~ *Added!*
- ~~Allow for multiple Identifiers to be added with Auto Ref Spreadsheets. Currently only 1 or 2 identifiers can be added at a time, under "Archive_Reference" or "Accession_Reference". These are also tied to be either "code" or "accref". An Option needs to be added to allow custom setting of identifier~~ *Added!*
- ~~Add an option/make it a default for Metadata XMLs to be located in a specified directory rather than in the package~~ *Added!*
- Zipping to conform to PAX - Last on the check list; it technically does...
- In theory, this tool should be compatible with any system that uses the OPEX standard... But in theory Communism works, in theory...

## Troubleshooting

- On Windows, ensure that when you enter the root folder it does not end in a `\`. This is slightly annoying as it adds it by default when tabbing.
- In the examples above, I've used Linux paths. If you're on Windows, don't forget to change these to backslashes `\`
- There are a number of helpers when entering options: use SHA1 instead of SHA-1, c for catalog, acc for accession.

## Developers

For Developers, you can also use the tool as a module:

```python
from opex_manifest_generator import OpexManifestGenerator

omg = OpexManifestGenerator(root="/path/to/root", fixity=["SHA-256"]).main()
```

`opexLib` a low-level reader/writer documentation is available here:

- [opexLib Developer Guide](docs/opexLib.md)

## Contributing

I welcome further contributions and feedback! If there are any issues please raise them [here](https://github.com/CPJPRINCE/opex_manifest_generator/issues)
