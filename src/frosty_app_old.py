from openai import OpenAI
import re
import streamlit as st
import matplotlib.pyplot as plt
from prompts import get_system_prompt

st.title("⚡🤖⚡ G-Bot - GDATA's AI Assitant")

# Initialize the chat messages history
client = OpenAI(api_key=st.secrets.OPENAI_API_KEY)

if "messages" not in st.session_state:
    # system prompt includes table information, rules, and prompts the LLM to produce
    # a welcome message to the user.
    st.session_state.messages = [{"role": "system", "content": get_system_prompt()}]

# Prompt for user input and save
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})

# display the existing chat messages
for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"],avatar="🦖"):
        st.write(message["content"])
        if "results" in message:
            st.dataframe(message["results"])

# If last message is not from assistant, we need to generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant",avatar="🤖"):
        response = ""
        resp_container = st.empty()
        for delta in client.chat.completions.create(
            model="gpt-3.5-turbo",
            #model="gpt-4",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True,
        ):
            response += (delta.choices[0].delta.content or "")
            resp_container.markdown(response)

        message = {"role": "assistant", "content": response}
        # Parse the response for a SQL query and execute if available
        sql_match = re.search(r"```sql\n(.*)\n```", response, re.DOTALL)
        if sql_match:
            sql = sql_match.group(1)
            conn = st.connection("snowflake")
            message["results"] = conn.query(sql)
            if "results" in message:
                # Prompt the user to select the visualization type
                chart_type = st.radio(
                    "How would you like to visualize the data?",
                    ('Table', 'Pie Chart'),
                    index=1  # Default to 'Table'
                )

                if chart_type == 'Pie Chart':
                    # Assuming the DataFrame has two columns: one for labels and one for values
                    fig, ax = plt.subplots()
                    ax.pie(message["results"].iloc[:, 1], labels=message["results"].iloc[:, 0], autopct='%1.1f%%')
                    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
                    st.pyplot(fig)
                else:
                    # Default to displaying as a DataFrame
                    st.dataframe(message["results"])
        st.session_state.messages.append(message)
