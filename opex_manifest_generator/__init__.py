"""
opex_manifest_generator package definitions

Author: Christopher Prince
license: Apache License 2.0"
"""

from opex_manifest_generator.opexManifest import OpexManifestGenerator
from opex_manifest_generator.opexLib import OpexDirReader, OpexDirWriter, OpexFileReader, OpexFileWriter
from opex_manifest_generator.hash import HashGenerator
from opex_manifest_generator.common import remove_tree,win_256_check,filter_win_hidden,win_path_delimiter,check_nan,check_bool,running_time
from opex_manifest_generator.cli import create_parser,run_cli
from importlib import metadata

__author__ = "Christopher Prince (c.pj.prince@gmail.com)"
__license__ = "Apache License Version 2.0"
try:
	__version__ = metadata.version("opex_manifest_generator")
except metadata.PackageNotFoundError:
	__version__ = "0.0.0"
