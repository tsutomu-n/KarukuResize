# 01_bare_except修正

## 分かったこと
- Pythonのbare except（except:）は非推奨（PEP 760で禁止提案中）
- bare exceptはKeyboardInterruptやSystemExitまで捉えてしまう
- except Exceptionが適切な代替策

## 技術要素
- PEP 760: No More Bare Excepts
- 例外階層: BaseException > Exception > KeyboardInterrupt, SystemExit

## 決定事項
- gui_app.pyの385行目付近のbare exceptをexcept Exceptionに修正

## 未解決点
- なし

## 検証方法
- uv run python -m py_compileで構文チェック
- ruff checkでLint確認

## 関連ファイル
- src/karuku_resizer/gui_app.py（382-386行目）

## 変更差分
```diff
-        except:
+        except Exception:
```
