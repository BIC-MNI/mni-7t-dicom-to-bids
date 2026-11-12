# Contributing

This document explains how to modify and contribute to the MNI 7T DICOM to BIDS converter.

## GitHub

The GitHub repository of the project can be found at https://github.com/bic-mni/mni-7t-dicom-to-bids, if you want to contribute, do not hesitate to fill an issue or open a a pull request.

## Python installation

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then clone the converter repository:

```sh
git clone https://github.com/bic-mni/mni-7t-dicom-to-bids
cd mni-7t-dicom-to-bids
```

Install the converter and its development and test dependencies using the committed lockfile:

```sh
uv sync --locked --extra dev --group test
```


## Docker build

To build the Docker image of the converter locally, use the following command in the project root directory:

```sh
docker build -t mni-7t-dicom-to-bids .
```

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

### Pytest

Run the existing unit tests with the following command:

```sh
pytest
```

## Getting help

If you need any help with the development installation and development tools, do not hesitate to open an issue.
