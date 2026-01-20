import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import seaborn as sns
import warnings
import json
import pymongo
import re
warnings.filterwarnings("ignore")
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
pd.set_option('display.max_rows', 100,'display.max_columns', 1000,"display.max_colwidth",1000,'display.width',1000)
data = pd.read_excel(r"D:\SELFSTUDY\PYTHON\project\ML房价预测杭州\025基于机器学习的杭州市二手房价预测模型实证分析＋机器学习模型详解\房价预测代码\房价预测代码\data\链家杭州二手房数据.xlsx", na_values=np.nan)
data = data[data.columns[:-4]]

# 再看一下数据
data.head()
data['单位价格'] = data['单位价格'].str[:-4]
data['单位价格'] = data['单位价格'].astype(float)

data['楼房信息'] = data['楼房信息'].str[:4]
data['楼房信息'].value_counts()
'''
输出：
未知年建    673
2019    187
2012    183
2018    175
2017    173
2015    171
2016    171
2014    150
2009    142
2010    140
2013    109
2011    102
2020    100
2008     99
2006     72
2007     67
2005     55
2000     43
2021     37
2004     35
1999     25
2003     20
1998     12
1996     10
1997      9
1995      6
2002      5
1990      3
2001      3
1994      3
1992      1
2090      1
2121      1
1987      1
Name: 楼房信息, dtype: int64

# 从楼房信息的输出结果可以看出，有673条样本为“未知年建”，因此这部分数据需要进一步处理，我们使用小区简介中的小区建造年份进行填补。
'''


# 定义填补函数
def fillBuildYear(df):
    if df['楼房信息'] == "未知年建":
        xiaoqu = json.loads(df['小区简介'].replace("'", '"'))
        return xiaoqu['小区建造年份'][:4]
    else:
        return df['楼房信息']


# 进行填补
data['楼房信息'] = data.apply(lambda x: fillBuildYear(x), axis=1)
# 再看一下
data['楼房信息'].value_counts()
'''
输出：
2012    224
2019    204
2017    194
2018    188
2015    183
2009    179
2014    176
2010    176
2016    172
2008    153
2000    127
2013    113
2011    106
2020    101
2006     98
2007     98
2005     86
2004     59
1999     48
2021     41
2003     36
1998     32
1995     28
1990     27
2002     26
2001     16
1996     16
1997     16
1988      8
1992      8
1987      6
1978      6
1980      6
1989      5
1994      4
1970      3
1985      2
1986      2
1955      1
2121      1
1993      1
1991      1
2090      1
1960      1
1983      1
1958      1
1900      1
1972      1
1979      1
Name: 楼房信息, dtype: int64
'''

# 转换一下类型
data['楼房信息'] = data['楼房信息'].astype(int)

# 然后看一下房屋户型，我们可以发现都是 x室x厅x厨x卫的格式，因此我们直接将其中的数字提取出来。
data['房屋户型_室'] = data['房屋户型'].str[0].astype(int)
data['房屋户型_厅'] = data['房屋户型'].str[2].astype(int)
data['房屋户型_厨'] = data['房屋户型'].str[4].astype(int)
data['房屋户型_卫'] = data['房屋户型'].str[6].astype(int)

# 所在楼层部分只有低中高楼层是确定的，后面的（共几层）无用，因此将低中高楼层提取替换
data['所在楼层'] = data['所在楼层'].str[:3]

# 然后将建筑面积的“㎡” 删掉
data['建筑面积'] = data['建筑面积'].str[:-1].astype(float)

# 然后我们看一下套内面积的数据分布情况
data['套内面积'].value_counts()
'''
输出：
暂无数据       2581
50㎡           5
129㎡          4
70㎡           4
73.66㎡        3
           ... 
47.54㎡        1
88.56㎡        1
66.37㎡        1
64㎡           1
122.64㎡       1
Name: 套内面积, Length: 317, dtype: int64
'''
# 我们可以发现，大量数据是“暂无数据”，但我认为套内面积这个属性还比较重要，因此我们对它进行一个均值填充
# 取其他有数值的房子，计算其建筑面积与套内面积的差值，并在最后取平均，对于“暂无数据”的这些房子，我们用建筑面积减去均值
count = 0
areaDiff = 0
for i in range(data.shape[0]):
    if "㎡" in data.iloc[i]['套内面积']:
        # print(data.iloc[i]['建筑面积'], data.iloc[i]['套内面积'][:-1])
        areaDiff += data.iloc[i]['建筑面积'] - float(data.iloc[i]['套内面积'][:-1])
        count += 1
print(round(areaDiff, 2), count, round(areaDiff / count, 2))  # 输出：6173.99 403 15.32


# 均值为15.32，因此我们进行填充
# 定义填充函数
def fillInsideArea(df):
    if "㎡" in df['套内面积']:
        return float(df['套内面积'][:-1])
    else:
        return (df['建筑面积'] - 15.32)


