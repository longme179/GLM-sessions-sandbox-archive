#!/usr/bin/env bash
# Several S1/S3 runs one after another on the host; each argument is MODE:TREE:LABEL.
# The output of each run is kept in /tmp/vis_batch-<LABEL>.log on the host and echoed here.
set -u
for spec in "$@"; do
  IFS=: read -r MODE TREE LABEL <<< "$spec"
  echo "=== $LABEL ($MODE) started $(date +%T)"
  MODE="$MODE" TREE="$TREE" LABEL="$LABEL" bash /tmp/vis_run_s1s3.sh > "/tmp/vis_batch-$LABEL.log" 2>&1
  tail -20 "/tmp/vis_batch-$LABEL.log"
done
echo "BATCH_DONE $(date +%T)"
