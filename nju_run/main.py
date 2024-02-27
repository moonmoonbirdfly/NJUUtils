# 肉体苦弱，赛博跑步，机械飞升！

import base64
import datetime
import hashlib
import json
import logging
import random
import time
import uuid
from io import BytesIO

import requests
from Crypto.Cipher import AES
from PIL import Image

logging.basicConfig(
    format="%(asctime)s - %(name)s[line:%(lineno)d] - %(levelname)s: %(message)s",
    level=logging.INFO,
)

DEVICE_CONSTANTS = {
    "mobileDeviceId": str(uuid.uuid4()),
    "mobileModel": "",
    "mobileOsVersion": "12",
    "ostype": "3",
    "version": "927",
    "versionName": "9.0.27",
    "token": "",
    "studentNum": "211250000",
    "uid": "1000123",
}

SIGN_KEY = "rDJiNB9j7vD2"

RESP_KEY = "Wet2C8d34f62ndi3".encode("ascii")
RESP_IV = "K6iv85jBD8jgf32D".encode("ascii")

API_URL = "https://kwpb.nju.edu.cn/v3/api.php"


def signed_params(extra_params=None):
    ret = DEVICE_CONSTANTS.copy()

    ret["nonce"] = str(random.randint(100000, 999999))
    ret["timestamp"] = str(int(time.time()))

    if extra_params:
        ret.update(extra_params)

    str2sign = (
        "".join(
            map(
                lambda x: str(x[0]) + str(x[1]), sorted(ret.items(), key=lambda x: x[0])
            )
        )
        + SIGN_KEY
    )

    ret["sign"] = hashlib.md5(str2sign.encode()).hexdigest()
    return ret


def aes_encrypt(data):
    pad = lambda s: s + (
        bytes([AES.block_size - len(s) % AES.block_size])
        * (AES.block_size - len(s) % AES.block_size)
    )
    cipher = AES.new(RESP_KEY, AES.MODE_CBC, RESP_IV)
    data = cipher.encrypt(pad(data))
    return base64.b64encode(data).decode("utf-8")


def aes_decrypt(b64_data):
    enc = base64.b64decode(b64_data)
    cipher = AES.new(RESP_KEY, AES.MODE_CBC, RESP_IV)
    unpad = lambda s: s[: -ord(s[len(s) - 1 :])]
    return unpad(cipher.decrypt(enc)).decode("utf-8")


def do_request(url, params=None):
    r = requests.get(
        API_URL + url,
        params=signed_params(params),
        headers={
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; M2011K2C Build/MRA58K)"
        },
    ).json()

    logging.debug("Response: " + str(r))

    if r["status"] != 1:
        raise Exception("API Error: " + r["info"])

    if "is_encrypt" in r and r["is_encrypt"]:
        return json.loads(aes_decrypt(r["data"]))
    else:
        return r.get("data", {})


def do_upload(content_type, data=None):
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

    random_path = str(int(random.randint(100, 999)))
    random_uuid = uuid.uuid4()

    type2path = {
        "text/plain": "file/run_record",
        "image/png": "pic/run_photo_screenshotImage",
    }
    type2suffix = {"text/plain": "txt", "image/png": "png"}

    target_path = f"Public/Upload/{type2path[content_type]}/{date_str}/{random_path}/{random_uuid}.{type2suffix[content_type]}"
    str2sign = f"PUT\n\n{content_type}\n{time_str}\n/lptiyu-data/{target_path}"

    logging.debug(str2sign)

    r = do_request("/Report/getOssSign", params={"content": str2sign})

    r = requests.put(
        "https://lptiyu-data.oss-cn-hangzhou.aliyuncs.com/" + target_path,
        headers={
            "Date": time_str,
            "Authorization": r["sign"],
            "Content-Type": content_type,
        },
        data=data,
    )

    if r.status_code != 200:
        raise Exception("OSS Error: " + r.text)

    return target_path


# from math import radians, sin, cos, sqrt, asin
#
# def haversine(lon1, lat1, lon2, lat2):
#     R = 6372.8  # 地球半径，单位：公里
#     dLat = radians(lat2 - lat1)
#     dLon = radians(lon2 - lon1)
#     lat1 = radians(lat1)
#     lat2 = radians(lat2)
#
#     a = sin(dLat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dLon / 2) ** 2
#     c = 2 * asin(sqrt(a))
#
#     return R * c


