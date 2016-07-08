from abc import abstractmethod
import json
import requests


class PushMessage:
    @abstractmethod
    def send_single(self, device_type, credentials, message):
        pass

    @abstractmethod
    def send_broadcast(self, device_type, credentials, message, clients):
        pass


class BmobPushMessage(PushMessage):
    def __init__(self):
        # self.BMOB_APPLICATION_ID = '68b1340c9b81500e3fd31f1d14586dc7'
        # self.BMOB_REST_API_KEY = '174730808c50dd82c4bb6c73d24ce639'
        self.BMOB_APPLICATION_ID = 'a23c4bcdcd1b1817e2abdcd83322c895'
        self.BMOB_REST_API_KEY = 'a7a1a2484f0608432ae6390e806931a7'
        self.BMOB_PUSH_URL = 'https://api.bmob.cn/1/push'

    def send_single(self, device_type, credential, message):
        headers = {
            "X-Bmob-Application-Id": self.BMOB_APPLICATION_ID,
            "X-Bmob-REST-API-Key": self.BMOB_REST_API_KEY,
            "Content-Type": 'application/json',
        }
        if device_type == 'ios':
            data = {
                "where": {
                    "deviceToken": credential
                },
                "data": {
                    "aps": {"alert": message, "badge": 1, "sound": "cheering.caf"}
                }
            }
        elif device_type == 'android':
            data = {
                "where": {
                    "installationId": credential
                },
                "data": {
                    "alert": message
                }
            }
        else:
            # Windows Phone
            data = {
                "where": {
                    "notificationUri": credential
                },
                "data": {
                    "alert": message,
                    "wpAlert": "bmob",
                    "wp": 2
                }
            }

        res = requests.post(self.BMOB_PUSH_URL, data=json.dumps(data), headers=headers)
        content = res.content.decode()
        if content.find('"result":true') == -1:
            print(content)
            print(data)

    @staticmethod
    def send_broadcast(self, device_type, credentials, message, clients):
        # TODO: Push broadcast
        pass