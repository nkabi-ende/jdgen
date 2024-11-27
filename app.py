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

@app.route('/', methods=['GET', 'POST'])
def generate_jd():
    if request.method == 'POST':
        job_title = request.form['job_title']
        company_name = request.form.get('company_name', 'the company')
        responsibilities = request.form.get('responsibilities', '')
        benefits = request.form.get('benefits', '')

        # Build the prompt dynamically based on user inputs
        prompt = f"Write a detailed job description for a {job_title} position at {company_name}."
        if responsibilities.strip():
            prompt += f" The key responsibilities include: {responsibilities}."
        else:
            prompt += " Include the typical responsibilities and qualifications for this role."
        if benefits.strip():
            prompt += f" Also, highlight the following benefits: {benefits}."
        else:
            prompt += " Mention common benefits and perks offered by the company."

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7,
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
