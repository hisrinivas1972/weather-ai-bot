from pyngrok import ngrok
import subprocess

# Update ngrok with the new authtoken (replace with your authtoken)
!ngrok config add-authtoken {your token}

# Kill existing processes
!pkill ngrok
!pkill streamlit

# Start the Streamlit app
app_process = subprocess.Popen(['streamlit', 'run', '/content/multi_chatbot.py'])

# Create a public URL
public_url = ngrok.connect(8501)
print(f'Streamlit app is running at: {public_url}')
