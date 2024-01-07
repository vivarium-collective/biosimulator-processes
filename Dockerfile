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


# RUN apt-get update && apt-get install -y \
#     build-essential \
#     wget \
#     libgl1-mesa-dev \
#     libglu1-mesa-dev \
#     # && rm -rf /var/lib/apt/lists/*

# RUN echo 'deb http://download.opensuse.org/repositories/home:/dilawar/Debian_11/ /' | tee /etc/apt/sources.list.d/home:dilawar.list
# RUN curl -fsSL https://download.opensuse.org/repositories/home:dilawar/Debian_11/Release.key | gpg --dearmor | tee /etc/apt/trusted.gpg.d/home_dilawar.gpg > /dev/null
# RUN apt update
# RUN apt install smoldyn

RUN pip install --upgrade pip \
    && pip install ipython \
    && pip install .

CMD ["ipython3"]
