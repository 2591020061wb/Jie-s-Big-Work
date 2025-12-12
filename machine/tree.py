import jieba
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score,classification_report
from sklearn.preprocessing import LabelEncoder
from sqlalchemy import create_engine,text

conn = create_engine('mysql+pymysql://root:ASDFasdf123456@127.0.0.1:3306/medicalinfo?charset=utf8')
stopwords = set(open('./machine/stopword.txt','r',encoding='utf-8').read().splitlines())
def tokensize(text):
    words = [word for word in jieba.cut(text) if word not in stopwords]
    return ' '.join(words)
def getData():
    query = text('select * from cases')
    df = pd.read_sql(query,con=conn,index_col='id')
    data = df[['content','type']]
    data['content'] = data['content'].apply(tokensize)
    # print(data)
    return data

vectorizer = TfidfVectorizer(max_features=10000)
def model_train(data):
    x_train,x_test,y_train,y_test = train_test_split(data['content'],data['type'],test_size=0.2,random_state=42)

    #文本提取
    x_train_vectorizer = vectorizer.fit_transform(x_train)
    x_test_vectorizer = vectorizer.transform(x_test)

    #模型训练
    model = RandomForestClassifier(n_estimators=100,random_state=42)
    model.fit(x_train_vectorizer,y_train)
    y_pred = model.predict(x_test_vectorizer)
    accuracy = accuracy_score(y_test,y_pred)
    return model

def pred(model,content):
    content = [' '.join(jieba.cut(content))]

    x_test_vectorizer = vectorizer.transform(content)
    pred = model.predict(x_test_vectorizer)
    return pred[0]

if __name__ == '__main__':
    trainData = getData()
    model = model_train(trainData)
    pred(model,'腰部疼痛')