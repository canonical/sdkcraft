#!/bin/bash

set -eu

print_help() {
    echo "Usage: $0 <filename> <track>/<stable|candidate|beta|edge>"
    echo "Example: $0 my-sdk.sdk latest/beta"
}

print_installation_instructions() {
    echo "To install gsutil, follow the instructions at:"
    echo "https://cloud.google.com/storage/docs/gsutil_install"
}

# Check if gsutil is installed
if ! command -v gsutil &> /dev/null; then
    echo "Error: gsutil is not installed."
    print_installation_instructions
    exit 1
fi

# Verify the number of arguments
if [ "$#" -ne 2 ]; then
    echo "Error: Incorrect number of arguments."
    print_help
    exit 1
fi

SDK_PATH=$(readlink -f "$1")
if [ ! -e "$SDK_PATH" ]; then
    echo "Error: File '$SDK_PATH' not found."
    exit 1
fi

re='^[a-z0-9]*/(stable|candidate|beta|edge)$'
channel="$2"

# shellcheck disable=SC2076
if [[ ! "$channel" =~ $re ]]; then
    echo "Error: channel must match regex: ${re}"
    print_help
    exit 1
fi

SDK_FILE=$(basename "$1")
SDK_NAME="${SDK_FILE%%.*}"
BUCKET_DIR="gs://sdk-store/$SDK_NAME/$channel/"

echo "Uploading $SDK_FILE to $BUCKET_DIR..."
gsutil -h "Cache-Control: no-store" cp "$SDK_FILE" "$BUCKET_DIR"

echo "Publishing SDK meta data..."
meta=$(tar -xOf "$SDK_FILE" ./meta/sdk.yaml | yq -r -o=j -I=0)
gcloud storage objects update "$BUCKET_DIR""$SDK_FILE" --custom-metadata=^DELIM^sdk-yaml="$meta"
