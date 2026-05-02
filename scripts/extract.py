#!/usr/bin/env python3
"""
Builder Digest · extract.py
三源统一提取：从 feed-x.json / feed-podcasts.json / feed-blogs.json 中提取内容，
输出统一格式的 JSON 到 data/tweets/YYYY-MM-DD/ 目录。
"""

import json
import os
import sys
from datetime import datetime

# --- 配置 ---
BASE_DIR = os.path.expanduser("~/.hermes/skills/builder-digest")
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")
TODAY = datetime.now().strftime("%Y-%m-%d")

SOURCES = [
    {
        "file": "feed-x.json",
        "type": "x",
        "platform": "X/Twitter",
        "list_key": "x",
        "items_key": "tweets",
        "item_fields": {
            "tweet_id": "id",
            "text": "text",
            "url": "url",
            "created_at": "createdAt",
            "likes": "likes",
            "retweets": "retweets",
        },
        "author_fields": {
            "author_name": "name",
            "author_handle": "handle",
            "bio": "bio",
        },
    },
    {
        "file": "feed-podcasts.json",
        "type": "podcast",
        "platform": "YouTube",
        "list_key": "podcasts",
        "items_key": None,
        "item_fields": {
            "tweet_id": "id",
            "text": "description",
            "url": "url",
            "created_at": "publishedAt",
            "likes": None,
            "retweets": None,
        },
        "author_fields": {
            "author_name": "channelTitle",
            "author_handle": "channelTitle",
            "bio": None,
        },
    },
    {
        "file": "feed-blogs.json",
        "type": "blog",
        "platform": "Blog",
        "list_key": "blogs",
        "items_key": None,
        "item_fields": {
            "tweet_id": "id",
            "text": "summary",
            "url": "url",
            "created_at": "publishedAt",
            "likes": None,
            "retweets": None,
        },
        "author_fields": {
            "author_name": "author",
            "author_handle": "source",
            "bio": None,
        },
    },
]

# --- 初始化 ---
output_dir = os.path.join(DATA_DIR, "tweets", TODAY)
os.makedirs(output_dir, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, f"extract-{TODAY}.log")
total_files = 0
stats = {}


def log(msg):
    """写日志：同时输出到屏幕和日志文件"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def safe_get(d, key):
    """安全取值，字段缺失返回空字符串"""
    if d is None or key is None:
        return ""
    return d.get(key, "")


def load_existing_ids():
    """加载已存在的 tweet_id，用于去重"""
    existing = set()
    if not os.path.exists(output_dir):
        return existing
    for fname in os.listdir(output_dir):
        if fname.endswith(".json"):
            fpath = os.path.join(output_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    tid = data.get("tweet_id", "")
                    if tid:
                        existing.add(tid)
            except (json.JSONDecodeError, KeyError):
                pass
    return existing


def extract_source(source_config, existing_ids):
    """提取单个数据源"""
    global total_files
    filepath = os.path.join(DATA_DIR, source_config["file"])

    if not os.path.exists(filepath):
        log(f"⚠️  {source_config['file']} 文件不存在，跳过")
        return 0

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get(source_config["list_key"], [])
    if not items:
        log(f"⚠️  {source_config['file']} 中 {source_config['list_key']} 为空（0 条记录）")
        return 0

    count = 0
    author_items_key = source_config.get("items_key")

    for author in items:
        author_info = {
            "author_name": safe_get(author, source_config["author_fields"]["author_name"]),
            "author_handle": safe_get(author, source_config["author_fields"]["author_handle"]),
            "bio": safe_get(author, source_config["author_fields"]["bio"]) if source_config["author_fields"]["bio"] else "",
        }

        entries = author[author_items_key] if author_items_key else [author]
        handle = author_info["author_handle"].replace("@", "").replace("/", "_") or author_info["author_name"].replace(" ", "_").lower()

        for i, item in enumerate(entries, 1):
            tweet_id = safe_get(item, source_config["item_fields"]["tweet_id"])

            if tweet_id and tweet_id in existing_ids:
                continue

            unified = {
                "source": source_config["type"],
                "platform": source_config["platform"],
                "tweet_id": tweet_id,
                "title": safe_get(item, source_config["item_fields"]["text"])[:60],
                "text": safe_get(item, source_config["item_fields"]["text"]),
                "url": safe_get(item, source_config["item_fields"]["url"]),
                "author_name": author_info["author_name"],
                "author_handle": author_info["author_handle"],
                "bio": author_info["bio"],
                "created_at": safe_get(item, source_config["item_fields"]["created_at"]),
                "likes": safe_get(item, source_config["item_fields"]["likes"]) if source_config["item_fields"]["likes"] else 0,
                "retweets": safe_get(item, source_config["item_fields"]["retweets"]) if source_config["item_fields"]["retweets"] else 0,
            }

            seq = 1
            while True:
                fname = f"{handle}-{seq:02d}.json"
                fpath = os.path.join(output_dir, fname)
                if not os.path.exists(fpath):
                    break
                seq += 1

            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(unified, f, ensure_ascii=False, indent=2)

            existing_ids.add(tweet_id)
            count += 1
            total_files += 1

    return count


# --- 主流程 ---
log("extract.py 开始执行")

existing_ids = load_existing_ids()
log(f"已加载 {len(existing_ids)} 条已存在的 tweet_id，将跳过重复")

for src in SOURCES:
    n = extract_source(src, existing_ids)
    stats[src["type"]] = n
    if n > 0:
        log(f"✅ {src['file']}：提取 {n} 条")
    elif n == 0 and os.path.exists(os.path.join(DATA_DIR, src["file"])):
        log(f"⚠️  {src['file']}：0 条新增")

# --- 汇总 ---
log("")
log(f"X 推文：{stats.get('x', 0)} 条，播客：{stats.get('podcast', 0)} 条，博客：{stats.get('blog', 0)} 条，共生成 {total_files} 个文件")
log(f"输出目录：{output_dir}")
