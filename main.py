import config.configscript as data
import mux
import sys
# First, we (kind of) efficiently perform all the sanity checks
# and config passes.
if data.PROD_MODE is True:
    print("[*] Running in production mode... Hello zomka, your server is wishing you well.")
    mux.runner(data.WEBHOOK, data.REGION_LETTER, data.WEBHOOK_PREFIX,
               data.PROD_WHOOK, data.PROD_PUSH,
               data.PROD_DIR, data.REGION_CODE)
elif data.TEST_MODE is True:
    print("[*] Running in test mode... Hello zomka, your server is wishing you well.")
    mux.runner(data.WEBHOOK, data.REGION_LETTER, data.WEBHOOK_PREFIX,
               data.TEST_WHOOK, data.TEST_PUSH,
               data.TEST_DIR, data.REGION_CODE)
# Gracefully exit
sys.exit(0)
