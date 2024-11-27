import os
from flask import Flask, request, render_template
import openai
from openai.error import AuthenticationError, OpenAIError

app = Flask(__name__)

# Set your OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

@app.route('/', methods=['GET', 'POST'])
def generate_jd():
    if request.method == 'POST':
        job_title = request.form['job_title']
        prompt = f"Write a detailed job description for a {job_title} position."

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.7,
            )

            job_description = response.choices[0].message.content.strip()
            return render_template('result.html', job_description=job_description)

        except AuthenticationError:
            return "Authentication Error: Please check your OpenAI API key."

        except OpenAIError as e:
            return f"An error occurred: {str(e)}"

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=False)
