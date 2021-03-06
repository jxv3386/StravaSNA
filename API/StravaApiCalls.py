import ast
import json
from os import listdir
from os.path import isfile, join
from pathlib import Path
from ratelimit import limits,sleep_and_retry
import pandas as pd
import requests


# never needs to be called again


def initDF():
    df = pd.DataFrame(columns=["email", "clientId", "password", "clientSecret", "refreshToken", "accessToken", "expireIn"])
    df.loc[len(df.index)] = ["jedicavebros@gmail.com","73426","secrldrasterls1","5f70bc1fab8a57d286aa98b9bf375b3d8971e1e1", "3eda2676ef9d1e0bf1a8e2c6db980bbb01b5a6cf","3f06bafe093fe2292f0e1704ef755b96dd24883a", "1635195521"]
    # df.loc[len(df.index)] = ["jedicavebros0001@gmail.com", "secrldrasterls1", "a6ec91cb7cf1ba167af25945671c3ecfd1422b69","7c17702e1cccd6786b139c963a7bd9ffac9ca80f", "fde88c316f792aba6b73cb6dcb98836840e94b09", "1635195910"]
    print(df)
    df.to_csv('loginInformation.csv', index=False)
    return



# call this everytime before making an api call to verify that the auth token has not expired
def refreshAccessToken(index):
    df = pd.read_csv('loginInformation.csv')
    user = df.loc[index]
    print(user["clientId"])
    params = {"client_id":user["clientId"], "client_secret":user["clientSecret"], "grant_type": "refresh_token", "refresh_token":user["refreshToken"]}
    r = requests.post('https://www.strava.com/api/v3/oauth/token',params=params)
    responseJson = json.loads(r.content)
    print(responseJson)
    accessToken = responseJson["access_token"]
    expireAt = responseJson["expires_at"]
    refreshToken = responseJson["refresh_token"]
    df.loc[index, "accessToken"]= accessToken
    df.loc[index, "expireAt"]= expireAt
    df.loc[index, "refreshToken"] = refreshToken
    df.to_csv('loginInformation.csv', index=False)
@sleep_and_retry
@limits(calls=100, period=60*15)
@sleep_and_retry
@limits(calls=1000, period=60*60*24)
def getSegmentMetaData(segment,accessToken):
    r = requests.get(f"https://www.strava.com/api/v3/segments/{str(segment)}",
                     headers={"Authorization": f"Bearer {accessToken}"})
    responseJson = json.loads(r.content)

    base_path = Path(__file__).parent
    file_path = (base_path / f"../Data/Master/SegmentMetaData/{str(segment)}.json").resolve()

    if 'message' not in responseJson or responseJson["message"] != "Rate Limit Exceeded":
        out_file = open(file_path, "w")
        json.dump(responseJson, out_file, indent=6)
        out_file.close()

def getAllSegmentMetaData(index):

    df = pd.read_csv('loginInformation.csv')
    user = df.loc[index]
    accessToken=user['accessToken']
    base_path = Path(__file__).parent
    file_path = (base_path / "../Data/Master/segmentList.txt").resolve()
    with open(file_path, 'r') as f:
        allSegments = list(map(int, list(ast.literal_eval(f.read()))))

    file_path = (base_path / "../Data/Master/SegmentMetaData").resolve()
    currentSegments = [int(f[:-5]) for f in listdir(file_path) if isfile(join(file_path, f))]
    newSegments = set(allSegments) - set(currentSegments)
    for segment in newSegments:
        getSegmentMetaData(segment,accessToken)
        print(segment)

def main():
    refreshAccessToken(1)
    getAllSegmentMetaData(1)


if __name__ == '__main__':
    main()