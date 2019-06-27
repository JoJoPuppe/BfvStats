from app import app
from flask import render_template
import json
import uuid
import requests
from app.models import PlayerStatsTable, FireStormTable
from app import db
from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy.sql import collate
from datetime import datetime, timedelta
import pytz


#from app.dummyData import data_01,data_02,data_03,data_04,data_05,data_06,data_07,data_08,data_09, last_week_data_01, last_week_data_02, last_week_data_03

#from models import Member

@app.route("/")
def index():
	user = {'username': 'Miguel'}
	#StatsTable = db.session.query(PlayerStatsTable).all()
	StatsTable = PlayerStatsTable.query.all()
	StatsTable_dict = dict((col, getattr(PlayerStatsTable, col)) for col in PlayerStatsTable.__table__.columns.keys())

	return render_template('index.html', title='Home', user=user, TableBody=StatsTable, TableHeader = StatsTable_dict)

@app.route("/week")
def week():

	currentWeek = datetime.today().strftime("%V")
	lastWeek = str(int(currentWeek)-1)

	WeeklyStats = db.session.query(PlayerStatsTable, func.max(PlayerStatsTable.TimeStamp)).filter(PlayerStatsTable.KW == currentWeek).group_by(PlayerStatsTable.playerName).order_by(collate(PlayerStatsTable.playerName, 'NOCASE'),PlayerStatsTable.id.desc()).all()
	lastWeekStats = db.session.query(PlayerStatsTable, func.max(PlayerStatsTable.TimeStamp)).filter(PlayerStatsTable.KW == lastWeek).group_by(PlayerStatsTable.playerName).order_by(collate(PlayerStatsTable.playerName, 'NOCASE'),PlayerStatsTable.id.desc()).all()
	WeeklyFireStats = db.session.query(FireStormTable, func.max(FireStormTable.TimeStamp)).filter(FireStormTable.KW == currentWeek).group_by(FireStormTable.playerName).order_by(collate(FireStormTable.playerName, 'NOCASE'),FireStormTable.id.desc()).all()
	lastWeekFireStats = db.session.query(FireStormTable, func.max(FireStormTable.TimeStamp)).filter(FireStormTable.KW == lastWeek).group_by(FireStormTable.playerName).order_by(collate(FireStormTable.playerName, 'NOCASE'),FireStormTable.id.desc()).all()


	def percent(a,b):
		return round((a/b*100),2) if b else 0

	def performancePerMin(playTime, stat):
		return round(stat/(playTime//60),2) if playTime else 0

	BaseStats = []

	for i in range(0,len(WeeklyStats)):
		for j in range(0,len(lastWeekStats)):
			if WeeklyStats[i][0].playerName == lastWeekStats[j][0].playerName:
				BaseStats.append(lastWeekStats[j])
		if len(BaseStats) != (i+1):
			lastCurrentWeekStat = db.session.query(PlayerStatsTable, func.min(PlayerStatsTable.TimePlayed)).filter(PlayerStatsTable.playerName == WeeklyStats[i][0].playerName ,PlayerStatsTable.KW == currentWeek).group_by(PlayerStatsTable.playerName).first()
			BaseStats.append(lastCurrentWeekStat)

	FireStats = []

	for i in range(0,len(WeeklyFireStats)):
		for j in range(0,len(lastWeekFireStats)):
			if WeeklyFireStats[i][0].playerName == lastWeekFireStats[j][0].playerName:
				FireStats.append(lastWeekFireStats[j])
		if len(FireStats) != (i+1):
			lastCurrentWeekStat = db.session.query(FireStormTable, func.min(FireStormTable.TimePlayed)).filter(FireStormTable.playerName == WeeklyFireStats[i][0].playerName ,FireStormTable.KW == currentWeek).group_by(FireStormTable.playerName).first()
			FireStats.append(lastCurrentWeekStat)

	firstDayOfWeek = datetime.today()

	start = firstDayOfWeek - timedelta(days=firstDayOfWeek.weekday())
	end = start + timedelta(days=6)

	WeekStartEnd = [start.strftime('%d-%b-%Y'), end.strftime('%d-%b-%Y')]


	cet = pytz.timezone('CET')

	timeDiffDict = {}


	for i in range(0,len(WeeklyStats)):
		timestr = WeeklyStats[i][0].lastUpdated
		timestr2 = lastWeekStats[i][0].lastUpdated
		currentTime = datetime.strptime(timestr, '%Y-%m-%dT%H:%M:%SZ')
		timeSinceUpdate = datetime.strptime(timestr2, '%Y-%m-%dT%H:%M:%SZ')
		timeDiff = (currentTime-timeSinceUpdate).total_seconds()
		print(timeDiff)
		hours, seconds = timeDiff // 3600, timeDiff%3600
		minutes = seconds // 60
		timeDiffString = str(int(hours)) + "h:" + str(int(minutes)) + "m"
		timeDiffDict[WeeklyStats[i][0].playerName] = timeDiffString
		offset = cet.utcoffset(currentTime, is_dst = True)
		currentTime += offset
		timeSinceUpdate += offset
		WeeklyStats[i][0].lastUpdated = currentTime.strftime('%d-%m/%H:%M')
		BaseStats[i][0].lastUpdated = timeSinceUpdate.strftime('%d-%m/%H:%M')
		
	performanceDict = []
	percentDict = []
	for i in WeeklyStats:
		percentDict.append(dict())
		performanceDict.append(dict())

	for key, value in WeeklyStats[0][0].__dict__.items():
		if type(value) is (int or float):
			weeklyPercent = []

			for i in range(0,len(WeeklyStats)):
				

				diff = getattr(WeeklyStats[i][0],key) - getattr(BaseStats[i][0],key)
			
				weeklyPercent.append(diff)

			maxVal = max(weeklyPercent)
			
			for j in range(0,len(WeeklyStats)):
				diffTime = WeeklyStats[j][0].TimePlayed - BaseStats[j][0].TimePlayed

				percentDict[j][key] = percent(weeklyPercent[j], maxVal)
				performanceDict[j][key] = performancePerMin(diffTime, weeklyPercent[j])
		else:
			print("no int or float")
				
	

	print(performanceDict)

		


	#arrNew = {}

	#maxVal = max(arr.values())

	#for key, value in arr.items():
	#    arrNew[key] = round((value / maxVal * 100),2)
	
	


	return render_template('week.html', WeeklyStats = WeeklyStats, BaseStats=BaseStats, WeeklyFireStats=WeeklyFireStats, FireStats=FireStats, WeekStartEnd=WeekStartEnd, timeDiffDict=timeDiffDict, percentDict=percentDict, performanceDict=performanceDict)

@app.route("/playerstats/<player>")
def player():

	currentWeek = datetime.today().strftime("%V")
	lastWeek = str(int(currentWeek)-1)

	dailyStats = db.session.query(PlayerStatsTable).filter(PlayerStatsTable.playerName == player, PlayerStatsTable.KW == currentWeek).order_by(PlayerStatsTable.id.desc()).all()
	#lastWeekStats = db.session.query(PlayerStatsTable, func.max(PlayerStatsTable.TimePlayed)).filter(PlayerStatsTable.KW == lastWeek).group_by(PlayerStatsTable.playerName).order_by(collate(PlayerStatsTable.playerName, 'NOCASE'),PlayerStatsTable.id.desc()).all()

	#BaseStats = [];

	#for i in range(0,len(WeeklyStats)):
	#	for j in range(0,len(lastWeekStats)):
	#		if WeeklyStats[i][0].playerName == lastWeekStats[j][0].playerName:
	#			BaseStats.append(lastWeekStats[j])
	#	if len(BaseStats) != (i+1):
	#		lastCurrentWeekStat = db.session.query(PlayerStatsTable, func.min(PlayerStatsTable.TimePlayed)).filter(PlayerStatsTable.playerName == WeeklyStats[i][0].playerName ,PlayerStatsTable.KW == currentWeek).group_by(PlayerStatsTable.playerName).first()
	#		BaseStats.append(lastCurrentWeekStat)

	#print(WeeklyStats)
	#print(BaseStats)


	#StatsTable_dict = dict((col, getattr(PlayerStatsTable, col)) for col in PlayerStatsTable.__table__.columns.keys())

	return render_template('player.html', dailyStats=dailyStats, currentWeek=currentWeek)



@app.route("/about")
def about():
	
	return "<h1 style='color: red'> About</h1>"


@app.route('/get')
def getBFVdata():

	def getTrackerData(Displayname):

		url = 'https://api.battlefieldtracker.com/api/v1/bfv/profile/psn/' + Displayname
		headers = {'Accept': 'application/json','Accept-Encoding': 'gzip', }
		APIrequest = requests.get(url, headers=headers)
		Stats = json.loads(APIrequest.text)

		statsFireStorm = Stats['data']['statsFirestorm']
		statsMultiplayer = Stats['data']['stats']

		PlayerStats = {}
		FireStormStats = {}

		PlayerStats['apiLastChecked'] = Stats['data']['account']['apiLastChecked']
		PlayerStats['lastUpdated'] = Stats['data']['stats']['lastUpdated']
		PlayerStats['playerName'] = Stats['data']['account']['playerName']



		for key, value in PlayerStats.items():
			FireStormStats[key] = value

		#getLastUpdate = PlayerStatsTable.query.filter(PlayerStatsTable.lastUpdated)
		exists = db.session.query(db.session.query(PlayerStatsTable).filter_by(lastUpdated=PlayerStats['lastUpdated'], playerName=PlayerStats['playerName']).exists()).scalar()
		#playerLastUpdate = db.session.query(PlayerStatsTable).filter_by(lastUpdated=PlayerStats['lastUpdated'], playerName=PlayerStats['playerName']).all()
		#exists = PlayerStatsTable.query(PlayerStatsTable.query.filter(and_(PlayerStatsTable.lastUpdated = PlayerStats['lastUpdated'], PlayerStatsTable.playerName=PlayerStats['playerName'])).exists()).scalar()

		

		if exists:
			print("keine updates vorhanden")
		else:
			for x in statsMultiplayer:
			    item = statsMultiplayer[x]
			    if type(item) is dict:
			        if 'value' in item:
			            PlayerStats[item['key']] = item['value']

			for y in statsFireStorm:
				item = statsFireStorm[y]
				if type(item) is dict:
				    if 'value' in item:
				       	FireStormStats[item['key']] = item['value']





			#print(PlayerStats)
			
			Player = PlayerStatsTable(**PlayerStats)
			FireStormPlayer = FireStormTable(**FireStormStats)
			db.session.add(Player)
			db.session.add(FireStormPlayer)
			db.session.commit()

	getTrackerData('jojopuppe')
	getTrackerData('dlt_orko')
	getTrackerData('neuner_eisen')
	getTrackerData('Topperinski')
	#getTrackerData('M4URiC3-HRO')
	

	return "<h1 style='color: red'> About</h1>"

#@app.route('/dummy')
#def getDummyData():
#
#	lw1 = PlayerStatsTable(**last_week_data_01)
#	lw2 = PlayerStatsTable(**last_week_data_02)
#	lw3 = PlayerStatsTable(**last_week_data_03)
#
#	db.session.add(lw1)
#	db.session.add(lw2)
#	db.session.add(lw3)
#
#	db.session.commit()
#
#
#
#	return "<h1 style='Blue: red'> DummyData</h1>"