#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
自动更新脚本 - 更新README中的贡献者名单

此脚本目前是一个占位符，确保README中存在贡献者标记。
未来可以扩展为从GitHub API拉取贡献者信息。
"""

import os
import re
import logging
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("update_contributors.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

CONTRIBUTORS_START_MARKER = "<!--CONTRIBUTORS_START-->"
CONTRIBUTORS_END_MARKER = "<!--CONTRIBUTORS_END-->"
DEFAULT_CONTRIBUTORS_TEXT = "感谢你的加入与支持！更多贡献者将在这里展示。"

def update_contributors_section(readme_path):
    """
    检查并确保README文件中有贡献者部分。
    如果标记存在但中间为空，则插入默认文本。

    Args:
        readme_path (str): README文件路径
        
    Returns:
        bool: 是否成功处理
    """
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()

        start_index = content.find(CONTRIBUTORS_START_MARKER)
        end_index = content.find(CONTRIBUTORS_END_MARKER)

        if start_index == -1 or end_index == -1:
            logger.error(f"README中未找到贡献者标记: {CONTRIBUTORS_START_MARKER} 或 {CONTRIBUTORS_END_MARKER}")
            # Optionally, create the section if it doesn't exist
            # For now, we just log an error if markers are missing.
            return False
        
        # Check if the section between markers is empty or just whitespace
        section_content_start = start_index + len(CONTRIBUTORS_START_MARKER)
        section_content_end = end_index
        current_section_text = content[section_content_start:section_content_end].strip()

        if not current_section_text:
            logger.info("贡献者部分为空，插入默认文本。")
            new_content = (
                content[:section_content_start] +
                "\n\n" + DEFAULT_CONTRIBUTORS_TEXT + "\n\n" +
                content[section_content_end:]
            )
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            logger.info(f"已向 {readme_path} 的贡献者部分插入默认文本。")
        else:
            logger.info("贡献者部分已存在内容，无需修改。")
            
        return True

    except Exception as e:
        logger.error(f"更新README贡献者部分时出错: {str(e)}")
        return False

def parse_args():
    parser = argparse.ArgumentParser(description='更新README中的贡献者名单')
    parser.add_argument('--readme-path', default='../../README.md', help='README文件路径')
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    readme_path = os.path.abspath(os.path.join(script_dir, args.readme_path))
    
    logger.info(f"README文件路径: {readme_path}")
    
    if update_contributors_section(readme_path):
        logger.info("贡献者部分检查/更新完成。")
    else:
        logger.error("贡献者部分检查/更新失败。")

if __name__ == "__main__":
    main() 