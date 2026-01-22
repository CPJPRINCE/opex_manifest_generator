import os
import zipfile
from lxml import etree as ET
import pytest
import pandas as pd

from opex_manifest_generator.opex_manifest import OpexManifestGenerator, OpexDir


def test_init_generate_descriptive_metadata(tmp_path):
    md_dir = tmp_path / "meta"
    md_dir.mkdir()
    xml = '<?xml version="1.0"?><root xmlns="urn:test"><a>1</a><b>2</b></root>'
    (md_dir / "sample.xml").write_text(xml)

    omg = OpexManifestGenerator(root=str(tmp_path), metadata_dir=str(md_dir))
    # simulate spreadsheet headers matching
    omg.column_headers = ["root:a", "root:b"]
    omg.init_generate_descriptive_metadata()

    assert hasattr(omg, "xml_files")
    assert len(omg.xml_files) == 1
    entry = omg.xml_files[0]
    assert "data" in entry and entry["localname"] == "root"
    assert entry["xmlfile"].endswith("sample.xml")


def test_generate_opex_fixity(tmp_path):
    p = tmp_path / "file.txt"
    p.write_text("hello")

    omg = OpexManifestGenerator(root=str(tmp_path), algorithm=["SHA-1"])
    omg.fixities = ET.Element(f"{{{omg.opexns}}}Fixities")

    # Call instance method and get returned list
    returned_fixity = omg.generate_opex_fixity(str(p), algorithm=omg.algorithm)

    # fixity element(s) should be present
    assert len(list(omg.fixities)) >= 1
    assert len(returned_fixity) >= 1
    # ensure an entry contains the file path
    assert any(item[2] == str(p) for item in returned_fixity)


def test_generate_pax_zip_opex_fixity(tmp_path):
    zp = tmp_path / "test.pax.zip"
    with zipfile.ZipFile(str(zp), 'w') as z:
        z.writestr("a.txt", "a")
        z.writestr("b.txt", "b")

    omg = OpexManifestGenerator(root=str(tmp_path), algorithm=["SHA-1"])
    omg.fixities = ET.Element(f"{{{omg.opexns}}}Fixities")

    # Call instance method and get returned list
    returned_fixity = omg.generate_pax_zip_opex_fixity(str(zp), algorithm=omg.algorithm)

    # ensure entries created for files inside zip
    assert len(list(omg.fixities)) >= 2
    assert any('a.txt' in item[2] or 'b.txt' in item[2] for item in returned_fixity)


def test_hash_df_lookup_uses_spreadsheet_values(tmp_path):
    p = tmp_path / "file.txt"
    p.write_text("hello")

    omg = OpexManifestGenerator(root=str(tmp_path))

    # build a dataframe with index and hash values
    df = pd.DataFrame([{omg.INDEX_FIELD: str(p), omg.HASH_FIELD: 'DEADBEEF', omg.ALGORITHM_FIELD: 'MD5'}])
    omg.df = df
    omg.column_headers = df.columns.values.tolist()

    idx = omg.index_df_lookup(str(p))

    fixities = ET.Element(f"{{{omg.opexns}}}Fixities")
    omg.hash_df_lookup(fixities, idx)

    elems = list(fixities)
    assert len(elems) == 1
    assert elems[0].get('type') == 'MD5'
    assert elems[0].get('value') == 'DEADBEEF'


def test_init_generate_descriptive_metadata_multiple_files(tmp_path):
    md_dir = tmp_path / "meta"
    md_dir.mkdir()
    xml1 = '<?xml version="1.0"?><root xmlns="urn:test"><a>1</a></root>'
    xml2 = '<?xml version="1.0"?><r2 xmlns="urn:test"><b>2</b></r2>'
    (md_dir / "one.xml").write_text(xml1)
    (md_dir / "two.xml").write_text(xml2)

    omg = OpexManifestGenerator(root=str(tmp_path), metadata_dir=str(md_dir))
    omg.column_headers = ["root:a","r2:b"]
    omg.init_generate_descriptive_metadata()

    assert hasattr(omg, "xml_files")
    assert len(omg.xml_files) == 2


