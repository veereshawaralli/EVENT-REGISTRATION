import json
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .logic import get_chatbot_response

@method_decorator(csrf_exempt, name='dispatch')
class ChatView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            message = data.get('message', '')
            
            if not message:
                return JsonResponse({"error": "Message is required"}, status=400)
            
            # Get existing history from session or initialize new
            chat_history = request.session.get('chat_history', [])
            
            # Get response from AI with history context
            response_data = get_chatbot_response(message, chat_history)
            
            # Update history with user message
            chat_history.append({"role": "user", "content": message})
            
            # Update history with bot response (text only)
            chat_history.append({"role": "assistant", "content": response_data.get('text', '')})
            
            # Keep only the last 10 messages to prevent session bloat
            request.session['chat_history'] = chat_history[-10:]
            request.session.modified = True
            
            return JsonResponse(response_data)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
