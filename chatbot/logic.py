import google.generativeai as genai
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from events.models import Event, Category
from decouple import config
import logging

logger = logging.getLogger(__name__)

# Configure Gemini
api_key = config("GEMINI_API_KEY", default="").strip(' "\'')
if api_key:
    genai.configure(api_key=api_key)
    # Model chain: try primary first, fall back to others if rate-limited
    GEMINI_MODELS = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-2.0-flash-lite']
    model = genai.GenerativeModel(GEMINI_MODELS[0])
else:
    model = None
    GEMINI_MODELS = []

def get_platform_context():
    """Fetches real-time facts about the platform to help Gemini answer accurately."""
    now = timezone.now().date()
    
    upcoming_count = Event.objects.filter(date__gte=now).count()
    total_events = Event.objects.count()
    past_events = Event.objects.filter(date__lt=now).count()
    categories = list(Category.objects.all().values_list('name', flat=True))
    
    # Get some upcoming event details for richer context
    upcoming_events = Event.objects.filter(date__gte=now).order_by('date')[:5]
    event_details = []
    for event in upcoming_events:
        price_str = "Free" if event.price == 0 else f"₹{int(event.price)}"
        event_details.append(
            f"- {event.title} on {event.date.strftime('%b %d, %Y')} at {event.location} ({price_str})"
        )
    
    context = f"Platform stats: {upcoming_count} upcoming events, {past_events} past events, {total_events} total events."
    if categories:
        context += f"\nAvailable categories: {', '.join(categories)}."
    if event_details:
        context += f"\nUpcoming events:\n" + "\n".join(event_details)
    
    return context

SYSTEM_PROMPT = """
You are 'EventHub Assistant', a professional and friendly conversational AI for EventHub — an online event discovery and registration platform.

## About EventHub
- EventHub is a platform where organizers can create and manage events, and users can discover, register, and attend events.
- Located primarily for: Sharnbasva University, Kalaburagi.
- Support email: veeawaralli@gmail.com

## Your Capabilities — You can answer ALL types of questions:

### 1. Event Discovery
- Help users find and learn about upcoming events
- Provide event details like dates, locations, and pricing
- Suggest events based on interests or categories

### 2. Platform Usage
- Explain how to register for an account (free signup, email verification required)
- How to browse and search for events
- How to register for specific events
- How to become an event organizer/provider
- How the ticketing system works (QR code tickets, email confirmations)
- How payments work (via Razorpay for paid events)

### 3. Platform Features
- Event categories and tags for easy discovery
- Reviews and ratings for events
- Comments on event pages
- Social sharing of events
- Calendar integration (add events to personal calendar)
- Waitlist system for sold-out events
- QR code ticketing and attendance tracking
- Organizer dashboard with analytics
- Email notifications for registrations and updates

### 4. General Knowledge
- You can answer general questions, greetings, and have friendly conversations
- For non-platform questions, provide helpful answers but gently guide users back to EventHub when relevant

### 5. Policies & Support
- Privacy policy, terms of service, refund policy inquiries
- Contact information and support channels
- Account management (password reset, profile updates)

## Response Guidelines:
- Be concise but informative (2-4 sentences for simple questions, more for complex ones)
- Use a warm, professional tone with occasional emojis
- Format responses clearly with line breaks for readability
- If you don't know something specific, say so honestly and suggest contacting support
- NEVER make up event details — only reference events from the PLATFORM CONTEXT provided
- For event listings, keep descriptions brief and suggest visiting the event page for full details
"""

def get_chatbot_response(message_text, chat_history=None):
    """
    Chatbot Logic with Gemini AI and local data fallback:
    - Uses Gemini for ALL conversational queries
    - Supplements with real-time platform data when relevant
    - Falls back to local responses if Gemini is unavailable
    """
    message_lower = message_text.lower().strip()
    platform_facts = get_platform_context()
    
    # 1. Check if user is asking about events (for local data supplement)
    local_data = None
    is_event_query = any(phrase in message_lower for phrase in [
        "show events", "list events", "upcoming events", "upcoming",
        "what events", "any events", "find events", "search events",
        "what's happening", "whats happening", "events near",
        "show more events"
    ])
    
    if is_event_query:
        events = Event.objects.filter(date__gte=timezone.now().date()).order_by('date')[:5]
        local_data = format_event_list(events, "Here are some exciting upcoming events for you:")

    # 2. AI Conversational Path (Gemini) — handles ALL questions
    if model and GEMINI_MODELS:
        # Prepare the history for Gemini (convert from our session format)
        gemini_history = []
        if chat_history:
            for msg in chat_history[-10:]:  # Limit to last 10 turns
                gemini_history.append({
                    "role": "user" if msg["role"] == "user" else "model",
                    "parts": [msg["content"]]
                })

        # Inject facts into the context for this specific prompt
        full_prompt = f"{SYSTEM_PROMPT}\n\n[CURRENT PLATFORM CONTEXT]:\n{platform_facts}\n\n[USER MESSAGE]: {message_text}"

        last_error = "No models available"
        # Try each model in the fallback chain
        for model_name in GEMINI_MODELS:
            try:
                current_model = genai.GenerativeModel(model_name)
                chat = current_model.start_chat(history=gemini_history)
                chat_response = chat.send_message(full_prompt)
                text = chat_response.text.strip()
                
                # Generate contextual chips based on what the user asked
                chips = get_contextual_chips(message_lower)
                
                if local_data:
                    # If we found local event data, merge with AI text
                    return {
                        "text": text,
                        "events": local_data["events"],
                        "type": "event_list",
                        "chips": local_data["chips"]
                    }
                
                return {
                    "text": text,
                    "chips": chips,
                    "type": "text"
                }
            except Exception as e:
                logger.error(f"Gemini API error with {model_name}: {type(e).__name__}: {e}")
                last_error = f"{type(e).__name__}: {e}"
                continue  # Try next model in the chain

    # 3. Local Fallback (If Gemini is unavailable or failed)
    if local_data:
        return local_data

    # 4. Smart local fallback for common questions when AI is down
    fallback_response = get_local_fallback(message_lower)
    if fallback_response:
        return fallback_response

    # 5. Global Fallback (API is dead and local logic didn't match perfectly)
    # Give a polite default instead of exposing raw backend server exceptions
    return {
        "text": "I'm having a little trouble connecting to my AI processor right now 🔌, but I'm still here to help! What would you like to know about? Try clicking one of the common topics below.",
        "chips": ["Upcoming Events", "How to Register", "Contact Support", "Browse Categories"],
        "type": "text"
    }


