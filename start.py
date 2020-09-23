from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_bootstrap import Bootstrap
import pandas as pd

from Forms import LoginForm


app = Flask(__name__)
Bootstrap(app)
app.secret_key = 's0m3k3y'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:fg67klbn0@172.16.14.196:3306/s11'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class OrgStructure(db.Model):
    __tablename__ = 'OrgStructure'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    type = db.Column(db.Integer, nullable=False)


class Client(db.Model):
    __tablename__ = 'Client'
    id = db.Column(db.Integer, primary_key=True)
    lastName = db.Column(db.String(30), nullable=False)
    firstName = db.Column(db.String(30), nullable=False)
    patrName = db.Column(db.String(30), nullable=False)
    birthDate = db.Column(db.DateTime, nullable=False)


class Event(db.Model):
    __tablename__ = 'Event'
    id = db.Column(db.Integer, primary_key=True)
    eventType_id = db.Column(db.Integer, nullable=False)
    externalId = db.Column(db.String(30), nullable=False)
    setDate = db.Column(db.DateTime, nullable=False)
    deleted = db.Column(db.Integer, nullable=False)

    client_id = db.Column(db.Integer, db.ForeignKey('Client.id'), nullable=False)
    client = db.relationship('Client', backref=db.backref('Events', lazy=True))


class Action(db.Model):
    __tablename__ = 'Action'
    id = db.Column(db.Integer, primary_key=True)
    actionType_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Integer, nullable=False)
    deleted = db.Column(db.Integer, nullable=False)

    event_id = db.Column(db.Integer, db.ForeignKey('Event.id'), nullable=False)
    event = db.relationship('Event', backref=db.backref('Actions', lazy=True))
    # actionType_id = db.Column(db.Integer, db.ForeignKey('ActionType.id', nullable=False))
    # actionType = db.relationship('ActionType', backref=db.backref('Actions', lazy=True))


class PlanOfOperation(db.Model):
    __tablename__ = 'PlanOfOperation'
    id = db.Column(db.Integer, primary_key=True)
    idx = db.Column(db.Integer, default=0, nullable=False)
    createDate = db.Column(db.DateTime, default=datetime.now(), nullable=False)
    dateOperation = db.Column(db.DateTime, nullable=False)
    externalId = db.Column(db.String(30), nullable=False)
    client_id = db.Column(db.Integer, nullable=False)
    age = db.Column(db.String(30), nullable=False)
    orgStruct_id = db.Column(db.Integer, nullable=False)
    diagnoz = db.Column(db.Text, nullable=True)
    operation = db.Column(db.Text, nullable=True)
    hirurg1 = db.Column(db.Integer, nullable=True)
    hirurg2 = db.Column(db.Integer, nullable=True)
    hirurg3 = db.Column(db.Integer, nullable=True)
    anestexiolog = db.Column(db.Integer, nullable=True)
    transfuziolog = db.Column(db.Integer, nullable=True)
    numbOperBlock = db.Column(db.String(30), nullable=True)


def get_externals():
    extArray = []
    externalsId = db.engine.execute("""
            SELECT Event.externalId AS Event_externalId,
            CONCAT(Client.lastName, ' ', LEFT(Client.firstName, 1), '.', LEFT(Client.patrName, 1), '.') 
            AS Client_FIO,
            CONCAT((YEAR(CURRENT_DATE()) - YEAR(Client.birthDate)) - if (DAYOFYEAR(CURRENT_DATE()) > 
            DAYOFYEAR(Client.birthDate),0,1), ' лет ', (IF(MONTH(CURRENT_DATE()) - MONTH(Client.birthDate) < 0, 
            MONTH(CURRENT_DATE()) - MONTH(Client.birthDate) + 12, MONTH(CURRENT_DATE()) - MONTH(Client.birthDate))), 
            ' мес.') AS Client_AGE
            FROM Event
            JOIN Action ON Action.event_id = Event.id
            JOIN Client ON Event.client_id = Client.id
            WHERE Event.deleted = 0 
              AND Action.deleted = 0 
              AND Action.status = 0 
              AND Action.actionType_id = 113 
              AND Event.setDate >= CONCAT((year(CURDATE())-1), '-01-01 00:00:00')
              and Event.eventType_id in (62, 72, 79, 73, 80, 78, 97)""")
    for external in externalsId:
        extArray.append({'Event_externalId': external['Event_externalId'], 'Client_FIO': external['Client_FIO'],
                         'Client_AGE': external['Client_AGE']})
    externalsId.close()
    return extArray


def get_hirurg_list(selectDep):
    hirurgArray = []
    hirurgList = db.engine.execute("""
            SELECT id, 
            CONCAT(lastName, ' ', LEFT(firstName,1),'.', LEFT(patrName,1),'.') fio 
            FROM Person 
            WHERE orgStructure_id = %s
            and retireDate is null 
            and speciality_id not in (107, 66, 67) 
            group by 2""", (int(selectDep),))
    for hirurg in hirurgList:
        hirurgArray.append({'id': hirurg['id'], 'fio': hirurg['fio']})
    hirurgList.close()
    return hirurgArray


