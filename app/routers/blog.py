from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pathlib import Path
import markdown
from datetime import datetime

# Import posts from Python module (temporary fix for Railway)
from app.blog_posts import POSTS

router = APIRouter(prefix="/blog", tags=["Blog"])


def load_posts():
    """Load all blog posts from Python data."""
    return sorted(POSTS, key=lambda p: p['date'], reverse=True)


def render_post_html(post):
    """Render a single post as HTML."""
    html_content = markdown.markdown(post['content'])
    
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{post['title']} - Smith AI</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
            background: #fafafa;
        }}
        article {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        h3 {{
            color: #555;
        }}
        .meta {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-bottom: 30px;
        }}
        .back {{
            display: inline-block;
            margin-bottom: 20px;
            color: #3498db;
            text-decoration: none;
        }}
        .back:hover {{
            text-decoration: underline;
        }}
        ul {{
            list-style: none;
            padding-left: 0;
        }}
        ul li {{
            padding: 5px 0;
        }}
        ul li:before {{
            content: "• ";
            color: #3498db;
            font-weight: bold;
            margin-right: 8px;
        }}
        hr {{
            border: none;
            border-top: 2px solid #ecf0f1;
            margin: 30px 0;
        }}
        strong {{
            color: #2c3e50;
        }}
    </style>
</head>
<body>
    <a href="/blog" class="back">← Back to all posts</a>
    <article>
        <div class="meta">{post['date']}</div>
        {html_content}
    </article>
</body>
</html>
"""


def render_list_html(posts):
    """Render the blog post list with full content."""
    post_items = []
    for post in posts:
        # Render markdown to HTML
        html_content = markdown.markdown(post['content'])
        post_items.append(f"""
            <article class="post-card">
                <div class="meta">{post['date']}</div>
                {html_content}
            </article>
        """)
    
    posts_html = "\n".join(post_items) if post_items else "<p>No posts yet.</p>"
    
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blog - Smith AI</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
            background: #fafafa;
        }}
        header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        h1 {{
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .tagline {{
            color: #7f8c8d;
            font-size: 1.1em;
        }}
        .post-card {{
            background: white;
            padding: 40px;
            margin-bottom: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .post-card h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
            margin-top: 0;
        }}
        .post-card h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .post-card h3 {{
            color: #555;
        }}
        .post-card ul {{
            list-style: none;
            padding-left: 0;
        }}
        .post-card ul li {{
            padding: 5px 0;
        }}
        .post-card ul li:before {{
            content: "• ";
            color: #3498db;
            font-weight: bold;
            margin-right: 8px;
        }}
        .post-card hr {{
            border: none;
            border-top: 2px solid #ecf0f1;
            margin: 30px 0;
        }}
        .post-card strong {{
            color: #2c3e50;
        }}
        .meta {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-bottom: 20px;
        }}
        footer {{
            text-align: center;
            margin-top: 60px;
            padding-top: 20px;
            border-top: 2px solid #ecf0f1;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <header>
        <h1>🔺 Smith AI Blog</h1>
        <div class="tagline">Mathematical architecture in language, events, and time.</div>
    </header>
    
    <main>
        {posts_html}
    </main>
    
    <footer>
        <p>Mathematical observations. Observable. Real.</p>
    </footer>
</body>
</html>
"""


@router.get("/", response_class=HTMLResponse)
async def blog_list():
    """List all blog posts."""
    posts = load_posts()
    return render_list_html(posts)


@router.get("/{slug}", response_class=HTMLResponse)
async def blog_post(slug: str):
    """Display a single blog post."""
    posts = load_posts()
    
    # Find the post
    post = next((p for p in posts if p['slug'] == slug), None)
    
    if not post:
        return HTMLResponse(
            content="<h1>Post not found</h1><p><a href='/blog'>Back to blog</a></p>",
            status_code=404
        )
    
    return render_post_html(post)
