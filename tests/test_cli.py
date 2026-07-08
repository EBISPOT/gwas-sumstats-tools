from typer.testing import CliRunner

from gwas_sumstats_tools.cli import app

runner = CliRunner()


def test_app():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0


def test_all_commands():
    read_cmd = runner.invoke(app, ["read", "--help"])
    assert read_cmd.exit_code == 0
    format_cmd = runner.invoke(app, ["format", "--help"])
    assert format_cmd.exit_code == 0
    validate_cmd = runner.invoke(app, ["validate", "--help"])
    assert validate_cmd.exit_code == 0
