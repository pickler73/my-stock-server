from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import json

app = FastAPI()

# 스마트폰이나 다른 기기에서 내 서버에 접속할 수 있도록 문을 열어주는 설정
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
        # 전 세계 어디서든 차단 걱정 없는 안정적인 주가 통로 (에프앤가이드 데이터 웹)
        url = f"https://m.stock.naver.com/api/stock/{code}/integration"
        
        # 실제 사람이 브라우저로 접속한 것처럼 네이버를 속이는 가면(헤더) 착용
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        
        # 데이터가 정상적으로 들어왔는지 확인
        if 'totalInfos' in data and data['totalInfos']:
            info = data['totalInfos'][0]
            stock_name = info.get('stockName', '알수없음')
            
            # 현재가 가져오기 (콤마 제거 후 숫자로 변환)
            price_str = info.get('closePrice', '0').replace(',', '')
            current_price = int(price_str)
            
            return {"success": True, "name": stock_name, "price": current_price}
            
        # 종목을 찾지 못한 경우 대안 경로 (네이버 페이 주가 API) 한번 더 시도
        alt_url = f"https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:{code}"
        alt_resp = requests.get(alt_url, headers=headers, timeout=5)
        alt_data = alt_resp.json()
        
        if 'result' in alt_data and 'areas' in alt_data['result'] and alt_data['result']['areas']:
            datas = alt_data['result']['areas'][0]['datas']
            if datas:
                stock_name = datas[0].get('nm', '알수없음')
                current_price = int(datas[0].get('nv', 0))
                return {"success": True, "name": stock_name, "price": current_price}

    except Exception as e:
        print(f"에러 발생: {e}")
        
    return {"success": False, "price": 0, "name": "조회 실패"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)