def get_anesteziolog_list():
    anesteziologArray = []
    anesteziologList = db.engine.execute("""
            SELECT id, 
            CONCAT(lastName, ' ', LEFT(firstName,1),'.', LEFT(patrName,1),'.') fio 
            FROM Person 
            WHERE speciality_id = 4 
            and retireDate is null 
            group by 2""")
    for anesteziolog in anesteziologList:
        anesteziologArray.append({'id': anesteziolog['id'], 'fio': anesteziolog['fio']})
    anesteziologList.close()
    return anesteziologArray


def get_oper_list(operDate_query, selectDep):
    importData = []
    dataTable = db.engine.execute("""
            SELECT DATE_FORMAT(dateOperation, '%d.%m.%Y') "Дата операции",
            externalId "Номер ИБ",
            CONCAT(c.lastName, ' ', LEFT(c.firstName,1),'.', LEFT(c.patrName,1),'.') "ФИО",
            age "Возраст",
            diagnoz "Диагноз",
            operation "Операция",
            IF(CONCAT(hirurg1.lastName, ' ', LEFT(hirurg1.firstName,1),'.', LEFT(hirurg1.patrName,1),'.') is null, '', 
            CONCAT(hirurg1.lastName, ' ', LEFT(hirurg1.firstName,1),'.', LEFT(hirurg1.patrName,1),'.')) "Хирург 1",
            IF(CONCAT(hirurg2.lastName, ' ', LEFT(hirurg2.firstName,1),'.', LEFT(hirurg2.patrName,1),'.') is null, '', 
            CONCAT(hirurg2.lastName, ' ', LEFT(hirurg2.firstName,1),'.', LEFT(hirurg2.patrName,1),'.')) "Хирург 2",
            IF(CONCAT(hirurg3.lastName, ' ', LEFT(hirurg3.firstName,1),'.', LEFT(hirurg3.patrName,1),'.') is null, '', 
            CONCAT(hirurg3.lastName, ' ', LEFT(hirurg3.firstName,1),'.', LEFT(hirurg3.patrName,1),'.')) "Хирург 3",
            IF(CONCAT(anesteziolog.lastName, ' ', LEFT(anesteziolog.firstName,1),'.', LEFT(anesteziolog.patrName,1),'.') 
            IS NULL, '', CONCAT(anesteziolog.lastName, ' ', LEFT(anesteziolog.firstName,1),'.', 
            LEFT(anesteziolog.patrName,1),'.')) "Анестезиолог",
            IF(CONCAT(transfuziolog.lastName, ' ', LEFT(transfuziolog.firstName,1),'.', LEFT(transfuziolog.patrName,1),'.') 
            IS NULL, '', CONCAT(transfuziolog.lastName, ' ', LEFT(transfuziolog.firstName,1),'.', 
            LEFT(transfuziolog.patrName,1),'.')) "Трансфузиолог",
            numbOperBlock "Операционная"
            FROM PlanOfOperation poo
            LEFT JOIN Client c ON poo.client_id = c.id
            LEFT JOIN Person hirurg1 ON poo.hirurg1 = hirurg1.id
            LEFT JOIN Person hirurg2 ON poo.hirurg2 = hirurg2.id
            LEFT JOIN Person hirurg3 ON poo.hirurg3 = hirurg3.id
            LEFT JOIN Person anesteziolog ON poo.anestziolog = anesteziolog.id
            LEFT JOIN Person transfuziolog ON poo.transfuziolog = transfuziolog.id
            where poo.deleted = 0
            and dateOperation = %s
            and orgStruct_id = %s
            order by idx asc""", (operDate_query, int(selectDep),))
    for dataRow in dataTable:
        importData.append({'Дата операции': dataRow['Дата операции'],
                           'Номер ИБ': dataRow['Номер ИБ'],
                           'ФИО': dataRow['ФИО'],
                           'Возраст': dataRow['Возраст'],
                           'Диагноз': dataRow['Диагноз'],
                           'Операция': dataRow['Операция'],
                           'Хирург 1': dataRow['Хирург 1'],
                           'Хирург 2': dataRow['Хирург 2'],
                           'Хирург 3': dataRow['Хирург 3'],
                           'Анестезиолог': dataRow['Анестезиолог'],
                           'Трансфузиолог': dataRow['Трансфузиолог'],
                           'Операционная': dataRow['Операционная']})
    dataTable.close()
    return importData


@app.route('/', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    form.departName.choices = [(org.id, org.name) for org in OrgStructure.query.filter_by(type=1).all()]
    if form.is_submitted():
        externalsID = get_externals()
        hirurgList = get_hirurg_list(form.departName.data)
        anesteziologList = get_anesteziolog_list()
        importData = get_oper_list(form.operDate.data, form.departName.data)
        depNameTitle = dict(form.departName.choices).get(form.departName.data)
        return render_template('add_client.html', departName=depNameTitle,
                               operDate=form.operDate.data.strftime('%d.%m.%Y'),
                               externals=externalsID, hirurgs=hirurgList, anesteziologList=anesteziologList,
                               dataSet=importData)
    return render_template('login.html', logForm=form)


@app.route('/exportExcel')
def exportExcel():
    exportData = get_oper_list('2020-09-22', 62)
    df = pd.DataFrame(exportData)
    writer = pd.ExcelWriter('План операций.xlsx')
    df.to_excel(writer)
    writer.save()
    return 'nothing'
