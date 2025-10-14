FROM jrottenberg/ffmpeg:4.4-ubuntu

# small wrapper that will run the watcher script
WORKDIR /work
COPY watch_and_transcode.sh /work/watch_and_transcode.sh
RUN apt-get update && apt-get install -y curl jq && rm -rf /var/lib/apt/lists/*
RUN chmod +x /work/watch_and_transcode.sh

ENTRYPOINT ["/work/watch_and_transcode.sh"]
