# 搜狗拼音词库导出工具

一个纯Python实现的搜狗拼音输入法个人词库导出工具，支持导出带词频的词库，并可过滤常用词。

## ✨ 特性

- ✅ **纯Python实现** - 无需外部依赖，直接解析bin文件
- ✅ **支持词频导出** - 导出词条和使用频率信息
- ✅ **智能过滤** - 自动过滤单字、常用词、重复字符等
- ✅ **一键转换** - 自动查找最新bin文件并完成整个转换流程
- ✅ **常用词词典** - 支持从外部词典文件加载常用词（中英文）
- ✅ **保持原始顺序** - 过滤后保持词条的原始顺序

## 🚀 快速开始

### 1. 准备词库文件

从搜狗输入法导出词库：
1. 打开搜狗输入法设置
2. 进入"词库"选项
3. 点击"导出/备份"
4. 选择导出为 `.bin` 格式
5. 将文件放到 `data/` 目录

### 2. 一键转换

```bash
# 自动查找data目录下最新的bin文件并完成整个转换流程
python3 convert.py
```

转换流程：
1. 自动查找 `data/` 目录下最新的 `.bin` 文件
2. 导出带词频的完整词库 → `{bin文件名}_带词频.txt`
3. 过滤词库 → `{bin文件名}_final_带词频.txt` 和 `{bin文件名}_final.txt`

### 3. 查看结果

转换完成后，在 `data/` 目录下会生成（基于bin文件名）：
- `{bin文件名}_带词频.txt` - 完整词库（带词频）
- `{bin文件名}_final_带词频.txt` - 最终版本（带词频）⭐ 推荐
- `{bin文件名}_final.txt` - 最终版本（不带词频）⭐ 可导入其他输入法

例如，如果bin文件是 `搜狗词库备份_2025_11_27.bin`，则生成：
- `搜狗词库备份_2025_11_27_带词频.txt`
- `搜狗词库备份_2025_11_27_final_带词频.txt`
- `搜狗词库备份_2025_11_27_final.txt`

## 📖 使用方法

### 一键转换（推荐）

```bash
python3 convert.py
```

### 手动转换

```bash
# 步骤1: 导出带词频的词库
python3 sogou_export_with_freq.py data/搜狗词库备份_2025_11_27.bin

# 步骤2: 过滤词库
python3 filter_dict.py data/词库_带词频.txt --min-freq=10
```

### 过滤选项

```bash
# 基本过滤（默认：词频>=10, 过滤单字、常用词等）
python3 filter_dict.py data/搜狗词库备份_2025_11_27_带词频.txt --min-freq=10

# 不过滤常用词
python3 filter_dict.py data/搜狗词库备份_2025_11_27_带词频.txt --min-freq=10 --no-common

# 不过滤单字
python3 filter_dict.py data/搜狗词库备份_2025_11_27_带词频.txt --min-freq=10 --no-single

# 指定自定义常用词词典
python3 filter_dict.py data/搜狗词库备份_2025_11_27_带词频.txt --dict=my_dict.txt --min-freq=10
```

## 📁 项目结构

```
sogou_export/
├── convert.py                    # 一键转换脚本（主入口）
├── sogou_export_with_freq.py    # 导出带词频词库
├── filter_dict.py               # 词库过滤脚本
├── download_dict.py             # 词典下载辅助工具（可选）
├── import_to_rime.py            # 导入词库到 Rime 输入法
├── install_rime.sh              # Rime 输入法一键安装脚本
├── README.md                    # 本文件
├── .gitignore                   # Git忽略文件
└── data/                        # 词库数据目录
    ├── *.bin                    # 原始词库备份文件（不提交）
    ├── {bin文件名}_带词频.txt   # 完整词库（带词频）
    ├── {bin文件名}_final_带词频.txt  # 最终版本（带词频）⭐
    ├── {bin文件名}_final.txt    # 最终版本（不带词频）⭐
    ├── README.md                # 数据目录说明
    └── dicts/                   # 常用词词典目录
        ├── common_words_merged.txt  # 合并的中英文词典
        ├── chinese_80000.txt         # 中文词库
        ├── english_10000.txt         # 英文常用词
        └── README.md                 # 词典说明
```

## 🔧 过滤规则

- ✅ **词频过滤** - 过滤词频小于阈值的词（默认10）
- ✅ **单字过滤** - 过滤单个汉字
- ✅ **常用词过滤** - 从外部词典文件读取常用词并过滤
- ✅ **重复字符** - 过滤如"啊啊啊"、"哈哈哈"等
- ✅ **语气词组合** - 过滤如"啊哈哈"、"哈啊哈"等
- ✅ **纯数字/标点** - 过滤纯数字和标点符号
- ⚙️ **可选** - 过滤纯英文词

## 📚 常用词词典

### 使用默认词典

脚本会自动从 `data/dicts/` 目录查找词典文件。如果目录中有词典文件，会自动使用。

### 下载词典

可以使用 `download_dict.py` 下载常用词词典：

```bash
# 列出可用资源
python3 download_dict.py list

# 下载英文常用词（10000词）
python3 download_dict.py https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english.txt english_10000.txt
```

### 词典文件格式

- 每行一个词条
- 支持 `#` 开头的注释行
- 支持制表符分隔的格式（只取第一列）
- 编码：UTF-8（也支持GBK、UTF-16等）

## 📊 输出格式

### 带词频格式

```
词条\t词频
```

示例：
```
我	24355
的	23374
是	17639
```

### 不带词频格式

```
词条
```

