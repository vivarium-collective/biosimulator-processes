# TODO: Make this work for Smoldyn to be platform-agnostic

FROM ubuntu:22.04

# Implement the next two lines for use in Cloud
# RUN useradd -m simuser

# USER simuser

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y \
    wget \
    # Add any other dependencies required by smoldyn
    && rm -rf /var/lib/apt/lists/*

# Download the smoldyn .deb package
RUN wget https://download.opensuse.org/repositories/home:/dilawar/xUbuntu_22.04/amd64/smoldyn_2.64.4-1+2.1_amd64.deb

# Install the downloaded package
RUN dpkg -i smoldyn_2.64.4-1+2.1_amd64.deb

# Set environment variables to avoid user interaction during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Update package lists and install Python 3 and pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Optional: Create a symlink for python and pip if you want to use `python` and `pip` commands directly
RUN ln -s /usr/bin/python3 /usr/bin/python

#RUN pip install --upgrade pip \
    #&& pip install ipython \
    #&& pip install .

CMD ["ipython3"]
