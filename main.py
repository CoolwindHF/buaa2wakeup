import csv
import uuid
from datetime import datetime, timedelta
import re
import requests
from bs4 import BeautifulSoup
from requests.packages import urllib3

urllib3.disable_warnings()


def login(id, passwd):

    def get_execution():
        cookies = {
            '_7da9a': 'http://10.0.3.35:8080',
        }

        headers = {
            'Host': 'sso.buaa.edu.cn',
        }

        params = {
            'service': 'https://byxt.buaa.edu.cn/jwapp/sys/homeapp/index.do',
        }

        response = requests.get('https://sso.buaa.edu.cn/login', params=params,
                                cookies=cookies, headers=headers)
        # print(response.text)
        soup = BeautifulSoup(response.text, 'html.parser')
        execution = soup.find('input', {'name': 'execution'}).get('value')
        # print(execution)
        return execution

    def get_location(id, passwd, execution):
        cookies = {
            '_7da9a': 'http://10.0.3.35:8080',
        }

        headers = {
            'Host': 'sso.buaa.edu.cn',
        }

        data = {
            'username': id,
            'password': passwd,
            'submit': '登录',
            'type': 'username_password',
            'execution': execution,
            '_eventId': 'submit',
        }

        response = requests.post('https://sso.buaa.edu.cn/login', cookies=cookies,
                                 headers=headers, data=data, allow_redirects=False)
        # print(response.headers)
        CASTGC = response.headers.get(
            'Set-Cookie').split(';')[0].split('=')[-1]
        location = response.headers.get(
            "Location").strip().split('=')[-1]  # ticket
        # print(CASTGC)
        # print(location)
        return location

    def get_gs_sessionid(location):
        headers = {
            'Host': 'byxt.buaa.edu.cn',
        }

        params = {
            "ticket": location,
        }

        response = requests.get('https://byxt.buaa.edu.cn/jwapp/sys/homeapp/index.do',
                                params=params, headers=headers, allow_redirects=False)

        # print(response.headers)
        import re
        pattern = r'GS_SESSIONID=([0-9a-f]{32});'
        match = re.search(pattern, response.headers.get("Set-Cookie").strip())
        if match:
            gs_sessionid = match.group(1)
            # print(gs_sessionid)
            return gs_sessionid
        else:
            print("GS_SESSIONID not found!")

    def get_WEU(gs_sessionid):
        # print(gs_sessionid)
        cookies = {
            'GS_SESSIONID': gs_sessionid,
        }

        headers = {
            'Host': 'byxt.buaa.edu.cn',
        }

        response = requests.get('https://byxt.buaa.edu.cn/jwapp/sys/homeapp/index.do',
                                cookies=cookies, headers=headers, allow_redirects=True)
        # print(response.headers)
        _WEU = response.headers.get(
            "Set-Cookie").strip().split(",")[-1].split(";")[0].split("=")[-1]
        # print(_WEU)
        return _WEU

    execution = get_execution()
    location = get_location(id, passwd, execution)
    gs_sessionid = get_gs_sessionid(location)
    _WEU = get_WEU(gs_sessionid)
    return gs_sessionid, _WEU


def get_schedule(gs_sessionid, _WEU, term):
    cookies = {
        'GS_SESSIONID': gs_sessionid,
        '_WEU': _WEU,
    }

    headers = {
        'Host': 'byxt.buaa.edu.cn',
    }

    data = {
        'termCode': term,
        'campusCode': '',
        'type': 'term',
    }

    response = requests.post(
        'https://byxt.buaa.edu.cn/jwapp/sys/homeapp/api/home/student/getMyScheduleDetail.do',
        cookies=cookies,
        headers=headers,
        data=data,
        verify=False,
    )
    # print(response.text)
    # print(response.content.decode('utf-8'))

    schedule_json = response.json()
    schedule_list = schedule_json["datas"]["arrangedList"]
    return schedule_list


