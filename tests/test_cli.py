import time
from pathlib import Path as P

from typer.testing import CliRunner

from powerconf.cli import app

from .unit_test_utils import working_directory

runner = CliRunner(mix_stderr=False)


def test_command_helps():
    result = runner.invoke(app, ["render", "--help"])
    assert result.exit_code == 0
    assert (
        "Usage: root render [OPTIONS] CONFIG_FILE TEMPLATE_FILE OUTPUT" in result.stdout
    )

    result = runner.invoke(app, ["print-instances", "--help"])
    assert result.exit_code == 0
    assert "Usage: root print-instances [OPTIONS] CONFIG_FILE" in result.stdout

    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "Usage: root run [OPTIONS] TOOL CONFIG_FILE" in result.stdout


def test_run_command_basic(tmp_path):
    with working_directory(tmp_path):
        config_text = """

powerconf-run:
    acme:
        command:
            - echo "HI FROM TOOL"
    """

        P("CONFIG.yml").write_text(config_text)

        result = runner.invoke(app, ["run", "missing", "CONFIG.yml"])

        assert result.exit_code == 1
        assert "'powerconf-run/missing'" in result.stderr
        assert "key in config instance" in result.stderr
        assert "0" in result.stderr

        result = runner.invoke(app, ["run", "acme", "CONFIG.yml"], env={"TERM": "dumb"})

        if result.exit_code != 0:
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
        assert result.exit_code == 0

        assert "Running:" in result.stdout
        assert "vvv\nHI FROM TOOL\n\n^^^" in result.stdout


def test_run_command_with_batch_configs(tmp_path):
    with working_directory(tmp_path):
        config_text = """
run:
    '@batch':
        - 1
        - 2

powerconf-run:
    acme:
        command:
            - touch OUTPUT-$(${/run}).txt
            - touch LOG-$(${/run}).txt
    """

        P("CONFIG.yml").write_text(config_text)

        result = runner.invoke(app, ["run", "acme", "CONFIG.yml"])

        assert result.exit_code == 0

        assert P("OUTPUT-1.txt").exists()
        assert P("OUTPUT-2.txt").exists()
        assert P("LOG-1.txt").exists()
        assert P("LOG-2.txt").exists()


def test_run_command_with_config_file_to_render(tmp_path):
    with working_directory(tmp_path):
        config_text = """
run: 1
acme:
    simulation:
      output: output-$(${/run}).txt
powerconf-run:
    acme:
        template_config_file: config-acme.txt.template
        command:
            - touch OUTPUT-$(${/run}).txt
            - touch LOG-$(${/run}).txt
    """
        P("CONFIG.yml").write_text(config_text)

        result = runner.invoke(app, ["run", "acme", "CONFIG.yml"])
        assert result.exit_code == 2
        assert "Invalid configuration" in result.stderr
        assert (
            "`powerconf-run/acme/template_config_file` was found but" in result.stderr
        )
        assert "`powerconf-run/acme/rendered_config_file` was not" in result.stderr

        config_text = """
run: 1
acme:
    simulation:
      output: output-$(${/run}).txt
powerconf-run:
    acme:
        rendered_config_file: config-acme.txt
        command:
            - touch OUTPUT-$(${/run}).txt
            - touch LOG-$(${/run}).txt
    """
        P("CONFIG.yml").write_text(config_text)

        result = runner.invoke(app, ["run", "acme", "CONFIG.yml"])
        assert result.exit_code == 2
        assert "Invalid configuration" in result.stderr
        assert (
            "`powerconf-run/acme/rendered_config_file` was found but" in result.stderr
        )
        assert "`powerconf-run/acme/template_config_file` was not" in result.stderr

        config_text = """
run: 1
acme:
    simulation:
      output: output-$(${/run}).txt
powerconf-run:
    acme:
        template_config_file: config-acme.txt.template
        rendered_config_file: config-acme.txt
        command:
            - touch OUTPUT-$(${/run}).txt
            - touch LOG-$(${/run}).txt
    """
        P("CONFIG.yml").write_text(config_text)

        template_config_text = """
output = {{acme/simulation/output}}
"""
        P("config-acme.txt.template").write_text(template_config_text)

        result = runner.invoke(app, ["run", "acme", "CONFIG.yml"])

        assert result.exit_code == 0

        print(list(P().glob("*")))
        assert P("config-acme.txt").exists()
        assert (
            P("config-acme.txt").read_text()
            == """
output = output-1.txt
"""
        )


def test_run_command_timing(tmp_path):
    with working_directory(tmp_path):
        config_text = """
powerconf-run:
    acme:
        command:
            - sleep 0.5
    """

        P("CONFIG.yml").write_text(config_text)

        start = time.perf_counter()
        result = runner.invoke(app, ["run", "acme", "CONFIG.yml"])
        if result.exit_code != 0:
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
        assert result.exit_code == 0
        end = time.perf_counter()
        duration = end - start
        assert duration > 0.5
        assert duration < 1

        config_text = """
powerconf-run:
    acme:
        command:
            - sleep 1
    """

        P("CONFIG.yml").write_text(config_text)

        start = time.perf_counter()
        result = runner.invoke(app, ["run", "acme", "CONFIG.yml"])
        end = time.perf_counter()
        duration = end - start
        assert duration > 1
        assert duration < 2

        config_text = """
num:
    '@batch':
      - 1
      - 2
powerconf-run:
    acme:
        command:
            - sleep 1
    """

        P("CONFIG.yml").write_text(config_text)

        start = time.perf_counter()
        result = runner.invoke(app, ["run", "acme", "CONFIG.yml"])
        assert result.exit_code == 0
        end = time.perf_counter()
        duration = end - start
        # we are running each config in parallel (using multiprocessing)
        # so the run time should be the same for two as it is for one.
        assert duration > 1
        assert duration < 2
