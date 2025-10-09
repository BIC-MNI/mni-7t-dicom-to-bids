# Contributing

This document explains how to modify and contribute to the MNI 7T DICOM to BIDS converter.

## GitHub

The GitHub repository of the project can be found at https://github.com/BIC-MNI/mni-7t-dicom-to-bids, if you want to contribute, do not hesitate to fill an issue or open a a pull request.

## Installation

As with the a normal installation, start by installing the BIC utilities Python package.

```sh
pip install git+https://github.com/BIC-MNI/bic-mri-pipeline-util
```

Then, clone the MNI 7T DICOM to BIDS converter Git repository to your machine:

```sh
git clone https://github.com/BIC-MNI/mni-7t-dicom-to-bids
```

Then, install the MNI 7T DICOM to BIDS converter Python package in development mode:

```sh
pip install -e mni-7t-dicom-to-bids[dev]
```

In this command:
- `mni-7t-dicom-to-bids` is the path of the repository you just cloned (if you moved into the project directory, then that path would be `.`).
- `-e` (or `--editable` in its long form) keeps the package modifiable instead of simply copying the current code.
- `[dev]` also installs the development tools.

## Development tools

This project uses the [Ruff](https://github.com/astral-sh/ruff) linter and the [Pyright](https://github.com/microsoft/pyright) type checker. All code must comply with both these tools to be merged into the project.

### Ruff

A linter is a tool that ensures the code adheres to a consistent style in line with the Python best practices.

To list all style violations currently present in the project, go to the project root directory and run the following command:
```sh
ruff check
```

Ruff also has an option to automatically fix many style inconsistencies, to do so, add the `--fix` option to the command:
```sh
ruff check --fix
```

### Pyright

A type checker is a tool that ensures the soundness of the way data flows in the code. This check is done in two steps:
- First, the code declares the type of the data (`int`, `str`, `list`...) it receives and returns in functions and classes.
- Second, the code is automatically checked to ensure that the flow of the data corresponds to the above type declarations.

To check the types in the code, use the following command in the project root directory:
```sh
pyright
```

## Getting help

If you need any help with the development installation and development tools, do not hesitate to open an issue.
