Opex Manifest Generator - Portable Edition
===========================================

This is a standalone, portable distribution of Opex Manifest Generator.

Installation
============

For Windows:
1. Extract the ZIP file to your desired location
2. Navigate to the opex_manifest_generator folder
3. Run install.cmd (right-click and select "Run as Administrator")
4. Follow the on-screen instructions

After installation, you can use opex_manifest_generator from any command prompt.

Usage
=====

Basic usage:
  opex_generate /path/to/root [options]

For full options:
  opex_generate --help

Examples
========

Generate Opex manifests with fixity:
  opex_generate C:\MyFiles -fx SHA-256

Generate with auto-reference (catalog):
  opex_generate C:\MyFiles -r catalog -p ARCH

Generate with CSV input and metadata:
  opex_generate C:\MyFiles -i metadata.xlsx -m exact

Zip files and generate fixity:
  opex_generate C:\MyFiles -z -fx MD5 SHA-1

Uninstallation
==============

To uninstall from Windows:
1. Navigate to the opex_manifest_generator folder
2. Run uninstall.cmd (right-click and select "Run as Administrator")
3. Follow the on-screen instructions

Support
=======

For more information, visit the project repository or consult the documentation.

This executable was built using Nuitka and includes all necessary dependencies.
No additional Python installation is required.
