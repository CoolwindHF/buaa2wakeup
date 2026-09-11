import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import csv
import re
from datetime import datetime, timedelta, date
import uuid
import yaml
import os

import logging
logging.basicConfig(level=logging.INFO)

class login:
    SSO_LOGIN = 'https://sso.buaa.edu.cn/login'
    JWAPP = 'https://byxt.buaa.edu.cn/jwapp/sys/homeapp/index.do'
    SHCEDULE_URL = 'https://byxt.buaa.edu.cn/jwapp/sys/homeapp/api/home/student/getMyScheduleDetail.do'

    def __init__(self, username: str = '', password: str = '', term: str = ''):
        self.session = requests.session()
        self.username = username
        self.password = password
        self.term = term
        self.execution = None

        if not self.username or not self.password:
            logging.error("Username or password is empty.")
            return False

        if not self.term:
            logging.error("Term is empty.")
            return False

        if logging.getLogger().level == logging.DEBUG:
            self.session.proxies = {
                "http": "http://127.0.0.1:8080",
                "https": "http://127.0.0.1:8080",
            }
            from requests.packages import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            self.session.verify = False

    def get_execution(self):
        logging.info("Fetching execution value...")
        response = self.session.get(self.SSO_LOGIN,
            params={'service':self.JWAPP})
        soup = BeautifulSoup(response.text, 'html.parser')
        execution_input = soup.find('input', {'name': 'execution'})
        if execution_input:
            self.execution = execution_input['value']
        else:
            logging.error("Failed to find execution input field.")
            return False

        logging.info("Finished fetching execution value.")
        return True

    def login(self):

        logging.info("Starting login process...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            "Referer": self.SSO_LOGIN,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        response = self.session.post(
            self.SSO_LOGIN,
            data={
                'username': self.username,
                'password': self.password,
                'submit': quote('登录'),
                'type': 'username_password',
                'execution': self.execution,
                '_eventId': 'submit'
            },
            headers=headers,
            allow_redirects=False
        )
        if response.status_code != 302:
            logging.error("Login failed, please try again.")
            logging.debug(f"Response status code: {response.status_code =}, Response text: {response.text}")
            return False

        logging.info("Login successful.")
        relocation_url = response.headers.get('Location', '')
        if not relocation_url:
            logging.error("No relocation URL found after login.")
            return False

        logging.info(f"Redirecting to {relocation_url}")
        response = self.session.get(relocation_url, allow_redirects=True)

        final_url = response.url
        logging.info(f"Final URL after redirection: {final_url}")
        if final_url == self.JWAPP:
            logging.info("Successfully logged into the academic system.")
            return True

        logging.error("Failed to log into the academic system.")
        return False

    def get_schedule(self):
        logging.info("Fetching schedule...")
        response = self.session.post(
            self.SHCEDULE_URL,
            data = {
                'termCode': self.term,
                'campusCode': '',
                'type': 'term',
            }
        )

        try:
            return_json = response.json()
            # print(return_json)
            logging.info("Schedule fetched successfully.")
            return return_json
        except:
            logging.error("Failed to parse schedule response as JSON.")
            return None

    def run(self):
        if not self.get_execution():
            return False

        if not self.login():
            return False

        schedule = self.get_schedule()
        if schedule is None:
            return False

        data = schedule.get('datas', [])
        if not data:
            logging.error("No schedule data found.")
            return False

        arranged_list = data.get('arrangedList', [])
        if not arranged_list:
            logging.error("No arranged list found in schedule data.")
            return False

        return arranged_list