# 填充
data['套内面积'] = data.apply(lambda x: fillInsideArea(x), axis=1)


# 然后是梯户比例，查看数据可以发现，x梯xx户的形式，因此我们直接将这部分转化为数值的比例，用 户/梯
# 定义转化函数
def ratioTH(df, flag):
    CN_NUM = {'十': 10, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '零': 0, '两': 2}
    if pd.isna(df['梯户比例']) or "" == df['梯户比例']:
        return 0

    strList = df['梯户比例'].split("梯")
    T = strList[0]
    H = strList[1]
    numTList = list(T)
    numHList = list(H)

    numTStr = '0'
    for i in range(len(numTList)):
        if numTList[i] in CN_NUM.keys():
            numTStr = str(int(numTStr) + CN_NUM[numTList[i]])

    numHStr = '0'
    for i in range(len(numHList)):
        if numHList[i] in CN_NUM.keys():
            numHStr = str(int(numHStr) + CN_NUM[numHList[i]])

    if flag == 1:
        return int(numTStr)
    elif flag == 2:
        return int(numHStr)
    else:
        return int(numHStr) / int(numTStr)


data['梯户比例_梯'] = data.apply(lambda x: ratioTH(x, 1), axis=1)
data['梯户比例_户'] = data.apply(lambda x: ratioTH(x, 2), axis=1)
data['梯户比例_比例'] = data.apply(lambda x: ratioTH(x, 3), axis=1)

# 查看一下转化后的结果
data[['梯户比例', '梯户比例_梯', '梯户比例_户', '梯户比例_比例']].head()
'''
输出：
	梯户比例	梯户比例_梯	梯户比例_户	梯户比例_比例
0	两梯两户		2			2			1.00
1	两梯四户		2			4			2.00
2	一梯两户		1			2			2.00
3	两梯三户		2			3			1.50
4	一梯两户		1			2			2.00
'''

# 可以填充的我们基本处理完了，再看一下data.info()
data.info()
'''
输出：
<class 'pandas.core.frame.DataFrame'>
RangeIndex: 2984 entries, 0 to 2983
Data columns (total 34 columns):
 #   Column   Non-Null Count  Dtype  
---  ------   --------------  -----  
 0   总价       2984 non-null   float64
 1   单位价格     2984 non-null   float64
 2   楼房信息     2984 non-null   int32  
 3   小区       2984 non-null   object 
 4   所属区县     2984 non-null   object 
 5   房屋户型     2984 non-null   object 
 6   所在楼层     2984 non-null   object 
 7   建筑面积     2984 non-null   float64
 8   户型结构     2967 non-null   object 
 9   套内面积     2984 non-null   float64
 10  建筑类型     2967 non-null   object 
 11  房屋朝向     2984 non-null   object 
 12  建筑结构     2984 non-null   object 
 13  装修情况     2984 non-null   object 
 14  梯户比例     2967 non-null   object 
 15  供暖方式     2984 non-null   object 
 16  配备电梯     2967 non-null   object 
 17  挂牌时间     2984 non-null   object 
 18  交易权属     2984 non-null   object 
 19  上次交易     2984 non-null   object 
 20  房屋用途     2984 non-null   object 
 21  房屋年限     2984 non-null   object 
 22  产权所属     2984 non-null   object 
 23  抵押信息     2984 non-null   object 
 24  房本备件     2984 non-null   object 
 25  户型分间     2984 non-null   object 
 26  小区简介     2984 non-null   object 
 27  房屋户型_室   2984 non-null   int32  
 28  房屋户型_厅   2984 non-null   int32  
 29  房屋户型_厨   2984 non-null   int32  
 30  房屋户型_卫   2984 non-null   int32  
 31  梯户比例_梯   2984 non-null   int64  
 32  梯户比例_户   2984 non-null   int64  
 33  梯户比例_比例  2984 non-null   float64
dtypes: float64(5), int32(5), int64(2), object(22)
memory usage: 734.5+ KB
'''
# 我们发现，仍有四列['户型结构', '建筑类型', '梯户比例', '配备电梯']，有空值，其中'梯户比例'已处理，直接删除该列，其他三列看看数据分布
data.drop(['梯户比例'], axis=1, inplace=True)
fillColName = ['户型结构', '建筑类型', '配备电梯']
for c in fillColName:
    print(data[c].value_counts())

'''
输出：
平层      2742
跃层       112
错层        53
复式        53
暂无数据       7
Name: 户型结构, dtype: int64

板楼      2463
板塔结合     330
塔楼       107
暂无数据      63
平房         4
Name: 建筑类型, dtype: int64

有       2218
无        410
暂无数据     339
Name: 配备电梯, dtype: int64
'''

# 我们发现，均有暂无数据，那么空值就可以填充为“暂无数据”了
for c in fillColName:
    data[c].fillna("暂无数据", inplace=True)

