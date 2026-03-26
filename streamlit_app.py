"""
CAIT web UI (Streamlit). Calls the FastAPI backend — start the API first:

  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Then:

  streamlit run streamlit_app.py --server.port 8501

Local: optional env CAIT_API_URL=http://127.0.0.1:8000

Hosted (Streamlit Cloud): set secret CAIT_API_URL to your public API URL
(https://share.streamlit.io → app → Settings → Secrets).
"""

from __future__ import annotations

import os

import pandas as pd
import requests
import streamlit as st


def _default_api_url() -> str:
    """Streamlit Cloud secrets, then env, then localhost."""
    try:
        if hasattr(st, "secrets") and "CAIT_API_URL" in st.secrets:
            return str(st.secrets["CAIT_API_URL"]).rstrip("/")
    except Exception:
        pass
    return os.environ.get("CAIT_API_URL", "http://127.0.0.1:8000").rstrip("/")


def get(base: str, path: str) -> dict | list:
    r = requests.get(f"{base}{path}", timeout=15)
    r.raise_for_status()
    return r.json()


def post(base: str, path: str, body: dict) -> dict | list:
    r = requests.post(f"{base}{path}", json=body, timeout=15)
    r.raise_for_status()
    return r.json()


def delete_req(base: str, path: str) -> None:
    r = requests.delete(f"{base}{path}", timeout=15)
    r.raise_for_status()


st.set_page_config(page_title="CAIT", layout="wide", initial_sidebar_state="collapsed")

st.title("Capacity-Aware Intelligent Task Allocation")
st.caption("Runs against your FastAPI server (see sidebar).")

with st.sidebar:
    base = st.text_input(
        "API base URL",
        value=_default_api_url(),
        help="Public https URL of your FastAPI app (no trailing slash). On Streamlit Cloud, set secret CAIT_API_URL.",
    ).rstrip("/")

tab_dash, tab_team, tab_tasks = st.tabs(["Dashboard", "Team", "Tasks"])

with tab_dash:
    try:
        d = get(base, "/dashboard")
    except requests.RequestException as e:
        st.error(f"Could not reach API at `{base}`. Is uvicorn running? ({e})")
    else:
        c1, c2 = st.columns(2)
        c1.metric("Total tasks", d["total_tasks"])
        c2.metric("Overloaded (≥100%)", len(d["overloaded_users"]))

        st.subheader("Team utilization")
        if d["team_utilization"]:
            chart_df = pd.DataFrame(
                {
                    "Member": [u["name"] for u in d["team_utilization"]],
                    "Utilization %": [round(u["utilization_rate"] * 100, 1) for u in d["team_utilization"]],
                }
            ).set_index("Member")
            st.bar_chart(chart_df)
        else:
            st.info("No team members yet. Add some on the Team tab.")

        st.subheader("Overloaded users")
        if not d["overloaded_users"]:
            st.success("None — team is within capacity.")
        else:
            for u in d["overloaded_users"]:
                st.warning(
                    f"**{u['name']}** — {u['current_assigned_hours']} / "
                    f"{u['weekly_capacity_hours']} h "
                    f"({u['utilization_rate'] * 100:.1f}%)"
                )

with tab_team:
    with st.form("add_user"):
        name = st.text_input("Name", placeholder="Ada Lovelace")
        skills = st.text_input("Skills (comma-separated)", placeholder="Python, FastAPI")
        cap = st.number_input("Weekly capacity (hours)", min_value=0, value=20, step=1)
        submitted = st.form_submit_button("Add team member")
    if submitted:
        if not name.strip():
            st.error("Name is required.")
        else:
            skill_list = [s.strip() for s in skills.split(",") if s.strip()]
            try:
                post(
                    base,
                    "/users",
                    {
                        "name": name.strip(),
                        "skills": skill_list,
                        "weekly_capacity_hours": int(cap),
                        "current_assigned_hours": 0,
                    },
                )
                st.success("User added.")
                st.rerun()
            except requests.HTTPError as e:
                st.error(getattr(e.response, "text", None) or str(e))

    st.subheader("Members")
    try:
        users = get(base, "/users")
    except requests.RequestException as e:
        st.error(str(e))
    else:
        if not users:
            st.caption("No members yet.")
        for u in users:
            with st.expander(
                f"{u['name']} — {u['current_assigned_hours']}/{u['weekly_capacity_hours']} h"
            ):
                st.write("Skills:", ", ".join(u["skills"]) if u["skills"] else "(none)")
                if st.button("Remove member", key=f"remove_user_{u['id']}"):
                    try:
                        delete_req(base, f"/users/{u['id']}")
                        st.success("Member removed.")
                        st.rerun()
                    except requests.HTTPError as ex:
                        st.error(getattr(ex.response, "text", None) or str(ex))

    st.divider()
    st.subheader("Reset team")
    st.caption(
        "Removes **every** user and **every** task. Use for a clean demo or to start over."
    )
    reset_ok = st.checkbox("I understand this deletes all users and all tasks.")
    if st.button("Reset entire team and all tasks", disabled=not reset_ok):
        try:
            msg = post(base, "/reset", {})
            st.success(msg.get("message", "Reset complete."))
            st.rerun()
        except requests.HTTPError as e:
            st.error(getattr(e.response, "text", None) or str(e))

with tab_tasks:
    with st.form("add_task"):
        title = st.text_input("Title", placeholder="Implement dashboard", key="t_title")
        req_skill = st.text_input(
            "Required skill(s)",
            placeholder="Python or: Python, HTML, CSS",
            key="t_skill",
            help="One skill, or several separated by commas. A member must list every skill.",
        )
        est = st.number_input("Estimated hours", min_value=1, value=4, step=1)
        prio = st.selectbox("Priority", ["High", "Med", "Low"])
        tsub = st.form_submit_button("Create & auto-assign")
    if tsub:
        if not title.strip() or not req_skill.strip():
            st.error("Title and required skill are required.")
        else:
            try:
                res = post(
                    base,
                    "/tasks",
                    {
                        "title": title.strip(),
                        "required_skill": req_skill.strip(),
                        "estimated_hours": int(est),
                        "priority": prio,
                    },
                )
                if res.get("allocation_message"):
                    st.warning(res["allocation_message"])
                else:
                    st.success(
                        f"Assigned to user id **{res.get('assigned_user_id')}** "
                        f"({res.get('status')})."
                    )
                st.rerun()
            except requests.HTTPError as e:
                st.error(getattr(e.response, "text", None) or str(e))

    st.subheader("All tasks")
    try:
        tasks = get(base, "/tasks")
    except requests.RequestException as e:
        st.error(str(e))
    else:
        if not tasks:
            st.caption("No tasks yet.")
        for t in tasks:
            line = f"**{t['title']}** — {t['priority']} · {t['status']}"
            if t.get("assigned_user_id") is not None:
                line += f" → user #{t['assigned_user_id']}"
            st.markdown(line)
            st.caption(f"Skill: {t['required_skill']} · {t['estimated_hours']} h")
            if t.get("allocation_message"):
                st.caption(t["allocation_message"])
