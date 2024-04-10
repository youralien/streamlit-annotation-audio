import streamlit as st
import json
from data_utils import *
import os

BUCKET_NAME = st.secrets.filenames["bucket_name"]
STATE = st.secrets.filenames["state_file"]
EXAMPLES = st.secrets.filenames["example_file"]

def update_global_dict(keys, dump = False):
    for key in keys:
        if key in st.session_state:
            global_dict[key] = st.session_state[key]

    if not dump:
        return

    if "logged_in" in st.session_state and st.session_state["logged_in"]:
        # json.dump(global_dict, open(f"data/state_{st.session_state['logged_in']}.json", 'w'))
        save_dict_to_gcs(BUCKET_NAME, f"data/{STATE}_{st.session_state['logged_in']}.json", global_dict)
    elif "pid" in st.session_state and st.session_state["pid"]:
        client = get_gc_client()
        bucket = client.get_bucket(BUCKET_NAME)
        if storage.Blob(bucket=bucket, name=f"data/{STATE}_{st.session_state['pid']}.json").exists(client):
        # if os.path.exists(f"data/state_{st.session_state['pid']}.json"):
            # load
            return
        else:
            # json.dump(global_dict, open(f"data/state_{st.session_state['pid']}.json", 'w'))
             save_dict_to_gcs(BUCKET_NAME, f"data/{STATE}_{st.session_state['pid']}.json", global_dict)
    else:
        save_dict_to_gcs(BUCKET_NAME, f"data/{STATE}.json", global_dict)
        # json.dump(global_dict, open(f'data/state.json', 'w'))

def example_finished_callback():
    for _ in st.session_state:
        global_dict[_] = st.session_state[_]
    global_dict["current_example_ind"] += 1
    if "logged_in" in st.session_state and st.session_state["logged_in"]:
        save_dict_to_gcs(BUCKET_NAME, f"data/{STATE}_{st.session_state['logged_in']}.json", dict(global_dict))
        # json.dump(dict(global_dict), open(f"data/state_{st.session_state['logged_in']}.json", 'w'))
    else:
        save_dict_to_gcs(BUCKET_NAME, f"data/{STATE}.json", dict(global_dict))
        # json.dump(dict(global_dict), open(f'data/state.json', 'w'))
    js = '''
    <script>
        function scrollToTop() {
            var body = window.parent.document.querySelector(".main");
            body.scrollTop = 0;
        }
        setTimeout(scrollToTop, 300);  // 300 milliseconds delay
    </script>
    '''
    with callback_placeholder.container():
        st.components.v1.html(js)



def get_id():
    """Document Prolific ID"""

    if "logged_in" in st.session_state and st.session_state["logged_in"]:
        return True

    with login_placeholder.container():
        col1, col2, col3 = st.columns([2,3,2])
        with col2:
            if "pid" in st.session_state and st.session_state["pid"]:
                st.session_state["logged_in"] = st.session_state["pid"]
                st.session_state["reload"] = True
                return True
            else:
                st.markdown(f'### Virtual Patient Response Ranking Tool - Test Set C')
                st.warning("""Before you log in and begin annotating data,
                            please ensure you have read and fully understood our research information sheet.
                            :red[**By providing your Email ID, you are providing your informed consent**] to participate in this research project.
                            If you have any questions or concerns about the research or your role in it,
                            please reach out to our team before proceeding.""", icon="⚠️")
                st.text_input("Email ID", key="pid", on_change=update_global_dict, args=[["pid"], "True"])
                st.session_state["reload"] = True
                return False


