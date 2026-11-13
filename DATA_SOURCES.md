# 默认字表的范围与来源

当前默认字表 `默认字表_新旧字形_v6.csv` 包含160条不同Unicode码位映射，SHA256及历史版本信息见 `mapping_manifest.json`。历史122条 v5 文件原样保留，不作为当前默认表。它是本工具选择的处理规则，不是国家标准逐字全文，也不是完整的新旧字形表。同码位字体差异、简繁转换和兼容字统一化不属于本工具范围。

## 可追溯来源

历史122条中有121条同向字对与 TerryTian-tech 的 Apache-2.0 字表相符：

- 仓库：https://github.com/TerryTian-tech/OpenCC-Traditional-Chinese-characters-according-to-Chinese-government-standards
- 固定提交：19de6a2a122de8b93c1ee20f915eeb00013f56a6
- 文件：t2gov/GovVariants_keep_simp.txt
- 上游原文件SHA256：693ef8d6c0ca169823293c37598dcee59a9d742897c271f1ffc323c2a6eb9344
- https://github.com/TerryTian-tech/OpenCC-Traditional-Chinese-characters-according-to-Chinese-government-standards/blob/19de6a2a122de8b93c1ee20f915eeb00013f56a6/t2gov/GovVariants_keep_simp.txt

本项目只选择所需字对并改为可编辑CSV，未引入OpenCC引擎或整张上游字表。上游署名与修改说明见NOTICE，许可证全文见LICENSE。

另一个字对刄→刃为独立核验的字符对应事实，参考书同文新旧字形页面：https://hanzi.unihan.com.cn/NewVsOld 。本项目不转载该网站的图片、说明文字或整表编排，也不声称Apache许可覆盖第三方网站内容。

核对时另参考：https://www.hanyudacidian.cn/about/zixing 。网站链接用于说明核对背景，不代表其内容的再分发许可或对本项目的认可。

## 本次扩充（v6）

在历史122条全部保留的基础上增加38条：3条整字资料候选，以及35条由项目维护者逐项选择的编辑规则（含舎→舍）。这不是35条均获国家标准审定的声明；不按部件相似性自动扩表，也不对其他地区、姓名、古籍引文一概适用。

3条整字资料候选的核对来源：

- 敎→教：郭圣林《韩中汉字字形区别略论》，第3页2.2.1；核过原PDF。https://journal.kci.go.kr/ksclc/archive/articlePdf?artiId=ART001356991
- 吿→告：李义琳、林仲湘论文转载正文，未核原刊图。https://www.qqxiuzi.cn/wz/zixun/1603.htm ；字样辅助参考：https://dict.variants.moe.edu.tw/dictView.jsp?ID=5669
- 漑→溉：汉典“漑”条的旧字形释义。https://zdic.net/hant/漑 ；字样辅助参考：https://dict.variants.moe.edu.tw/dictView.jsp?ID=24463 和 https://dict.variants.moe.edu.tw/dictView.jsp?ID=24462

上述来源用于核对字符事实，不表示同一地区规范、第三方背书或内容再分发许可。本仓库不复制论文图片、词条全文或私人审阅资料。

扩充后与上游提交 `7e36fb6789246521d2e824f6a083b0403fb454e4` 的 `t2gov/GovVariants_keep_simp.txt` 比较：155条同向相同，无同源字冲突；本项目另有刄→刃、嚔→嚏、悳→惪、敎→教、槇→槙这5条。相同不等于每一条都由该上游独立审定。本项目没有启用其整表或转换引擎。

固定比较文件：https://github.com/TerryTian-tech/OpenCC-Traditional-Chinese-characters-according-to-Chinese-government-standards/blob/7e36fb6789246521d2e824f6a083b0403fb454e4/t2gov/GovVariants_keep_simp.txt

本轮明确保持原字的18项为：晉、戩、為、偽、媯、溈、蒍、羨、盜、茲、孶、縁、敻、粵、晩、鄕、袞、殼。默认表不含这些源字的替换规则；嚔→嚏则是本轮选入的规则，不再沿用旧版保留嚔的选择。

## 使用边界

使用前请核对所选字表。编辑后的副本由使用者决定规则。本程序不会自行添加规则，也不将全部异体字视为可互换字。默认表的SHA256用于识别原始版本，编辑副本会标记为待核对。
