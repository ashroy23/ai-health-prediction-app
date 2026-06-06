import streamlit as st
import sqlite3
import pandas as pd
import re
import os

from datetime import date
from dotenv import load_dotenv
import google.generativeai as genai

st.set_page_config(
    page_title="AI Health Prediction",
    page_icon="🏥",
    layout="wide"
)

# Gemini Setup

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel("gemini-2.5-flash")


def generate_remarks(glucose, haemoglobin, cholesterol):

    try:
        prompt = f"""
           Patient Health Report

           Glucose: {glucose}
           Haemoglobin: {haemoglobin}
           Cholesterol: {cholesterol}

           Act as a healthcare screening assistant.

           Provide a professional health observation in 2-3 sentences.

           Requirements:
            - Do not diagnose any disease.
            - Clearly mention which values are outside normal ranges.
            - Use a serious and professional tone.
            - Explain potential health concerns associated with abnormal values.
            - Recommend medical consultation when values appear significantly abnormal.
            - Avoid casual phrases such as "appears okay" or "looks fine".

            Response should read like a preliminary medical report.
"""

        response = model.generate_content(prompt)

        return response.text

    except Exception as e:
        return f"AI remarks unavailable: {e}"


# Database Setup

conn = sqlite3.connect(
    "patients.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    dob TEXT,
    email TEXT,
    glucose REAL,
    haemoglobin REAL,
    cholesterol REAL,
    remarks TEXT
)
""")

conn.commit()

st.sidebar.title("🏥 AI Health Prediction App")

st.sidebar.markdown("---")
st.sidebar.caption("Patient Management System")

page = st.sidebar.radio(
    "Navigation",
    [
        "Add Patient",
        "View Records",
        "Update Patient",
        "Delete Patient"
    ]
)

# Main App

if page == "Add Patient":
   st.title("🏥 Health Prediction App")
   st.caption("Add a new patient and generate AI-powered health remarks.")    
   name = st.text_input("Full Name")
   dob = st.date_input("Date of Birth")
   email = st.text_input("Email Address")
   glucose = st.number_input("Glucose")
   haemoglobin = st.number_input("Haemoglobin")
   cholesterol = st.number_input("Cholesterol")
   
   if st.button("Submit"):
        if not name.strip():
            st.error("Name cannot be empty.")

        elif dob > date.today():
            st.error("Date of Birth cannot be in the future.")

        elif not re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", email):
            st.error("Please enter a valid email address.")

    
        elif glucose <= 0:
            st.error("Please enter a valid glucose value.")
    
        elif haemoglobin <= 0:
            st.error("Please enter a valid haemoglobin value.")
    
        elif cholesterol <= 0:
            st.error("Please enter a valid cholesterol value.")


        else:
            remarks = generate_remarks(
            glucose,
            haemoglobin,
            cholesterol
        )

            cursor.execute(
            """
            INSERT INTO patients
            (name, dob, email, glucose, haemoglobin, cholesterol, remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                str(dob),
                email,
                glucose,
                haemoglobin,
                cholesterol,
                remarks
            )
        )

            conn.commit()

            st.success("Patient record submitted successfully!")

            st.write("Name:", name)
            st.write("DOB:", dob)
            st.write("Email:", email)
            st.write("Glucose:", glucose)
            st.write("Haemoglobin:", haemoglobin)
            st.write("Cholesterol:", cholesterol)
            st.write("Remarks:", remarks)

# View Records

if page == "View Records":

    cursor.execute(
        "SELECT * FROM patients ORDER BY id DESC"
    )

    records = cursor.fetchall()

    df = pd.DataFrame(
        records,
        columns=[
            "ID",
            "Name",
            "DOB",
            "Email",
            "Glucose",
            "Haemoglobin",
            "Cholesterol",
            "Remarks"
        ]
    )

    col1, col2 = st.columns([4, 1])

    with col1:
        st.title("📋 Patient Records")
        st.caption("View all patient records stored in the database.")
    with col2:
        st.metric(
            "Total Patients",
            len(df)
        )

    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True
    )
# Update Patient

if page == "Update Patient":
    st.title("✏️ Update Patient")
    st.caption("Modify patient information and regenerate AI remarks.")
    update_id = st.number_input(
        "Patient ID to Update",
        min_value=1,
        step=1,
        key="update_id"
        )

    new_email = st.text_input(
        "New Email Address"
    )

    new_glucose = st.number_input(
       "New Glucose",
        min_value=0.0,
        value=0.0,
        key="new_glucose"
    )
    
    
    new_haemoglobin = st.number_input(
        "New Haemoglobin",
        min_value=0.0,
        value=0.0,
        key="new_haemoglobin"
    )

    new_cholesterol = st.number_input(
        "New Cholesterol",
        min_value=0.0,
        value=0.0,
        key="new_cholesterol"
    )

    if st.button("Update Patient"):

       cursor.execute(
        "SELECT * FROM patients WHERE id = ?",
        (update_id,)
       )

       patient = cursor.fetchone()

       if patient is None:
        st.error("Patient ID does not exist.")

       elif not new_email.strip():
        st.error("Email cannot be empty.")

       elif not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", new_email):
        st.error("Please enter a valid email address.")

       elif new_glucose <= 0:
        st.error("Please enter a valid glucose value.")

       elif new_haemoglobin <= 0:
        st.error("Please enter a valid haemoglobin value.")

       elif new_cholesterol <= 0:
        st.error("Please enter a valid cholesterol value.")

      
       else:
        new_remarks = generate_remarks(
           new_glucose,
           new_haemoglobin,
           new_cholesterol
        )

        cursor.execute(
    """
    UPDATE patients
    SET glucose = ?,
        haemoglobin = ?,
        email = ?,
        cholesterol = ?,
        remarks = ?
    WHERE id = ?
    """,
    (
        new_glucose,
        new_haemoglobin,
        new_email,
        new_cholesterol,
        new_remarks,
        update_id
    )
)

        conn.commit()
        st.success("Patient updated successfully!")

# Delete Patient

if page == "Delete Patient":

    st.title("🗑️ Delete Patient")
    st.caption("Remove a patient record from the system.")

    delete_id = st.number_input(
        "Enter Patient ID",
        min_value=1,
        step=1
    )

    if st.button("Delete Patient"):

        cursor.execute(
            "SELECT * FROM patients WHERE id = ?",
            (delete_id,)
        )

        patient = cursor.fetchone()

        if patient is None:
            st.error("Patient ID does not exist.")

        else:
            cursor.execute(
                "DELETE FROM patients WHERE id = ?",
                (delete_id,)
            )

            conn.commit()

            st.success("Patient deleted successfully!")

conn.close()