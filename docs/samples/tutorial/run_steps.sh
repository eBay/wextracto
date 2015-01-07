#!/bin/sh

for dirname in `ls -d -1 step*`
do
	pushd $dirname > /dev/null
	echo $(basename $(pwd))
	wex http://gilessbrown.github.io/cheeses/cheddar.html
	popd
done
