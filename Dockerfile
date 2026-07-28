FROM python:3.11-slim

# Install the installation dependencies.
RUN apt-get update && apt-get install -y git

# Copy the project directory.
COPY . /mni_7t_dicom_to_bids
WORKDIR /mni_7t_dicom_to_bids

# Install the package and its dependencies.
RUN pip install --no-cache-dir .

# Define the converter as the entrypoint.
ENTRYPOINT ["mni7t_dcm2bids"]
