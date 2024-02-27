# 抢课脚本
# 下面一大堆选项自己看着改

import base64
import json
import random
import sys
import time

import requests

STUDENT_NUMBER = "211250000"
# ENCRYPTED_PASSWORD 最简单的获取方法是网页登录 XHR 抓一下
ENCRYPTED_PASSWORD = "xxxxx"
BATCH_CODE = "xxxxx"
# 抢到一门就退出 (防止不同课之间有替换关系)
EXIT_ON_FIRST_SUCCESS = False

# 对着一门课抢 (一般用于抢课开始前, 且只有一节最想抢的课)
DEAD_LOOP_FOR_ONE = False

# 强制清空收藏列表并使用自定义的列表抢课
FORCE_INTERNAL_LIST = True
TARGET_COURSES = [
    {"teachingClassID": "2023202412201114001", "teachingClassType": "KZY"}
]


def list_sleep_():
    time.sleep(random.random() * 0.0 + 1)


def grab_sleep_():
    time.sleep(random.random() * 0.0 + 0.5)


course_kind_table = {
    "ZY": "1",
    "TY": "2",
    "GG01": "4",
    "GG02": "6,7",
    "KZY": "12",
    "TX01": "13",
    "TX02": "14",
    "TX03": "15",
    "TX04": "16",
}


# 登录账号
def get_session():
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
            "Referer": "https://xk.nju.edu.cn/xsxkapp/sys/xsxkapp/*default/index.do",
        }
    )

    code = session.post(
        "https://xk.nju.edu.cn/xsxkapp/sys/xsxkapp/student/4/vcode.do"
    ).json()
    token = code["data"]["token"]

    pic = session.get(
        "https://xk.nju.edu.cn/xsxkapp/sys/xsxkapp/student/vcode/image.do?vtoken="
        + token
    ).content
    pic_res = requests.post(
        "https://captcha.994321.xyz/ocr/b64/json", data=base64.b64encode(pic)
    ).json()

    r = session.post(
        "https://xk.nju.edu.cn/xsxkapp/sys/xsxkapp/student/check/login.do",
        data={
            "loginName": STUDENT_NUMBER,
            "loginPwd": ENCRYPTED_PASSWORD,
            "verifyCode": pic_res["result"],
            "vtoken": token,
        },
    ).json()

    print(r)
    assert r["msg"] == "登录成功"

    login_token = r["data"]["token"]

    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
            "Referer": "https://xk.nju.edu.cn/xsxkapp/sys/xsxkapp/*default/index.do",
            "token": login_token,
        }
    )

    r = session.post(
        "https://xk.nju.edu.cn/xsxkapp/sys/xsxkapp/student/xkxf.do",
        data={"xh": STUDENT_NUMBER, "xklcdm": BATCH_CODE},
    ).json()

    print(r)
    assert r["msg"] == "查询学生基础信息成功"

    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
            "Referer": "https://xk.nju.edu.cn/xsxkapp/sys/xsxkapp/*default/grablessons.do?token="
            + login_token,
            "token": login_token,
        }
    )
    return session


# 删除所有收藏并添加指定的课程
def sync_fav_list():
    print(">>>正在同步收藏列表")
    for i in get_fav_list()["dataList"]:
        delete_payload = {
            "data": {
                "operationType": "2",
                "studentCode": STUDENT_NUMBER,
                "electiveBatchCode": BATCH_CODE,
                "teachingClassId": i["teachingClassID"],
                "courseKind": course_kind_table.get(i["teachingClassType"]),
                "teachingClassType": i["teachingClassType"],
            }
        }
        print("删除现有课程: " + str(delete_payload))
        r = session.post(
            "https://xk.nju.edu.cn/xsxkapp/sys/xsxkapp/elective/favorite.do",
            data={"addParam": json.dumps(delete_payload)},
        )
        print(r.text)

    for i in TARGET_COURSES:
        add_payload = {
            "data": {
                "operationType": "1",
                "studentCode": STUDENT_NUMBER,
                "electiveBatchCode": BATCH_CODE,
                "teachingClassId": i["teachingClassID"],
                "courseKind": course_kind_table.get(i["teachingClassType"]),
                "teachingClassType": i["teachingClassType"],
            }
        }

        print("添加课程: " + str(add_payload))
        r = session.post(
            "https://xk.nju.edu.cn/xsxkapp/sys/xsxkapp/elective/favorite.do",
            data={"addParam": json.dumps(add_payload)},
        )
        print(r.text)
    print(">>>同步收藏列表完成")
    pass


# 获取收藏课程列表
def get_fav_list():
    r = session.post(
        "https://xk.nju.edu.cn/xsxkapp/sys/xsxkapp/elective/queryfavorite.do",
        data={
            "querySetting": '{"data":{"studentCode":"'
            + STUDENT_NUMBER
            + '","electiveBatchCode":"'
            + BATCH_CODE
            + '","teachingClassType":"SC","queryContent":""},"pageSize":"10","pageNumber":"0","order":"isChoose -"}'
        },
    ).json()
    print("获取收藏列表: " + str(r))
    list_sleep_()
    return r


def clear_status(classId):
    r = session.post(
        "https://xk.nju.edu.cn/xsxkapp/sys/xsxkapp/elective/studentstatus.do",
        data={"studentCode": STUDENT_NUMBER, "type": "1", "teachingClassId": classId},
    )
    return r.json()


def grab_class(data):
    while True:
        print(data)
        add_param_payload = (
            '{"data":{"operationType":"1","studentCode":"'
            + data["studentCode"]
            + '","electiveBatchCode":"'
            + data["electiveBatchCode"]
            + '","teachingClassId":"'
            + data["teachingClassID"]
            + '","courseKind":"'
            + (course_kind_table.get(data["teachingClassType"]) or "")
            + '","teachingClassType":"'
            + data["teachingClassType"]
            + '"}}'
        )

        print(add_param_payload)
        r = session.post(
            "https://xk.nju.edu.cn/xsxkapp/sys/xsxkapp/elective/volunteer.do",
            data={"addParam": add_param_payload},
        )
        print(r.text)
        print("Request Done Time: " + r.headers["Date"])

        r = clear_status(data["teachingClassID"])
        print(r)
        grab_sleep_()

        if not DEAD_LOOP_FOR_ONE:
            return r


if __name__ == "__main__":
    session = get_session()

    if FORCE_INTERNAL_LIST:
        sync_fav_list()

    while True:
        courses = get_fav_list()["dataList"]
        if len(courses) == 0:
            break

        for i in courses:
            if i["numberOfFirstVolunteer"] != "已满" and i["isChoose"] is None:
                r = grab_class(i)

                if EXIT_ON_FIRST_SUCCESS and r["code"] == "1":
                    sys.exit(0)
