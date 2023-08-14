FROM node:20.4.0-bullseye

WORKDIR /app

RUN ["npm", "install", "-g", "http-server@14.1.1", "apidoc@1.1.0"]

COPY src/RestApi src/RestApi

RUN node --harmony "$(which apidoc)" -i src/RestApi -o docs

USER www-data
CMD ["http-server", "docs", "--port", "3050"]
