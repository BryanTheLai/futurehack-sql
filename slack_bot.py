# slack_bot.py

import os
import threading
import datetime
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from src.cogniquery_crew.crew import CogniQueryCrew
from src.cogniquery_crew.tools.reporting_tools import ReportingTools

# Load environment variables from .env file
load_dotenv()

# --- Slack App Initialization ---
# Initialize with your bot token and app token
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

def run_cogniquery_and_reply(query: str, channel_id: str, client):
    """
    This function runs the long-running CogniQuery crew in a separate thread
    and sends the result back to the Slack channel.
    """
    try:
        print(f"🚀 Starting CogniQuery crew for query: '{query}'")

        # 1. Instantiate and run the CogniQuery crew
        db_conn_str = os.environ.get("NEONDB_CONN_STR")
        cogniquery_crew = CogniQueryCrew(db_connection_string=db_conn_str)
        crew_result = cogniquery_crew.crew().kickoff(inputs={'query': query})

        print(f"✅ Crew finished with result:\n{crew_result}")

        # 2. The final task saves the markdown report. We need to find and read it.
        markdown_report_path = "output/final_report.md"
        if not os.path.exists(markdown_report_path):
            raise FileNotFoundError("The final markdown report was not created by the crew.")
        
        with open(markdown_report_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # 3. Convert the markdown report to a PDF
        reporting_tool = ReportingTools()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_report_path = f"output/CogniQuery_Report_{timestamp}.pdf"
        
        pdf_creation_result = reporting_tool.create_report(
            markdown_content=markdown_content,
            report_file_path=pdf_report_path
        )
        print(f"📄 PDF Creation Result: {pdf_creation_result}")

        if not os.path.exists(pdf_report_path):
             raise FileNotFoundError(f"PDF generation failed. Tool message: {pdf_creation_result}")

        # 4. Upload the PDF report to the Slack channel
        client.files_upload_v2(
            channel=channel_id,
            file=pdf_report_path,
            title=f"CogniQuery Analysis for: '{query}'",
            initial_comment="Here is the detailed analysis you requested. The report includes key findings and data visualizations.",
        )
        print(f"🎉 Successfully uploaded report to channel {channel_id}")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        error_message = f"I'm sorry, I encountered an error while processing your request: `{str(e)}`"
        client.chat_postMessage(channel=channel_id, text=error_message)


@app.event("app_mention")
def handle_app_mention_events(body: dict, say, client):
    """
    This listener triggers when the bot is @mentioned in a channel.
    """
    print(f"🎯 Received app_mention event: {body}")
    
    event = body["event"]
    channel_id = event["channel"]
    user_id = event["user"]
    
    # Extract the bot's own user ID from the event
    bot_user_id = body.get("authorizations", [{}])[0].get("user_id")
    if not bot_user_id:
        # Fallback method to get bot user ID
        try:
            auth_response = client.auth_test()
            bot_user_id = auth_response["user_id"]
        except Exception as e:
            print(f"❌ Could not get bot user ID: {e}")
            bot_user_id = None

    # Remove the bot's user ID from the message text to get the clean query
    query = event["text"]
    if bot_user_id:
        query = query.replace(f"<@{bot_user_id}>", "").strip()
    
    print(f"🤖 Received mention in channel {channel_id} from user {user_id}")
    print(f"📝 Raw message: {event['text']}")
    print(f"🔍 Extracted query: '{query}'")

    if not query:
        say("Hi! Please provide a question about your data after mentioning me. For example: `@CogniQuery Bot What are our top selling products?`")
        return

    # Acknowledge the request immediately to avoid Slack timeout errors
    say(f"On it! I'm analyzing your request: *'{query}'*... This might take a minute.")

    # Run the intensive crew process in a separate thread
    thread = threading.Thread(
        target=run_cogniquery_and_reply,
        args=(query, channel_id, client)
    )
    thread.start()

# Add a simple test event handler to verify the bot is receiving events
@app.event("message")
def handle_message_events(body, logger):
    """
    This is just for debugging - to see if we're receiving any events at all
    """
    print(f"📨 Received message event (for debugging): {body.get('event', {}).get('text', 'No text')}")

# Add error handling
@app.error
def global_error_handler(error, body, logger):
    print(f"❌ Global error occurred: {error}")
    print(f"Body: {body}")

if __name__ == "__main__":
    print("⚡️ CogniQuery Slack Bot is starting...")
    print("📡 Attempting to connect to Slack via Socket Mode...")
    
    try:
        # Use SocketModeHandler for easy local development without exposing a public URL
        handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
        print("✅ Socket Mode handler created successfully")
        print("🚀 Bot is now running and listening for events...")
        handler.start()
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        import traceback
        traceback.print_exc()