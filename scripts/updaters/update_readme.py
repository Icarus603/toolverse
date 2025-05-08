#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
自动更新脚本 - 更新README中的工具表格
"""

import os
import re
import yaml
import logging
import argparse
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("update_readme.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_tools_yaml(yaml_path):
    """
    加载工具数据YAML文件
    
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
            logger.warning(f"YAML文件不存在: {yaml_path}")
            return []
    except Exception as e:
        logger.error(f"加载YAML文件时出错: {str(e)}")
        return []

def get_latest_tools(tools, days=30, limit=10):
    """
    获取最新添加的工具
    
    Args:
        tools (list): 工具数据列表
        days (int): 天数范围
        limit (int): 最大数量
        
    Returns:
        list: 最新工具列表
    """
    # 计算日期范围
    today = datetime.now()
    date_threshold = (today - timedelta(days=days)).strftime("%Y-%m-%d")
    
    # 过滤最近添加的工具
    recent_tools = [
        tool for tool in tools 
        if tool.get('added_date') and tool.get('added_date') >= date_threshold
    ]
    
    # 按添加日期排序
    recent_tools.sort(key=lambda x: x.get('added_date', ''), reverse=True)
    
    return recent_tools[:limit]

def generate_tools_table(tools):
    """
    生成工具表格的Markdown
    
    Args:
        tools (list): 工具列表
        
    Returns:
        str: Markdown表格
    """
    # 表头
    table = "| 工具名称 | 分类 | 添加日期 | 描述 | 标签 |\n"
    table += "| ------- | ---- | -------- | ---- | ---- |\n"
    
    # 类别映射（英文到中文）
    category_map = {
        'text': '📝 文本',
        'image': '🖼️ 图像',
        'video': '🎬 视频',
        'audio': '🔊 音频',
        'workflow': '⚙️ 工作流',
        'robotics': '🤖 机器人',
        'multimodal': '🔄 多模态',
        'other': '🔍 其他'
    }
    
    # 生成表格行
    for tool in tools:
        name = tool.get('name', '')
        url = tool.get('url', '')
        category = category_map.get(tool.get('category', 'other'), '🔍 其他')
        added_date = tool.get('added_date', '')
        description = tool.get('description', '').replace('\n', ' ')
        tags = ", ".join([f"`{tag}`" for tag in tool.get('tags', [])])
        
        # 生成链接
        linked_name = f"[{name}]({url})" if url else name
        
        # 添加一行
        table += f"| {linked_name} | {category} | {added_date} | {description} | {tags} |\n"
    
    return table

def update_readme(readme_path, tools_table):
    """
    更新README文件中的工具表格
    
    Args:
        readme_path (str): README文件路径
        tools_table (str): 工具表格Markdown
        
    Returns:
        bool: 是否成功更新
    """
    try:
        # 读取README
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 定义标记
        start_marker = "<!--LATEST_TOOLS_START-->"
        end_marker = "<!--LATEST_TOOLS_END-->"
        
        # 查找标记
        start_index = content.find(start_marker)
        end_index = content.find(end_marker)
        
        if start_index == -1 or end_index == -1:
            logger.error(f"README中未找到标记: {start_marker} 或 {end_marker}")
            return False
        
        # 替换内容
        new_content = (
            content[:start_index + len(start_marker)] + 
            "\n\n" + tools_table + "\n" + 
            content[end_index:]
        )
        
        # 保存README
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logger.info(f"已更新README: {readme_path}")
        return True
        
    except Exception as e:
        logger.error(f"更新README时出错: {str(e)}")
        return False

def parse_args():
    parser = argparse.ArgumentParser(description='更新README中的工具表格')
    parser.add_argument('--yaml-path', default='../../data/processed/tools.yaml', help='YAML文件路径')
    parser.add_argument('--readme-path', default='../../README.md', help='README文件路径')
    parser.add_argument('--days', type=int, default=30, help='显示最近几天添加的工具')
    parser.add_argument('--limit', type=int, default=10, help='最多显示多少个工具')
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    # 获取工作目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 解析相对路径
    yaml_path = os.path.abspath(os.path.join(script_dir, args.yaml_path))
    readme_path = os.path.abspath(os.path.join(script_dir, args.readme_path))
    
    logger.info(f"YAML文件路径: {yaml_path}")
    logger.info(f"README文件路径: {readme_path}")
    
    # 加载工具数据
    tools = load_tools_yaml(yaml_path)
    
    # 获取最新工具
    latest_tools = get_latest_tools(tools, args.days, args.limit)
    logger.info(f"找到 {len(latest_tools)} 个最新添加的工具")
    
    # 生成表格
    table = generate_tools_table(latest_tools)
    
    # 更新README
    if update_readme(readme_path, table):
        logger.info("README更新成功")
    else:
        logger.error("README更新失败")

if __name__ == "__main__":
    main() 