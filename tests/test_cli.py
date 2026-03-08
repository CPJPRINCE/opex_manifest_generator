import argparse

import pytest

from opex_manifest_generator import cli


class DummyGenerator:
    called = False
    init_kwargs = None

    def __init__(self, **kwargs):
        DummyGenerator.called = True
        DummyGenerator.init_kwargs = kwargs

    def main(self):
        return None

    def print_descriptive_xmls(self):
        return None

    def convert_descriptive_xmls(self):
        return None


@pytest.fixture
def reset_dummy_generator():
    DummyGenerator.called = False
    DummyGenerator.init_kwargs = None
    yield
    DummyGenerator.called = False
    DummyGenerator.init_kwargs = None


def test_fixity_helper_aliases_and_invalid():
    assert cli.fixity_helper("md5") == "MD5"
    assert cli.fixity_helper("s1") == "SHA-1"
    assert cli.fixity_helper("256") == "SHA-256"
    assert cli.fixity_helper("sha-512") == "SHA-512"

    with pytest.raises(argparse.ArgumentTypeError):
        cli.fixity_helper("bad")


def test_suffix_and_metadata_helpers():
    assert cli.suffix_helper("files") == "file"
    assert cli.suffix_helper("folder") == "directory"
    assert cli.suffix_helper("b") == "both"

    assert cli.metadata_helper("e") == "exact"
    assert cli.metadata_helper("flat") == "flat"

    with pytest.raises(argparse.ArgumentTypeError):
        cli.suffix_helper("nope")
    with pytest.raises(argparse.ArgumentTypeError):
        cli.metadata_helper("nope")


def test_format_helper_aliases_and_invalid():
    assert cli.fmthelper("excel") == "xlsx"
    assert cli.fmthelper("comma") == "csv"
    assert cli.fmthelper("jsn") == "json"
    assert cli.fmthelper("open_document_spreadsheet") == "ods"
    assert cli.fmthelper("htm") == "xml"

    with pytest.raises(argparse.ArgumentTypeError):
        cli.fmthelper("binary")


def test_run_cli_raises_for_missing_root(tmp_path):
    args = cli.create_parser().parse_args([str(tmp_path / "does-not-exist")])

    with pytest.raises(FileNotFoundError):
        cli.run_cli(args)


def test_run_cli_raises_for_input_and_autoref_conflict(tmp_path):
    args = cli.create_parser().parse_args([str(tmp_path), "-i", "input.csv", "-r", "catalog"])

    with pytest.raises(ValueError, match="Both Input and Auto ref"):
        cli.run_cli(args)


def test_run_cli_raises_for_remove_without_input(tmp_path):
    args = cli.create_parser().parse_args([str(tmp_path), "-rm"])

    with pytest.raises(ValueError, match="Removal flag has been given without input"):
        cli.run_cli(args)


def test_run_cli_sets_default_output_and_invokes_generator(monkeypatch, tmp_path, reset_dummy_generator):
    monkeypatch.setattr(cli, "OpexManifestGenerator", DummyGenerator)
    args = cli.create_parser().parse_args([str(tmp_path)])

    cli.run_cli(args)

    assert DummyGenerator.called is True
    assert args.output == str(tmp_path.resolve())
    assert DummyGenerator.init_kwargs["root"] == str(tmp_path.resolve())
    assert DummyGenerator.init_kwargs["output_path"] == str(tmp_path.resolve())


def test_run_cli_sets_accession_mode_default_for_accession(monkeypatch, tmp_path, reset_dummy_generator):
    monkeypatch.setattr(cli, "OpexManifestGenerator", DummyGenerator)
    args = cli.create_parser().parse_args([str(tmp_path), "-r", "accession"])

    cli.run_cli(args)

    assert DummyGenerator.called is True
    assert args.accession_mode == "file"
    assert DummyGenerator.init_kwargs["accession_mode"] == "file"


def test_fixity_action_defaults_to_sha1_when_no_value(tmp_path):
    args = cli.create_parser().parse_args([str(tmp_path), "-fx"])

    assert args.fixity == ["SHA-1"]


def test_verbose_flag_disables_show_progress_bar_in_generator(monkeypatch, tmp_path, reset_dummy_generator):
    monkeypatch.setattr(cli, "OpexManifestGenerator", DummyGenerator)
    args = cli.create_parser().parse_args([str(tmp_path), "-v"])

    cli.run_cli(args)

    assert args.verbose is False
    assert DummyGenerator.init_kwargs["show_progress_bar"] is False


def test_run_cli_print_xmls_exits_early(monkeypatch, tmp_path, reset_dummy_generator):
    monkeypatch.setattr(cli, "OpexManifestGenerator", DummyGenerator)
    args = cli.create_parser().parse_args([str(tmp_path), "--print-xmls"])

    with pytest.raises(SystemExit):
        cli.run_cli(args)


def test_run_cli_convert_xmls_exits_early(monkeypatch, tmp_path, reset_dummy_generator):
    monkeypatch.setattr(cli, "OpexManifestGenerator", DummyGenerator)
    args = cli.create_parser().parse_args([str(tmp_path), "--convert-xmls"])

    with pytest.raises(SystemExit):
        cli.run_cli(args)
