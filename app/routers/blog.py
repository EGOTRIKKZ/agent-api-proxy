from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pathlib import Path
import markdown
from datetime import datetime

router = APIRouter(prefix="/blog", tags=["Blog"])

BLOG_DIR = Path(__file__).parent.parent.parent / "blog"


def load_posts():
    """Load all blog posts from the blog directory."""
    posts = []
    
    if not BLOG_DIR.exists():
        return posts
    
    for md_file in sorted(BLOG_DIR.glob("*.md"), reverse=True):
        # Parse filename: YYYY-MM-DD-slug.md
        parts = md_file.stem.split("-", 3)
        if len(parts) >= 4:
            year, month, day, slug = parts[0], parts[1], parts[2], parts[3]
            date = f"{year}-{month}-{day}"
            
            # Read content
            content = md_file.read_text(encoding='utf-8')
            
            # Extract title from first heading
            title = "Untitled"
            for line in content.split('\n'):
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
            
            posts.append({
                'slug': md_file.stem,
                'title': title,
                'date': date,
                'content': content,
                'path': md_file
            })
    
    return posts


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
    """Render the blog post list."""
    post_items = []
    for post in posts:
        post_items.append(f"""
            <div class="post-card">
                <h2><a href="/blog/{post['slug']}">{post['title']}</a></h2>
                <div class="meta">{post['date']}</div>
            </div>
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
            padding: 30px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        .post-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        .post-card h2 {{
            margin: 0 0 10px 0;
        }}
        .post-card h2 a {{
            color: #2c3e50;
            text-decoration: none;
        }}
        .post-card h2 a:hover {{
            color: #3498db;
        }}
        .meta {{
            color: #7f8c8d;
            font-size: 0.9em;
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
