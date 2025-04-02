from agents.supervisor import Supervisor
import json
import os
import streamlit as st
import re
import time
from datetime import datetime

current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, "config", "agents.yml")
log_dir = os.path.join(current_dir, "logs")
os.makedirs(log_dir, exist_ok=True)

st.set_page_config(page_title="Agentic KYC Dashboard")
st.title("📊 Agentic KYC Dashboard")

supervisor = Supervisor(config_path)
with open("data/customer_data.json") as f:
    customers = json.load(f)

# Tabs for separation
customer_tab, agent_tab, log_tab = st.tabs(["📄 Customer KYC Results", "🧩 Agent Task Execution", "📜 Logs"])

agent_outputs = {}
agent_times = {}

with customer_tab:
    st.title("📄 Customer KYC Summary")
    progress_text = st.empty()
    progress_bar = st.progress(0)

    def update_progress(step, total, customer, agent):
        percent = int((step + 1) / total * 100)
        progress_bar.progress(percent)
        progress_text.text(f"Running agent '{agent}' for customer '{customer}'... ({percent}%)")

    if 'results' not in st.session_state:
        st.session_state.results = supervisor.run_all(customers, callback=update_progress)
    results = st.session_state.results

    if 'log_written' not in st.session_state:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file_path = os.path.join(log_dir, f"log_{timestamp}.json")
        with open(log_file_path, "w") as log_file:
            json.dump(results, log_file, indent=2)
        st.session_state.log_written = True

    progress_bar.empty()
    progress_text.text("✅ All agents completed.")

    # Prepare output and time for agent dashboard
    for agent_def in supervisor.agent_defs:
        agent_name = agent_def['name']
        start_time = time.time()
        combined_output = []
        for customer in customers:
            result = results[customer['name']].get(agent_name, "")
            combined_output.append(f"**{customer['name']}**\n{result.strip()}\n")
        elapsed = time.time() - start_time
        output_text = "\n---\n".join(combined_output)
        clean_output = re.sub(r'\*\*(.*?)\*\*', r'\1', output_text)
        clean_output = re.sub(r'(?m)^\s*(\d+)\.', r'\1.', clean_output)
        agent_outputs[agent_name] = clean_output
        agent_times[agent_name] = elapsed

    table_data = []
    for name, tasks in results.items():
        risk_score = "-"
        risk_color = ""
        id_status = "❓"
        watchlist_status = "❓"
        block_status = "-"

        if "RiskScorer" in tasks:
            score = None
            full_output = tasks["RiskScorer"]
            match = re.search(r"risk score.*?(\d{1,2})", full_output.lower())
            if match:
                score = int(match.group(1))
            if score is not None and 1 <= score <= 10:
                risk_score = f"{score}"
                if score <= 3:
                    risk_color = "🟢"
                    block_status = "✅ Clear"
                elif score <= 6:
                    risk_color = "🟡"
                    block_status = "⚠️ Manual Review"
                else:
                    risk_color = "🔴"
                    block_status = "🚫 Blocked"
                risk_score = f"{risk_color} {score}"

        if "IDValidator" in tasks:
            if "does not meet" in tasks["IDValidator"]:
                id_status = "❌"
            elif "meets" in tasks["IDValidator"]:
                id_status = "✅"

        if "WatchlistChecker" in tasks:
            if "not on any known watchlists" in tasks["WatchlistChecker"]:
                watchlist_status = "No"
            elif "flagged" in tasks["WatchlistChecker"]:
                watchlist_status = "Yes"

        table_data.append({
            "Customer": name,
            "ID Valid": id_status,
            "Watchlist": watchlist_status,
            "Risk Score": risk_score,
            "Decision": block_status
        })

    st.subheader("📋 KYC Summary Table")
    st.dataframe(table_data, use_container_width=True)

    st.subheader("🔎 Detailed Results")
    for name, tasks in results.items():
        with st.expander(f"Details for {name}"):
            for agent_name, output in tasks.items():
                st.subheader(agent_name)
                clean_output = re.sub(r'\*\*(.*?)\*\*', r'\1', output)
                clean_output = re.sub(r'(?m)^\s*(\d+)\.', r'\1.', clean_output)
                lines = clean_output.count('\n') + 1
                avg_chars_per_line = 90
                estimated_lines = max(lines, len(clean_output) // avg_chars_per_line)
                dynamic_height = min(max(100, estimated_lines * 25), 600)
                st.markdown(f"<div style='white-space:pre-wrap; background-color:#111; padding:1em; border-radius:0.5em; color:white; font-family:inherit'>{clean_output}</div>", unsafe_allow_html=True)
                st.markdown("---")

with agent_tab:
    st.title("🧩 Agent Execution Dashboard")
    agents_list = supervisor.agent_defs

    for agent_def in agents_list:
        agent_name = agent_def['name']
        with st.container():
            cols = st.columns([6, 2, 2])
            with cols[0]:
                st.markdown(f"✅ **{agent_name}**")
            with cols[1]:
                run_key = f"run_{agent_name}"
                run_btn = st.button("▶️ Execute", key=run_key)
            with cols[2]:
                time_placeholder = st.empty()
                if agent_name in agent_times:
                    time_placeholder.markdown(f"⏱ **{agent_times[agent_name]:.2f}s**")

            output_container = st.empty()

            if agent_name in agent_outputs:
                output_container.expander("🔍 Output").markdown(
                    f"<div style='white-space:pre-wrap; background-color:#111; padding:1em; border-radius:0.5em; color:white; font-family:inherit'>{agent_outputs[agent_name]}</div>",
                    unsafe_allow_html=True)

            if run_btn:
                with st.spinner(f"Running {agent_name} for all customers..."):
                    start_time = time.time()
                    from agents.kyc_agents import Agent
                    agent = Agent(**agent_def)
                    combined_output = []
                    for customer in customers:
                        result = agent.run(customer)
                        combined_output.append(f"**{customer['name']}**\n{result.strip()}\n")
                    elapsed = time.time() - start_time
                    output_text = "\n---\n".join(combined_output)
                    clean_output = re.sub(r'\*\*(.*?)\*\*', r'\1', output_text)
                    clean_output = re.sub(r'(?m)^\s*(\d+)\.', r'\1.', clean_output)
                    agent_outputs[agent_name] = clean_output
                    agent_times[agent_name] = elapsed
                    time_placeholder.markdown(f"⏱ **{elapsed:.2f}s**")
                    output_container.expander("🔍 Output").markdown(
                        f"<div style='white-space:pre-wrap; background-color:#111; padding:1em; border-radius:0.5em; color:white; font-family:inherit'>{clean_output}</div>",
                        unsafe_allow_html=True)
                    st.markdown("---")

with log_tab:
    st.title("📜 Past Execution Logs")
    log_files = sorted([f for f in os.listdir(log_dir) if f.endswith(".json")], reverse=True)

    if not log_files:
        st.info("No logs available yet.")
    else:
        selected_log = st.selectbox("Select a log file to view", log_files)
        with open(os.path.join(log_dir, selected_log)) as log_file:
            log_data = json.load(log_file)
        for customer, tasks in log_data.items():
            with st.expander(f"📌 {customer}"):
                for agent_name, output in tasks.items():
                    st.subheader(agent_name)
                    clean_output = re.sub(r'\*\*(.*?)\*\*', r'\1', output)
                    clean_output = re.sub(r'(?m)^\s*(\d+)\.', r'\1.', clean_output)
                    st.markdown(f"<div style='white-space:pre-wrap; background-color:#111; padding:1em; border-radius:0.5em; color:white; font-family:inherit'>{clean_output}</div>", unsafe_allow_html=True)
                st.markdown("---")
