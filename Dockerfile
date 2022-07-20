FROM gcc:12.1.0-bullseye

RUN apt-get update &&\
    apt-get install -y libgsl-dev

ADD . .

RUN ./download_globes.sh

RUN tar -xzvf globes-3.2.18.tar.gz

RUN rm globes-3.2.18.tar.gz

WORKDIR globes-3.2.18

RUN ./configure &&\
    make &&\
    make install
