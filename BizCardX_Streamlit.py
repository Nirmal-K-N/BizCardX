import streamlit as st
import easyocr
import io
from io import BytesIO
from streamlit_option_menu import option_menu
import mysql.connector
import pandas as pd
import re
from PIL import Image
import numpy as np
import os
from pprint import pprint
import time

#MySql Connection
mydb = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Nirmal9699',
    database='business_cards')
cursor = mydb.cursor()

#Function to extract the data
def upload_image(image_path):
    reader = easyocr.Reader(['en'])
    result = reader.readtext(image_path)
    details = [res[1] for res in result]
    
    name = []
    designation = []
    contact = []
    email = []
    website = []
    street = []
    city = []
    state = []
    pincode = []
    company = []

    for detail in details:
        match1 = re.findall('([0-9]+ [A-Z]+ [A-Za-z]+)., ([a-zA-Z]+). ([a-zA-Z]+)', detail)
        match2 = re.findall('([0-9]+ [A-Z]+ [A-Za-z]+)., ([a-zA-Z]+)', detail)
        match3 = re.findall('^[E].+[a-z]', detail)
        match4 = re.findall('([A-Za-z]+) ([0-9]+)', detail)
        match5 = re.findall('([0-9]+ [a-zA-z]+)', detail)
        match6 = re.findall('.com$', detail)
        match7 = re.findall('([0-9]+)', detail)

        if detail == details[0]:
            name.append(detail)
        elif detail == details[1]:
            designation.append(detail)
        elif '-' in detail:
            contact.append(detail)
        elif '@' in detail:
            email.append(detail)
        elif "www " in detail.lower() or "www." in detail.lower():
            website.append(detail)
        elif "WWW" in detail:
            website.append(detail + "." + details[details.index(detail) + 1])
        elif match6:
            pass
        elif match1:
            street.append(match1[0][0])
            city.append(match1[0][1])
            state.append(match1[0][2])
        elif match2:
            street.append(match2[0][0])
            city.append(match2[0][1])
        elif match3:
            city.append(match3[0])
        elif match4:
            state.append(match4[0][0])
            pincode.append(match4[0][1])
        elif match5:
            street.append(match5[0] + ' St,')
        elif match7:
            pincode.append(match7[0])
        else:
            company.append(detail)

    if len(company) > 1:
        comp = company[0] + ' ' + company[1]
    else:
        comp = company[0]

    contact_number = contact[0] if contact else None
    alternative_number = contact[1] if len(contact) > 1 else None
    
    image_details = {'Name': name[0], 'Designation': designation[0], 'Company_Name': comp,
                     'Contact': contact_number, 'Alternative_Contact': alternative_number, 'Email': email[0],
                     'Website': website[0], 'Street': street[0], 'City': city[0], 'State': state[0],
                     'Pincode': pincode[0]}

    return image_details

with st.sidebar:
    selected = option_menu("Main Menu", ["Home","Extract Business Card Data","Details"], 
                icons=['house','question','map'], menu_icon="cast", default_index=0)
    
    if selected == "Details":
        choose = st.radio("**Data Manipulation**",["Show Data", "Update Data", "Delete Data"],
                captions = ["View the data", "Edit the data", "Delete the data"])


if selected == "Home":
    st.title(":orange[BizCardX: Extracting Business Card Data with OCR]")
    st.write("""**The project would require skills in image processing, OCR, GUI development, and
            database management. It would also require careful design and planning of the
            application architecture to ensure that it is scalable, maintainable, and extensible.
            Good documentation and code organization would also be important for the project.
            Overall, the result of the project would be a useful tool for businesses and individuals
            who need to manage business card information efficiently.**""")
    st.subheader(":blue[Technologies Used]",divider='grey')
    st.text("> OCR,")
    st.text("> StreamLit GUI,")
    st.text("> SQL, &")
    st.text("> Data Extraction")

