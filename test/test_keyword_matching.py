#!/usr/bin/env python3
"""测试关键词匹配逻辑"""
import re

query = "查询一下我的成绩"
content = """==== Sheet: 全部GPA === 序号 学年学期 课程代码 课程序号 课程名称 课程类别 级别 学分 获得学分 有效 期末总评成绩 补考后总评成绩 系数 最终 绩点 提升绩点 考试性质 1.0 2023-2024-1 999W033N 999W033N.01 走进南航 社会科学与人文类 0...."""

print("测试关键词匹配逻辑")
print("=" * 60)
print(f"查询: {query}")
print(f"内容: {content[:100]}...")
print()

# 提取中文词
query_cn = set(re.findall(r'[\u4e00-\u9fff]+', query))
content_cn = set(re.findall(r'[\u4e00-\u9fff]+', content))

print(f"查询中文词: {query_cn}")
print(f"内容中文词: {content_cn}")
print(f"交集: {query_cn & content_cn}")
print(f"是否有交集: {bool(query_cn & content_cn)}")

# 提取英文单词
query_lower = query.lower()
content_lower = content.lower()
query_words = set(re.findall(r'\b[a-z]+\b', query_lower))
content_words = set(re.findall(r'\b[a-z]+\b', content_lower))

print()
print(f"查询英文词: {query_words}")
print(f"内容英文词: {content_words}")
print(f"交集: {query_words & content_words}")
print(f"是否有交集: {bool(query_words & content_words)}")