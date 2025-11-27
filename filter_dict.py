#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
词库过滤工具
根据词频、单字、常用词汇等规则过滤词库
"""

import re
import sys
import os
from pathlib import Path


# 常用词汇词典文件路径（默认）
# 如果文件不存在，脚本会提示用户下载或创建
COMMON_WORDS_DICT = Path(__file__).parent / "data" / "常用词词典.txt"

# 可选的词典目录，可以放置多个词典文件
DICT_DIR = Path(__file__).parent / "data" / "dicts"


def load_common_words_from_file(dict_file=None):
    """
    从外部词典文件加载常用词
    
    Args:
        dict_file: 词典文件路径，如果为None则使用默认路径
    
    Returns:
        set: 常用词集合
    """
    if dict_file is None:
        dict_file = COMMON_WORDS_DICT
    
    common_words = set()
    
    dict_path = Path(dict_file)
    if not dict_path.is_absolute():
        # 相对路径，尝试多个位置
        possible_paths = [
            Path(__file__).parent / dict_file,
            Path(__file__).parent / "data" / dict_file,
            Path(dict_file),
        ]
    else:
        possible_paths = [dict_path]
    
    found = False
    for path in possible_paths:
        if path.exists():
            try:
                # 尝试不同的编码
                encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin1']
                content = None
                for enc in encodings:
                    try:
                        with open(path, 'r', encoding=enc) as f:
                            content = f.readlines()
                        break
                    except (UnicodeDecodeError, UnicodeError):
                        continue
                
                if content is None:
                    # 尝试二进制读取并检测编码
                    with open(path, 'rb') as f:
                        raw = f.read()
                    # 尝试UTF-16
                    try:
                        content = raw.decode('utf-16').splitlines()
                    except:
                        raise Exception(f"无法识别文件编码: {path}")
                
                import re
                for line in content:
                    word = line.strip()
                    # 跳过空行和注释
                    if not word or word.startswith('#'):
                        continue
                    
                    # 支持多种格式：
                    # 1. 词条\t其他信息
                    # 2. 词条 拼音（如：是的de这zhe个）
                    # 3. 纯词条
                    parts = word.split('\t')
                    if parts and parts[0]:
                        word = parts[0].strip()
                    else:
                        word = word.strip()
                    
                    if not word:
                        continue
                    
                    # 处理"词条+拼音"格式（如：是的de这zhe个）
                    # 提取中文字符部分（连续的中文字符）
                    chinese_chars = re.findall(r'[\u4e00-\u9fff]+', word)
                    if chinese_chars:
                        # 如果有中文字符，取第一个连续的中文部分
                        word = chinese_chars[0]
                        # 只保留有效的中文词（至少1个字符，且不全是标点）
                        if word and len(word) >= 1 and re.search(r'[\u4e00-\u9fff]', word):
                            common_words.add(word)
                    else:
                        # 如果没有中文字符，取第一个单词（英文词）
                        word_parts = word.split()
                        if word_parts:
                            word = word_parts[0]
                        # 只保留有效的英文词（至少2个字符，纯字母）
                        if word and len(word) >= 2 and word.isalpha():
                            common_words.add(word.lower())
                print(f"从外部词典加载常用词: {len(common_words):,} 个")
                print(f"  词典文件: {path}")
                if len(common_words) > 0:
                    sample = sorted(list(common_words))[:10]
                    print(f"  示例: {', '.join(sample)}")
                found = True
                break
            except Exception as e:
                print(f"警告: 无法读取词典文件 {path}: {e}")
                continue
    
    if not found:
        # 尝试从dicts目录加载（可以合并多个词典）
        if DICT_DIR.exists():
            dict_files = list(DICT_DIR.glob("*.txt"))
            # 排除README和下载指南
            dict_files = [f for f in dict_files if not any(kw in f.name.lower() for kw in ['readme', '指南', 'md'])]
            
            if dict_files:
                # 按文件名排序，优先使用包含"常用"或"common"或"merged"的文件
                dict_files.sort(key=lambda x: (
                    0 if any(kw in x.name.lower() for kw in ['常用', 'common', 'merged', 'dict']) else 1,
                    x.name
                ))
                
                # 如果找到合并词典，只使用它；否则合并所有词典
                merged_file = next((f for f in dict_files if 'merged' in f.name.lower()), None)
                if merged_file:
                    dict_files = [merged_file]
                    print(f"在 {DICT_DIR} 目录找到合并词典: {merged_file.name}")
                else:
                    print(f"在 {DICT_DIR} 目录找到 {len(dict_files)} 个词典文件，将合并使用")
                    print(f"词典文件: {', '.join([f.name for f in dict_files[:5]])}")
                    if len(dict_files) > 5:
                        print(f"  ... 还有 {len(dict_files) - 5} 个文件")
                
                try:
                    # 尝试不同的编码
                    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'utf-16', 'utf-16-le', 'utf-16-be']
                    content = None
                    for enc in encodings:
                        try:
                            with open(dict_files[0], 'r', encoding=enc) as f:
                                content = f.readlines()
                            break
                        except (UnicodeDecodeError, UnicodeError):
                            continue
                    
                    if content is None:
                        raise Exception(f"无法识别文件编码: {dict_files[0]}")
                    
                    import re
                    # 如果只有一个文件，直接处理；否则合并所有文件
                    files_to_process = dict_files if not merged_file else [merged_file]
                    
                    for dict_file in files_to_process:
                        # 尝试不同的编码
                        file_encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'utf-16', 'utf-16-le', 'utf-16-be']
                        file_content = None
                        for enc in file_encodings:
                            try:
                                with open(dict_file, 'r', encoding=enc) as f:
                                    file_content = f.readlines()
                                break
                            except (UnicodeDecodeError, UnicodeError):
                                continue
                        
                        if file_content is None:
                            print(f"  警告: 无法读取 {dict_file.name}，跳过")
                            continue
                        
                        file_words_count = 0
                        for line in file_content:
                            word = line.strip()
                            if not word or word.startswith('#'):
                                continue
                            
                            # 支持多种格式
                            parts = word.split('\t')
                            if parts and parts[0]:
                                word = parts[0].strip()
                            else:
                                word = word.strip()
                            
                            if not word:
                                continue
                            
                            # 处理中英文词
                            chinese_chars = re.findall(r'[\u4e00-\u9fff]+', word)
                            if chinese_chars:
                                word = chinese_chars[0]
                                if word and len(word) >= 1:
                                    if word not in common_words:
                                        common_words.add(word)
                                        file_words_count += 1
                            else:
                                word_parts = word.split()
                                if word_parts:
                                    word = word_parts[0]
                                if word and len(word) >= 2 and word.isalpha():
                                    word_lower = word.lower()
                                    if word_lower not in common_words:
                                        common_words.add(word_lower)
                                        file_words_count += 1
                        
                        if len(files_to_process) > 1:
                            print(f"  从 {dict_file.name} 加载了 {file_words_count:,} 个新词")
                    
                    print(f"已加载总计 {len(common_words):,} 个常用词")
                    if len(common_words) > 0:
                        sample = sorted(list(common_words))[:10]
                        print(f"  示例: {', '.join(sample)}")
                    found = True
                except Exception as e:
                    print(f"无法加载 {dict_files[0]}: {e}")
        
        if not found:
            print(f"\n⚠️  未找到常用词词典文件")
            print(f"\n请执行以下操作之一：")
            print(f"1. 下载常用词词典文件到: {DICT_DIR}/")
            print(f"2. 或使用 --dict=文件路径 指定词典文件")
            print(f"3. 或放置词典文件到: {COMMON_WORDS_DICT}")
            print(f"\n词典文件格式: 每行一个词条，支持#注释")
            print(f"\n推荐的词典资源：")
            print(f"- GitHub搜索: 'chinese common words' 或 '中文常用词'")
            print(f"- 现代汉语常用字表（3500字）")
            print(f"- 现代汉语常用词表")
            print(f"\n查看 {DICT_DIR}/README.md 获取更多信息")
    
    return common_words


def is_single_char(word):
    """判断是否为单字"""
    return len(word) == 1


def is_repeated_char(word):
    """判断是否为重复字符（如：啊啊啊、哈哈哈）"""
    if len(word) < 2:
        return False
    if len(set(word)) == 1:
        return True
    if re.match(r'^([啊哦嗯额呃诶呀哟哈呵唉哎])\1{2,}$', word):
        return True
    if re.match(r'^([\u4e00-\u9fff])\1{2,}$', word):
        return True
    return False


def is_pure_number(word):
    """判断是否为纯数字"""
    return bool(re.match(r'^[0-9]+$', word))


def is_pure_punctuation(word):
    """判断是否为纯标点符号"""
    return bool(re.match(r'^[^\w\s\u4e00-\u9fff]+$', word))


def is_pure_english(word):
    """判断是否为纯英文"""
    return bool(re.match(r'^[a-zA-Z]+$', word))


def is_interjection_repeat(word):
    """判断是否为语气词重复"""
    if len(word) < 2:
        return False
    if all(c in {'啊', '哦', '嗯', '额', '呃', '诶', '呀', '哟', '哈', '呵', '唉', '哎'} for c in word):
        return True
    if word[0] in {'啊', '哦', '嗯', '额', '呃', '诶', '呀', '哟', '哈', '呵', '唉', '哎'}:
        if re.match(r'^([啊哦嗯额呃诶呀哟哈呵唉哎])\1+$', word):
            return True
    return False


def should_keep(word, freq, filter_options, common_words):
    """判断是否应该保留该词"""
    # 过滤词频小于阈值的词
    if filter_options.get('min_freq', 0) > 0:
        if freq < filter_options['min_freq']:
            return False
    
    # 过滤单字
    if filter_options.get('filter_single_char', True):
        if is_single_char(word):
            return False
    
    # 过滤常用词汇
    if filter_options.get('filter_common_words', True):
        if word in common_words:
            return False
    
    # 过滤重复字符
    if filter_options.get('filter_repeated', True):
        if is_repeated_char(word):
            return False
    
    # 过滤语气词重复
    if filter_options.get('filter_interjection', True):
        if is_interjection_repeat(word):
            return False
    
    # 过滤纯数字
    if filter_options.get('filter_numbers', True):
        if is_pure_number(word):
            return False
    
    # 过滤纯标点
    if filter_options.get('filter_punctuation', True):
        if is_pure_punctuation(word):
            return False
    
    # 过滤纯英文（可选）
    if filter_options.get('filter_english', False):
        if is_pure_english(word):
            return False
    
    return True


def filter_dict_with_freq(input_file, output_file, filter_options=None, common_words_dict=None):
    """过滤带词频的词库文件"""
    if filter_options is None:
        filter_options = {
            'min_freq': 10,  # 最小词频
            'filter_single_char': True,
            'filter_common_words': True,
            'filter_repeated': True,
            'filter_interjection': True,
            'filter_numbers': True,
            'filter_punctuation': True,
            'filter_english': False,
        }
    
    # 如果需要过滤常用词，从外部词典文件加载
    if filter_options.get('filter_common_words', True) and common_words_dict is None:
        dict_file = filter_options.get('common_words_dict_file')
        common_words_dict = load_common_words_from_file(dict_file)
    elif common_words_dict is None:
        common_words_dict = set()
    
    kept_words = []
    filtered_count = {
        'low_freq': 0,
        'single_char': 0,
        'common_words': 0,
        'repeated': 0,
        'interjection': 0,
        'numbers': 0,
        'punctuation': 0,
        'english': 0,
    }
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # 解析词条和词频（格式：词条\t词频）
            parts = line.split('\t')
            if len(parts) >= 2:
                word = parts[0]
                try:
                    freq = int(parts[1])
                except ValueError:
                    freq = 1
            else:
                word = line
                freq = 1
            
            if should_keep(word, freq, filter_options, common_words_dict):
                kept_words.append((word, freq))
            else:
                # 统计被过滤的类型
                if filter_options.get('min_freq', 0) > 0 and freq < filter_options['min_freq']:
                    filtered_count['low_freq'] += 1
                elif is_single_char(word):
                    filtered_count['single_char'] += 1
                elif word in common_words_dict:
                    filtered_count['common_words'] += 1
                elif is_repeated_char(word):
                    filtered_count['repeated'] += 1
                elif is_interjection_repeat(word):
                    filtered_count['interjection'] += 1
                elif is_pure_number(word):
                    filtered_count['numbers'] += 1
                elif is_pure_punctuation(word):
                    filtered_count['punctuation'] += 1
                elif is_pure_english(word):
                    filtered_count['english'] += 1
    
    # 去重但保持原始顺序
    seen = set()
    unique_words = []
    for word, freq in kept_words:
        if word not in seen:
            seen.add(word)
            unique_words.append((word, freq))
    
    # 写入输出文件（带词频）
    with open(output_file, 'w', encoding='utf-8') as f:
        for word, freq in unique_words:
            f.write(f"{word}\t{freq}\n")
    
    # 如果输出文件在data目录，同时生成不带词频的版本
    output_path = Path(output_file)
    if output_path.parent.name == "data" and "带词频" in output_path.name:
        # 生成不带词频的版本（基于输出文件名，去掉"_带词频"后缀）
        base_name = output_path.stem.replace("_带词频", "").replace("带词频", "")
        # 如果已经包含"final"，就不再添加
        if "_final" not in base_name:
            final_file = output_path.parent / f"{base_name}_final.txt"
        else:
            final_file = output_path.parent / f"{base_name}.txt"
        with open(final_file, 'w', encoding='utf-8') as f:
            for word, freq in unique_words:
                f.write(f"{word}\n")
        print(f"同时生成不带词频版本: {final_file.name}")
    
    return len(unique_words), filtered_count


def filter_dict(input_file, output_file, filter_options=None, common_words_dict=None):
    """过滤不带词频的词库文件（兼容旧格式）"""
    if filter_options is None:
        filter_options = {
            'filter_single_char': True,
            'filter_common_words': False,  # 不带词频时默认不过滤常用词
            'filter_repeated': True,
            'filter_interjection': True,
            'filter_numbers': True,
            'filter_punctuation': True,
            'filter_english': False,
        }
    
    if common_words_dict is None:
        common_words_dict = set()
    
    kept_words = []
    filtered_count = {
        'single_char': 0,
        'common_words': 0,
        'repeated': 0,
        'interjection': 0,
        'numbers': 0,
        'punctuation': 0,
        'english': 0,
    }
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            word = line.strip()
            if not word:
                continue
            
            if should_keep(word, 1, filter_options, common_words_dict):
                kept_words.append(word)
            else:
                # 统计被过滤的类型
                if is_single_char(word):
                    filtered_count['single_char'] += 1
                elif word in common_words_dict:
                    filtered_count['common_words'] += 1
                elif is_repeated_char(word):
                    filtered_count['repeated'] += 1
                elif is_interjection_repeat(word):
                    filtered_count['interjection'] += 1
                elif is_pure_number(word):
                    filtered_count['numbers'] += 1
                elif is_pure_punctuation(word):
                    filtered_count['punctuation'] += 1
                elif is_pure_english(word):
                    filtered_count['english'] += 1
    
    # 去重但保持原始顺序
    seen = set()
    unique_words = []
    for word in kept_words:
        if word not in seen:
            seen.add(word)
            unique_words.append(word)
    
    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        for word in unique_words:
            f.write(word + '\n')
    
    return len(unique_words), filtered_count


def main():
    if len(sys.argv) < 2:
        print("词库过滤工具")
        print("=" * 50)
        print("用法: python3 filter_dict.py <输入文件> [输出文件] [选项]")
        print("\n选项:")
        print("  --min-freq=N       最小词频（默认10，仅对带词频文件有效）")
        print("  --no-common        不过滤常用词汇")
        print("  --no-single        不过滤单字")
        print("  --dict=FILE        指定常用词词典文件（默认: data/常用词词典.txt）")
        print("\n示例:")
        print("  python3 filter_dict.py data/词库_带词频.txt data/词库_过滤.txt")
        print("  python3 filter_dict.py data/词库_带词频.txt --min-freq=10")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # 默认输出到data目录
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    # 解析选项
    filter_common = '--no-common' not in sys.argv
    filter_single = '--no-single' not in sys.argv
    min_freq = 10
    common_dict_file = None  # 外部常用词词典文件
    
    for arg in sys.argv:
        if arg.startswith('--min-freq='):
            min_freq = int(arg.split('=')[1])
        elif arg.startswith('--dict='):
            common_dict_file = arg.split('=', 1)[1]
    
    # 检查输入文件是否带词频（包含\t分隔符）
    has_freq = False
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            if '\t' in first_line:
                has_freq = True
    except:
        pass
    
    if len(sys.argv) > 2 and not sys.argv[2].startswith('--'):
        output_file = sys.argv[2]
    else:
        # 基于输入文件名生成输出文件名
        input_path = Path(input_file)
        base_name = input_path.stem  # 不含扩展名的文件名
        
        # 如果输入文件名包含"_带词频"，去掉它作为基础名
        if "_带词频" in base_name:
            base_name = base_name.replace("_带词频", "")
        
        if input_path.parent.name == "data":
            if has_freq:
                output_file = str(input_path.parent / f"{base_name}_final_带词频.txt")
            else:
                output_file = str(input_path.parent / f"{base_name}_final.txt")
        else:
            if has_freq:
                output_file = str(data_dir / f"{base_name}_final_带词频.txt")
            else:
                output_file = str(data_dir / f"{base_name}_final.txt")
    
    filter_options = {
        'min_freq': min_freq if has_freq else 0,
        'filter_single_char': filter_single,
        'filter_common_words': filter_common,
        'filter_repeated': True,
        'filter_interjection': True,
        'filter_numbers': True,
        'filter_punctuation': True,
        'filter_english': False,
        'common_words_dict_file': common_dict_file,
    }
    
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    print(f"过滤选项: {filter_options}")
    print("-" * 50)
    
    # 如果需要过滤常用词，从外部词典文件加载
    common_words_dict = None
    if filter_common:
        print("正在从外部词典加载常用词...")
        common_words_dict = load_common_words_from_file(common_dict_file)
    
    # 统计原始词条数
    with open(input_file, 'r', encoding='utf-8') as f:
        original_count = sum(1 for line in f if line.strip())
    
    # 执行过滤
    if has_freq:
        kept_count, filtered_stats = filter_dict_with_freq(
            input_file, output_file, filter_options, common_words_dict
        )
    else:
        kept_count, filtered_stats = filter_dict(
            input_file, output_file, filter_options, common_words_dict
        )
    
    # 显示统计
    print(f"\n原始词条数: {original_count:,}")
    print(f"保留词条数: {kept_count:,}")
    print(f"过滤词条数: {original_count - kept_count:,}")
    print(f"\n过滤统计:")
    for key, count in filtered_stats.items():
        if count > 0:
            print(f"  - {key}: {count:,}")
    
    print(f"\n✅ 过滤完成! 文件已保存到: {output_file}")
    
    # 显示前20个保留的词条
    if kept_count > 0:
        print("\n前20个保留的词条:")
        with open(output_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if i > 20:
                    break
                print(f"  {i}. {line.strip()}")


if __name__ == '__main__':
    main()
