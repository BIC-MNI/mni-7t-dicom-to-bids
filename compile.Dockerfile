# Use an old Debian system to compile the converter with an old glibc version and ensure
# compatibility with many users.
FROM debian:11

RUN apt-get update

# Install Python 3.11

# Python 3.11 is not available by default on Debian 11. As such, we compile it from source instead.

# Install the Python build dependencies.
# Copied from https://github.com/python/cpython/blob/3.11/.github/workflows/posix-deps-apt.sh
RUN apt-get -yq install \
    build-essential \
    pkg-config \
    ccache \
    gdb \
    lcov \
    libb2-dev \
    libbz2-dev \
    libffi-dev \
    libgdbm-dev \
    libgdbm-compat-dev \
    liblzma-dev \
    libncurses5-dev \
    libreadline6-dev \
    libsqlite3-dev \
    libssl-dev \
    lzma \
    lzma-dev \
    tk-dev \
    uuid-dev \
    xvfb \
    zlib1g-dev

# Install an HTTP client to download Python.
RUN apt-get install -y wget

# Install Python 3.11.
RUN wget https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz \
    && tar xzf Python-3.11.9.tgz \
    && cd Python-3.11.9 \
    && ./configure --enable-optimizations --enable-shared \
    && make altinstall \
    && cd .. \
    && rm -r Python-3.11.9 Python-3.11.9.tgz

# Install the MNI 7T DICOM to BIDS converter

# Install Git.
RUN apt-get install -y git

# Copy the project directory.
COPY . /mni_7t_dicom_to_bids
WORKDIR /mni_7t_dicom_to_bids

# Install the package and its other dependencies.
RUN pip3.11 install --no-cache-dir git+https://github.com/BIC-MNI/bic-mri-pipeline-util.git
RUN pip3.11 install --no-cache-dir .[dev]

# Run PyInstaller, the executable will be created as `/mni_7t_dicom_to_bids/dist/mni7t_dcm2bids`.
CMD ["pyinstaller", "mni7t_dcm2bids.spec"]
