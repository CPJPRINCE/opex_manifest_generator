"""
opex_manifest_generator package definitions

Author: Christopher Prince
license: Apache License 2.0"
"""

from .opex_manifest import OpexManifestGenerator,OpexDir,OpexFile
from .hash import HashGenerator
from .common import *
from .cli import create_parser,run_cli
from importlib import metadata

__author__ = "Christopher Prince (c.pj.prince@gmail.com)"
__license__ = "Apache License Version 2.0"
try:
	__version__ = metadata.version("opex_manifest_generator")
except metadata.PackageNotFoundError:
	__version__ = "0.0.0"
