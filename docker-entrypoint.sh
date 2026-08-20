#!/bin/sh
set -eu

# The sleep is needed to make rlwrap work. Without the sleep rlwrap
# can't determine the terminal dimensions.
sleep 0.1
exec rlwrap python -m gdpr_api_tester
