#!/usr/bin/env python3
"""测试关键词匹配"""
import re

query = "Python有哪些主要特点？"
content = "Python编程基础 Python是一种高级编程语言，由Guido van Rossum于1991年创建。"

query_keywords = set(re.findall(r'[\w\u4e00-\u9fff]+', query.lower()))
content_keywords = set(re.findall(r'[\w\u4e00-\u9fff]+', content.lower()))

print(f"查询关键词: {query_keywords}")
print(f"内容关键词: {content_keywords}")
print(f"交集: {query_keywords & content_keywords}")
print(f"是否有交集: {bool(query_keywords & content_keywords)}")