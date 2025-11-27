#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键转换脚本
自动查找最新的bin文件，执行完整转换流程：
bin -> 带词频 -> final / final_带词频
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 导入其他模块的函数
from sogou_export_with_freq import parse_sogou_bin_with_freq, export_with_freq
from filter_dict import filter_dict_with_freq, load_common_words_from_file


def find_latest_bin_file(data_dir):
    """查找data目录下最新的bin文件"""
    data_path = Path(data_dir)
    if not data_path.exists():
        return None
    
    bin_files = list(data_path.glob("*.bin"))
    if not bin_files:
        return None
    
    # 按修改时间排序，返回最新的
    latest = max(bin_files, key=lambda p: p.stat().st_mtime)
    return latest


def main():
    print("=" * 60)
    print("搜狗词库一键转换工具")
    print("=" * 60)
    print()
    
    # 获取脚本所在目录
    script_dir = Path(__file__).parent
    data_dir = script_dir / "data"
    data_dir.mkdir(exist_ok=True)
    
    # 查找最新的bin文件
    print("正在查找最新的bin文件...")
    bin_file = find_latest_bin_file(data_dir)
    
    if not bin_file:
        print("❌ 错误: 在data目录下未找到bin文件")
        print(f"请将搜狗词库备份文件(.bin)放到: {data_dir}")
        sys.exit(1)
    
    print(f"✅ 找到bin文件: {bin_file.name}")
    print(f"   文件路径: {bin_file}")
    print(f"   文件大小: {bin_file.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"   修改时间: {datetime.fromtimestamp(bin_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 步骤1: 导出带词频的词库
    # 基于bin文件名生成输出文件名
    base_name = bin_file.stem  # 不含扩展名的文件名
    output_with_freq = data_dir / f"{base_name}_带词频.txt"
    print(f"\n{'='*60}")
    print(f"步骤1: 导出带词频的词库")
    print(f"{'='*60}")
    print(f"输入文件: {bin_file}")
    print(f"输出文件: {output_with_freq.name}")
    print()
    
    try:
        # 解析bin文件
        words_with_freq = parse_sogou_bin_with_freq(str(bin_file))
        
        # 导出到文件
        line_count = export_with_freq(words_with_freq, str(output_with_freq))
        
        print(f"✅ 导出成功: {line_count:,} 个词条（带词频）")
        
        if words_with_freq:
            print(f"\n词频统计:")
            print(f"  最高词频: {words_with_freq[0][1]:,}")
            print(f"  最低词频: {words_with_freq[-1][1]:,}")
            print(f"  平均词频: {sum(f for _, f in words_with_freq) // len(words_with_freq):,}")
    except Exception as e:
        print(f"\n❌ 错误: 导出带词频词库时出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 步骤2: 过滤词库
    print(f"\n{'='*60}")
    print(f"步骤2: 过滤词库")
    print(f"{'='*60}")
    print(f"过滤规则: 词频>=10, 过滤单字、常用词、重复字符等")
    print()
    
    # 基于bin文件名生成最终输出文件名
    final_with_freq = data_dir / f"{base_name}_final_带词频.txt"
    final_file = data_dir / f"{base_name}_final.txt"
    
    try:
        # 准备过滤选项
        filter_options = {
            'min_freq': 10,
            'filter_single_char': True,
            'filter_common_words': True,
            'filter_repeated': True,
            'filter_interjection': True,
            'filter_numbers': True,
            'filter_punctuation': True,
            'filter_english': False,
        }
        
        # 加载常用词词典
        print("正在从外部词典加载常用词...")
        common_words_dict = load_common_words_from_file(None)
        
        # 执行过滤
        final_count, filtered_stats = filter_dict_with_freq(
            str(output_with_freq),
            str(final_with_freq),
            filter_options,
            common_words_dict
        )
        
        print(f"✅ 过滤成功: {final_count:,} 个词条")
        print(f"\n过滤统计:")
        for key, count in filtered_stats.items():
            if count > 0:
                print(f"  - {key}: {count:,}")
    except Exception as e:
        print(f"\n❌ 错误: 过滤词库时出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 显示最终结果
    print("\n" + "=" * 60)
    print("✅ 转换完成!")
    print("=" * 60)
    print()
    print("生成的文件:")
    print(f"  📄 {output_with_freq.name}")
    print(f"     - 完整词库（带词频）")
    print(f"     - {line_count:,} 个词条")
    print()
    
    if final_with_freq.exists():
        with open(final_with_freq, 'r', encoding='utf-8') as f:
            final_count = sum(1 for _ in f)
        print(f"  ⭐ {final_with_freq.name}")
        print(f"     - 最终版本（带词频）")
        print(f"     - {final_count:,} 个词条")
        print()
    
    if final_file.exists():
        with open(final_file, 'r', encoding='utf-8') as f:
            final_count = sum(1 for _ in f)
        print(f"  ⭐ {final_file.name}")
        print(f"     - 最终版本（不带词频）")
        print(f"     - {final_count:,} 个词条")
        print()
    
    print("文件位置:")
    print(f"  {data_dir}")
    print()
    print("使用建议:")
    print(f"  - 推荐使用: {final_with_freq.name if final_with_freq.exists() else 'N/A'}")
    print(f"  - 导入其他输入法: {final_file.name if final_file.exists() else 'N/A'}")


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

