import streamlit as st
from data_utils import *
import os
import json

# Directory where audio files are stored. 
AUDIO_BASE_DIR = '/Users/npb/Desktop/anticipation/humaneval_mp3_final'
AUDIO_FILES_DIR = ''
BUCKET_NAME = st.secrets.filenames["bucket_name"]
STATE = st.secrets.filenames["state_file"]

# whether to use /data in local directory or GCS
USE_LOCAL_DATA = True

global global_dict

def get_audio_files_dir(split):
    """Return the directory based on the selected audio split."""
    return os.path.join(AUDIO_BASE_DIR, f"{split}".lower())

def list_audio_pairs(directory):
    files = os.listdir(directory)
    pairs = {}
    for file in files:
        if '-A.mp3' in file or '-B.mp3' in file:
            num = file.split('-')[0]
            if num in pairs:
                pairs[num].append(file)
            else:
                pairs[num] = [file]
    return pairs

def play_and_collect_response(pair, unique_key):
    st.audio(os.path.join(AUDIO_FILES_DIR, pair[0]), format='audio/mp3')
    st.audio(os.path.join(AUDIO_FILES_DIR, pair[1]), format='audio/mp3')
    choice = st.radio(
        "Which accompaniment sounds more coherent with the melody?",
        ('A', 'Tie', 'B'),
        key=unique_key 
    )
    return choice

def update_global_dict(keys, dump = False):

    global global_dict

    for key in keys:
        if key in st.session_state:
            global_dict[key] = st.session_state[key]

    if not dump:
        return
    
    global_dict = serialize_session_state(global_dict)

    if "logged_in" in st.session_state and st.session_state["logged_in"]:
        if USE_LOCAL_DATA:
            json.dump(global_dict, open(f"data/state_{st.session_state['logged_in']}.json", 'w'))
        else:
            save_dict_to_gcs(BUCKET_NAME, f"data/{STATE}_{st.session_state['logged_in']}.json", global_dict)
    elif "pid" in st.session_state and st.session_state["pid"]:
        if USE_LOCAL_DATA:
            json.dump(global_dict, open(f"data/state_{st.session_state['pid']}.json", 'w'))
        else:
            client = get_gc_client()
            bucket = client.get_bucket(BUCKET_NAME)
            if storage.Blob(bucket=bucket, name=f"data/{STATE}_{st.session_state['pid']}.json").exists(client):
                # load
                return
            else:
                save_dict_to_gcs(BUCKET_NAME, f"data/{STATE}_{st.session_state['pid']}.json", global_dict)      


def begin_survey(email, split):
    if email and split:
            st.session_state["logged_in"] = st.session_state["pid"]
            st.session_state["split"] = st.session_state["audio_split"]
            st.session_state["reload"] = True

def get_id():
    """Document Prolific ID"""

    if "logged_in" in st.session_state and st.session_state["logged_in"]:
        return True

    with login_placeholder.container():
        col1, col2, col3 = st.columns([2,3,2])
        with col2:
            if "pid" in st.session_state and st.session_state["pid"] and "reload" in st.session_state and st.session_state["reload"]:
                st.session_state["logged_in"] = st.session_state["pid"]
                st.session_state["reload"] = True
                return True
            else:
                st.markdown(f'### Musical Comparison Annotation Tool')
                st.warning("""**Please begin by entering your email and selecting the split you were given.** On the next page, you will be asked to listen to two 20 second audio clips and select which one sounds more *musically coherent*. One instrument (often the melody) will be shared between clips, although it is not necessary to pay attention to this for this task. There are two pages to the survey and 50 comparisons in total. Please click 'next' once you have finished all questions on a page.""", icon="⚠️")
                email = st.text_input("Email ID", key="pid", on_change=update_global_dict, args=[["pid"], "True"])
                split = st.radio("Split:", ('A', 'B', 'C'), key="audio_split", on_change=update_global_dict, args=[["audio_split"], "True"])
                st.button("Start", on_click=begin_survey, args=[email, split])
                return False


def serialize_session_state(data):
    if isinstance(data, dict):
        return {key: serialize_session_state(value) for key, value in data.items() if not isinstance(value, st.delta_generator.DeltaGenerator)}
    elif isinstance(data, list):
        return [serialize_session_state(item) for item in data]
    elif isinstance(data, (str, int, float, bool)):
        return data
    # Add more types as needed based on what you store in session_state
    else:
        return str(data)  # Or handle in a more sophisticated way
    

if __name__ == "__main__":
    
    st.set_page_config(layout="wide")

    # Create placeholders for each dynamic section
    login_placeholder = st.empty()
    callback_placeholder = st.empty()

    if "reload" not in st.session_state or st.session_state["reload"]:
        if "logged_in" in st.session_state and st.session_state["logged_in"]:
            if USE_LOCAL_DATA:
                global_dict = json.load(open(f"data/{STATE}_{st.session_state['logged_in']}.json", 'r'))
            else:
                global_dict = read_or_create_json_from_gcs(BUCKET_NAME, f"data/{STATE}_{st.session_state['logged_in']}.json")
        elif "pid" in st.session_state and st.session_state["pid"]:
            if USE_LOCAL_DATA:
                global_dict = json.load(open(f"data/{STATE}_{st.session_state['pid']}.json", 'r'))
            else:
                global_dict = read_or_create_json_from_gcs(BUCKET_NAME, f"data/{STATE}_{st.session_state['pid']}.json")
        else:
            if USE_LOCAL_DATA:
                global_dict = json.load(open(f'data/{STATE}.json', 'r'))
            else:
                global_dict = read_or_create_json_from_gcs(BUCKET_NAME, f"data/{STATE}.json")
        st.session_state["reload"] = False
    else:
        global_dict = st.session_state
    
    if get_id():

        # Initialize or retrieve the current index and responses from the session state
        if 'current_batch_index' not in st.session_state:
            st.session_state.current_batch_index = 0
            st.session_state.responses = {}

        AUDIO_FILES_DIR = get_audio_files_dir(st.session_state["split"])
        
        # List the audio pairs
        pairs = list_audio_pairs(AUDIO_FILES_DIR)
        pairs_keys = sorted(list(pairs.keys()))

        # Calculate number of batches (assuming 50 total comparisons for 2 pages)
        total_batches = 2
        batch_size = 25

        if st.session_state.current_batch_index < total_batches:
            start_index = st.session_state.current_batch_index * batch_size
            end_index = start_index + batch_size
            batch_pairs_keys = pairs_keys[start_index:end_index]

            for i, pair_key in enumerate(batch_pairs_keys, start=1):
                pair = pairs[pair_key]
                st.header(f"Comparison {start_index + i}")
                unique_key = f"response_{start_index + i}"
                response = play_and_collect_response(pair, unique_key)
                # Collect each response with its pair key
                st.session_state.responses[pair_key] = response

            if st.button('Next'):
                # Move to the next batch or complete
                st.session_state.current_batch_index += 1
                if st.session_state.current_batch_index < total_batches:
                    st.experimental_rerun()
                else:
                    st.header("Thank you for completing the survey!")
                    st.balloons()

                    for _ in st.session_state:
                        if 'response_' not in _:
                            global_dict[_] = st.session_state[_]

                    global_dict["current_batch_index"] += 1
                    global_dict = serialize_session_state(global_dict)

                    if USE_LOCAL_DATA:
                        json.dump(global_dict, open(f"data/state_{st.session_state['logged_in']}.json", 'w'))
                    else:
                        save_dict_to_gcs(BUCKET_NAME, f"data/{STATE}_{st.session_state['logged_in']}.json", dict(global_dict))
                    
                    st.session_state["reload"] = True