Opex Manifest Generator - Portable Distribution
================================================

FOLDER STRUCTURE:
  opex_generate/
  ├─ bin/
  │  ├─ opex_generate.exe      # Nuitka onefile executable
  │  └─ opex_generate.cmd      # Command wrapper
  ├─ README.txt
  ├─ install.cmd
  └─ uninstall.cmd

PORTABLE USE:
  Run directly from this folder without installation:
  
    bin\opex_generate.cmd [options]
  
  Example:
    bin\opex_generate.cmd --help
    bin\opex_generate.cmd C:\path\to\files -fx SHA-256

INSTALLATION:
  To install to your system, run:
  
    install.cmd
  
  This will copy files to:
    - C:\Program Files\Opex Generate (if run as Administrator)
    - %LOCALAPPDATA%\Opex Generate (if run as regular user)

UNINSTALLATION:
  To remove the installed version, run:
  
    uninstall.cmd
  
  Note: This only removes installed files, not the portable folder.

For full documentation and options, visit:
  https://github.com/cprincetn/opex_manifest_generator
