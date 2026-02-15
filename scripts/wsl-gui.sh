#!/bin/bash
# WSL2でKarukuResize GUIを起動するスクリプト

# 色付き出力用の設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}KarukuResize WSL2 起動スクリプト${NC}"
echo "================================"

# Display設定
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
export LIBGL_ALWAYS_INDIRECT=1

# GUI/CLIコマンドを解決（新コマンドを優先）
GUI_CMD=""
CLI_CMD=""
if command -v karuku-resizer &> /dev/null; then
    GUI_CMD="karuku-resizer"
elif command -v karukuresize-gui &> /dev/null; then
    GUI_CMD="karukuresize-gui"
elif command -v uv &> /dev/null; then
    GUI_CMD="uv run karuku-resizer"
fi

if command -v karukuresize-cli &> /dev/null; then
    CLI_CMD="karukuresize-cli"
elif command -v uv &> /dev/null; then
    CLI_CMD="uv run karukuresize-cli"
fi

if [[ -z "$GUI_CMD" ]]; then
    echo -e "${RED}エラー: GUI起動コマンドが見つかりません${NC}"
    echo ""
    echo "プロジェクトルートで次を実行してください："
    echo "  uv sync --group dev"
    echo "  uv run karuku-resizer"
    exit 1
fi

# X11サーバーの接続テスト
X_SERVER_IP=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')
echo -e "X11サーバーをチェック中... (${X_SERVER_IP}:0)"

if ! timeout 2 nc -z "$X_SERVER_IP" 6000 2>/dev/null; then
    echo -e "${YELLOW}警告: X11サーバーが検出されません${NC}"
    echo ""
    echo "解決方法："
    echo "1. Windows側でVcXsrvを起動してください"
    echo "   - XLaunchを実行"
    echo "   - 'Disable access control'にチェック"
    echo ""
    echo "2. またはCLI版を使用してください："
    if [[ -n "$CLI_CMD" ]]; then
        echo -e "   ${GREEN}${CLI_CMD} -s input -d output -w 1280 -q 85${NC}"
    else
        echo -e "   ${GREEN}uv run karukuresize-cli -s input -d output -w 1280 -q 85${NC}"
    fi
    echo ""
    echo -n "CLI版の使い方を表示しますか？ [Y/n]: "
    read -r response

    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]] || [[ -z "$response" ]]; then
        echo ""
        echo -e "${GREEN}=== CLI版の使い方 ===${NC}"
        echo ""
        echo "基本的な使い方:"
        if [[ -n "$CLI_CMD" ]]; then
            echo "  ${CLI_CMD} -s input -d output -w 1280 -q 85"
        else
            echo "  uv run karukuresize-cli -s input -d output -w 1280 -q 85"
        fi
        echo ""
        echo "便利なオプション:"
        echo "  -w, --width    : リサイズ後の幅（デフォルト: 1280）"
        echo "  -q, --quality  : JPEG品質（1-100、デフォルト: 85）"
        echo "  --dry-run      : 実際に保存せずシミュレート"
        echo "  --json         : 実行結果サマリをJSON出力"
        echo ""
        echo "使用例:"
        echo "  # Web用に最適化"
        if [[ -n "$CLI_CMD" ]]; then
            echo "  ${CLI_CMD} -s photos -d web_photos -w 1280 -q 85"
        else
            echo "  uv run karukuresize-cli -s photos -d web_photos -w 1280 -q 85"
        fi
        echo ""
        echo "  # サムネイル作成"
        if [[ -n "$CLI_CMD" ]]; then
            echo "  ${CLI_CMD} -s photos -d thumbnails -w 300 -q 80"
        else
            echo "  uv run karukuresize-cli -s photos -d thumbnails -w 300 -q 80"
        fi
        echo ""
        echo "  # 高品質で保存"
        if [[ -n "$CLI_CMD" ]]; then
            echo "  ${CLI_CMD} -s photos -d hq_photos -w 1920 -q 95"
        else
            echo "  uv run karukuresize-cli -s photos -d hq_photos -w 1920 -q 95"
        fi
    fi
    exit 0
fi

# GUIを起動
echo -e "${GREEN}X11サーバーが検出されました。GUIを起動します...${NC}"
echo ""

# エラーをキャッチして、失敗した場合はCLI版を提案
if ! eval "$GUI_CMD" 2>/tmp/karuku_gui_error.log; then
    echo -e "${RED}GUIの起動に失敗しました${NC}"
    echo ""
    echo "エラー詳細:"
    head -5 /tmp/karuku_gui_error.log
    echo ""
    echo -e "${YELLOW}代替案: CLI版を使用してください${NC}"
    if [[ -n "$CLI_CMD" ]]; then
        echo -e "  ${GREEN}${CLI_CMD} -s input -d output -w 1280 -q 85${NC}"
    else
        echo -e "  ${GREEN}uv run karukuresize-cli -s input -d output -w 1280 -q 85${NC}"
    fi
    exit 1
fi
