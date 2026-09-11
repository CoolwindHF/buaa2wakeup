# README

> [!NOTE]
>
> 更新于2026.9.11，在2026-2027秋季学期完成测试

通过生成csv解决wakeup无法直接解析buaa本科生新教务学期课程表的问题，并且可以生成ics文件导入任何支持通过该格式创建日程表的日历软件
p.s. 现在可以直接解析了，但我还是更喜欢日历

现在也支持**研究生课表**（研究生教育综合管理信息系统 GSMIS），在`config.yaml`中设置`type: graduate`即可，本科生设置`type: undergraduate`（或不设置）

## Usage

根据`config_example.yaml`创建自己的`config.yaml`后运行

```
pip install -r requirements.txt
python3 main.py
```

csv文件可以用于导入wakeup，ics文件可以导入日历

## 导入日历

支持生成ics文件，让你彻底不用给~~wakeup掏钱~~

生成ics文件导入日历（苹果日历、谷歌日历）的方法可以参考[该链接](https://jackyu.cn/tech/apple-ics-import/)，包括但不限于邮件、airdrop