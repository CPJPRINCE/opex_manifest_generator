import pandas as pd
import pytest
from lxml import etree

from opex_manifest_generator.opexLib import OpexDirWriter
from opex_manifest_generator.hash import HashGenerator
from opex_manifest_generator.opexManifest import OpexManifestGenerator
from opex_manifest_generator.common import filter_manifest

def test_init_generate_descriptive_metadata(tmp_path):
    md_dir = tmp_path / "meta"
    md_dir.mkdir()
    xml = '<?xml version="1.0"?><root xmlns="urn:test"><a>1</a><b>2</b></root>'
    (md_dir / "sample.xml").write_text(xml)

    omg = OpexManifestGenerator(root=str(tmp_path), metadata_dir=str(md_dir))
    omg.column_headers = ["root:a", "root:b"]

    xml_files = omg.init_generate_descriptive_metadata()

    assert len(xml_files) == 1
    entry = xml_files[0]
    assert entry["localname"] == "root"
    assert entry["xmlfile"].endswith("sample.xml")
    assert len(entry["data"]) >= 1


def test_hash_df_lookup_uses_spreadsheet_values(tmp_path):
    p = tmp_path / "file.txt"
    p.write_text("hello")

    omg = OpexManifestGenerator(root=str(tmp_path))
    df = pd.DataFrame([{omg.INDEX_FIELD: str(p), f"{omg.HASH_FIELD}:SHA-1": "DEADBEEF"}])
    omg.df = df
    omg.column_headers = df.columns.values.tolist()

    idx = omg.index_df_lookup(str(p))
    hashes = omg.hash_df_lookup(idx, ["SHA-1"])

    assert hashes == [{'type': "SHA-1", "value": "DEADBEEF"}]

def test_hash_df_lookup_returns_none_when_column_missing(tmp_path):
    p = tmp_path / "file.txt"
    p.write_text("hello")

    omg = OpexManifestGenerator(root=str(tmp_path))
    df = pd.DataFrame([{omg.INDEX_FIELD: str(p), "Other": "value"}])
    omg.df = df
    omg.column_headers = df.columns.values.tolist()

    idx = omg.index_df_lookup(str(p))
    hashes = omg.hash_df_lookup(idx, ["SHA-1"])

    assert hashes is None


def test_index_df_lookup_raises_when_df_uninitialised(tmp_path):
    omg = OpexManifestGenerator(root=str(tmp_path))

    with pytest.raises(RuntimeError, match="Dataframe not initialised"):
        omg.index_df_lookup("missing")


def test_ident_df_lookup_custom_identifier(tmp_path):
    omg = OpexManifestGenerator(root=str(tmp_path))
    header = f"{omg.IDENTIFIER_FIELD}:custom"
    omg.df = pd.DataFrame([{omg.INDEX_FIELD: "path", header: "IDVALUE"}])
    omg.column_headers = omg.df.columns.values.tolist()

    identifiers = omg.ident_df_lookup(omg.index_df_lookup("path"))

    assert identifiers == [{"type": "custom", "value": "IDVALUE"}]


def test_ident_df_lookup_returns_none_for_empty_index(tmp_path):
    omg = OpexManifestGenerator(root=str(tmp_path))
    header = f"{omg.IDENTIFIER_FIELD}:custom"
    omg.df = pd.DataFrame([{omg.INDEX_FIELD: "path", header: "IDVALUE"}])
    omg.column_headers = omg.df.columns.values.tolist()

    idx = omg.index_df_lookup("does-not-exist")
    identifiers = omg.ident_df_lookup(idx)

    assert identifiers is None


def test_xip_df_lookup_returns_expected_values(tmp_path):
    omg = OpexManifestGenerator(root=str(tmp_path))
    omg.title_flag = True
    omg.description_flag = True
    omg.security_flag = True
    omg.df = pd.DataFrame([
        {
            omg.INDEX_FIELD: "path",
            omg.TITLE_FIELD: "My Title",
            omg.DESCRIPTION_FIELD: "My Description",
            omg.SECURITY_FIELD: "open",
        }
    ])

    idx = omg.index_df_lookup("path")
    title, description, security = omg.xip_df_lookup(idx)

    assert title == "My Title"
    assert description == "My Description"
    assert security == "open"


