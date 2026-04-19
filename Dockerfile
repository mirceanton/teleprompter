FROM gcr.io/distroless/static-debian12:nonroot
COPY teleprompter /teleprompter
USER 8675:8675
ENTRYPOINT ["/teleprompter"]
