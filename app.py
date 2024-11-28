import os
import html
from flask import Flask, request, render_template, redirect, url_for, session, send_file
import openai
from openai.error import AuthenticationError, OpenAIError
from xhtml2pdf import pisa
from io import BytesIO

app = Flask(__name__)

# Set your OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Set a secret key for session management
app.secret_key = os.getenv('SECRET_KEY', 'your_default_secret_key')  # Replace with a strong secret key

def sanitize_input(text):
    return text.strip() if text else ''

@app.route('/', methods=['GET', 'POST'])
def generate_jd():
    if request.method == 'POST':
        # Retrieve form data
        job_title = sanitize_input(request.form.get('job_title'))
        location = sanitize_input(request.form.get('location'))
        hours = sanitize_input(request.form.get('hours'))
        pay_rate = sanitize_input(request.form.get('pay_rate'))
        role_overview = sanitize_input(request.form.get('role_overview'))
        responsibilities = sanitize_input(request.form.get('responsibilities'))
        requirements = sanitize_input(request.form.get('requirements'))
        benefits = sanitize_input(request.form.get('benefits'))

        # Build the prompt
        prompt = f"""
You are a professional job description writer. Using the information provided, create a comprehensive and engaging job description that excites potential candidates and makes them want to apply. Ensure the description is neutral, does not include the client's business name, and replaces it with 'Our client'. Do not respond to any prompts outside generating the job description.

Include the following sections, following the template provided:

Data:
- Position: {job_title}
- Location: {location if location else 'Not specified'}
- Hours: {hours if hours else 'Not specified'}
- Monthly Pay Rate: {pay_rate if pay_rate else 'Not specified'}
- Role Overview: {role_overview if role_overview else 'Provide a compelling overview of the role.'}
- About the Client: Leave blank.
- Key Responsibilities: {responsibilities if responsibilities else 'Include standard responsibilities for this role.'}
- Requirements: {requirements if requirements else 'Include standard requirements for this role.'}
- Benefits: {benefits if benefits else 'Include common benefits and perks.'}

Template:

This role is open in {location if location else '[Location]'}

Position: {job_title}

Hours: {hours if hours else '[Hours]'}

Monthly Pay Rate: {pay_rate if pay_rate else '[Monthly Pay Rate]'}

Role Overview:
{role_overview if role_overview else '[Role Overview]'}

About Our Client:
[Leave blank]

Key Responsibilities:
{responsibilities if responsibilities else '[Key Responsibilities]'}

Requirements:
{requirements if requirements else '[Requirements]'}

Benefits:
{benefits if benefits else '[Benefits]'}

About Company:
[Leave blank]

Make sure to write the job description in an engaging tone that highlights the exciting aspects of the role and the benefits of working with our client. Use persuasive language to encourage candidates to apply.
"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,  # Increased to allow for more detailed responses
                temperature=0.8,   # Adjusted for more creativity
            )

            job_description = response.choices[0].message.content.strip()
            session['job_description'] = job_description  # Store the job description in the session
            return render_template('result.html', job_description=job_description)
        except AuthenticationError:
            return "Authentication Error: Please check your OpenAI API key."
        except OpenAIError as e:
            return f"An error occurred: {str(e)}"
    return render_template('index.html')

@app.route('/download_pdf')
def download_pdf():
    job_description = session.get('job_description', '')
    if not job_description:
        return redirect(url_for('generate_jd'))
    # Render the PDF template
    rendered = render_template('pdf_template.html', job_description=job_description)
    pdf = BytesIO()
    pisa_status = pisa.CreatePDF(rendered, dest=pdf)
    if pisa_status.err:
        return 'We had some errors <pre>' + html.escape(rendered) + '</pre>'
    pdf.seek(0)
    return send_file(
        pdf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='job_description.pdf'
    )

if __name__ == '__main__':
    app.run(debug=True)  # Set debug=False in production