def test_generate_descriptive_metadata_flat_mode(tmp_path):
    md_dir = tmp_path / "meta"
    md_dir.mkdir()
    xml = '<?xml version="1.0"?><root xmlns="urn:test"><a>1</a></root>'
    (md_dir / "sample.xml").write_text(xml)

    omg = OpexManifestGenerator(root=str(tmp_path), metadata_dir=str(md_dir))
    omg.column_headers = ["root:a"]
    omg.df = pd.DataFrame([{omg.INDEX_FIELD: 'file', 'root:a': 'VALUE'}])
    omg.metadata_flag = 'f'
    omg.init_generate_descriptive_metadata()

    idx = omg.index_df_lookup('file')
    xml_desc = ET.Element('DescriptiveMetadata')
    omg.generate_descriptive_metadata(xml_desc, idx)

    # the element should have been appended with populated text
    assert len(list(xml_desc)) == 1
    assert list(xml_desc)[0].find('.//{urn:test}a').text == 'VALUE'


def test_identifiers_added_from_dataframe(tmp_path):
    omg = OpexManifestGenerator(root=str(tmp_path))
    # create dataframe with an identifier column
    header = f"{omg.IDENTIFIER_FIELD}:custom"
    omg.df = pd.DataFrame([{omg.INDEX_FIELD: 'path', header: 'IDVALUE'}])
    omg.column_headers = omg.df.columns.values.tolist()

    xmlroot = ET.Element('Root')
    omg.generate_opex_properties(xmlroot, omg.index_df_lookup('path'))

    ids = xmlroot.find(f'.//{{{omg.opexns}}}Identifiers')
    assert ids is not None
    ident = ids.find(f'./{{{omg.opexns}}}Identifier')
    assert ident is not None
    assert ident.get('type') == 'custom' or ident.get('type') == omg.IDENTIFIER_DEFAULT


def test_filter_directories_respects_hidden_flag(tmp_path):
    base = tmp_path / "dir"
    base.mkdir()
    (base / "visible.txt").write_text("ok")
    (base / ".hidden.txt").write_text("secret")

    omg = OpexManifestGenerator(root=str(tmp_path))
    # default hidden_flag False: hidden files should be filtered out
    d = OpexDir(omg, str(base))
    entries = d.filter_directories(str(base))
    assert any('visible.txt' in e for e in entries)
    assert not any('.hidden.txt' in e for e in entries)

    # when hidden_flag True, hidden files are included
    omg.hidden_flag = True
    d2 = OpexDir(omg, str(base))
    entries2 = d2.filter_directories(str(base))
    assert any('.hidden.txt' in e for e in entries2)


def test_generate_opex_dirs_does_not_overwrite_existing_opex(tmp_path):
    base = tmp_path / "folder"
    base.mkdir()
    # create existing opex file that should prevent overwrite
    target = base / "folder.opex"
    target.write_text("EXISTING")
    # add one content file to cause generation attempt
    (base / "file.txt").write_text("data")

    omg = OpexManifestGenerator(root=str(tmp_path))
    OpexDir(omg, str(base)).generate_opex_dirs(str(base))

    # ensure existing file unchanged
    assert target.read_text() == "EXISTING"


def test_generate_opex_fixity_default_algorithm(tmp_path):
    p = tmp_path / "file.txt"
    p.write_text("hello")

    omg = OpexManifestGenerator(root=str(tmp_path))
    omg.fixities = ET.Element(f"{{{omg.opexns}}}Fixities")

    # call without passing algorithm - should default to SHA-1 and record fixity
    returned_fixity = omg.generate_opex_fixity(str(p))
    assert len(list(omg.fixities)) >= 1
    assert any(item[0] == 'SHA-1' for item in returned_fixity)


