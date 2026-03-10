# opexLib Developer Guide

`opexLib` provides lower-level classes for reading and writing OPEX XML manifests outside of the high-level CLI flow.

This page covers:
- Reader classes for existing `.opex` files
- Writer classes for generating new folder/file manifests
- PAX-aware fixity handling
- Common usage patterns

## Module Location

```python
from opex_manifest_generator.opexLib import (
    OpexDirReader,
    OpexFileReader,
    OpexDirWriter,
    OpexFileWriter,
)
```

## Readers

### `OpexDirReader`

Reads a directory-level `.opex` manifest and exposes parsed content.

Common methods:
- `get_manifest()`
- `get_folders()`
- `get_files()`
- `get_files_dict()`
- `get_title()`
- `get_description()`
- `get_security_descriptor()`
- `get_identifiers()`
- `get_sourceid()`
- `get_descriptive_metadata()`
- `verify_opex_version(expected_version="1.2")`

Example:

```python
from opex_manifest_generator.opexLib import OpexDirReader

reader = OpexDirReader("/path/to/folder/folder.opex")
print(reader.get_title())
print(reader.get_manifest())
```

### `OpexFileReader`

Reads a file-level `.opex` manifest.

Common methods:
- `get_fixities()`
- `get_title()`
- `get_description()`
- `get_security_descriptor()`
- `get_identifiers()`
- `get_sourceid()`
- `get_descriptive_metadata()`
- `verify_opex_version(expected_version="1.2")`

Example:

```python
from opex_manifest_generator.opexLib import OpexFileReader

reader = OpexFileReader("/path/to/file.ext.opex")
print(reader.get_fixities())
```

## Writers

### `OpexDirWriter`

Generates directory manifests and can include:
- Folder and file entries
- Metadata file entries (`.opex` inside the folder)
- Optional title/description/security/identifiers/source ID
- Optional descriptive XML metadata
- Optional PAX folder fixities

Example:

```python
from opex_manifest_generator.opexLib import OpexDirWriter

writer = OpexDirWriter(
    folder_path="/path/to/folder",
    title="Collection Folder",
    description="Top-level transfer folder",
    security_tag="open",
    identifiers={"code": "ARCH/001"},
)

# Write to /path/to/folder/folder.opex by default
writer.write_opex_manifest()
```

### `OpexFileWriter`

Generates file manifests and can include:
- Optional generated fixities (`generate_fixity=[...]`)
- Optional supplied fixities (`fixity=[{"type":..., "value":...}]`)
- Optional title/description/security/identifiers/source ID
- Optional descriptive XML metadata
- Zip helper (`zip_opex_file`) to package file + `.opex`

Example:

```python
from opex_manifest_generator.opexLib import OpexFileWriter

writer = OpexFileWriter(
    file_path="/path/to/file.ext",
    title="File Title",
    generate_fixity=["SHA-256"],
    identifiers={"code": "ARCH/001/01"},
)

writer.write_opex_file()
```

## PAX Notes

`opexLib` supports PAX-specific fixity behavior:
- `OpexDirWriter(..., pax_flag=True)` with a folder ending in `.pax` can produce per-file fixities in the transfer.
- `OpexFileWriter(..., pax_flag=True, generate_fixity=[...])` with `.pax` or `.pax.zip` can produce path-based fixities for archive contents.

## Path Handling

The reader/writer classes normalize Windows extended-length path prefixes (`\\?\`) where needed.

## Error Handling

Common exceptions include:
- `FileNotFoundError` when input files do not exist
- `lxml.etree.ParseError` when malformed XML is provided
- `ValueError` for invalid writer options (for example invalid `filter_flag`)

## Quick Reference

- Directory read: `OpexDirReader`
- File read: `OpexFileReader`
- Directory write: `OpexDirWriter`
- File write: `OpexFileWriter`

For end-to-end recursive generation workflows, continue to use the CLI (`opex_generate`) or `OpexManifestGenerator`.
