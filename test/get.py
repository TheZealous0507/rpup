# encoding:utf-8
import requests 

host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=kZcGpvWdRsvRt9IcuWOpHfq8&client_secret=VhefhxqV5OaDirZ3zEMsQavECvKnDCMw'
response = requests.get(host)
if response:
    print(response.json())
