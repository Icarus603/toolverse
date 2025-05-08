#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Hugging Face Spaces爬虫脚本 - 用于从Hugging Face Spaces抓取AI工具相关信息
"""

import os
import json
import time
import logging
import argparse
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("huggingface_crawler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HuggingFaceCrawler:
    """从Hugging Face Spaces抓取AI工具信息的爬虫类"""
    
    def __init__(self, base_url="https://huggingface.co", max_pages=10, delay=1):
        """
        初始化Hugging Face爬虫
        
        Args:
            base_url (str): Hugging Face基础URL
            max_pages (int): 最大抓取页数
            delay (int): 请求延迟(秒)
        """
        self.base_url = base_url
        self.max_pages = max_pages
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                      "data", "raw", "huggingface")
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
    
    def crawl(self):
        """执行爬取过程"""
        all_spaces = []
        
        # 抓取Spaces列表页
        for page in range(1, self.max_pages + 1):
            try:
                url = f"{self.base_url}/spaces?sort=trending&p={page}"
                logger.info(f"正在抓取页面: {url}")
                
                response = self.session.get(url)
                if response.status_code != 200:
                    logger.error(f"请求失败，状态码: {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找所有Space卡片
                space_cards = soup.select('article.space-card')
                
                if not space_cards:
                    logger.warning(f"页面 {page} 未找到Space卡片，可能到达末页或选择器有变化")
                    break
                
                # 遍历卡片提取信息
                for card in space_cards:
                    try:
                        space_data = self._extract_space_data(card)
                        if space_data:
                            # 获取详细信息
                            space_details = self._fetch_space_details(space_data['url'])
                            if space_details:
                                space_data.update(space_details)
                                
                            all_spaces.append(space_data)
                            logger.info(f"抓取到Space: {space_data['name']}")
                    except Exception as e:
                        logger.error(f"处理Space卡片时出错: {str(e)}")
                
                # 添加延迟，避免请求过快
                time.sleep(self.delay)
                
            except Exception as e:
                logger.error(f"抓取页面 {page} 时出错: {str(e)}")
        
        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.output_dir, f"huggingface_spaces_{timestamp}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_spaces, f, ensure_ascii=False, indent=2)
        
        logger.info(f"爬取完成，共抓取 {len(all_spaces)} 个Space，保存到 {output_file}")
        return all_spaces
    
    def _extract_space_data(self, card):
        """
        从Space卡片中提取数据
        
        Args:
            card: BeautifulSoup对象，表示一个Space卡片
            
        Returns:
            dict: Space数据字典
        """
        try:
            # 提取链接和名称
            title_element = card.select_one('a.header')
            if not title_element:
                return None
                
            space_url = urljoin(self.base_url, title_element.get('href'))
            
            # 提取作者和空间名
            author, space_name = self._parse_space_url(space_url)
            if not author or not space_name:
                return None
            
            # 提取标题和描述
            title = title_element.text.strip()
            description_element = card.select_one('div.description')
            description = description_element.text.strip() if description_element else ""
            
            # 提取点赞数
            likes_element = card.select_one('span.inline-flex span')
            likes = 0
            if likes_element:
                likes_text = likes_element.text.strip()
                likes = int(likes_text) if likes_text.isdigit() else 0
            
            # 提取标签
            tags = []
            tag_elements = card.select('a.tag')
            for tag_element in tag_elements:
                tag = tag_element.text.strip()
                if tag:
                    tags.append(tag)
            
            # 创建数据结构
            space_data = {
                "id": f"hf-space-{author}-{space_name}",
                "name": title,
                "url": space_url,
                "description": description,
                "author": author,
                "space_name": space_name,
                "likes": likes,
                "tags": tags,
                "source": {
                    "type": "crawler",
                    "url": space_url,
                    "date": datetime.now().strftime("%Y-%m-%d")
                },
                "added_date": datetime.now().strftime("%Y-%m-%d")
            }
            
            return space_data
            
        except Exception as e:
            logger.error(f"提取Space数据时出错: {str(e)}")
            return None
    
    def _parse_space_url(self, url):
        """
        从URL中解析作者和Space名称
        
        Args:
            url (str): Space URL
            
        Returns:
            tuple: (author, space_name)
        """
        pattern = r'https?://huggingface\.co/spaces/([^/]+)/([^/]+)'
        match = re.match(pattern, url)
        if match:
            return match.group(1), match.group(2)
        return None, None
    
    def _fetch_space_details(self, space_url):
        """
        获取Space详细信息
        
        Args:
            space_url (str): Space URL
            
        Returns:
            dict: 详细信息字典
        """
        try:
            logger.info(f"正在获取Space详情: {space_url}")
            
            response = self.session.get(space_url)
            if response.status_code != 200:
                logger.error(f"请求Space详情失败，状态码: {response.status_code}")
                return {}
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取详细描述
            readme_element = soup.select_one('div.space-readme article')
            detailed_description = ""
            if readme_element:
                detailed_description = readme_element.text.strip()
            
            # 尝试确定分类
            category = self._determine_category(soup, detailed_description)
            
            # 提取SDK/模型信息
            sdk_elements = soup.select('div.space-sdk-items a.link-box')
            sdk_info = []
            for element in sdk_elements:
                sdk_name = element.text.strip()
                if sdk_name:
                    sdk_info.append(sdk_name)
            
            # 获取评论数
            comments_count = 0
            comments_element = soup.select_one('span.discussion-tab-count')
            if comments_element:
                comments_text = comments_element.text.strip()
                if comments_text.isdigit():
                    comments_count = int(comments_text)
            
            # 获取创建/更新时间
            created_at = ""
            updated_at = ""
            time_elements = soup.select('div.metadata time')
            if len(time_elements) >= 2:
                updated_at = time_elements[0].get('datetime', "")
                created_at = time_elements[1].get('datetime', "")
            
            return {
                "detailed_description": detailed_description,
                "category": category,
                "tech_stack": sdk_info,
                "comments_count": comments_count,
                "created_at": created_at,
                "updated_at": updated_at,
            }
            
        except Exception as e:
            logger.error(f"获取Space详情时出错: {str(e)}")
            return {}
    
    def _determine_category(self, soup, description):
        """
        确定Space的类别
        
        Args:
            soup: BeautifulSoup对象
            description (str): 详细描述
            
        Returns:
            str: 类别
        """
        # 首先查找标签
        tags = [tag.text.strip().lower() for tag in soup.select('a.tag')]
        
        # 将描述转为小写
        description = description.lower()
        
        # 根据标签和描述判断类别
        if any(keyword in ' '.join(tags) or keyword in description for keyword in 
               ['image', 'img', 'vision', 'picture', 'photo', 'gan', 'diffusion']):
            return 'image'
            
        elif any(keyword in ' '.join(tags) or keyword in description for keyword in 
                ['video', 'movie', 'animation', 'motion']):
            return 'video'
            
        elif any(keyword in ' '.join(tags) or keyword in description for keyword in 
                ['audio', 'sound', 'music', 'voice', 'speech', 'whisper']):
            return 'audio'
            
        elif any(keyword in ' '.join(tags) or keyword in description for keyword in 
                ['workflow', 'pipeline', 'automation', 'langchain']):
            return 'workflow'
            
        elif any(keyword in ' '.join(tags) or keyword in description for keyword in 
                ['multimodal', 'multi-modal', 'vision-language']):
            return 'multimodal'
            
        elif any(keyword in ' '.join(tags) or keyword in description for keyword in 
                ['robotics', 'robot', 'hardware']):
            return 'robotics'
            
        # 默认为文本类别
        return 'text'

def parse_args():
    parser = argparse.ArgumentParser(description='Hugging Face Spaces爬虫')
    parser.add_argument('--base-url', default='https://huggingface.co', help='Hugging Face基础URL')
    parser.add_argument('--max-pages', type=int, default=10, help='最大抓取页数')
    parser.add_argument('--delay', type=int, default=1, help='请求延迟(秒)')
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    crawler = HuggingFaceCrawler(
        base_url=args.base_url,
        max_pages=args.max_pages,
        delay=args.delay
    )
    
    spaces = crawler.crawl()
    logger.info(f"共抓取到 {len(spaces)} 个Space")

if __name__ == "__main__":
    main() 