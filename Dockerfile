FROM python:3.9

WORKDIR /bmrs_api

COPY requirements.txt /bmrs_api/requirements.txt

RUN apt-get -qq update && apt-get -qq install -y \
    curl \
    git \
    wget \
    > /dev/null

RUN pip install --no-cache-dir git+https://github.com/SheffieldSolar/Elexon-BMRS-API.git@0.1 > /dev/null

CMD ["bmrs_api", "-h"]
