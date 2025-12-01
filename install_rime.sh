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

# 步骤3: 检查 rime-lua 支持
install_rime_lua() {
    print_section "步骤 3/8: 检查 rime-lua 支持"
    
    # Rime (Squirrel) 通常已内置 Lua 支持
    # 如果使用 plum 安装，可以尝试：
    bash rime-install lua
    
    print_info "检查 Lua 支持..."
    
    # 检查 Squirrel 是否支持 Lua
    if [ -f "/Library/Input Methods/Squirrel.app/Contents/MacOS/Squirrel" ]; then
        print_success "Squirrel 已安装（通常已内置 Lua 支持）"
        print_info "如果 Lua 功能不工作，可能需要："
        print_info "  1. 更新 Squirrel 到最新版本"
        print_info "  2. 或从源码编译支持 Lua 的版本"
    else
        print_warning "Squirrel 未找到"
    fi
    
    # 尝试通过 plum 安装（如果可用）
    if [ -d "$PLUM_DIR" ]; then
        print_info "尝试通过 plum 安装 Lua 支持..."
        cd "$PLUM_DIR"
        if bash rime-install lua 2>/dev/null; then
            print_success "Lua 支持已安装"
        else
            print_warning "plum 安装失败（可能已内置或不需要）"
        fi
    fi
}

# 步骤4: 安装 rime-ice 方案
install_rime_ice() {
    print_section "步骤 4/7: 安装 rime-ice (雾凇拼音)"
    
    cd "$PLUM_DIR"
    
    print_info "正在安装 rime-ice..."
    bash rime-install iDvel/rime-ice:others/recipes/full
    
    print_success "rime-ice 安装完成"
}

