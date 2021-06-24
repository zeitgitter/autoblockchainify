#!/bin/sh
# Are we probably called with parameters for the real test?
# - "-c tests/mailtest.conf" option
# - Existence of `tests/mailtest.conf`
# - Lack of `stamper-from`/`stamper-to` options therein
if echo "$EXTRA_DAEMONPARAMS" | grep tests/mailtest.conf; then
  if [ -r tests/mailtest.conf ]; then
    if ! grep ^stamper-from tests/mailtest.conf; then
      if ! grep ^stamper-to tests/mailtest.conf; then
        echo "$0: Assuming external mail test, letting this run for 30 minutes"
        sleep 1800
        exit 0
      fi
    fi
  fi
fi
echo "$0: Daemon not running external mail; skipping test"
exit 0
