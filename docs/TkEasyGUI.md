(Files content cropped to 300k characters, download full ingest to see more)
================================================
FILE: README.md
================================================
# TkEasyGUI - the easiest library for GUI

[![PyPI Downloads](https://static.pepy.tech/badge/TkEasyGUI)](https://pepy.tech/projects/TkEasyGUI)
[![PyPI Version](https://img.shields.io/pypi/v/TkEasyGUI)](https://pypi.org/project/TkEasyGUI/)
[![GitHub License](https://img.shields.io/github/license/kujirahand/TkEasyGUI-python)](https://github.com/kujirahand/kudb-python/blob/main/LICENSE)

`TkEasyGUI` is the easiest library for creating GUIs in Python.

This library allows you to easily create GUI applications with Python.
Since it is based on Tkinter, it runs consistently on Windows, macOS, and Linux.
With a variety of built-in dialogs and customizable forms, you can develop applications effortlessly.

<img src="https://github.com/kujirahand/TkEasyGUI-python/raw/main/docs/image/TkEasyGUI-shot1000.jpg" width="500" alt="TkEasyGUI Screenshot">

- [👉日本語](https://github.com/kujirahand/TkEasyGUI-python/blob/main/README-ja.md) / [👉中文](https://github.com/kujirahand/TkEasyGUI-python/blob/main/README-zh.md) / [👉한국어](https://github.com/kujirahand/TkEasyGUI-python/blob/main/README-ko.md)

## Platform

- Windows / macOS / Linux (Tkinter required)


## Install

Install package from [PyPI](https://pypi.org/project/TkEasyGUI/).

```sh
pip install TkEasyGUI
# or
python -m pip install TkEasyGUI
```

Install package from [GitHub Repository](https://github.com/kujirahand/TkEasyGUI-python).

```sh
python -m pip install git+https://github.com/kujirahand/TkEasyGUI-python
```

## Features of This Library

- Python's standard UI library `Tkinter`, is often considered to have a high barrier to entry and to be difficult to use. By using this library, you can create GUI applications easily and intuitively.
- This package supports type hints, allowing property selection via code completion. `Python 3.9 or later` is required.
- In the event model, it is compatible with the well-known GUI library `PySimpleGUI`.
- This project adopts the lenient MIT license. This license will not change in the future. Let's enjoy creating GUI programs.

## How to use - popup dialogs

Using TkEasyGUI is simple. If you only want to display a dialog, it requires just two lines of code.

```py
import TkEasyGUI as eg
# Show Text dialog
eg.print("A joyful heart is good medicine.")
```

<img src="https://github.com/kujirahand/TkEasyGUI-python/raw/main/docs/image/sample1.png" width="300" alt="TkEasyGUI">


Ask the user for their name and display that name in the window.

```py
import TkEasyGUI as eg
# Show Input dialog
name = eg.input("What is your name?")
eg.print(f"Hello, {name}.")
```

<img src="https://github.com/kujirahand/TkEasyGUI-python/raw/main/docs/image/sample2.png" width="300" alt="TkEasyGUI">

Furthermore, a dialog is available that allows specifying multiple input fields.

```py
import TkEasyGUI as eg
# Show Form dialog
form = eg.popup_get_form(["Name", "Age", "Hobbies"])
if form:
    name = form["Name"]
    age = form["Age"]
    hobbies = form["Hobbies"]
    eg.print(f"name={name}, age={age}, hobby={hobbies}")
```

<img src="https://github.com/kujirahand/TkEasyGUI-python/raw/main/docs/image/sample3.png" width="300" alt="TkEasyGUI">

### More Dialogs

`TkEasyGUI` provides a variety of dialogs. For example, a color selection dialog, a file selection dialog, and a calendar dialog.

- [Docs > Dialogs](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/dialogs-py.md)

## How to use - widgets

To create a simple window with only labels and buttons, you would write as follows:

```py
import TkEasyGUI as eg
# define layout
layout = [
    [eg.Text("Hello, World!")],
    [eg.Button("OK")]
]
# create a window
with eg.Window("Hello App", layout) as window:
    # event loop
    for event, values in window.event_iter():
        if event == "OK":
            eg.print("Thank you.")
            break
```


You can describe it using an event model similar to the famous GUI library, PySimpleGUI.

```py
import TkEasyGUI as eg

# define layout
layout = [
    [eg.Text("Hello, World!")],
    [eg.Button("OK")]
]
# create a window
window = eg.Window("Hello App", layout)
# event loop
while True:
    event, values = window.read()
    if event in ["OK", eg.WINDOW_CLOSED]:
        eg.popup("Thank you.")
        break
# close window
window.close()
```

- [Docs > What kind of elements can be used?](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/README.md#TkEasyGUI-elements-list)

## Samples

We have prepared a selection of samples to demonstrate simple usage. Please check them out.

- [samples](https://github.com/kujirahand/TkEasyGUI-python/tree/main/tests).

Running `tests/file_viewer.py` allows all samples to be easily launched.

## Documents

Below is a detailed list of classes and methods.

- [docs](https://github.com/kujirahand/TkEasyGUI-python/tree/main/docs)
  - [Dialogs](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/dialogs-py.md)
  - [Elements](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md)
  - [Utilities](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/utils-py.md)

## Tutorial

Japanese tutorials:

- [TkEasyGUI - Pythonで最も素早くデスクトップアプリを創るライブラリ](https://note.com/kujirahand/n/n33a2df3aa3e5)
- [マイナビニュースPython連載116回目 - 合計/整形/コピーのツールを作ろう](https://news.mynavi.jp/techplus/article/zeropython-116/)
- [(Book) Pythonでつくるデスクトップアプリ メモ帳からスクレイピング・生成AI利用まで](https://amzn.to/45R2NSH)
- [(Magazine) 日経ソフトウエア2025年5月号の特集記事 - TkEasyGUIを使ってみよう](https://amzn.to/4j1lj0c)

There are other helpful articles as well.

- [TkEasyGUI - 目的別ダイアログ完全ガイド](https://note.com/sirodon_256/n/n4138ebf4877f)
- [TkEasyGUIライブラリの基本とサンプルコード解説](https://note.com/sirodon_256/n/na73d3fdac68d)

## Compatibility with PySimpleGUI

- When using basic functionalities, it is compatible with PySimpleGUI. Programs can be written using the same event-driven model as PySimpleGUI.
- The names of basic GUI components are kept the same, but some property names differ.
- TkEasyGUI has been completely reimplemented from scratch and is licensed under the MIT License.
- However, full compatibility with PySimpleGUI is not intended.

## TkEasyGUI features:

- Using a `for` loop and `window.event_iter()` enables straightforward event processing.
- Custom popup dialogs, such as a color selection dialog(`eg.popup_color`), a list dialog(`eg.popup_listbox`), form dialog(`eg.popup_get_form`) are available.
- The `Image` class supports not only PNG but also JPEG formats.
- Convenient event hooks and features for bulk event registration are provided - [docs/custom_events](docs/custom_events.md).
- Methods such as Copy, Paste, and Cut are added to text boxes (Multiline/Input).
- The system's default color scheme is utilized.

<img src="https://github.com/kujirahand/TkEasyGUI-python/raw/main/docs/image/icon256.png" width="256" alt="TkEasyGUI Logo">

## Link

- [pypi.org > TkEasyGUI](https://pypi.org/project/TkEasyGUI/)
- [GitHub > TkEasyGUI](https://github.com/kujirahand/TkEasyGUI-python/)
- [Discord > TkEasyGUI](https://discord.gg/NX8WEQd42S)



================================================
FILE: check.sh
================================================
#!/bin/sh

# pip install ruff
ruff check TkEasyGUI/*.py
mypy TkEasyGUI/*.py



================================================
FILE: element2json.py
================================================
#!/usr/bin/env python
"""
make elements.json and elements_test.py
"""
import json
import os

SCRIPT_DIR = os.path.dirname(__file__)

TEST_FILENAME = os.path.join(SCRIPT_DIR, "elements_test.py")
FILE_ELEMENTS = os.path.join(SCRIPT_DIR, "docs", "scripts", "elements.json")

COLS_PER_ROW = 4

def read_file() -> str:
    # read elements.json
    with open(FILE_ELEMENTS, "r", encoding="utf-8") as fp:
        elements = json.load(fp)
    args = {}
    for e in elements:
        args[e] = []
        if e in ["Button", "Text", "Input", "Frame", "Checkbox", "Label", "InputText", "Multiline"]:
            args[e].append(f"'{e}'")
        if e in ["Column", "Frame"]:
            args[e].append("layout=[[eg.Button('OK')]]")
        if e in ["Menu"]:
            args[e].append("menu_definition=[['File', ['Open', 'Save', 'Exit']], ['Edit', ['Copy', 'Paste']]]")
        if e in ["Table"]:
            args[e].append("values=[[1,2,3],[4,5,6],[7,8,9]]")
            args[e].append("headings=['aaa', 'bbb', 'ccc']")
        if e in ["Image"]:
            args[e].append("filename='a.png'")
            args[e].append("size=(100,100)")
        if e in ["Canvas"]:
            args[e].append("size=(100,100)")
        if e in ["Graph"]:
            args[e].append("size=(100,100)")
        if e in ["Combo"]:
            args[e].append("values=['combo1', 'combo2', 'combo3']")
            args[e].append("default_value='combo1'")
        if e in ["Listbox", "ListBrowse"]:
            args[e].append("values=['item1', 'item2', 'item3']")
        if e in ["Tab"]:
            args[e].append("title='tab'")
            args[e].append("layout=[[eg.Button('OK')]]")
        if e in ["TabGroup"]:
            args[e].append("layout=[[ eg.Tab('tab1', layout=[[eg.Button('OK')]]) ]]")
    return elements, args

def make_code():
    elements, init_args = read_file()
    src = """
### auto generated by element2json.py ###
# Test all elements of TkEasyGUI
import TkEasyGUI as eg
layout = [
"""
    src += "    [\n"
    for i, e in enumerate(elements):
        args = init_args.get(e, {})
        args_s = ",".join(args)
        if ("Browse" in e) or ("FileSaveAs" == e):
            src += f"        eg.Frame('{e}', layout=[[eg.Input(''), eg.{e}({args_s})]]),\n"
        else:
            src += f"        eg.Frame('{e}', layout=[[eg.{e}({args_s})]]),\n"
        if i % COLS_PER_ROW == (COLS_PER_ROW-1):
            src += "    ],\n"
            src += "    [\n"
    src += "    ],\n"
    src += "]\n"
    src += """
window = eg.Window(f"all element v.{eg.__version__}", layout=layout, size=(800, 600), font=("Arial", 12), resizable=True, show_scrollbar=True)
for event, values in window.event_iter():
    if event == "OK":
        break
"""
    print(f"==={TEST_FILENAME}===")
    print(src)
    with open("elements_test.py", "w", encoding="utf-8") as f:
        f.write(src)
    # os.system("python elements_test.py")
if __name__ == "__main__":
    make_code()



================================================
FILE: LICENSE
================================================
MIT License

Copyright (c) 2024 kujirahand

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.



================================================
FILE: makedoc.py
================================================
import glob
import inspect
import json
import os
import re
import types

import TkEasyGUI as eg

SCRIPT_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "docs", "TkEasyGUI")
DOCS_SCRIPTS_DIR = os.path.join(SCRIPT_DIR, "docs", "scripts")
REPO = "https://github.com/kujirahand/TkEasyGUI-python/blob/main"

def main():
    package_path = eg.__path__[0]
    print(package_path)
    # print(eg.__doc__)
    root_name = eg.__package__

    # get modules
    outputs = []
    files = glob.glob(os.path.join(package_path, "*.py"))
    for file in files:
        read_module(file, root_name)
        outputs.append(file)
    print("[output files]")
    for file in outputs:
        print("-", file)

def read_module(file: str, root_name: str) -> None:
    module_name = os.path.basename(file).replace(".py", "")
    if module_name == "__init__":
        return
    mod = getattr(eg, module_name)
    doc = trim_docstring(str(mod.__doc__))
    print("---------------------------")
    output_file = os.path.join(OUTPUT_DIR, f"{module_name}-py.md")
    result = ""
    head = f"# Module {root_name}.{module_name}\n\n"
    head += doc + "\n\n"
    head += "---------------------------\n\n"
    print(head)
    head_link = []
    # classes
    elements = []
    classes = ""
    for prop in dir(mod):
        if prop.startswith("__"):
            continue
        p = getattr(mod, prop)
        if type(p) is type:
            mod2 = inspect.getmodule(p)
            if mod2 != mod:
                continue
            pclass = p
            class_name = pclass.__name__
            doc = trim_docstring(p.__doc__)
            classes += f"## {prop}\n\n"
            classes += doc + "\n\n"
            elements.append(class_name)
            # get init code
            if p.__init__ is not None:
                print(f"- class {prop}")
                code_def = get_function_definition(p.__init__, skip_self=True)
                code_def = re.sub("^def __init__", f"class {class_name}", code_def)
                code_def = re.sub(r"->\s*None\s*:", "", code_def)
                if prop == "Button":
                    # for DEBUG - print only button
                    print("@@@ (debug)", code_def)
                    # print(inspect.getsource(p.__init__))
                if code_def != "":
                    classes += "```py\n"
                    classes += code_def
                    classes += "```\n\n"
                    code = p.__init__.__code__
                    fname = code.co_filename.replace(SCRIPT_DIR, "")
                    classes += f"- [source]({REPO}{fname}#L{code.co_firstlineno})\n"
                    classes += "\n"
            # get methods
            method_doc = ""
            method_link = []
            methods = inspect.getmembers(pclass)
            for name, method in methods:
                if name.startswith("_"):
                    continue
                print(f"  - (method) {module_name}.{class_name}.{name}")
                method_doc += f"### {class_name}.{name}\n\n"
                doc = trim_docstring(method.__doc__)
                if doc.strip() != "":
                    method_doc += doc.strip() + "\n\n"
                ff = getattr(p, name)
                if not isinstance(ff, types.FunctionType):
                    print("*** skip *** ", type(ff), class_name, name)
                    continue
                def_code = get_function_definition(method, skip_self=True)
                method_doc += "```py\n"
                method_doc += def_code
                method_doc += "```\n\n"
                method_doc += f"- [source]({REPO}{fname}#L{code.co_firstlineno})\n"
                method_doc += "\n"
                method_link.append(f"- [{name}](#{class_name.lower()}{name.lower()})")
            if method_doc != "":
                classes += f"### Methods of {class_name}\n\n"
                classes += "\n".join(method_link) + "\n\n"
                classes += method_doc
    if classes:
        result += f"# Classes of {root_name}.{module_name}\n\n"
        if module_name == "widgets":
            class_link = []
            for class_name in elements:
                class_link.append(f"- [{class_name}](#{class_name.lower()})")
            result += "\n".join(class_link) + "\n\n"
        result += classes
        head_link.append(f"- [Classes](#classes-of-{root_name.lower()}{module_name.lower()})")
    # elements
    if len(elements) > 0 and module_name == "widgets":
        print("* elements:\n", elements)
        if "Window" in elements:
            elements.remove("Window")
        if "Element" in elements:
            elements.remove("Element")
        if "TkEasyError" in elements:
            elements.remove("TkEasyError")
        file_elements = os.path.join(DOCS_SCRIPTS_DIR, "elements.json")
        with open(file_elements, "w", encoding="utf-8") as fp:
            elements = list(sorted(elements))
            json.dump(elements, fp, ensure_ascii=False, indent=2)

    # functions
    functions = ""
    function_link = []
    for prop in dir(mod):
        if prop.startswith("_"):
            continue
        p = getattr(mod, prop)
        if isinstance(p, types.FunctionType):
            print(f"- (func_type) {module_name}.{prop}")
            doc = trim_docstring(p.__doc__)
            code = p.__code__
            def_code = get_function_definition(p)

            fname = code.co_filename.replace(SCRIPT_DIR, "")
            functions += f"## {prop}\n\n"
            functions += doc + "\n\n"
            functions += "```py\n"
            functions += def_code
            functions += "```\n\n"
            functions += f"- [source]({REPO}{fname}#L{code.co_firstlineno})\n"
            functions += "\n"
            function_link.append(f"- [{prop}](#{prop.lower()})")
    if functions:
        result += f"# Functions of {root_name}.{module_name}\n\n"
        result += "\n".join(function_link) + "\n\n"
        result += functions
        head_link.append(f"- [Functions](#functions-of-{root_name.lower()}{module_name.lower()})")

    print("---------------------------")
    result = head + "\n".join(head_link) + "\n\n" + result
    # print(result)
    with open(output_file, "w", encoding="utf-8") as fp:
        fp.write(result)
    print("- output=", output_file)

def trim_docstring(doc):
    """docstringのインデントを整形する"""
    if not doc or doc == "":
        return ""
    lines = doc.expandtabs().splitlines()
    indent = 0
    stripped = ""
    for line in lines:
        if line.strip() == "":
            continue
        stripped = line.lstrip()
        if stripped:
            indent = line.find(stripped)
            break
    trimmed = [lines[0].strip()]
    for line in lines[1:]:
        trimmed.append(line[indent:].rstrip())
    res = "\n".join(trimmed).strip()
    return res

def get_function_definition(func, skip_self=False):
    """関数の定義部分を取得する"""
    # 関数のソースコードを取得
    src = str(inspect.getsource(func))
    src = src.strip()
    res = []
    flag = False
    lines = src.split("\n")
    for line in lines:
        if not flag:
            if line.startswith("@"):
                flag = True
            if line.startswith("def "):
                flag = True
        if not flag:
            continue
        line = line.rstrip()
        if line != "" and line[0] == " ":
            line = "    " + line.strip()
        res.append(line)
        if line.endswith(":"):
            break
    return "\n".join(res).strip() + "\n"

if __name__ == "__main__":
    main()



================================================
FILE: makedoc.sh
================================================
#!/bin/bash
SCRIPT_DIR=$(cd $(dirname $0); pwd)

echo "--- makedoc.py ---"
python makedoc.py

echo "--- make docs/README.md ---"
python $SCRIPT_DIR/docs/scripts/readme_maker.py

echo "ok"



================================================
FILE: mypy.ini
================================================
[mypy]

[mypy-setuptools.*]
ignore_missing_imports = True



================================================
FILE: package.sh
================================================
#!/bin/sh
set -e
echo "+--------------------------------"
echo "| package.sh"
echo "+--------------------------------"
echo "|"
echo "[Package]"
echo "https://packaging.python.org/en/latest/tutorials/packaging-projects/"

# make manual
echo "--- makedoc.sh ---"
./makedoc.sh

# clean
rm -f -r dist
rm -f -r TkEasyGUI.egg-info
python3 -m pip uninstall -y TkEasyGUI

# change version from pyproject.toml
python3 update_version.py
# build
echo "--- build ---"
python3 -m build

# test install
echo "--- upload test repo ---"
python3 -m twine upload --repository testpypi dist/* --verbose
echo "--- wait a moment ---"

echo "--- install test repo ---"
echo "[TRY]: python -m pip install -U --index-url https://test.pypi.org/simple/ --no-deps TkEasyGUI"
echo "** check version **"

echo "--- upload pypi ---"
echo "[TRY]: python -m twine upload dist/* --verbose"





================================================
FILE: pyproject.toml
================================================
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "TkEasyGUI"
version = "1.0.36"
dependencies = [
  "Pillow",
  "pyperclip",
]
requires-python = ">=3.9"
authors = [
  { name="kujirahand", email="web@kujirahand.com" },
]
maintainers = [
 { name="kujirahand", email="web@kujirahand.com" },
]
description = "TkEasyGUI is simple GUI Library for Python3 with Tkinter"
readme = "README.md"
license = "MIT"
license-files = ["LICENSE"]
keywords = ["GUI", "tkinter", "TkEasyGUI"]
classifiers = [
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3 :: Only",
    "Topic :: Software Development :: User Interfaces",
]

[project.urls]
Homepage = "https://github.com/kujirahand/TkEasyGUI-python"
Documentation = "https://github.com/kujirahand/TkEasyGUI-python/blob/main/README.md"
Repository = "https://github.com/kujirahand/TkEasyGUI-python/"
Issues = "https://github.com/kujirahand/TkEasyGUI-python/issues"
Changelog = "https://github.com/kujirahand/TkEasyGUI-python/releases"

[tool.ruff.lint]
select = ["E", "F", "D"]
ignore = ["E501", "D415", "D203", "D212", "D400", "D401"]



================================================
FILE: README-ja.md
================================================
# TkEasyGUI

`TkEasyGUI`は、**Pythonで最も簡単にGUIアプリが開発できるライブラリ**です。`Tkinter`のような従来のUIライブラリが持つ複雑さを解消し、シンプルな使い勝手を実現しました。手軽に使える豊富なダイアログを用意しています。本ライブラリは、簡単にGUIを構築できるライブラリ`PySimpleGUI`の概念を引き継ぎつつ、独自の機能を追加しています。

- [👉English](https://github.com/kujirahand/TkEasyGUI-python/blob/main/README.md)

## TkEasyGUIの特徴:

- `TkEasyGUI`は、GUIアプリケーションを簡単かつシンプルに作成することができるPythonライブラリです。
- Pythonの標準UIライブラリ`Tkinter`は、学習障壁が高いと考えられていますが、このライブラリを使用すると、GUIアプリケーションを直感的に作成できます。
- イベントモデルや基本部品では、よく知られたGUIライブラリ`PySimpleGUI`と互換性があります。
- 型ヒントに対応しているので、コード補完でプロパティを選択できます。(本パッケージの利用には、`Python 3.9以降`が必要です。)
- ライセンスには比較的緩い`MITライセンス`を採用しています。将来このライセンスを変えることはありません。

## 対象プラットフォーム

- Windows / macOS / Linux (Tkinterが動く環境)

## インストール:

[PyPI](https://pypi.org/project/TkEasyGUI/)からインストールできます。

```sh
python -m pip install TkEasyGUI
```

[GitHubリポジトリ](https://github.com/kujirahand/TkEasyGUI-python)からインストールできます。

```sh
python -m pip install git+https://github.com/kujirahand/TkEasyGUI-python
```

- (メモ) v0.2.24未満からのアップデートに失敗する場合は[こちら](docs/installation_trouble.md)を確認してください。

## 簡単な使い方 - ポップアップダイアログを使う

TkEasyGUIの使い方は簡単です。もし、ダイアログにメッセージを表示したい場合、次のように記述します。

```py
import TkEasyGUI as eg
eg.print("A joyful heart is good medicine.")
```

<img src="https://github.com/kujirahand/TkEasyGUI-python/raw/main/docs/image/sample1.png" width="300" alt="TkEasyGUI">


入力ボックス付きのダイアログで尋ねることもできます。次のコードは、名前を尋ねて、続くダイアログに名前を表示します。

```py
import TkEasyGUI as eg
name = eg.input("What is your name?")
eg.print(f"Hello, {name}.")
```

<img src="https://github.com/kujirahand/TkEasyGUI-python/raw/main/docs/image/sample2.png" width="300" alt="TkEasyGUI">

さらに、複数入力が可能なフォームダイアログも手軽に表示できます。

```py
import TkEasyGUI as eg
# フォームダイアログを表示
form = eg.popup_get_form(["名前", "年齢", "趣味"], title="プロフィールの入力")
if form:
    name = form["名前"]
    age = form["年齢"]
    hobbies = form["趣味"]
    eg.print(f"name={name}, age={age}, hobby={hobbies}")
```

<img src="https://github.com/kujirahand/TkEasyGUI-python/raw/main/docs/image/sample3.png" width="300" alt="TkEasyGUI">

### バラエティ豊かなダイアログを提供

`TkEasyGUI` はさまざまなダイアログを提供します。
たとえば、色選択ダイアログ、ファイル選択ダイアログ、カレンダーダイアログなどです。

- [Docs > Dialogs](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/dialogs-py.md)


## 簡単な使い方 - カスタムウィンドウを定義して使う

ラベルとボタンのみを持つシンプルなウィンドウを作成するには、以下のように記述します。`with`文を使うことで、イベントループを抜けると自動的にウィンドウが閉じるように指定できます。

```py
import TkEasyGUI as eg
# 画面レイアウトの定義
layout = [
    [eg.Text("Hello, World!")],
    [eg.Button("OK")]
]
# ウィンドウを表示する
with eg.Window("Hello App", layout) as window:
    # イベントループを処理する
    for event, values in window.event_iter():
        if event == "OK":
            eg.print("Thank you.")
            break # ループを抜ける
```

有名GUIライブラリの`PySimpleGUI`と同じイベントモデルの使い勝手で記述できます。（多くのGUI部品でPySimpleGUIと互換性を持たせています。）

```py
import TkEasyGUI as eg
# define layout
layout = [[eg.Text("Hello, World!")],
          [eg.Button("Exit")]]
# create a window
window = eg.Window("test", layout)
# event loop
while True:
    event, values = window.read()
    if event in ["Exit", eg.WINDOW_CLOSED]:
        eg.popup("Thank you.")
        break
# close window
window.close()
```

- [Docs > どんなElementが使えますか？](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/README.md#TkEasyGUI-elements-list)

## チュートリアル

- [TkEasyGUI - Pythonで最も素早くデスクトップアプリを創るライブラリ](https://note.com/kujirahand/n/n33a2df3aa3e5)
- [マイナビニュースPython連載116回目 - 合計/整形/コピーのツールを作ろう](https://news.mynavi.jp/techplus/article/zeropython-116/)
- [(書籍) Pythonでつくるデスクトップアプリ メモ帳からスクレイピング・生成AI利用まで](https://amzn.to/45R2NSH)
- [(特集記事) 日経ソフトウエア2025年5月号の特集記事 - TkEasyGUIを使ってみよう](https://amzn.to/4j1lj0c)

公式ではないですが、役立つ技術記事があります！

- [TkEasyGUI - 目的別ダイアログ完全ガイド](https://note.com/sirodon_256/n/n4138ebf4877f)
- [TkEasyGUIライブラリの基本とサンプルコード解説](https://note.com/sirodon_256/n/na73d3fdac68d)

## サンプル

簡単な使い方を示すサンプルを揃えました。確認してみてください。

- [samples](https://github.com/kujirahand/TkEasyGUI-python/tree/main/tests).

`tests/file_viewer.py`を実行することで、すべてのサンプルを手軽に起動できます。

## ドキュメント

ライブラリの詳細なクラスやメソッドの一覧です。

- [マニュアル](https://github.com/kujirahand/TkEasyGUI-python/tree/main/docs)
  - [ダイアログの一覧](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/dialogs-py.md)
  - [カスタム要素の一覧](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md)
  - [便利なユーティリティ関数群](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/utils-py.md)

## PySimpleGUIとの互換性について

- 基本機能を使う場合、PySimpleGUIと互換性があります。PySimpleGUIと同じイベントモデルでプログラムを記述できます。
- 基本的なGUI部品の名前も同じにしてありますが、いくつかのプロパティ名は異なります。
- TkEasyGUIは完全にゼロから実装しなおしており、MITライセンスを採用しています。
- ただし、PySimpleGUIと完全な互換性は考えていません。

### TkEasyGUI独自の機能

- for文と `window.event_iter()` を使って気軽にイベント処理が可能
- 任意のボタンを持つダイアログ(`eg.popup_buttons`)や色選択ダイアログ(`eg.popup_color`)、複数項目を入力するダイアログ(`eg.popup_get_form`)など、独自のポップアップダイアログを用意
- ImageはPNGだけでなくJPEGも読み込み可能
- 便利なイベントフックや一括イベント登録機能 - [docs/custom_events](docs/custom_events.md)
- テキストボックス(Muliline/Input)に便利なCopy/Paste/Cutなどのメソッドを追加

## リンク

- [pypi.org > TkEasyGUI](https://pypi.org/project/TkEasyGUI/)
- [GitHub > TkEasyGUI](https://github.com/kujirahand/TkEasyGUI-python/)
- [Discord > TkEasyGUI](https://discord.gg/NX8WEQd42S)




================================================
FILE: README-ko.md
================================================
# TkEasyGUI

`TkEasyGUI`는 Python에서 GUI를 가장 쉽게 작성할 수 있는 라이브러리입니다.

<img src="https://github.com/kujirahand/TkEasyGUI-python/raw/main/docs/image/logo-button.jpg" width="180" alt="TkEasyGUI 로고">

- Python 표준 UI 라이브러리인 `Tkinter`는 종종 접근 장벽이 높고 사용하기 어렵다고 여겨집니다. 이 라이브러리를 사용하면 GUI 애플리케이션을 쉽고 직관적으로 만들 수 있습니다.
- 이벤트 모델은 잘 알려진 GUI 라이브러리인 `PySimpleGUI`와 호환됩니다.
- 이 패키지는 타입 힌트를 지원하여 코드 완성을 통해 속성을 선택할 수 있습니다. `Python 3.9 이상`이 필요합니다.
- 이 프로젝트는 관대한 MIT 라이선스를 채택하고 있으며, 이 라이선스는 향후 변경되지 않을 것입니다. 함께 GUI 프로그램 제작을 즐겨보세요.

- [👉English](https://github.com/kujirahand/TkEasyGUI-python/blob/main/README.md)

> This document has been translated automatically. Please let us know if you find any unnatural expressions.

## 플랫폼

- Windows / macOS / Linux (Tkinter 필요)

<img src="https://github.com/kujirahand/TkEasyGUI-python/raw/main/docs/image/TkEasyGUI-shot640.jpg" width="300" alt="TkEasyGUI">

## 설치

[PyPI](https://pypi.org/project/TkEasyGUI/)에서 패키지 설치:

```sh
pip install TkEasyGUI
# 또는
python -m pip install TkEasyGUI
```

[GitHub Repository](https://github.com/kujirahand/TkEasyGUI-python)에서 패키지 설치:

```sh
python -m pip install git+https://github.com/kujirahand/TkEasyGUI-python
```

- (메모) 0.2.24 이전 버전에서 업데이트 시 실패할 수 있습니다. ([해결 방법 보기](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/installation_trouble.md))

## 사용 방법 - 팝업 대화상자

TkEasyGUI를 사용하는 것은 간단합니다. 대화상자만 표시하려면 두 줄의 코드만 필요합니다.

```py
import TkEasyGUI as eg
# 텍스트 대화상자 표시
eg.print("기쁨의 마음은 좋은 약이다.")
```

사용자에게 이름을 묻고 창에 이름을 표시합니다.

```py
import TkEasyGUI as eg
# 입력 대화상자 표시
name = eg.input("당신의 이름은 무엇인가요?")
eg.print(f"안녕하세요, {name}님.")
```

또한, 여러 입력 필드를 지정할 수 있는 대화상자도 사용할 수 있습니다.

```py
import TkEasyGUI as eg
# 폼 대화상자 표시
form = eg.popup_get_form(["이름", "나이", "취미"])
if form:
    name = form["이름"]
    age = form["나이"]
    hobbies = form["취미"]
    eg.print(f"이름={name}, 나이={age}, 취미={hobbies}")
```

- [문서 > 대화상자](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/dialogs-py.md)


### 사용 방법 - 위젯

레이블과 버튼만 있는 간단한 창을 생성하려면 다음과 같이 작성할 수 있습니다.

```py
import TkEasyGUI as eg
# 레이아웃 정의
layout = [
    [eg.Text("안녕하세요, 세상!")],
    [eg.Button("확인")]
]
# 창 생성
with eg.Window("Hello App", layout) as window:
    # 이벤트 루프
    for event, values in window.event_iter():
        if event == "확인":
            eg.print("감사합니다.")
            break
```

PySimpleGUI와 유사한 이벤트 모델을 사용하여 설명할 수 있습니다.

```py
import TkEasyGUI as eg

# 레이아웃 정의
layout = [[eg.Text("안녕하세요, 세상!")], [eg.Button("확인")]]
# 창 생성
window = eg.Window("Hello App", layout)
# 이벤트 루프
while True:
    event, values = window.read()
    if event in ["확인", eg.WINDOW_CLOSED]:
        eg.popup("감사합니다.")
        break
# 창 닫기
window.close()
```

- [문서 > 사용할 수 있는 요소는?](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/README.md#TkEasyGUI-elements-list)

## 샘플

간단한 사용 방법을 보여주는 여러 샘플을 준비했습니다. 확인해 보세요.

- [샘플](https://github.com/kujirahand/TkEasyGUI-python/tree/main/tests).

`tests/file_viewer.py`를 실행하면 모든 샘플을 쉽게 실행할 수 있습니다.

## 문서

다음은 클래스와 메서드의 상세 목록입니다.

- [문서](https://github.com/kujirahand/TkEasyGUI-python/tree/main/docs)
  - [대화상자](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/dialogs-py.md)
  - [요소](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md)
  - [유틸리티](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/utils-py.md)

## 튜토리얼

일본어 튜토리얼:

- [TkEasyGUI - Python으로 가장 빠르게 데스크톱 애플리케이션을 만드는 라이브러리](https://note.com/kujirahand/n/n33a2df3aa3e5)
- [마이나비 뉴스 Python 연재 116회 - 합계/서식/복사 도구 만들기](https://news.mynavi.jp/techplus/article/zeropython-116/)
- [(도서) Python으로 만드는 데스크톱 앱 메모장부터 스크레이핑 및 생성 AI 활용까지](https://amzn.to/45R2NSH)

## PySimpleGUI와의 호환성

- 기본 기능을 사용할 때 PySimpleGUI와 호환됩니다. PySimpleGUI와 동일한 이벤트 구동 모델을 사용하여 프로그램을 작성할 수 있습니다.
- 기본 GUI 구성 요소의 이름은 동일하게 유지되지만, 일부 속성 이름은 다릅니다.
- TkEasyGUI는 완전히 새로 구현되었으며 MIT 라이선스 하에 제공됩니다.
- 그러나 PySimpleGUI와의 완전한 호환성을 목표로 하지는 않습니다.

### TkEasyGUI의 주요 기능:

- `for` 루프와 `window.event_iter()`를 사용하여 간단한 이벤트 처리가 가능합니다.
- 색상 선택 대화상자(`eg.popup_color`), 폼 대화상자(`eg.popup_get_form`) 등 맞춤형 팝업 대화상자가 제공됩니다.
- `Image` 클래스는 PNG뿐만 아니라 JPEG 형식도 지원합니다.
- 대량 이벤트 등록을 위한 편리한 이벤트 훅 및 기능 제공 - [docs/custom_events](docs/custom_events.md).
- 텍스트 박스(Multiline/Input)에 복사, 붙여넣기, 잘라내기 기능이 추가되었습니다.
- 시스템의 기본 색상 스킴을 활용합니다.

## 링크

- [pypi.org > TkEasyGUI](https://pypi.org/project/TkEasyGUI/)
- [GitHub > TkEasyGUI](https://github.com/kujirahand/TkEasyGUI-python/)
- [Discord > TkEasyGUI](https://discord.gg/NX8WEQd42S)



================================================
FILE: README-zh.md
================================================
# TkEasyGUI

`TkEasyGUI` 是一个 Python 库，允许轻松简单地创建 GUI 应用程序。在事件模型中，它与著名的 GUI 库 `PySimpleGUI` 兼容。

Python 的标准 UI 库 `Tkinter`，通常被认为入门门槛高且难以使用。通过使用这个库，你可以轻松直观地创建 GUI 应用程序。

此项目采用宽松的 MIT 许可证。这个许可证将来不会更改。让我们享受创建 GUI 程序的乐趣。

- [👉English](https://github.com/kujirahand/TkEasyGUI-python/blob/main/README.md)

> This document has been translated automatically. Please let us know if you find any unnatural expressions.

## 平台

- Windows / macOS / Linux（需要 tkinter）

## 安装

从 pypi 安装


```sh
python -m pip install TkEasyGUI
```

从 GitHub 仓库安装


```sh
python -m pip install git+https://github.com/kujirahand/TkEasyGUI-python
```

- （备忘）从旧版本更新（小于 0.2.24）将失败。([查看解决方案](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/installation_trouble.md))

## 如何使用

要创建一个只有标签和按钮的简单窗口，你可以这样写：

```py
import TkEasyGUI as eg

# 创建窗口
layout = [
    [eg.Text("Hello, World!")],
    [eg.Button("OK")]
]
window = eg.Window("Hello", layout=layout)

# 事件循环
while window.is_alive():
    # 获取事件
    event, values = window.read()
    # 检查事件
    if event == "OK":
        eg.popup("按下了 OK 按钮")
        break
window.close()
```

## 示例

我们准备了一系列示例以展示简单的使用方式。请查看。

- [示例](https://github.com/kujirahand/TkEasyGUI-python/tree/main/tests).

## 文档

下面是类和方法的详细列表。

- [文档](https://github.com/kujirahand/TkEasyGUI-python/tree/main/docs)

## 关于与 PySimpleGUI 的关系

- 在使用基本功能时，它与 PySimpleGUI 兼容。你可以使用与 PySimpleGUI 相同的事件模型编写程序。
- 基本 GUI 组件的名称也保持一致。然而，虽然一些属性名称不同，但实现了许多独特的功能。
- 本项目是以 PySimpleGUI 为思路开发的，但完全从头开始实现。不存在许可问题。
- 我们不考虑与 PySimpleGUI 完全兼容。

## 链接

- [pypi.org > TkEasyGUI](https://pypi.org/project/TkEasyGUI/)
- [GitHub > TkEasyGUI](https://github.com/kujirahand/TkEasyGUI-python/)
- [Discord > TkEasyGUI](https://discord.gg/NX8WEQd42S)



================================================
FILE: requirements.txt
================================================
Pillow
pyperclip
ruff
mypy
toml



================================================
FILE: Taskfile.yml
================================================
version: '3'

tasks:
  run:
    cmds:
      - python tests/file_viewer.py
  install-dev:
    cmds:
      - pip install -r requirements.txt
  install-test:
    cmds:
      - echo "--- install from test repo ---"
      - python -m pip install -U --index-url https://test.pypi.org/simple/ --no-deps TkEasyGUI
      - echo "*** check yoru version ***"
  install-main:
    cmds:
      - echo "--- install from main repo ---"
      - python -m pip install -U TkEasyGUI
  check:
    cmds:
      - ruff check
      - mypy TkEasyGUI/
  lint:
    cmds:
      - ruff check
      - mypy TkEasyGUI/
  test:
    cmds:
      - ruff check
      - echo "*** TODO ***"
  build-docs:
    cmds:
      - echo "Buikding..."
      - python3 update_version.py
      - python makedoc.py
      - python docs/scripts/readme_maker.py
      - echo "ok."
  deploy-build-only:
    cmds:
      - task build-docs
      - echo "Deploying..."
      - echo "-- remove cache ---"
      - rm -f -r dist
      - rm -f -r TkEasyGUI.egg-info
      - echo "build package"
      - python -m build
  deploy-test:
    cmds:
      - task deploy-build-only
      - echo "--- upload to testpypi ---""
      - python -m twine upload --repository testpypi dist/* --verbose
      - echo "[TRY] task install test"
  deploy-main:
    cmds:
      - task deploy-build-only
      - echo "--- upload to pypi(main) ---"
      - python -m twine upload dist/* --verbose





================================================
FILE: update_version.py
================================================
#!/usr/bin/env python
# pyprojet.tomlを見てパッケージのバージョンを更新する
# 使い方: python update_version.py
import sys

import toml

# read
with open("pyproject.toml", "r", encoding="utf-8") as f:
    data = toml.load(f)
version = data["project"]["version"]
versions = version.split(".")
if int(versions[0]) == 0 or int(versions[2]) == 0:
    print("---------------------------------------", file=sys.stderr)
    print("!!! BROKEN VERSION INFO", file=sys.stderr)
    print("!!! Please check : `update_version.py` & `pyproject.toml`", file=sys.stderr)
    print("---------------------------------------", file=sys.stderr)
    sys.exit(1) # 異常終了
# write
with open("TkEasyGUI/version.py", "w", encoding="utf-8") as f:
    f.write(f"""
\"\"\"
# TkEasyGUI version {version}

- audo generated by [pyproject.toml](https://github.com/kujirahand/TkEasyGUI-python/blob/main/pyproject.toml)
\"\"\"
__version__ = \"{version}\"

""".strip())
print(version)




================================================
FILE: docs/README.md
================================================
# TkEasyGUI > docs

**TkEasyGUI** is a Python library that allows for the **easy** and simple creation of **GUI** applications.

- [TkEasyGUI > README.md](https://github.com/kujirahand/TkEasyGUI-python/blob/main/README.md)
- [TkEasyGUI > Modules](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/index.md)

## Widgets documents

### TkEasyGUI popup dialogs

- [dialogs module](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/dialogs-py.md) ... popup / popup_get_file etc ...

### TkEasyGUI Elements

- [widgets module](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md) ... Window / Button / Input / Text etc ...

#### TkEasyGUI Elements list

Here is a list of elements:

- [Window](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#Window)
- [Button](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#button)
- [CalendarBrowse](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#calendarbrowse)
- [CalendarButton](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#calendarbutton)
- [Canvas](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#canvas)
- [Checkbox](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#checkbox)
- [CloseButton](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#closebutton)
- [ColorBrowse](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#colorbrowse)
- [Column](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#column)
- [Combo](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#combo)
- [FileBrowse](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#filebrowse)
- [FileSaveAs](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#filesaveas)
- [FileSaveAsBrowse](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#filesaveasbrowse)
- [FilesBrowse](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#filesbrowse)
- [FolderBrowse](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#folderbrowse)
- [Frame](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#frame)
- [Graph](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#graph)
- [HSeparator](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#hseparator)
- [Image](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#image)
- [Input](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#input)
- [InputText](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#inputtext)
- [Label](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#label)
- [ListBrowse](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#listbrowse)
- [Listbox](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#listbox)
- [Menu](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#menu)
- [Multiline](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#multiline)
- [MultilineBrowse](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#multilinebrowse)
- [Output](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#output)
- [Push](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#push)
- [Radio](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#radio)
- [Slider](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#slider)
- [Submit](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#submit)
- [Tab](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#tab)
- [TabGroup](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#tabgroup)
- [Table](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#table)
- [Text](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#text)
- [Textarea](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#textarea)
- [VPush](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#vpush)
- [VSeparator](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#vseparator)

### TkEasyGUI Utilities

- [utils](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/utils-py.md) ... get_clipboard / set_clipboard

### TkEasyGUI Original features

- [Custom Events](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/custom_events.md)

### Package developper

- [TkEasyGUI Package Developer's Guide](/docs/dev.md)



================================================
FILE: docs/custom_events.md
================================================
# TkEasyGUI > Custom Events

In addition to the unique events of the element, you can use **custom events** available in `Tkinter`.
There are several ways to bind them.

## Simple bind

After creating the element, bind the event with the bind method.
The event name will be in the format of "f{key}{handle_name}".

```py
import TkEasyGUI as sg
# (1) create Element
canvas = sg.Canvas(size=(400, 400), key="-canvas-")
window = sg.Window("Canvas", layout=[[canvas]], finalize=True)

# (2) bind custom events
canvas.bind("<ButtonPress>", "press")
canvas.bind("<ButtonRelease>", "release")
canvas.bind("<Motion>", "motion")

# (3) event loop
while True:
    event, values = window.read()
    if event == "-canvas-press":
        print(canvas.user_bind_event) # get event data
        print("x=", canvas.user_bind_event.x)
        print("y=", canvas.user_bind_event.y)
        break
    elif event == "-canvas-relase":
        pass
    elif event == "-canvas-motion":
        pass
```

## Multiple bind - using `bind_events` method

When creating an element, you can specify multiple events using the bind_events method.

```py
canvas = sg.Canvas(size=(400, 400), key="-canvas-").bind_events({
    "<ButtonPress>": "press",
    "<ButtonRelease>": "release",
    "<Motion>": "motion",
})
```

## Set custom events in constructor

Within the constructor, you can specify bind_events as an argument.

```py
canvas = sg.Canvas(
    size=(400, 400),
    key="-canvas-",
    bind_events={
        "<ButtonPress>": "mousedown",
        "<ButtonRelease>": "mouseup",
        "<Motion>": "mousemove"
    }
)
```

## Samples:

- [/tests/paint_eg.py](https://github.com/kujirahand/TkEasyGUI-python/blob/main/tests/paint_eg.py)
- [/tests/paint_compatible.py](https://github.com/kujirahand/TkEasyGUI-python/blob/main/tests/paint_compatible.py)


# Event Hook

You can hook an event before a system event occurs.
This mechanism is utilized within elements like `FileBrowse`.

```py
import TkEasyGUI as eg

window = eg.Window("Event Hook Test", layout=[
    [eg.Button("OK")],
    [eg.Button("Cancel")],
])
# register event hook
window.register_event_hooks({
    "OK": [
        lambda event, values: print("#OK#hook1:", event, values),
        lambda event, values: print("#OKhook#2:", event, values),
        lambda event, values: print("#OKhook#3:", event, values),
    ],
    "Cancel": [
        lambda event, values: print("#Cancel#hook#1:", event, values),
        lambda event, values: print("#Cancel#hook#2:", event, values),
        lambda event, values: True, # stop event propagation
        lambda event, values: print("#Cancel#hook#3:", event, values),
    ]
})
while window.is_alive():
    event, values = window.read()
    print(event, values)
    if event == "OK":
        break
    elif event == "Cancel":
        break
    elif event == "Cancel-stopped":
        break
window.close()
```

## Samples:

- [/tests/event_hooks.py](https://github.com/kujirahand/TkEasyGUI-python/blob/main/tests/event_hooks.py)



================================================
FILE: docs/dev.md
================================================
# TkEasyGUI Package Developer's Guide

- Please feel free to ask questions in the [issue tracker](https://github.com/kujirahand/TkEasyGUI-python/issues).
- If you have any requests for new features, please let us know.
  - [Discord > TkEasyGUI](https://discord.gg/NX8WEQd42S)
- Pull requests are highly welcome.
  - When sending a pull request, it would be appreciated if you could include a sample to verify the changes. Please add the file to the tests directory.
  - It would be helpful if you could include the issue number related to the commit. (example) [#96](https://github.com/kujirahand/TkEasyGUI-python/issues/96).

## Task runner

- Using [Task runner task](https://taskfile.dev/)
  - [Taskfile.yaml](/Taskfile.yml)

```sh
# check all task
task -a
# run viewer
task run
```

## Lint

```sh
task check
task lint
```

## Build documents

```sh
task build-docs
```

## Deploy to pypi

```sh
task deploy-test
task deploy-main
```



================================================
FILE: docs/installation_trouble.md
================================================
# TkEasyGUI - Installation troubles

### (ja) インストールのトラブルについて

- 0.2.24以降、パッケージ名が、全部小文字の`TkEasyGUI`から大文字込みの`TkEasyGUI`に変わりました。
  - その影響で古いバージョンからアップデートしようとすると、`ModuleNotFoundError: No module named 'TkEasyGUI'`というエラーが発生します。
  - これを防ぐために、`pip uninstall TkEasyGUI`実行後に、下記のPythonコードをIDLEやREPL(`python`コマンドで起動するインタプリタ)で実行してください。
  - その後、`pip install TkEasyGUI`を実行して最新版をインストールしてください。

```py:remove_old_package.py
# 古いTkEasyGUIパッケージを完全に削除するプログラム
import os, shutil, PIL
packages = os.path.dirname(PIL.__path__[0])
old_package = os.path.join(packages, "TkEasyGUI")
print(f"Remove: {old_package}")
if os.path.exists(old_package): shutil.rmtree(old_package)
print("ok")
```

これは、pipの問題で、パッケージを`pip uninstall`コマンドでアンインストールしても、古いパッケージ名のフォルダが残ってしまうことが問題です。

### 上記手順がうまくいかない場合

上記手順で削除できない場合があるようです。お手数ですが下記の手順を確認してください。

(1) ターミナル(PowerShell/ターミナル.app)を開いて、一度、TkEasyGUIがインストールできるか確認しましょう。

```sh
python -m pip install TkEasyGUI
```

(2) 続いて、インストールパスを調べます。

```sh
python -m pip show TkEasyGUI
```

(3) 上記手順で表示された情報の中に下記のようなLocation情報があります。

```
Location: C:\Users\<username>\AppData\Local\Programs\Python\Python312\Lib\site-packages
```

(4) Locationを確認した後、下記のコマンドを実行して、古いTkEasyGUIをアンインストールします。

```sh
python -m pip uninstall TkEasyGUI
```

(5) エクスプローラー(Windows)かFinder(macOS)を使って上記(4)のフォルダを開きます。

(6) 上記(4)のフォルダ(site-packages)の中にある「TkEasyGUI」というフォルダを探して削除します。

(7) 改めて、TkEasyGUIをインストールします。

```sh
python -m pip install TkEasyGUI
```

--------------

以上です。(以下は英語で手順を示したものです。)

### (en) Installation troubles

- From version 0.2.24, the package name has also been changed from `TkEasyGUI` to `TkEasyGUI`.
  - Updating from older versions (less than 0.2.24) will fail.
  - If you have used a previous version, you will see `ModuleNotFoundError: No module named 'TkEasyGUI'`.
  - Please run the command below to completely remove the old `TkEasyGUI` package.
  - It seems that cache files remain even if you use the `pip uninstall TkEasyGUI` command.
  - Start the `python` command or `IDLE` and execute the following command.
  - Then run `pip install TkEasyGUI` to install the latest version.

```py:remove_old_package.py
# remove old package directory
import os, shutil, PIL
packages = os.path.dirname(PIL.__path__[0])
old_package = os.path.join(packages, "TkEasyGUI")
print(f"Remove: {old_package}")
if os.path.exists(old_package): shutil.rmtree(old_package)
print("ok")
```




================================================
FILE: docs/scripts/elements.json
================================================
[
  "Button",
  "CalendarBrowse",
  "CalendarButton",
  "Canvas",
  "Checkbox",
  "CloseButton",
  "ColorBrowse",
  "Column",
  "Combo",
  "FileBrowse",
  "FileSaveAs",
  "FileSaveAsBrowse",
  "FilesBrowse",
  "FolderBrowse",
  "Frame",
  "Graph",
  "HSeparator",
  "Image",
  "Input",
  "InputText",
  "Label",
  "ListBrowse",
  "Listbox",
  "Menu",
  "Multiline",
  "MultilineBrowse",
  "Output",
  "Push",
  "Radio",
  "Slider",
  "Submit",
  "Tab",
  "TabGroup",
  "Table",
  "Text",
  "Textarea",
  "VPush",
  "VSeparator"
]


================================================
FILE: docs/scripts/readme_maker.py
================================================
# foramt documents script
import json
import os

# path
SCRIPT_DIR = os.path.dirname(__file__)
DOCS_DIR = os.path.dirname(SCRIPT_DIR)
ROOT_DIR = os.path.dirname(DOCS_DIR)
TEMPLATE_DIR = os.path.join(SCRIPT_DIR, "template")
ELEMENTS_JSON = os.path.join(SCRIPT_DIR, "elements.json")

REPO = "https://github.com/kujirahand/TkEasyGUI-python/blob/main"

print("TEMPLATE_DIR=", TEMPLATE_DIR)
print("DOCS_DIR=", DOCS_DIR)

# read
with open(os.path.join(TEMPLATE_DIR, "README.md"), "r", encoding="utf-8") as fp:
    readme = fp.read()

with open(ELEMENTS_JSON, "r", encoding="utf-8") as fp:
    elements = json.load(fp)
    result = []
    for name in elements:
        name2 = name.replace(" ", "-").lower()
        result.append(f"- [{name}]({REPO}/docs/TkEasyGUI/widgets-py.md#{name2})")
    readme = readme.replace("__ELEMENTS__", "\n".join(result))

# write
with open(os.path.join(DOCS_DIR, "README.md"), "w", encoding="utf-8") as fp:
    fp.write(readme)



================================================
FILE: docs/scripts/icon/make_icon.py
================================================
import os
from PIL import Image
import base64

icon_dir = os.path.dirname(__file__)
script_dir = os.path.dirname(icon_dir)
docs_dir = os.path.dirname(script_dir)
root_dir = os.path.dirname(docs_dir)
image_dir = os.path.join(docs_dir, "image")

# Path to the generated PNG icon from the previous step
src_path = os.path.join(icon_dir, "TkEasyGUI-org.png")
dest_path = os.path.join(icon_dir, "icon.ico")
png_path = os.path.join(image_dir, "icon64.png")
png256_path = os.path.join(image_dir, "icon256.png")
py_path = os.path.join(root_dir, "TkEasyGUI", "icon.py")

# Open the source image
img = Image.open(src_path)
# Save as ICO with the requested sizes
img.save(dest_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

# Resize to 256x256
img256 = img.resize((256, 256), Image.LANCZOS)
img256.save(png256_path, format="PNG")

# Resize to 64x64
img = img.resize((64, 64), Image.LANCZOS)
img.save(png_path, format="PNG")

# Read the ICO file and encode it to base64
with open(png_path, "rb") as ico_path:
    # Read the ICO file and encode it to base64
    # The result is a string that can be used in a data URI
    # Example: "data:image/x-icon;base64,BASE64_ENCODED_STRING"
    b64_string = base64.b64encode(ico_path.read()).decode("ascii")
    src = f"""
\"\"\"TkEasyGUI icon\"\"\"
ICON = b"{b64_string}"
"""
    with open(py_path, "w", encoding="utf-8") as fp:
        fp.write(src)
    print(src)



================================================
FILE: docs/scripts/icon/.DS_Store
================================================
[Non-text file]


================================================
FILE: docs/scripts/template/README.md
================================================
# TkEasyGUI > docs

**TkEasyGUI** is a Python library that allows for the **easy** and simple creation of **GUI** applications.

- [TkEasyGUI > README.md](https://github.com/kujirahand/TkEasyGUI-python/blob/main/README.md)
- [TkEasyGUI > Modules](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/index.md)

## Widgets documents

### TkEasyGUI popup dialogs

- [dialogs module](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/dialogs-py.md) ... popup / popup_get_file etc ...

### TkEasyGUI Elements

- [widgets module](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md) ... Window / Button / Input / Text etc ...

#### TkEasyGUI Elements list

Here is a list of elements:

- [Window](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/widgets-py.md#Window)
__ELEMENTS__

### TkEasyGUI Utilities

- [utils](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/TkEasyGUI/utils-py.md) ... get_clipboard / set_clipboard

### TkEasyGUI Original features

- [Custom Events](https://github.com/kujirahand/TkEasyGUI-python/blob/main/docs/custom_events.md)

### Package developper

- [TkEasyGUI Package Developer's Guide](/docs/dev.md)



================================================
FILE: docs/TkEasyGUI/dialogs-py.md
================================================
# Module TkEasyGUI.dialogs

TkEasyGUI dialogs.

---------------------------

- [Functions](#functions-of-TkEasyGUIdialogs)

# Functions of TkEasyGUI.dialogs

- [ask_ok_cancel](#ask_ok_cancel)
- [ask_retry_cancel](#ask_retry_cancel)
- [ask_yes_no](#ask_yes_no)
- [cast](#cast)
- [confirm](#confirm)
- [copy_to_clipboard](#copy_to_clipboard)
- [get_root_window](#get_root_window)
- [input](#input)
- [input_number](#input_number)
- [is_mac](#is_mac)
- [is_win](#is_win)
- [msgbox](#msgbox)
- [popup](#popup)
- [popup_auto_close](#popup_auto_close)
- [popup_buttons](#popup_buttons)
- [popup_cancel](#popup_cancel)
- [popup_color](#popup_color)
- [popup_error](#popup_error)
- [popup_get_date](#popup_get_date)
- [popup_get_file](#popup_get_file)
- [popup_get_folder](#popup_get_folder)
- [popup_get_form](#popup_get_form)
- [popup_get_text](#popup_get_text)
- [popup_image](#popup_image)
- [popup_info](#popup_info)
- [popup_input](#popup_input)
- [popup_listbox](#popup_listbox)
- [popup_memo](#popup_memo)
- [popup_no_buttons](#popup_no_buttons)
- [popup_no_wait](#popup_no_wait)
- [popup_non_blocking](#popup_non_blocking)
- [popup_notify](#popup_notify)
- [popup_ok](#popup_ok)
- [popup_ok_cancel](#popup_ok_cancel)
- [popup_scrolled](#popup_scrolled)
- [popup_warning](#popup_warning)
- [popup_yes_no](#popup_yes_no)
- [popup_yes_no_cancel](#popup_yes_no_cancel)
- [print](#print)
- [send_notification_mac](#send_notification_mac)
- [send_notification_win](#send_notification_win)
- [show_info](#show_info)
- [show_message](#show_message)

## ask_ok_cancel

Display a message in a popup window with OK and Cancel buttons. Return True or False. (use Tkinter)

```py
def ask_ok_cancel(message: str, title: str = "Question") -> bool:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L1364)

## ask_retry_cancel

Display a message in a popup window with Retry and Cancel buttons. Return True or False. (use Tkinter)

```py
def ask_retry_cancel(message: str, title: str = "Question") -> bool:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L1369)

## ask_yes_no

Display a message in a popup window with Yes and No buttons. Return True or False. (use Tkinter)

```py
def ask_yes_no(message: str, title: str = "Question") -> bool:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L1359)

## cast

Cast a value to a type.

This returns the value unchanged.  To the type checker this
signals that the return value has the designated type, but at
runtime we intentionally don't check anything (we want this
to be as fast as possible).

```py
def cast(typ, val):
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/Users/kujirahand/.pyenv/versions/3.13.3/lib/python3.13/typing.py#L2371)

## confirm

Display a message in a popup window with Yes and No buttons. Return True or False.

```py
def confirm(question: str, title: Union[str, None] = None) -> bool:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L1428)

## copy_to_clipboard

Copy text to clipboard

```py
def copy_to_clipboard(text):
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L74)

## get_root_window

Get root window.

```py
def get_root_window() -> tk.Tk:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L175)

## input

Display a message in a popup window with a text entry. Return the text entered.

```py
def input(
    message: str,
    title: Union[str, None] = None,
    default: str = "",
    only_number: bool = False,
    window_icon: Optional[str] = None,  # window icon, specify filename
) -> Union[str, float, None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L1395)

## input_number

Display a message in a popup window with a number entry. Return the text entered.

```py
def input_number(
    message: str,
    title: Union[str, None] = None,
    default: str = "",
    window_icon: Optional[str] = None,  # window icon, specify filename
) -> Union[float, None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L1415)

## is_mac

Platform : is mac?

```py
def is_mac() -> bool:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L92)

## is_win

Platform : is Windows?

```py
def is_win() -> bool:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L97)

## msgbox

Show message in a popup window like VB

```py
def msgbox(message: str, title: Union[str, None] = None) -> None:  # message
    """Show message in a popup window like VB"""
    title = title if title is not None else le.get_text("Information")
    messagebox.showinfo(title, message)
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L1386)

## popup

Display a message in a popup window.

#### Example:
```py
eg.popup("I like an apple.", "Information")
```

```py
def popup(
    message: str,
    title: str = "",
    size: Union[tuple[int, int], None] = None,
    icon: str = "",
    icon_size: tuple[int, int] = (48, 48),
    window_icon: Optional[str] = None,  # window icon, specify filename
    can_copy_message: bool = True,
) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L131)

## popup_auto_close

Display a message in a popup window that closes automatically after a specified time.

```py
def popup_auto_close(
    message: str,
    title: str = "",
    auto_close_duration: int = 3,
    buttons: list[str] = ["OK", "Cancel"],
    timeout_key="-TIMEOUT-",
    size: Union[tuple[int, int], None] = None,
    icon: str = "information",
    icon_size: tuple[int, int] = (48, 48),
    window_icon: Optional[str] = None,  # window icon, specify filename
    can_copy_message: bool = True,
) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L208)

## popup_buttons

Popup window with user defined buttons. Return button's label.

#### Example:
```py
color = eg.popup_buttons(
    "Which color do you like?",
    "Question",
    buttons=["red","yellow","green"])
print(color)
```

```py
def popup_buttons(
    message: str,
    title: Union[str, None] = None,
    buttons: list[str] = ["OK", "Cancel"],
    auto_close_duration: int = -1,  # auto close duration (msec)
    timeout_key: str = "-TIMEOUT-",  # timeout key
    non_blocking: bool = False,
    default: str = "",
    size: Union[tuple[int, int], None] = None,
    icon: str = "",  # filename or icon name(information/info, warning, error, question/?)
    icon_size: tuple[int, int] = (48, 48),
    window_icon: Optional[str] = None,  # window icon, specify filename
    can_copy_message: bool = True, # show copy message in popup menu
) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L40)

## popup_cancel

Display a message in a popup window with OK and Cancel buttons. Return "Cancel" or eg.WINDOW_CLOSED.

```py
def popup_cancel(
    message: str,
    title: str = "",
    size: Union[tuple[int, int], None] = None,
    icon: str = "information",
    icon_size: tuple[int, int] = (48, 48),
    window_icon: Optional[str] = None,  # window icon, specify filename
    can_copy_message: bool = True,
) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L413)

## popup_color

Popup a color selection dialog. Return the color selected.

format: "html", "rgb", "tuple"

```py
def popup_color(
    title: str = "",
    default_color: Union[str, None] = None,
    format: ColorFormatType = "html",
) -> Union[str, tuple[int, int, int], None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L1239)

## popup_error

Display a message in a popup window with an error icon.

```py
def popup_error(
    message: str,
    title: Union[str, None] = None,
    size: Union[tuple[int, int], None] = None,
    icon: str = "error",
    icon_size: tuple[int, int] = (48, 48),
    window_icon: Optional[str] = None,  # window icon, specify filename
    can_copy_message: bool = True,
    use_tk_dialog: bool = False,
) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L527)

## popup_get_date

Display a calendar in a popup window. Return the datetime entered or None.

```py
def popup_get_date(
    message: str = "",
    title: Union[str, None] = None,
    current_date: Union[datetime, None] = None,
    font: Union[tuple[str, int], None] = None,
    ok_label: Union[str, None] = None,
    cancel_label: Union[str, None] = None,
    date_format: Union[str, None] = None,
    close_when_date_chosen: bool = False,
    sunday_first: bool = False,  # Sunday is the first day of the week
    window_icon: Optional[str] = None,  # window icon, specify filename
) -> Union[datetime, None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L766)

## popup_get_file

Popup a file selection dialog. Return the file selected.

```py
def popup_get_file(
    message: str = "",
    title: Union[str, None] = None,
    initial_folder: Union[str, None] = None,
    save_as: bool = False,  # show `save as` dialog
    multiple_files: bool = False,  # can select multiple files
    file_types: tuple[tuple[str, str]] = (("All Files", "*.*"),),
    default_extension: Union[str, None] = None,
    no_window: Union[bool, None] = None,  # for compatibility
    **kw,
) -> Union[str, tuple[str], None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L613)

## popup_get_folder

Popup a folder selection dialog. Return the folder selected.

```py
def popup_get_folder(
    message: str = "",
    title: Union[str, None] = None,
    default_path: Union[str, None] = None,
    no_window: Union[bool, None] = None,  # for compatibility
    **kw,
) -> Union[str, None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L668)

## popup_get_form

Displays a form that allows multiple items to be entered.

By specifying the labels and input types for each item, the form is automatically generated and displayed in a dialog.
When the user enters the items and clicks [OK], it returns `{label: value}`. If the user clicks [Cancel], it returns `None`.

### Arguments:
- `form_items` (list): A list of form items. Each item can be:
  - A string (label only, default type is "text").
  - A tuple of `(label, default_value)` (default type is "text").
  - A tuple of `(label, default_value, type)` where `type` can be:
    - `"text"`: Single-line text input.
    - `"number"`: Numeric input.
    - `"password"`: Password input (masked).
    - `"combo"`: Dropdown menu.
    - `"list"`: List selection.
    - `"date"`: Date picker.
    - `"file"`: File selection.
    - `"files"`: Multiple file selection.
    - `"folder"`: Folder selection.
    - `"color"`: Color picker.

- `title` (str): The title of the form window. Default is "Form".
- `size` (tuple[int, int] | None): The size of the form window. Default is `None`.

### Returns:
- `dict[str, Any] | None`: A dictionary with `{label: value}` pairs if the user clicks [OK]. Returns `None` if the user clicks [Cancel].

### Examples:
#### Simple Example:
```python
import TkEasyGUI as eg
form = eg.popup_get_form(["Name", "Hobbies"])
if form:
    name = form["Name"]
    hobbies = form["Hobbies"]
    eg.print(f"name={name}, hobbies={hobbies}")
```

```py
def popup_get_form(
    form_items: list[
    Union[str, tuple[str, Any], tuple[str, Any, str]]
    ],  # list of form items(label[,selection or default][,type])
    title: str = "Form",  # window title
    size: Union[tuple[int, int], None] = None,
    window_icon: Optional[str] = None,  # window icon, specify filename
) -> Union[dict[str, Any], None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L977)

## popup_get_text

Display a message in a popup window with a text entry. Return the text entered.

```py
def popup_get_text(
    message: str,
    title: Union[str, None] = None,
    default: Union[str, None] = None,
    default_text: Union[str, None] = None,  # same as default for compatibility
    font: Optional[FontType] = None,
    size: Union[tuple[int, int], None] = None,
    window_icon: Optional[str] = None,  # window icon, specify filename
) -> Union[str, None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L437)

## popup_image

Display an image in a popup window. Return the pushed Button("OK" or None).

```py
def popup_image(
    message: str,
    title: Union[str, None] = None,
    image_path: Union[str, None] = None,
    image_data: Union[bytes, None] = None,
    size: tuple[int, int] = (400, 300),
    ok_label: Union[str, None] = None,
    ok_value: str = "OK",
    cancel_label: Union[str, None] = None,
    cancel_value: Union[str, None] = None,
    font: Union[FontType, None] = None,
    window_icon: Optional[str] = None,  # window icon, specify filename
) -> Union[str, None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L1318)

## popup_info

Display a message in a popup window with an warning icon.

```py
def popup_info(
    message: str,
    title: Union[str, None] = None,
    size: Union[tuple[int, int], None] = None,
    icon: str = "information",
    icon_size: tuple[int, int] = (48, 48),
    window_icon: Optional[str] = None,  # window icon, specify filename
    can_copy_message: bool = True,
    use_tk_dialog: bool = False,
) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L585)

## popup_input

Display a message in a popup window with a text entry. Return the text entered. if canceled, return cancel_value.

```py
def popup_input(
    message: str,
    title: Optional[str] = None,
    default: str = "",
    ok_label: Optional[str] = None,
    cancel_label: Optional[str] = None,
    cancel_value: Any = None,
    only_number: bool = False,
    font: Optional[FontType] = None,
    size: Union[tuple[int, int], None] = None,
    window_icon: Optional[str] = None,  # window icon, specify filename
) -> Union[str, float, None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L466)

## popup_listbox

Display Listbox in a popup window

```py
def popup_listbox(
    values: list[str],  # list of items
    message: str = "",
    title: str = "",
    size: tuple[int, int] = (20, 7),
    font: Union[FontType, None] = None,
    default_value: Union[str, None] = None,  # default value
    multiple: bool = False,  # multiple selection
    resizable: bool = True,  # resizable
    window_icon: Optional[str] = None,  # window icon, specify filename
) -> Union[str, None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L1262)

## popup_memo

Display a multiline message in a popup window. Return the text entered. if canceled, return cancel_value(default is None).

```py
def popup_memo(
    message: str,  # Text to enter in a multi-line text box
    title: Union[str, None] = None,  # Window title
    size: tuple[int, int] = (60, 8),  # Size of the text box
    readonly: bool = False,  # Read-only mode
    header: str = "",  # Label displayed above the text box
    resizable: bool = True,  # resizable
    window_icon: Optional[str] = None,  # window icon, specify filename
    ok_label: Union[str, None] = None,
    cancel_label: Union[str, None] = None,
    cancel_value: Union[str, None] = None,
    font: Union[FontType, None] = None,
) -> Union[str, None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L683)

## popup_no_buttons

Display a message in a popup window without buttons.

```py
def popup_no_buttons(
    message: str,
    title: str = "",
    icon: str = "",
    icon_size: tuple[int, int] = (48, 48),
    window_icon: Optional[str] = None,  # window icon, specify filename
    size: Union[tuple[int, int], None] = None,
    can_copy_message: bool = True,
) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L186)

## popup_no_wait

Display a message in a popup window without waiting.

```py
def popup_no_wait(
    message: str,
    title: str = "",
    size: Union[tuple[int, int], None] = None,
    icon: str = "information",
    icon_size: tuple[int, int] = (48, 48),
    window_icon: Optional[str] = None,  # window icon, specify filename
    **kw,
) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L235)

## popup_non_blocking

(TODO) Display a non blocking window

```py
def popup_non_blocking(
    message: str,
    title: str = "",
    auto_close_duration: int = -1,
    size: Union[tuple[int, int], None] = None,
    icon: str = "",
    icon_size: tuple[int, int] = (48, 48),
    window_icon: Optional[str] = None,  # window icon, specify filename
    can_copy_message=True,
) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L161)

## popup_notify

Popup a information

```py
def popup_notify(message: str, title: str = "") -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L1143)

## popup_ok

Display a message in a popup window.(Alias popup)

```py
def popup_ok(
    message: str,
    title: str = "",
    size: Union[tuple[int, int], None] = None,
    icon: str = "information",
    icon_size: tuple[int, int] = (48, 48),
    window_icon: Optional[str] = None,  # window icon, specify filename
    can_copy_message: bool = True,
) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L257)

## popup_ok_cancel

Display a message in a popup window with OK and Cancel buttons. Return "OK" or "Cancel" or eg.WINDOW_CLOSED.

```py
def popup_ok_cancel(
    message: str,
    title: Union[str, None] = None,
    ok_label: Union[str, None] = None,
    cancel_label: Union[str, None] = None,
    ok_value: str = "OK",
    cancel_value: str = "Cancel",
    size: Union[tuple[int, int], None] = None,
    icon: str = "?",
    icon_size: tuple[int, int] = (48, 48),
    window_icon: Optional[str] = None,  # window icon, specify filename
    can_copy_message: bool = True,
) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L279)

## popup_scrolled

Display a multiline message in a popup window. Return the text entered. if canceled, return cancel_value(default is None).

#### Example:
```py
import TkEasyGUI as eg
text = eg.popup_scrolled("This is a long text.", "Information")
eg.print(text)
```

```py
def popup_scrolled(
    message: str,  # Text to enter in a multi-line text box
    title: Union[str, None] = None,  # Window title
    size: tuple[int, int] = (40, 5),  # Size of the text box
    readonly: bool = False,  # Read-only mode
    header: str = "",  # Label displayed above the text box
    resizable: bool = True,  # resizable
    window_icon: Optional[str] = None,  # window icon, specify filename
    ok_label: Union[str, None] = None,
    cancel_label: Union[str, None] = None,
    cancel_value: Union[str, None] = None,
    font: Union[FontType, None] = None,
) -> Union[str, None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L712)

## popup_warning

Display a message in a popup window with an warning icon.

```py
def popup_warning(
    message: str,
    title: Union[str, None] = None,
    size: Union[tuple[int, int], None] = None,
    icon: str = "warning",
    icon_size: tuple[int, int] = (48, 48),
    window_icon: Optional[str] = None,  # window icon, specify filename
    can_copy_message: bool = True,
    use_tk_dialog: bool = False,
) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L557)

## popup_yes_no

Display a message in a popup window with Yes and No buttons. Return "Yes" or "No" (or eg.WINDOW_CLOSED).

@see [tests/localize_test.py](https://github.com/kujirahand/TkEasyGUI-python/blob/main/tests/localize_test.py)
#### Example - simple:
Ask user question, [Yes] or [No] buttons.
```py
ans = eg.popup_yes_no("Do you like Sushi?", "Question")
print(ans) # "Yes" or "No"
```
#### Eample - custom label:
Ask user question in special button
```py
ans = eg.popup_yes_no("Do you eat Sushi?", yes_label="EAT", no_label="no")
print(ans) # "Yes" or "No"
```
#### Example - custom return value:
ans = eg.popup_yes_no("Can you speak Japanese?", yes_value="can", no_value="no")
print(ans) # "can" or "no"

```py
def popup_yes_no(
    message: str,  # question message
    title: Union[str, None] = None,  # window title
    yes_label: Union[str, None] = None,  # label for yes button
    no_label: Union[str, None] = None,  # label for no button
    yes_value: str = "Yes",  # return value for yes
    no_value: str = "No",  # return value for no
    size: Union[tuple[int, int], None] = None,
    icon: str = "?",
    icon_size: tuple[int, int] = (48, 48),
    window_icon: Optional[str] = None,  # window icon, specify filename
    can_copy_message: bool = True,
) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L314)

## popup_yes_no_cancel

Display a message in a popup window with Yes and No buttons. Return "Yes" or "No" or "Cancel".

```py
def popup_yes_no_cancel(
    message: str,
    title: Union[str, None] = None,
    yes_label: Union[str, None] = None,
    no_label: Union[str, None] = None,
    cancel_label: Union[str, None] = None,
    yes_value: str = "Yes",
    no_value: str = "No",
    cancel_value: str = "Cancel",
    size: Union[tuple[int, int], None] = None,
    icon: str = "?",
    icon_size: tuple[int, int] = (48, 48),
    window_icon: Optional[str] = None,  # window icon, specify filename
    can_copy_message: bool = True,
) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L370)

## print

Print message to popup window.(call default print function if no_window is True)

```py
def print(*args, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L1406)

## send_notification_mac

Send Notification on mac

```py
def send_notification_mac(message: str, title: str = "") -> bool:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L1154)

## send_notification_win

Send Notification on Windows using PowerShell

```py
def send_notification_win(message: str, title: str = "") -> bool:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L1175)

## show_info

Show message in a popup window

```py
def show_info(message: str, title: Union[str, None] = None) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L1380)

## show_message

Show message in a popup window

```py
def show_message(message: str, title: Union[str, None] = None) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/dialogs.py#L1374)




================================================
FILE: docs/TkEasyGUI/index.md
================================================
# Module TkEasyGUI

TkEasyGUI - A simple GUI library for Python using tkinter.

## Submodules

[TkEasyGUI.dialogs](dialogs-py.md)

[TkEasyGUI.utils](utils-py.md)

[TkEasyGUI.version](version-py.md)

[TkEasyGUI.widgets](widgets-py.md)


================================================
FILE: docs/TkEasyGUI/locale_easy-py.md
================================================
# Module TkEasyGUI.locale_easy

TkEasyGUI locale module

---------------------------

- [Functions](#functions-of-TkEasyGUIlocale_easy)

# Functions of TkEasyGUI.locale_easy

- [get_locale](#get_locale)
- [get_text](#get_text)
- [set_locale](#set_locale)
- [set_text](#set_text)

## get_locale

Get locale

```py
def get_locale() -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/locale_easy.py#L66)

## get_text

Get locale text

```py
def get_text(key: str, default_text: Union[str, None] = None) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/locale_easy.py#L84)

## set_locale

Set locale

```py
def set_locale(locale: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/locale_easy.py#L78)

## set_text

Set locale text

```py
def set_text(key: str, message: str, locale: str = "") -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/locale_easy.py#L95)




================================================
FILE: docs/TkEasyGUI/utils-py.md
================================================
# Module TkEasyGUI.utils

TkEasyGUI utilities functions.

---------------------------

- [Functions](#functions-of-TkEasyGUIutils)

# Functions of TkEasyGUI.utils

- [append_text_file](#append_text_file)
- [convert_color_html](#convert_color_html)
- [convert_color_rgb16](#convert_color_rgb16)
- [copy_to_clipboard](#copy_to_clipboard)
- [generate_element_id](#generate_element_id)
- [generate_element_style_key](#generate_element_style_key)
- [get_clipboard](#get_clipboard)
- [get_current_theme](#get_current_theme)
- [get_platform](#get_platform)
- [get_root_window](#get_root_window)
- [get_tnemes](#get_tnemes)
- [get_ttk_style](#get_ttk_style)
- [is_mac](#is_mac)
- [is_win](#is_win)
- [load_json_file](#load_json_file)
- [load_text_file](#load_text_file)
- [paste_from_clipboard](#paste_from_clipboard)
- [register_element_key](#register_element_key)
- [remove_element_key](#remove_element_key)
- [save_json_file](#save_json_file)
- [save_text_file](#save_text_file)
- [screenshot](#screenshot)
- [set_PySimpleGUI_compatibility](#set_pysimplegui_compatibility)
- [set_clipboard](#set_clipboard)
- [set_default_theme](#set_default_theme)
- [set_theme](#set_theme)
- [str_to_float](#str_to_float)
- [theme](#theme)

## append_text_file

Append text file.

```py
def append_text_file(filename: str, text: str, encoding: str = "utf-8") -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L130)

## convert_color_html

Convert RGB color(16bit tuple) to HTML color name.

```py
def convert_color_html(color_name: str) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L286)

## convert_color_rgb16

Convert color to RGB, return (r, g, b) tuple. range=0-65535

```py
def convert_color_rgb16(color_name: str) -> tuple[int, int, int]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L280)

## copy_to_clipboard

Copy text to clipboard

```py
def copy_to_clipboard(text):
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L74)

## generate_element_id

Generate a unique id for a value element.

```py
def generate_element_id() -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L336)

## generate_element_style_key

Get a unique id for an element.

```py
def generate_element_style_key(element_type: str) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L301)

## get_clipboard

Get text from clipboard

```py
def get_clipboard():
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L69)

## get_current_theme

Get current theme

```py
def get_current_theme() -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L255)

## get_platform

Get platform

```py
def get_platform() -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L87)

## get_root_window

Get root window.

```py
def get_root_window() -> tk.Tk:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L175)

## get_tnemes

Get theme list

```py
print(get_themes())
```

```py
def get_tnemes() -> tuple[str, ...]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L237)

## get_ttk_style

Get ttk style

```py
def get_ttk_style() -> ttk.Style:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L208)

## is_mac

Platform : is mac?

```py
def is_mac() -> bool:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L92)

## is_win

Platform : is Windows?

```py
def is_win() -> bool:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L97)

## load_json_file

Load JSON file.

```py
def load_json_file(filename: str, default_value: Any = None) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L136)

## load_text_file

Load text file.

```py
def load_text_file(
    filename: str, encoding: str = "utf-8", default_value: str = ""
) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L113)

## paste_from_clipboard

Get text from clipboard

```py
def paste_from_clipboard():
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L79)

## register_element_key

Register element key.

```py
def register_element_key(key: KeyType) -> bool:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L317)

## remove_element_key

Remove element key.

```py
def remove_element_key(key: KeyType) -> bool:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L325)

## save_json_file

Save JSON file.

```py
def save_json_file(filename: str, data: Any) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L147)

## save_text_file

Save text file.

```py
def save_text_file(filename: str, text: str, encoding: str = "utf-8") -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L124)

## screenshot

Take a screenshot.

```py
def screenshot() -> PIL.Image.Image:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L102)

## set_PySimpleGUI_compatibility

Set compatibility with PySimpleGUI (Default=True)

```py
def set_PySimpleGUI_compatibility(flag: bool = True) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L202)

## set_clipboard

Copy text to clipboard

```py
def set_clipboard(text):
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L64)

## set_default_theme

Set default theme

```py
print(get_themes())
```

```py
def set_default_theme() -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L260)

## set_theme

Change look and feel

- macOS --- ('aqua', 'clam', 'alt', 'default', 'classic')
- Windows --- ('winnative', 'clam', 'alt', 'default', 'classic', 'vista', 'xpnative')
- Linux --- ('clam', 'alt', 'default', 'classic')

```py
def set_theme(name: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L221)

## str_to_float

Convert string to float.

```py
def str_to_float(value: str, default_value: float = 0) -> float:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L158)

## theme

Set theme (alias of set_theme)

```py
def theme(name: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/utils.py#L250)




================================================
FILE: docs/TkEasyGUI/version-py.md
================================================
# Module TkEasyGUI.version

# TkEasyGUI version 1.0.36

- audo generated by [pyproject.toml](https://github.com/kujirahand/TkEasyGUI-python/blob/main/pyproject.toml)

---------------------------






================================================
FILE: docs/TkEasyGUI/widgets-py.md
================================================
# Module TkEasyGUI.widgets

TkEasyGUI Widgets.

---------------------------

- [Classes](#classes-of-TkEasyGUIwidgets)
- [Functions](#functions-of-TkEasyGUIwidgets)

# Classes of TkEasyGUI.widgets

- [Button](#button)
- [CalendarBrowse](#calendarbrowse)
- [CalendarButton](#calendarbutton)
- [Canvas](#canvas)
- [Checkbox](#checkbox)
- [CloseButton](#closebutton)
- [ColorBrowse](#colorbrowse)
- [Column](#column)
- [Combo](#combo)
- [Element](#element)
- [FileBrowse](#filebrowse)
- [FileSaveAs](#filesaveas)
- [FileSaveAsBrowse](#filesaveasbrowse)
- [FilesBrowse](#filesbrowse)
- [FolderBrowse](#folderbrowse)
- [Frame](#frame)
- [Graph](#graph)
- [HSeparator](#hseparator)
- [Image](#image)
- [Input](#input)
- [InputText](#inputtext)
- [Label](#label)
- [ListBrowse](#listbrowse)
- [Listbox](#listbox)
- [Menu](#menu)
- [Multiline](#multiline)
- [MultilineBrowse](#multilinebrowse)
- [Output](#output)
- [Push](#push)
- [Radio](#radio)
- [Slider](#slider)
- [Submit](#submit)
- [Tab](#tab)
- [TabGroup](#tabgroup)
- [Table](#table)
- [Text](#text)
- [Textarea](#textarea)
- [TkEasyError](#tkeasyerror)
- [VPush](#vpush)
- [VSeparator](#vseparator)
- [Window](#window)

## Button

Button element

**Example**
The program below changes the button's label to "Pushed" when the button is pressed.
```python
import TkEasyGUI as eg
button:eg.Button = eg.Button("Push me")
with eg.Window("Title", layout=[[button]]) as window:
    for event, values in window.event_iter():
        if event == button.get_text():
            button.set_text("Pushed")
            break
```

```py
class Button(
    self,
    button_text: str = "Button",
    key: Union[str, None] = None,
    disabled: bool = False,
    size: Union[tuple[int, int], None] = None,
    tooltip: Union[str, None] = None,  # (TODO) tooltip
    button_color: Union[str, tuple[str, str], None] = None,
    width: Optional[int] = None,  # set characters width
    # text props
    text_align: Union[TextAlign, None] = "left",  # text align
    font: Union[FontType, None] = None,  # font
    color: Union[str, None] = None,  # text color
    text_color: Union[str, None] = None,  # same as color
    background_color: Optional[str] = None,  # background color (not supported on macOS)
    # pack props
    expand_x: bool = False,
    expand_y: bool = False,
    pad: Union[PadType, None] = None,
    # other
    use_ttk_buttons: bool = False,
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Methods of Button

- [bind](#buttonbind)
- [bind_events](#buttonbind_events)
- [create](#buttoncreate)
- [disptach_event](#buttondisptach_event)
- [get](#buttonget)
- [get_height](#buttonget_height)
- [get_name](#buttonget_name)
- [get_prev_element](#buttonget_prev_element)
- [get_text](#buttonget_text)
- [get_width](#buttonget_width)
- [post_create](#buttonpost_create)
- [prepare_create](#buttonprepare_create)
- [set_button_color](#buttonset_button_color)
- [set_cursor](#buttonset_cursor)
- [set_disabled](#buttonset_disabled)
- [set_text](#buttonset_text)
- [update](#buttonupdate)

### Button.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Button.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Button.create

Create a Button widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Button.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Button.get

Returns the text of the button..

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Button.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Button.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Button.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Button.get_text

Get the text of the button.

```py
def get_text(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Button.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Button.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Button.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Button.set_button_color

Set the button color.

```py
def set_button_color(
    self, button_color: Union[str, tuple[str, str]], update: bool = True
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Button.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Button.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Button.set_text

Set the text of the button.

```py
def set_text(self, text: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Button.update

Update the widget.

```py
def update(
    self,
    text: Union[str, None] = None,
    disabled: Union[bool, None] = None,
    button_color: Union[str, tuple[str, str], None] = None,
    **kw,
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

## CalendarBrowse

CalendarBrowse element.

```py
class CalendarBrowse(
    self,
    button_text: str = "...",
    key: Union[str, None] = None,
    target_key: Union[str, None] = None,
    default_date: Union[datetime, None] = None,
    date_format: str = "%Y-%m-%d",
    title: str = "",
    enable_events: bool = False,  # enable changing events
    # other
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### Methods of CalendarBrowse

- [bind](#calendarbrowsebind)
- [bind_events](#calendarbrowsebind_events)
- [create](#calendarbrowsecreate)
- [disptach_event](#calendarbrowsedisptach_event)
- [get](#calendarbrowseget)
- [get_height](#calendarbrowseget_height)
- [get_name](#calendarbrowseget_name)
- [get_prev_element](#calendarbrowseget_prev_element)
- [get_width](#calendarbrowseget_width)
- [post_create](#calendarbrowsepost_create)
- [prepare_create](#calendarbrowseprepare_create)
- [set_cursor](#calendarbrowseset_cursor)
- [set_disabled](#calendarbrowseset_disabled)
- [set_text](#calendarbrowseset_text)
- [show_dialog](#calendarbrowseshow_dialog)
- [update](#calendarbrowseupdate)

### CalendarBrowse.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarBrowse.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarBrowse.create

Create a FileBrowse widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarBrowse.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarBrowse.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarBrowse.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarBrowse.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarBrowse.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarBrowse.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarBrowse.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarBrowse.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarBrowse.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarBrowse.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarBrowse.set_text

Set the text of the button.

```py
def set_text(self, text: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarBrowse.show_dialog

Show file dialog

```py
def show_dialog(self, *args) -> Union[datetime, None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarBrowse.update

Update the widget.

```py
def update(self, text: Union[str, None] = None, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

## CalendarButton

CalendarButton element. (alias of CalendarBrowse)

```py
class CalendarButton(
    self,
    button_text: str = "...",
    key: Union[str, None] = None,
    target_key: Union[str, None] = None,
    default_date: Union[datetime, None] = None,
    date_format: str = "%Y-%m-%d",
    title: str = "",
    enable_events: bool = False,  # enable changing events
    # other
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### Methods of CalendarButton

- [bind](#calendarbuttonbind)
- [bind_events](#calendarbuttonbind_events)
- [create](#calendarbuttoncreate)
- [disptach_event](#calendarbuttondisptach_event)
- [get](#calendarbuttonget)
- [get_height](#calendarbuttonget_height)
- [get_name](#calendarbuttonget_name)
- [get_prev_element](#calendarbuttonget_prev_element)
- [get_width](#calendarbuttonget_width)
- [post_create](#calendarbuttonpost_create)
- [prepare_create](#calendarbuttonprepare_create)
- [set_cursor](#calendarbuttonset_cursor)
- [set_disabled](#calendarbuttonset_disabled)
- [set_text](#calendarbuttonset_text)
- [show_dialog](#calendarbuttonshow_dialog)
- [update](#calendarbuttonupdate)

### CalendarButton.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarButton.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarButton.create

Create a FileBrowse widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarButton.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarButton.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarButton.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarButton.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarButton.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarButton.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarButton.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarButton.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarButton.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarButton.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarButton.set_text

Set the text of the button.

```py
def set_text(self, text: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarButton.show_dialog

Show file dialog

```py
def show_dialog(self, *args) -> Union[datetime, None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

### CalendarButton.update

Update the widget.

```py
def update(self, text: Union[str, None] = None, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4547)

## Canvas

Canvas element.

This widget provides the same drawing methods as [tk.Canvas](https://tkdocs.com/tutorial/canvas.html).
methods: create_line/create_rectangle/create_oval/create_polygon/create_arc/create_image/delete etc...

```py
class Canvas(
    self,
    key: Union[str, None] = None,
    enable_events: bool = False,
    background_color: Union[str, None] = None,
    size: tuple[int, int] = (300, 300),
    # other
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3252)

### Methods of Canvas

- [bind](#canvasbind)
- [bind_events](#canvasbind_events)
- [clear](#canvasclear)
- [create](#canvascreate)
- [disptach_event](#canvasdisptach_event)
- [get](#canvasget)
- [get_height](#canvasget_height)
- [get_name](#canvasget_name)
- [get_prev_element](#canvasget_prev_element)
- [get_width](#canvasget_width)
- [post_create](#canvaspost_create)
- [prepare_create](#canvasprepare_create)
- [set_cursor](#canvasset_cursor)
- [set_disabled](#canvasset_disabled)
- [update](#canvasupdate)

### Canvas.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3252)

### Canvas.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3252)

### Canvas.clear

Clear the canvas.

```py
def clear(self) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3252)

### Canvas.create

Create Canvas widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3252)

### Canvas.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3252)

### Canvas.get

Return Widget

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3252)

### Canvas.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3252)

### Canvas.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3252)

### Canvas.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3252)

### Canvas.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3252)

### Canvas.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3252)

### Canvas.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3252)

### Canvas.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3252)

### Canvas.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3252)

### Canvas.update

Update the widget.

```py
def update(self, *args, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3252)

## Checkbox

Checkbox element.

```py
class Checkbox(
    self,
    text: str = "",
    default: bool = False,
    key: Union[str, None] = None,
    enable_events: bool = False,
    group_id: Union[
    str, None
    ] = None,  # If a group_id is provided, the values will contain key's list of True
    # other
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2278)

### Methods of Checkbox

- [bind](#checkboxbind)
- [bind_events](#checkboxbind_events)
- [create](#checkboxcreate)
- [disptach_event](#checkboxdisptach_event)
- [get](#checkboxget)
- [get_height](#checkboxget_height)
- [get_name](#checkboxget_name)
- [get_prev_element](#checkboxget_prev_element)
- [get_value](#checkboxget_value)
- [get_width](#checkboxget_width)
- [post_create](#checkboxpost_create)
- [prepare_create](#checkboxprepare_create)
- [set_cursor](#checkboxset_cursor)
- [set_disabled](#checkboxset_disabled)
- [set_text](#checkboxset_text)
- [set_value](#checkboxset_value)
- [update](#checkboxupdate)

### Checkbox.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2278)

### Checkbox.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2278)

### Checkbox.create

Create a Checkbox widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2278)

### Checkbox.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2278)

### Checkbox.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2278)

### Checkbox.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2278)

### Checkbox.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2278)

### Checkbox.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2278)

### Checkbox.get_value

Get the value of the widget.

```py
def get_value(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2278)

### Checkbox.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2278)

### Checkbox.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2278)

### Checkbox.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2278)

### Checkbox.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2278)

### Checkbox.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2278)

### Checkbox.set_text

Set the text of the widget.

```py
def set_text(self, text: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2278)

### Checkbox.set_value

Set the value of the widget.

```py
def set_value(self, b: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2278)

### Checkbox.update

Update the widget.

```py
def update(self, *args, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2278)

## CloseButton

CloseButton element.

```py
class CloseButton(
    self,
    button_text: str = "Close",
    key: Union[str, None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2245)

### Methods of CloseButton

- [bind](#closebuttonbind)
- [bind_events](#closebuttonbind_events)
- [close_window](#closebuttonclose_window)
- [create](#closebuttoncreate)
- [disptach_event](#closebuttondisptach_event)
- [get](#closebuttonget)
- [get_height](#closebuttonget_height)
- [get_name](#closebuttonget_name)
- [get_prev_element](#closebuttonget_prev_element)
- [get_text](#closebuttonget_text)
- [get_width](#closebuttonget_width)
- [post_create](#closebuttonpost_create)
- [prepare_create](#closebuttonprepare_create)
- [set_button_color](#closebuttonset_button_color)
- [set_cursor](#closebuttonset_cursor)
- [set_disabled](#closebuttonset_disabled)
- [set_text](#closebuttonset_text)
- [update](#closebuttonupdate)

### CloseButton.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2245)

### CloseButton.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2245)

### CloseButton.close_window

Close the window.

```py
def close_window(self) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2245)

### CloseButton.create

Create a Button widget.

```py
def create(self, win: Window, parent: tk.Widget) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2245)

### CloseButton.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2245)

### CloseButton.get

Returns the text of the button..

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2245)

### CloseButton.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2245)

### CloseButton.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2245)

### CloseButton.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2245)

### CloseButton.get_text

Get the text of the button.

```py
def get_text(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2245)

### CloseButton.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2245)

### CloseButton.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2245)

### CloseButton.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2245)

### CloseButton.set_button_color

Set the button color.

```py
def set_button_color(
    self, button_color: Union[str, tuple[str, str]], update: bool = True
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2245)

### CloseButton.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2245)

### CloseButton.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2245)

### CloseButton.set_text

Set the text of the button.

```py
def set_text(self, text: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2245)

### CloseButton.update

Update the widget.

```py
def update(
    self,
    text: Union[str, None] = None,
    disabled: Union[bool, None] = None,
    button_color: Union[str, tuple[str, str], None] = None,
    **kw,
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2245)

## ColorBrowse

ColorBrowse element.

```py
class ColorBrowse(
    self,
    button_text: str = "...",
    key: Union[str, None] = None,
    target_key: Union[str, None] = None,
    default_color: Union[str, None] = None,
    title: str = "",
    enable_events: bool = False,  # enable changing events
    # other
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4401)

### Methods of ColorBrowse

- [bind](#colorbrowsebind)
- [bind_events](#colorbrowsebind_events)
- [create](#colorbrowsecreate)
- [disptach_event](#colorbrowsedisptach_event)
- [get](#colorbrowseget)
- [get_height](#colorbrowseget_height)
- [get_name](#colorbrowseget_name)
- [get_prev_element](#colorbrowseget_prev_element)
- [get_width](#colorbrowseget_width)
- [post_create](#colorbrowsepost_create)
- [prepare_create](#colorbrowseprepare_create)
- [set_cursor](#colorbrowseset_cursor)
- [set_disabled](#colorbrowseset_disabled)
- [set_text](#colorbrowseset_text)
- [show_dialog](#colorbrowseshow_dialog)
- [update](#colorbrowseupdate)

### ColorBrowse.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4401)

### ColorBrowse.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4401)

### ColorBrowse.create

Create a FileBrowse widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4401)

### ColorBrowse.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4401)

### ColorBrowse.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4401)

### ColorBrowse.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4401)

### ColorBrowse.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4401)

### ColorBrowse.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4401)

### ColorBrowse.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4401)

### ColorBrowse.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4401)

### ColorBrowse.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4401)

### ColorBrowse.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4401)

### ColorBrowse.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4401)

### ColorBrowse.set_text

Set the text of the button.

```py
def set_text(self, text: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4401)

### ColorBrowse.show_dialog

Show file dialog

```py
def show_dialog(self, *args) -> Union[str, None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4401)

### ColorBrowse.update

Update the widget.

```py
def update(self, text: Union[str, None] = None, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4401)

## Column

Frame element.

```py
class Column(
    self,
    layout: LayoutType,
    key: str = "",
    background_color: Union[str, None] = None,
    vertical_alignment: TextVAlign = "top",
    size: Union[tuple[int, int], None] = None,  # set (width, height) pixel size
    width: Union[int, None] = None,  # set pixel width
    # text props
    text_align: Union[TextAlign, None] = "left",  # text align
    # pack props
    expand_x: bool = False,
    expand_y: bool = False,
    pad: Union[PadType, None] = None,
    # other
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1600)

### Methods of Column

- [bind](#columnbind)
- [bind_events](#columnbind_events)
- [create](#columncreate)
- [disptach_event](#columndisptach_event)
- [get](#columnget)
- [get_height](#columnget_height)
- [get_name](#columnget_name)
- [get_prev_element](#columnget_prev_element)
- [get_width](#columnget_width)
- [post_create](#columnpost_create)
- [prepare_create](#columnprepare_create)
- [set_cursor](#columnset_cursor)
- [set_disabled](#columnset_disabled)
- [update](#columnupdate)

### Column.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1600)

### Column.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1600)

### Column.create

Create a Column element

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1600)

### Column.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1600)

### Column.get

Return Widget

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1600)

### Column.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1600)

### Column.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1600)

### Column.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1600)

### Column.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1600)

### Column.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1600)

### Column.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1600)

### Column.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1600)

### Column.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1600)

### Column.update

Update the widget.

```py
def update(self, *args, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1600)

## Combo

Combo element.

```py
class Combo(
    self,
    values: list[str] = [],
    default_value: str = "",
    key: Union[str, None] = None,
    enable_events: bool = False,
    readonly: bool = False,
    # other
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3854)

### Methods of Combo

- [bind](#combobind)
- [bind_events](#combobind_events)
- [create](#combocreate)
- [disptach_event](#combodisptach_event)
- [get](#comboget)
- [get_height](#comboget_height)
- [get_name](#comboget_name)
- [get_prev_element](#comboget_prev_element)
- [get_width](#comboget_width)
- [post_create](#combopost_create)
- [prepare_create](#comboprepare_create)
- [set_cursor](#comboset_cursor)
- [set_disabled](#comboset_disabled)
- [set_readonly](#comboset_readonly)
- [set_value](#comboset_value)
- [set_values](#comboset_values)
- [update](#comboupdate)

### Combo.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3854)

### Combo.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3854)

### Combo.create

[Combo.create] create Listbox widget

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3854)

### Combo.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3854)

### Combo.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3854)

### Combo.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3854)

### Combo.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3854)

### Combo.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3854)

### Combo.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3854)

### Combo.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3854)

### Combo.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3854)

### Combo.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3854)

### Combo.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3854)

### Combo.set_readonly

Set readonly

```py
def set_readonly(self, readonly: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3854)

### Combo.set_value

Set the value of the widget.

```py
def set_value(self, v: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3854)

### Combo.set_values

Set values to list

```py
def set_values(self, values: list[str]) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3854)

### Combo.update

Update the widget.

```py
def update(self, *args, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3854)

## Element

Element class.

```py
class Element(
    self,
    element_type: str,  # element type
    ttk_style_name: str,  # tkinter widget type
    key: Optional[KeyType],  # key
    has_value: bool,  # has value
    metadata: Union[dict[str, Any], None] = None,  # meta data
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1148)

### Methods of Element

- [bind](#elementbind)
- [bind_events](#elementbind_events)
- [create](#elementcreate)
- [disptach_event](#elementdisptach_event)
- [get](#elementget)
- [get_height](#elementget_height)
- [get_name](#elementget_name)
- [get_prev_element](#elementget_prev_element)
- [get_width](#elementget_width)
- [post_create](#elementpost_create)
- [prepare_create](#elementprepare_create)
- [set_cursor](#elementset_cursor)
- [set_disabled](#elementset_disabled)
- [update](#elementupdate)

### Element.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1148)

### Element.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1148)

### Element.create

Create a widget.

```py
def create(self, win: Window, parent: tk.Widget) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1148)

### Element.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1148)

### Element.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1148)

### Element.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1148)

### Element.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1148)

### Element.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1148)

### Element.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1148)

### Element.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1148)

### Element.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1148)

### Element.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1148)

### Element.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1148)

### Element.update

Update widget configuration.

```py
def update(self, *args, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1148)

## FileBrowse

FileBrowse element.

```py
class FileBrowse(
    self,
    button_text: str = "...",
    key: Union[str, int, None] = None,
    title: str = "",
    target_key: Union[str, None] = None,
    file_types: tuple[tuple[str, str]] = (("All Files", "*.*"),),
    multiple_files: bool = False,
    initial_folder: Union[str, None] = None,
    save_as: bool = False,
    enable_events: bool = False,  # enable changing events
    # other
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4206)

### Methods of FileBrowse

- [bind](#filebrowsebind)
- [bind_events](#filebrowsebind_events)
- [create](#filebrowsecreate)
- [disptach_event](#filebrowsedisptach_event)
- [get](#filebrowseget)
- [get_height](#filebrowseget_height)
- [get_name](#filebrowseget_name)
- [get_prev_element](#filebrowseget_prev_element)
- [get_width](#filebrowseget_width)
- [post_create](#filebrowsepost_create)
- [prepare_create](#filebrowseprepare_create)
- [set_cursor](#filebrowseset_cursor)
- [set_disabled](#filebrowseset_disabled)
- [set_text](#filebrowseset_text)
- [show_dialog](#filebrowseshow_dialog)
- [update](#filebrowseupdate)

### FileBrowse.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4206)

### FileBrowse.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4206)

### FileBrowse.create

Create a FileBrowse widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4206)

### FileBrowse.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4206)

### FileBrowse.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4206)

### FileBrowse.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4206)

### FileBrowse.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4206)

### FileBrowse.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4206)

### FileBrowse.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4206)

### FileBrowse.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4206)

### FileBrowse.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4206)

### FileBrowse.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4206)

### FileBrowse.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4206)

### FileBrowse.set_text

Set the text of the button.

```py
def set_text(self, text: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4206)

### FileBrowse.show_dialog

Show file dialog

```py
def show_dialog(self, *args) -> Union[Any, None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4206)

### FileBrowse.update

Update the widget.

```py
def update(self, text: Union[str, None] = None, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4206)

## FileSaveAs

FileSaveAs element. (alias of FileSaveAsBrowse)

```py
class FileSaveAs(
    self,
    button_text: str = "...",
    key: Union[str, None] = None,
    target_key: Union[str, None] = None,
    title: str = "",
    file_types: tuple[tuple[str, str]] = (("All Files", "*.*"),),
    enable_events: bool = False,  # enable changing events
    # other
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### Methods of FileSaveAs

- [bind](#filesaveasbind)
- [bind_events](#filesaveasbind_events)
- [create](#filesaveascreate)
- [disptach_event](#filesaveasdisptach_event)
- [get](#filesaveasget)
- [get_height](#filesaveasget_height)
- [get_name](#filesaveasget_name)
- [get_prev_element](#filesaveasget_prev_element)
- [get_width](#filesaveasget_width)
- [post_create](#filesaveaspost_create)
- [prepare_create](#filesaveasprepare_create)
- [set_cursor](#filesaveasset_cursor)
- [set_disabled](#filesaveasset_disabled)
- [set_text](#filesaveasset_text)
- [show_dialog](#filesaveasshow_dialog)
- [update](#filesaveasupdate)

### FileSaveAs.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAs.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAs.create

Create a FileBrowse widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAs.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAs.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAs.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAs.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAs.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAs.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAs.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAs.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAs.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAs.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAs.set_text

Set the text of the button.

```py
def set_text(self, text: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAs.show_dialog

Show file dialog

```py
def show_dialog(self, *args) -> Union[Any, None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAs.update

Update the widget.

```py
def update(self, text: Union[str, None] = None, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

## FileSaveAsBrowse

FileSaveAsBrowse element.

```py
class FileSaveAsBrowse(
    self,
    button_text: str = "...",
    key: Union[str, None] = None,
    target_key: Union[str, None] = None,
    title: str = "",
    file_types: tuple[tuple[str, str]] = (("All Files", "*.*"),),
    enable_events: bool = False,  # enable changing events
    # other
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### Methods of FileSaveAsBrowse

- [bind](#filesaveasbrowsebind)
- [bind_events](#filesaveasbrowsebind_events)
- [create](#filesaveasbrowsecreate)
- [disptach_event](#filesaveasbrowsedisptach_event)
- [get](#filesaveasbrowseget)
- [get_height](#filesaveasbrowseget_height)
- [get_name](#filesaveasbrowseget_name)
- [get_prev_element](#filesaveasbrowseget_prev_element)
- [get_width](#filesaveasbrowseget_width)
- [post_create](#filesaveasbrowsepost_create)
- [prepare_create](#filesaveasbrowseprepare_create)
- [set_cursor](#filesaveasbrowseset_cursor)
- [set_disabled](#filesaveasbrowseset_disabled)
- [set_text](#filesaveasbrowseset_text)
- [show_dialog](#filesaveasbrowseshow_dialog)
- [update](#filesaveasbrowseupdate)

### FileSaveAsBrowse.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAsBrowse.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAsBrowse.create

Create a FileBrowse widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAsBrowse.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAsBrowse.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAsBrowse.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAsBrowse.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAsBrowse.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAsBrowse.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAsBrowse.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAsBrowse.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAsBrowse.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAsBrowse.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAsBrowse.set_text

Set the text of the button.

```py
def set_text(self, text: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAsBrowse.show_dialog

Show file dialog

```py
def show_dialog(self, *args) -> Union[Any, None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

### FileSaveAsBrowse.update

Update the widget.

```py
def update(self, text: Union[str, None] = None, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4327)

## FilesBrowse

FilesBrowse element.

```py
class FilesBrowse(
    self,
    button_text: str = "...",
    key: Union[str, None] = None,
    target_key: Union[str, None] = None,
    title: str = "",
    file_types: tuple[tuple[str, str]] = (("All Files", "*.*"),),
    enable_events: bool = False,  # enable changing events
    # other
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4300)

### Methods of FilesBrowse

- [bind](#filesbrowsebind)
- [bind_events](#filesbrowsebind_events)
- [create](#filesbrowsecreate)
- [disptach_event](#filesbrowsedisptach_event)
- [get](#filesbrowseget)
- [get_height](#filesbrowseget_height)
- [get_name](#filesbrowseget_name)
- [get_prev_element](#filesbrowseget_prev_element)
- [get_width](#filesbrowseget_width)
- [post_create](#filesbrowsepost_create)
- [prepare_create](#filesbrowseprepare_create)
- [set_cursor](#filesbrowseset_cursor)
- [set_disabled](#filesbrowseset_disabled)
- [set_text](#filesbrowseset_text)
- [show_dialog](#filesbrowseshow_dialog)
- [update](#filesbrowseupdate)

### FilesBrowse.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4300)

### FilesBrowse.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4300)

### FilesBrowse.create

Create a FileBrowse widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4300)

### FilesBrowse.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4300)

### FilesBrowse.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4300)

### FilesBrowse.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4300)

### FilesBrowse.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4300)

### FilesBrowse.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4300)

### FilesBrowse.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4300)

### FilesBrowse.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4300)

### FilesBrowse.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4300)

### FilesBrowse.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4300)

### FilesBrowse.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4300)

### FilesBrowse.set_text

Set the text of the button.

```py
def set_text(self, text: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4300)

### FilesBrowse.show_dialog

Show file dialog

```py
def show_dialog(self, *args) -> Union[Any, None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4300)

### FilesBrowse.update

Update the widget.

```py
def update(self, text: Union[str, None] = None, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4300)

## FolderBrowse

FolderBrowse element.

```py
class FolderBrowse(
    self,
    button_text: str = "...",
    key: Union[str, None] = None,
    target_key: Union[str, None] = None,
    default_path: Union[str, None] = None,
    title: str = "",
    enable_events: bool = False,  # enable changing events
    # other
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4360)

### Methods of FolderBrowse

- [bind](#folderbrowsebind)
- [bind_events](#folderbrowsebind_events)
- [create](#folderbrowsecreate)
- [disptach_event](#folderbrowsedisptach_event)
- [get](#folderbrowseget)
- [get_height](#folderbrowseget_height)
- [get_name](#folderbrowseget_name)
- [get_prev_element](#folderbrowseget_prev_element)
- [get_width](#folderbrowseget_width)
- [post_create](#folderbrowsepost_create)
- [prepare_create](#folderbrowseprepare_create)
- [set_cursor](#folderbrowseset_cursor)
- [set_disabled](#folderbrowseset_disabled)
- [set_text](#folderbrowseset_text)
- [show_dialog](#folderbrowseshow_dialog)
- [update](#folderbrowseupdate)

### FolderBrowse.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4360)

### FolderBrowse.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4360)

### FolderBrowse.create

Create a FileBrowse widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4360)

### FolderBrowse.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4360)

### FolderBrowse.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4360)

### FolderBrowse.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4360)

### FolderBrowse.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4360)

### FolderBrowse.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4360)

### FolderBrowse.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4360)

### FolderBrowse.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4360)

### FolderBrowse.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4360)

### FolderBrowse.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4360)

### FolderBrowse.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4360)

### FolderBrowse.set_text

Set the text of the button.

```py
def set_text(self, text: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4360)

### FolderBrowse.show_dialog

Show file dialog

```py
def show_dialog(self, *args) -> Union[str, None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4360)

### FolderBrowse.update

Update the widget.

```py
def update(self, text: Union[str, None] = None, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4360)

## Frame

Frame element.

```py
class Frame(
    self,
    title: str,
    layout: LayoutType,
    key: str = "",
    size: Union[tuple[int, int], None] = None,
    relief: ReliefType = "groove",
    # text props
    font: Union[FontType, None] = None,  # font
    color: Union[str, None] = None,
    text_color: Union[str, None] = None,
    background_color: Union[str, None] = None,  # background_color
    # pack props
    label_outside: bool = False,
    vertical_alignment: TextVAlign = "top",  # vertical alignment
    text_align: Union[TextAlign, None] = "left",  # text align
    # pack props
    expand_x: bool = False,
    expand_y: bool = False,
    pad: Union[PadType, None] = None,
    # other
    metadata: Union[dict[str, Any], None] = None,
    use_ttk: bool = False,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1525)

### Methods of Frame

- [bind](#framebind)
- [bind_events](#framebind_events)
- [create](#framecreate)
- [disptach_event](#framedisptach_event)
- [get](#frameget)
- [get_height](#frameget_height)
- [get_name](#frameget_name)
- [get_prev_element](#frameget_prev_element)
- [get_width](#frameget_width)
- [post_create](#framepost_create)
- [prepare_create](#frameprepare_create)
- [set_cursor](#frameset_cursor)
- [set_disabled](#frameset_disabled)
- [update](#frameupdate)

### Frame.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1525)

### Frame.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1525)

### Frame.create

Create a Frame widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1525)

### Frame.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1525)

### Frame.get

Return Widget

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1525)

### Frame.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1525)

### Frame.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1525)

### Frame.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1525)

### Frame.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1525)

### Frame.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1525)

### Frame.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1525)

### Frame.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1525)

### Frame.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1525)

### Frame.update

Update the widget.

```py
def update(self, *args, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1525)

## Graph

Graph element.

```py
class Graph(
    self,
    key: Union[str, None] = None,
    background_color: Union[str, None] = None,
    size: tuple[int, int] = (300, 300),
    canvas_size: Union[tuple[int, int], None] = None,
    graph_bottom_left: Union[tuple[int, int], None] = None,
    graph_top_right: Union[tuple[int, int], None] = None,
    # other
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Methods of Graph

- [bind](#graphbind)
- [bind_events](#graphbind_events)
- [create](#graphcreate)
- [disptach_event](#graphdisptach_event)
- [draw_arc](#graphdraw_arc)
- [draw_circle](#graphdraw_circle)
- [draw_image](#graphdraw_image)
- [draw_line](#graphdraw_line)
- [draw_lines](#graphdraw_lines)
- [draw_oval](#graphdraw_oval)
- [draw_point](#graphdraw_point)
- [draw_polygon](#graphdraw_polygon)
- [draw_rectangle](#graphdraw_rectangle)
- [draw_text](#graphdraw_text)
- [erase](#grapherase)
- [get](#graphget)
- [get_height](#graphget_height)
- [get_name](#graphget_name)
- [get_prev_element](#graphget_prev_element)
- [get_width](#graphget_width)
- [post_create](#graphpost_create)
- [prepare_create](#graphprepare_create)
- [set_cursor](#graphset_cursor)
- [set_disabled](#graphset_disabled)
- [update](#graphupdate)

### Graph.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Graph.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Graph.create

Create Graph widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Graph.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Graph.draw_arc

Draw an arc.

```py
def draw_arc(
    self,
    top_left: PointType,
    bottom_right: PointType,
    extent: Union[int, None] = None,
    start_angle: Union[int, None] = None,
    style: Union[str, None] = None,
    arc_color: Union[str, None] = "black",
    line_width: int = 1,
    fill_color: Union[str, None] = None,
    ) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Graph.draw_circle

Draw a circle.

```py
def draw_circle(
    self,
    center_location: PointType,
    radius: Union[int, float],
    fill_color: Union[str, None] = None,
    line_color: Union[str, None] = "black",
    line_width: int = 1,
    ) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Graph.draw_image

Draw image

```py
def draw_image(
    self,
    filename: Union[str, None] = None,
    data: Union[bytes, None] = None,
    location: Union[PointType, None] = None,
    ) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Graph.draw_line

Draw a line.

```py
def draw_line(
    self,
    point_from: PointType,
    point_to: PointType,
    color: str = "black",
    width: int = 1,
    ) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Graph.draw_lines

Draw lines.

```py
def draw_lines(self, points: list[PointType], color="black", width=1) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Graph.draw_oval

Draw an oval.

```py
def draw_oval(
    self,
    top_left: PointType,
    bottom_right: PointType,
    fill_color: Union[str, None] = None,
    line_color: Union[str, None] = None,
    line_width: int = 1,
    ):
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Graph.draw_point

Draw a point.

```py
def draw_point(self, point: PointType, size: int = 2, color: str = "black") -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Graph.draw_polygon

Draw polygon

```py
def draw_polygon(
    self,
    points: list[PointType],
    fill_color: Union[str, None] = None,
    line_color: Union[str, None] = None,
    line_width: Union[int, None] = None,
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Graph.draw_rectangle

Draw rectangle

```py
def draw_rectangle(
    self,
    top_left: PointType,
    bottom_right: PointType,
    fill_color: Union[str, None] = None,
    line_color: Union[str, None] = None,
    line_width: Union[int, None] = None,
    ) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Graph.draw_text

Draw text

```py
def draw_text(
    self,
    text: str,
    location: PointType,
    color: Union[str, None] = "black",
    font: Union[FontType, None] = None,
    angle: Union[float, str, None] = 0,
    text_location: TextAlign = tk.CENTER,
    ) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Graph.erase

Delete all

```py
def erase(self) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Graph.get

Return Widget

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Graph.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Graph.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Graph.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Graph.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Graph.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Graph.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Graph.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Graph.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

### Graph.update

Update the widget.

```py
def update(self, *args, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3309)

## HSeparator

HSeparator element.

```py
class HSeparator(
    self,
    key: Union[str, None] = None,
    background_color: Union[str, None] = None,
    pad: PadType = 5,
    size: tuple[int, int] = (100, 5),
    # other
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3683)

### Methods of HSeparator

- [bind](#hseparatorbind)
- [bind_events](#hseparatorbind_events)
- [create](#hseparatorcreate)
- [disptach_event](#hseparatordisptach_event)
- [get](#hseparatorget)
- [get_height](#hseparatorget_height)
- [get_name](#hseparatorget_name)
- [get_prev_element](#hseparatorget_prev_element)
- [get_width](#hseparatorget_width)
- [post_create](#hseparatorpost_create)
- [prepare_create](#hseparatorprepare_create)
- [set_cursor](#hseparatorset_cursor)
- [set_disabled](#hseparatorset_disabled)
- [update](#hseparatorupdate)

### HSeparator.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3683)

### HSeparator.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3683)

### HSeparator.create

Create HSeparator widget.

```py
def create(self, win: Window, parent: tk.Widget) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3683)

### HSeparator.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3683)

### HSeparator.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3683)

### HSeparator.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3683)

### HSeparator.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3683)

### HSeparator.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3683)

### HSeparator.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3683)

### HSeparator.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3683)

### HSeparator.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3683)

### HSeparator.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3683)

### HSeparator.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3683)

### HSeparator.update

Update widget configuration.

```py
def update(self, *args, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3683)

## Image

Image element.

```py
class Image(
    self,
    source: Union[bytes, str, None] = None,  # image source
    filename=None,  # filen ame
    data: Union[bytes, PILImage.Image, None] = None,  # image data
    key: Union[str, None] = None,
    background_color: Union[
    tuple[int, int, int], str, None
    ] = None,  # background color (example) "red", "#FF0000"
    size: tuple[int, int] = (300, 300),
    resize_type: ImageResizeType = ImageResizeType.FIT_BOTH,
    enable_events: bool = False,
    # other
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3495)

### Methods of Image

- [bind](#imagebind)
- [bind_events](#imagebind_events)
- [create](#imagecreate)
- [disptach_event](#imagedisptach_event)
- [erase](#imageerase)
- [get](#imageget)
- [get_height](#imageget_height)
- [get_name](#imageget_name)
- [get_prev_element](#imageget_prev_element)
- [get_width](#imageget_width)
- [post_create](#imagepost_create)
- [prepare_create](#imageprepare_create)
- [screenshot](#imagescreenshot)
- [set_cursor](#imageset_cursor)
- [set_disabled](#imageset_disabled)
- [set_image](#imageset_image)
- [update](#imageupdate)

### Image.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3495)

### Image.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3495)

### Image.create

Create a Image widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3495)

### Image.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3495)

### Image.erase

Erase image

```py
def erase(self) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3495)

### Image.get

Return Widget

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3495)

### Image.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3495)

### Image.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3495)

### Image.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3495)

### Image.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3495)

### Image.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3495)

### Image.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3495)

### Image.screenshot

Take a screenshot

```py
def screenshot(self) -> PILImage.Image:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3495)

### Image.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3495)

### Image.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3495)

### Image.set_image

Set image to Image widget.

- ImageResizeType is NO_RESIZE/FIT_HEIGHT/FIT_WIDTH/FIT_BOTH/IGNORE_ASPECT_RATIO/CROP_TO_SQUARE

```py
def set_image(
    self,
    source: Union[bytes, str, None] = None,
    filename: Union[str, None] = None,
    data: Union[bytes, PILImage.Image, None] = None,
    size: Union[tuple[int, int], None] = None,
    resize_type: ImageResizeType = ImageResizeType.FIT_BOTH,
    background_color: Union[
    tuple[int, int, int], str, None
    ] = None,  # background color (example) "red", "#FF0000"
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3495)

### Image.update

Update the widget.

```py
def update(
    self,
    source: Union[bytes, str, None] = None,
    filename: Union[str, None] = None,
    data: Union[bytes, None] = None,
    size: Union[tuple[int, int], None] = None,
    resize_type: ImageResizeType = ImageResizeType.FIT_BOTH,
    background_color: Union[tuple[int, int, int], str, None] = None,
    **kw,
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3495)

## Input

Text input element.

```py
class Input(
    self,
    text: str = "",  # default text
    key: Union[str, None] = None,  # key
    default_text: Union[str, None] = None,  # same as text
    enable_events: bool = False,  # enabled events ([enter] or [change])
    enable_key_events: bool = False,  # enabled key events
    enable_focus_events: bool = False,  # enabled focus events
    readonly_background_color: Union[str, None] = "silver",
    password_char: Union[
    str, None
    ] = None,  # if you want to use it as a password input box, set "*"
    readonly: bool = False,  # read only box
    size: Union[
    tuple[int, int], None
    ] = None,  # set (width, height) character size (only width is supported)
    width: Union[int, None] = None,  # set width character size
    # text props
    text_align: Union[TextAlign, None] = "left",  # text align
    font: Union[FontType, None] = None,  # font
    color: Union[str, None] = None,  # text color
    text_color: Union[str, None] = None,  # same as color
    background_color: Union[str, None] = None,  # background color
    # pack props
    expand_x: bool = False,
    expand_y: bool = False,
    pad: Union[PadType, None] = None,
    # other
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Methods of Input

- [bind](#inputbind)
- [bind_events](#inputbind_events)
- [copy](#inputcopy)
- [copy_selected_text](#inputcopy_selected_text)
- [create](#inputcreate)
- [cut](#inputcut)
- [delete_selected](#inputdelete_selected)
- [disptach_event](#inputdisptach_event)
- [get](#inputget)
- [get_cursor_pos](#inputget_cursor_pos)
- [get_height](#inputget_height)
- [get_name](#inputget_name)
- [get_prev_element](#inputget_prev_element)
- [get_selected_text](#inputget_selected_text)
- [get_selection_length](#inputget_selection_length)
- [get_selection_pos](#inputget_selection_pos)
- [get_selection_start](#inputget_selection_start)
- [get_text](#inputget_text)
- [get_width](#inputget_width)
- [paste](#inputpaste)
- [post_create](#inputpost_create)
- [prepare_create](#inputprepare_create)
- [select_all](#inputselect_all)
- [set_cursor](#inputset_cursor)
- [set_cursor_pos](#inputset_cursor_pos)
- [set_disabled](#inputset_disabled)
- [set_readonly](#inputset_readonly)
- [set_selection_start](#inputset_selection_start)
- [set_text](#inputset_text)
- [update](#inputupdate)

### Input.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.copy

Copy to clipboard

```py
def copy(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.copy_selected_text

Copy selected text

```py
def copy_selected_text(self) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.create

Create Input widget

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.cut

Cut to clipboard

```py
def cut(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.delete_selected

Delete selected text

```py
def delete_selected(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.get_cursor_pos

Get cursor position

```py
def get_cursor_pos(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.get_selected_text

Get selected text

```py
def get_selected_text(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.get_selection_length

Get selection length

```py
def get_selection_length(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.get_selection_pos

Get selection positions

```py
def get_selection_pos(self) -> tuple[int, int]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.get_selection_start

Get selection start

```py
def get_selection_start(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.get_text

Get text

```py
def get_text(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.paste

Paste from clipboard

```py
def paste(self):
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.select_all

select_all

```py
def select_all(self) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.set_cursor_pos

Set cursor position

```py
def set_cursor_pos(self, index: int) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.set_readonly

Set readonly

```py
def set_readonly(self, readonly: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.set_selection_start

Set selection start and length

```py
def set_selection_start(self, sel_start: int, sel_length: int = 0) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.set_text

Set text

```py
def set_text(self, text: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Input.update

Update the widget.

```py
def update(
    self, text: Union[str, None] = None, readonly: Union[bool, None] = None, **kw
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

## InputText

InputText element. (alias of Input)

```py
class InputText(
    self,
    text: str = "",  # default text
    key: Union[str, None] = None,  # key
    default_text: Union[str, None] = None,  # same as text
    enable_events: bool = False,  # enabled events ([enter] or [change])
    enable_key_events: bool = False,  # enabled key events
    enable_focus_events: bool = False,  # enabled focus events
    readonly_background_color: Union[str, None] = "silver",
    password_char: Union[
    str, None
    ] = None,  # if you want to use it as a password input box, set "*"
    readonly: bool = False,  # read only box
    size: Union[
    tuple[int, int], None
    ] = None,  # set (width, height) character size (only width is supported)
    width: Union[int, None] = None,  # set width character size
    # text props
    text_align: Union[TextAlign, None] = "left",  # text align
    font: Union[FontType, None] = None,  # font
    color: Union[str, None] = None,  # text color
    text_color: Union[str, None] = None,  # same as color
    background_color: Union[str, None] = None,  # background color
    # pack props
    expand_x: bool = False,
    expand_y: bool = False,
    pad: Union[PadType, None] = None,
    # other
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### Methods of InputText

- [bind](#inputtextbind)
- [bind_events](#inputtextbind_events)
- [copy](#inputtextcopy)
- [copy_selected_text](#inputtextcopy_selected_text)
- [create](#inputtextcreate)
- [cut](#inputtextcut)
- [delete_selected](#inputtextdelete_selected)
- [disptach_event](#inputtextdisptach_event)
- [get](#inputtextget)
- [get_cursor_pos](#inputtextget_cursor_pos)
- [get_height](#inputtextget_height)
- [get_name](#inputtextget_name)
- [get_prev_element](#inputtextget_prev_element)
- [get_selected_text](#inputtextget_selected_text)
- [get_selection_length](#inputtextget_selection_length)
- [get_selection_pos](#inputtextget_selection_pos)
- [get_selection_start](#inputtextget_selection_start)
- [get_text](#inputtextget_text)
- [get_width](#inputtextget_width)
- [paste](#inputtextpaste)
- [post_create](#inputtextpost_create)
- [prepare_create](#inputtextprepare_create)
- [select_all](#inputtextselect_all)
- [set_cursor](#inputtextset_cursor)
- [set_cursor_pos](#inputtextset_cursor_pos)
- [set_disabled](#inputtextset_disabled)
- [set_readonly](#inputtextset_readonly)
- [set_selection_start](#inputtextset_selection_start)
- [set_text](#inputtextset_text)
- [update](#inputtextupdate)

### InputText.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.copy

Copy to clipboard

```py
def copy(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.copy_selected_text

Copy selected text

```py
def copy_selected_text(self) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.create

Create Input widget

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.cut

Cut to clipboard

```py
def cut(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.delete_selected

Delete selected text

```py
def delete_selected(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.get_cursor_pos

Get cursor position

```py
def get_cursor_pos(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.get_selected_text

Get selected text

```py
def get_selected_text(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.get_selection_length

Get selection length

```py
def get_selection_length(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.get_selection_pos

Get selection positions

```py
def get_selection_pos(self) -> tuple[int, int]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.get_selection_start

Get selection start

```py
def get_selection_start(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.get_text

Get text

```py
def get_text(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.paste

Paste from clipboard

```py
def paste(self):
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.select_all

select_all

```py
def select_all(self) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.set_cursor_pos

Set cursor position

```py
def set_cursor_pos(self, index: int) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.set_readonly

Set readonly

```py
def set_readonly(self, readonly: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.set_selection_start

Set selection start and length

```py
def set_selection_start(self, sel_start: int, sel_length: int = 0) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.set_text

Set text

```py
def set_text(self, text: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

### InputText.update

Update the widget.

```py
def update(
    self, text: Union[str, None] = None, readonly: Union[bool, None] = None, **kw
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2468)

## Label

Label element (alias of Text)

```py
class Label(
    self,
    text: str = "",
    key: Union[str, None] = None,
    enable_events: bool = False,  # enabled events (click)
    wrap_length: Union[int, None] = None,  # wrap length(unit=pixel)
    # text props
    text_align: Union[TextAlign, None] = "left",  # text align
    font: Union[FontType, None] = None,  # font
    color: Union[str, None] = None,  # text color
    text_color: Union[str, None] = None,  # same as color
    background_color: Union[str, None] = None,  # background color
    # pack props
    expand_x: bool = False,
    expand_y: bool = False,
    pad: Union[PadType, None] = None,
    # other
    metadata: Union[dict[str, Any], None] = None,  # user metadata
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Methods of Label

- [bind](#labelbind)
- [bind_events](#labelbind_events)
- [create](#labelcreate)
- [disptach_event](#labeldisptach_event)
- [get](#labelget)
- [get_height](#labelget_height)
- [get_name](#labelget_name)
- [get_prev_element](#labelget_prev_element)
- [get_text](#labelget_text)
- [get_width](#labelget_width)
- [post_create](#labelpost_create)
- [prepare_create](#labelprepare_create)
- [set_cursor](#labelset_cursor)
- [set_disabled](#labelset_disabled)
- [set_text](#labelset_text)
- [update](#labelupdate)

### Label.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Label.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Label.create

Create a Text widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Label.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Label.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Label.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Label.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Label.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Label.get_text

Get the text of the widget.

```py
def get_text(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Label.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Label.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Label.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Label.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Label.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Label.set_text

Set the text of the widget.

```py
def set_text(self, text: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Label.update

Update the widget.

```py
def update(self, text: Union[str, None] = None, *args, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

## ListBrowse

ListBrowse element.

```py
class ListBrowse(
    self,
    values: list[str] = [],
    message: str = "",
    button_text: str = "...",
    default_value: Union[str, None] = None,  # default value
    key: Union[str, None] = None,
    target_key: Union[str, None] = None,
    title: str = "",
    font: Union[FontType, None] = None,
    enable_events: bool = False,  # enable changing events
    # other
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4442)

### Methods of ListBrowse

- [bind](#listbrowsebind)
- [bind_events](#listbrowsebind_events)
- [create](#listbrowsecreate)
- [disptach_event](#listbrowsedisptach_event)
- [get](#listbrowseget)
- [get_height](#listbrowseget_height)
- [get_name](#listbrowseget_name)
- [get_prev_element](#listbrowseget_prev_element)
- [get_width](#listbrowseget_width)
- [post_create](#listbrowsepost_create)
- [prepare_create](#listbrowseprepare_create)
- [set_cursor](#listbrowseset_cursor)
- [set_disabled](#listbrowseset_disabled)
- [set_text](#listbrowseset_text)
- [show_dialog](#listbrowseshow_dialog)
- [update](#listbrowseupdate)

### ListBrowse.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4442)

### ListBrowse.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4442)

### ListBrowse.create

Create a FileBrowse widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4442)

### ListBrowse.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4442)

### ListBrowse.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4442)

### ListBrowse.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4442)

### ListBrowse.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4442)

### ListBrowse.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4442)

### ListBrowse.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4442)

### ListBrowse.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4442)

### ListBrowse.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4442)

### ListBrowse.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4442)

### ListBrowse.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4442)

### ListBrowse.set_text

Set the text of the button.

```py
def set_text(self, text: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4442)

### ListBrowse.show_dialog

Show Listbox dialog

```py
def show_dialog(self, *args) -> Union[str, None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4442)

### ListBrowse.update

Update the widget.

```py
def update(self, text: Union[str, None] = None, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4442)

## Listbox

Listbox element.

```py
class Listbox(
    self,
    values: list[str] = [],
    default_values: Union[list[str], None] = None,  # selected values
    default_value: Union[str, None] = None,  # a default value
    key: Union[str, None] = None,
    enable_events: bool = False,
    select_mode: ListboxSelectMode = LISTBOX_SELECT_MODE_BROWSE,
    # other
    metadata: Union[dict[str, Any], None] = None,
    items: Union[list[str], None] = None,  # same as values (alias values)
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3711)

### Methods of Listbox

- [bind](#listboxbind)
- [bind_events](#listboxbind_events)
- [create](#listboxcreate)
- [disptach_event](#listboxdisptach_event)
- [get](#listboxget)
- [get_cursor_index](#listboxget_cursor_index)
- [get_height](#listboxget_height)
- [get_name](#listboxget_name)
- [get_prev_element](#listboxget_prev_element)
- [get_selected_items](#listboxget_selected_items)
- [get_width](#listboxget_width)
- [post_create](#listboxpost_create)
- [prepare_create](#listboxprepare_create)
- [select_values](#listboxselect_values)
- [set_cursor](#listboxset_cursor)
- [set_cursor_index](#listboxset_cursor_index)
- [set_disabled](#listboxset_disabled)
- [set_values](#listboxset_values)
- [update](#listboxupdate)

### Listbox.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3711)

### Listbox.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3711)

### Listbox.create

[Listbox.create] create Listbox widget

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3711)

### Listbox.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3711)

### Listbox.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3711)

### Listbox.get_cursor_index

Get cursor index (return -1 if not selected)

```py
def get_cursor_index(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3711)

### Listbox.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3711)

### Listbox.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3711)

### Listbox.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3711)

### Listbox.get_selected_items

Get selected items

```py
def get_selected_items(self) -> list[str]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3711)

### Listbox.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3711)

### Listbox.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3711)

### Listbox.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3711)

### Listbox.select_values

Select values in Listbox.

**example**
```py
import TkEasyGUI as eg
with eg.Window("Sample", layout=[
    [eg.Listbox(["A", "B", "C"], key="a_list", select_mode="multiple")],
    [eg.Button("Select")],
]) as win:
    for event, values in win.event_iter():
        if event == "Select":
            win["a_list"].select_values(["A", "B"]) # select A and B
```

```py
def select_values(self, values: Union[list[str], None]) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3711)

### Listbox.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3711)

### Listbox.set_cursor_index

Set cursor index

```py
def set_cursor_index(self, index: int) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3711)

### Listbox.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3711)

### Listbox.set_values

Set values to list

```py
def set_values(self, values: list[str]) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3711)

### Listbox.update

Update the widget.

```py
def update(self, *args, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3711)

## Menu

Menu element.

**Example**
```
menu = eg.Menu([
    ["File", ["Open", "Save", "---","Exit"]],
    ["Edit", ["Copy", "Paste"]],
])
```
**Note**
- "!label" is disabled
- "label::-event_name-" is set event name
- "---" is separator

```py
class Menu(
    self,
    items: Union[list[list[Union[str, list[Any]]]], None] = None,
    menu_definition: Union[list[list[Union[str, list[Any]]]], None] = None,
    key: Union[str, None] = None,
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1998)

### Methods of Menu

- [bind](#menubind)
- [bind_events](#menubind_events)
- [create](#menucreate)
- [disptach_event](#menudisptach_event)
- [get](#menuget)
- [get_height](#menuget_height)
- [get_name](#menuget_name)
- [get_prev_element](#menuget_prev_element)
- [get_text](#menuget_text)
- [get_width](#menuget_width)
- [post_create](#menupost_create)
- [prepare_create](#menuprepare_create)
- [set_cursor](#menuset_cursor)
- [set_disabled](#menuset_disabled)
- [set_text](#menuset_text)
- [update](#menuupdate)

### Menu.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1998)

### Menu.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1998)

### Menu.create

Create a Text widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1998)

### Menu.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1998)

### Menu.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1998)

### Menu.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1998)

### Menu.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1998)

### Menu.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1998)

### Menu.get_text

Get the text of the widget.

```py
def get_text(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1998)

### Menu.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1998)

### Menu.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1998)

### Menu.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1998)

### Menu.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1998)

### Menu.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1998)

### Menu.set_text

Set the text of the widget.

```py
def set_text(self, text: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1998)

### Menu.update

Update the widget.

```py
def update(
    self,
    menu_definition: Union[list[list[Union[str, list[Any]]]], None] = None,
    *args,
    **kw,
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1998)

## Multiline

Multiline text input element.

```py
class Multiline(
    self,
    text: str = "",  # default text
    default_text: Union[str, None] = None,  # same as text
    key: Union[str, None] = None,  # key
    readonly: bool = False,
    enable_events: bool = False,
    enable_key_events: bool = False,
    enable_focus_events: bool = False,
    size: tuple[int, int] = (50, 10),  # element size (unit=character)
    # text props
    font: Union[FontType, None] = None,  # font
    color: Union[str, None] = None,  # text color
    text_color: Union[str, None] = None,  # same as color
    background_color: Union[str, None] = None,  # background color
    text_align: Union[TextAlign, None] = None,  # text align
    # pack props
    expand_x: bool = False,
    expand_y: bool = False,
    pad: Union[PadType, None] = None,
    # other
    autoscroll: bool = False,  # When autoscroll is set to True, it scrolls to the end with text changes.
    readonly_background_color: Union[str, None] = None,
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Methods of Multiline

- [bind](#multilinebind)
- [bind_events](#multilinebind_events)
- [copy](#multilinecopy)
- [create](#multilinecreate)
- [cut](#multilinecut)
- [disptach_event](#multilinedisptach_event)
- [get](#multilineget)
- [get_cursor_pos](#multilineget_cursor_pos)
- [get_height](#multilineget_height)
- [get_name](#multilineget_name)
- [get_prev_element](#multilineget_prev_element)
- [get_selected_text](#multilineget_selected_text)
- [get_selection_length](#multilineget_selection_length)
- [get_selection_pos](#multilineget_selection_pos)
- [get_selection_start](#multilineget_selection_start)
- [get_text](#multilineget_text)
- [get_width](#multilineget_width)
- [index_to_pos](#multilineindex_to_pos)
- [paste](#multilinepaste)
- [pos_to_index](#multilinepos_to_index)
- [post_create](#multilinepost_create)
- [prepare_create](#multilineprepare_create)
- [print](#multilineprint)
- [select_all](#multilineselect_all)
- [set_cursor](#multilineset_cursor)
- [set_cursor_pos](#multilineset_cursor_pos)
- [set_disabled](#multilineset_disabled)
- [set_readonly](#multilineset_readonly)
- [set_selection_pos](#multilineset_selection_pos)
- [set_selection_start](#multilineset_selection_start)
- [set_text](#multilineset_text)
- [update](#multilineupdate)

### Multiline.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.copy

Copy the selected text.

```py
def copy(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.create

Create a Multiline widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.cut

Cut the selected text.

```py
def cut(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.get_cursor_pos

Get Cursor position. liek `3.0` row=3, col=0

```py
def get_cursor_pos(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.get_selected_text

Get the selected text.

```py
def get_selected_text(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.get_selection_length

Get selection length

```py
def get_selection_length(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.get_selection_pos

Get selection position, returns (start_pos, end_pos).

```py
def get_selection_pos(self) -> tuple[str, str]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.get_selection_start

Get selection start

```py
def get_selection_start(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.get_text

Get the text of the widget.

```py
def get_text(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.index_to_pos

Convert index to postion.

```py
def index_to_pos(self, index: int) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.paste

Paste the text.

```py
def paste(self) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.pos_to_index

Convert position to index.

```py
def pos_to_index(self, pos: str) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.print

Print text.

```py
def print(
    self,
    text: str,
    text_color: Union[str, None] = None,
    background_color: Union[str, None] = None,
    end: str = "\n",
    autoscroll: bool = False,
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.select_all

Select all text

```py
def select_all(self) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.set_cursor_pos

Set cursor position. (like `3.0`, row=3, col=0)

```py
def set_cursor_pos(self, pos: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.set_readonly

Set readonly

```py
def set_readonly(self, readonly: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.set_selection_pos

Set selection position.

```py
def set_selection_pos(self, start_pos: str, end_pos: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.set_selection_start

Set selection start

```py
def set_selection_start(self, index: int, sel_length: int = 0) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.set_text

Set text

```py
def set_text(self, text: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Multiline.update

Update the widget.

```py
def update(
    self,
    text: Union[str, None] = None,
    readonly: Union[bool, None] = None,
    autoscroll: Union[
    bool, None
    ] = None,  # When autoscroll is set to True, it scrolls to the end with text changes.
    **kw,
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

## MultilineBrowse

MultilineBrowse element.

```py
class MultilineBrowse(
    self,
    message: str = "",
    key: Union[str, None] = None,
    button_text: str = "...",
    target_key: Union[str, None] = None,
    title: str = "",
    font: Union[FontType, None] = None,
    enable_events: bool = False,  # enable changing events
    # other
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4496)

### Methods of MultilineBrowse

- [bind](#multilinebrowsebind)
- [bind_events](#multilinebrowsebind_events)
- [create](#multilinebrowsecreate)
- [disptach_event](#multilinebrowsedisptach_event)
- [get](#multilinebrowseget)
- [get_height](#multilinebrowseget_height)
- [get_name](#multilinebrowseget_name)
- [get_prev_element](#multilinebrowseget_prev_element)
- [get_width](#multilinebrowseget_width)
- [post_create](#multilinebrowsepost_create)
- [prepare_create](#multilinebrowseprepare_create)
- [set_cursor](#multilinebrowseset_cursor)
- [set_disabled](#multilinebrowseset_disabled)
- [set_text](#multilinebrowseset_text)
- [show_dialog](#multilinebrowseshow_dialog)
- [update](#multilinebrowseupdate)

### MultilineBrowse.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4496)

### MultilineBrowse.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4496)

### MultilineBrowse.create

Create a FileBrowse widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4496)

### MultilineBrowse.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4496)

### MultilineBrowse.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4496)

### MultilineBrowse.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4496)

### MultilineBrowse.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4496)

### MultilineBrowse.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4496)

### MultilineBrowse.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4496)

### MultilineBrowse.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4496)

### MultilineBrowse.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4496)

### MultilineBrowse.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4496)

### MultilineBrowse.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4496)

### MultilineBrowse.set_text

Set the text of the button.

```py
def set_text(self, text: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4496)

### MultilineBrowse.show_dialog

Show Listbox dialog

```py
def show_dialog(self, *args) -> Union[str, None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4496)

### MultilineBrowse.update

Update the widget.

```py
def update(self, text: Union[str, None] = None, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L4496)

## Output

Output element. (alias of Multiline) TODO: implement

```py
class Output(
    self,
    text: str = "",  # default text
    default_text: Union[str, None] = None,  # same as text
    key: Union[str, None] = None,  # key
    readonly: bool = False,
    enable_events: bool = False,
    enable_key_events: bool = False,
    enable_focus_events: bool = False,
    size: tuple[int, int] = (50, 10),  # element size (unit=character)
    # text props
    font: Union[FontType, None] = None,  # font
    color: Union[str, None] = None,  # text color
    text_color: Union[str, None] = None,  # same as color
    background_color: Union[str, None] = None,  # background color
    text_align: Union[TextAlign, None] = None,  # text align
    # pack props
    expand_x: bool = False,
    expand_y: bool = False,
    pad: Union[PadType, None] = None,
    # other
    autoscroll: bool = False,  # When autoscroll is set to True, it scrolls to the end with text changes.
    readonly_background_color: Union[str, None] = None,
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Methods of Output

- [bind](#outputbind)
- [bind_events](#outputbind_events)
- [copy](#outputcopy)
- [create](#outputcreate)
- [cut](#outputcut)
- [disptach_event](#outputdisptach_event)
- [get](#outputget)
- [get_cursor_pos](#outputget_cursor_pos)
- [get_height](#outputget_height)
- [get_name](#outputget_name)
- [get_prev_element](#outputget_prev_element)
- [get_selected_text](#outputget_selected_text)
- [get_selection_length](#outputget_selection_length)
- [get_selection_pos](#outputget_selection_pos)
- [get_selection_start](#outputget_selection_start)
- [get_text](#outputget_text)
- [get_width](#outputget_width)
- [index_to_pos](#outputindex_to_pos)
- [paste](#outputpaste)
- [pos_to_index](#outputpos_to_index)
- [post_create](#outputpost_create)
- [prepare_create](#outputprepare_create)
- [print](#outputprint)
- [select_all](#outputselect_all)
- [set_cursor](#outputset_cursor)
- [set_cursor_pos](#outputset_cursor_pos)
- [set_disabled](#outputset_disabled)
- [set_readonly](#outputset_readonly)
- [set_selection_pos](#outputset_selection_pos)
- [set_selection_start](#outputset_selection_start)
- [set_text](#outputset_text)
- [update](#outputupdate)

### Output.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.copy

Copy the selected text.

```py
def copy(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.create

Create a Multiline widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.cut

Cut the selected text.

```py
def cut(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.get_cursor_pos

Get Cursor position. liek `3.0` row=3, col=0

```py
def get_cursor_pos(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.get_selected_text

Get the selected text.

```py
def get_selected_text(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.get_selection_length

Get selection length

```py
def get_selection_length(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.get_selection_pos

Get selection position, returns (start_pos, end_pos).

```py
def get_selection_pos(self) -> tuple[str, str]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.get_selection_start

Get selection start

```py
def get_selection_start(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.get_text

Get the text of the widget.

```py
def get_text(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.index_to_pos

Convert index to postion.

```py
def index_to_pos(self, index: int) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.paste

Paste the text.

```py
def paste(self) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.pos_to_index

Convert position to index.

```py
def pos_to_index(self, pos: str) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.print

Print text.

```py
def print(
    self,
    text: str,
    text_color: Union[str, None] = None,
    background_color: Union[str, None] = None,
    end: str = "\n",
    autoscroll: bool = False,
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.select_all

Select all text

```py
def select_all(self) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.set_cursor_pos

Set cursor position. (like `3.0`, row=3, col=0)

```py
def set_cursor_pos(self, pos: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.set_readonly

Set readonly

```py
def set_readonly(self, readonly: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.set_selection_pos

Set selection position.

```py
def set_selection_pos(self, start_pos: str, end_pos: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.set_selection_start

Set selection start

```py
def set_selection_start(self, index: int, sel_length: int = 0) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.set_text

Set text

```py
def set_text(self, text: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Output.update

Update the widget.

```py
def update(
    self,
    text: Union[str, None] = None,
    readonly: Union[bool, None] = None,
    autoscroll: Union[
    bool, None
    ] = None,  # When autoscroll is set to True, it scrolls to the end with text changes.
    **kw,
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

## Push

An element for achieving right alignment and center alignment.

**Example**
```py
win = sg.Window(
    title="Hello World",
    layout=[
        [sg.Text("=" * 50)],
        [sg.Push(), sg.Button("Hello World")],  # right alignment
        [sg.Push(), sg.Button("OK"), sg.Push()], # center alignment
    ])
while win.is_running():
    event, values = win.read()
```

```py
class Push(
    self, metadata: Union[dict[str, Any], None] = None, **kw  # user metadata
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1938)

### Methods of Push

- [bind](#pushbind)
- [bind_events](#pushbind_events)
- [create](#pushcreate)
- [disptach_event](#pushdisptach_event)
- [get](#pushget)
- [get_height](#pushget_height)
- [get_name](#pushget_name)
- [get_prev_element](#pushget_prev_element)
- [get_text](#pushget_text)
- [get_width](#pushget_width)
- [post_create](#pushpost_create)
- [prepare_create](#pushprepare_create)
- [set_cursor](#pushset_cursor)
- [set_disabled](#pushset_disabled)
- [set_text](#pushset_text)
- [update](#pushupdate)

### Push.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1938)

### Push.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1938)

### Push.create

Create a Text widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1938)

### Push.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1938)

### Push.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1938)

### Push.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1938)

### Push.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1938)

### Push.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1938)

### Push.get_text

Get the text of the widget.

```py
def get_text(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1938)

### Push.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1938)

### Push.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1938)

### Push.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1938)

### Push.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1938)

### Push.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1938)

### Push.set_text

Set the text of the widget.

```py
def set_text(self, text: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1938)

### Push.update

Update the widget.

```py
def update(self, text: Union[str, None] = None, *args, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1938)

## Radio

Checkbox element.

```py
class Radio(
    self,
    text: str = "",
    group_id: Union[int, str] = "group",
    default: bool = False,
    key: Union[str, None] = None,
    enable_events: bool = False,
    # other
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2363)

### Methods of Radio

- [bind](#radiobind)
- [bind_events](#radiobind_events)
- [create](#radiocreate)
- [disptach_event](#radiodisptach_event)
- [get](#radioget)
- [get_height](#radioget_height)
- [get_name](#radioget_name)
- [get_prev_element](#radioget_prev_element)
- [get_value](#radioget_value)
- [get_width](#radioget_width)
- [is_selected](#radiois_selected)
- [post_create](#radiopost_create)
- [prepare_create](#radioprepare_create)
- [select](#radioselect)
- [set_cursor](#radioset_cursor)
- [set_disabled](#radioset_disabled)
- [set_text](#radioset_text)
- [update](#radioupdate)

### Radio.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2363)

### Radio.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2363)

### Radio.create

Create a Radio widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2363)

### Radio.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2363)

### Radio.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2363)

### Radio.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2363)

### Radio.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2363)

### Radio.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2363)

### Radio.get_value

Returns the id of an element within a group.

```py
def get_value(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2363)

### Radio.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2363)

### Radio.is_selected

Check if the radio button is selected.

```py
def is_selected(self) -> bool:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2363)

### Radio.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2363)

### Radio.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2363)

### Radio.select

Select the radio button.

```py
def select(self) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2363)

### Radio.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2363)

### Radio.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2363)

### Radio.set_text

Set the text of the widget.

```py
def set_text(self, text: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2363)

### Radio.update

Update the widget.

```py
def update(self, text: Union[str, None] = None, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2363)

## Slider

Slider element.

```py
class Slider(
    self,
    range: tuple[float, float] = (1, 10),  # value range (from, to)
    default_value: Union[float, None] = None,  # default value
    resolution: float = 1,  # value resolution
    orientation: OrientationType = "horizontal",  # orientation (h|v|horizontal|vertical)
    tick_interval: Union[float, None] = None,  # tick marks interval on the scale
    enable_events: bool = False,  # enable changing events
    enable_changed_events: bool = False,  # enable changed event
    disable_number_display: bool = False,  # hide number display
    size: Union[
    tuple[int, int], None
    ] = None,  # size (unit: character) / horizontal: (bar_length, thumb_size), vertical: (thumb_size, bar_length)
    key: Union[str, None] = None,
    # other
    default: Union[float, None] = None,  # same as default_value
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3119)

### Methods of Slider

- [bind](#sliderbind)
- [bind_events](#sliderbind_events)
- [create](#slidercreate)
- [disptach_event](#sliderdisptach_event)
- [get](#sliderget)
- [get_height](#sliderget_height)
- [get_name](#sliderget_name)
- [get_prev_element](#sliderget_prev_element)
- [get_range](#sliderget_range)
- [get_width](#sliderget_width)
- [post_create](#sliderpost_create)
- [prepare_create](#sliderprepare_create)
- [set](#sliderset)
- [set_cursor](#sliderset_cursor)
- [set_disabled](#sliderset_disabled)
- [set_range](#sliderset_range)
- [update](#sliderupdate)

### Slider.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3119)

### Slider.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3119)

### Slider.create

Create the widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3119)

### Slider.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3119)

### Slider.get

Return slider value.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3119)

### Slider.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3119)

### Slider.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3119)

### Slider.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3119)

### Slider.get_range

Get the range of the slider.

```py
def get_range(self) -> tuple[float, float]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3119)

### Slider.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3119)

### Slider.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3119)

### Slider.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3119)

### Slider.set

Set value of Slider

```py
def set(self, value: float) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3119)

### Slider.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3119)

### Slider.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3119)

### Slider.set_range

Set the range of the slider.

```py
def set_range(self, from_: float, to: float) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3119)

### Slider.update

Update the widget.

```py
def update(
    self,
    value: Union[float, None] = None,
    range: Union[tuple[float, float], None] = None,
    disable_number_display: Union[bool, None] = None,
    **kw,
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3119)

## Submit

Subtmi element. (Alias of Button) : todo: add submit event

```py
class Submit(
    self,
    button_text: str = "Button",
    key: Union[str, None] = None,
    disabled: bool = False,
    size: Union[tuple[int, int], None] = None,
    tooltip: Union[str, None] = None,  # (TODO) tooltip
    button_color: Union[str, tuple[str, str], None] = None,
    width: Optional[int] = None,  # set characters width
    # text props
    text_align: Union[TextAlign, None] = "left",  # text align
    font: Union[FontType, None] = None,  # font
    color: Union[str, None] = None,  # text color
    text_color: Union[str, None] = None,  # same as color
    background_color: Optional[str] = None,  # background color (not supported on macOS)
    # pack props
    expand_x: bool = False,
    expand_y: bool = False,
    pad: Union[PadType, None] = None,
    # other
    use_ttk_buttons: bool = False,
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Methods of Submit

- [bind](#submitbind)
- [bind_events](#submitbind_events)
- [create](#submitcreate)
- [disptach_event](#submitdisptach_event)
- [get](#submitget)
- [get_height](#submitget_height)
- [get_name](#submitget_name)
- [get_prev_element](#submitget_prev_element)
- [get_text](#submitget_text)
- [get_width](#submitget_width)
- [post_create](#submitpost_create)
- [prepare_create](#submitprepare_create)
- [set_button_color](#submitset_button_color)
- [set_cursor](#submitset_cursor)
- [set_disabled](#submitset_disabled)
- [set_text](#submitset_text)
- [update](#submitupdate)

### Submit.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Submit.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Submit.create

Create a Button widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Submit.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Submit.get

Returns the text of the button..

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Submit.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Submit.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Submit.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Submit.get_text

Get the text of the button.

```py
def get_text(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Submit.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Submit.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Submit.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Submit.set_button_color

Set the button color.

```py
def set_button_color(
    self, button_color: Union[str, tuple[str, str]], update: bool = True
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Submit.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Submit.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Submit.set_text

Set the text of the button.

```py
def set_text(self, text: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

### Submit.update

Update the widget.

```py
def update(
    self,
    text: Union[str, None] = None,
    disabled: Union[bool, None] = None,
    button_color: Union[str, tuple[str, str], None] = None,
    **kw,
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2114)

## Tab

(experimental) Tab element - Tab is used together with TabGroup.

**Example:**
```py
import TkEasyGUI as sg
# Tab's Layout
tab1_layout = [[sg.Text("Tab1")], [sg.Input(key="input1")], [sg.Button("Read1")]]
tab2_layout = [[sg.Text("Tab2")], [sg.Input(key="input2")], [sg.Button("Read2")]]
# Main Layout
layout = [[
    sg.TabGroup([[
        sg.Tab("Tab title1", tab1_layout),
        sg.Tab("Tab title2", tab2_layout),
    ]])],
    [sg.Button("Quit")]]
# create window and event loop
with sg.Window("Tab Demo", layout) as window:
    for event, values in window:
        pass
```

```py
class Tab(
    self,
    title: str,
    layout: LayoutType,
    key: str = "",
    background_color: Union[str, None] = None,
    vertical_alignment: TextVAlign = "top",
    size: Union[tuple[int, int], None] = None,
    # text props
    text_align: Union[TextAlign, None] = "left",  # text align
    # pack props
    expand_x: bool = False,
    expand_y: bool = False,
    pad: Union[PadType, None] = None,
    # other
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1686)

### Methods of Tab

- [bind](#tabbind)
- [bind_events](#tabbind_events)
- [create](#tabcreate)
- [disptach_event](#tabdisptach_event)
- [get](#tabget)
- [get_height](#tabget_height)
- [get_name](#tabget_name)
- [get_prev_element](#tabget_prev_element)
- [get_width](#tabget_width)
- [post_create](#tabpost_create)
- [prepare_create](#tabprepare_create)
- [set_cursor](#tabset_cursor)
- [set_disabled](#tabset_disabled)
- [update](#tabupdate)

### Tab.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1686)

### Tab.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1686)

### Tab.create

Create a Tab element.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1686)

### Tab.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1686)

### Tab.get

Return Widget title

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1686)

### Tab.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1686)

### Tab.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1686)

### Tab.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1686)

### Tab.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1686)

### Tab.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1686)

### Tab.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1686)

### Tab.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1686)

### Tab.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1686)

### Tab.update

Update the widget.

```py
def update(self, *args, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1686)

## TabGroup

(experimental) TabGroup element - Specify the Tab element for the child elements.

**Example:**
```py
import TkEasyGUI as sg
# Tab's Layout
tab1_layout = [[sg.Text("Tab1")], [sg.Input(key="input1")], [sg.Button("Read1")]]
tab2_layout = [[sg.Text("Tab2")], [sg.Input(key="input2")], [sg.Button("Read2")]]
# Main Layout
layout = [[
    sg.TabGroup([[
        sg.Tab("Tab title1", tab1_layout),
        sg.Tab("Tab title2", tab2_layout),
    ]])],
    [sg.Button("Quit")]]
# create window and event loop
with sg.Window("Tab Demo", layout) as window:
    for event, values in window:
        pass
```

```py
class TabGroup(
    self,
    layout: Union[list[list[Tab]], list[Tab]],
    key: str = "",
    background_color: Union[str, None] = None,
    vertical_alignment: TextVAlign = "top",
    size: Union[tuple[int, int], None] = None,
    # text props
    text_align: Union[TextAlign, None] = "left",  # text align
    # pack props
    expand_x: bool = True,
    expand_y: bool = True,
    pad: Union[PadType, None] = None,
    # other
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1770)

### Methods of TabGroup

- [bind](#tabgroupbind)
- [bind_events](#tabgroupbind_events)
- [create](#tabgroupcreate)
- [disptach_event](#tabgroupdisptach_event)
- [get](#tabgroupget)
- [get_height](#tabgroupget_height)
- [get_name](#tabgroupget_name)
- [get_prev_element](#tabgroupget_prev_element)
- [get_width](#tabgroupget_width)
- [post_create](#tabgrouppost_create)
- [prepare_create](#tabgroupprepare_create)
- [set_cursor](#tabgroupset_cursor)
- [set_disabled](#tabgroupset_disabled)
- [update](#tabgroupupdate)

### TabGroup.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1770)

### TabGroup.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1770)

### TabGroup.create

Create a TabGroup element.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1770)

### TabGroup.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1770)

### TabGroup.get

Return Widget

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1770)

### TabGroup.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1770)

### TabGroup.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1770)

### TabGroup.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1770)

### TabGroup.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1770)

### TabGroup.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1770)

### TabGroup.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1770)

### TabGroup.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1770)

### TabGroup.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1770)

### TabGroup.update

Update the widget.

```py
def update(self, *args, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1770)

## Table

Table element.

```py
class Table(
    self,
    values: list[list[str]] = [],  # Specify the table values as 2D list.
    headings: list[str] = [],  # Specify the table header as a list.
    key: Union[str, None] = None,
    justification: TextAlign = "center",
    auto_size_columns: bool = True,
    max_col_width: int = 0,
    col_widths: Union[list[int], None] = None,
    enable_events: bool = False,
    event_returns_values: Union[
    bool, None
    ] = None,  # Returns the table value if set to True, otherwise returns the index.
    select_mode: str = "browse",
    max_columns: int = 20,  # This property cannot be changed later. It is advisable to set a larger value.
    vertical_scroll_only: bool = True,  # vertical scroll only
    # text props
    text_align: Union[TextAlign, None] = "left",  # text align
    font: Union[FontType, None] = None,  # font
    color: Union[str, None] = None,  # text color
    text_color: Union[str, None] = None,  # same as color
    background_color: Union[str, None] = None,  # background color
    # pack props
    expand_x: bool = False,
    expand_y: bool = False,
    pad: Union[PadType, None] = None,
    # other
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3934)

### Methods of Table

- [bind](#tablebind)
- [bind_events](#tablebind_events)
- [create](#tablecreate)
- [disptach_event](#tabledisptach_event)
- [get](#tableget)
- [get_height](#tableget_height)
- [get_name](#tableget_name)
- [get_prev_element](#tableget_prev_element)
- [get_width](#tableget_width)
- [load_from_file](#tableload_from_file)
- [post_create](#tablepost_create)
- [prepare_create](#tableprepare_create)
- [set_cursor](#tableset_cursor)
- [set_disabled](#tableset_disabled)
- [set_values](#tableset_values)
- [update](#tableupdate)

### Table.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3934)

### Table.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3934)

### Table.create

Create a Table widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3934)

### Table.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3934)

### Table.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3934)

### Table.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3934)

### Table.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3934)

### Table.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3934)

### Table.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3934)

### Table.load_from_file

Load data from a file.

```py
def load_from_file(
    self,
    filename: str,
    delimiter: str = ",",
    encoding: str = "UTF-8",
    use_header: bool = True,
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3934)

### Table.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3934)

### Table.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3934)

### Table.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3934)

### Table.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3934)

### Table.set_values

Set values to the table.

```py
def set_values(
    self, values: list[list[str]], headings: Union[list[str], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3934)

### Table.update

Update the widget.

```py
def update(self, *args, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L3934)

## Text

Text element.

```py
class Text(
    self,
    text: str = "",
    key: Union[str, None] = None,
    enable_events: bool = False,  # enabled events (click)
    wrap_length: Union[int, None] = None,  # wrap length(unit=pixel)
    # text props
    text_align: Union[TextAlign, None] = "left",  # text align
    font: Union[FontType, None] = None,  # font
    color: Union[str, None] = None,  # text color
    text_color: Union[str, None] = None,  # same as color
    background_color: Union[str, None] = None,  # background color
    # pack props
    expand_x: bool = False,
    expand_y: bool = False,
    pad: Union[PadType, None] = None,
    # other
    metadata: Union[dict[str, Any], None] = None,  # user metadata
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Methods of Text

- [bind](#textbind)
- [bind_events](#textbind_events)
- [create](#textcreate)
- [disptach_event](#textdisptach_event)
- [get](#textget)
- [get_height](#textget_height)
- [get_name](#textget_name)
- [get_prev_element](#textget_prev_element)
- [get_text](#textget_text)
- [get_width](#textget_width)
- [post_create](#textpost_create)
- [prepare_create](#textprepare_create)
- [set_cursor](#textset_cursor)
- [set_disabled](#textset_disabled)
- [set_text](#textset_text)
- [update](#textupdate)

### Text.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Text.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Text.create

Create a Text widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Text.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Text.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Text.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Text.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Text.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Text.get_text

Get the text of the widget.

```py
def get_text(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Text.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Text.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Text.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Text.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Text.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Text.set_text

Set the text of the widget.

```py
def set_text(self, text: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

### Text.update

Update the widget.

```py
def update(self, text: Union[str, None] = None, *args, **kw) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1842)

## Textarea

Textarea element. (alias of Multiline)

```py
class Textarea(
    self,
    text: str = "",  # default text
    default_text: Union[str, None] = None,  # same as text
    key: Union[str, None] = None,  # key
    readonly: bool = False,
    enable_events: bool = False,
    enable_key_events: bool = False,
    enable_focus_events: bool = False,
    size: tuple[int, int] = (50, 10),  # element size (unit=character)
    # text props
    font: Union[FontType, None] = None,  # font
    color: Union[str, None] = None,  # text color
    text_color: Union[str, None] = None,  # same as color
    background_color: Union[str, None] = None,  # background color
    text_align: Union[TextAlign, None] = None,  # text align
    # pack props
    expand_x: bool = False,
    expand_y: bool = False,
    pad: Union[PadType, None] = None,
    # other
    autoscroll: bool = False,  # When autoscroll is set to True, it scrolls to the end with text changes.
    readonly_background_color: Union[str, None] = None,
    metadata: Union[dict[str, Any], None] = None,
    **kw,
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Methods of Textarea

- [bind](#textareabind)
- [bind_events](#textareabind_events)
- [copy](#textareacopy)
- [create](#textareacreate)
- [cut](#textareacut)
- [disptach_event](#textareadisptach_event)
- [get](#textareaget)
- [get_cursor_pos](#textareaget_cursor_pos)
- [get_height](#textareaget_height)
- [get_name](#textareaget_name)
- [get_prev_element](#textareaget_prev_element)
- [get_selected_text](#textareaget_selected_text)
- [get_selection_length](#textareaget_selection_length)
- [get_selection_pos](#textareaget_selection_pos)
- [get_selection_start](#textareaget_selection_start)
- [get_text](#textareaget_text)
- [get_width](#textareaget_width)
- [index_to_pos](#textareaindex_to_pos)
- [paste](#textareapaste)
- [pos_to_index](#textareapos_to_index)
- [post_create](#textareapost_create)
- [prepare_create](#textareaprepare_create)
- [print](#textareaprint)
- [select_all](#textareaselect_all)
- [set_cursor](#textareaset_cursor)
- [set_cursor_pos](#textareaset_cursor_pos)
- [set_disabled](#textareaset_disabled)
- [set_readonly](#textareaset_readonly)
- [set_selection_pos](#textareaset_selection_pos)
- [set_selection_start](#textareaset_selection_start)
- [set_text](#textareaset_text)
- [update](#textareaupdate)

### Textarea.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
    self,
    event_name: str,
    handle_name: str,
    propagate: bool = True,
    event_mode: EventMode = "user",
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.bind_events

Bind user events.

@see [custom events](/docs/custom_events.md)
The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
@see [Window.read](#windowread)

```py
def bind_events(
    self, events: dict[str, str], event_mode: EventMode = "user"
    ) -> "Element":
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.copy

Copy the selected text.

```py
def copy(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.create

Create a Multiline widget.

```py
def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.cut

Cut the selected text.

```py
def cut(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.disptach_event

Dispatch event

```py
def disptach_event(
    self, values: Union[dict[Union[str, int], Any], None] = None
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.get

Get the value of the widget.

```py
def get(self) -> Any:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.get_cursor_pos

Get Cursor position. liek `3.0` row=3, col=0

```py
def get_cursor_pos(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.get_height

Get height of element.

```py
def get_height(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.get_name

Get key of element.

```py
def get_name(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.get_prev_element

Get the previous widget.

```py
def get_prev_element(
    self, target_key: Union[str, None] = None
    ) -> Union["Element", None]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.get_selected_text

Get the selected text.

```py
def get_selected_text(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.get_selection_length

Get selection length

```py
def get_selection_length(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.get_selection_pos

Get selection position, returns (start_pos, end_pos).

```py
def get_selection_pos(self) -> tuple[str, str]:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.get_selection_start

Get selection start

```py
def get_selection_start(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.get_text

Get the text of the widget.

```py
def get_text(self) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.get_width

Get width of element.

```py
def get_width(self) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.index_to_pos

Convert index to postion.

```py
def index_to_pos(self, index: int) -> str:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.paste

Paste the text.

```py
def paste(self) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.pos_to_index

Convert position to index.

```py
def pos_to_index(self, pos: str) -> int:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.post_create

Post create widget.

```py
def post_create(self, win: Window, parent: tk.Widget) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.prepare_create

Prepare to create a widget.

```py
def prepare_create(self, win: Window) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.print

Print text.

```py
def print(
    self,
    text: str,
    text_color: Union[str, None] = None,
    background_color: Union[str, None] = None,
    end: str = "\n",
    autoscroll: bool = False,
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.select_all

Select all text

```py
def select_all(self) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.set_cursor

Set the cursor.

```py
def set_cursor(self, cursor: CursorType) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.set_cursor_pos

Set cursor position. (like `3.0`, row=3, col=0)

```py
def set_cursor_pos(self, pos: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.set_disabled

Set disabled widgets state

```py
def set_disabled(self, disabled: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.set_readonly

Set readonly

```py
def set_readonly(self, readonly: bool) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.set_selection_pos

Set selection position.

```py
def set_selection_pos(self, start_pos: str, end_pos: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.set_selection_start

Set selection start

```py
def set_selection_start(self, index: int, sel_length: int = 0) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.set_text

Set text

```py
def set_text(self, text: str) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

### Textarea.update

Update the widget.

```py
def update(
    self,
    text: Union[str, None] = None,
    readonly: Union[bool, None] = None,
    autoscroll: Union[
    bool, None
    ] = None,  # When autoscroll is set to True, it scrolls to the end with text changes.
    **kw,
    ) -> None:
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L2760)

## TkEasyError

TkEasyError Exception class.

```py
class TkEasyError(self, message="TkEasyError"):
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L83)

### Methods of TkEasyError



### TkEasyError.add_note

Exception.add_note(note) --
    add a note to the exception

### TkEasyError.args

### TkEasyError.with_traceback

Exception.with_traceback(tb) --
    set self.__traceback__ to tb and return self.

## VPush

An element that inserts flexible space above or below to shift the layout to the center or bottom.

**Example**
```py
import TkEasyGUI as eg

layout = [
    [eg.VPush()],
    [eg.Push(), eg.Text("== Middle =="), eg.Push()],
    [eg.Push(), eg.Button("OK"), eg.Push()],
    [eg.VPush()],
]

window = eg.Window(title="VPush Test", layout=layout, size=(400, 350))
while window.is_alive():
    event, values = window.read(timeout=1000)
    if event == eg.WIN_CLOSED or event == "OK":
        break
```

```py
class VPush(
    self, metadata: Union[dict[str, Any], None] = None, **kw  # user metadata
    )
```

- [source](https://github.com/kujirahand/TkEasyGUI-python/blob/main/TkEasyGUI/widgets.py#L1968)

### Methods of VPush

- [bind](#vpushbind)
- [bind_events](#vpushbind_events)
- [create](#vpushcreate)
- [disptach_event](#vpushdisptach_event)
- [get](#vpushget)
- [get_height](#vpushget_height)
- [get_name](#vpushget_name)
- [get_prev_element](#vpushget_prev_element)
- [get_text](#vpushget_text)
- [get_width](#vpushget_width)
- [post_create](#vpushpost_create)
- [prepare_create](#vpushprepare_create)
- [set_cursor](#vpushset_cursor)
- [set_disabled](#vpushset_disabled)
- [set_text](#vpushset_text)
- [update](#vpushupdate)

### VPush.bind

Bind event. @see [Window.bind](#windowbind)

```py
def bind(
