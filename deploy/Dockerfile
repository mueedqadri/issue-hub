# Build from the repository root: docker build -f deploy/Dockerfile -t issue-board .
FROM python:3.13.7-alpine3.22
RUN apk add --no-cache git
COPY skills /app/skills
COPY --chmod=755 deploy/run.sh /usr/local/bin/issue-board
USER 1000:1000
EXPOSE 8788
ENTRYPOINT ["/usr/local/bin/issue-board"]
