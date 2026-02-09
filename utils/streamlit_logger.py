import streamlit as st
import sys
import threading
import html

class StreamlitLogger:
    def __init__(self):
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        self._lock = threading.Lock()

    def write(self, message):
        if message.strip():
            with self._lock:
                if "agent_logs" not in st.session_state:
                    st.session_state.agent_logs = []
                st.session_state.agent_logs.append(message.rstrip())
                
                # Update live log placeholder if available
                if hasattr(st.session_state, 'live_log_placeholder') and st.session_state.live_log_placeholder is not None:
                    try:
                        logs = st.session_state.agent_logs[-50:]  # Last 50 logs
                        lines = [f'<p style="margin: 2px 0; color: #e5e7eb;">{html.escape(log)}</p>' for log in logs]
                        # Use img onerror hack to trigger scroll
                        html_content = f'''
                            <div class="log-box-live" id="live-logs">{"".join(lines)}</div>
                            <img src="x" style="display:none" onerror="var el=document.getElementById('live-logs'); if(el) el.scrollTop=el.scrollHeight;">
                        '''
                        st.session_state.live_log_placeholder.markdown(html_content, unsafe_allow_html=True)
                    except:
                        pass
        self._stdout.write(message)

    def flush(self):
        self._stdout.flush()

def enable_streamlit_logging():
    # Only set up once
    if not isinstance(sys.stdout, StreamlitLogger):
        logger = StreamlitLogger()
        sys.stdout = logger
        sys.stderr = logger