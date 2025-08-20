import requests

request_url = "https://aip.baidubce.com/api/v1/solution/direct/imagerecognition/combination"

params = "{\"imgUrl\":\"http://127.0.0.1:8000/media/dishes/2_1755145342_R-C.png\",\"scenes\":[\"dishs\"]}"
access_token = '24.e79a10837efd9b83217bf7ab7b34cc51.2592000.1757688481.282335-119765408'
request_url = request_url + "?access_token=" + access_token
headers = {'content-type': 'application/json'}
response = requests.post(request_url, data=params, headers=headers)
if response:
    print (response.json())
