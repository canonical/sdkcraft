#!/bin/bash

set -eu

print_help() {
    echo "Usage: $0 <filename> <stable|candidate|beta|edge>"
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

SDK_PATH=$(readlink -f $1)
if [ ! -e "$SDK_PATH" ]; then
    echo "Error: File '$SDK_PATH' not found."
    exit 1
fi

allowed_channels=("stable" "candidate" "beta" "edge")
channel="$2"

if [[ ! " ${allowed_channels[@]} " =~ " $channel " ]]; then
    echo "Error: Second argument should be one of: ${allowed_channels[*]}"
    print_help
    exit 1
fi

CHANNEL=latest/$channel
SDK_FILE=$(basename $1)
SDK_NAME="${SDK_FILE%%.*}"
BUCKET_DIR="gs://sdk-store/$SDK_NAME/$CHANNEL/"

gsutil -h "Cache-Control: no-store" cp $SDK_FILE $BUCKET_DIR
