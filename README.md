# VoterEligibilityMaintenance
用于维护中文维基百科合资格选民清单的机器人，同时提供资格验证API。

本仓库中：
* `api.py`：提供了资格验证API功能
* `database.py`：提供了数据库相关功能
* `lists_maintenance.py`：提供了站内页面维护功能
* `maintenance_cli.py`：计划编写的cli程序，供机器人维护者使用
* `telegram_bot.py`：正在编写的telegram机器人，提供变动通知、创建新列表等功能，供选举助理使用
* `user-config.py`：用于pywikibot
* `LICENSE`
* `Procfile`：用于API相关功能
* `README.md`：本文档
* `requirements.txt`

计划：
* `main.py`： 提供方便的运行方式，拟于`telegram_bot.py`完成后编写。

## 使用指南
本项目为toolforge环境开发，多数主要功能依赖toolforge环境，不能直接在本地运行。如你有类似需求，请完整阅读本仓库代码，并作适当修改。

## 贡献指南
感谢你愿意为本项目作出贡献。不过相关指南并不完善，甚至应该说没有，因而还请你阅读本仓库代码，如有不解之处，可以通过下文问题回报处说明的方式联系我。

本项目`database.py`主要依赖两个wikimedia cloud服务：
* `ToolsDB`[链接](https://wikitech.wikimedia.org/wiki/Help:Toolforge/ToolsDB)：提供了机器人存储本地列表数据的空间
* `Wiki Replicas`[链接](https://wikitech.wikimedia.org/wiki/Wiki_Replicas)：机器人定期获取合资格用户清单用

## 问题回报
请使用issues功能报告问题。安全问题、亟需解答的问题，可以电邮至 `me@soyorin.moe`，或通过Telegram与我取得联系，用户名为 `@eveningtaco`。

倘若你使用Telegram与我联系，且我逾三日未能回复，或我先前屏蔽了你，则请你站内告知我主动联系你，或委托其他选举助理与我联系。谢谢。