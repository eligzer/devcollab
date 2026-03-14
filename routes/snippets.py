from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from markupsafe import Markup
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter
from sqlalchemy.orm import joinedload
from models import db, Project, CodeSnippet, Comment, Notification, User
from forms import CodeSnippetForm, CommentForm
from utils import log_activity

snippets_bp = Blueprint('snippets', __name__)


def highlight_code(code, language):
    """Return syntax-highlighted HTML for a code string."""
    try:
        lexer = get_lexer_by_name(language, stripall=True)
    except Exception:
        lexer = TextLexer()
    formatter = HtmlFormatter(
        linenos=True,
        cssclass='highlight',
        style='monokai'
    )
    return Markup(highlight(code, lexer, formatter))


def get_highlight_css():
    """Return the Pygments CSS for the monokai theme."""
    return HtmlFormatter(style='monokai').get_style_defs('.highlight')


@snippets_bp.route('/projects/<int:project_id>/snippets/new', methods=['GET', 'POST'])
@login_required
def create_snippet(project_id):
    project = Project.query.get_or_404(project_id)
    form = CodeSnippetForm()
    if form.validate_on_submit():
        snippet = CodeSnippet(
            title=form.title.data,
            code=form.code.data,
            language=form.language.data,
            description=form.description.data,
            project_id=project.id,
            author_id=current_user.id
        )
        db.session.add(snippet)
        db.session.flush()
        log_activity(current_user.id, 'create_snippet', 'snippet', snippet.id,
                     f'{current_user.username} created a new snippet "{snippet.title}" in project {project.name}')
        db.session.commit()
        flash('Code snippet shared!', 'success')
        return redirect(url_for('snippets.detail', snippet_id=snippet.id))

    return render_template('snippets/create.html', form=form, project=project)


@snippets_bp.route('/snippets/<int:snippet_id>')
def detail(snippet_id):
    snippet = CodeSnippet.query.options(
        joinedload(CodeSnippet.comments).joinedload(Comment.author),
        joinedload(CodeSnippet.comments).joinedload(Comment.likes)
    ).get_or_404(snippet_id)
    highlighted = highlight_code(snippet.code, snippet.language)
    css = get_highlight_css()
    comments = sorted(snippet.comments, key=lambda c: c.created_at)
    comment_form = CommentForm()
    return render_template('snippets/detail.html', snippet=snippet,
                           highlighted_code=highlighted, highlight_css=css,
                           comments=comments, comment_form=comment_form)


@snippets_bp.route('/snippets/<int:snippet_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_snippet(snippet_id):
    snippet = CodeSnippet.query.get_or_404(snippet_id)
    form = CodeSnippetForm(obj=snippet)

    if form.validate_on_submit():
        snippet.title = form.title.data
        snippet.code = form.code.data
        snippet.language = form.language.data
        snippet.description = form.description.data
        snippet.edited_by = current_user.username
        snippet.updated_at = datetime.now(timezone.utc)
        log_activity(current_user.id, 'edit_snippet', 'snippet', snippet.id,
                     f'{current_user.username} edited the snippet "{snippet.title}"')
        db.session.commit()
        flash('Snippet updated successfully!', 'success')
        return redirect(url_for('snippets.detail', snippet_id=snippet.id))

    return render_template('snippets/edit.html', form=form, snippet=snippet)


@snippets_bp.route('/snippets/<int:snippet_id>/delete', methods=['POST'])
@login_required
def delete_snippet(snippet_id):
    snippet = CodeSnippet.query.get_or_404(snippet_id)
    
    if snippet.author_id != current_user.id and not current_user.is_admin:
        flash('Permission denied.', 'danger')
        return redirect(url_for('snippets.detail', snippet_id=snippet.id))

    project_id = snippet.project_id
    db.session.delete(snippet)
    db.session.commit()
    flash('Snippet deleted.', 'info')
    
    return redirect(url_for('projects.detail', project_id=project_id))


@snippets_bp.route('/snippets/<int:snippet_id>/comment', methods=['POST'])
@login_required
def comment_snippet(snippet_id):
    snippet = CodeSnippet.query.get_or_404(snippet_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            author_id=current_user.id,
            snippet_id=snippet.id
        )
        db.session.add(comment)
        db.session.flush()

        if snippet.author_id != current_user.id:
            notif = Notification(
                user_id=snippet.author_id,
                message=f'{current_user.username} commented on your snippet "{snippet.title}"',
                link=url_for('snippets.detail', snippet_id=snippet.id)
            )
            db.session.add(notif)
        log_activity(current_user.id, 'comment', 'comment', comment.id,
                     f'{current_user.username} commented on snippet "{snippet.title}"')
        db.session.commit()
        flash('Comment posted!', 'success')
    return redirect(url_for('snippets.detail', snippet_id=snippet.id))


@snippets_bp.route('/snippets/<int:snippet_id>/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(snippet_id, comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    if comment.author_id != current_user.id and not current_user.is_admin:
        flash('Permission denied.', 'danger')
        return redirect(url_for('snippets.detail', snippet_id=snippet_id))

    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted.', 'info')
    
    return redirect(url_for('snippets.detail', snippet_id=snippet_id))
