#! /bin/bash
# gets and expands the timezone data for flot

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $DIR

DESTDIR="../static/tz"
if [[ -e $DESTDIR ]]; then
   echo 'timezones already loaded'
   exit
fi

echo 'making $DESTDIR'
mkdir -p $DESTDIR

echo 'curling'
curl ftp://ftp.iana.org/tz/tzdata-latest.tar.gz -o $DESTDIR/tzdata-latest.tar.gz

echo 'untarring'
tar -xvzf $DESTDIR/tzdata-latest.tar.gz -C $DESTDIR

#echo 'cleaning up'
rm $DESTDIR/tzdata-latest.tar.gz

echo 'success'

