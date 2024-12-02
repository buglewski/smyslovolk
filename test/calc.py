import time
import os
import requests
import asyncio
import aiohttp
from tqdm import tqdm
from main import get_password_hash

URL = 'http://127.0.0.1:8000/gen/admin/meow/'


class Api:
    def __init__(self, url: str):
        self.url = url

    def http_get(self, path: str, times: int):
        content = []
        for _ in tqdm(range(times), desc='Fetching data...', colour='GREEN'):
            response = requests.get(self.url + path)
            content.append(response.json())
        return content
    
    def http_get_with_session(self, path: str, times: int):
        content = []
        with requests.session() as session:
            for _ in tqdm(range(times), desc='Fetching data...', colour='GREEN'):
                response = session.get(self.url + path)
                content.append(response.json())
        return content
    
    async def async_http_get(self, path: str, times: int):
        async with aiohttp.ClientSession() as session:
            content = []
            for _ in tqdm(range(times), desc='Async fetching data...', colour='GREEN'):
                response = await session.get(url=self.url + path)
                content.append(await response.text(encoding='UTF-8'))
            return content
    

def run_case(func, path, times):
    start_timestamp = time.time()
    
    asyncio.run(func(path, times))

    task_time = round(time.time() - start_timestamp, 2)
    rps = round(times / task_time, 1)
    print(
        f"| Requests: {times}; Total time: {task_time} s; RPS: {rps}. |\n"
    )


if __name__ == '__main__':
    N = 10
    #api = Api(URL)

    #run_case(api.async_http_get, path='', times=N)
    #print(os.listdir("."))
    print(get_password_hash("333501"))

    