elif selected == "Extract Business Card Data":
    # Upload file using Streamlit
    uploaded_file = st.file_uploader("**Upload a business card image**", type=["jpg", "png", "jpeg"])
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Image.", use_column_width=True)
        image_bytes = uploaded_file.read()

        df = pd.DataFrame(upload_image(image_bytes),index=[1])
        st.dataframe(df)
    else:
        st.empty()

    if st.button("Save to Database"):
        try:
            # Create a table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bixcard (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    card_holder_name VARCHAR(255),
                    designation VARCHAR(255),
                    company_name VARCHAR(255),
                    mobile_number VARCHAR(20),
                    alternative_mobile_number VARCHAR(20),
                    email_address VARCHAR(255),
                    website_url VARCHAR(255),
                    street VARCHAR(255),
                    city VARCHAR(255),
                    state VARCHAR(255),
                    pin_code VARCHAR(20)
                )''')

            sql = """INSERT INTO bixcard (
                        card_holder_name, designation, company_name, mobile_number,
                        alternative_mobile_number, email_address, website_url, street, city, state, pin_code) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            for i in df.to_records().tolist():
                cursor.execute(sql,i[1:])

            # Commit the transaction
            mydb.commit()
            st.success("Data saved to the database.")
        except Exception as e:
            st.error(f"Error: {e}")

elif selected == "Details":
    if choose == "Show Data":
        st.title("Details of entire data collected")
        def show_data():
            sql = """SELECT *
                    FROM business_cards.bixcard"""
            cursor.execute(sql)
            data = cursor.fetchall()
            data_df = pd.DataFrame(data, columns=['ID','Name', 'Designation','Company Name','Number','Alternate Number','Email ID','Website','Street','City','State','Pincode']).reset_index(drop=True)
            data_df.index += 1
            return data_df
       
        SD = show_data()
        
        #Inserting search bar
        def search_table():
            #st.title("Search Bar for Table")
            search_term = st.text_input("Search by Name:", "")
            # Filter the dataframe based on the search term
            filtered_df = SD[SD['Name'].astype(str).str.contains(search_term)]
            if not search_term:
                st.table(SD)
            else:
                if not filtered_df.empty:
                    st.table(filtered_df)
                else:
                    st.error("Data Not Found !!!")
        search_table()

    elif choose == "Update Data":
        # Streamlit app
        st.title('Update Database')
        sql = """select id from business_cards.bixcard"""
        cursor.execute(sql)
        ids = cursor.fetchall()
        ids = [item[0] for item in ids]
        id = st.selectbox('Select ID',ids, index=None, placeholder="ID")
        
        # Query the database to get the current data for the specified name
        query = """SELECT card_holder_name, designation, company_name, mobile_number, alternative_mobile_number,
		            email_address, website_url, street, city, state, pin_code
                    FROM business_cards.bixcard WHERE id = %s"""
        cursor.execute(query, (id,))
        result = cursor.fetchone()
        
        # If the name exists in the database, display the current data and allow the user to update it

        if id is None or id == "":
            st.warning(f"NO INPUT GIVEN")


        elif id is not None or id != "":
            st.write(f"Current data for {id}:{result}")

            # Get user input for different columns
            name = st.text_input('Enter new value for Name:')
            if name is None or name == "":
                pass
            else:
                query = """UPDATE business_cards.bixcard 
                    SET card_holder_name = %s
                    WHERE id = %s"""
                cursor.execute(query, (name, id))
                mydb.commit()
            

            designation = st.text_input('Enter new value for Designation:')
            if designation is None or designation == "":
                pass            
            else:
                query = """UPDATE business_cards.bixcard 
                    SET designation = %s
                    WHERE id = %s"""
                cursor.execute(query, (designation, id))
                mydb.commit()
                
            company_name = st.text_input('Enter new value for Company Name:')
            if company_name is None or company_name == "":
                pass
            else: 
                query = """UPDATE business_cards.bixcard 
                    SET company_name = %s
                    WHERE id = %s"""
                cursor.execute(query, (company_name, id))
                mydb.commit()

            number = st.text_input('Enter new value for Number:')
            if number is None or number == "":
                pass
            else: 
                query = """UPDATE business_cards.bixcard 
                    SET mobile_number = %s
                    WHERE id = %s"""
                cursor.execute(query, (number, id))
                mydb.commit()

            alternate_number = st.text_input('Enter new value for Alternate Number:')
            if alternate_number is None or alternate_number == "":
                pass
            else: 
                query = """UPDATE business_cards.bixcard 
                    SET alternative_mobile_number = %s
                    WHERE id = %s"""
                cursor.execute(query, (alternate_number, id))
                mydb.commit()

            email_id = st.text_input('Enter new value for Email ID:')
            if email_id is None or email_id == "":
                pass
            else:
                query = """UPDATE business_cards.bixcard 
                    SET email_address = %s
                    WHERE id = %s"""
                cursor.execute(query, (email_id, id))
                mydb.commit()

            website = st.text_input('Enter new value for Website:')
            if website is None or website == "":
                pass
            else:
                query = """UPDATE business_cards.bixcard 
                    SET website_url = %s
                    WHERE id = %s"""
                cursor.execute(query, (website, id))
                mydb.commit()

            street = st.text_input('Enter new value for Street:')
            if street is None or street == "":
                pass
            else:
                query = """UPDATE business_cards.bixcard 
                    SET street = %s
                    WHERE id = %s"""
                cursor.execute(query, (street, id))
                mydb.commit()

            city = st.text_input('Enter new value for City:')
            if city is None or city == "":
                pass
            else:
                query = """UPDATE business_cards.bixcard 
                    SET city = %s
                    WHERE id = %s"""
                cursor.execute(query, (city, id))
                mydb.commit()

            state = st.text_input('Enter new value for State:')
            if state is None or state == "":
                pass
            else:
                query = """UPDATE business_cards.bixcard 
                    SET state = %s
                    WHERE id = %s"""
                cursor.execute(query, (state, id))
                mydb.commit()

            pincode = st.text_input('Enter new value for Pincode:')
            if pincode is None or pincode == "":
                pass
            else:
                query = """UPDATE business_cards.bixcard 
                    SET pin_code = %s
                    WHERE id = %s"""
                cursor.execute(query, (pincode, id))
                mydb.commit()
            submit = st.button('Submit')
            if (submit):
                st.success('Database updated successfully!')
                with st.spinner('Fetching information...'):
                    time.sleep(2)
                    st.write("**Updated Database**")
                    sql = """SELECT * FROM business_cards.bixcard WHERE id = %s"""
                    cursor.execute(sql, (id,))
                    data = cursor.fetchall()
                    

                    data_df = pd.DataFrame(data, columns=['ID','Name', 'Designation','Company Name','Number','Alternate Number','Email ID','Website','Street','City','State','Pincode']).reset_index(drop=True)
                    data_df.index += 1
                    st.dataframe(pd.DataFrame(data_df))
        
    
    elif choose == "Delete Data":
        st.title('Delete Data')
        # Get user input for ID
        sql = """select id from business_cards.bixcard"""
        cursor.execute(sql)
        ids = cursor.fetchall()
        ids = [item[0] for item in ids]
        id = st.selectbox('Select ID',ids, index=None, placeholder="ID")
        submit = st.button('Submit')
        
        if submit and (id is not None or id != ""):
            # Query the database to get the current data for the specified name
            query = """DELETE FROM business_cards.bixcard WHERE id = %s"""
            cursor.execute(query, (id,))
            mydb.commit()
            with st.spinner('Deleting data...'):
                time.sleep(2)
                st.success(f"Successfully deleted the row with ID: {id}")
        
        
                                

        
