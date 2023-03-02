from typer.testing import CliRunner

from gwas_sumstats_tools.cli import app

runner = CliRunner()


def test_app():
    result = runner.invoke(app)
    assert result.exit_code == 0


def test_all_commands():
    read_cmd = runner.invoke(app, ["read"])
    assert read_cmd.exit_code == 0
    format_cmd = runner.invoke(app, ["format"])
    assert format_cmd.exit_code == 0
    validate_cmd = runner.invoke(app, ["validate"])
    assert validate_cmd.exit_code == 0
