# Word Clean · 新旧字形

一个离线运行的Windows桌面工具：按可编辑字表替换DOCX/TXT中的指定字形，保留原文件，另存处理结果。

## 下载试用版

[下载 Windows x64 试用版 v0.2.0（160条）](https://github.com/tokitoki54/word-clean/releases/tag/v0.2.0)。下载页面中的 `WordClean-v0.2.0-windows-x64.zip`，完整解压后运行 `WordClean/WordClean.exe`，保留 `_internal` 和默认CSV。这是未签名的预发布版本，建议先用文稿副本验证效果。

新版已重新构建，默认160条，包含舎→舍；[旧版 v0.1.0（122条）](https://github.com/tokitoki54/word-clean/releases/tag/v0.1.0) 保留。构建基线为 `39896b4`，包内 `build_source` 附窗口标题及160条自测补丁、精确构建源码与重建说明。验证范围和限制详见Release页面及包内TEST_REPORT.txt。

## 功能

- 默认160条不同码位的新旧字形映射，不进行通用简繁转换。
- 字表支持CSV/XLSX，可按旧字或新字搜索，编辑后另存副本。筛选不会丢失未显示规则。
- 先预览替换数量及字对统计，再转换另存。预览不是正文对照。
- 每批次输出转换后的文稿，以及一份汇总`字形统计.csv`（旧字型、新字形、次数）。CSV含UTF-8 BOM，可用Excel打开。
- 成功另存后自动移出待处理列表；失败、取消和预览不移除。完成结果留在窗口下方。
- 本地历史只保存成功文件的文件名、时间、替换字对和次数，不保存正文或完整路径。

## 运行

Windows EXE版：将完整程序文件夹解压至可写目录，双击`WordClean.exe`。必须保留旁边的`_internal`和默认CSV，不要只复制EXE。不需要安装Python。也可按下方说明使用源码运行。

源码：安装带Tkinter的Python 3.12或兼容版本后，在项目目录运行：

```console
python word_clean_gui.pyw
```

添加DOCX/TXT → 点击底部“1 预览替换” → 核对结果 → 点击“2 转换并另存”。每次转换新建独立批次目录，不覆盖原文或旧结果。点击“打开输出文件夹”查看文稿和统计。

## 格式与限制

DOCX处理正文、表格、页眉页脚、脚注尾注、文本框内普通Word文本节点，支持常见和Strict OOXML。批注、域指令、修订删除文字、图片、嵌入对象和SmartArt不处理。复杂或不支持的XML结构会拒绝处理。复杂文稿应在Word中复核排版。

TXT支持UTF-8、UTF-8 BOM和带BOM的UTF-16并保留换行与字节序；GB18030须明确选择。不支持DOC、PDF或加密文稿。XLSX字表读取第一张工作表。字表仅支持单字对单字，单次替换、不级联；冲突映射会报错。

同一个 Unicode 码位在不同字体、地区字形规范中可能显示为不同写法。由于底层字符相同，普通字符替换无法区分并转换这些视觉差异；需要选用合适的字体或地区字形，并在排版软件中核对。默认160条是项目逐项审阅后选择的替换规则，不代表所有字对均有国家标准规定，也不是完整的新旧字形表。

## 隐私与保存

转换不联网。文稿、输出、编辑字表和`history.jsonl`均保留在本地。历史文件名可能包含个人信息，请勿把自己的完整工作目录直接上传GitHub。默认字表与历史在程序目录；请放在自己有写权限的位置。

## 验证

```console
python run_tests.py
```

测试使用合成文稿；历史私有字表未公开，对应测试会跳过。Windows隐藏窗口自动回归和独立EXE的DOCX/TXT合成转换已通过。尚未覆盖所有Windows版本、DPI设置或复杂文稿。本项目尚未提供代码签名；Windows可能提示未知发布者。

## 构建

```console
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-build.txt
.venv\Scripts\python -m PyInstaller --onedir --windowed --name WordClean word_clean_gui.pyw
```

将默认CSV复制到`dist/WordClean/`的EXE旁。分发前必须携带本项目LICENSE、NOTICE、DATA_SOURCES.md及Python、Tk、PyInstaller和所包含二进制组件的适用许可/通知。不要把用户历史、文稿、输出和内部审查资料加入发布包。

## 许可证与来源

项目采用Apache-2.0，见LICENSE。默认字表来源与改动说明见[DATA_SOURCES.md](DATA_SOURCES.md)和NOTICE。第三方运行时按各自许可分发；网站资料不因引用而改为本项目许可。
