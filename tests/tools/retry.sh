retry() {
    max="$1"
    shift
    delay=5

    i=1
    while [ "$i" -le "$max" ]; do
        echo "Attempt $i/$max: $*"
        if "$@"; then
            return 0
        fi

        if [ "$i" -lt "$max" ]; then
            echo "Failed. Sleeping $delay sec..."
            sleep "$delay"
            delay=$((delay * 2))
        fi

        i=$((i + 1))
    done

    echo "Command failed after $max attempts."
    return 1
}
