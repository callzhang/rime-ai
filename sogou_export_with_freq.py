#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜狗拼音词库导出工具（带词频）
直接解析搜狗词库.bin文件并导出为带词频的文本格式
"""

import struct
import sys
import os
from pathlib import Path


def read_uint32(data, offset):
    """读取32位无符号整数（小端）"""
    if offset + 4 > len(data):
        return None
    return struct.unpack('<I', data[offset:offset+4])[0]


def read_uint16(data, offset):
    """读取16位无符号整数（小端）"""
    if offset + 2 > len(data):
        return None
    return struct.unpack('<H', data[offset:offset+2])[0]


def read_int16(data, offset):
    """读取16位有符号整数（小端）"""
    if offset + 2 > len(data):
        return None
    return struct.unpack('<h', data[offset:offset+2])[0]


def parse_sogou_bin_with_freq(bin_file):
    """
    解析搜狗词库.bin文件，提取词条和词频
    
    基于rose工具的解析逻辑
    """
    with open(bin_file, 'rb') as f:
        data = f.read()
    
    if len(data) < 20:
        raise ValueError("文件太小，不是有效的搜狗词库文件")
    
    # 检查文件头
    if data[:4] != b'SGPU':
        raise ValueError(f"无效的文件头: {data[:4]}, 期望: SGPU")
    
    # 解析文件头
    version = read_uint32(data, 4)
    date = read_uint32(data, 8)
    reserved = read_uint32(data, 12)
    file_size = read_uint32(data, 16)
    
    print(f"版本: {version}")
    print(f"日期: {date}")
    print(f"文件大小: {file_size:,} 字节")
    
    # 读取索引信息（从偏移20开始，跳过36字节）
    offset = 20
    idx_begin = read_uint32(data, offset + 36)
    idx_size = read_uint32(data, offset + 40)
    word_count = read_uint32(data, offset + 44)
    dict_begin = read_uint32(data, offset + 48)
    dict_total_size = read_uint32(data, offset + 52)
    dict_size = read_uint32(data, offset + 56)
    
    print(f"\n索引区:")
    print(f"  开始位置: 0x{idx_begin:x} ({idx_begin:,} 字节)")
    print(f"  大小: 0x{idx_size:x} ({idx_size:,} 字节)")
    print(f"  词条数量: {word_count:,}")
    
    print(f"\n数据区:")
    print(f"  开始位置: 0x{dict_begin:x} ({dict_begin:,} 字节)")
    print(f"  有效大小: 0x{dict_size:x} ({dict_size:,} 字节)")
    
    # 解析词条
    words_with_freq = []
    
    for i in range(word_count):
        # 读取索引
        idx_offset = idx_begin + 4 * i
        if idx_offset + 4 > len(data):
            break
        
        idx = read_uint32(data, idx_offset)
        entry_offset = idx + dict_begin
        
        if entry_offset + 20 > len(data):
            break
        
        # 读取词频（2字节有符号整数）
        freq = read_int16(data, entry_offset)
        if freq is None:
            break
        
        # 跳过未知字段
        entry_offset += 2  # freq
        entry_offset += 2  # unknown
        entry_offset += 5  # unknown 5 bytes
        
        # 读取拼音长度
        py_len_bytes = read_uint16(data, entry_offset)
        if py_len_bytes is None:
            break
        py_len = py_len_bytes // 2
        entry_offset += 2
        
        # 跳过拼音（我们不需要拼音，只需要词条和词频）
        entry_offset += py_len * 2
        
        # 读取词条大小
        word_size_bytes = read_uint16(data, entry_offset)
        if word_size_bytes is None:
            break
        entry_offset += 2
        
        word_size = read_uint16(data, entry_offset)
        if word_size is None:
            break
        entry_offset += 2
        
        # 读取词条
        if entry_offset + word_size > len(data):
            break
        
        word_bytes = data[entry_offset:entry_offset + word_size]
        try:
            word = word_bytes.decode('utf-16le')
            words_with_freq.append((word, freq))
        except UnicodeDecodeError:
            continue
    
    return words_with_freq


def export_with_freq(words_with_freq, output_file):
    """导出带词频的词库"""
    # 按词频降序排序
    words_with_freq.sort(key=lambda x: x[1], reverse=True)
    
    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        for word, freq in words_with_freq:
            f.write(f"{word}\t{freq}\n")
    
    return len(words_with_freq)


def main():
    if len(sys.argv) < 2:
        print("搜狗拼音词库导出工具（带词频）")
        print("=" * 50)
        print("用法: python3 sogou_export_with_freq.py <搜狗词库.bin文件> [输出文件.txt]")
        print("\n示例:")
        print("  python3 sogou_export_with_freq.py data/搜狗词库备份_2025_11_27.bin")
        print("  python3 sogou_export_with_freq.py data/搜狗词库备份_2025_11_27.bin output.txt")
        sys.exit(1)
    
    bin_file = sys.argv[1]
    if not os.path.exists(bin_file):
        print(f"错误: 文件不存在: {bin_file}")
        sys.exit(1)
    
    # 默认输出到data目录
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        # 基于bin文件名生成输出文件名
        bin_path = Path(bin_file)
        base_name = bin_path.stem  # 不含扩展名的文件名
        if bin_path.parent.name == "data":
            output_file = str(bin_path.parent / f"{base_name}_带词频.txt")
        else:
            output_file = str(data_dir / f"{base_name}_带词频.txt")
    
    print(f"输入文件: {bin_file}")
    print(f"输出文件: {output_file}")
    print("-" * 50)
    
    try:
        words_with_freq = parse_sogou_bin_with_freq(bin_file)
        count = export_with_freq(words_with_freq, output_file)
        
        print(f"\n✅ 成功! 共导出 {count:,} 个词条（带词频）")
        print(f"文件已保存到: {output_file}")
        
        if words_with_freq:
            print(f"\n词频统计:")
            print(f"  最高词频: {words_with_freq[0][1]:,}")
            print(f"  最低词频: {words_with_freq[-1][1]:,}")
            print(f"  平均词频: {sum(f for _, f in words_with_freq) // len(words_with_freq):,}")
            
            print(f"\n前10个高频词:")
            for i, (word, freq) in enumerate(words_with_freq[:10], 1):
                print(f"  {i}. {word}\t{freq:,}")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
