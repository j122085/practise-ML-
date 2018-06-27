from datetime import tzinfo, timedelta, datetime
import pymongo
import time


beganTime=time.time()

#撈柏融全資料
uri = "mongodb://py:123@ds014648.mlab.com:14648/wustudio"
client=pymongo.mongo_client.MongoClient(uri)
db=client.wustudio
print(client.wustudio.collection_names())
collection=db.probe
datas=list(collection.find({}))
print(len(datas)) #印出數量
collection.drop()#刪除柏融的資料(因為很容易就爆了)
client.close()

#upsert自己的位置
ids=[i.pop("_id") for i in datas]
operates=[pymongo.UpdateOne({"_id":idn},{"$set":datan},upsert=True) for idn,datan in zip(ids,datas)]
uri = "mongodb://j122085:850605@localhost:27017/wustudio"
client = pymongo.mongo_client.MongoClient(uri)
db=client.wustudio
collection=db.probe
try:
    collection.bulk_write(operates,ordered=False)
except Exception as e:
    print(e)
    
collection.count()#看看自己目前幾筆資料

from datetime import datetime
#時間 現在
d1 = datetime.now()
#前一小時
d2 = d1 - timedelta(hours =1)
#前一天
d3 = d1 - timedelta(days =1)

d1
#year, month, day, hour, minute, second, microsecond, and tzinfo

# d1.weekday()

#前一日的開始跟結束的時間
from datetime import timedelta
yesterday = datetime.now()-timedelta(days =1)
ydt=yesterday.date()
start = datetime(ydt.year, ydt.month, ydt.day)
end = start + timedelta(1)

start,end

# collection.drop()
# collection.insert_many(data, ordered=False)
rawdata=list(collection.find({"time":{"$gte":start,"$lt":end}},{"_id":False}))
client.close()

len(rawdata)

# get info 2

lunchData=[i for i in rawdata if i["time"]>start+timedelta(hours =10.5) and i["time"]<start+timedelta(hours =15)]
#留下中餐時間的資料

dinnerData=[i for i in rawdata if i["time"]>start+timedelta(hours =15) and i["time"]<start+timedelta(hours =22)]
#留下晚餐時間的資料

from collections import Counter

#顧客id
Customers={k[0] for k in 
           Counter([j['mac'] for i in rawdata for j in i['data'] 
                    if ('router' not in j or 'wow' not in j['router']) 
                    and ('ts' not in j or 'wow' not in j['ts'])]).items() 
           if k[1]>50}
print(len(Customers) )
#店家id
dienIDs={i["id"] for i in rawdata}

##########################################################抓之前的資料，找到員工IDList
uri = "mongodb://j122085:850605@localhost:27017"
client = pymongo.mongo_client.MongoClient(uri)
db=client.rawData
print(db.collection_names())

collectionsCustomer=db.wowCustomer2
fIds=[i["_id"]for i in list(collectionsCustomer.find({},{"_id":True}))]
fDatas=list(collectionsCustomer.find({},{"_id":False}))
customerDatas={i:j for i,j in zip(fIds,fDatas)}
# customerDatas=collections.find_one({"_id":"customer"}).get("data",{})


staffList=[]
for i in customerDatas:
    for j in customerDatas[i]:
        #來過超過3次、且最後7天內有來過4次的話 視為員工
        if len(customerDatas[i][j])>3 and len(customerDatas[i][j][3])>3 and sum(customerDatas[i][j][3][-4:])<7:
            staffList.append(i)
##########################################################抓之前的資料

#轉換資料>>顧客:{店家:[中餐來過幾次,晚餐來過幾次,最後一天來的日期,上次來跟這次來差了幾天]}
import time
x=list()

b=time.time()

for dienID in dienIDs:
    lunchMacs=[j['mac'] for k in lunchData if k["id"]==dienID for j in k['data']]
    dinnerMacs=[j['mac'] for k in dinnerData if k["id"]==dienID for j in k['data']]
    for Customer in Customers:
        if Customer not in staffList:
            lunch=0
            dinner=0
            if Customer in lunchMacs and lunchMacs.count(Customer)>50:
                lunch=1
            if Customer in dinnerMacs and dinnerMacs.count(Customer)>50:
                dinner=1
            if lunch+dinner>0:
                appearTime=start
                x.append([Customer,dienID,lunch,dinner,appearTime])

