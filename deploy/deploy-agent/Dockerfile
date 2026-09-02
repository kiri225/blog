ARG REGISTRY=docker.1ms.run

FROM ${REGISTRY}/library/docker:27-cli

RUN apk add --no-cache git bash openssh-client

WORKDIR /stack

CMD ["sleep", "infinity"]