def test_ignore_and_removal_lookup_return_false_for_empty_index(tmp_path):
    omg = OpexManifestGenerator(root=str(tmp_path))
    omg.df = pd.DataFrame([
        {
            omg.INDEX_FIELD: "path",
            omg.REMOVAL_FIELD: True,
            omg.IGNORE_FIELD: True,
        }
    ])

    idx = omg.index_df_lookup("does-not-exist")

    assert omg.removal_df_lookup(idx) is False
    assert omg.ignore_df_lookup(idx) is False


def test_sourceid_df_lookup_value_and_empty_index(tmp_path):
    omg = OpexManifestGenerator(root=str(tmp_path))
    omg.df = pd.DataFrame([
        {
            omg.INDEX_FIELD: "path",
            omg.SOURCEID_FIELD: "SRC-001",
        }
    ])

    idx = omg.index_df_lookup("path")
    assert omg.sourceid_df_lookup(idx) == "SRC-001"

    empty_idx = omg.index_df_lookup("does-not-exist")
    assert omg.sourceid_df_lookup(empty_idx) is None


def test_filter_manifest_respects_hidden_flag(tmp_path):
    base = tmp_path / "dir"
    base.mkdir()
    (base / "visible.txt").write_text("ok")
    (base / ".hidden.txt").write_text("secret")
    writer = OpexDirWriter(str(base))

    entries = filter_manifest(str(base), include_hidden=False)
    assert any("visible.txt" in e for e in entries)
    assert not any(".hidden.txt" in e for e in entries)

    entries_hidden = filter_manifest(str(base), include_hidden=True)
    assert any(".hidden.txt" in e for e in entries_hidden)


def test_write_opex_manifest_does_not_overwrite_existing(tmp_path):
    base = tmp_path / "folder"
    base.mkdir()
    target = base / "folder.opex"
    target.write_text("EXISTING")
    (base / "file.txt").write_text("data")

    writer = OpexDirWriter(str(base))
    result = writer.write_opex_manifest()

    assert result is None
    assert target.read_text() == "EXISTING"


def test_write_opex_manifest_creates_opex(tmp_path):
    base = tmp_path / "folder"
    base.mkdir()
    (base / "file.txt").write_text("data")

    writer = OpexDirWriter(str(base))
    output_path = writer.write_opex_manifest()

    assert output_path is not None
    assert (base / "folder.opex").exists()


def test_generate_descriptive_metadata_exact_mode(tmp_path):
    md_dir = tmp_path / "meta"
    md_dir.mkdir()
    xml_path = md_dir / "sample.xml"
    xml_path.write_text('<?xml version="1.0"?><root xmlns="urn:test"><a /></root>')

    omg = OpexManifestGenerator(root=str(tmp_path), metadata_dir=str(md_dir))
    omg.metadata_flag = "exact"
    omg.df = pd.DataFrame([{omg.INDEX_FIELD: "file", "root:a": "VALUE"}])
    omg.column_headers = omg.df.columns.values.tolist()
    omg.xml_files = [{
        "data": [{"Name": "root:a", "Namespace": "urn:test", "Path": "root:a"}],
        "localname": "root",
        "localns": "urn:test",
        "xmlfile": str(xml_path),
    }]

    idx = omg.index_df_lookup("file")
    result = omg.generate_descriptive_metadata(idx)
    
    # Should return an XML string containing the populated metadata
    assert result is not None
    assert isinstance(result, list)
    # Should contain the updated value
    assert "VALUE" in result[0]
    assert 'xmlns="urn:test"' in result[0]
    # Parse and verify structure
    root_elem = etree.fromstring(result[0])
    a_elem = root_elem.find('.//{urn:test}a')
    assert a_elem is not None
    assert a_elem.text == "VALUE"