def fake_run():
    r = do_request("/User/User")
    logging.info("当前用户信息: " + str(r))

    logging.info("开始赛博跑步...")
    r = do_request("/Run2/beforeRunV260")
    logging.info("请求 beforeRun: " + str(r))

    r = do_request("/Run/getTimestampV278")
    logging.info("请求 getTimestamp: " + str(r))
    record_str = r["str"]
    logging.info("得到 record str: " + record_str)

    logging.info("=====生成数据中=====")

    c_list = [random.randint(300, 350) for _ in range(3)]
    b_list = [
        random.uniform(1.0, 1.0001),
        random.uniform(1.0, 1.0001),
        random.uniform(0.4, 0.6),
    ]

    end_time = str(int(time.time()))
    duration = int(c_list[0] + c_list[1] + c_list[2] * b_list[2])
    start_time = str(int(end_time) - duration)

    fake_step_list = [random.randint(150, 190) for _ in range(duration // 60)]
    fake_step_info = json.dumps({"interval": 60, "list": fake_step_list}).replace(
        " ", ""
    )
    total_steps = sum(fake_step_list) + int(
        duration % 60 / 60 * random.randint(150, 190)
    )

    distance_real = sum(b_list)
    distance = str(round(distance_real, 2))

    logging.info("开始时间: " + start_time)
    logging.info("结束时间: " + end_time)
    logging.info("持续时间: " + str(duration))
    logging.info("步频数据: " + str(fake_step_list))
    logging.info("总步数: " + str(total_steps))
    logging.info("距离: " + distance + " km")
    logging.info("配速: " + str(c_list))
    logging.info("公里数: " + str(b_list))

    fake_location_info = json.load(open("ref_location.json", "r"))

    counter = 0
    for i in range(len(fake_location_info)):
        fake_location_info[i]["o"] += random.uniform(-0.000006, 0.000006)
        fake_location_info[i]["a"] += random.uniform(-0.000006, 0.000006)
        fake_location_info[i]["s"] += random.uniform(-0.4, 0.4)
        if "b" in fake_location_info[i]:
            fake_location_info[i]["b"] = b_list[counter]
            fake_location_info[i]["c"] = c_list[counter]
            counter += 1

    fake_pic = Image.open("ref_pic.png")

    def random_crop(image):
        width, height = image.size
        crop_width = int(width * 0.1)
        crop_height = int(height * 0.1)
        left = random.randint(0, crop_width)
        top = random.randint(0, crop_height)
        right = width - random.randint(0, crop_width)
        bottom = height - random.randint(0, crop_height)
        cropped_image = image.crop((left, top, right, bottom))
        stretched_image = cropped_image.resize((width, height))

        with BytesIO() as output:
            stretched_image.save(output, format="PNG")
            bytes_data = output.getvalue()
            return bytes_data

    fake_pic = random_crop(fake_pic)

    logging.info("位置上报数据点: " + str(len(fake_location_info)))
    logging.info("截图大小: " + str(len(fake_pic)) + " bytes")
    logging.info("=====生成数据完成=====")

    for i in range(random.randint(8, 15)):
        random_rec = random.choice(fake_location_info)
        params = {
            "latitude": round(random_rec["a"], 6),
            "longitude": round(random_rec["o"], 6),
        }
        # do_request("/Run/setRunLocationRecord", params=params)
        logging.info("位置上报: " + str(params))

    logging.info("上传数据: 记录txt")
    txt_path = do_upload(
        "text/plain",
        BytesIO(
            aes_encrypt(
                json.dumps(fake_location_info).replace(" ", "").encode()
            ).encode()
        ),
    )
    logging.info("上传成功: " + txt_path)
    logging.info("上传数据: 截图")
    pic_path = do_upload("image/png", fake_pic)
    logging.info("上传成功: " + pic_path)

    # TODO: 时间模拟
    # TODO: 更好的轨迹文件生成与图片生成

    # for i in range(len(fake_location_info) - 1):
    #     print(haversine(fake_location_info[i]['o'], fake_location_info[i]['a'],
    #                     fake_location_info[i + 1]['o'], fake_location_info[i + 1]['a']) * 1000)
    #     print(fake_location_info[i], fake_location_info[i + 1])
    #
    # print(len(fake_location_info))

    params = signed_params(
        {
            "distance": distance,
            "end_time": int(end_time),
            "file_img": pic_path,
            "game_id": "2",
            "is_running_area_valid": "1",
            "newMobileDeviceId": "",
            "record_file": txt_path,
            "record_img": "",
            "record_str": record_str,
            "school_id": "769",
            "start_time": int(start_time),
            "step_info": str(fake_step_info),
            "step_num": str(total_steps),
            "term_id": "4765",
            "used_time": str(duration),
        }
    )

    logging.info("请求构造: " + json.dumps(params))

    r = requests.post(
        API_URL + "/Run/stopRunV278",
        data={"key": aes_encrypt(json.dumps(params).replace(" ", "").encode())},
    )

    logging.info("调用 stopRun: " + str(r.json()))
    logging.info("结果: " + str(json.loads(aes_decrypt(r.json()["data"]))))
    logging.info("赛博跑步完成!")


# print(do_request("/Run2/allRecordList", params={"year": "2023"}))
if __name__ == "__main__":
    fake_run()

# do_upload("image/png", open("ref_pic.png", "rb").read())

# print(json.dumps(do_request("/Run/recordDetailV270", params={"record_id": "385", "year_num": "2023"})))


# print(do_request("/RunStat/getAllScore", params={"term_id": "4765"}))