collectionsDien=db.wowDien2
fIds=[i["_id"]for i in list(collectionsDien.find({},{"_id":True}))]
fDatas=list(collectionsDien.find({},{"_id":False}))
dienDatas={i:j for i,j in zip(fIds,fDatas)}
# dienDatas=collections.find_one({"_id":"dien"}).get("data",{})


# customerDatas={}
for i in x:
    customerID=i[0]
    dienID=i[1]
    lunch=i[2]
    dinner=i[3]
    appearTime=i[4]
    #轉換資料>>顧客:{店家:[中餐來過幾次,晚餐來過幾次,最後一天來的日期,上次來跟這次來差了幾天]}
    if customerID not in customerDatas:
        customerDatas[customerID]={}
    if dienID not in customerDatas[customerID]:
        customerDatas[customerID][dienID]=[lunch,dinner,appearTime,[]]
    else:
        #每次增加跟上次來的天數差異(#間格時間>0天才跑)
        if (appearTime-customerDatas[customerID][dienID][2]).days>0:
            customerDatas[customerID][dienID][3].append((appearTime-customerDatas[customerID][dienID][2]).days)#這是動作，不會有return
                                               #中餐+1
            customerDatas[customerID][dienID]=[customerDatas[customerID][dienID][0]+lunch,
                                               #晚餐+1
                                               customerDatas[customerID][dienID][1]+dinner,
                                               #最後出現日期
                                               appearTime,
                                               #出現時間的間隔
                                               customerDatas[customerID][dienID][3]]
    #轉換資料>>店家:{顧客:[中餐來過幾次,晚餐來過幾次,最後一天來的日期,上次來跟這次來差了幾天]}
    if dienID not in dienDatas:
        dienDatas[dienID]={}
    if customerID not in dienDatas[dienID]:
        dienDatas[dienID][customerID]=[lunch,dinner,appearTime,[]]
    else:
        #每次增加跟上次來的天數差異(#間格時間>0天才跑)
        if (appearTime-dienDatas[dienID][customerID][2]).days>0:
            dienDatas[dienID][customerID][3].append((appearTime-dienDatas[dienID][customerID][2]).days)#這是動作，不會有return
                                               #中餐+1
            dienDatas[dienID][customerID]=[dienDatas[dienID][customerID][0]+lunch,
                                               #晚餐+1
                                               dienDatas[dienID][customerID][1]+dinner,
                                               #最後出現日期
                                               appearTime,
                                               #出現時間的間隔
                                               dienDatas[dienID][customerID][3]]
            
            
        
e=time.time()
print(e-b)   
# {x.split("-")[0]: for i in x}

datas=[customerDatas[i] for i in customerDatas]
ids=[i for i in customerDatas]
from pymongo import UpdateOne
uri = "mongodb://j122085:850605@localhost:27017"
client = pymongo.mongo_client.MongoClient(uri)
db=client.rawData
db.collection_names()
collections=db.wowCustomer2
operaters=[UpdateOne({"_id":idn},{"$set":data},upsert=True) for idn,data in zip(ids,datas)]
try:
    collections.bulk_write(operaters,ordered=False)
except:
    print("some data is exist")

datas=[dienDatas[i] for i in dienDatas]
ids=[i for i in dienDatas]
from pymongo import UpdateOne
uri = "mongodb://j122085:850605@localhost:27017"
client = pymongo.mongo_client.MongoClient(uri)
db=client.rawData
db.collection_names()
collections=db.wowDien2
operaters=[UpdateOne({"_id":idn},{"$set":data},upsert=True) for idn,data in zip(ids,datas)]
try:
    collections.bulk_write(operaters,ordered=False)
except:
    print("some data is exist")

# collections=db.wowCustomer2
# list(collections.find())[:20]

