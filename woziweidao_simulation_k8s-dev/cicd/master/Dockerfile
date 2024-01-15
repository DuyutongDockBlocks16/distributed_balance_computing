FROM harbor-pull.mgr.jjweb.cn/jenkins-dev/python3.6-tf:whl-1.10.0

ENV DEBIAN_FRONTEND noninteractive
ENV TIME_ZONE Asia/Shanghai

WORKDIR /app

# add app
ADD . /app

# set working directory
RUN mkdir -p /app/logs && mkdir -p /data/logs/ \
    && sed -i 's#security.ubuntu#mirrors.aliyun#g' /etc/apt/sources.list \
    && sed -i 's#archive.ubuntu#mirrors.aliyun#g' /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y openssh-server tzdata \
    && echo "${TIME_ZONE}" > /etc/timezone \
    && ln -sf /usr/share/zoneinfo/${TIME_ZONE} /etc/localtime \
    && pip install --upgrade pip \
    && cp test/libtolua.so /usr/lib/ \
    && pip install test/lupa-1.10-cp36-cp36m-linux_x86_64.whl

# install requirements
RUN pip install -i https://pypi.srv.jj.cn/simple/ -r requirements/prod.txt || \
    if [ $? -ne 0 ]; then \
        pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements/prod.txt ; \
    fi

CMD ["/bin/bash", "/app/entrypoint/master.sh"]
