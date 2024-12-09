'''
Author: he4966
'''
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse, parse_qs
from hashlib import md5
from datetime import datetime
from fastapi.responses import HTMLResponse
import os
from fastapi import FastAPI
import time

app = FastAPI()

def setup_driver():
    try:
        # 设置Chrome选项
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 无界面模式
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
            
        # 设置 Selenium Grid 的 URL
        grid_url = "http://127.0.0.1:24444"
        # 设置所需的浏览器驱动能力
        capabilities = DesiredCapabilities.CHROME
        capabilities["browserName"] = "chrome"
        # 初始化 WebDriver 对象
        driver = webdriver.Remote(command_executor=grid_url, desired_capabilities=capabilities)
        # 设置浏览器窗口大小
        driver.set_window_size(1200,789)
        # 初始化driver
        # driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        raise Exception(f"设置驱动程序时出错: {str(e)}")

@app.get("/search")
async def search(q: str, gl: str = "us", pws: str = "0", hl: str = "en", lr: str = "lang_en"):
    driver = None
    try:
        # 构建Google搜索URL
        base_url = "http://www.google.com/search"
        params = {
            "q": q,
            "gl": gl,
            "pws": pws,
            "hl": hl,
            "lr": lr
        }

         # 生成当前日期字符串
        date_str = datetime.now().strftime('%Y%m%d')
        
        # 生成参数字符串并计算MD5
        param_str = f"{date_str}_{q}_{gl}_{pws}_{hl}_{lr}"
        filename_hash = md5(param_str.encode()).hexdigest()

           
        # 创建存储目录
        save_dir = "search_results"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        # 生成文件名
        filename = os.path.join(save_dir, f"{filename_hash}.html")
        
        
        # 如果文件已存在且不超过24小时，直接返回缓存内容
        if os.path.exists(filename):
            file_time = datetime.fromtimestamp(os.path.getmtime(filename))
            if (datetime.now() - file_time).days < 1:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                return HTMLResponse(content=content)
        
        # 构建查询URL
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{base_url}?{query_string}"
        
        driver = setup_driver()
        if not driver:
            return {
                "status": "error",
                "message": "无法初始化浏览器驱动"
            }
        
        try:
            driver.get(full_url)
            page_source = driver.page_source
            
            # 保存结果
            with open(filename, "w", encoding="utf-8") as f:
                f.write(page_source)
            
            # 直接返回HTML内容
            return HTMLResponse(content=page_source)
            
        finally:
            if driver:
                try:
                    driver.close()
                except:
                    pass
                try:
                    driver.quit()
                except:
                    pass
                
    except Exception as e:
        return {
            "status": "error",
            "message": f"搜索过程中出错: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)