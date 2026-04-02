import os
import zipfile

import pytest

from opex_manifest_generator.opexLib import OpexDirReader, OpexDirWriter, OpexFileReader, OpexFileWriter


def test_opex_file_writer_and_reader_roundtrip(tmp_path):
    content_file = tmp_path / "doc.txt"
    content_file.write_text("hello")

    writer = OpexFileWriter(
        str(content_file),
        title="Title",
        description="Description",
        security_tag="open",
        sourceid="SRC-123",
        identifiers=[{"type": "custom", "value": "ID-1"}],
    )
    opex_path = writer.write_opex_file()

    assert opex_path is not None
    assert os.path.exists(opex_path)

    reader = OpexFileReader(opex_path)
    assert reader.get_title() == "Title"
    assert reader.get_description() == "Description"
    assert reader.get_security_descriptor() == "open"
    assert reader.get_sourceid() == "SRC-123"
    assert reader.get_identifiers() == [{"type": "custom", "value": "ID-1"}]
    assert reader.verify_opex_version("1.2") is False
    assert reader.verify_opex_version("v1.2") is True


def test_opex_file_writer_does_not_overwrite_existing_by_default(tmp_path):
    content_file = tmp_path / "doc.txt"
    content_file.write_text("hello")

    target = tmp_path / "custom.opex"
    target.write_text("EXISTING")

    writer = OpexFileWriter(str(content_file))
    result = writer.write_opex_file(str(target))

    assert result is None
    assert target.read_text() == "EXISTING"


def test_opex_file_writer_generate_fixity_populates_value(tmp_path):
    content_file = tmp_path / "doc.txt"
    content_file.write_text("hello")

    writer = OpexFileWriter(
        str(content_file),
        generate_fixity=["SHA-1"],
    )
    opex_path = writer.write_opex_file()

    reader = OpexFileReader(opex_path)
    fixities = reader.get_fixities()
    assert fixities == [{"type": "SHA-1", "value": None}]

    # Generated fixity is currently stored on the XML attribute, not element text.
    tree = reader.to_tree()
    opexns = tree.getroot().nsmap.get("opex")
    fixity = tree.find(f".//{{{opexns}}}Fixities/{{{opexns}}}Fixity")
    assert fixity is not None
    assert fixity.attrib.get("type") == "SHA-1"
    assert fixity.attrib.get("value") is not None


def test_opex_dir_writer_and_reader_manifest_roundtrip(tmp_path):
    folder = tmp_path / "folder"
    sub = folder / "subfolder"
    folder.mkdir()
    sub.mkdir()
    (folder / "file.txt").write_text("data")

    writer = OpexDirWriter(str(folder), title="Dir Title")
    opex_path = writer.write_opex_manifest()

    assert opex_path is not None

    reader = OpexDirReader(opex_path)
    assert reader.get_title() == "Dir Title"
    assert "subfolder" in reader.get_folders()
    assert "file.txt" in reader.get_files()
    assert reader.verify_opex_version("1.2") is False
    assert reader.verify_opex_version("v1.2") is True


def test_opex_dir_writer_invalid_filter_flag_raises(tmp_path):
    folder = tmp_path / "folder"
    folder.mkdir()

    with pytest.raises(ValueError, match="Invalid filter_flag value"):
        OpexDirWriter(str(folder), filter_flag="bad")


def test_zip_opex_file_creates_zip_and_removes_originals(tmp_path):
    content_file = tmp_path / "doc.txt"
    content_file.write_text("hello")

    writer = OpexFileWriter(str(content_file))
    zip_path = writer.zip_opex_file(remove_files=True)

    assert os.path.exists(zip_path)
    assert not content_file.exists()
    assert not (tmp_path / "doc.txt.opex").exists()

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = set(zf.namelist())

    assert "doc.txt" in names
    assert "doc.txt.opex" in names


def test_zip_opex_file_when_zip_exists_returns_existing_path(tmp_path):
    content_file = tmp_path / "doc.txt"
    content_file.write_text("hello")
    existing_zip = tmp_path / "doc.txt.zip"
    existing_zip.write_text("placeholder")

    writer = OpexFileWriter(str(content_file))
    zip_path = writer.zip_opex_file()

    assert zip_path == str(existing_zip)
    assert content_file.exists()


def test_write_opex_file_to_custom_path(tmp_path):
    content_file = tmp_path / "doc.txt"
    content_file.write_text("hello")

    custom_path = tmp_path / "custom-name.opex"
    writer = OpexFileWriter(str(content_file), title="Custom")
    out = writer.write_opex_file(str(custom_path), file_override=True)

    assert out == str(custom_path)
    assert custom_path.exists()


def test_opex_file_reader_raises_on_invalid_xml(tmp_path):
    bad = tmp_path / "bad.opex"
    bad.write_text("<not-xml")

    with pytest.raises(Exception):
        OpexFileReader(str(bad))


def test_opex_dir_reader_raises_on_invalid_xml(tmp_path):
    bad = tmp_path / "bad-dir.opex"
    bad.write_text("<not-xml")

    with pytest.raises(Exception):
        OpexDirReader(str(bad))
