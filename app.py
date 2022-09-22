import os

from flask import Flask, request, make_response
from sqlalchemy import and_, create_engine
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

from waitress import serve

username = 'root'
password = 'CFBF5117CBF5A6802F7E2A'
host = '127.0.0.1'
database = '1010gps'
port = '3321'

database_url = 'mysql+pymysql://' + username + ':' + password + '@' + \
               host + ':' + port + '/' + database
engine = create_engine(database_url)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(15)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Counter(db.Model):
    dt = datetime.now() + timedelta(hours=6)
    __tablename__ = 'dev_alarm_' + dt.strftime('%Y%m')

    guid = db.Column('Guid', db.String, primary_key=True)
    vehicle = db.Column('DevIDNo')
    alarm_time = db.Column('ArmTime', db.DateTime)
    alarm_type = db.Column('ArmType', db.Integer)
    alarm_info = db.Column('ArmInfo', db.Integer)
    alarm_desc = db.Column('ArmDesc', db.String)
    latitude = db.Column('WeiDu', db.Integer)
    longitude = db.Column('JingDu', db.Integer)

    def __repr__(self):
        return f'<Counter(bus: {self.vehicle}, alarm_time: {self.alarm_time}>)'


@app.route('/passenger-data', methods=['GET'])
def get_data_by_time():
    # Passenger counter is ArmType == 232
    # if ArmInfo == 15, second value of ArmDesc is passenger in
    # passenger out is third value, and 7th value is total people
    bus_no = []
    in_count = []
    out_count = []
    no_people = []
    alarm = []
    gnss = []
    args = request.args
    dt = datetime.strptime(args['time'], '%Y-%m-%d %H:%M:%S') + timedelta(hours=6)

    counter = Counter.query.filter(and_(Counter.alarm_time > dt, Counter.alarm_type == 232)).all()

    for i in range(len(counter)):
        bus = int(counter[i].vehicle)
        pass_data = counter[i].alarm_desc.split(',')
        alarm_t = counter[i].alarm_time - timedelta(hours=6)
        alarm_ts = alarm_t.strftime('%Y-%m-%d %H:%M:%S')
        if counter[i].alarm_info == 15:
            in_c = int(pass_data[1])
            out_c = int(pass_data[2])
            in_count.append(in_c)
            out_count.append(out_c)
        elif counter[i].alarm_info != 15:
            in_c = int(pass_data[2])
            out_c = int(pass_data[3])
            in_count.append(in_c)
            out_count.append(out_c)
        total_c = int(pass_data[6])
        gnss_str = f'{counter[i].latitude},{counter[i].longitude}'

        bus_no.append(bus)
        no_people.append(total_c)
        alarm.append(alarm_ts)
        gnss.append(gnss_str)

    data = {'Bus No': bus_no, 'IN': in_count, 'Out': out_count,
            'Number of people': no_people, 'Alarm Time': alarm, 'GNSS': gnss}

    return make_response(data)


serve(app, host='0.0.0.0', port=5555, threads=1)