示例：
```
数据
这个
我们
```

## ⚙️ 依赖

### 核心依赖

- **Python 3.6+** - 无需外部依赖（纯Python实现）

### 可选依赖

- **pypinyin** - 用于导入词库到 Rime（生成拼音）
  
  使用 requirements.txt 安装（推荐）：
  ```bash
  pip3 install -r requirements.txt
  ```
  
  或单独安装：
  ```bash
  pip3 install pypinyin
  ```

- **Homebrew** - 用于安装 Rime 输入法（macOS）
  ```bash
  # 安装 Homebrew（如果未安装）
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  ```

## 🔍 工作原理

1. **解析bin文件** - `sogou_export_with_freq.py` 直接解析搜狗词库的二进制格式，提取词条和词频信息
2. **过滤词库** - `filter_dict.py` 根据规则过滤词库，去除无意义词条
3. **生成最终文件** - 自动生成带词频和不带词频两个版本

## ❓ 常见问题

### 为什么bin文件比txt文件大很多？

bin文件包含的信息比纯文本多：
- **词条文本**：词条本身
- **拼音信息**：每个词条的拼音编码
- **词频数据**：词条的使用频率
- **索引结构**：用于快速查找的数据结构
- **元数据**：文件头、版本信息等

因此2.2MB的bin文件导出为纯文本后只有约600KB。

### 为什么导出的词条数量与搜狗显示的不一致？

**常见情况**：搜狗显示25.5万条，但bin文件只有5.7万条

可能的原因：
1. **统计口径不同**：搜狗显示的25.5万可能是所有词库的总数（系统词库+个人词库），而bin文件只包含**个人词库**
2. **系统词库不包含**：bin备份文件通常只包含用户添加的个人词库，不包含搜狗自带的系统词库
3. **重复词条**：bin文件中可能有重复词条，导出时会去重

建议：
- 在搜狗输入法设置中查看"个人词库"的具体数量（不是总词库数）
- 使用带词频的版本可以查看详细的词条统计

### 如何获取常用词词典？

1. **使用下载脚本**：
   ```bash
   python3 download_dict.py list  # 查看可用资源
   ```

2. **手动下载**：
   - 从GitHub搜索 "chinese common words" 或 "中文常用词"
   - 下载词典文件到 `data/dicts/` 目录

3. **使用已有词典**：
   - 项目已包含一些常用词词典示例
   - 可以编辑 `data/dicts/` 目录下的词典文件

## 🎯 导入到 Rime 输入法

### 安装 Rime 输入法

项目提供了 Rime 输入法的一键安装脚本，包含：
- Squirrel (Rime for macOS)
- rime-ice (雾凇拼音) 方案
- 微信键盘风格主题
- iCloud 自动备份
- emoji 支持

```bash
# 运行安装脚本
bash install_rime.sh
```

安装完成后：
1. 打开 **系统设置 > 键盘 > 输入法**
2. 点击 **+** 添加输入法
3. 搜索并添加「鼠鬚管」或「Squirrel」
4. 使用 `Control+Space` 或 `Command+Space` 切换输入法

### 导入词库到 Rime

将过滤后的词库导入到 Rime：

```bash
# 导入最终版本的词库（不带词频）
python3 import_to_rime.py data/搜狗词库备份_2025_11_27_final.txt

# 或指定输出文件
python3 import_to_rime.py data/搜狗词库备份_2025_11_27_final.txt ~/Library/Rime/custom_phrase.txt
```

导入后需要重新部署 Rime 配置：

```bash
/Library/Input\ Methods/Squirrel.app/Contents/MacOS/Squirrel --reload
```

**注意**：导入脚本需要安装 `pypinyin` 库：

```bash
pip3 install pypinyin
```

## 📝 示例输出

```bash
$ python3 convert.py

============================================================
搜狗词库一键转换工具
============================================================

正在查找最新的bin文件...
✅ 找到bin文件: 搜狗词库备份_2025_11_27.bin
   文件大小: 2.22 MB
   修改时间: 2025-11-27 15:00:24

============================================================
步骤1: 导出带词频的词库
============================================================
✅ 导出成功: 57,625 个词条（带词频）

词频统计:
  最高词频: 24,355
  最低词频: -16,797
  平均词频: 25

============================================================
步骤2: 过滤词库
============================================================
正在从外部词典加载常用词...
已加载总计 441,373 个常用词
✅ 过滤成功: 3,972 个词条

过滤统计:
  - low_freq: 46,500
  - single_char: 831
  - common_words: 6,091

============================================================
✅ 转换完成!
============================================================

生成的文件:
  📄 词库_带词频.txt
     - 完整词库（带词频）
     - 57,625 个词条

  ⭐ 词库_final_带词频.txt
     - 最终版本（带词频）
     - 3,972 个词条

  ⭐ 词库_final.txt
     - 最终版本（不带词频）
     - 3,972 个词条
```

## 📄 许可证

MIT License

## 🙏 致谢

本工具的bin文件解析逻辑参考了以下项目：
- [rose](https://github.com/nopdan/rose) - 专业的词库转换工具
- [深蓝词库转换](https://github.com/studyzy/imewlconverter) - 另一个优秀的词库转换工具

Rime 输入法相关：
- [Rime](https://github.com/rime) - 中州韵输入法引擎
- [rime-ice](https://github.com/iDvel/rime-ice) - 雾凇拼音方案
- [rime-emoji](https://github.com/rime/rime-emoji) - Emoji 输入支持

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📮 反馈

如有问题或建议，请提交Issue。
