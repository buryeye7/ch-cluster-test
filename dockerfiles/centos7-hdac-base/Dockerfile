FROM centos/devtoolset-7-toolchain-centos7

USER root
ENV HOME=/root
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib:/usr/lib:/usr/local/lib64:/usr/lib64
ENV GOPATH=$HOME/go
ENV GOROOT=/usr/local/go
ENV PATH=$PATH:$HOME/.cargo/bin:$GOPATH/bin:$GOROOT/bin
ENV PROTOC_ZIP=protoc-3.7.1-linux-x86_64.zip
WORKDIR $HOME

RUN echo $PATH
RUN echo $LD_LIBRARY_PATH

RUN gcc --version

RUN yum -y upgrade
RUN yum -y update
RUN yum -y install git
RUN yum -y install wget
RUN yum -y install unzip 
RUN yum -y install which
RUN yum -y install epel-release
RUN yum -y install jq
RUN yum -y install bzip2

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs > tmp.sh
RUN chmod 777 tmp.sh
RUN ./tmp.sh -y
RUN /bin/bash -c "source $HOME/.cargo/env"
RUN rustup --version
RUN wget https://dl.google.com/go/go1.13.linux-amd64.tar.gz
RUN sha256sum go1.13.linux-amd64.tar.gz
RUN tar -C /usr/local -xzf go1.13.linux-amd64.tar.gz
RUN curl -OL https://github.com/protocolbuffers/protobuf/releases/download/v3.7.1/$PROTOC_ZIP
RUN unzip -o $PROTOC_ZIP -d /usr/local bin/protoc
RUN unzip -o $PROTOC_ZIP -d /usr/local 'include/*'
RUN rm -f $PROTOC_ZIP
RUN curl -sL https://rpm.nodesource.com/setup_10.x |  bash -
RUN yum -y install nodejs
RUN yum -y install bzip2 


RUN mkdir -p $HOME/go/src
RUN mkdir -p $HOME/go/pkg
RUN mkdir -p $HOME/go/bin

WORKDIR $HOME
RUN wget http://www.cmake.org/files/v3.6/cmake-3.6.1.tar.gz
RUN tar zvxf cmake-3.6.1.tar.gz
WORKDIR $HOME/cmake-3.6.1
RUN ./bootstrap
RUN make
RUN make install
RUN cmake -version