# collections=db.wowDien2
# list(collections.find())[2]

# 以上方案一 
### 中餐時段(10:30~15:00)、晚餐時段(15:00~22:00) ，時段內出現50次以上，且不連WOW網路才算顧客
### 資料格式json
# [顧客A:{店家A:[中午來幾次,晚上來幾次,最後一次來的日期，每次來的間隔時間LIST],
#       店家B:[中午來幾次,晚上來幾次,最後一次來的日期，每次來的間隔時間LIST],
#       店家C:[中午來幾次,晚上來幾次,最後一次來的日期，每次來的間隔時間LIST]}]
      
# [店家A:{顧客A:[中午來幾次,晚上來幾次,最後一次來的日期，每次來的間隔時間LIST],
#       顧客B:[中午來幾次,晚上來幾次,最後一次來的日期，每次來的間隔時間LIST],
#       顧客C:[中午來幾次,晚上來幾次,最後一次來的日期，每次來的間隔時間LIST]}]

# －－－－－－－－－－－－－－－－－－－－－－－－－－－－－－
# 方案二考慮產成SQL樣子的資料(店、顧客、日期、停留時間(進時、出時))
### 待太久(3HR)、太常出現(每周4次)、連WOW網路都視為員工
### 待太短(800SEC以下)視為路人

# rawdata[0]
# Customers
# dienIDs

#dienId+CustomerMac+time table
table=[{"dienId":i['id'],"CustomerMac":j['mac'],"time":i['time']} for i in rawdata for j in i['data']]
NCustomAppear=dict(Counter([i["CustomerMac"] for i in table]))
#Appear>50times Custome and not in stafflist
CustomerMacS=[i for i in NCustomAppear if NCustomAppear[i]>50 and i not in staffList]

dienIdS=list(dienIDs)


import time
b=time.time()
targetTable=[]
for CustomerMac in CustomerMacS:
    for dienId in dienIdS:
        row={}
        row["CustomerMac"]=CustomerMac
        row['dienId']=dienId
        row['comeDate']=str(ydt)
        #get dien-customer[index] datas
        locationCustomerDatas=[j for j in table if j['CustomerMac']==CustomerMac and j['dienId']==dienId]
        if len(locationCustomerDatas)>50:
            row['comeTime']=locationCustomerDatas[2]['time']
            time1=locationCustomerDatas[1]['time']
            time2=locationCustomerDatas[2]['time']
            beginTime=locationCustomerDatas[2]['time']
            listTimeGap=[]
            endTime=""
            for i in locationCustomerDatas[2:]:
                gap=time2-time1
                time1=time2
                time2=i['time']
                if gap>timedelta(seconds=300):
                    endTime=time1
                    break
            #     listTimeGap.append(gap)
            if endTime=="":
                endTime=time2
            row['leaveTime']=endTime
            row['stopTime']=(endTime-beginTime).seconds
            #去除來的時間過長(員工) 或過短(路過)的人
            if row['stopTime']>1200 and row['stopTime']<9600:
                targetTable.append(row)
    e=time.time()
    print(e-b)
    
print("共花費{}秒".format(round(e-b)))

# beganTime=time.time()
endTime=time.time()

print("共使用{}秒".format(endTime-beganTime))

uri = "mongodb://j122085:850605@localhost:27017"
client = pymongo.mongo_client.MongoClient(uri)
db=client.rawData
db.collection_names()
collections=db.wowCustomerTable

ids=[i['CustomerMac']+i["dienId"]+str(i['comeDate']) for i in targetTable]

operaters=[UpdateOne({"_id":idn},{"$set":data},upsert=True) for idn,data in zip(ids,targetTable)]
try:
    collections.bulk_write(operaters,ordered=False)
except Exception as e:
    print(e)

# list(collections.find({}))

allTable=list(collections.find({},{"_id":False}))
import pandas as pd
df=pd.DataFrame(allTable)

ew=pd.ExcelWriter(r"D:\outputXLS\dienCustomer.xlsx")
df.to_excel(ew)

ew.save()