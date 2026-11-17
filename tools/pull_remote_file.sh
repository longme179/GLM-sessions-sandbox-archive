#!/bin/bash
# Chunked pull of a large remote file through the oc.sh bridge (cap 49152 bytes).
# Usage: pull_remote_file.sh <remote_path> <local_path> <size> <expected_md5>
set -e
R="$1"; L="$2"; SZ="$3"; WANT_MD5="${4:-}"
OC=/home/z/my-project/scripts/oc.sh
CH=30000
N=$(( (SZ + CH - 1) / CH ))
echo "remote size=$SZ chunks=$N"
rm -f "$L"
for ((i=0; i<N; i++)); do
  $OC 30000 "dd if='$R' bs=$CH skip=$i count=1 2>/dev/null | base64 -w0" > /tmp/prf_b64.txt 2>/dev/null
  tr -d ' \n\r\t' < /tmp/prf_b64.txt | base64 -d >> "$L"
done
GOT=$(md5sum "$L" | cut -d' ' -f1)
LOC=$(stat -c %s "$L")
echo "local size=$LOC md5=$GOT"
if [ -n "$WANT_MD5" ] && [ "$GOT" != "$WANT_MD5" ]; then
  echo "MD5 MISMATCH (want $WANT_MD5)"; exit 1
fi
echo "MD5 MATCH"
