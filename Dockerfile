FROM fedora:34

RUN curl https://packages.codenotary.org/codenotary.repo -o /etc/yum.repos.d/codenotary.repo
RUN mkdir -p /code && \
    yum update -y && \
    yum install --enablerepo="codenotary-repo" cas python3-virtualenv python39 libmodulemd python3-libmodulemd \
                python3-libmodulemd1 modulemd-tools python-gobject git -y && \
    yum clean all
RUN curl https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh -o wait_for_it.sh && chmod +x wait_for_it.sh
COPY requirements.txt /tmp/requirements.txt
COPY install_dependencies.py /tmp/install_dependencies.py
RUN cd /code && virtualenv -p python3.9 --system-site-packages env && source env/bin/activate \
    && python3 /tmp/install_dependencies.py
COPY alws /code/alws
COPY tests /code/tests
WORKDIR /code
CMD ["/bin/bash", "-c", "source env/bin/activate && uvicorn --workers 4 --host 0.0.0.0 alws.app:app"]
