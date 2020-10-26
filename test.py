import dateparser
from datetime import datetime
import pytz

print(str(dateparser.parse("Oct 5")).split()[0])
print(str(datetime.now(pytz.timezone("America/Denver"))).split()[0])
