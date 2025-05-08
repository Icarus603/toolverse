#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Reddit爬虫脚本 - 用于从Reddit抓取AI工具相关信息
"""

import os
import json
import time
import logging
import argparse
from datetime import datetime, timedelta
import praw
import yaml

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("reddit_crawler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RedditCrawler:
    """从Reddit抓取AI工具信息的爬虫类"""
    
    def __init__(self, client_id, client_secret, user_agent, subreddits, limit=100):
        """
        初始化Reddit爬虫
        
        Args:
            client_id (str): Reddit API客户端ID
            client_secret (str): Reddit API客户端密钥
            user_agent (str): User Agent字符串
            subreddits (list): 要抓取的子版块列表
            limit (int): 每个子版块抓取的帖子数量限制
        """
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        self.subreddits = subreddits
        self.limit = limit
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                      "data", "raw", "reddit")
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        self.crawled_urls = set() # To avoid processing duplicate URLs within a single crawl
        
    def crawl(self):
        """执行爬取过程"""
        all_tools = []
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        for subreddit_name in self.subreddits:
            logger.info(f"开始抓取子版块: r/{subreddit_name}")
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # 获取最新帖子 (过去7天内)
                logger.info(f"正在从 r/{subreddit_name} 获取最新帖子...")
                for post in subreddit.new(limit=self.limit * 2): # Fetch more to filter by date
                    post_time = datetime.utcfromtimestamp(post.created_utc)
                    if post_time >= seven_days_ago:
                        if self._is_ai_tool_post(post) and post.url not in self.crawled_urls:
                            tool_data = self._extract_tool_data(post)
                            if tool_data:
                                all_tools.append(tool_data)
                                self.crawled_urls.add(tool_data['url'])
                                logger.info(f"从 'new' 抓取到工具: {tool_data['name']}")
                    else:
                        # Posts are sorted by new, so we can break if older than 7 days
                        break 
                
                # 获取带有特定关键词的帖子 (过去7天内)
                search_queries = ["AI tool", "AI new tool", "GPT tool", "LLM tool", "machine learning app", "AI project release"]
                logger.info(f"正在从 r/{subreddit_name} 搜索关键词帖子 (time_filter='week')...")
                for query in search_queries:
                    try:
                        for post in subreddit.search(query, sort='new', time_filter='week', limit=self.limit // 2):
                            # Search with time_filter='week' should already limit to past week
                            # but double check created_utc just in case of edge cases or PRAW behavior
                            post_time = datetime.utcfromtimestamp(post.created_utc)
                            if post_time >= seven_days_ago: # Redundant if time_filter='week' is strict, but safe
                                if self._is_ai_tool_post(post) and post.url not in self.crawled_urls:
                                    tool_data = self._extract_tool_data(post)
                                    if tool_data:
                                        all_tools.append(tool_data)
                                        self.crawled_urls.add(tool_data['url'])
                                        logger.info(f"通过搜索 '{query}' 找到工具: {tool_data['name']}")
                            # else: # Not strictly necessary to break here as search limit is smaller
                            #    pass 
                    except Exception as e:
                        logger.error(f"在 r/{subreddit_name} 中搜索关键词 '{query}' 时出错: {str(e)}")

            except Exception as e:
                logger.error(f"抓取子版块 r/{subreddit_name} 时出错: {str(e)}")
        
        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.output_dir, f"reddit_tools_{timestamp}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_tools, f, ensure_ascii=False, indent=2)
        
        logger.info(f"爬取完成，共抓取 {len(all_tools)} 个工具，保存到 {output_file}")
        return all_tools
    
    def _is_ai_tool_post(self, post):
        """
        判断一个帖子是否与AI工具相关
        
        Args:
            post: Reddit帖子对象
            
        Returns:
            bool: 是否是AI工具相关帖子
        """
        # 检查标题是否包含关键词
        title_keywords = ['tool', 'app', 'launch', 'platform', 'website', 'api', 
                         'released', 'built', 'created', 'introducing', 'check out', 
                         'project', 'service', 'webapp', 'script', 'library', 'framework', 'opensource']
        ai_keywords = ['ai', 'gpt', 'ml', 'machine learning', 'artificial intelligence', 
                      'neural', 'deep learning', 'model', 'llm', 'generative', 'agent', 'copilot', 
                      'ocr', 'asr', 'tts', 'computer vision', 'nlp']
        
        post_title_lower = post.title.lower()
        # 检查是否同时包含工具关键词和AI关键词
        has_tool_keyword = any(keyword in post_title_lower for keyword in title_keywords)
        has_ai_keyword = any(keyword in post_title_lower for keyword in ai_keywords)
        
        # 检查是否包含URL
        has_url = (post.url and post.url.startswith('http') and 'reddit.com' not in post.url)
        
        return (has_tool_keyword and has_ai_keyword) or (has_ai_keyword and has_url)
    
    def _extract_tool_data(self, post):
        """
        从帖子中提取工具数据
        
        Args:
            post: Reddit帖子对象
            
        Returns:
            dict: 工具数据字典，如果无法提取则返回None
        """
        # 如果没有URL，则跳过
        if not post.url or 'reddit.com' in post.url:
            return None
        
        # 获取评论
        post.comments.replace_more(limit=0)
        comments_text = " ".join([comment.body for comment in post.comments.list()[:10]])
        
        # 提取工具名称（默认使用帖子标题）
        name = post.title
        
        # 移除常见前缀
        prefixes_to_remove = [
            "i made ", "i built ", "i created ", "check out ", "introducing ", 
            "just launched ", "new tool: ", "new ai tool: ", "presenting ", 
            "my new ", "our new ", "release: ", "show HN: ", "ask HN: ", "[P]", "[R]", "[D]", "[Project]", "[Tool]"
        ]
        for prefix in prefixes_to_remove:
            if name.lower().startswith(prefix.lower()):
                name = name[len(prefix):]
                break
        
        # 提取描述
        description = post.selftext[:500] if post.selftext else post.title
        
        # 尝试确定类别
        category = self._determine_category(post.title, post.selftext, comments_text)
        # 获取热度指标
        score = post.score
        num_comments = post.num_comments
        upvote_ratio = post.upvote_ratio

        # 创建工具数据结构
        tool_data = {
            "id": f"reddit-{post.id}",
            "name": name.strip(),
            "url": post.url,
            "description": description.strip(),
            "detailed_description": post.selftext.strip() if post.selftext else "",
            "category": category,
            "tags": self._extract_tags(post.title, post.selftext, comments_text),
            "source": {
                "type": "crawler",
                "name": "Reddit",
                "url": f"https://www.reddit.com{post.permalink}",
                "date": datetime.utcfromtimestamp(post.created_utc).strftime("%Y-%m-%d")
            },
            "popularity": {
                "reddit_score": score,
                "reddit_num_comments": num_comments,
                "reddit_upvote_ratio": upvote_ratio
            },
            "added_date": datetime.now().strftime("%Y-%m-%d"),
            "raw_data_link": f"https://www.reddit.com/api/info.json?id=t3_{post.id}" # Link to raw JSON for the post
        }
        
        return tool_data
    
    def _determine_category(self, title, selftext, comments):
        """
        根据帖子信息确定工具类别
        
        Args:
            title (str): 帖子标题
            selftext (str): 帖子内容
            comments (str): 评论内容
            
        Returns:
            str: 工具类别
        """
        combined_text = f"{title} {selftext} {comments}".lower()
        
        # 根据关键词判断类别
        if any(kw in combined_text for kw in ['image', 'photo', 'picture', 'art', 'drawing', 'painting', 'stable diffusion', 'midjourney', 'dalle', 'imaging', 'computer vision', 'cv', 'segmentation', 'object detection']):
            return 'image'
        elif any(kw in combined_text for kw in ['video', 'movie', 'film', 'animation', 'motion graphics', 'editing', 'streaming']):
            return 'video'
        elif any(kw in combined_text for kw in ['audio', 'music', 'sound', 'voice', 'speech', 'podcast', 'tts', 'asr', 'sound effect']):
            return 'audio'
        elif any(kw in combined_text for kw in ['workflow', 'automation', 'nocode', 'no-code', 'automate', 'pipeline', 'agent', 'multi-agent', 'langchain', 'flow']):
            return 'workflow'
        elif any(kw in combined_text for kw in ['robot', 'robotics', 'hardware', 'ros', 'drone', 'manipulator']):
            return 'robotics'
        elif any(kw in combined_text for kw in ['multimodal', 'multi-modal', 'text-to-image', 'image-to-text', 'text-to-video', 'video-to-text', 'vision-language']):
            return 'multimodal'
        elif any(kw in combined_text for kw in ['text', 'nlp', 'writing', 'translation', 'summarization', 'chat', 'gpt', 'llm', 'language model', 'content generation', 'copywriting']):
            return 'text' # Explicitly check for text last as it can be broad
        else:
            # 默认为其他类别
            return 'other'
    
    def _extract_tags(self, title, selftext, comments):
        """
        根据帖子信息提取标签
        
        Args:
            title (str): 帖子标题
            selftext (str): 帖子内容
            comments (str): 评论内容
            
        Returns:
            list: 标签列表
        """
        combined_text = f"{title} {selftext} {comments}".lower()
        tags = []
        
        # 技术标签
        tech_keywords = {
            'gpt': ['gpt', 'openai'],
            'stable-diffusion': ['stable diffusion', 'sd'],
            'llama': ['llama', 'meta-llama'],
            'bert': ['bert'],
            'open-source': ['open source', 'open-source', 'github', 'opensource'],
            'api-available': ['api', 'rest api', 'graphql', 'sdk'],
            'cli': ['cli', 'command line'],
            'gui': ['gui', 'desktop app', 'ui'],
            'web-app': ['web app', 'online tool', 'webapp', 'browser-based'],
            'mobile-app': ['mobile app', 'ios', 'android'],
            'plugin': ['plugin', 'extension', 'addon'],
            'library': ['library', 'framework', 'package'],
            'research': ['research', 'paper', 'study', 'arxiv']
        }
        
        for tag, keywords in tech_keywords.items():
            if any(kw in combined_text for kw in keywords):
                tags.append(tag)
        
        # 功能标签
        function_keywords = {
            'summarization': ['summary', 'summarize', 'summarization'],
            'translation': ['translate', 'translation', 'multilingual'],
            'generation': ['generate', 'generation', 'creator'],
            'editing': ['edit', 'editing', 'modify'],
            'coding': ['code', 'programming', 'developer'],
            'analysis': ['analyze', 'analysis', 'analytics', 'data analysis', 'insights'],
            'search': ['search', 'retrieval', 'information retrieval'],
            'personalization': ['personalize', 'customization', 'recommendation'],
            'productivity': ['productivity', 'efficiency', 'workflow optimization'],
            'education': ['education', 'learning', 'teaching', 'edtech'],
            'developer-tool': ['developer tool', 'devtool', 'coding tool', 'ide']
        }
        
        for tag, keywords in function_keywords.items():
            if any(kw in combined_text for kw in keywords):
                tags.append(tag)
        
        return tags
        

def parse_args():
    parser = argparse.ArgumentParser(description='Reddit AI工具爬虫')
    parser.add_argument('--client_id', required=True, help='Reddit API客户端ID')
    parser.add_argument('--client_secret', required=True, help='Reddit API客户端密钥')
    parser.add_argument('--user_agent', default='Toolverse Reddit Crawler v1.1', help='User Agent字符串')
    parser.add_argument('--subreddits', nargs='+', default=['artificial', 'MachineLearning', 'OpenAI', 'StableDiffusion', 'AItools', 'LocalLLaMA', 'SingularityNET', 'GenerativeAI', 'AISafety'], 
                        help='要抓取的子版块列表')
    parser.add_argument('--limit', type=int, default=50, help='每个子版块抓取的帖子数量限制 (new listings limit will be 2x this)')
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    crawler = RedditCrawler(
        client_id=args.client_id,
        client_secret=args.client_secret,
        user_agent=args.user_agent,
        subreddits=args.subreddits,
        limit=args.limit
    )
    
    tools = crawler.crawl()
    logger.info(f"共抓取到 {len(tools)} 个工具")

if __name__ == "__main__":
    main() 