import schedule
import time
from backup import create_backup
from datetime import datetime

print("[INFO] Backup scheduler চালু হয়েছে")
print("[INFO] প্রতিদিন রাত ১১টায় backup নেওয়া হবে")

# প্রতিদিন রাত ১১টায় backup নেবে
schedule.every().day.at("23:00").do(create_backup)

while True:
    schedule.run_pending()
    time.sleep(60)