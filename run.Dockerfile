FROM python:3.11-slim

# Install the installation dependencies.
RUN apt-get update && apt-get install -y curl git unzip

# Install the latest version of `dcm2niix`.
RUN curl -fLO https://github.com/rordenlab/dcm2niix/releases/latest/download/dcm2niix_lnx.zip
RUN unzip dcm2niix_lnx.zip -d /usr/bin

# Copy the project directory.
COPY . /mni_7t_dicom_to_bids
WORKDIR /mni_7t_dicom_to_bids

# Install the package and its other dependencies.
RUN pip install --no-cache-dir git+https://github.com/BIC-MNI/bic-mri-pipeline-util.git
RUN pip install --no-cache-dir .

CMD ["mni_7t_dicom_to_bids"]