class convert:
    def __init__(self, schedule_list=[]):
        self.first_day = datetime.today()
        # 上课时间表，单位为北京时间 (UTC+8)
        self.daily_time = {
            1: ["08:00", "08:45"], 2: ["08:50", "09:35"],
            3: ["09:50", "10:35"], 4: ["10:40", "11:25"],
            5: ["11:30", "12:15"], 6: ["14:00", "14:45"],
            7: ["14:50", "15:35"], 8: ["15:50", "16:35"],
            9: ["16:40", "17:25"], 10: ["17:30", "18:15"],
            11: ["19:00", "19:45"], 12: ["19:50", "20:35"],
            13: ["20:40", "21:25"], 14: ["21:30", "22:15"],
        }
        self.raw_schedule_list = schedule_list
        self.parsed_schedule = []

    def parse_schedule(self):
        """
        解析从API获取的原始课程数据，转换为结构化的字典列表。
        这是核心处理步骤，为生成CSV和ICS文件做准备。
        """
        for each_class in self.raw_schedule_list:
            class_name = each_class.get("courseName", "N/A")
            class_day = each_class.get("dayOfWeek")
            beginSection = each_class.get("beginSection")
            endSection = each_class.get("endSection")
            place = each_class.get("placeName", "地点待定")
            credit = each_class.get("credit", "N/A")
            course_code = each_class.get("courseCode", "N/A")

            teacher_week_string = ""
            for detail in each_class.get("cellDetail", []):
                text = detail.get("text", "")
                if text and "[" in text and "]" in text:
                    teacher_week_string = text
                    break

            if not teacher_week_string:
                logging.warning(f"未能找到课程 '{class_name}' 的教师/周数信息，已跳过。")
                continue

            teacher_week_pairs = re.findall(r"([^\[\]]+?)\[([^\]]+)\]", teacher_week_string)

            for teacher_raw, weeks_raw in teacher_week_pairs:
                teacher = teacher_raw.strip() or "教师待定"

                weeks = weeks_raw.split(",")
                week_list = []
                for week in weeks:
                    # --- 修改开始：更稳健的周数清理逻辑 ---
                    # 替换所有干扰字符，生成干净的格式，如 '1-5单', '6-13', '7'
                    processed_week = week.replace("周", "").replace("(", "").replace(")", "")
                    # --- 修改结束 ---
                    week_list.append(processed_week)

                week_all = "、".join(week_list)

                parsed_class = {
                    "name": class_name,
                    "credit": credit,
                    "course_code": course_code,
                    "day": class_day,
                    "start_section": beginSection,
                    "end_section": endSection,
                    "teacher": teacher,
                    "place": place,
                    "weeks_str": week_all,
                }
                self.parsed_schedule.append(parsed_class)
        return True

    def write_to_csv(self, filename="schedule.csv"):
        """将解析后的课程数据写入CSV文件。"""
        logging.info(f"Writing schedule to {filename}...")

        headers = ["课程名称", "学分", "课程号", "星期", "开始节数", "结束节数", "老师", "地点", "周数"]

        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            for item in self.parsed_schedule:
                writer.writerow([
                    item["name"], item["credit"], item["course_code"],
                    item["day"], item["start_section"], item["end_section"],
                    item["teacher"], item["place"], item["weeks_str"],
                ])
        logging.info(f"Successfully wrote to {filename}.")
        return True

    def set_the_first_day_of_term(self, year, month, day):
        input_day = datetime(year, month, day)
        if input_day.weekday() != 0:
            logging.error("输入的日期不是周一，请重新输入！")
            return False
        self.first_day = datetime(year, month, day)
        return True

    def set_the_default_first_day_of_term(self):
        today = datetime.today()
        today_weekday = today.weekday()
        self.first_day = today - timedelta(days=today_weekday)
        logging.info(f"Set the first day：{self.first_day.strftime('%Y-%m-%d')}")
        return True

    def write_to_ical(self, filename="schedule.ics"):
        """将解析后的课程数据写入iCalendar (.ics) 文件。"""
        logging.info(f"Writing iCalendar file to {filename}...")

        beijing_tz = "BEGIN:VTIMEZONE\nTZID:Asia/Shanghai\nX-LIC-LOCATION:Asia/Shanghai\nBEGIN:STANDARD\nTZOFFSETFROM:+0800\nTZOFFSETTO:+0800\nTZNAME:CST\nDTSTART:19700101T000000\nEND:STANDARD\nEND:VTIMEZONE\n"

        with open(filename, "w", encoding="utf-8") as f:
            f.write("BEGIN:VCALENDAR\n")
            f.write("VERSION:2.0\n")
            f.write("PRODID:-//buaa2ical by CoolwindHF & Gemini//NONSGML v1.0//EN\n")
            f.write("CALSCALE:GREGORIAN\n")
            f.write(beijing_tz)

            for each_class in self.parsed_schedule:
                name = each_class["name"]
                day = each_class["day"]
                start_section = each_class["start_section"]
                end_section = each_class["end_section"]
                teacher = each_class["teacher"]
                place = each_class["place"]
                credit = each_class["credit"]
                course_code = each_class["course_code"]

                start_time_str = self.daily_time.get(int(start_section), ["00:00"])[0]
                end_time_str = self.daily_time.get(int(end_section), ["00:00"])[1]

                weeks = each_class["weeks_str"].split("、")
                for week_range in weeks:
                    week_parts = week_range.split("-")
                    interval = 1
                    is_odd_even = None

                    if len(week_parts) == 1:
                        if "单" in week_parts[0]:
                            start_week = int(week_parts[0][:-1])
                            end_week = start_week
                            is_odd_even = '单'
                        elif "双" in week_parts[0]:
                            start_week = int(week_parts[0][:-1])
                            end_week = start_week
                            is_odd_even = '双'
                        else:
                            start_week = int(week_parts[0])
                            end_week = start_week
                    else:
                        start_week = int(week_parts[0])
                        if "单" in week_parts[1]:
                            end_week = int(week_parts[1][:-1])
                            is_odd_even = '单'
                        elif "双" in week_parts[1]:
                            end_week = int(week_parts[1][:-1])
                            is_odd_even = '双'
                        else:
                            end_week = int(week_parts[1])

                    first_class_date = self.first_day + timedelta(days=(int(day) - 1) + (start_week - 1) * 7)
                    if is_odd_even == '单' and start_week % 2 == 0:
                        first_class_date += timedelta(weeks=1)
                    elif is_odd_even == '双' and start_week % 2 != 0:
                        first_class_date += timedelta(weeks=1)

                    if is_odd_even:
                        interval = 2

                    dtstart_str = f"{first_class_date.strftime('%Y%m%d')}T{start_time_str.replace(':', '')}00"
                    dtend_str = f"{first_class_date.strftime('%Y%m%d')}T{end_time_str.replace(':', '')}00"

                    # --- 核心修正 ---
                    # 正确计算最后一节课的日期
                    last_class_date = self.first_day + timedelta(days=(int(day) - 1) + (end_week - 1) * 7)
                    # 将 UNTIL 日期设置为最后一节课当天的结束时间，确保包含最后一节课
                    until_str = last_class_date.strftime("%Y%m%d") + "T235959Z"
                    # --- 修正结束 ---

                    f.write("BEGIN:VEVENT\n")
                    f.write(f"UID:{uuid.uuid4()}@buaa.edu.cn\n")
                    from datetime import timezone
                    f.write(f"DTSTAMP:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}\n")
                    f.write(f"DTSTART;TZID=Asia/Shanghai:{dtstart_str}\n")
                    f.write(f"DTEND;TZID=Asia/Shanghai:{dtend_str}\n")

                    description = (
                        f"教师: {teacher}\\n"
                        f"周数: {week_range}周\\n"
                        f"节数: {start_section}-{end_section}节\\n"
                        f"学分: {credit}\\n"
                        f"课程号: {course_code}"
                    )
                    f.write(f"DESCRIPTION:{description}\n")
                    f.write(f"LOCATION:{place}\n")
                    f.write(f"SUMMARY:{name}\n")

                    if start_week != end_week or is_odd_even:
                        f.write(f"RRULE:FREQ=WEEKLY;INTERVAL={interval};UNTIL={until_str}\n")

                    f.write("END:VEVENT\n")
            f.write("END:VCALENDAR\n")
        logging.info(f"Successfully wrote to {filename}.")


if __name__ == "__main__":
    if not os.path.exists("config.yaml"):
        logging.error("File `config.yaml` isn't exist, please create one.")
        exit(1)

    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    username = config.get("username", "")
    password = config.get("password", "")
    term = config.get("term", "")
    first_day_input : date = config.get("first_day_of_term", None)
    if first_day_input:
        year, month, day = first_day_input.year, first_day_input.month, first_day_input.day
    else:
        year = month = day = None

    obj = login(username, password, term)
    schedule = obj.run()
    if not schedule:
        logging.error("Failed to retrieve schedule.")
        exit(1)

    conv = convert(schedule_list=schedule)
    if year and month and day:
        if not conv.set_the_first_day_of_term(year, month, day):
            exit(1)
    else:
        conv.set_the_default_first_day_of_term()

    # 按顺序执行：解析 -> 写CSV -> 写ICS
    conv.parse_schedule()
    conv.write_to_csv()
    conv.write_to_ical()
    print("任务完成！已生成 schedule.csv 和 schedule.ics 文件。")


