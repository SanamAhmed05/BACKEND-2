from flask import Blueprint, request, jsonify, render_template_string
from flask_cors import cross_origin
from src.models.blog import BlogPost
from src.models.user import db
from datetime import datetime
import os

blog_bp = Blueprint('blog', __name__)

# Blog listing page template
BLOG_LIST_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VideoGrab Blog</title>
    <link rel="stylesheet" href="/styles.css">
    <style>
        .blog-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        .blog-header {
            text-align: center;
            margin-bottom: 3rem;
        }
        .blog-header h1 {
            color: #fff;
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }
        .blog-header p {
            color: #b0b0b0;
            font-size: 1.1rem;
        }
        .blog-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 2rem;
            margin-bottom: 3rem;
        }
        .blog-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .blog-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }
        .blog-card h3 {
            color: #fff;
            font-size: 1.3rem;
            margin-bottom: 0.5rem;
        }
        .blog-card .meta {
            color: #888;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }
        .blog-card .excerpt {
            color: #ccc;
            line-height: 1.6;
            margin-bottom: 1rem;
        }
        .blog-card .tags {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }
        .tag {
            background: rgba(74, 144, 226, 0.2);
            color: #4a90e2;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
        }
        .read-more {
            color: #4a90e2;
            text-decoration: none;
            font-weight: 500;
        }
        .read-more:hover {
            text-decoration: underline;
        }
        .create-post-btn {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 50px;
            padding: 1rem 2rem;
            font-size: 1rem;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease;
        }
        .create-post-btn:hover {
            transform: scale(1.05);
        }
        .no-posts {
            text-align: center;
            color: #888;
            font-size: 1.1rem;
            margin: 3rem 0;
        }
    </style>
</head>
<body>
    <nav style="padding: 1rem 2rem; background: rgba(0, 0, 0, 0.3);">
        <div style="display: flex; justify-content: space-between; align-items: center; max-width: 1200px; margin: 0 auto;">
            <a href="/" style="color: #4a90e2; text-decoration: none; font-size: 1.5rem; font-weight: bold;">
                🎬 VideoGrab
            </a>
            <div>
                <a href="/" style="color: #ccc; text-decoration: none; margin-right: 2rem;">Home</a>
                <a href="/blog" style="color: #4a90e2; text-decoration: none;">Blog</a>
            </div>
        </div>
    </nav>

    <div class="blog-container">
        <div class="blog-header">
            <h1>VideoGrab Blog</h1>
            <p>Tips, tutorials, and updates about video downloading</p>
        </div>

        <div class="blog-grid" id="blogGrid">
            <!-- Blog posts will be loaded here -->
        </div>

        <div class="no-posts" id="noPosts" style="display: none;">
            <p>No blog posts yet. Be the first to create one!</p>
        </div>
    </div>

    <button class="create-post-btn" onclick="window.location.href='/blog/create'">
        ✏️ Write Post
    </button>

    <script>
        async function loadBlogPosts() {
            try {
                const response = await fetch('/api/blog/posts');
                const posts = await response.json();
                
                const blogGrid = document.getElementById('blogGrid');
                const noPosts = document.getElementById('noPosts');
                
                if (posts.length === 0) {
                    noPosts.style.display = 'block';
                    return;
                }
                
                blogGrid.innerHTML = posts.map(post => `
                    <div class="blog-card">
                        <h3>${post.title}</h3>
                        <div class="meta">
                            By ${post.author} • ${new Date(post.created_at).toLocaleDateString()}
                        </div>
                        <div class="excerpt">${post.excerpt || post.content.substring(0, 150) + '...'}</div>
                        ${post.tags.length > 0 ? `
                            <div class="tags">
                                ${post.tags.map(tag => `<span class="tag">${tag.trim()}</span>`).join('')}
                            </div>
                        ` : ''}
                        <a href="/blog/post/${post.id}" class="read-more">Read More →</a>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error loading blog posts:', error);
            }
        }
        
        loadBlogPosts();
    </script>
</body>
</html>
"""

# Blog post creation page template
BLOG_CREATE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Create Blog Post - VideoGrab</title>
    <link rel="stylesheet" href="/styles.css">
    <style>
        .create-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
        }
        .create-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .create-header h1 {
            color: #fff;
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        .form-group label {
            display: block;
            color: #fff;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }
        .form-group input,
        .form-group textarea {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.05);
            color: #fff;
            font-size: 1rem;
        }
        .form-group textarea {
            min-height: 300px;
            resize: vertical;
        }
        .form-group input:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #4a90e2;
            box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2);
        }
        .form-actions {
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-top: 2rem;
        }
        .btn {
            padding: 0.75rem 2rem;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-secondary {
            background: rgba(255, 255, 255, 0.1);
            color: #ccc;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        .success-message {
            background: rgba(76, 175, 80, 0.2);
            border: 1px solid #4caf50;
            color: #4caf50;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            display: none;
        }
        .error-message {
            background: rgba(244, 67, 54, 0.2);
            border: 1px solid #f44336;
            color: #f44336;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            display: none;
        }
    </style>
</head>
<body>
    <nav style="padding: 1rem 2rem; background: rgba(0, 0, 0, 0.3);">
        <div style="display: flex; justify-content: space-between; align-items: center; max-width: 1200px; margin: 0 auto;">
            <a href="/" style="color: #4a90e2; text-decoration: none; font-size: 1.5rem; font-weight: bold;">
                🎬 VideoGrab
            </a>
            <div>
                <a href="/" style="color: #ccc; text-decoration: none; margin-right: 2rem;">Home</a>
                <a href="/blog" style="color: #ccc; text-decoration: none;">Blog</a>
            </div>
        </div>
    </nav>

    <div class="create-container">
        <div class="create-header">
            <h1>Create New Blog Post</h1>
        </div>

        <div class="success-message" id="successMessage">
            Blog post created successfully!
        </div>
        
        <div class="error-message" id="errorMessage">
            Error creating blog post. Please try again.
        </div>

        <form id="blogForm">
            <div class="form-group">
                <label for="title">Title *</label>
                <input type="text" id="title" name="title" required>
            </div>

            <div class="form-group">
                <label for="author">Author *</label>
                <input type="text" id="author" name="author" required>
            </div>

            <div class="form-group">
                <label for="excerpt">Excerpt (Optional)</label>
                <input type="text" id="excerpt" name="excerpt" placeholder="Brief description of the post">
            </div>

            <div class="form-group">
                <label for="tags">Tags (Optional)</label>
                <input type="text" id="tags" name="tags" placeholder="Comma-separated tags (e.g., tutorial, tips, youtube)">
            </div>

            <div class="form-group">
                <label for="content">Content *</label>
                <textarea id="content" name="content" required placeholder="Write your blog post content here..."></textarea>
            </div>

            <div class="form-actions">
                <button type="button" class="btn btn-secondary" onclick="window.location.href='/blog'">
                    Cancel
                </button>
                <button type="submit" class="btn btn-primary">
                    Publish Post
                </button>
            </div>
        </form>
    </div>

    <script>
        document.getElementById('blogForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const postData = {
                title: formData.get('title'),
                author: formData.get('author'),
                content: formData.get('content'),
                excerpt: formData.get('excerpt'),
                tags: formData.get('tags')
            };
            
            try {
                const response = await fetch('/api/blog/posts', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(postData)
                });
                
                if (response.ok) {
                    document.getElementById('successMessage').style.display = 'block';
                    document.getElementById('errorMessage').style.display = 'none';
                    e.target.reset();
                    setTimeout(() => {
                        window.location.href = '/blog';
                    }, 2000);
                } else {
                    throw new Error('Failed to create post');
                }
            } catch (error) {
                document.getElementById('errorMessage').style.display = 'block';
                document.getElementById('successMessage').style.display = 'none';
                console.error('Error creating post:', error);
            }
        });
    </script>
</body>
</html>
"""

# Blog post view template
BLOG_POST_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ post.title }} - VideoGrab Blog</title>
    <link rel="stylesheet" href="/styles.css">
    <style>
        .post-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
        }
        .post-header {
            margin-bottom: 2rem;
            text-align: center;
        }
        .post-title {
            color: #fff;
            font-size: 2.5rem;
            margin-bottom: 1rem;
            line-height: 1.2;
        }
        .post-meta {
            color: #888;
            font-size: 1rem;
            margin-bottom: 1rem;
        }
        .post-tags {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 2rem;
        }
        .tag {
            background: rgba(74, 144, 226, 0.2);
            color: #4a90e2;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.9rem;
        }
        .post-content {
            color: #ccc;
            line-height: 1.8;
            font-size: 1.1rem;
        }
        .post-content p {
            margin-bottom: 1.5rem;
        }
        .post-content h1, .post-content h2, .post-content h3 {
            color: #fff;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }
        .back-link {
            display: inline-block;
            color: #4a90e2;
            text-decoration: none;
            margin-bottom: 2rem;
            font-weight: 500;
        }
        .back-link:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <nav style="padding: 1rem 2rem; background: rgba(0, 0, 0, 0.3);">
        <div style="display: flex; justify-content: space-between; align-items: center; max-width: 1200px; margin: 0 auto;">
            <a href="/" style="color: #4a90e2; text-decoration: none; font-size: 1.5rem; font-weight: bold;">
                🎬 VideoGrab
            </a>
            <div>
                <a href="/" style="color: #ccc; text-decoration: none; margin-right: 2rem;">Home</a>
                <a href="/blog" style="color: #4a90e2; text-decoration: none;">Blog</a>
            </div>
        </div>
    </nav>

    <div class="post-container">
        <a href="/blog" class="back-link">← Back to Blog</a>
        
        <div class="post-header">
            <h1 class="post-title">{{ post.title }}</h1>
            <div class="post-meta">
                By {{ post.author }} • {{ post.created_at.strftime('%B %d, %Y') }}
            </div>
            {% if post.tags %}
            <div class="post-tags">
                {% for tag in post.tags.split(',') %}
                <span class="tag">{{ tag.strip() }}</span>
                {% endfor %}
            </div>
            {% endif %}
        </div>

        <div class="post-content">
            {{ post.content | replace('\n', '<br>') | safe }}
        </div>
    </div>
</body>
</html>
"""

@blog_bp.route('/blog')
def blog_list():
    """Display blog listing page"""
    return render_template_string(BLOG_LIST_TEMPLATE)

@blog_bp.route('/blog/create')
def blog_create():
    """Display blog creation page"""
    return render_template_string(BLOG_CREATE_TEMPLATE)

@blog_bp.route('/blog/post/<int:post_id>')
def blog_post(post_id):
    """Display individual blog post"""
    post = BlogPost.query.get_or_404(post_id)
    return render_template_string(BLOG_POST_TEMPLATE, post=post)

@blog_bp.route('/api/blog/posts', methods=['GET'])
@cross_origin()
def get_blog_posts():
    """Get all published blog posts"""
    try:
        posts = BlogPost.query.filter_by(is_published=True).order_by(BlogPost.created_at.desc()).all()
        return jsonify([post.to_dict() for post in posts])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blog_bp.route('/api/blog/posts', methods=['POST'])
@cross_origin()
def create_blog_post():
    """Create a new blog post"""
    try:
        data = request.get_json()
        
        if not data.get('title') or not data.get('content') or not data.get('author'):
            return jsonify({'error': 'Title, content, and author are required'}), 400
        
        post = BlogPost(
            title=data['title'],
            content=data['content'],
            author=data['author'],
            excerpt=data.get('excerpt', ''),
            tags=data.get('tags', ''),
            is_published=data.get('is_published', True)
        )
        
        db.session.add(post)
        db.session.commit()
        
        return jsonify(post.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@blog_bp.route('/api/blog/posts/<int:post_id>', methods=['GET'])
@cross_origin()
def get_blog_post(post_id):
    """Get a specific blog post"""
    try:
        post = BlogPost.query.get_or_404(post_id)
        return jsonify(post.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blog_bp.route('/api/blog/posts/<int:post_id>', methods=['PUT'])
@cross_origin()
def update_blog_post(post_id):
    """Update a blog post"""
    try:
        post = BlogPost.query.get_or_404(post_id)
        data = request.get_json()
        
        if 'title' in data:
            post.title = data['title']
        if 'content' in data:
            post.content = data['content']
        if 'author' in data:
            post.author = data['author']
        if 'excerpt' in data:
            post.excerpt = data['excerpt']
        if 'tags' in data:
            post.tags = data['tags']
        if 'is_published' in data:
            post.is_published = data['is_published']
        
        post.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(post.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@blog_bp.route('/api/blog/posts/<int:post_id>', methods=['DELETE'])
@cross_origin()
def delete_blog_post(post_id):
    """Delete a blog post"""
    try:
        post = BlogPost.query.get_or_404(post_id)
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({'message': 'Post deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

