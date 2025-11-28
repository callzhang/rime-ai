#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将搜狗词库导入到Rime
将导出的词库文件转换为Rime的custom_phrase.txt格式
"""

import sys
from pathlib import Path

try:
    from pypinyin import lazy_pinyin, Style
    PYPINYIN_AVAILABLE = True
except ImportError:
    PYPINYIN_AVAILABLE = False


def word_to_pinyin(word):
    """将中文词转换为拼音"""
    # 使用lazy_pinyin，不带声调
    pinyin_list = lazy_pinyin(word, style=Style.NORMAL)
    return ''.join(pinyin_list)


def convert_to_rime_format(input_file, output_file=None, min_freq=1):
    """
    将搜狗词库转换为Rime格式
    
    Args:
        input_file: 输入文件（词条列表，每行一个词）
        output_file: 输出文件（默认为 ~/Library/Rime/custom_phrase.txt）
        min_freq: 最小词频（默认1）
    
    Raises:
        ImportError: 如果 pypinyin 未安装
        FileNotFoundError: 如果输入文件不存在
    """
    if not PYPINYIN_AVAILABLE:
        raise ImportError("需要安装 pypinyin 库。安装命令: pip3 install pypinyin")
    
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"文件不存在: {input_file}")
    
    # 默认输出到Rime目录
    if output_file is None:
        rime_dir = Path.home() / "Library" / "Rime"
        rime_dir.mkdir(exist_ok=True)
        output_file = rime_dir / "custom_phrase.txt"
    else:
        output_file = Path(output_file)
    
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    print("-" * 60)
    
    # 读取词条
    words = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            word = line.strip()
            if word:
                words.append(word)
    
    print(f"读取到 {len(words):,} 个词条")
    print("正在转换为Rime格式...")
    
    # 转换为Rime格式
    rime_entries = []
    for i, word in enumerate(words, 1):
        if i % 1000 == 0:
            print(f"  处理进度: {i:,}/{len(words):,}")
        
        # 生成拼音
        pinyin = word_to_pinyin(word)
        
        # Rime格式: 词条	拼音	词频
        # 使用默认词频100（可以根据需要调整）
        freq = 100
        rime_entries.append(f"{word}\t{pinyin}\t{freq}")
    
    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Rime 自定义词库\n")
        f.write("# 从搜狗词库导入\n")
        f.write("# 格式: 词条	拼音	词频\n\n")
        for entry in rime_entries:
            f.write(entry + "\n")
    
    print(f"\n✅ 转换完成!")
    print(f"共转换 {len(rime_entries):,} 个词条")
    print(f"文件已保存到: {output_file}")
    print(f"\n下一步:")
    print(f"  1. 部署Rime配置:")
    print(f"     /Library/Input\\ Methods/Squirrel.app/Contents/MacOS/Squirrel --reload")
    print(f"  2. 或者重启输入法")


def main():
    if not PYPINYIN_AVAILABLE:
        print("错误: 需要安装 pypinyin 库")
        print("安装命令: pip3 install pypinyin")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("搜狗词库导入Rime工具")
        print("=" * 60)
        print("用法: python3 import_to_rime.py <词库文件> [输出文件]")
        print("\n示例:")
        print("  python3 import_to_rime.py data/搜狗词库备份_2025_11_27_final.txt")
        print("  python3 import_to_rime.py data/词库_final.txt ~/Library/Rime/custom_phrase.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    convert_to_rime_format(input_file, output_file)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

