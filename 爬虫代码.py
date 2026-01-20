import requests
from bs4 import BeautifulSoup
import json
import pymongo

MONGO_URL = 'localhost'
MONGO_DB = 'lianjia'
client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def getPage(url):
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    try:
        res = session.get(url)
        if res.status_code == 200:
            return res.text
        else:
            return ""  # Return an empty string if status code is not 200
    except Exception as e:
        print(f"Failed to retrieve {url}: {e}")
        return ""  # Return an empty string in case of an exception


def getPage(url):
    try:
        res = requests.get(url)
        if res.status_code == 200:
            # print(res.text)
            # print(res.encoding)
            return res.text
    except Exception as e:
        print(e)


def getHouseId(url):
    pageText = getPage(url)
    soup = BeautifulSoup(pageText, 'lxml')
    soupContent = soup.find_all(name="a", attrs={"data-el": "ershoufang"})
    houseIdSet = set()
    for a in soupContent:
        houseIdSet.add(a.get("href"))
        # print(a.get("href"))

    return list(houseIdSet)


def saveData(houseDict):
    # 这里是沈阳市的二手房数据，若需要获取其他，更换表名db[’tableName‘]
    db['shenyang'].save(houseDict)
    print("存入数据库" + str(len(houseDict)) + "条数据！")


def getHouseContent(url):
    houseInfoDict = {}
    pageText = getPage(url)
    soup = BeautifulSoup(pageText, 'lxml')

    # 一些数据重复，因此将重复的部分注释了
    # 简要信息
    # 总价
    price = soup.find(name="span", attrs={"class": "total"}).text
    houseInfoDict['总价'] = price
    # print(price)

    # 单位价格
    unitPrice = soup.find(name="span", attrs={"class": "unitPriceValue"}).text
    houseInfoDict['单位价格'] = unitPrice
    # print(unitPrice)

    # 户型
    # room = soup.find(name="div", attrs={"class": "room"})
    # roomInfo = BeautifulSoup(str(room), 'lxml').find(name="div", attrs={"class": "mainInfo"}).text
    # print(roomInfo)

    # 楼层
    # roomSubInfo = BeautifulSoup(str(room), 'lxml').find(name="div", attrs={"class": "subInfo"}).text
    # print(roomSubInfo)

    # 朝向
    # type = soup.find(name="div", attrs={"class": "type"})
    # typeInfo = BeautifulSoup(str(type), 'lxml').find(name="div", attrs={"class": "mainInfo"}).text
    # print(typeInfo)

    # 装修
    # typeSubInfo = BeautifulSoup(str(type), 'lxml').find(name="div", attrs={"class": "subInfo"}).text
    # print(typeSubInfo)

    # 面积
    area = soup.find(name="div", attrs={"class": "area"})
    # areaInfo = BeautifulSoup(str(area), 'lxml').find(name="div", attrs={"class": "mainInfo"}).text
    # print(areaInfo)

    # 楼房信息
    areaSubInfo = BeautifulSoup(str(area), 'lxml').find(name="div", attrs={"class": "subInfo noHidden"}).text
    houseInfoDict['楼房信息'] = areaSubInfo
    # print(areaSubInfo)

    # 小区
    community = soup.find(name="div", attrs={"class": "communityName"})
    communityInfo = BeautifulSoup(str(community), 'lxml').find(name="a", attrs={"class": "info"}).text
    houseInfoDict['小区'] = communityInfo
    # print(communityInfo)

    # 所属区县
    areaDistrict = soup.find(name="div", attrs={"class": "areaName"})
    areaDistrictInfo = BeautifulSoup(str(areaDistrict), 'lxml').find_all(name="a")[0].text
    houseInfoDict['所属区县'] = areaDistrictInfo
    # print(areaDistrictInfo)

    # 基本属性
    base = soup.find(name="div", attrs={"class": "base"})
    baseInfo = BeautifulSoup(str(base), 'lxml').find_all(name="li")
    for li in baseInfo:
        key = li.text[:4]
        houseInfoDict[key] = li.text[4:]
        # print(li.text[4:])

    # 交易属性
    transaction = soup.find(name="div", attrs={"class": "transaction"})
    transactionInfo = BeautifulSoup(str(transaction), 'lxml').find_all(name="li")
    for li in transactionInfo:
        liText = li.text.strip("\r").strip("\n").strip('\r').strip('\n').replace('\n', '').replace(' ', '')
        key = liText[:4]
        houseInfoDict[key] = liText[4:]
        # print(li.text[4:])

    # 户型分间
    layout = soup.find(name="div", attrs={"class": "layout"})
    roomRow = BeautifulSoup(str(layout), 'lxml').find_all(name="div", attrs={"class": "row"})
    # print(roomRow)
    houseInfoDict['户型分间'] = {}
    for row in roomRow:
        # key = roomRow[0]
        col = BeautifulSoup(str(row), 'lxml').find_all(name="div", attrs={"class": "col"})
        for i in range(1, len(col)):
            key = col[0].text
            if i == 1:
                houseInfoDict['户型分间'][key + "面积"] = col[1].text
            elif i == 2:
                houseInfoDict['户型分间'][key + "朝向"] = col[2].text
            elif i == 3:
                houseInfoDict['户型分间'][key + "窗型"] = col[3].text

    # 小区简介
    rid = soup.find(name="div", attrs={"id": "framesdk"}).get("data-resblock-id")
    # print(rid)
    houseRecord = soup.find(name="div", attrs={"class": "houseRecord"})
    hid = BeautifulSoup(str(houseRecord), 'lxml').find(name="span", attrs={"class": "info"}).text[:-2]
    # print(hid)
    # 这里是沈阳市的二手房数据，若需要获取其他，更换链接前缀
    xiaoquInfoUrl = 'https://sy.lianjia.com/ershoufang/housestat?hid=' + str(hid) + '&rid=' + str(rid)
    # print(xiaoquInfoUrl)
    xiaoquInfo = json.loads(getPage(xiaoquInfoUrl))
    # print(xiaoquInfo)
    # print(xiaoquInfo['data']['resblockCard'])
    # buildYear
    buildYear = xiaoquInfo['data']['resblockCard']['buildYear']
    buildNum = xiaoquInfo['data']['resblockCard']['buildNum']
    unitPrice = xiaoquInfo['data']['resblockCard']['unitPrice']

    houseInfoDict['小区简介'] = {}
    houseInfoDict['小区简介']['小区建造年份'] = buildYear
    houseInfoDict['小区简介']['楼栋总数'] = buildNum
    houseInfoDict['小区简介']['小区均价'] = unitPrice

    try:
        saveData(houseInfoDict)
    except Exception as e:
        print(e)
    # print(houseInfoDict)


for i in range(1, 101):
    # 这里是沈阳市的二手房数据，若需要获取其他，更换链接前缀
    url = 'https://sy.lianjia.com/ershoufang/pg' + str(i)
    houseIdList = getHouseId(url)
    print("第" + str(i) + "页")
    for j in range(len(houseIdList)):
        print(j)
        try:
            getHouseContent(houseIdList[j])
        except Exception as e:
            print(e)
