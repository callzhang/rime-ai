#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载常用词词典的辅助脚本
"""

import urllib.request
import sys
import os
from pathlib import Path

DICT_DIR = Path(__file__).parent / "data" / "dicts"
DICT_DIR.mkdir(parents=True, exist_ok=True)

# 一些可用的词典资源
DICT_SOURCES = {
    "chinese_common_words": {
        "name": "中文常用词",
        "description": "中文常用词汇列表",
        "urls": [
            # GitHub上的一些资源（需要用户确认）
            "https://raw.githubusercontent.com/fighting41love/funNLP/master/data/中文常用词/中文常用词.txt",
            "https://github.com/studyzy/imewlconverter/raw/master/参考/8万精准超小词库.txt",
        ],
    },
    "english_common_words": {
        "name": "英文常用词",
        "description": "英文常用词汇列表（10000词）",
        "urls": [
            "https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english.txt",
            "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt",
        ],
    },
}

def download_dict(url, output_file):
    """下载词典文件"""
    try:
        print(f"正在从 {url} 下载...")
        # 处理URL中的中文字符
        from urllib.parse import quote
        # 如果URL包含中文字符，需要编码
        if any(ord(c) > 127 for c in url):
            # 分离基础URL和路径部分
            parts = url.split('/', 3)
            if len(parts) >= 4:
                base_url = '/'.join(parts[:3])
                path = '/'.join(parts[3:])
                # 编码路径中的中文字符
                encoded_path = '/'.join(quote(part, safe='/') for part in path.split('/'))
                url = f"{base_url}/{encoded_path}"
        
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req) as response:
            with open(output_file, 'wb') as f:
                f.write(response.read())
        print(f"✅ 下载完成: {output_file}")
        return True
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return False

def list_sources():
    """列出可用的词典资源"""
    print("可用的词典资源：")
    print("=" * 60)
    for key, info in DICT_SOURCES.items():
        print(f"\n{info['name']} - {info['description']}")
        print("  可用URL:")
        for i, url in enumerate(info['urls'], 1):
            print(f"    {i}. {url}")

def main():
    if len(sys.argv) < 2:
        print("常用词词典下载工具")
        print("=" * 60)
        print(f"词典保存目录: {DICT_DIR}")
        print()
        list_sources()
        print()
        print("使用方法：")
        print("  python3 download_dict.py <URL> [文件名]")
        print("  python3 download_dict.py list  # 列出可用资源")
        print()
        print("示例：")
        print("  # 下载中文常用词")
        print("  python3 download_dict.py https://raw.githubusercontent.com/.../中文常用词.txt chinese_common.txt")
        print()
        print("  # 下载英文常用词")
        print("  python3 download_dict.py https://raw.githubusercontent.com/.../words.txt english_common.txt")
        return
    
    if sys.argv[1] == "list":
        list_sources()
        return
    
    url = sys.argv[1]
    filename = sys.argv[2] if len(sys.argv) > 2 else "common_words.txt"
    output_file = DICT_DIR / filename
    
    if download_dict(url, output_file):
        # 检查文件内容
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
            print(f"\n词典统计:")
            print(f"  总行数: {len(lines):,}")
            print(f"  有效词条: {len([l for l in lines if l])}")
            print(f"  前10个词条:")
            for word in lines[:10]:
                print(f"    {word}")
        except Exception as e:
            print(f"无法读取文件: {e}")

if __name__ == '__main__':
    main()
