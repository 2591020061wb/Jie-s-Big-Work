from flask import Flask,request,jsonify
from utils.getAllData import *
app = Flask(__name__)
from utils.getPublicData import *
from machine.tree import *
@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'

@app.route('/getHomeData',methods=['GET','POST'])
def getHomeData():
    pieData = getPieData()
    configOne,wordData = getConfigOne()
    casesData = list(getAllCasesData())
    maxNum,maxType,maxDep,maxHos,maxAge,minAge = getFoundData()
    boyList,girlList,ratioData = getGenderData()
    circleData=getCircleData()
    xData,y1Data,y2Data = getBodyData()
    return jsonify({
        'message':'success',
        'code':200,
        'data':{
            'pieData':pieData,
            'configOne':configOne,
            'casesData':casesData,
            'maxNum':maxNum,
            'maxType': maxType,
            'maxDep': maxDep,
            'maxHos': maxHos,
            'maxAge': maxAge,
            'minAge': minAge,
            'boyList':boyList,
            'girlList':girlList,
            'ratioData':ratioData,
            'circleData':circleData,
            'wordData':wordData,
            'lastData':{
                'xData':xData,
                'y1Data':y1Data,
                'y2Data':y2Data
            }
        }
    })

@app.route('/submitModel',methods=['GET','POST'])
def submitModel():
    if request.method == 'POST':
        content = request.json['content']
        print(content)
        model = model_train(getData())
        result = pred(model,content)
    return jsonify({
        'message':'success',
        'code':200,
        'data':{
            'resultData':result
        }
    })

@app.route('/tableData',methods=['GET','POST'])
def tableData():
    tableDataList = getAllCasesData()
    resultData = [x[1:] for x in tableDataList]
    # print(resultData)
    return jsonify({
        'message':'success',
        'code':200,
        'data':{
            'resultData':resultData
        }
    })


if __name__ == '__main__':
    app.run()
