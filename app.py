from vpb import VPB
import json
import requests
import json
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import sys
import traceback
from api_response import APIResponse
import subprocess



app = FastAPI()
@app.get("/")
def read_root():
    return {"Hello": "World"}
class LoginDetails(BaseModel):
    username: str
    password: str
    account_number: str
@app.post('/login', tags=["login"])
def login_api(input: LoginDetails):
    try:
        vpb = VPB(input.username, input.password, input.account_number)
        response = vpb.doLogin()
        return APIResponse.json_format(response)
    except Exception as e:
        response = str(e)
        print(traceback.format_exc())
        print(sys.exc_info()[2])
        return APIResponse.json_format(response)    
@app.post('/balance', tags=["balance"])
def confirm_api(input: LoginDetails):
    try:
        vpb = VPB(input.username, input.password, input.account_number)
        response = vpb.get_balance()
        print(response)
        return APIResponse.json_format(response)
    except Exception as e:
        response = str(e)
        print(traceback.format_exc())
        print(sys.exc_info()[2])
        return APIResponse.json_format(response)
    
class Transactions(BaseModel):
    username: str
    password: str
    account_number: str
    limit: int
    from_date: str
    to_date: str
    
@app.post('/transactions', tags=["transactions"])
def get_transactions_api(input: Transactions):
    try:
        vpb = VPB(input.username, input.password, input.account_number)
        response = vpb.getHistories(input.account_number, input.limit, input.from_date, input.to_date)
        print(response)
        return APIResponse.json_format(response)
    except Exception as e:
        response = str(e)
        print(traceback.format_exc())
        print(sys.exc_info()[2])
        return APIResponse.json_format(response)

@app.post('/test', tags=["test"])
def test():
    try:
        # 定義要傳遞的資料
        data = {
            "package_name": "vn.com.techcombank.bb.appC",
        }
        json_str = json.dumps(data)
        result = subprocess.Popen(['python', 'test.py', json_str])
    except Exception as e:
        response = str(e)
        print(traceback.format_exc())
        print(sys.exc_info()[2])
        return APIResponse.json_format(response)

if __name__ == "__main__":
    uvicorn.run(app ,host='0.0.0.0', port=23120)
    # uvicorn.run(app ,host='127.0.0.1', port=23120)
    
    