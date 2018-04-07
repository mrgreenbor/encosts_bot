
import os 
import json



tg_token = str(os.getenv("TG_TOKEN"))
accounts_tg = json.loads(str(os.getenv("ACCOUNTS_TG")).replace("'", "\""))


amo_apiuserhash = str(os.getenv("AMO_APIUSERHASH"))
amo_apiuser = str(os.getenv("AMO_APIUSER"))
amo_domain = str(os.getenv("AMO_DOMAIN"))



accounts_amo = json.loads(str(os.getenv("ACCOUNTS_AMO")).replace("'", "\""))