def convert_schedule_to_csv(schedule_list):
    with open("schedule.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["课程名称", "星期", "开始节数", "结束节数", "老师", "地点", "周数"])
    list_for_csv = []

    for each_class in schedule_list:
        class_name = each_class["courseName"]
        class_day = each_class["dayOfWeek"]
        beginSection = each_class["beginSection"]
        endSection = each_class["endSection"]
        place = each_class["placeName"]
        weeks_and_teachers = each_class["cellDetail"][1]["text"].split(" ")
        for i in weeks_and_teachers:
            append_list = []
            find = re.findall(r"(.*?)\[(.*?)\]", i)
            teacher = find[0][0]
            weeks = find[0][1].split(",")
            week_list = []
            for week in weeks:
                if re.findall(r"单", week):
                    week = week[:-4]
                    week += "单"
                elif re.findall(r"双", week):
                    week = week[:-4]
                    week += "双"
                else:
                    week = week[:-1]
                week_list.append(week)
                week_all = "、".join(week_list)
            append_list.append(class_name)
            append_list.append(class_day)
            append_list.append(beginSection)
            append_list.append(endSection)
            append_list.append(teacher)
            append_list.append(place)
            append_list.append(week_all)
            list_for_csv.append(append_list)

    with open("schedule.csv", "a") as f:
        writer = csv.writer(f)
        writer.writerows(list_for_csv)

    return list_for_csv


daily_time = {
    1: ["000000", "004500"],
    2: ["005000", "013500"],
    3: ["015000", "023500"],
    4: ["024000", "032500"],
    5: ["033000", "041500"],
    6: ["060000", "064500"],
    7: ["065000", "073500"],
    8: ["075000", "083500"],
    9: ["084000", "092500"],
    10: ["093000", "101500"],
    11: ["110000", "114500"],
    12: ["115000", "123500"],
    13: ["124000", "132500"],
    14: ["133000", "141500"],
}

first_day_of_term = datetime(2024, 9, 10)


def set_the_first_day_of_term(year, month, day):
    global first_day_of_term
    input_day = datetime(year, month, day)
    if input_day.weekday() != 0:
        print("输入的日期不是周一，请重新输入！")
        return False
    first_day_of_term = datetime(year, month, day)
    return True


def set_the_default_first_day_of_term():
    global first_day_of_term
    today = datetime.today()
    today_weekday = today.weekday()
    if today_weekday != 0:
        first_day_of_term = today - timedelta(days=today_weekday)
    else:
        first_day_of_term = today


def convert_schedule_to_icaleander(list_for_csv):
    with open("schedule.ics", "w") as f:
        f.write("BEGIN:VCALENDAR\n")
        f.write("VERSION:2.0\n")
        f.write("PRODID:-//hacksw/handcal//NONSGML v1.0//EN\n")
        f.write("CALSCALE:GREGORIAN\n")
        for each_class in list_for_csv:
            name = each_class[0]
            day = each_class[1]
            start_section = each_class[2]
            end_section = each_class[3]
            teacher = each_class[4]
            place = each_class[5]
            weeks = each_class[6].split("、")
            for week in weeks:
                f.write("BEGIN:VEVENT\n")
                f.write("UID:buaa2ical-{}-CoolwindHF\n".format(str(uuid.uuid4())))
                # print(week)
                week = week.split("-")
                every_2_weeks = False
                if len(week) == 1:
                    start_week = int(week[0])
                    end_week = int(week[0])
                else:
                    if re.findall(r"单|双", week[1]):
                        every_2_weeks = True
                        start_week = int(week[0])
                        end_week = int(week[1][:-1])
                    else:
                        start_week = int(week[0])
                        end_week = int(week[1])
                start_day = (first_day_of_term + timedelta(days=(int(day) -
                             1) + (int(start_week) - 1) * 7)).strftime("%Y%m%d")
                end_day = (first_day_of_term + timedelta(days=(int(day) -
                           1) + (int(end_week) - 1) * 7)).strftime("%Y%m%d")
                DTSTART = start_day + "T" + \
                    daily_time[int(start_section)][0] + "Z"
                DTEND = start_day + "T" + daily_time[int(end_section)][1] + "Z"
                f.write("DTSTART:{}\n".format(DTSTART))
                f.write("DTEND:{}\n".format(DTEND))
                if len(week) == 1:
                    description = f"第{start_week}周\\n第{start_section} - {end_section}节\\n{place}\\n{teacher}\\n"
                else:
                    if not every_2_weeks:
                        description = f"第{start_week} - {end_week}周\\n第{start_section} - {end_section}节\\n{place}\\n{teacher}\\n"
                    else:
                        description = f"第{start_week} - {end_week}{week[1][-1:]}周\\n第{start_section} - {end_section}节\\n{place}\\n{teacher}\\n"
                f.write(f"DESCRIPTION:{description}\n")
                f.write(f"SUMMARY:{name}\n")
                f.write(f"LOCATION:{place} {teacher}\n")
                if not every_2_weeks:
                    f.write(f"RRULE:FREQ=WEEKLY;INTERVAL=1;UNTIL={end_day}\n")
                else:
                    f.write(f"RRULE:FREQ=WEEKLY;INTERVAL=2;UNTIL={end_day}\n")
                f.write("END:VEVENT\n")
        f.write("END:VCALENDAR\n")


if __name__ == "__main__":
    id = input("请输入统一认证学号：").strip()
    import getpass
    passwd = getpass.getpass("请输入统一认证密码：").strip()
    gs_session, _WEU = login(id, passwd)
    print("账号{}登陆成功！".format(id))
    year = input("请输入学年，如“2024-2025-1”代表2024-2025学年第一学期：").strip()
    schedule_list = get_schedule(gs_session, _WEU, year)
    # print(schedule_list)
    list_for_csv = convert_schedule_to_csv(schedule_list)
    print("课程表已保存为schedule.csv文件！请发送到手机后导入wakeup课程表！")
    to_ical = input("是否将课程表转换为iCalendar文件？(y/n):").strip()
    if to_ical == "y":
        while True:
            first_day = input(
                "请输入学期第一周的周一日期，如“2024-09-02”，直接回车跳过默认以当前周作为学期第一周：").strip().split("-")
            if len(first_day) != 3:
                set_the_default_first_day_of_term()
            else:
                year, month, day = first_day[0], first_day[1], first_day[2]
                if not set_the_first_day_of_term(int(year), int(month), int(day)):
                    continue
            break
        convert_schedule_to_icaleander(list_for_csv)
        print("课程表已保存为schedule.ics文件！请导入日历软件！")
