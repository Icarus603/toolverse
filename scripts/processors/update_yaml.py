#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据处理脚本 - 用于将爬虫抓取的数据合并到主数据库中
"""

import os
import sys
import json
import yaml
import glob
import logging
import argparse
from datetime import datetime
from urllib.parse import urlparse


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("update_yaml.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def normalize_url(url):
    """
    规范化URL，移除协议、www和尾部斜杠，用于URL去重
    
    Args:
        url (str): 原始URL
        
    Returns:
        str: 规范化后的URL
    """
    if not url:
        return ""
    
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    path = parsed.path.rstrip("/")
    
    return f"{domain}{path}"


def load_tools_yaml(yaml_path):
    """
    加载主工具数据库YAML文件
    
    Args:
        yaml_path (str): YAML文件路径
        
    Returns:
        list: 工具数据列表
    """
    try:
        if os.path.exists(yaml_path):
            with open(yaml_path, 'r', encoding='utf-8') as f:
                tools = yaml.safe_load(f) or []
                logger.info(f"从 {yaml_path} 加载了 {len(tools)} 个工具")
                return tools
        else:
            logger.warning(f"YAML文件不存在: {yaml_path}，将创建新文件")
            return []
    except Exception as e:
        logger.error(f"加载YAML文件 {yaml_path} 时出错: {str(e)}")
        return []


def load_raw_json_files(raw_dir, days=7):
    """
    加载原始爬虫数据文件
    
    Args:
        raw_dir (str): 原始数据目录
        days (int): 只处理最近几天的文件
        
    Returns:
        list: 工具数据列表
    """
    all_tools = []
    
    # 递归查找所有JSON文件
    json_files = []
    for root, _, files in os.walk(raw_dir):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    
    # 按修改时间排序，只处理最新的文件
    json_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    # 读取并合并数据
    for json_file in json_files[:days * 5]:  # 假设每天最多5个爬虫文件
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                tools = json.load(f)
                if isinstance(tools, list):
                    logger.info(f"从 {json_file} 加载了 {len(tools)} 个工具")
                    all_tools.extend(tools)
                else:
                    logger.warning(f"JSON文件 {json_file} 格式不正确，应为列表")
        except Exception as e:
            logger.error(f"读取JSON文件 {json_file} 时出错: {str(e)}")
    
    return all_tools


def merge_tools(existing_tools, new_tools):
    """
    合并新旧工具数据，处理重复和冲突
    
    Args:
        existing_tools (list): 现有工具列表
        new_tools (list): 新工具列表
        
    Returns:
        list: 合并后的工具列表
    """
    # 创建映射表，用于快速查找现有工具
    existing_map = {}
    for tool in existing_tools:
        if 'url' in tool and tool['url']:
            norm_url = normalize_url(tool['url'])
            existing_map[norm_url] = tool
        
        # 也用ID作为键
        if 'id' in tool and tool['id']:
            existing_map[tool['id']] = tool
    
    # 计数器
    added_count = 0
    updated_count = 0
    skipped_count = 0
    
    # 处理新工具
    for new_tool in new_tools:
        if not new_tool.get('url'):
            skipped_count += 1
            continue
        
        norm_url = normalize_url(new_tool['url'])
        
        # 检查是否已存在相同URL的工具
        if norm_url in existing_map:
            # 更新现有工具
            existing_tool = existing_map[norm_url]
            
            # 只更新来源为爬虫的工具数据
            if new_tool.get('source', {}).get('type') == 'crawler':
                # 合并标签
                if 'tags' in new_tool and new_tool['tags']:
                    existing_tags = existing_tool.get('tags', [])
                    for tag in new_tool['tags']:
                        if tag not in existing_tags:
                            existing_tags.append(tag)
                    existing_tool['tags'] = existing_tags
                
                # 更新更新日期
                existing_tool['updated_date'] = datetime.now().strftime("%Y-%m-%d")
                
                updated_count += 1
            else:
                skipped_count += 1
        else:
            # 添加新工具
            if 'id' not in new_tool or not new_tool['id']:
                # 生成ID
                domain = urlparse(new_tool['url']).netloc.replace("www.", "")
                new_tool['id'] = f"{domain.split('.')[0]}-{datetime.now().strftime('%Y%m%d')}"
            
            # 确保有添加日期
            if 'added_date' not in new_tool:
                new_tool['added_date'] = datetime.now().strftime("%Y-%m-%d")
            
            # 添加到现有列表和映射
            existing_tools.append(new_tool)
            existing_map[norm_url] = new_tool
            existing_map[new_tool['id']] = new_tool
            
            added_count += 1
    
    logger.info(f"合并结果: 添加 {added_count} 个新工具, 更新 {updated_count} 个现有工具, 跳过 {skipped_count} 个工具")
    
    return existing_tools


def validate_tool(tool):
    """
    验证工具数据是否有效
    
    Args:
        tool (dict): 工具数据
        
    Returns:
        bool: 是否有效
    """
    # 基本验证：必须有名称、URL和描述
    if not tool.get('name') or not tool.get('url') or not tool.get('description'):
        return False
    
    # URL必须是有效的
    url = tool.get('url', '')
    if not url.startswith(('http://', 'https://')):
        return False
    
    # 类别必须有效
    valid_categories = ['text', 'image', 'video', 'audio', 'workflow', 'robotics', 'multimodal', 'other']
    if tool.get('category') not in valid_categories:
        # 设置默认类别
        tool['category'] = 'other'
    
    return True


def save_tools_yaml(tools, yaml_path):
    """
    保存工具数据到YAML文件
    
    Args:
        tools (list): 工具数据列表
        yaml_path (str): YAML文件路径
    """
    # 验证数据
    validated_tools = []
    for tool in tools:
        if validate_tool(tool):
            validated_tools.append(tool)
        else:
            logger.warning(f"工具数据无效，已跳过: {tool.get('name', 'unknown')}")
    
    # 确保目录存在
    os.makedirs(os.path.dirname(yaml_path), exist_ok=True)
    
    # 保存数据
    try:
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(validated_tools, f, allow_unicode=True, sort_keys=False, indent=2)
        logger.info(f"已将 {len(validated_tools)} 个工具保存到 {yaml_path}")
    except Exception as e:
        logger.error(f"保存YAML文件 {yaml_path} 时出错: {str(e)}")


def archive_yaml(yaml_path, archive_dir):
    """
    归档YAML文件
    
    Args:
        yaml_path (str): YAML文件路径
        archive_dir (str): 归档目录
    """
    if not os.path.exists(yaml_path):
        logger.warning(f"YAML文件不存在，无法归档: {yaml_path}")
        return
    
    os.makedirs(archive_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path = os.path.join(
        archive_dir, 
        f"tools_{timestamp}.yaml"
    )
    
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f_in:
            with open(archive_path, 'w', encoding='utf-8') as f_out:
                f_out.write(f_in.read())
        logger.info(f"已将YAML文件归档到 {archive_path}")
    except Exception as e:
        logger.error(f"归档YAML文件时出错: {str(e)}")


def parse_args():
    parser = argparse.ArgumentParser(description='更新工具数据库')
    parser.add_argument('--raw-dir', default='../../data/raw', help='原始数据目录')
    parser.add_argument('--yaml-path', default='../../data/processed/tools.yaml', help='YAML文件路径')
    parser.add_argument('--archive-dir', default='../../data/processed/tools_archive', help='归档目录')
    parser.add_argument('--days', type=int, default=7, help='处理最近几天的文件')
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 获取工作目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 解析相对路径
    raw_dir = os.path.abspath(os.path.join(script_dir, args.raw_dir))
    yaml_path = os.path.abspath(os.path.join(script_dir, args.yaml_path))
    archive_dir = os.path.abspath(os.path.join(script_dir, args.archive_dir))
    
    logger.info(f"原始数据目录: {raw_dir}")
    logger.info(f"YAML文件路径: {yaml_path}")
    logger.info(f"归档目录: {archive_dir}")
    
    # 归档现有YAML文件
    archive_yaml(yaml_path, archive_dir)
    
    # 加载现有工具数据
    existing_tools = load_tools_yaml(yaml_path)
    
    # 加载新工具数据
    new_tools = load_raw_json_files(raw_dir, args.days)
    
    # 合并数据
    merged_tools = merge_tools(existing_tools, new_tools)
    
    # 保存结果
    save_tools_yaml(merged_tools, yaml_path)
    
    logger.info("更新完成")


if __name__ == "__main__":
    main() 