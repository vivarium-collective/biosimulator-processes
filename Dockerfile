# TODO: Make this work for Smoldyn to be platform-agnostic

FROM python:3.10-bullseye

# Implement the next two lines for use in Cloud
# RUN useradd -m simuser

# USER simuser

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    && rm -rf /var/lib/apt/lists/*

RUN echo 'deb http://download.opensuse.org/repositories/home:/dilawar/Debian_11/ /' | tee /etc/apt/sources.list.d/home:dilawar.list
RUN curl -fsSL https://download.opensuse.org/repositories/home:dilawar/Debian_11/Release.key | gpg --dearmor | tee /etc/apt/trusted.gpg.d/home_dilawar.gpg > /dev/null
RUN apt update
RUN apt install smoldyn

RUN pip install --upgrade pip \
    && pip install . ipython
    # && pytest

CMD ["ipython3"]
