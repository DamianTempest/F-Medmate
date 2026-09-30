import json
import pytest
import requests
from medmate.assistant import Assistant, AssistantError

class Response:
    def __init__(self,status,data): self.status_code=status; self.data=data
    def json(self):
        if isinstance(self.data,Exception): raise self.data
        return self.data

class Session:
    def __init__(self,response): self.response=response; self.payload=None
    def post(self,url,**kwargs):
        assert url=='https://openrouter.ai/api/v1/chat/completions'
        assert kwargs['timeout']==(5,45)
        self.payload=kwargs['json']
        if isinstance(self.response,Exception): raise self.response
        return self.response

def test_requires_key_and_model():
    with pytest.raises(AssistantError): Assistant(key='',model='').reply('hello',[])

def test_valid_reply_and_profile_opt_in_context():
    s=Session(Response(200,{'id':'test','object':'chat.completion','created':1,'model':'example/model','choices':[{'index':0,'finish_reason':'stop','message':{'role':'assistant','content':'Hello there'}}],'usage':{'prompt_tokens':1,'completion_tokens':2,'total_tokens':3}}))
    a=Assistant(key='test',model='example/model',session=s)
    assert a.reply('Hello',[],None)=='Hello there'
    assert 'allergies' not in json.dumps(s.payload)
    a.reply('Hello',[],{'allergies':'fish','name':'Secret name','license_number':'Secret license'})
    assert 'fish' in json.dumps(s.payload)
    assert 'Secret name' not in json.dumps(s.payload)
    assert 'Secret license' not in json.dumps(s.payload)

@pytest.mark.parametrize('response,expected',[
    (requests.Timeout(),'timed out'),
    (requests.ConnectionError(),'connect'),
    (Response(401,{'error':{'code':401,'message':'invalid'}}),'key'),
    (Response(429,{'error':{'code':429,'message':'rate'}}),'busy'),
    (Response(200,{'error':{'code':400,'message':'bad'}}),'usable'),
    (Response(200,{'choices':[]}),'usable'),
    (Response(200,ValueError('bad json')),'usable'),
    (Response(200,{'choices':[{'message':{'content':None}}]}),'usable'),
])
def test_failure_messages(response,expected):
    with pytest.raises(AssistantError,match=expected): Assistant(key='test',model='model',session=Session(response)).reply('hello',[])

def test_history_is_bounded():
    s=Session(Response(200,{'choices':[{'message':{'content':'OK'}}]}))
    Assistant(key='test',model='model',session=s).reply('hello',[{'role':'user','text':'x'*9000}]*40)
    assert len(s.payload['messages'])<=14
    assert max(len(m['content']) for m in s.payload['messages'])<=7000
