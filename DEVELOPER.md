# Developer Notes

## Supported Platforms

This code runs as a daemon and is intended for use Linux and UNIX-like platforms.

## Packaging and Dependencies

This project uses [Poetry](https://python-poetry.org/) to manage Python packaging and dependencies.  Most day-to-day tasks (such as running unit tests from the command line) are orchestrated through Poetry.  

A coding standard is enforced using [Black](https://github.com/psf/black), [isort](https://pypi.org/project/isort/) and [Pylint](https://www.pylint.org/).  Python 3 type hinting is validated using [MyPy](https://pypi.org/project/mypy/).

## Retries

Most API calls automatically retried using [tenacity](https://tenacity.readthedocs.io/en/latest/) annotations.  This
includes all `GET` API calls as well as any idempotent `POST` or `DELETE`
calls.

## Integration Testing

Local integration testing against the server can be accomplished in the repo
using a combination of `run server` and `run database`.  The `run database`
command relies on Docker Compose.  It starts both InfluxDB and Grafana.  If you
want to send in requests manually to watch the application's behavior, then
it's easiest if you disable signature checking 
in `config/local/sensortrack/server/application.yaml`.  InfluxDB is running
at localhost:8086 and Grafana is at localhost:3000.

## Continuous Integration (CI)

We use [GitHub Actions](https://docs.github.com/en/actions/quickstart) for CI.  See [.github/workflows/tox.yml](.github/workflows/tox.yml) for the definition of the workflow, and go to the [Actions tab](https://github.com/pronovic/smartapp-sensortrack/actions) to see what actions have been executed.  

## Pre-Commit Hooks

We rely on pre-commit hooks to ensure that the code is properly-formatted,
clean, and type-safe when it's checked in.  The `run install` step described
below installs the project pre-commit hooks into your repository.  These hooks
are configured in [`.pre-commit-config.yaml`](.pre-commit-config.yaml).

If necessary, you can temporarily disable a hook using Git's `--no-verify`
switch.  However, keep in mind that the CI build on GitHub enforces these
checks, so the build will fail.

## Line Endings

The [`.gitattributes`](.gitattributes) file controls line endings for the files
in this repository.  Instead of relying on automatic behavior, the
`.gitattributes` file forces most files to have UNIX line endings.  

## Prerequisites

Nearly all prerequisites are managed by Poetry.  All you need to do is make
sure that you have a working Python 3 enviroment and install Poetry itself.  

### MacOS

On MacOS, it's easiest to use [Homebrew](https://brew.sh/):

```
$ brew install python3
$ brew install poetry
```

Once that's done, make sure the `python` on your `$PATH` is Python 3 from
Homebrew (in `/usr/local`), rather than the standard Python 2 that comes with
MacOS.

### Debian

First, install Python 3 and related tools:

```
$ sudo apt-get install python3 python3-venv python3-pip
```

Next, make sure that the `python` interpreter on your `$PATH` is Python 3.

If you are using Debian _bullseye_ or later (first released in August 2021),
then Python 2 is deprecated and Python 3 is the primary Python on your system.
However, by default there is only a `python3` interpreter on your `$PATH`, not
a `python` interpreter.  To add the `python` interpreter, use:

```
$ sudo apt-get install python-is-python3
```

For earlier releases of Debian where both Python 2 and Python 3 are available,
the process is a little more complicated.  The approach I used before upgrading
to _bullseye_ was based on `update-alternatives`, as discussed on
[StackExchange](https://unix.stackexchange.com/a/410851).

Once Python 3 is on your `$PATH` as `python`, install Poetry in your home
directory:

```
$ curl -sSL https://install.python-poetry.org | python3 -
```

### Windows

First, install Python 3 from your preferred source, either a standard
installer or a meta-installer like Chocolatey.  Make sure the `python`
on your `$PATH` is Python 3.  

Then, install Poetry in your home directory:

```
$ curl -sSL https://install.python-poetry.org | python3 -
```

The development environment (with the `run` script, etc.) expects a bash shell
to be available.  On Windows, it works fine with the standard Git Bash.

## Developer Tasks

The [`run`](run) script provides shortcuts for common developer tasks:

```
$ run

------------------------------------
Shortcuts for common developer tasks
------------------------------------

Usage: run <command>

- run install: Setup the virtualenv via Poetry and install pre-commit hooks
- run activate: Print command needed to activate the Poetry virtualenv
- run format: Run the code formatters
- run checks: Run the code checkers
- run test: Run the unit tests
- run test -c: Run the unit tests with coverage
- run test -ch: Run the unit tests with coverage and open the HTML report
- run tox: Run the Tox test suite used by the GitHub CI action
- run server: Run the REST server at localhost:8080
- run database: Run the InfluxDB & Grafana servers via docker-compose
- run release: Release a specific version and tag the code
- run build: Build artifacts in the dist/ directory
```

For local testing, use `run influxdb` in one window and `run server` in another.
The standard local configuration is able to connect to the database.

## Integration with PyCharm

Currently, I use [PyCharm Community Edition](https://www.jetbrains.com/pycharm/download) as 
my day-to-day IDE.  By integrating Black and Pylint, most everything important
that can be done from a shell environment can also be done right in PyCharm.

PyCharm offers a good developer experience.  However, the underlying configuration
on disk mixes together project policy (i.e. preferences about which test runner to
use) with system-specific settings (such as the name and version of the active Python 
interpreter). This makes it impossible to commit complete PyCharm configuration 
to the Git repository.  Instead, the repository contains partial configuration, and 
there are instructions below about how to manually configure the remaining items.

### Prerequisites

Before going any further, make sure sure that you have installed all of the system
prerequisites discussed above.  Then, make sure your environment is in working
order.  In particular, if you do not run the install step, there will be no
virtualenv for PyCharm to use:

```
$ run install && run checks && run test
```

### Open the Project

Once you have a working shell development environment, **Open** (do not
**Import**) the `smartapp-sensortrack` directory in PyCharm, then follow the remaining
instructions below.  By using **Open**, the existing `.idea` directory will be
retained and all of the existing settings will be used.

### Interpreter

As a security precaution, PyCharm does not trust any virtual environment
installed within the repository, such as the Poetry `.venv` directory. In the
status bar on the bottom right, PyCharm will report _No interpreter_.  Click
on this error and select **Add Interpreter**.  In the resulting dialog, click
**Ok** to accept the selected environment, which should be the Poetry virtual
environment.

### Project Structure

Go to the PyCharm settings and find the `smartapp-sensortrack` project.  Under **Project
Structure**, mark both `src` and `tests` as source folders.  In the **Exclude
Files** box, enter the following:

```
LICENSE;NOTICE;PyPI.md;.coverage;.coveragerc;.github;.gitignore;.gitattributes;.htmlcov;.idea;.isort.cfg;.mypy.ini;.mypy_cache;.pre-commit-config.yaml;.pylintrc;.pytest_cache;.readthedocs.yml;.tox;.toxrc;.tabignore;build;dist;docs/_build;out;poetry.lock;poetry.toml;run;.runtime;pytest.ini
```

When you're done, click **Ok**.  Then, go to the gear icon in the project panel 
and uncheck **Show Excluded Files**.  This will hide the files and directories 
in the list above.

### Tool Preferences

In the PyCharm settings, go to **Editor > Inspections** and be sure that the
**Project Default** profile is selected.

Unit tests are written using [Pytest](https://docs.pytest.org/en/latest/),
and API documentation is written
using [Google Style Python Docstring](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html).  However, 
neither of these is the default in PyCharm.  In the PyCharm settings, go to 
**Tools > Python Integrated Tools**.  Under **Testing > Default test runner**, 
select _pytest_.  Under **Docstrings > Docstring format**, select _Google_.

### Running Unit Tests

Right click on the `tests` folder in the project explorer and choose **Run
'pytest in tests'**.  Make sure that all of the tests pass.  If you see a slightly
different option (i.e. for "Unittest" instead of "pytest") then you probably 
skipped the preferences setup discussed above.  You may need to remove the
run configuration before PyCharm will find the right test suite.

### External Tools

Optionally, you might want to set up external tools for some of common
developer tasks: code reformatting and the PyLint and MyPy checks.  One nice
advantage of doing this is that you can configure an output filter, which makes
the Pylint and MyPy errors clickable.  To set up external tools, go to PyCharm
settings and find **Tools > External Tools**.  Add the tools as described
below.

#### Linux or MacOS

On Linux or MacOS, you can set up the external tools to invoke the `run` script
directly.

##### Shell Environment

For this to work, it's important that tools like `poetry` are on the system
path used by PyCharm.  On Linux, depending on how you start PyCharm, your
normal shell environment may or may not be inherited.  For instance, I had to
adjust the target of my LXDE desktop shortcut to be the script below, which
sources my profile before running the `pycharm.sh` shell script:

```sh
#!/bin/bash
source ~/.bash_profile
/opt/local/lib/pycharm/pycharm-community-2020.3.2/bin/pycharm.sh
```

##### Format Code

|Field|Value|
|-----|-----|
|Name|`Format Code`|
|Description|`Run the Black and isort code formatters`|
|Group|`Developer Tools`|
|Program|`$ProjectFileDir$/run`|
|Arguments|`format`|
|Working directory|`$ProjectFileDir$`|
|Synchronize files after execution|_Checked_|
|Open console for tool outout|_Checked_|
|Make console active on message in stdout|_Unchecked_|
|Make console active on message in stderr|_Unchecked_|
|Output filters|_Empty_|

##### Run MyPy Checks

|Field|Value|
|-----|-----|
|Name|`Run MyPy Checks`|
|Description|`Run the MyPy code checks`|
|Group|`Developer Tools`|
|Program|`$ProjectFileDir$/run`|
|Arguments|`mypy`|
|Working directory|`$ProjectFileDir$`|
|Synchronize files after execution|_Unchecked_|
|Open console for tool outout|_Checked_|
|Make console active on message in stdout|_Checked_|
|Make console active on message in stderr|_Checked_|
|Output filters|`$FILE_PATH$:$LINE$:$COLUMN$:.*`|

##### Run Pylint Checks

|Field|Value|
|-----|-----|
|Name|`Run Pylint Checks`|
|Description|`Run the Pylint code checks`|
|Group|`Developer Tools`|
|Program|`$ProjectFileDir$/run`|
|Arguments|`pylint`|
|Working directory|`$ProjectFileDir$`|
|Synchronize files after execution|_Unchecked_|
|Open console for tool outout|_Checked_|
|Make console active on message in stdout|_Checked_|
|Make console active on message in stderr|_Checked_|
|Output filters|`$FILE_PATH$:$LINE$:$COLUMN.*`|

#### Windows

On Windows, PyCharm has problems invoking the `run` script, even via the Git
Bash interpreter.  I have created a Powershell script `utils/tools.ps1` that
can be used instead.

##### Format Code

|Field|Value|
|-----|-----|
|Name|`Format Code`|
|Description|`Run the Black and isort code formatters`|
|Group|`Developer Tools`|
|Program|`powershell.exe`|
|Arguments|`-executionpolicy bypass -File utils\tools.ps1 format`|
|Working directory|`$ProjectFileDir$`|
|Synchronize files after execution|_Checked_|
|Open console for tool outout|_Checked_|
|Make console active on message in stdout|_Unchecked_|
|Make console active on message in stderr|_Unchecked_|
|Output filters|_Empty_|

##### Run MyPy Checks

|Field|Value|
|-----|-----|
|Name|`Run MyPy Checks`|
|Description|`Run the MyPy code checks`|
|Group|`Developer Tools`|
|Program|`powershell.exe`|
|Arguments|`-executionpolicy bypass -File utils\tools.ps1 mypy`|
|Working directory|`$ProjectFileDir$`|
|Synchronize files after execution|_Unchecked_|
|Open console for tool outout|_Checked_|
|Make console active on message in stdout|_Checked_|
|Make console active on message in stderr|_Checked_|
|Output filters|`$FILE_PATH$:$LINE$:$COLUMN$:.*`|

##### Run Pylint Checks

|Field|Value|
|-----|-----|
|Name|`Run Pylint Checks`|
|Description|`Run the Pylint code checks`|
|Group|`Developer Tools`|
|Program|`powershell.exe`|
|Arguments|`-executionpolicy bypass -File utils\tools.ps1 pylint`|
|Working directory|`$ProjectFileDir$`|
|Synchronize files after execution|_Unchecked_|
|Open console for tool outout|_Checked_|
|Make console active on message in stdout|_Checked_|
|Make console active on message in stderr|_Checked_|
|Output filters|`$FILE_PATH$:$LINE$:$COLUMN.*`|


