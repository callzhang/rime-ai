#!/bin/bash
# -*- coding: utf-8 -*-
#
# Rime 输入法一键安装脚本
# 包含：Squirrel、plum、rime-ice、主题配置、iCloud备份、emoji支持
#

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 路径定义
RIME_DIR="$HOME/Library/Rime"
PLUM_DIR="$RIME_DIR/plum"
ICLOUD_BACKUP_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Backup/Rime"

# 打印函数
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_section() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# 检查命令是否存在
check_command() {
    if command -v "$1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# 步骤1: 安装 Squirrel (Rime for macOS)
install_squirrel() {
    print_section "步骤 1/6: 安装 Squirrel (Rime for macOS)"
    
    if check_command brew; then
        print_info "检测到 Homebrew，使用 brew 安装..."
        if brew list --cask squirrel &> /dev/null; then
            print_success "Squirrel 已安装"
        else
            print_info "正在安装 Squirrel..."
            brew install --cask squirrel
            print_success "Squirrel 安装完成"
        fi
    else
        print_warning "未检测到 Homebrew，请手动安装 Squirrel:"
        print_info "  1. 访问: https://github.com/rime/squirrel/releases"
        print_info "  2. 下载并安装 Squirrel.dmg"
        print_info "  3. 在系统设置中启用输入法"
        read -p "按回车键继续..." dummy
    fi
}

# 步骤2: 安装 plum 工具
install_plum() {
    print_section "步骤 2/6: 安装 plum 工具"
    
    if [ -d "$PLUM_DIR" ]; then
        print_success "plum 已存在，更新中..."
        cd "$PLUM_DIR"
        git pull origin master 2>/dev/null || print_warning "更新 plum 失败，继续使用现有版本"
    else
        print_info "正在克隆 plum..."
        mkdir -p "$RIME_DIR"
        cd "$RIME_DIR"
        git clone --depth 1 https://github.com/rime/plum.git
        print_success "plum 安装完成"
    fi
}

# 步骤3: 安装 rime-ice 方案
install_rime_ice() {
    print_section "步骤 3/6: 安装 rime-ice (雾凇拼音)"
    
    cd "$PLUM_DIR"
    
    print_info "正在安装 rime-ice..."
    bash rime-install iDvel/rime-ice:others/recipes/full
    
    print_success "rime-ice 安装完成"
}

# 步骤4: 配置主题
configure_theme() {
    print_section "步骤 4/6: 配置主题 (微信键盘风格)"
    
    mkdir -p "$RIME_DIR"
    
    cat > "$RIME_DIR/squirrel.custom.yaml" << 'EOF'
# squirrel.custom.yaml
patch:
  # 通知栏显示方式以及 ascii_mode 应用，与外观无关
  show_notifications_via_notification_center: true

  # 以下软件默认英文模式
  app_options:
    com.svend.uPic:
      ascii_mode: true

  # 如果想要修改皮肤，直接更改 color_scheme 的值即可
  style:
    color_scheme: wechat_light
    color_scheme_dark: wechat_dark

  preset_color_schemes:
    wechat_light:
      name: 微信键盘浅色
      horizontal: true                          # true横排，false竖排
      back_color: 0xFFFFFF                      # 候选条背景色
      border_height: 0                          # 窗口上下高度，大于圆角半径才生效
      border_width: 8                           # 窗口左右宽度，大于圆角半径才生效
      candidate_format: '%c %@ '                # 用 1/6 em 空格 U+2005 来控制编号 %c 和候选词 %@ 前后的空间
      comment_text_color: 0x999999              # 拼音等提示文字颜色
      corner_radius: 5                          # 窗口圆角
      hilited_corner_radius: 5                  # 高亮圆角
      font_face: PingFangSC                     # 候选词字体
      font_point: 16                            # 候选字大小
      hilited_candidate_back_color: 0x75B100    # 第一候选项背景色
      hilited_candidate_text_color: 0xFFFFFF    # 第一候选项文字颜色
      label_font_point: 12                      # 候选编号大小
      text_color: 0x424242                      # 拼音行文字颜色
      inline_preedit: true                      # 拼音位于： 候选框 false | 行内 true
    wechat_dark:
      name: 微信键盘深色
      horizontal: true                          # true横排，false竖排
      back_color: 0x2e2925                      # 候选条背景色
      border_height: 0                          # 窗口上下高度，大于圆角半径才生效
      border_width: 8                           # 窗口左右宽度，大于圆角半径才生效
      candidate_format: '%c %@ '                # 用 1/6 em 空格 U+2005 来控制编号 %c 和候选词 %@ 前后的空间
      comment_text_color: 0x999999              # 拼音等提示文字颜色
      corner_radius: 5                          # 窗口圆角
      hilited_corner_radius: 5                  # 高亮圆角
      font_face: PingFangSC                     # 候选词字体
      font_point: 16                            # 候选字大小
      hilited_candidate_back_color: 0x75B100    # 第一候选项背景色
      hilited_candidate_text_color: 0xFFFFFF    # 第一候选项文字颜色
      label_font_point: 12                      # 候选编号大小
      text_color: 0x424242                      # 拼音行文字颜色
      label_color: 0x999999                     # 预选栏编号颜色
      candidate_text_color: 0xe9e9ea            # 预选项文字颜色
      inline_preedit: true                      # 拼音位于： 候选框 false | 行内 true
EOF
    
    print_success "主题配置完成"
}

# 步骤5: 配置 iCloud 自动备份
configure_icloud_backup() {
    print_section "步骤 5/6: 配置 iCloud 自动备份"
    
    # 创建 iCloud 备份目录
    if [ ! -d "$ICLOUD_BACKUP_DIR" ]; then
        print_info "创建 iCloud 备份目录..."
        mkdir -p "$ICLOUD_BACKUP_DIR"
        print_success "iCloud 备份目录已创建"
    else
        print_success "iCloud 备份目录已存在"
    fi
    
    # 配置 installation.yaml
    if [ -f "$RIME_DIR/installation.yaml" ]; then
        # 检查是否已配置 sync_dir
        if grep -q "sync_dir:" "$RIME_DIR/installation.yaml"; then
            print_success "iCloud 备份已配置"
        else
            print_info "添加 sync_dir 配置..."
            echo "sync_dir: \"$ICLOUD_BACKUP_DIR\"" >> "$RIME_DIR/installation.yaml"
            print_success "iCloud 备份配置完成"
        fi
    else
        print_warning "installation.yaml 不存在，将在首次部署时自动创建"
    fi
}

# 步骤6: 安装 rime-emoji
install_rime_emoji() {
    print_section "步骤 6/6: 安装 rime-emoji"
    
    cd "$PLUM_DIR"
    
    print_info "正在安装 rime-emoji..."
    bash rime-install emoji
    
    print_info "配置 rime-ice 以支持 emoji..."
    bash rime-install emoji:customize:schema=rime_ice
    
    # 修复 rime_ice.custom.yaml 配置
    if [ -f "$RIME_DIR/rime_ice.custom.yaml" ]; then
        cat > "$RIME_DIR/rime_ice.custom.yaml" << 'EOF'
patch:
  # Emoji 建议功能
  switches/@next:
    name: emoji_suggestion
    reset: 1
    states: [ "🈚︎", "🈶️" ]
  'engine/filters/@before 0':
    simplifier@emoji_suggestion
  emoji_suggestion:
    opencc_config: emoji.json
    option_name: emoji_suggestion
    tips: none
    inherit_comment: false
EOF
        print_success "emoji 配置已更新"
    fi
    
    print_success "rime-emoji 安装完成"
}

# 部署 Rime 配置
deploy_rime() {
    print_section "部署 Rime 配置"
    
    if [ -f "/Library/Input Methods/Squirrel.app/Contents/MacOS/Squirrel" ]; then
        print_info "正在同步用户数据..."
        /Library/Input\ Methods/Squirrel.app/Contents/MacOS/Squirrel --sync
        
        print_info "正在重新部署配置..."
        /Library/Input\ Methods/Squirrel.app/Contents/MacOS/Squirrel --reload
        
        print_success "Rime 配置部署完成"
    else
        print_warning "Squirrel 未找到，请先安装 Squirrel"
    fi
}

# 主函数
main() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Rime 输入法一键安装脚本${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    
    # 检查 macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "此脚本仅支持 macOS"
        exit 1
    fi
    
    # 执行安装步骤
    install_squirrel
    install_plum
    install_rime_ice
    configure_theme
    configure_icloud_backup
    install_rime_emoji
    deploy_rime
    
    # 完成提示
    print_section "安装完成"
    print_success "Rime 输入法安装完成！"
    echo ""
    print_info "下一步操作："
    echo "  1. 打开 系统设置 > 键盘 > 输入法"
    echo "  2. 点击 + 添加输入法"
    echo "  3. 搜索并添加「鼠鬚管」或「Squirrel」"
    echo "  4. 使用 Control+Space 或 Command+Space 切换输入法"
    echo ""
    print_info "输入方案："
    echo "  - 雾凇拼音 (rime_ice) - 推荐使用"
    echo ""
    print_info "功能说明："
    echo "  - Emoji 支持：输入中文词汇时自动显示相关 emoji"
    echo "  - iCloud 备份：用户数据自动备份到 iCloud"
    echo "  - 微信键盘主题：浅色/深色主题自动切换"
    echo ""
}

# 运行主函数
main "$@"

