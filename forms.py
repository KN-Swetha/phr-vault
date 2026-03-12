from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, TextAreaField, SelectField, FileField, DateField
from wtforms.validators import DataRequired, Email, Length

class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Phone")
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")

class ProfileForm(FlaskForm):
    age = IntegerField("Age")
    gender = SelectField("Gender", choices=[("", "Select"), ("Male","Male"), ("Female","Female"), ("Other","Other")])
    blood_group = StringField("Blood Group")
    known_conditions = TextAreaField("Known Conditions")
    address = TextAreaField("Address")
    submit = SubmitField("Update Profile")

class UploadRecordForm(FlaskForm):
    file = FileField("File", validators=[DataRequired()])
    file_type = SelectField("Type", choices=[("Prescription","Prescription"), ("Lab","Lab"), ("Scan","Scan"), ("Discharge","Discharge"), ("Vaccination","Vaccination")])
    doctor_name = StringField("Doctor Name")
    hospital_name = StringField("Hospital / Clinic")
    visit_date = DateField("Visit Date", format='%Y-%m-%d')
    notes = TextAreaField("Notes")
    submit = SubmitField("Upload")