# 看一下有哪些列为数值型数据
data.dtypes[data.dtypes != 'object']
'''
输出：
总价         float64
单位价格       float64
楼房信息         int32
建筑面积       float64
套内面积       float64
房屋户型_室       int32
房屋户型_厅       int32
房屋户型_厨       int32
房屋户型_卫       int32
梯户比例_梯       int64
梯户比例_户       int64
梯户比例_比例    float64
'''

# 哪些列为Object型数据
data.dtypes[data.dtypes == 'object']
'''
输出：
小区      object
所属区县    object
房屋户型    object
所在楼层    object
户型结构    object
建筑类型    object
房屋朝向    object
建筑结构    object
装修情况    object
供暖方式    object
配备电梯    object
挂牌时间    object
交易权属    object
上次交易    object
房屋用途    object
房屋年限    object
产权所属    object
抵押信息    object
房本备件    object
户型分间    object
小区简介    object
'''


# 类型为Object的数据我们暂时先不用处理了，后面会做独热编码处理

def xiaoquInfo(df, flag):
    xiaoqu = json.loads(df['小区简介'].replace("'", '"'))
    if flag == 1:
        return int(xiaoqu['小区建造年份'][:-1])
    elif flag == 2:
        return int(xiaoqu['楼栋总数'][:-1])
    else:
        return xiaoqu['小区均价']

data['小区建造年份'] = data.apply(lambda x:xiaoquInfo(x, 1), axis=1)
data['楼栋总数'] = data.apply(lambda x:xiaoquInfo(x, 2), axis=1)
data['小区均价'] = data.apply(lambda x:xiaoquInfo(x, 3), axis=1)

# 剔除一些无用列，
data = data[['总价', '单位价格', '楼房信息', '所属区县', '所在楼层', '建筑面积', '户型结构', '套内面积', '建筑类型', '房屋朝向', '建筑结构', '装修情况', '供暖方式', '配备电梯', '挂牌时间', '交易权属', '上次交易', '房屋用途', '房屋年限', '产权所属', '抵押信息', '房屋户型_室', '房屋户型_厅', '房屋户型_厨', '房屋户型_卫', '梯户比例_梯', '梯户比例_户', '梯户比例_比例', '小区建造年份', '楼栋总数', '小区均价']]

# 将列中只含两种类型的列进行0-1转换，“抵押信息”列中，可以理解为只含“无抵押”和“有抵押”
def diyaInfo(df):
    if df['抵押信息'] == '无抵押':
        return 0
    else:
        return 1

data['抵押信息_01'] = data.apply(lambda x:diyaInfo(x), axis=1)
data['产权所属'] = data['产权所属'].replace("非共有", 0).replace("共有", 1)

# 将数据获取时间定义
data['数据获取日期'] = '2022-04-24'

# 定义一下处理日期型数据的函数，将日期转化为时间差值，天为单位
import datetime
def calDate(df, c):
    if df[c] == '暂无数据':
        return np.nan
    d1=datetime.datetime.strptime('2022-04-24',"%Y-%m-%d")
    d2=datetime.datetime.strptime(df[c],"%Y-%m-%d")
    diff_days=d1-d2
    return diff_days.days
for c in ['挂牌时间', '上次交易']:
    data[c+'差（天）'] = data.apply(lambda x:calDate(x, c), axis=1)
# 有空缺值按均值填充了
for c in ['挂牌时间差（天）', '上次交易差（天）']:
    data[c].fillna(data[c].mean(), inplace=True)

# 生成房龄数据
data['房龄'] = 2022 - data['楼房信息']

# 将某些列做独热编码处理，房屋朝向这一列含有的类别过多，做独热编码时会使数据稀疏，因此，将一些少量类别的数据进行合并为“其他朝向”
def calChaoxiang(df):
    chaoxiangCol = ['南 北', '南', '东南', '西南', '北 南', '东 南 北', '西北', '西', '东', '南 西 北', '东北', '北', '东 西', '南 北 西', '东 北', '南 北 东']
    if df['房屋朝向'] not in chaoxiangCol:
        return "其他朝向"
    else:
        return df['房屋朝向']

data['房屋朝向'] = data.apply(lambda x:calChaoxiang(x), axis=1)

one_hot_col_names = ['所属区县',
 '所在楼层',
 '户型结构',
 '建筑类型',
 '房屋朝向',
 '建筑结构',
 '装修情况',
 '供暖方式',
 '配备电梯',
 '交易权属',
 '房屋用途',
 '房屋年限']

# 删除已处理过的时间列
data.drop(['挂牌时间', '上次交易', '数据获取日期'], axis=1, inplace=True)

one_hot_data = pd.get_dummies(data[one_hot_col_names])
data = pd.concat([data,one_hot_data],axis = 1)
data.drop(one_hot_col_names, axis=1, inplace=True)

# 将处理过的数据导出（注意，这一部分代码要续上之前分享过的代码，上次数据处理不完全）
data.to_excel("二手房数据（处理后）.xlsx", index=False)
