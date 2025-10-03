# manage_vector_stores.py
# -------------------------------------------------------------
# Streamlit UI to inspect & manage OpenAI uploaded files and
# vector stores:
# - List all uploaded files
# - List all vector stores (id + name)
# - Inspect files within a selected vector store
# - Delete selected files, vector stores, or files in a store
#
# Tested with openai==1.101.0
# -------------------------------------------------------------

import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
import streamlit as st


# -----------------------------
# Helpers: OpenAI client & utils
# -----------------------------
def get_client() -> OpenAI:
    """
    Create an OpenAI client from the OPENAI_API_KEY environment variable.
    Streamlit-safe: show an error in the UI if the key is missing.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        st.error("OPENAI_API_KEY is not set in your environment.")
        st.stop()
    return OpenAI(api_key=api_key)


def _safe(attr, default=""):
    """Return a safe string value for display."""
    if attr is None:
        return default
    return str(attr)


# -----------------------------
# Data access functions
# -----------------------------
def list_all_files(client: OpenAI) -> List[Any]:
    """
    List all uploaded files in your account (first page).
    The object typically has: id, filename, bytes, created_at, purpose, etc.
    """
    try:
        resp = client.files.list()
        return list(resp.data or [])
    except Exception as e:
        st.error(f"Error listing files: {e}")
        return []


def delete_files(client: OpenAI, file_ids: List[str]) -> Dict[str, str]:
    """
    Delete multiple files by id. Returns a status map {file_id: "ok"/"error:..."}.
    """
    results = {}
    for fid in file_ids:
        try:
            client.files.delete(file_id=fid)
            results[fid] = "ok"
        except Exception as e:
            results[fid] = f"error: {e}"
    return results


def list_vector_stores(client: OpenAI) -> List[Any]:
    """
    List all vector stores (first page).
    Vector store objects typically include: id, name, created_at, etc.
    """
    try:
        # If your SDK has pagination, you can add limit=... here as needed.
        resp = client.vector_stores.list()
        return list(resp.data or [])
    except Exception as e:
        st.error(f"Error listing vector stores: {e}")
        return []


def delete_vector_stores(client: OpenAI, vs_ids: List[str]) -> Dict[str, str]:
    """
    Delete multiple vector stores by id. Returns a status map {vs_id: "ok"/"error:..."}.
    """
    results = {}
    for vsid in vs_ids:
        try:
            client.vector_stores.delete(vector_store_id=vsid)
            results[vsid] = "ok"
        except Exception as e:
            results[vsid] = f"error: {e}"
    return results


def list_vector_store_files(client: OpenAI, vector_store_id: str) -> List[Any]:
    """
    List files attached to a given vector store (first page).
    """
    try:
        resp = client.vector_stores.files.list(vector_store_id=vector_store_id)
        return list(resp.data or [])
    except Exception as e:
        st.error(f"Error listing files for vector store {vector_store_id}: {e}")
        return []


def delete_vector_store_files(client: OpenAI, vector_store_id: str, file_ids: List[str]) -> Dict[str, str]:
    """
    Delete specific files from a vector store (detach/remove from index).
    Returns status map.
    """
    results = {}
    for fid in file_ids:
        try:
            client.vector_stores.files.delete(vector_store_id=vector_store_id, file_id=fid)
            results[fid] = "ok"
        except Exception as e:
            results[fid] = f"error: {e}"
    return results


# -----------------------------
# UI helpers
# -----------------------------
def render_status_table(status_map: Dict[str, str], what: str):
    """
    Show a small table-like status for deletion operations.
    """
    if not status_map:
        return
    st.write(f"**Result of deleting {what}:**")
    for k, v in status_map.items():
        if v == "ok":
            st.success(f"{what} {k}: deleted")
        else:
            st.error(f"{what} {k}: {v}")


# -----------------------------
# Streamlit App
# -----------------------------
st.set_page_config(page_title="OpenAI Files & Vector Stores", page_icon="🧰", layout="wide")
st.title("🧰 OpenAI File & Vector Store Manager")

client = get_client()

# Tabs: Files | Vector Stores
tab_files, tab_stores = st.tabs(["📄 Files", "🗂️ Vector Stores"])

# -----------------------------
# Tab: Files
# -----------------------------
with tab_files:
    st.subheader("All uploaded files")

    files = list_all_files(client)

    if not files:
        st.info("No files found.")
    else:
        # Quick action: Select all images
        st.divider()
        if st.button("Select all images"):
            for f in files:
                fid = _safe(getattr(f, "id", ""))
                fname = _safe(getattr(f, "filename", getattr(f, "display_name", ""))).lower()
                if fname.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")):
                    st.session_state[f"sel_file_{fid}"] = True

        # Show a compact table
        cols = st.columns([2, 3, 3, 2, 2])
        with cols[0]:
            st.markdown("**Select**")
        with cols[1]:
            st.markdown("**File ID**")
        with cols[2]:
            st.markdown("**Name**")
        with cols[3]:
            st.markdown("**Bytes**")
        with cols[4]:
            st.markdown("**Purpose**")

        selected_file_ids = []
        for f in files:
            fid = _safe(getattr(f, "id", ""))
            fname = _safe(getattr(f, "filename", getattr(f, "display_name", "")))
            fbytes = _safe(getattr(f, "bytes", ""))
            fpurpose = _safe(getattr(f, "purpose", ""))

            row = st.columns([2, 3, 3, 2, 2])
            with row[0]:
                if st.checkbox("", key=f"sel_file_{fid}"):
                    selected_file_ids.append(fid)
            row[1].code(fid, language="text")
            row[2].write(fname or "—")
            row[3].write(fbytes or "—")
            row[4].write(fpurpose or "—")

        st.divider()
        col1, col2 = st.columns([1, 5])
        with col1:
            confirm = st.checkbox("Confirm deletion")
        with col2:
            if st.button("🗑️ Delete selected files", disabled=not selected_file_ids or not confirm):
                status = delete_files(client, selected_file_ids)
                render_status_table(status, "file")
                st.experimental_rerun()

# -----------------------------
# Tab: Vector Stores
# -----------------------------
with tab_stores:
    st.subheader("All vector stores")

    stores = list_vector_stores(client)

    if not stores:
        st.info("No vector stores found.")
    else:
        # Table header
        cols = st.columns([2, 3, 3])
        with cols[0]:
            st.markdown("**Select**")
        with cols[1]:
            st.markdown("**Vector Store ID**")
        with cols[2]:
            st.markdown("**Name**")

        selected_vs_ids = []
        for vs in stores:
            vsid = _safe(getattr(vs, "id", ""))
            vsname = _safe(getattr(vs, "name", ""))

            row = st.columns([2, 3, 3])
            with row[0]:
                if st.checkbox("", key=f"sel_vs_{vsid}"):
                    selected_vs_ids.append(vsid)
            row[1].code(vsid, language="text")
            row[2].write(vsname or "—")

        st.divider()
        col1, col2, col3 = st.columns([2, 2, 6])

        # Pick one store to inspect its files
        with col1:
            selected_detail_vs: Optional[str] = st.selectbox(
                "Inspect files in vector store",
                options=["—"] + [getattr(vs, "id", "") for vs in stores],
                index=0,
                key="vs_detail_select",
            )

        # Confirm + delete selected vector stores
        with col2:
            confirm_vs = st.checkbox("Confirm VS deletion", key="confirm_vs_del")
        with col3:
            if st.button("🗑️ Delete selected vector stores", disabled=not selected_vs_ids or not confirm_vs):
                status = delete_vector_stores(client, selected_vs_ids)
                render_status_table(status, "vector store")
                st.experimental_rerun()

        # Show files within the chosen store and allow detaching/deleting them from the store
        if selected_detail_vs and selected_detail_vs != "—":
            st.markdown("### Files in selected vector store")
            vs_files = list_vector_store_files(client, selected_detail_vs)

            if not vs_files:
                st.info("No files attached to this store.")
            else:
                # Quick action: Select all images in this store
                st.divider()
                if st.button("Select all images in this store"):
                    for vfile in vs_files:
                        vsfid = _safe(getattr(vfile, "id", ""))
                        file_ref = _safe(getattr(vfile, "file_id", getattr(vfile, "id", "")))
                        fname = ""
                        try:
                            fobj = client.files.retrieve(file_id=file_ref)
                            fname = _safe(getattr(fobj, "filename", getattr(fobj, "display_name", ""))).lower()
                        except Exception:
                            fname = ""
                        if fname.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")):
                            st.session_state[f"sel_vsfile_{selected_detail_vs}_{vsfid}"] = True

                cols2 = st.columns([2, 3, 3])
                with cols2[0]:
                    st.markdown("**Select**")
                with cols2[1]:
                    st.markdown("**File ID**")
                with cols2[2]:
                    st.markdown("**State / Status**")

                selected_vs_file_ids = []
                for vfile in vs_files:
                    fid = _safe(getattr(vfile, "id", ""))
                    # Vector-store-file entries often include processing status
                    state = _safe(getattr(vfile, "status", getattr(vfile, "state", "")))

                    row2 = st.columns([2, 3, 3])
                    with row2[0]:
                        if st.checkbox("", key=f"sel_vsfile_{selected_detail_vs}_{fid}"):
                            selected_vs_file_ids.append(fid)
                    row2[1].code(fid, language="text")
                    row2[2].write(state or "—")

                st.divider()
                colA, colB = st.columns([1, 5])
                with colA:
                    confirm_vf = st.checkbox("Confirm deletion (from this store)", key="confirm_vsfile_del")
                with colB:
                    if st.button(
                        "🗑️ Remove selected files from this vector store",
                        disabled=not selected_vs_file_ids or not confirm_vf
                    ):
                        status = delete_vector_store_files(client, selected_detail_vs, selected_vs_file_ids)
                        render_status_table(status, f"file in store {selected_detail_vs}")
                        st.experimental_rerun()
