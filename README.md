# 🚀 Rime AI 输入法 - 全球首款流式 AI 输入法

> **🎯 革命性创新**：在输入法中直接呼唤 AI，实现**实时流式 AI 对话**，无需切换应用，输入即得答案！

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![macOS](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](https://www.apple.com/macos/)

---

## ✨ 核心亮点

### 🌟 **全球首款流式 AI 输入法**

**在输入法中直接呼唤 AI，实时流式输出答案！**

- ✅ **无需切换应用** - 在任何应用中直接使用 AI
- ✅ **实时流式输出** - AI 回答逐字显示，无需等待
- ✅ **无缝集成** - 完全融入输入法体验，就像输入普通文字
- ✅ **多场景支持** - 聊天、翻译、代码生成，一键切换

**使用示例**：
```
输入: chat:台湾在哪里
回车: [AI 实时流式输出] 台湾位于东亚、东海与南海之间...
```

---

## 🎯 项目定位

本项目不仅仅是一个词库导入工具，而是一个**完整的智能输入法解决方案**：

```
词库导入 → Rime 安装 → 自动配置 → AI 集成 → 一键部署
```

### 📋 完整功能流程

1. **📥 词库导入** - 从搜狗输入法导出并优化个人词库
2. **⚙️ Rime 安装** - 一键安装 Rime 输入法（Squirrel for macOS）
3. **🎨 自动配置** - 自动配置主题、emoji、学习功能等
4. **🤖 AI 集成** - 集成流式 AI 对话功能（全球首创）
5. **🚀 一键部署** - 自动部署配置并打开项目主页

---

## 🚀 快速开始

### 系统要求

⚠️ **目前仅支持 macOS 系统**

本项目使用 Squirrel（Rime for macOS），因此需要 macOS 10.15 或更高版本。

### 准备词库文件（可选）

如果你想导入搜狗输入法的个人词库：

1. **从搜狗输入法导出词库**：
   - 打开搜狗输入法设置
   - 进入"词库"选项
   - 点击"导出/备份"
   - 选择导出为 `.bin` 格式

2. **将 .bin 文件放到项目目录**：
   ```bash
   # 将导出的 .bin 文件复制到 data/ 目录
   cp ~/Downloads/搜狗词库备份_*.bin data/
   ```

### 一键安装（推荐）

```bash
# 1. 克隆项目
git clone <repo-url>
cd sogou_export

# 2. 运行一键安装脚本
bash install_rime.sh
```

**安装脚本会自动完成**：
- ✅ 安装 Squirrel (Rime for macOS)
- ✅ 安装 rime-ice 拼音方案
- ✅ 配置微信键盘风格主题
- ✅ 启用 emoji 支持
- ✅ 配置 iCloud 自动备份
- ✅ **安装流式 AI 功能**（全球首创）
- ✅ 导入搜狗词库（如果存在）

### 配置 AI 功能

安装完成后，配置 OpenAI API：

```bash
# 编辑配置文件
nano ~/Library/Rime/.env
```

添加以下内容：
```env
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
```

或设置环境变量：
```bash
export OPENAI_API_KEY='sk-xxx'
export OPENAI_BASE_URL='https://api.openai.com/v1'
```

### 使用 AI 功能

1. **切换到 Rime 输入法**（Control+Space 或 Command+Space）
2. **输入 AI 命令**：
   - `ai:你的问题` - AI 对话
   - `chat:你的问题` - 聊天模式
   - `tr:要翻译的内容` - 翻译模式
3. **按回车键** - AI 会实时流式输出答案

---

## 🌟 核心功能

### 1. 🤖 流式 AI 对话（全球首创）

**在输入法中直接呼唤 AI，实时流式输出答案！**

- **实时流式输出** - AI 回答逐字显示，无需等待完整响应
- **无缝集成** - 完全融入输入法体验，就像输入普通文字
- **多场景支持**：
  - `ai:` - 通用 AI 对话
  - `chat:` - 聊天模式
  - `tr:` - 翻译模式

**技术实现**：
- Lua Processor 拦截按键事件
- Python 脚本调用 OpenAI API
- 实时流式输出到输入法候选框
- 支持完整的 Unicode 字符处理

### 2. 📥 搜狗词库导入

**智能导出和优化搜狗输入法个人词库**

- ✅ 纯 Python 实现，无需外部依赖
- ✅ 支持词频导出，保留使用频率信息
- ✅ 智能过滤：单字、常用词、重复字符等
- ✅ 一键转换，自动查找最新 bin 文件

**使用方法**：
```bash
# 将搜狗词库 .bin 文件放到 data/ 目录
# 运行一键转换
python3 convert.py
```

### 3. ⚙️ Rime 输入法一键安装

**完整的 Rime 输入法安装和配置方案**

- ✅ **Squirrel** - Rime for macOS
- ✅ **rime-ice** - 雾凇拼音方案（推荐）
- ✅ **微信键盘风格主题** - 浅色/深色自动切换
- ✅ **Emoji 支持** - 输入中文自动显示相关 emoji
- ✅ **iCloud 自动备份** - 用户数据自动同步
- ✅ **学习新词功能** - 自动学习用户输入习惯

### 4. 🎨 智能配置

**自动配置所有必要设置**

- 主题配置（微信键盘风格）
- 候选词翻页键（`,` 和 `.`）
- 以词定字快捷键（`[` 和 `]`）
- 用户词典学习功能
- AI 功能集成

---

## 📖 详细文档

### 词库导入

#### 准备词库文件

**步骤 1：从搜狗输入法导出词库**

1. 打开搜狗输入法设置
2. 进入"词库"选项
3. 点击"导出/备份"
4. 选择导出为 `.bin` 格式
5. 保存到本地（如 `~/Downloads/`）

**步骤 2：将 .bin 文件放到项目目录**

```bash
# 将导出的 .bin 文件复制到项目的 data/ 目录
cp ~/Downloads/搜狗词库备份_*.bin data/
```

**重要**：必须将 `.bin` 文件放在项目的 `data/` 目录下，`convert.py` 脚本会自动查找该目录下最新的 `.bin` 文件。

#### 一键转换

```bash
# 确保 .bin 文件已在 data/ 目录下
# 运行一键转换脚本
python3 convert.py
```

转换流程：
1. 自动查找 `data/` 目录下最新的 `.bin` 文件
2. 导出带词频的完整词库 → `data/{bin文件名}_带词频.txt`
3. 智能过滤词库
4. 生成最终版本：
   - `data/{bin文件名}_final_带词频.txt` - 带词频版本（推荐）
   - `data/{bin文件名}_final.txt` - 不带词频版本（可导入其他输入法）

#### 导入到 Rime

```bash
# 导入最终版本的词库
python3 import_to_rime.py data/词库_final.txt
```

### AI 功能使用

#### 基本用法

1. **切换到 Rime 输入法**
2. **输入 AI 命令**：
   ```
   ai:台湾在哪里
   ```
3. **按回车键** - AI 会实时流式输出答案

#### 支持的命令

- `ai:` - 通用 AI 对话
- `chat:` - 聊天模式
- `tr:` - 翻译模式

#### 技术细节

- **Processor** - 拦截按键事件，处理 AI 命令
- **Translator** - 生成 AI 提示候选词
- **Filter** - 过滤和优化候选词显示
- **Python 脚本** - 调用 OpenAI API，实现流式输出

详细技术文档请参考：
- [Rime Lua 执行逻辑](docs/rime_lua_execution_logic.md)
- [调试指南](docs/debugging.md)

---

## 📁 项目结构

```
sogou_export/
├── convert.py                    # 一键转换脚本（词库导出）
├── sogou_export_with_freq.py    # 导出带词频词库
├── filter_dict.py               # 词库过滤脚本
├── import_to_rime.py            # 导入词库到 Rime
├── install_rime.sh              # Rime 一键安装脚本（包含 AI 功能）
│
├── rime_config/                 # Rime 配置文件（项目文件）
│   ├── lua/                     # Lua 脚本
│   │   ├── ai_processor.lua    # AI 处理器（拦截按键）
│   │   ├── ai_translator.lua    # AI 翻译器（生成候选词）
│   │   └── ai_filter.lua        # AI 过滤器（优化显示）
│   ├── ai_streamer.py           # AI 流式输出脚本
│   ├── rime_ice.schema.yaml     # Rime 输入方案配置
│   └── rime_ice.custom.yaml     # Rime 自定义配置
├── Rime -> ~/Library/Rime       # 符号链接（指向用户 Rime 目录）
│
├── docs/                        # 文档目录
│   ├── rime_lua_execution_logic.md  # Lua 执行逻辑详解
│   └── debugging.md            # 调试指南
│
└── data/                        # 词库数据目录
    ├── *.bin                    # 原始词库备份文件（将搜狗导出的 .bin 文件放在这里）
    └── dicts/                   # 常用词词典
```

---

## 🔧 技术架构

### AI 功能架构

```
用户输入 (ai:问题)
    ↓
Lua Processor (拦截按键)
    ↓
Lua Translator (生成提示)
    ↓
用户按回车
    ↓
Lua Processor (触发 AI)
    ↓
Python ai_streamer.py (调用 OpenAI API)
    ↓
实时流式输出 (逐字显示)
    ↓
输入法候选框 (实时更新)
```

### 核心技术

- **Rime Lua** - 输入法脚本引擎
- **OpenAI API** - AI 对话接口
- **流式输出** - 实时逐字显示
- **Unicode 处理** - 完整支持多语言字符

---

## 🎯 使用场景

### 1. 快速查询

在任何应用中直接查询信息：
```
ai:Python 如何读取文件
```

### 2. 实时翻译

快速翻译文本：
```
tr:Hello, how are you?
```

### 3. 代码生成

生成代码片段：
```
ai:写一个 Python 函数计算斐波那契数列
```

### 4. 智能对话

与 AI 进行自然对话：
```
chat:今天天气怎么样？
```

---

## ⚙️ 系统要求

⚠️ **重要提示：目前仅支持 macOS 系统**

- **操作系统**: macOS 10.15+（必需）
- **Python**: 3.6+
- **依赖**:
  - `requests` - HTTP 请求库（AI 功能需要）
  - `pypinyin` - 拼音生成（词库导入需要）

**为什么只支持 macOS？**

本项目使用 Squirrel（Rime for macOS）作为输入法前端，因此只能在 macOS 系统上运行。Windows 和 Linux 用户可以使用对应的 Rime 前端（小狼毫、中州韻），但需要手动配置，本项目暂不提供自动安装脚本。

### 安装依赖

```bash
# 安装所有依赖
pip3 install -r requirements.txt

# 或单独安装
pip3 install requests pypinyin
```

---

## 🔍 常见问题

### AI 功能无法使用？

1. **检查 API Key**：
   ```bash
   # 检查配置文件
   cat ~/Library/Rime/.env
   ```

2. **检查 Python 依赖**：
   ```bash
   python3 -c "import requests"
   ```

3. **查看日志**：
   ```bash
   tail -f /tmp/rime_ai.log
   ```

详细故障排除请参考：[故障排除指南](docs/squirrel_troubleshooting.md)

### 词库导入问题？

请参考 [词库导入文档](#词库导入) 部分。

---

## 🎉 特色功能对比

| 功能 | 本项目 | 其他输入法 |
|------|--------|-----------|
| 流式 AI 对话 | ✅ **全球首创** | ❌ 不支持 |
| 词库导入 | ✅ 智能过滤 | ⚠️ 基础支持 |
| 一键安装 | ✅ 全自动 | ❌ 手动配置 |
| 主题配置 | ✅ 微信键盘风格 | ⚠️ 基础主题 |
| Emoji 支持 | ✅ 自动显示 | ⚠️ 需手动启用 |
| iCloud 备份 | ✅ 自动同步 | ❌ 不支持 |

---

## 📄 许可证

MIT License

---

## 🙏 致谢

### 核心技术

- [Rime](https://github.com/rime) - 中州韵输入法引擎
- [rime-ice](https://github.com/iDvel/rime-ice) - 雾凇拼音方案
- [librime-lua](https://github.com/hchunhui/librime-lua) - Lua 脚本支持

### 参考项目

- [rose](https://github.com/nopdan/rose) - 词库转换工具
- [深蓝词库转换](https://github.com/studyzy/imewlconverter) - 词库转换工具

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📮 反馈与支持

- **问题反馈**: [GitHub Issues](https://github.com/your-repo/issues)
- **功能建议**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **技术文档**: [docs/](docs/)

---

## 🌟 Star History

如果这个项目对你有帮助，请给一个 ⭐ Star！

---

**🎯 全球首款流式 AI 输入法，让 AI 触手可及！**