if __name__ == "__main__":

    st.set_page_config(layout="wide")

    # Create placeholders for each dynamic section
    login_placeholder = st.empty()
    main_content_placeholder = st.empty()
    main_instructions_placeholder = st.empty()
    case_input_placeholder = st.empty()
    dimension_1_placeholder = st.empty()
    dimension_2_placeholder = st.empty()
    dimension_3_placeholder = st.empty()
    overall_ranking_placeholder = st.empty()
    prepare_submit_placeholder = st.empty()
    callback_placeholder = st.empty()

    if "reload" not in st.session_state or st.session_state["reload"]:
        if "logged_in" in st.session_state and st.session_state["logged_in"]:
            global_dict = read_or_create_json_from_gcs(BUCKET_NAME, f"data/{STATE}_{st.session_state['logged_in']}.json")
            # global_dict = json.load(open(f"data/state_{st.session_state['logged_in']}.json", 'r'))
        elif "pid" in st.session_state and st.session_state["pid"]:
            global_dict = read_or_create_json_from_gcs(BUCKET_NAME, f"data/{STATE}_{st.session_state['pid']}.json")
            # global_dict = json.load(open(f"data/state_{st.session_state['pid']}.json", 'r'))
        else:
            global_dict = read_or_create_json_from_gcs(BUCKET_NAME, f"data/{STATE}.json")
            # global_dict = json.load(open(f'data/state.json', 'r'))
        st.session_state["reload"] = False
        st.session_state["testcases"] = global_dict["testcases"]
        st.session_state["current_example_ind"] = global_dict["current_example_ind"]
    else:
        global_dict = st.session_state

    if "testcases_text" not in st.session_state:
        testcases = read_or_create_json_from_gcs(BUCKET_NAME, f"data/{EXAMPLES}.json")
        # testcases = json.load(open('data/errors_test.json', 'r'))
        st.session_state["testcases_text"] = testcases

    testcases = st.session_state["testcases_text"]

    if get_id():
        with main_content_placeholder.container():
            example_ind = global_dict["current_example_ind"]

            with st.sidebar:
                st.markdown(""" # **Annotation Instructions**
**Case Data**: You have been provided a description of the patient case, and a conversation between the virtual patient and a therapist.

**Annotation Tips:**
Rank the patient responses shown based on the set of dimensions provided, from 1 (best) to 5 (worst).
The same rank can be assigned to multiple responses, if required. For example, if the first and second response are of similar quality, and both are better than the third response, the ranking would look like

| Response  | Rank |
| --------- | ---- |
| ResponseX | 1    |
| ResponseY | 1    |
| ResponseZ | 2    |
""")

            c1, c2, c3 = st.columns([1,5,1])
            with c2:
                if example_ind >= len(global_dict["testcases"]):
                    st.title("Thank you!")
                    st.balloons()
                    st.success("You have annotated all the examples! 🎉")

                else:

                    for key in global_dict:
                        st.session_state[key] = global_dict[key]

                    with main_instructions_placeholder.container():
                        st.markdown(f'### **Virtual Patient Response Ranking Tool - Test Set C**')
                        st.info("This is a tool to rank patient responses generated from different AI models along different dimensions. Please read the conversation, patient description and set of principles for the patient to follow below and provide responses in the following sections.")
                        st.subheader(f"Case {example_ind + 1} of {len(global_dict['testcases'])}")

                    example_ind = global_dict["current_example_ind"]
                    testcase = testcases["tests"][global_dict["testcases"][example_ind]]

                    count_required_feedback = 0
                    count_done_feedback = 0

                    with case_input_placeholder.container():
                        st.markdown(f'### **Description of Patient**')
                        st.markdown(testcase["input"]["description"])

                        conv = testcase["input"]["messages"]
                        st.markdown(f'### **Conversation History**')
                        for i in range(len(conv)):
                            to_print = f"**{conv[i]['role']}** : {conv[i]['content']}"
                            if conv[i]["role"] == 'therapist':
                                st.markdown(f':blue[{to_print}]')
                            else:
                                st.markdown(f':red[{to_print}]')

                        # principles_list = f'### **Principles**'
                        # for _ in testcase["input"]["principles"]:
                        #     principles_list += f'\n- {_}'
                        # st.markdown(principles_list)

                    responses = testcase["responses"]
                    with dimension_1_placeholder.container():
                        st.markdown(f'### **Dimension 1**')
                        st.markdown('Rank responses (1=best, 5=worst) based on how consistent they are to the patient description and conversation history, and if they offer an appropriate reply to the last message from the therapist. All suitably consistent responses should have the same rank.')

                        for idx, response in enumerate(responses):
                            col1, col2 = st.columns([4,2])
                            with col1:
                                to_print = f"**patient** : {response['message']}"
                                st.markdown(f':red[{to_print}]')
                                count_required_feedback += 1

                            with col2:
                                key = f'{example_ind}_1_{idx}'
                                st.selectbox(label="Rank", options=["None"] + [str(_+1) for _ in list(range(len(responses)))], key=key)
                                if key in st.session_state and st.session_state[key] != "None":
                                    count_done_feedback += 1

                    with dimension_2_placeholder.container():
                        st.markdown(f'### **Dimension 2**')
                        # st.markdown('The response avoids stylistic errors. Such errors may include: starting a sentence with a greeting in the middle of a conversation, or always ending a response with an abbreviation.')
                        st.markdown('Evaluate whether each response has an awkward style of speech. An example of awkward style could be starting a sentence with a greeting in the middle of a conversation.')

                        for idx, response in enumerate(responses):
                            col1, col2 = st.columns([4,2])
                            with col1:
                                to_print = f"**patient** : {response['message']}"
                                st.markdown(f':red[{to_print}]')
                                count_required_feedback += 1

                            with col2:
                                key = f'{example_ind}_2_{idx}'
                                st.selectbox(label="Is this response awkward?", options=["None", "Yes", "No"], key=key)
                                if key in st.session_state and st.session_state[key] != "None":
                                    count_done_feedback += 1

                    with dimension_3_placeholder.container():
                        st.markdown(f'### **Dimension 3**')
                        st.markdown("""Rank responses (1=best, 5=worst) based on how well they adhere to all the written principles.

* Responses that violate fewer principles should be ranked higher.
* Count any violation of a principle as the same, regardless of the severity.
* ⚠️ *Do not* evaluate responses based on *your internal-set of principles*.  Please only evaluate based on principles that are written
""")

                        principles_list = f'##### **Principles for Patient Actor to Follow**'
                        for i, principle in enumerate(testcase["input"]["principles"]):
                            principles_list += f'\n{i+1}. {principle}'
                        st.markdown(principles_list)

                        for idx, response in enumerate(responses):
                            col1, col2 = st.columns([4,2])
                            with col1:
                                to_print = f"**patient** : {response['message']}"
                                st.markdown(f':red[{to_print}]')
                                count_required_feedback += 1

                            with col2:
                                key = f'{example_ind}_3_{idx}'
                                st.selectbox(label="Rank", options=["None"] + [str(_+1) for _ in list(range(len(responses)))], key=key)
                                if key in st.session_state and st.session_state[key] != "None":
                                    count_done_feedback += 1

                    with overall_ranking_placeholder.container():
                        st.markdown(f'### **Overall Ranking**')
                        st.markdown('Based on your answers for the dimensions above, provide an overall ranking (1=best, 5=worst) for the responses in the context of the patient description, conversation history and set of principles. In cases where responses do not have significant errors according to dimensions 1 and 2, the overall ranking can be determined on the basis of dimension 3. ')

                        for idx, response in enumerate(responses):
                            col1, col2 = st.columns([4,2])
                            with col1:
                                to_print = f"**patient** : {response['message']}"
                                st.markdown(f':red[{to_print}]')
                                count_required_feedback += 1

                            with col2:
                                key = f'{example_ind}_4_{idx}'
                                st.selectbox(label="Rank", options=["None"] + [str(_+1) for _ in list(range(len(responses)))], key=key)
                                if key in st.session_state and st.session_state[key] != "None":
                                    count_done_feedback += 1

                        count_required_feedback += 1
                        st.text_area("Please provide a brief explanation for the overall ranking provided above.", key=f"reason_{example_ind}", height=200)
                        if f"reason_{example_ind}" in st.session_state and st.session_state[f"reason_{example_ind}"]:
                            count_done_feedback += 1

                    with prepare_submit_placeholder.container():
                        st.checkbox('I have finished annotating', key=f"finished_{example_ind}")

                        if f"finished_{example_ind}" in st.session_state and st.session_state[f"finished_{example_ind}"]:
                            if count_done_feedback != count_required_feedback:
                                st.error('Some annotations seem to be missing. Please annotate the full conversation', icon="❌")
                            else:
                                st.success('We got your annotations!', icon="✅")
                                st.button("Submit final answers and go to next testcase", type="primary", on_click=example_finished_callback)
                                st.session_state["reload"] = True
