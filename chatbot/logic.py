import google.generativeai as genai
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from events.models import Event, Category
from decouple import config

# Configure Gemini
api_key = config("GEMINI_API_KEY", default="")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

SYSTEM_PROMPT = """
You are 'EventHub Assistant', a professional and friendly chatbot for EventHub, 
a premium event registration platform. 

Your goals:
1. Help users discover events.
2. Explain how to use the platform (registration, payments via Razorpay).
3. Be concise and professional.
4. If a user asks for 'upcoming events' or a specific search, I will handle the data part, 
   but you should provide a friendly introduction.

Context: 
- Location: Sharnbasva University, Kalaburagi.
- Registration is free for organizers.
- Support Email: veeawaralli@gmail.com
"""

def get_chatbot_response(message_text):
    """
    Hybrid Chatbot Logic:
    1. Uses local logic for event searching (accurate & fast).
    2. Uses Gemini AI for natural conversation and general platform help.
    """
    message_lower = message_text.lower().strip()
    
    # 1. Local Logic: Check if they want to see events specifically
    if any(phrase in message_lower for phrase in ["show events", "list events", "upcoming events", "what's happening", "upcoming"]):
        events = Event.objects.filter(date__gte=timezone.now().date()).order_by('date')[:5]
        return format_event_list(events, "Sure! Here are some of the most exciting upcoming events on EventHub:")

    # 2. Local Logic: Specific Keyword Search (Fast Path)
    search_query = message_lower.replace("find", "").replace("search", "").replace("looking for", "").strip()
    if len(search_query) > 3 and not any(chip.lower() in search_query for chip in ["how", "what", "where", "why"]):
        events = Event.objects.filter(
            Q(title__icontains=search_query) | 
            Q(location__icontains=search_query) |
            Q(category__name__icontains=search_query)
        ).filter(date__gte=timezone.now().date()).distinct().order_by('date')[:5]
        
        if events.exists():
            return format_event_list(events, f"I found {events.count()} events related to '{search_query}':")

    # 3. Gemini AI: For everything else (Human-like conversation)
    if model:
        try:
            chat_response = model.generate_content(f"{SYSTEM_PROMPT}\n\nUser: {message_text}\nAssistant:")
            text = chat_response.text.strip()
            
            # Extract common chips based on response content or use defaults
            chips = ["Upcoming Events", "How to Register", "Browse Categories"]
            if "register" in text.lower(): chips = ["Sign Up", "Pricing Info", "Upcoming Events"]
            if "event" in text.lower(): chips = ["Show Events", "Categories", "Search"]
            
            return {
                "text": text,
                "chips": chips,
                "type": "text"
            }
        except Exception as e:
            # Fallback if Gemini fails
            pass

    # 4. Fallback (Local) - if Gemini is off or failed
    if any(word in message_lower for word in ["hi", "hello", "hey"]):
        return {
            "text": "Hello! I'm your EventHub assistant. I can help you find events or explain how registration works. What would you like to know?",
            "chips": ["Upcoming Events", "How to Register", "Browse Categories"],
            "type": "text"
        }

    return {
        "text": "I can help you browse events or answer questions about EventHub. Try asking 'What events are happening soon?'",
        "chips": ["Upcoming Events", "How to Register", "Contact Support"],
        "type": "text"
    }

def format_event_list(events, prefix):
    if not events:
        return {
            "text": "I couldn't find any upcoming events matching that request right now. Would you like to see all categories?",
            "chips": ["Browse Categories", "Upcoming Events", "All Events"],
            "type": "text"
        }
    
    event_data = []
    for event in events:
        event_data.append({
            "title": event.title,
            "date": event.date.strftime("%b %d, %Y"),
            "location": event.location,
            "url": event.get_absolute_url(),
            "price": "Free" if event.price == 0 else f"₹{int(event.price)}"
        })
    
    return {
        "text": prefix,
        "events": event_data,
        "type": "event_list",
        "chips": ["Show More Events", "Search by Category", "How to Register"]
    }
