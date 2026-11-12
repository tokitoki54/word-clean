# Windows EXE 第三方组件

本项目源码仅使用Python标准库。EXE另外包含运行时，按各自许可分发；应用Apache-2.0不覆盖或替换组件许可。

- CPython 3.12.10：https://www.python.org/downloads/release/python-31210/ ，许可见Python-LICENSE.txt。
- Tcl/Tk 8.6：许可见TclTk-*-license.terms。
- PyInstaller 6.22.3：https://pyinstaller.org/en/stable/license.html ，许可见PyInstaller-COPYING.txt及其bootloader例外。
- OpenSSL 3.0.16：https://github.com/openssl/openssl/tree/openssl-3.0.16 ，Apache-2.0，见OpenSSL-3.0.16-LICENSE.txt。该版本官方树未提供单独NOTICE。
- zlib 1.3.1：https://github.com/madler/zlib/tree/v1.3.1 ，见zlib-1.3.1-LICENSE.txt。
- Expat 2.7.1：https://github.com/libexpat/libexpat/tree/R_2_7_1 ，见Expat-2.7.1-COPYING.txt。
- XZ/liblzma 5.2.5：https://github.com/python/cpython-source-deps/tree/xz-5.2.5 ，见XZ-5.2.5-COPYING.txt。liblzma公有领域条款不要求应用使用GPL。
- Microsoft VC运行库：来自Python安装目录的原始文件，分发附加条款见Python-LICENSE.txt。本包不附带ucrtbase.dll，依赖Windows 10/11系统UCRT。

支持范围：Windows 10/11 x64；其他系统未验证。公开EXE不包含用户文稿、输出、历史记录或内部审查资料。
