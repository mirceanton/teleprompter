FROM scratch
COPY teleprompter /teleprompter
ENTRYPOINT ["/teleprompter"]
