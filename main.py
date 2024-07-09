import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time as time_module
import spacy
from flask import Flask, request, jsonify

app = Flask(__name__)

nlp = spacy.load("en_core_web_sm")

# Initialize the OpenAI client
api_key = ''
client = OpenAI(api_key=api_key)
# openai.api_key = ''

    
# Load the data from the Excel spreadsheet into the course_data variable
course_data = pd.read_excel("course_info_with_date_and_time.xlsx")
event_data = pd.read_excel("event_info_With_date_and_time.xlsx")



# Define the chatbot endpoint
@app.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.json
    question = data.get('question')
    answer = answer_query(question, course_data, event_data)
    return jsonify({'answer': answer})

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)

def answer_course_question(question, course_data):
    # Extract topics from the question
    topics = extract_keywords_from_question(question)

    # Find courses that match the topics
    matching_courses = course_data[course_data['Topics'].str.contains('|'.join(topics), case=False, na=False)]

    # Format the input for OpenAI's API
    if not matching_courses.empty:
        # Convert all relevant columns to string
        matching_courses = matching_courses.astype({'Course Code': 'str', 'Course Name': 'str', 'Units': 'str', 'Day': 'str', 'Time': 'str', 'Location': 'str'})

        course_list = '\n'.join(matching_courses['Course Code'] + ' - ' + matching_courses['Course Name'] +
                                ' (' + matching_courses['Units'] + ' units)' +
                                ', Day: ' + matching_courses['Day'] +
                                ', Time: ' + matching_courses['Time'] +
                                ', Location: ' + matching_courses['Location'])
        messages = [
            {"role": "system", "content": "You are a helpful student advisor at a university providing course recommendations based on the course list provided. Be conversational but provide some options for the student, come across as a human"},
            {"role": "user", "content": f"Question: {question}"},
            {"role": "assistant", "content": f"Relevant Courses:\n{course_list}"}
        ]
    else:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Question: {question}"},
            {"role": "assistant", "content": "No relevant courses found."}
        ]

    # Use OpenAI's API to generate a recommendation
    response = client.chat.completions.create(
        messages=messages,
        model="gpt-3.5-turbo",
    )
    return response.choices[0].message.content

def answer_event_question(question, event_data):
    # Extract keywords from the question
    topics = extract_keywords_from_question(question)

    # Find events that match the topics
    matching_events = event_data[event_data['Event Description'].str.contains('|'.join(topics), case=False, na=False)]

    # Format the input for OpenAI's API
    if not matching_events.empty:
        # Convert all relevant columns to string
        matching_events = matching_events.astype({'Event Title': 'str', 'Event Date And Time': 'str', 'Event Description': 'str'})

        event_list = '\n'.join(matching_events['Event Title'] +
                               ' - Date and Time: ' + matching_events['Event Date And Time'] +
                               ', Description: ' + matching_events['Event Description'])
        messages = [
            {"role": "system", "content": "You are a helpful student advisor at a university providing event recommendations based on the event list provided. Be conversational but provide some options for the student, come across as a human"},
            {"role": "user", "content": f"Question: {question}"},
            {"role": "assistant", "content": f"Upcoming Events:\n{event_list}"}
        ]
    else:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Question: {question}"},
            {"role": "assistant", "content": "No relevant events found."}
        ]

    # Use OpenAI's API to generate a recommendation
    response = client.chat.completions.create(
        messages=messages,
        model="gpt-3.5-turbo",
    )
    return response.choices[0].message.content

    
def answer_query(question, course_data, event_data):
    # Check if the question is about courses or events
    if "class" in question.lower() or "course" in question.lower():
        return answer_course_question(question, course_data)
    elif "event" in question.lower():
        return answer_event_question(question, event_data)
    else:
        return "I'm not sure how to answer that. Please specify if you're asking about courses or events."


def extract_keywords_from_question(question):
    # Use spaCy NLP to process the question
    doc = nlp(question)

    # Extract nouns and proper nouns as keywords
    keywords = [token.text for token in doc if token.pos_ in ['NOUN', 'PROPN']]

    return keywords

# Example usage
question = "Can you recommend some courses on Greek mythology?"
answer = answer_query(question, course_data, event_data)
print("Question:", question)
print("Answer:", answer)

#Example usage
question = "What are some events on campus for international students?"
answer = answer_query(question, course_data, event_data)
print("Question:", question)
print("Answer:", answer)