def get_contextual_chips(message_lower):
    """Return context-aware chip suggestions based on what the user is asking about."""
    if any(w in message_lower for w in ["register", "signup", "sign up", "account", "join"]):
        return ["Browse Events", "How does payment work?", "Contact Support"]
    elif any(w in message_lower for w in ["pay", "price", "cost", "ticket", "fee"]):
        return ["Upcoming Events", "Free Events", "How to Register"]
    elif any(w in message_lower for w in ["organiz", "create event", "host", "provider"]):
        return ["How to Register", "Upcoming Events", "Contact Support"]
    elif any(w in message_lower for w in ["hello", "hi", "hey", "good"]):
        return ["Upcoming Events", "How to Register", "Browse Categories"]
    elif any(w in message_lower for w in ["help", "support", "contact", "issue", "problem"]):
        return ["How to Register", "Upcoming Events", "Browse Categories"]
    elif any(w in message_lower for w in ["review", "rating", "feedback"]):
        return ["Upcoming Events", "How to Register", "Browse Categories"]
    elif any(w in message_lower for w in ["category", "categories", "type", "kind"]):
        return ["Upcoming Events", "How to Register", "Contact Support"]
    else:
        return ["Upcoming Events", "How to Register", "Browse Categories"]


def get_local_fallback(message_lower):
    """Provides smart local fallback responses when AI is unavailable."""
    
    if any(w in message_lower for w in ["hello", "hi", "hey", "good morning", "good evening"]):
        return {
            "text": "Hello! 👋 Welcome to EventHub! I'm your assistant. How can I help you today? You can ask me about upcoming events, how to register, or anything about the platform!",
            "chips": ["Upcoming Events", "How to Register", "Browse Categories"],
            "type": "text"
        }
    
    if any(w in message_lower for w in ["register", "signup", "sign up", "how to join"]):
        return {
            "text": "Registering on EventHub is easy and free! 🎉\n\n1. Click 'Sign Up' on the top right\n2. Fill in your details (name, email, password)\n3. Verify your email address\n4. Start browsing and registering for events!\n\nFor event registration, just visit any event page and click 'Register Now'.",
            "chips": ["Upcoming Events", "Browse Categories", "Contact Support"],
            "type": "text"
        }
    
    if any(w in message_lower for w in ["contact", "support", "email", "help me"]):
        return {
            "text": "📧 You can reach our support team at:\n\nEmail: veeawaralli@gmail.com\n\nWe're based at Sharnbasva University, Kalaburagi. We typically respond within 24 hours!",
            "chips": ["Upcoming Events", "How to Register", "Browse Categories"],
            "type": "text"
        }
    
    if any(w in message_lower for w in ["payment", "pay", "price", "cost", "razorpay"]):
        return {
            "text": "💳 EventHub supports secure payments via Razorpay. Many events are free! For paid events, you can pay securely through the platform during registration. Payments are processed instantly and you'll receive a confirmation email with your QR code ticket.",
            "chips": ["Upcoming Events", "How to Register", "Contact Support"],
            "type": "text"
        }
    
    if any(w in message_lower for w in ["category", "categories", "types"]):
        categories = list(Category.objects.all().values_list('name', flat=True))
        if categories:
            text = f"📂 We have events in these categories: {', '.join(categories)}. Browse them to find events that match your interests!"
        else:
            text = "📂 We have various event categories available. Visit the Events page to browse by category!"
        return {
            "text": text,
            "chips": ["Upcoming Events", "How to Register", "Contact Support"],
            "type": "text"
        }

    if any(w in message_lower for w in ["what is eventhub", "about eventhub", "what's eventhub", "about this"]):
        return {
            "text": "🎪 EventHub is an online event discovery and registration platform built for Sharnbasva University, Kalaburagi. It helps you discover exciting events, register seamlessly, get QR code tickets, and much more! Organizers can create and manage events with powerful analytics.",
            "chips": ["Upcoming Events", "How to Register", "Browse Categories"],
            "type": "text"
        }
    
    if any(w in message_lower for w in ["thank", "thanks", "bye", "goodbye"]):
        return {
            "text": "You're welcome! 😊 Feel free to come back anytime you need help. Have a great day! 🎉",
            "chips": ["Upcoming Events", "Browse Categories"],
            "type": "text"
        }
    
    if any(w in message_lower for w in ["login", "log in", "sign in", "signin"]):
        return {
            "text": "To log into EventHub, look for the 'Login' button at the top right of the page. If you've forgotten your password, there is a helpful reset link right there on the login form! 🔑",
            "chips": ["Upcoming Events", "How to Register", "Contact Support"],
            "type": "text"
        }
        
    return None


def format_event_list(events, prefix):
    if not events:
        return {
            "text": "I couldn't find any upcoming events matching that right now. Check back soon! 🔍",
            "chips": ["Browse Categories", "How to Register", "Contact Support"],
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
