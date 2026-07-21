import streamlit as st

from api import APIError, get_result, get_status, upload_image

st.set_page_config(
    page_title="Vehicle Image Processing System",
    layout="centered",
)

if "processing_id" not in st.session_state:
    st.session_state.processing_id = None
if "current_status" not in st.session_state:
    st.session_state.current_status = None


def display_status(status: str) -> None:
    status_messages = {
        "pending": (st.warning, "Pending"),
        "processing": (st.info, "Processing"),
        "completed": (st.success, "Completed"),
        "failed": (st.error, "Failed"),
    }
    display, label = status_messages.get(status, (st.warning, status.title()))
    display(f"Current status: {label}")


st.title("Vehicle Image Processing System")
st.write("Upload a vehicle image to analyze its quality and license plate information.")

st.header("Upload Image")
uploaded_file = st.file_uploader(
    "Choose a vehicle image",
    type=["jpg", "jpeg", "png"],
)

if uploaded_file is not None:
    st.image(uploaded_file, caption=uploaded_file.name, width="stretch")

if st.button("Upload", type="primary", disabled=uploaded_file is None):
    try:
        response = upload_image(uploaded_file)
        st.session_state.processing_id = response["id"]
        st.session_state.current_status = response.get("status", "pending")
        st.success("Upload Successful")
    except (APIError, KeyError) as error:
        st.error(f"Upload failed: {error}")

if st.session_state.processing_id is not None:
    st.write(f"**Processing ID:** {st.session_state.processing_id}")

    st.header("Processing Status")
    if st.button("Refresh Status"):
        try:
            response = get_status(st.session_state.processing_id)
            st.session_state.current_status = response["status"]
        except (APIError, KeyError) as error:
            st.error(f"Could not refresh status: {error}")

    if st.session_state.current_status:
        display_status(st.session_state.current_status)

    st.header("Analysis Result")
    if st.session_state.current_status != "completed":
        st.info("Analysis not available yet.")
    else:
        try:
            result = get_result(st.session_state.processing_id)
            first_row = st.columns(2)
            first_row[0].metric("Blur Score", result.get("blur_score"))
            first_row[1].metric("Brightness Score", result.get("brightness_score"))

            st.text_area(
                "OCR Text",
                result.get("extracted_text") or "No text detected",
                disabled=True,
            )

            second_row = st.columns(2)
            second_row[0].metric(
                "Vehicle Plate Number",
                result.get("plate_text") or "Not detected",
            )
            second_row[1].metric(
                "Plate Valid",
                "Yes" if result.get("plate_valid") else "No",
            )

            third_row = st.columns(2)
            third_row[0].metric(
                "Duplicate",
                "Yes" if result.get("duplicate") else "No",
            )
            third_row[1].write(f"**Remarks**\n\n{result.get('remarks') or 'None'}")
        except (APIError, KeyError) as error:
            st.error(f"Could not load analysis result: {error}")
