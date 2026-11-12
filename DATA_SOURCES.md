# 默认字表的范围与来源

默认字表包含122条旧字→新字的不同Unicode码位映射。它是本工具选择的处理规则，不是国家标准逐字全文，也不是完整的新旧字形表。同码位字体差异、简繁转换和兼容字统一化不属于本工具范围。

## 可追溯来源

121条同向字对与 TerryTian-tech 的 Apache-2.0 字表相符：

- 仓库：https://github.com/TerryTian-tech/OpenCC-Traditional-Chinese-characters-according-to-Chinese-government-standards
- 固定提交：19de6a2a122de8b93c1ee20f915eeb00013f56a6
- 文件：t2gov/GovVariants_keep_simp.txt
- 上游原文件SHA256：693ef8d6c0ca169823293c37598dcee59a9d742897c271f1ffc323c2a6eb9344
- https://github.com/TerryTian-tech/OpenCC-Traditional-Chinese-characters-according-to-Chinese-government-standards/blob/19de6a2a122de8b93c1ee20f915eeb00013f56a6/t2gov/GovVariants_keep_simp.txt

本项目只选择所需字对并改为可编辑CSV，未引入OpenCC引擎或整张上游字表。上游署名与修改说明见NOTICE，许可证全文见LICENSE。

另一个字对刄→刃为独立核验的字符对应事实，参考书同文新旧字形页面：https://hanzi.unihan.com.cn/NewVsOld 。本项目不转载该网站的图片、说明文字或整表编排，也不声称Apache许可覆盖第三方网站内容。

核对时另参考：https://www.hanyudacidian.cn/about/zixing 。网站链接用于说明核对背景，不代表其内容的再分发许可或对本项目的认可。

## 使用边界

使用前请核对所选字表。编辑后的副本由使用者决定规则。本程序不会自行添加规则，也不将全部异体字视为可互换字。默认表的SHA256用于识别原始版本，编辑副本会标记为待核对。
