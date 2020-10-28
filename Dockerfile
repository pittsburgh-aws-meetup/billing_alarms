FROM python:3.9

RUN curl -sL https://deb.nodesource.com/setup_14.x | bash - && apt-get install -y nodejs
RUN npm install -g aws-cdk
RUN mkdir src
WORKDIR src
COPY ./ /src/
RUN pip install -r requirements.txt

CMD /bin/bash