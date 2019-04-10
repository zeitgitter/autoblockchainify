#!/bin/bash -e
# Test basic key import and tag timestamping
h="$PWD"
d=$1
shift
cd "$d"

# Init GNUPG
export GNUPGHOME="$d/gnupg"
mkdir -m 700 "$GNUPGHOME"

# Init GIT
git init
echo $RANDOM > a.txt
git add a.txt
git commit -m "Random change $RANDOM"
tagid=v$RANDOM
$h/git-timestamp.py --tag $tagid --server https://gitta.enotar.ch

# Check key import
if ! gpg --list-keys | grep -q 9C67D18C5119896C35FE3E0D8A0B0941E7C49D65; then
	echo "Key 9C67D18C5119896C35FE3E0D8A0B0941E7C49D65 not imported" >&2
	exit 1
fi

# Check config
tail -3 $d/.git/config > $d/10-tag-config-real.txt
cat > $d/10-tag-config-verify.txt << EOF
[timestamper "gitta-enotar-ch"]
	keyid = 8A0B0941E7C49D65
	name = Gitta Timestamping Service <gitta@enotar.ch>
EOF
diff $d/10-tag-config*.txt

# Check tag existence
if [ 1 -ne `git tag | wc -l` ]; then
	echo "Found `git tag | wc -l` tags instead of 1" >&2
	exit 1
fi
if ! git tag | grep -q "^$tagid$"; then
	echo "Tag $tagid does not match `git tag`" >&2
	exit 1
fi

# Check tag signature
git tag -v $tagid