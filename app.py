import os
import html
from flask import Flask, request, render_template, redirect, url_for, send_file, current_app
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
        hours = sanitize_input(request.form.get('hours'))
        industry = sanitize_input(request.form.get('industry'))
        responsibilities = sanitize_input(request.form.get('responsibilities'))
        requirements = sanitize_input(request.form.get('requirements'))
        benefits = sanitize_input(request.form.get('benefits'))

        # Neutral, non-country-specific, remote-work-focused default benefits
        default_benefits = ("Fully remote or flexible hybrid work arrangements, Flexible working hours, "
                            "Performance-based bonuses, Professional development opportunities, "
                            "Collaborative online team environment, Regular virtual team-building activities, "
                            "Supportive leadership with clear communication channels, Opportunities for career growth")

        if not benefits:
            benefits_input = 'Use a set of neutral, non-country-specific, remote-friendly benefits such as:\n' + default_benefits
        else:
            benefits_input = benefits

        # Build the prompt
        prompt = f"""
You are a professional job description writer. Using the information provided below, create a comprehensive and engaging job description that excites potential candidates and makes them want to apply.

**Instructions:**

- Organize the job description with clear headings corresponding to each section.
- Use HTML tags for formatting: <h2> for headings, <p> for paragraphs, and <ul><li> for bullet points.
- Start with "About the Company" at the beginning.
- Do not include the client's business name; instead, use 'Our client' or 'the company'.
- Present the 'Key Responsibilities' and 'Requirements' sections in bullet point format with at least 8 and 6 points, respectively.
- For the 'Benefits' section, if no benefits were provided by the user, use only neutral, non-country-specific, remote-work-friendly benefits.
- Keep the tone professional yet exciting.
- Do not include sections such as 'Role is open in XX' or 'Pay Rate'.

**Job Information:**

- **Position**: {job_title}
- **Hours**: {hours if hours else 'Not specified'}
- **Industry**: {industry if industry else 'Not specified'}
- **Key Responsibilities**: {responsibilities if responsibilities else 'Include standard responsibilities for this role.'}
- **Requirements**: {requirements if requirements else 'Include standard requirements for this role.'}
- **Benefits**: {benefits_input}

Please generate the job description accordingly, ensuring proper formatting with HTML tags and replacing any placeholders with the provided information.

Ensure the following structure:

1. **About the Company**: Generate based on the industry and make it generic without mentioning the company name.
2. **Role Overview**: Generate a compelling overview based on the position and industry.
3. **Key Responsibilities**: Use the input to generate at least 8 bullet points.
4. **Requirements**: Use the input to generate at least 6 bullet points.
5. **Benefits**: If no user-provided benefits, use the neutral, non-country-specific, remote-friendly benefits mentioned.

Do not include any other sections.
"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional job description writer specializing in creating engaging and persuasive job postings."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,  # Adjust as needed
                temperature=0.5,   # Lowered to increase consistency
            )

            job_description = response.choices[0].message.content.strip()
            return render_template('result.html', job_description=job_description)
        except AuthenticationError:
            return "Authentication Error: Please check your OpenAI API key."
        except OpenAIError as e:
            return f"An error occurred: {str(e)}"
    return render_template('index.html')

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    # Retrieve job_description from the form data
    job_description = request.form.get('job_description', '')
    if not job_description:
        return redirect(url_for('generate_jd'))

    # Set the logo filename
    logo_filename = 'Employmate_Logo_2.png'  # Ensure this matches your logo file name

    # Construct the logo path using forward slashes
    logo_path = os.path.join('static', logo_filename).replace('\\', '/')

    # Render the PDF template
    rendered = render_template('pdf_template.html', job_description=job_description, logo_path=logo_path)
    pdf = BytesIO()
    pisa_status = pisa.CreatePDF(
        rendered, dest=pdf, link_callback=link_callback
    )
    if pisa_status.err:
        return 'We had some errors <pre>' + html.escape(rendered) + '</pre>'
    pdf.seek(0)
    return send_file(
        pdf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='job_description.pdf'
    )

def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those resources
    """
    import os

    if uri.startswith('static/'):
        path = os.path.join(current_app.root_path, uri)
        return path
    else:
        return uri

if __name__ == '__main__':
    app.run(debug=True)  # Set debug=False in production
