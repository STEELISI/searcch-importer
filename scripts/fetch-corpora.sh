#!/bin/sh

set -x

PYTHON=`which pypy3`
if [ -z "$PYTHON" ]; then
    PYTHON=`which pypy`
fi
if [ -z "$PYTHON" ]; then
    PYTHON=`which python3`
fi
if [ -z "$PYTHON" ]; then
    PYTHON=`which python`
fi
if [ -z "$PYTHON" ]; then
    echo "Error: could not detect python or pypy; aborting"
    exit 1
fi

set -e

$PYTHON -m nltk.downloader stopwords
$PYTHON -m nltk.downloader punkt
$PYTHON -m nltk.downloader universal_tagset
$PYTHON -m spacy download en_core_web_sm

for lang in `ls -1 /root/nltk_data/corpora/stopwords`; do
    fgrep -qrni $lang /usr/local/lib/python3.*/dist-packages/pke \
        || rm -fv /root/nltk_data/corpora/stopwords/$lang
done

curl -o /var/tmp/google-10000-english-no-swears.txt \
    https://github.com/first20hours/google-10000-english/raw/master/google-10000-english-no-swears.txt

exit 0