def test_generate_descriptive_metadata_handles_missing_element(tmp_path):
    md_dir = tmp_path / "meta"
    md_dir.mkdir()
    xml = '<?xml version="1.0"?><root xmlns="urn:test"><a>1</a></root>'
    (md_dir / "sample.xml").write_text(xml)

    omg = OpexManifestGenerator(root=str(tmp_path), metadata_dir=str(md_dir))
    omg.column_headers = ["root:missing"]
    omg.df = pd.DataFrame([{omg.INDEX_FIELD: 'file', 'root:missing': 'VALUE'}])
    omg.metadata_flag = 'e'
    omg.init_generate_descriptive_metadata()

    idx = omg.index_df_lookup('file')
    xml_desc = ET.Element('DescriptiveMetadata')

    # should not raise and should simply skip missing element
    omg.generate_descriptive_metadata(xml_desc, idx)
    # since element missing, nothing appended
    assert len(list(xml_desc)) == 0


def test_clear_opex(tmp_path):
    d = tmp_path / "dir"
    d.mkdir()
    o = d / "sample.opex"
    o.write_text("meta")
    other = d / "keep.txt"
    other.write_text("keep")

    omg = OpexManifestGenerator(root=str(tmp_path))
    omg.clear_opex()

    assert not o.exists()
    assert other.exists()


def test_generate_opex_dirs_creates_opex(tmp_path):
    d = tmp_path / "folder"
    d.mkdir()
    (d / "file.txt").write_text("data")

    omg = OpexManifestGenerator(root=str(tmp_path))
    OpexDir(omg, str(d)).generate_opex_dirs(str(d))

    # find any .opex file in the folder
    opex_files = list(d.glob("*.opex"))
    assert len(opex_files) >= 1


def test_input_option_with_excel_file(tmp_path):
    # Create a test directory with a file
    base = tmp_path / "data"
    base.mkdir()
    test_file = base / "document.txt"
    test_file.write_text("test content")

    # Create an input Excel file with metadata
    input_file = tmp_path / "input.xlsx"
    df_input = pd.DataFrame([
        {
            "index": str(test_file),
            "title": "Test Document",
            "description": "A test document for opex generation"
        }
    ])
    df_input.to_excel(input_file, index=False)

    # Initialize OpexManifestGenerator with input option
    omg = OpexManifestGenerator(root=str(tmp_path), input=str(input_file))
    # Call init_df to load the input file
    omg.init_df()

    # Verify that the dataframe was loaded from the input file
    assert omg.df is not None
    assert len(omg.df) >= 1
    assert "index" in omg.column_headers


def test_input_option_with_csv_file(tmp_path):
    # Create a test directory with a file
    base = tmp_path / "data"
    base.mkdir()
    test_file = base / "file.csv"
    test_file.write_text("data")

    # Create an input CSV file
    input_file = tmp_path / "input.csv"
    df_input = pd.DataFrame([
        {
            "index": str(test_file),
            "title": "CSV Test"
        }
    ])
    df_input.to_csv(input_file, index=False)

    # Initialize with CSV input
    omg = OpexManifestGenerator(root=str(tmp_path), input=str(input_file))
    # Call init_df to load the input file
    omg.init_df()

    # Verify dataframe was loaded
    assert omg.df is not None
    assert len(omg.df) >= 1
    assert "index" in omg.column_headers


def test_input_option_sets_flags_with_special_columns(tmp_path):
    # Create an Excel file with special column headers that trigger flags
    input_file = tmp_path / "input.xlsx"
    df_input = pd.DataFrame([
        {
            "FullName": "path/to/file",
            "Title": "My Title",
            "Description": "My Description",
            "Security": "open",
            "SourceID": "SOURCE123"
        }
    ])
    df_input.to_excel(input_file, index=False)

    # Initialize with input
    omg = OpexManifestGenerator(root=str(tmp_path), input=str(input_file))
    # Call init_df to load and process the input file
    omg.init_df()

    # Verify that appropriate flags were set based on column headers
    assert omg.title_flag is True
    assert omg.description_flag is True
    assert omg.security_flag is True
    assert omg.sourceid_flag is True