def test_generate_descriptive_metadata_missing_element_does_not_raise(tmp_path):
    md_dir = tmp_path / "meta"
    md_dir.mkdir()
    xml_path = md_dir / "sample.xml"
    xml_path.write_text('<?xml version="1.0"?><root xmlns="urn:test"><a>1</a></root>')

    omg = OpexManifestGenerator(root=str(tmp_path), metadata_dir=str(md_dir))
    omg.metadata_flag = "exact"
    omg.df = pd.DataFrame([{omg.INDEX_FIELD: "file", "root:missing": "VALUE"}])
    omg.column_headers = omg.df.columns.values.tolist()
    omg.xml_files = [{
        "data": [{"Name": "root:missing", "Namespace": "urn:test", "Path": "root:missing"}],
        "localname": "root",
        "localns": "urn:test",
        "xmlfile": str(xml_path),
    }]

    idx = omg.index_df_lookup("file")
    # Should not raise an error when element is missing, just log a warning
    result = omg.generate_descriptive_metadata(idx)
    
    # Should still return an XML string (with original content unchanged)
    assert result is not None
    assert isinstance(result, list)
    # Original value should remain since update failed
    assert "<a>1</a>" in result[0]


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


def test_input_option_with_excel_file(tmp_path):
    base = tmp_path / "data"
    base.mkdir()
    test_file = base / "document.txt"
    test_file.write_text("test content")

    input_file = tmp_path / "input.xlsx"
    df_input = pd.DataFrame([
        {
            "index": str(test_file),
            "title": "Test Document",
            "description": "A test document for opex generation",
        }
    ])
    df_input.to_excel(input_file, index=False)

    omg = OpexManifestGenerator(root=str(tmp_path), input=str(input_file))
    omg.init_df()

    assert omg.df is not None
    assert len(omg.df) >= 1
    assert "index" in omg.column_headers


def test_input_option_with_csv_file(tmp_path):
    base = tmp_path / "data"
    base.mkdir()
    test_file = base / "file.csv"
    test_file.write_text("data")

    input_file = tmp_path / "input.csv"
    df_input = pd.DataFrame([
        {
            "index": str(test_file),
            "title": "CSV Test",
        }
    ])
    df_input.to_csv(input_file, index=False)

    omg = OpexManifestGenerator(root=str(tmp_path), input=str(input_file))
    omg.init_df()

    assert omg.df is not None
    assert len(omg.df) >= 1
    assert "index" in omg.column_headers


def test_process_fixity_eager_merges_spreadsheet_and_generated_hashes(tmp_path):
    test_file = tmp_path / "file.txt"
    test_file.write_text("hello")

    omg = OpexManifestGenerator(root=str(tmp_path), fixity=["SHA-1", "SHA-256"])
    omg.df = pd.DataFrame([
        {
            omg.INDEX_FIELD: str(test_file),
            f"{omg.HASH_FIELD}:SHA-1": "DEADBEEF",
        }
    ])
    omg.column_headers = omg.df.columns.values.tolist()
    omg.hash_from_spread = True

    idx = omg.index_df_lookup(str(test_file))
    hash_list, generate_fixity = omg._process_fixity(str(test_file), index=idx, eager=True)

    assert generate_fixity is None
    assert hash_list is not None
    hash_map = {entry["type"]: entry["value"] for entry in hash_list}
    assert hash_map["SHA-1"] == "DEADBEEF"
    assert hash_map["SHA-256"] == HashGenerator("SHA-256").hash_generator(str(test_file))


def test_main_writes_threaded_file_opex_with_fixity(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    file_a = root / "a.txt"
    file_b = root / "b.txt"
    file_a.write_text("alpha")
    file_b.write_text("beta")

    omg = OpexManifestGenerator(
        root=str(root),
        fixity=["SHA-1"],
        max_workers=2,
    )

    omg.main()

    ns = {"opex": "http://www.openpreservationexchange.org/opex/v1.2"}
    for source_file in (file_a, file_b):
        opex_path = source_file.with_suffix(source_file.suffix + ".opex")
        assert opex_path.exists()

        tree = etree.parse(str(opex_path))
        fixity = tree.find(".//opex:Fixity", namespaces=ns)

        assert fixity is not None
        assert fixity.attrib["type"] == "SHA-1"
        fixity_value = fixity.attrib.get("value") or fixity.text
        assert fixity_value is not None
        assert len(fixity_value) == 40
