# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

# HTML 앱과 파이썬 간의 데이터 통신을 허용하는 보안 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/price/{code}")
def get_stock_price(code: str):
    try:
        # 네이버보다 데이터 구조가 깨끗한 다음 금융 API를 직접 호출
        url = f"https://finance.daum.net/api/quotes/A{code}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://finance.daum.net'
        }
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        
        if data and "data" in data:
            return {
                "success": True, 
                "price": int(data["data"]["tradePrice"]), 
                "name": data["data"]["name"]
            }
    except Exception as e:
        print(f"주가 가져오기 에러 발생: {e}")
    
    return {"success": False, "price": 0, "name": "조회 실패"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)