# 步骤5: 配置主题
configure_theme() {
    print_section "步骤 5/7: 配置主题 (微信键盘风格)"
    
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

# 步骤6: 配置 iCloud 自动备份
configure_icloud_backup() {
    print_section "步骤 6/7: 配置 iCloud 自动备份"
    
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

# 步骤7: 安装 rime-emoji
install_rime_emoji() {
    print_section "步骤 7/8: 安装 rime-emoji"
    
    cd "$PLUM_DIR"
    
    print_info "正在安装 rime-emoji..."
    bash rime-install emoji
    
    print_info "配置 rime-ice 以支持 emoji..."
    bash rime-install emoji:customize:schema=rime_ice
    
    # 注意：Emoji 功能已在 rime_ice.schema.yaml 中配置（开关名：emoji）
    # 无需在 custom.yaml 中重复配置
    
    print_success "rime-emoji 安装完成"
}

# 步骤8: 启用学习新词功能
enable_user_dict_learning() {
    print_section "步骤 8/9: 启用学习新词功能"
    
    mkdir -p "$RIME_DIR"
    
    # 读取或创建 rime_ice.custom.yaml
    if [ -f "$RIME_DIR/rime_ice.custom.yaml" ]; then
        # 检查是否已配置学习功能
        if grep -q "translator/enable_user_dict" "$RIME_DIR/rime_ice.custom.yaml"; then
            print_success "学习新词功能已配置"
            return 0
        fi
        
        # 追加配置（使用正确的路径方式）
        cat >> "$RIME_DIR/rime_ice.custom.yaml" << 'EOF'

  # 启用学习新词功能（正确的配置方式）
  'translator/enable_user_dict': true        # 启用用户词典（自动学习新词）
  'translator/enable_sentence': true         # 启用句子输入（整句记忆）
  'translator/enable_completion': true       # 启用补全功能
  'translator/enable_encoder': true          # 启用编码器
EOF
    else
        # 创建新配置文件
        cat > "$RIME_DIR/rime_ice.custom.yaml" << 'EOF'
patch:
  # 启用学习新词功能（正确的配置方式）
  'translator/enable_user_dict': true        # 启用用户词典（自动学习新词）
  'translator/enable_sentence': true         # 启用句子输入（整句记忆）
  'translator/enable_completion': true       # 启用补全功能
  'translator/enable_encoder': true          # 启用编码器
EOF
    fi
    
    print_success "学习新词功能已启用"
    print_info "功能说明："
    echo "  - 用户词典：自动学习你输入的新词"
    echo "  - 句子输入：支持整句输入和记忆"
    echo "  - 补全功能：智能补全常用短语"
}

# 步骤9: 安装 AI 问答系统
install_ai_system() {
    print_section "步骤 9/10: 安装 AI 问答系统"
    
    # 获取脚本所在目录
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    RIME_AI_DIR="$SCRIPT_DIR/Rime"
    TARGET_RIME_DIR="$RIME_DIR"
    TARGET_LUA_DIR="$TARGET_RIME_DIR/lua"
    
    # 检查 Python3
    if ! command -v python3 &>/dev/null; then
        print_error "未检测到 python3，AI 功能需要 Python3"
        print_info "请先安装 Python3: brew install python3"
        return 1
    fi
    
    print_info "检查 Python 依赖..."
    # 检查并安装 requests
    if ! python3 -c "import requests" 2>/dev/null; then
        print_info "正在安装 requests..."
        if pip3 install --user requests 2>/dev/null; then
            print_success "requests 安装完成"
        else
            print_warning "requests 安装失败，请手动安装: pip3 install requests"
        fi
    else
        print_success "requests 已安装"
    fi
    
    # 创建目标目录
    mkdir -p "$TARGET_LUA_DIR"
    
    # 复制 Lua 脚本
    print_info "复制 Lua 脚本..."
    local lua_files=("ai_processor.lua" "ai_translator.lua" "ai_filter.lua")
    for file in "${lua_files[@]}"; do
        local source_file="$RIME_AI_DIR/lua/$file"
        local target_file="$TARGET_LUA_DIR/$file"
        
        if [ -f "$source_file" ]; then
            cp "$source_file" "$target_file"
            print_success "已复制 $file"
        else
            print_warning "$file 不存在，跳过"
        fi
    done
    
    # 复制 Python 脚本
    print_info "复制 Python 脚本..."
    local python_files=("ai_streamer.py")
    for file in "${python_files[@]}"; do
        local source_file="$RIME_AI_DIR/$file"
        local target_file="$TARGET_RIME_DIR/$file"
        
        if [ -f "$source_file" ]; then
            cp "$source_file" "$target_file"
            chmod +x "$target_file"
            print_success "已复制 $file"
        else
            print_warning "$file 不存在，跳过"
        fi
    done
    
    # 更新 rime_ice.custom.yaml 配置
    print_info "更新 rime_ice.custom.yaml 配置..."
    local schema_file="$TARGET_RIME_DIR/rime_ice.custom.yaml"
    
    # 检查文件是否存在
    if [ ! -f "$schema_file" ]; then
        print_info "创建 rime_ice.custom.yaml..."
        cat > "$schema_file" << 'EOF'
patch:
EOF
    fi
    
    # 检查是否已配置 AI 功能
    local has_ai_config=false
    if grep -q "ai_cmd:" "$schema_file" && \
       grep -q "lua_translator@\*ai_translator" "$schema_file" && \
       grep -q "lua_filter@\*ai_filter" "$schema_file"; then
        has_ai_config=true
    fi
    
    if [ "$has_ai_config" = false ]; then
        print_info "添加 AI 配置..."
        
        # 检查是否已有 recognizer 配置
        local has_recognizer=false
        if grep -q "^  recognizer:" "$schema_file"; then
            has_recognizer=true
        fi
        
        # 检查是否已有 engine/translators 配置
        local has_translators=false
        if grep -q "^  engine/translators" "$schema_file"; then
            has_translators=true
        fi
        
        # 检查是否已有 engine/filters 配置
        local has_filters=false
        if grep -q "^  engine/filters" "$schema_file"; then
            has_filters=true
        fi
        
        # 添加 recognizer（如果不存在）
        if [ "$has_recognizer" = false ] && ! grep -q "ai_cmd:" "$schema_file"; then
            cat >> "$schema_file" << 'EOF'

  # AI 聊天功能
  # 使用方式：@ai 输入 或 ai:输入
  recognizer:
    patterns:
      ai_cmd: "^(@ai|ai:|chat:|tr:)"  # 匹配 @ai 或 ai: 开头的输入
EOF
        elif [ "$has_recognizer" = true ] && ! grep -q "ai_cmd:" "$schema_file"; then
            # 已有 recognizer，但缺少 ai_cmd pattern
            print_warning "检测到已有 recognizer 配置，请手动添加 ai_cmd pattern"
        fi
        
        # 添加 translator（如果不存在）
        if [ "$has_translators" = false ] && ! grep -q "lua_translator@\*ai_translator" "$schema_file"; then
            cat >> "$schema_file" << 'EOF'
  engine/translators/+:
    - lua_translator@*ai_translator
EOF
        elif [ "$has_translators" = true ] && ! grep -q "lua_translator@\*ai_translator" "$schema_file"; then
            # 已有 translators，但缺少 ai_translator
            print_warning "检测到已有 engine/translators 配置，请手动添加 lua_translator@*ai_translator"
        fi
        
        # 添加 filter（如果不存在）
        if [ "$has_filters" = false ] && ! grep -q "lua_filter@\*ai_filter" "$schema_file"; then
            cat >> "$schema_file" << 'EOF'
  engine/filters/+:
    - lua_filter@*ai_filter
EOF
        elif [ "$has_filters" = true ] && ! grep -q "lua_filter@\*ai_filter" "$schema_file"; then
            # 已有 filters，但缺少 ai_filter
            print_warning "检测到已有 engine/filters 配置，请手动添加 lua_filter@*ai_filter"
        fi
        
        print_success "AI 配置已添加"
    else
        print_success "AI 配置已存在"
    fi
    
    # 检查是否需要添加 processor（如果配置中没有）
    if ! grep -q "lua_processor@\*ai_processor" "$schema_file"; then
        print_info "提示：processor 配置默认未启用，如需启用请手动添加"
    fi
    
    # 创建 .env 文件模板（如果不存在）
    local env_file="$TARGET_RIME_DIR/.env"
    if [ ! -f "$env_file" ]; then
        print_info "创建 .env 文件模板..."
        cat > "$env_file" << 'EOF'
# OpenAI API 配置
# 请设置你的 API Key 和 Base URL
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
EOF
        print_success ".env 文件模板已创建"
        print_warning "请编辑 $env_file 设置你的 API Key"
    else
        print_success ".env 文件已存在"
    fi
    
    print_success "AI 问答系统安装完成"
    print_info "下一步："
    echo "  1. 编辑 $env_file 设置 OPENAI_API_KEY 和 OPENAI_BASE_URL"
    echo "  2. 或设置环境变量: export OPENAI_API_KEY='sk-xxx'"
    echo "  3. 重新部署 Rime 配置"
    echo ""
    print_info "使用方法："
    echo "  - 输入 'ai:' 或 '@ai' 开始 AI 对话"
    echo "  - 输入 'chat:' 进行聊天"
    echo "  - 输入 'tr:' 进行翻译"
    echo "  - 输入问题后按回车键触发 AI"
}

# 步骤10: 导入词库到 Rime
import_dict_to_rime() {
    print_section "步骤 9/9: 导入词库到 Rime"
    
    # 获取脚本所在目录
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    DATA_DIR="$SCRIPT_DIR/data"
    
    # 查找最新的 final.txt 文件
    if [ ! -d "$DATA_DIR" ]; then
        print_warning "data 目录不存在，跳过词库导入"
        return 0
    fi
    
    # 优先查找带词频的版本
    DICT_FILE=$(find "$DATA_DIR" -maxdepth 1 -name "*_final_带词频.txt" -type f | sort -r | head -1)
    
    # 如果没找到带词频的版本，查找不带词频的版本
    if [ -z "$DICT_FILE" ]; then
        DICT_FILE=$(find "$DATA_DIR" -maxdepth 1 -name "*_final.txt" -type f ! -name "*_final_带词频.txt" | sort -r | head -1)
    fi
    
    if [ -z "$DICT_FILE" ]; then
        print_warning "未找到词库文件（*_final.txt 或 *_final_带词频.txt），跳过导入"
        print_info "提示: 运行 python3 convert.py 生成词库文件"
        return 0
    fi
    
    print_info "找到词库文件: $(basename "$DICT_FILE")"
    
    # 检查 pypinyin 是否安装
    if ! python3 -c "import pypinyin" 2>/dev/null; then
        print_warning "pypinyin 未安装，正在安装..."
        # 优先使用 requirements.txt
        if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
            if pip3 install -r "$SCRIPT_DIR/requirements.txt"; then
                print_success "依赖安装完成（从 requirements.txt）"
            else
                print_warning "从 requirements.txt 安装失败，尝试单独安装 pypinyin..."
                if pip3 install pypinyin; then
                    print_success "pypinyin 安装完成"
                else
                    print_error "pypinyin 安装失败，跳过词库导入"
                    print_info "手动安装: pip3 install -r requirements.txt"
                    print_info "或单独安装: pip3 install pypinyin"
                    print_info "手动导入: python3 import_to_rime.py \"$DICT_FILE\""
                    return 0
                fi
            fi
        else
            if pip3 install pypinyin; then
                print_success "pypinyin 安装完成"
            else
                print_error "pypinyin 安装失败，跳过词库导入"
                print_info "手动安装: pip3 install pypinyin"
                print_info "手动导入: python3 import_to_rime.py \"$DICT_FILE\""
                return 0
            fi
        fi
    fi
    
    # 导入词库
    print_info "正在导入词库到 Rime..."
    if python3 "$SCRIPT_DIR/import_to_rime.py" "$DICT_FILE"; then
        print_success "词库导入完成"
        
        # 重新部署 Rime 配置
        if [ -f "/Library/Input Methods/Squirrel.app/Contents/MacOS/Squirrel" ]; then
            print_info "正在重新部署 Rime 配置..."
            /Library/Input\ Methods/Squirrel.app/Contents/MacOS/Squirrel --reload
            print_success "Rime 配置已更新"
        fi
    else
        print_warning "词库导入失败，你可以稍后手动运行:"
        print_info "  python3 import_to_rime.py \"$DICT_FILE\""
    fi
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
    install_rime_lua
    install_rime_ice
    configure_theme
    configure_icloud_backup
    install_rime_emoji
    enable_user_dict_learning
    install_ai_system
    deploy_rime
    import_dict_to_rime
    
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
    echo "  - 学习新词：自动学习你输入的新词和短语"
    echo "  - AI 问答系统：支持 AI 对话、翻译等功能（需配置 API Key）"
    echo "  - 词库导入：自动导入搜狗词库（如果存在）"
    echo ""
    print_info "AI 功能配置："
    echo "  编辑 ~/Library/Rime/.env 设置 OPENAI_API_KEY"
    echo "  或设置环境变量: export OPENAI_API_KEY='sk-xxx'"
    echo ""
}

# 运行主函数
main "$@"

