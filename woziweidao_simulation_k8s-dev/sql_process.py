import pymysql
import time
import datetime
from setup import Card 
from apscheduler.schedulers.blocking import BlockingScheduler
scheduler = BlockingScheduler() 

def cleandb(prop, interval=1):
  db = pymysql.connect(
  host = '192.168.17.93',
  user = 'root',
  password = '1111',
  db = 'csv_sql',
  port = 3306,
  charset = 'utf8'
  )
  print('test one time')
  now_time = datetime.datetime.now()
  print('prop', prop)
  new_t = (now_time + datetime.timedelta(minutes=-20)).strftime("%Y-%m-%d %H:%M:%S")
  # print('new_t', new_t)
  select_stmt = "DELETE FROM {} WHERE task_id not in (SELECT task_id FROM celery_taskmeta WHERE date_done >= %(time)s)".format(prop)

  cursor = db.cursor()
  data = cursor.execute(select_stmt, {'time':new_t, 'prop':prop})
  if data:
    all_data = cursor.fetchall()
    print('data', data)
  # new_list = [list(i)[0] for i in all_data]
  # print('new_list', new_list)
    print('one', type(all_data), list(all_data))
    db.commit()
  if db:
    db.close()

def test():
  for prop in properties:
    cleandb(prop.lower())
    
  print('this is a schedule test')

card = Card()
properties = card.properties
scheduler.add_job(test, 'interval', seconds=10)
scheduler.start()