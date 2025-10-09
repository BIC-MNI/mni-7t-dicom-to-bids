# Compilation

## Setup

To more easily distribute the MNI 7T DICOM to BIDS converter, this project can be compiled into an executable by using PyInstaller.

Compiling a package with PyInstaller requires the Python header files, which can be installed using the following command:

```sh
sudo apt install python3.11-dev
```

PyInstaller is a development dependency of the project, and can be installed as such using the following command in the project directory:

```sh
pip install .[dev]
```

## Configuration

The PyInstaller configuration of the MNI 7T DICOM to BIDS converter is saved in the `mni7t_dcm2bids.spec` file. To regenerate this configuration, use the following command in the project root directory:

```sh
pyi-makespec --onefile --name mni7t_dcm2bids --add-data src/mni_7t_dicom_to_bids/assets:mni_7t_dicom_to_bids/assets src/mni_7t_dicom_to_bids/scripts/run_mni7t_dcm2bids.py
```

## Compilation (local compatibility)

To compile the MNI 7T DICOM to BIDS converter, use the following command in the project root directory:

```sh
pyinstaller mni7t_dcm2bids.spec
```

This will create a `dist/mni7t_dcm2bids` executable for the MNI 7T DICOM to BIDS converter.

## Compilation (maximum compatibility)

The executable of a project compiled with PyInstaller may be depend on the `glibc` version of the system on which it was compiled. As such, the MNI 7T DICOM to BIDS includes a `compile.Dockerfile` file designed to build the project using an old `glibc` version such that the executable created is compatible with Debian 11 or more recent Debian-based systems.

To build the Docker image for the compiler, use the following command in the project root directory:

```sh
docker build -t compile_mni_7t_dicom_to_bids -f compile.Dockerfile .
```

To compile the using the previously built Docker image, use the following command while replacing `TARGET_DIRECTORY_PATH` by the directory in which to create the executable:

```sh
docker run --mount type=bind,src=TARGET_DIRECTORY_PATH,dst=/mni_7t_dicom_to_bids/dist compile_mni_7t_dicom_to_bids
```
