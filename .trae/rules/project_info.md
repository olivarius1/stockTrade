---
trigger: always_on
---
前后端分离系统

系统代码包含: 
    前端:frontend/
    后端:backend/
## 系统功能
- 用于股票估值, 可以部署查看估值/回测报告
- 提供了一个skill `.qoder\skills\stock-valuation-skill`, 该skill可以复用系统代码生成本地估值报告

修改stock-valuation-skill时,禁止做破坏/修改原前后端系统代码的行为,但是可以:
- 调整skill的提示词描述
- 可以修改skill的脚本`.qoder\skills\stock-valuation-skill\scripts`来扩展和修改功能

务必注意:
处理报告/db文件时,文件可能很大,不要盲目读取,避免过多消耗token

环境:
项目在windows 环境下开发,本地部署. 
机器上有wsl, 可以执行`wsl` 进入 ubuntu24.04 环境
