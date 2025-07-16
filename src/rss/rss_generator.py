import os
import xml.etree.ElementTree as ET
from email.utils import formatdate
from pathlib import Path
from typing import List, Optional

from twikit.tweet import Tweet

class RSSGenerator:
    """
    RSSジェネレーター: ツイートのリストをRSS 2.0 XML形式に変換するクラス

    RSS Generator: A class that converts a list of tweets to RSS 2.0 XML format
    """

    def __init__(self, output_dir: str = "data/rss_feeds", max_tweets: int = 5):
        """
        RSSジェネレーターを初期化します

        Initialize the RSS generator

        Args:
            output_dir (str): RSS XMLファイルの出力ディレクトリ / Output directory for RSS XML files
            max_tweets (int): RSSフィードに含めるツイートの最大数 / Maximum number of tweets to include in the RSS feed
        """
        self.output_dir = output_dir
        self.max_tweets = min(5,max_tweets)

        # 出力ディレクトリが存在しない場合は作成
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

    def generate_rss(self, tweets: List[Tweet], screen_name: str) -> str:
        """
        ツイートのリストからRSS XMLを生成します
        URLのみを保存します

        Generate RSS XML from a list of tweets
        Only saves the URLs

        Args:
            tweets (List[Tweet]): ツイートのリスト / List of tweets
            screen_name (str): Twitterユーザー名 / Twitter username

        Returns:
            str: 生成されたRSS XML / Generated RSS XML
        """
        # 最大数に制限
        # Limit to maximum number
        tweets = tweets[:self.max_tweets]

        # RSSのルート要素を作成
        # Create root element for RSS
        rss = ET.Element("rss", version="2.0")

        # チャンネル要素を作成
        # Create channel element
        channel = ET.SubElement(rss, "channel")

        # チャンネルの基本情報を設定
        # Set basic channel information
        title = ET.SubElement(channel, "title")
        title.text = f"{screen_name} のツイート"

        link = ET.SubElement(channel, "link")
        link.text = f"https://twitter.com/{screen_name}"

        description = ET.SubElement(channel, "description")
        description.text = f"{screen_name} の最新ツイート"

        language = ET.SubElement(channel, "language")
        language.text = "ja"  # デフォルトは日本語 / Default is Japanese

        last_build_date = ET.SubElement(channel, "lastBuildDate")
        last_build_date.text = formatdate(localtime=True)

        # 各ツイートをRSSアイテムに変換 (URLのみ)
        # Convert each tweet to an RSS item (URL only)
        for tweet in tweets:
            item = ET.SubElement(channel, "item")

            # タイトル (ツイートID)
            # Title (tweet ID)
            item_title = ET.SubElement(item, "title")
            item_title.text = f"Tweet {tweet.id}"

            # リンク (ツイートのURL)
            # Link (tweet URL)
            item_link = ET.SubElement(item, "link")
            tweet_url = f"https://twitter.com/{screen_name}/status/{tweet.id}"
            item_link.text = tweet_url

            # GUID (ツイートのURL)
            # GUID (tweet URL)
            item_guid = ET.SubElement(item, "guid", isPermaLink="true")
            item_guid.text = tweet_url

        # XMLを文字列に変換
        # Convert XML to string
        ET.indent(rss)  # Python 3.9以上で利用可能 / Available in Python 3.9+
        xml_str = ET.tostring(rss, encoding="unicode")
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'

        return xml_declaration + xml_str

    def save_rss(self, tweets: List[Tweet], screen_name: str) -> str:
        """
        ツイートのリストからRSS XMLを生成し、ファイルに保存します

        Generate RSS XML from a list of tweets and save it to a file

        Args:
            tweets (List[Tweet]): ツイートのリスト / List of tweets
            screen_name (str): Twitterユーザー名 / Twitter username

        Returns:
            str: 保存されたファイルのパス / Path of the saved file
        """
        # RSS XMLを生成
        # Generate RSS XML
        xml_content = self.generate_rss(tweets, screen_name)

        # ファイルパスを作成
        # Create file path
        file_path = Path(self.output_dir) / f"{screen_name}.xml"

        # ファイルに保存
        # Save to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_content)

        return str(file_path)
