import requests
from bs4 import BeautifulSoup
from collections import Counter
import re
import nltk
from nltk.corpus import stopwords

# Download stopwords once - comment out after first run
nltk.download('stopwords')

def get_user_posts_and_comments(username):
    headers = {"User-Agent": "myTestBot/1.0"}
    posts = []
    comments = []

    # Get posts
    post_url = f"https://old.reddit.com/user/{username}/submitted/"
    post_page = requests.get(post_url, headers=headers)
    soup = BeautifulSoup(post_page.text, "html.parser")
    post_blocks = soup.find_all("div", class_="thing")

    for post in post_blocks:
        title_tag = post.find("a", class_="title")
        if title_tag:
            posts.append({
                "text": title_tag.text.strip(),
                "link": title_tag['href'] if title_tag['href'].startswith("http") else "https://reddit.com" + title_tag['href']
            })

    # Get comments
    comment_url = f"https://old.reddit.com/user/{username}/comments/"
    comment_page = requests.get(comment_url, headers=headers)
    soup2 = BeautifulSoup(comment_page.text, "html.parser")
    comment_blocks = soup2.find_all("div", class_="md")

    for block in comment_blocks:
        comment_text = block.text.strip()
        if comment_text:
            parent = block.find_parent("div", class_="thing")
            if parent:
                link_tag = parent.find("a", class_="bylink")
                if link_tag:
                    comments.append({
                        "text": comment_text,
                        "link": "https://reddit.com" + link_tag['href']
                    })

    return posts, comments

def analyze_text(data):
    stopwords_set = set(stopwords.words('english'))

    # Add Reddit-specific stopwords
    reddit_extra = {"im", "r", "t", "serious", "s", "also", "dont", "got", "just", "like",
                    "think", "people", "know", "about", "can", "have", "should", "would",
                    "could", "does", "did", "why", "when", "where", "who", "how", "its",
                    "us", "our", "them"}

    stopwords_set = stopwords_set.union(reddit_extra)

    words_list = []
    total_length = 0

    for item in data:
        words = re.findall(r'\b\w+\b', item["text"].lower())
        filtered = [word for word in words if word not in stopwords_set]
        words_list.extend(filtered)
        total_length += len(item["text"].split())

    top_words = Counter(words_list).most_common(5)

    # Writing Style
    average_length = total_length / len(data) if data else 0
    if average_length < 10:
        style = "Short"
    elif average_length < 20:
        style = "Medium"
    else:
        style = "Long"

    # Sentiment
    positive_words = ["good", "great", "happy", "love", "like", "awesome"]
    negative_words = ["bad", "sad", "angry", "hate", "dislike", "terrible"]

    pos_count = sum(1 for word in words_list if word in positive_words)
    neg_count = sum(1 for word in words_list if word in negative_words)

    if pos_count > neg_count:
        mood = "Positive"
    elif neg_count > pos_count:
        mood = "Negative"
    else:
        mood = "Neutral"

    return top_words, style, mood

def save_persona_file(username, words, style, mood, data):
    file_name = f"{username}_persona.txt"
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(f"User Persona Report for: {username}\n\n")
        file.write("Top Interests:\n")
        for word, count in words:
            file.write(f"- {word} ({count} times)\n")
            for item in data:
                if word in item["text"].lower():
                    file.write(f"  • {item['link']}\n")
                    break
        file.write(f"\nWriting Style: {style}\n")
        file.write(f"Sentiment: {mood}\n")
    print(f"\n✅ Persona saved as {file_name}")

if __name__ == "__main__":
    url = input("Enter Reddit user profile URL: ").strip()
    username = url.rstrip('/').split('/')[-1]

    print(f"\n🔍 Collecting posts and comments for '{username}'...")
    posts, comments = get_user_posts_and_comments(username)

    if not posts and not comments:
        print("❌ No posts or comments found.")
    else:
        all_data = posts + comments
        words, style, mood = analyze_text(all_data)
        save_persona_file(username, words, style, mood, all_data)
