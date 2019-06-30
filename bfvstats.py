from app import app

import time
from threading import Thread
import schedule
from app.scheduleStats import run_every_10_seconds, run_schedule, start_time



if __name__ == "__main__":

	schedule.every(10).seconds.do(run_every_10_seconds)
	t = Thread(target=run_schedule)
	t.start()
	print( "Start time: " + str(start_time))

	app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
	#app.run(debug=True)