ARG W4R_CUSTOM_INIT_PYTHON_SCRIPT= $W4R_CUSTOM_INIT_PYTHON_SCRIPT
ARG W4R_INIT_FOLDER= $W4R_INIT_FOLDER

FROM python:3.10-alpine

# bring argument into image
ARG W4R_CUSTOM_INIT_PYTHON_SCRIPT
ARG W4R_INIT_FOLDER

# set current working directory to /app
WORKDIR /app


# install missing dependencies
RUN pip install pandas tqdm rdflib requests wikibaseintegrator python-dotenv

# Install Bash
RUN apk update && apk add --no-cache bash

# Install PHP
RUN apk update && apk add --no-cache php php-cli php-fpm php-mysqli php-json

COPY $W4R_CUSTOM_INIT_PYTHON_SCRIPT /app/custom_init.py
COPY scripts/entrypoint_control.sh /app/entrypoint_control.sh
RUN chmod +x /app/entrypoint_control.sh
ENTRYPOINT ["/app/entrypoint_control.sh"]

CMD ["tail", "-f", "/dev/null"]