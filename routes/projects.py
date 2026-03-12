from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Project
from forms import ProjectForm

projects_bp = Blueprint('projects', __name__, url_prefix='/projects')


@projects_bp.route('/')
def list_projects():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('projects/list.html', projects=projects)


@projects_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_project():
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(
            name=form.name.data,
            description=form.description.data,
            owner_id=current_user.id
        )
        db.session.add(project)
        db.session.commit()
        flash('Project created successfully!', 'success')
        return redirect(url_for('projects.detail', project_id=project.id))

    return render_template('projects/create.html', form=form)


@projects_bp.route('/<int:project_id>')
def detail(project_id):
    project = Project.query.get_or_404(project_id)
    snippets = project.snippets.order_by(db.text('created_at DESC')).all()
    return render_template('projects/detail.html', project=project, snippets=snippets)
