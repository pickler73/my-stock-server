from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

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
        # 해외/국내 어디서든 100% 프리패스인 야후 파이낸스 API 가동
        # 코스피(.KS)로 먼저 요청
        yahoo_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}.KS"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(yahoo_url, headers=headers, timeout=5)
        data = response.json()
        
        # 코스피 결과가 없으면 코스닥(.KQ)으로 재요청
        if not data.get('chart', {}).get('result'):
            yahoo_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}.KQ"
            response = requests.get(yahoo_url, headers=headers, timeout=5)
            data = response.json()
            
        if data.get('chart', {}).get('result'):
            result = data['chart']['result'][0]
            meta = result.get('meta', {})
            
            # 1. 실시간 현재가 추출 (원화 가격 그대로)
            current_price = int(round(meta.get('regularMarketPrice', 0)))
            
            # 2. 종목명 추출 (야후 파이낸스가 기억하는 한글/영문 이름 활용)
            # 야후가 주는 이름 뒤의 회사 종류 접미사(.KS, Co., Ltd. 등)를 깔끔하게 정돈
            raw_name = meta.get('symbol', '알수없음')
            
            # 만약 야후 자체에 등록된 긴 이름(longName)이나 정식 명칭이 있다면 그것을 사용
            # 한국 종목은 야후에서 영문이나 한글 공식명으로 깔끔하게 내려줍니다.
            stock_name = raw_name
            
            # 더 정확한 한글 종목명을 위해 야후 검색 자동완성 API를 아주 살짝 역이용 (해외 서버 가능)
            search_url = f"https://query1.finance.yahoo.com/v1/finance/search?q={code}"
            search_resp = requests.get(search_url, headers=headers, timeout=3)
            search_data = search_resp.json()
            if search_data.get('quotes'):
                stock_name = search_data['quotes'][0].get('longname') or search_data['quotes'][0].get('shortname') or raw_name

            # 보기 싫은 해외 접미사들 청소 (예: KODEX 200 -> 깔끔하게 출력)
            stock_name = stock_name.split('(')[0].strip()

            if current_price > 0:
                # 캡처화면에 보내주신 '122630(KODEX 레버리지)'처럼 종목명이 안 뜨던 버그 예방책
                if stock_name == f"{code}.KS" or stock_name == f"{code}.KQ" or not stock_name:
                    stock_name = f"종목 [{code}]"

                return {"success": True, "name": stock_name, "price": current_price}

    except Exception as e:
        print(f"서버 우회 중 에러 발생: {e}")
        
    return {"success": False, "price": 0, "name": "조 scheme 실패"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)