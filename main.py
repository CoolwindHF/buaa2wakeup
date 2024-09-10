import requests
from bs4 import BeautifulSoup
from requests.packages import urllib3

urllib3.disable_warnings()

def getpass_echo(prompt='Password: ', stream=None, placeholder='*'):
    """Prompt for password with echo on, using Windows getwch()."""
    
    try:
        import msvcrt
        import sys
        if sys.stdin is not sys.__stdin__:
            raise Exception("stdin is wrong.")
    except Exception as e:
        print("回退到默认方法... ")
        import getpass
        return getpass.getpass(prompt, stream)
    
    def repaint(old_len = 0, len = 0):
        msvcrt.putwch('\r')
        for c in prompt:
            msvcrt.putwch(c)
        for i in range(len):
            msvcrt.putwch(placeholder)
        for i in range(len, old_len):
            msvcrt.putwch(' ')
        if len < old_len:
            repaint(len, len)
    
    pw = ""
    repaint()
    while 1:
        c = msvcrt.getwch()
        if c == '\r' or c == '\n':
            break
        if c == '\003':
            raise KeyboardInterrupt
        if c == '\b':
            l = len(pw)
            pw = pw[:-1]
            repaint(l, len(pw))
        elif c == '\xe0':
            # Special code... 
            msvcrt.putwch('\a')
            msvcrt.getwch() # Skip it.
        else:
            pw = pw + c
            msvcrt.putwch(placeholder)
            
    msvcrt.putwch('\r')
    msvcrt.putwch('\n')
    return pw


def login(id, passwd):
    
    def get_execution():
        cookies = {
            '_7da9a': 'http://10.0.3.60:8080',
        }

        headers = {
            'Host': 'sso.buaa.edu.cn',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.100 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Ch-Ua': '"Chromium";v="127", "Not)A;Brand";v="99"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Accept-Language': 'zh-CN',
            'Referer': 'https://byxt.buaa.edu.cn/',
            'Priority': 'u=0, i',
            'Connection': 'keep-alive',
        }

        params = {
            'service': 'https://byxt.buaa.edu.cn/jwapp/sys/homeapp/index.do',
        }

        response = requests.get('https://sso.buaa.edu.cn/login', params=params, cookies=cookies, headers=headers, verify=False, allow_redirects=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        execution = soup.find('input', {'name': 'execution'}).get('value')
        # print(execution)
        return execution
    
    def get_location(id, passwd, execution):
        cookies = {
            '_7da9a': 'http://10.0.3.60:8080',
        }

        headers = {
            'Host': 'sso.buaa.edu.cn',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Chromium";v="127", "Not)A;Brand";v="99"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Accept-Language': 'zh-CN',
            'Upgrade-Insecure-Requests': '1',
            'Origin': 'https://sso.buaa.edu.cn',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.100 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Referer': 'https://sso.buaa.edu.cn/login?service=https%3A%2F%2Fbyxt.buaa.edu.cn%2Fjwapp%2Fsys%2Fhomeapp%2Findex.do',
            'Priority': 'u=0, i',
            'Connection': 'keep-alive',
        }

        data = {
            'username': id,
            'password': passwd,
            'submit': '登录',
            'type': 'username_password',
            'execution': execution,
            '_eventId': 'submit',
        }

        response = requests.post('https://sso.buaa.edu.cn/login', cookies=cookies, headers=headers, data=data, verify=False, allow_redirects=False)
        # print(response.headers)
        # CASTGC = response.headers.get('Set-Cookie').split(';')[0].split('=')[-1]
        location = response.headers.get("Location").strip().split("=")[-1]
        # print(CASTGC)
        return location

    def get_gs_sessionid(location):
        headers = {
            'Host': 'byxt.buaa.edu.cn',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.100 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Ch-Ua': '"Chromium";v="127", "Not)A;Brand";v="99"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Accept-Language': 'zh-CN',
            'Referer': 'https://sso.buaa.edu.cn/',
            # 'Accept-Encoding': 'gzip, deflate, br',
            'Priority': 'u=0, i',
            'Connection': 'keep-alive',
        }

        params = {
            "ticket": location,
        }

        response = requests.get('https://byxt.buaa.edu.cn/jwapp/sys/homeapp/index.do', params=params, headers=headers, verify=False, allow_redirects=False)

        # print(response.headers)
        gs_sessionid = response.headers.get("Set-Cookie").strip().split(";")[0].split("=")[-1]
        return gs_sessionid
    
    def get_WEU(gs_sessionid):
        cookies = {
            'GS_SESSIONID': gs_sessionid,
        }

        headers = {
            'Host': 'byxt.buaa.edu.cn',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.100 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Ch-Ua': '"Chromium";v="127", "Not)A;Brand";v="99"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Accept-Language': 'zh-CN',
            'Referer': 'https://sso.buaa.edu.cn/',
            'Priority': 'u=0, i',
            'Connection': 'keep-alive',
        }

        response = requests.get('https://byxt.buaa.edu.cn/jwapp/sys/homeapp/index.do', cookies=cookies, headers=headers, verify=False, allow_redirects=False)
        _WEU = response.headers.get("Set-Cookie").strip().split(",")[-1].split(";")[0].split("=")[-1]
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
        'Cache-Control': 'max-age=0',
        'Sec-Ch-Ua': '"Chromium";v="127", "Not)A;Brand";v="99"',
        'Accept-Language': 'zh-CN',
        'Sec-Ch-Ua-Mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.100 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'Accept': 'application/json',
        'Fetch-Api': 'true',
        'Sec-Ch-Ua-Platform': '"macOS"',
        'Origin': 'https://byxt.buaa.edu.cn',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://byxt.buaa.edu.cn/jwapp/sys/homeapp/home/index.html?av=1725888244394&contextPath=/jwapp',
        'Priority': 'u=1, i',
        'Connection': 'keep-alive',
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
    
    schedule_json = response.json()
    schedule_list = schedule_json["datas"]["arrangedList"]
    return schedule_list

import csv
import re
def convert_schedule_to_csv(schedule_list):
    
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
                if "单" in week:
                    week = week[:-4]
                    week += "单"
                elif "双" in week:
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
    with open("schedule.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["课程名称", "星期", "开始节数", "结束节数", "老师", "地点", "周数"])
        writer.writerows(list_for_csv)
    import sys
    writer = csv.writer(sys.stdout,delimiter="\t")
    writer.writerow(["课程名称", "星期", "开始节数", "结束节数", "老师", "地点", "周数"])
    writer.writerows(list_for_csv)

if __name__ == "__main__":
    id = input("请输入统一认证学号：").strip()
    passwd = getpass_echo("请输入统一认证密码：")
    try:
        gs_session, _WEU = login(id, passwd)
    except:
        print("登录失败... 学号/密码错误？")
        import time; time.sleep(0.5)
        raise
        
    print("账号{}登陆成功！".format(id))
    year = input("请输入学年，如“2024-2025-1”代表2024-2025学年第一学期：").strip()
    schedule_list = get_schedule(gs_session, _WEU, year)
    if len(schedule_list) == 0:
        print("没有课程？学年输入错误？")
    else: 
        convert_schedule_to_csv(schedule_list)
        print("课程表已保存为schedule.csv文件！请发送到手机后倒入wakeup课程表！")
   
