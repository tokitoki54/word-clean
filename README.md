# Word Clean · 新旧字形

一个离线运行的Windows桌面工具：按可编辑字表替换DOCX/TXT中的指定字形，保留原文件，另存处理结果。

## 功能

- 默认122条不同码位的新旧字形映射，不进行通用简繁转换。
- 字表支持CSV/XLSX，可按旧字或新字搜索，编辑后另存副本。筛选不会丢失未显示规则。
- 先预览替换数量及字对统计，再转换另存。预览不是正文对照。
- 每批次输出转换后的文稿，以及一份汇总`字形统计.csv`（旧字型、新字形、次数）。CSV含UTF-8 BOM，可用Excel打开。
- 成功另存后自动移出待处理列表；失败、取消和预览不移除。完成结果留在窗口下方。
- 本地历史只保存成功文件的文件名、时间、替换字对和次数，不保存正文或完整路径。

## 运行

Windows EXE版：将完整程序文件夹解压至可写目录，双击`WordClean.exe`。必须保留旁边的`_internal`和默认CSV，不要只复制EXE。不需要安装Python。若Release尚无附件，可使用源码运行。

源码：安装带Tkinter的Python 3.12或兼容版本后，在项目目录运行：

```console
python word_clean_gui.pyw
```

添加DOCX/TXT → 点击底部“1 预览替换” → 核对结果 → 点击“2 转换并另存”。每次转换新建独立批次目录，不覆盖原文或旧结果。点击“打开输出文件夹”查看文稿和统计。

## 格式与限制

DOCX处理正文、表格、页眉页脚、脚注尾注、文本框内普通Word文本节点，支持常见和Strict OOXML。批注、域指令、修订删除文字、图片、嵌入对象和SmartArt不处理。复杂或不支持的XML结构会拒绝处理。复杂文稿应在Word中复核排版。

TXT支持UTF-8、UTF-8 BOM和带BOM的UTF-16并保留换行与字节序；GB18030须明确选择。不支持DOC、PDF或加密文稿。XLSX字表读取第一张工作表。字表仅支持单字对单字，单次替换、不级联；冲突映射会报错。

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
