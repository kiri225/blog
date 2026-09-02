ARG REGISTRY=docker.1ms.run

FROM ${REGISTRY}/library/alpine:3.20

RUN apk add --no-cache docker-cli git bash openssh-client

WORKDIR /stack

CMD ["sleep", "infinity"]
