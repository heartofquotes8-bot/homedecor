"""
Trend Finder Module
Pinterest trending topics + Google Trends se popular recipe topics dhundta hai
"""

import json
import time
import random
import requests
from datetime import datetime, timedelta
from pytrends.request import TrendReq
from bs4 import BeautifulSoup


class TrendFinder:
    def __init__(self, config: dict, context: dict):
        self.config = config
        self.context = context
        self.niche = config.get("niche", "Home Decor & Interiors")
        
        self.used_topics = []
        if self.context and "published_posts" in self.context:
            self.used_topics = [post.get("topic", "") for post in self.context["published_posts"].values()]

        # Home Decor niche ke liye seed keywords
        self.seed_keywords = [
            "modern minimalist bedroom ideas",
            "small living room decor",
            "aesthetic room decor",
            "bathroom remodeling ideas on a budget",
            "mid century modern furniture",
            "boho bedroom decor",
            "kitchen interior design trends",
            "indoor plants decoration",
            "diy home decor projects",
            "apartment balcony decorating ideas",
            "japandi interior design",
            "luxury living room inspiration",
            "cozy reading nook ideas",
            "home office setup ideas",
            "gallery wall layout ideas"
        ]

    def get_google_trends(self, num_topics=20) -> list:
        """Google Trends se trending recipe topics fetch karo"""
        print("📊 Google Trends se topics fetch kar raha hoon...")
        trending_topics = []

        try:
            pytrends = TrendReq(hl='en-US', tz=360)

            # Daily trending searches fetch karo
            try:
                trending_searches = pytrends.trending_searches(pn='united_states')
                daily_trends = trending_searches[0].tolist()[:10]
                trending_topics.extend(daily_trends)
                print(f"   ✅ Google daily trends: {len(daily_trends)} topics mila")
            except Exception as e:
                print(f"   ⚠️ Daily trends error: {e}")

            # Recipe related interest over time check karo
            recipe_related = []
            for keyword in random.sample(self.seed_keywords, min(5, len(self.seed_keywords))):
                try:
                    pytrends.build_payload([keyword], cat=71, timeframe='now 7-d', geo='US') # cat=71 is Food & Drink
                    related = pytrends.related_queries()
                    if keyword in related and related[keyword]['top'] is not None:
                        top_queries = related[keyword]['top']['query'].tolist()[:5]
                        recipe_related.extend(top_queries)
                    time.sleep(1)  # Rate limiting
                except Exception as e:
                    print(f"   ⚠️ Related queries error for '{keyword}': {e}")
                    continue

            trending_topics.extend(recipe_related)
            print(f"   ✅ Google related queries: {len(recipe_related)} topics mila")

        except Exception as e:
            print(f"   ❌ Google Trends error: {e}")

        # Fallback: pre-defined high-traffic topics
        fallback_topics = self._get_fallback_topics()
        trending_topics.extend(fallback_topics)

        # Filter aur deduplicate
        unique_topics = list(set([t.strip().lower() for t in trending_topics if len(t) > 3]))
        print(f"   ✅ Total unique topics: {len(unique_topics)}")

        return unique_topics[:num_topics]

    def get_pinterest_trending_categories(self) -> list:
        """Pinterest ke popular recipe categories scrape karo"""
        print("📌 Pinterest se trending categories fetch kar raha hoon...")
        topics = []

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        # Pinterest trending URLs for home decor category
        pinterest_urls = [
            "https://www.pinterest.com/ideas/home-decor/935531980842/",
            "https://www.pinterest.com/ideas/room-decor/943152285117/",
        ]

        for url in pinterest_urls:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'lxml')

                    # Title tags se topics extract karo
                    titles = soup.find_all(['h1', 'h2', 'h3', 'h4'], limit=30)
                    for title in titles:
                        text = title.get_text(strip=True)
                        if 5 < len(text) < 100:
                            topics.append(text)

                    print(f"   ✅ Pinterest se {len(topics)} topics mila")
                else:
                    print(f"   ⚠️ Pinterest status: {response.status_code}")
                time.sleep(2)
            except Exception as e:
                print(f"   ⚠️ Pinterest scraping error: {e}")

        return topics

    def _get_fallback_topics(self) -> list:
        """Agar APIs fail ho jain toh yeh evergreen topics use karo"""
        evergreen_decor_topics = [
            "10 Minimalist Bedroom Ideas for a Calming Space",
            "How to Decorate a Small Living Room to Look Bigger",
            "The Ultimate Guide to Japandi Interior Design",
            "5 Budget-Friendly Bathroom Makeover Ideas",
            "Cozy Boho Living Room Decor Inspiration",
            "Best Indoor Plants for Modern Home Decor",
            "DIY Wall Art Projects to Elevate Your Space",
            "Mid-Century Modern Furniture Essentials",
            "How to Create the Perfect Gallery Wall",
            "Luxury Kitchen Design Trends for 2026",
            "Aesthetic Apartment Balcony Decorating Ideas",
            "Creating a Cozy Reading Nook in a Small Space",
            "Home Office Setup Ideas for Maximum Productivity",
            "Earthy Tone Color Palettes for a Warm Home",
            "Scandinavian Interior Design Tips for Beginners"
        ]
        return evergreen_decor_topics

    def select_best_topic(self, num_topics=2) -> list:
        """
        Sab sources se topics collect karo aur best select karo
        Already used topics exclude karo
        """
        print("\n🔍 Best topics select kar raha hoon...")

        all_topics = []

        # Google Trends se
        google_topics = self.get_google_trends()
        all_topics.extend(google_topics)

        # Pinterest se
        pinterest_topics = self.get_pinterest_trending_categories()
        all_topics.extend(pinterest_topics)

        # Fallback topics
        fallback = self._get_fallback_topics()
        all_topics.extend(fallback)

        # Already published topics remove karo
        fresh_topics = []
        for topic in all_topics:
            topic_lower = topic.lower()
            already_used = any(
                used.lower() in topic_lower or topic_lower in used.lower()
                for used in self.used_topics
            )
            if not already_used and len(topic) > 10:
                fresh_topics.append(topic)

        if not fresh_topics:
            print("   ⚠️ Saare topics use ho gaye, fallback use kar raha hoon")
            fresh_topics = self._get_fallback_topics()

        # Random shuffle aur select karo
        random.shuffle(fresh_topics)
        selected = fresh_topics[:num_topics]

        print(f"   ✅ Selected topics: {selected}")
        return selected


if __name__ == "__main__":
    # Test karo
    with open("config.json") as f:
        config = json.load(f)
    with open("project_context.json") as f:
        context = json.load(f)

    finder = TrendFinder(config, context)
    topics = finder.select_best_topic(2)
    print(f"\n🎯 Final Topics:\n{topics}")
