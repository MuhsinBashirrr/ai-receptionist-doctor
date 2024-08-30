from flask import Flask, render_template, request, jsonify
import time
import random
import threading

app = Flask(__name__)

class State:
    INITIAL = 'initial'
    EMERGENCY = 'emergency'
    MESSAGE = 'message'
    LOCATION = 'location'
    FINAL = 'final'

class AIReceptionist:
    def __init__(self):
        self.reset()

    def reset(self):
        """Reset the AI receptionist to its initial state for a new session."""
        self.state = State.INITIAL
        self.emergency_type = None
        self.location = None
        self.message = None
        self.database_thread = None
        self.emergency_responses = {
            "not breathing": "Start CPR immediately. Place your hands on the center of the chest and push hard and fast at a rate of 100-120 compressions per minute. After every 30 compressions, give 2 rescue breaths.",
            "chest pain": "Help the person sit down and rest comfortably. Loosen any tight clothing. If the person takes heart medication like nitroglycerin, help them take it.",
            "severe bleeding": "Apply direct pressure to the wound using a clean cloth or sterile bandage. If possible, elevate the injured area above the heart.",
            "broken bone": "Do not attempt to realign the bone. Immobilize the injured area and apply a cold pack wrapped in a towel to reduce swelling.",
            "allergic reaction": "If the person has an epinephrine auto-injector (EpiPen), help them use it according to the instructions. Remove any allergens if possible.",
        }

    def simulate_database_call(self, emergency):
        """Simulate a delay for fetching emergency instructions from a database."""
        time.sleep(15)  # Simulate a 15-second delay
        return self.emergency_responses.get(emergency.lower(), 
            "Stay calm and do not move the patient unless they are in immediate danger. Wait for professional help.")

    def simulate_database_call_async(self):
        """Perform the database call in a separate thread to avoid blocking the main thread."""
        def target():
            self.database_thread.result = self.simulate_database_call(self.emergency_type)
        thread = threading.Thread(target=target)
        thread.start()
        return thread

    def get_eta(self):
        """Generate a random estimated time of arrival (ETA) for the doctor."""
        return random.randint(5, 20)

    def process_input(self, user_input):
        """Process user input and generate an appropriate response based on the current state."""
        user_input = user_input.strip().lower()

        # Handle initial state
        if self.state == State.INITIAL:
            if not user_input:
                return "Are you having an emergency or would you like to leave a message?"
            if "emergency" in user_input:
                self.state = State.EMERGENCY
                return "I understand this is an emergency. Can you please tell me what the specific emergency is?"
            elif "message" in user_input:
                self.state = State.MESSAGE
                return "Certainly, I can take a message for Dr. Adrin. What message would you like to leave?"
            else:
                return "I'm sorry, I didn't understand that. Are you having an emergency or would you like to leave a message?"

        # Handle emergency state
        elif self.state == State.EMERGENCY:
            self.emergency_type = user_input
            self.state = State.LOCATION
            self.database_thread = self.simulate_database_call_async()
            return "I am checking what you should do immediately. Meanwhile, can you tell me which area you are located right now?"

        # Handle location state
        elif self.state == State.LOCATION:
            self.location = user_input
            eta = self.get_eta()
            response = f"Dr. Adrin will be coming to your location immediately. The estimated time of arrival is {eta} minutes."

            # Wait for the database thread to finish
            if self.database_thread:
                self.database_thread.join()

            emergency_response = getattr(self.database_thread, 'result', 
                "Please follow basic first aid procedures.")
            return f"{response} Meanwhile, we suggest that you {emergency_response}"

        # Handle message state
        elif self.state == State.MESSAGE:
            self.message = user_input
            self.state = State.FINAL
            return "Thanks for the message. We will forward it to Dr. Adrin."

        # Handle final state
        elif self.state == State.FINAL:
            if "late" in user_input:
                emergency_response = self.simulate_database_call(self.emergency_type)
                return f"I understand that you are worried that Dr. Adrin will arrive too late. Meanwhile, we suggest that you {emergency_response}. Please follow these steps while the doctor comes to help the patient get better."
            return "Is there anything else I can help you with? If not, please follow the instructions provided and stay calm. Dr. Adrin will be with you shortly."

        # Fallback response for unrecognized input
        return "I'm sorry, I don't understand that. Could you please rephrase your request?"

# Initialize AI receptionist
ai_receptionist = AIReceptionist()

@app.route('/')
def index():
    # Reset the AI receptionist for each new session
    ai_receptionist.reset()
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    # Handle incoming user input and provide an AI response
    user_input = request.json.get('message')
    response = ai_receptionist.process_input(user_input)
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True)
