from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange
from models import User, InviteCode


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')


class RegisterForm(FlaskForm):
    invite_code = StringField('Invite Code', validators=[DataRequired(), Length(min=1, max=40)])
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm Password',
                              validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Create Account')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_invite_code(self, field):
        code = InviteCode.query.filter_by(code=field.data.strip()).first()
        if not code:
            raise ValidationError('Invalid invite code.')
        if not code.is_active:
            raise ValidationError('This invite code has been deactivated.')
        if code.used_by:
            raise ValidationError('This invite code has already been used.')


class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired(), Length(min=1, max=140)])
    description = TextAreaField('Description', validators=[Length(max=2000)])
    submit = SubmitField('Create Project')


LANGUAGE_CHOICES = [
    ('python', 'Python'), ('javascript', 'JavaScript'), ('typescript', 'TypeScript'),
    ('java', 'Java'), ('csharp', 'C#'), ('cpp', 'C++'), ('c', 'C'),
    ('go', 'Go'), ('rust', 'Rust'), ('ruby', 'Ruby'), ('php', 'PHP'),
    ('swift', 'Swift'), ('kotlin', 'Kotlin'), ('html', 'HTML'),
    ('css', 'CSS'), ('sql', 'SQL'), ('bash', 'Bash'), ('json', 'JSON'),
    ('yaml', 'YAML'), ('xml', 'XML'), ('markdown', 'Markdown'),
]


class CodeSnippetForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=140)])
    language = SelectField('Language', choices=LANGUAGE_CHOICES, default='python')
    description = TextAreaField('Description', validators=[Length(max=2000)])
    code = TextAreaField('Code', validators=[DataRequired()])
    submit = SubmitField('Share Snippet')


class ClassNoteForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Save Note')


class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired(), Length(min=1, max=5000)])
    submit = SubmitField('Post Comment')


class InviteCodeForm(FlaskForm):
    count = IntegerField('Number of Codes', validators=[DataRequired(), NumberRange(min=1, max=50)], default=1)
    submit = SubmitField('Generate Codes')
