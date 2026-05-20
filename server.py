from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/price/{code}")
def get_price(code: str):
    try:
        # 1. 해외 인프라에서도 절대 차단 안 당하는 '야후 파이낸스' 통로 가동
        # 한국 주식은 종목코드 뒤에 .KS(코스피) 또는 .KQ(코스닥)를 붙여야 조회됨
        
        # 우선 코스피(.KS)로 먼저 찔러보기
        yahoo_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}.KS"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(yahoo_url, headers=headers, timeout=5)
        data = response.json()
        
        # 만약 데이터가 없거나 비어있으면 코스닥(.KQ)으로 다시 찔러보기
        if not data.get('chart', {}).get('result'):
            yahoo_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}.KQ"
            response = requests.get(yahoo_url, headers=headers, timeout=5)
            data = response.json()
            
        if data.get('chart', {}).get('result'):
            result = data['chart']['result'][0]
            meta = result.get('meta', {})
            
            # 야후 파이낸스에서 받아온 실시간 현재가 (달러 아님! 원화 가격 그대로 들고옴)
            current_price = int(round(meta.get('regularMarketPrice', 0)))
            
            # 2. 종목명은 네이버가 해외 IP를 차단해도 '이 주소'는 필터링을 안 해서 안전함!
            # 네이버 주식 검색창 자동완성 시스템을 역이용하여 종목명 낚셔오기
            name_url = f"https://ac.finance.naver.com/ac?q={code}&q_enc=utf-8&st=1&frm=stock"
            name_resp = requests.get(name_url, headers=headers, timeout=5)
            name_data = name_resp.json()
            
            stock_name = "알수없음"
            if name_data.get('items') and name_data['items'][0]:
                # 검색 결과에서 종목명 추출 (예: ["삼성전자","005930","..."])
                stock_name = name_data['items'][0][0][0]
                
            if current_price > 0:
                return {"success": True, "name": stock_name, "price": current_price}

    except Exception as e:
        print(f"해외 API 서버 우회 중 에러 발생: {e}")
        
    return {"success": False, "price": 0, "name": "조회 실패"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)