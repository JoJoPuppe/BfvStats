import time
import schedule


start_time = time.time()

def run_every_10_seconds():
    print("Running periodic task!")
    print( "Elapsed time: " + str(time.time() - start_time))

def run_schedule():
    while 1:
        schedule.run_pending()
        time.sleep(1)