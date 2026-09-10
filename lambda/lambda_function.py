# -*- coding: utf-8 -*-
"""Alexa custom skill that sends spoken questions to the Google Gemini API."""

import logging
import os
import re
from datetime import datetime

import requests
from ask_sdk_core.dispatch_components import (
    AbstractExceptionHandler,
    AbstractRequestHandler,
)
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_intent_name, is_request_type

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite").strip()
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)
MAX_RESPONSE_CHARS = 700
MAX_HISTORY_MESSAGES = 10

TEXT = {
    "en-US": {
        "launch": "Hello, I am your Gemini voice assistant. Ask me a question.",
        "reprompt": "What would you like to know?",
        "empty": "I did not understand your question.",
        "repeat": "Could you say that again?",
        "help": "You can ask me questions about almost any topic.",
        "more": "Would you like to ask anything else?",
        "goodbye": "Goodbye!",
        "fallback": "Sorry, I did not understand that.",
        "missing_key": "The Gemini service is not configured yet.",
        "api_error": "I could not connect to Gemini right now.",
        "timeout": "Gemini took too long to respond.",
        "empty_result": "Gemini did not return an answer.",
        "generic_error": "Something went wrong while contacting Gemini.",
        "system": "You are a helpful voice assistant powered by Gemini. "
        "Always answer in English. Be natural, concise, and direct. "
        "Do not use Markdown, emojis, or special formatting. "
        "Today is {date}. Use this date when answering time-sensitive questions.",
    },
    "pt-BR": {
        "launch": "Olá, eu sou seu assistente de voz Gemini. Faça uma pergunta.",
        "reprompt": "O que você deseja saber?",
        "empty": "Não entendi sua pergunta.",
        "repeat": "Pode repetir?",
        "help": "Você pode me fazer perguntas sobre praticamente qualquer assunto.",
        "more": "Quer perguntar mais alguma coisa?",
        "goodbye": "Até mais!",
        "fallback": "Desculpe, não consegui entender isso.",
        "missing_key": "O serviço Gemini ainda não foi configurado.",
        "api_error": "Não consegui conectar ao Gemini agora.",
        "timeout": "O Gemini demorou muito para responder.",
        "empty_result": "O Gemini não retornou uma resposta.",
        "generic_error": "Ocorreu um erro ao falar com o Gemini.",
        "system": "Você é um assistente de voz útil, alimentado pelo Gemini. "
        "Responda sempre em português do Brasil. Seja natural, conciso e direto. "
        "Não use Markdown, emojis ou formatação especial. "
        "A data de hoje é {date}. Use essa data ao responder perguntas relacionadas ao tempo.",
    },
}


def locale_for(handler_input):
    locale = getattr(handler_input.request_envelope, "request", None)
    locale = getattr(locale, "locale", "en-US")
    return locale if locale in TEXT else "en-US"


def t(handler_input, key):
    return TEXT[locale_for(handler_input)][key]


def clean_for_alexa(text):
    """Remove formatting that sounds bad or is unsupported in Alexa speech."""
    if not text or not isinstance(text, str):
        return ""
    text = re.sub(r"[`*_#<>]", "", text)
    text = text.replace("&", "and")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > MAX_RESPONSE_CHARS:
        text = text[:MAX_RESPONSE_CHARS].rsplit(" ", 1)[0] + "..."
    return text


def ask_gemini(question, history, locale, messages):
    if not GEMINI_API_KEY:
        return messages["missing_key"], history

    history = list(history or [])
    history.append({"role": "user", "parts": [{"text": question}]})
    history = history[-MAX_HISTORY_MESSAGES:]
    prompt = messages["system"].format(date=datetime.now().strftime("%Y-%m-%d"))
    payload = {
        "systemInstruction": {"parts": [{"text": prompt}]},
        "contents": history,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 512,
            "topP": 0.95,
            "topK": 40,
        },
    }

    try:
        response = requests.post(
            GEMINI_ENDPOINT,
            params={"key": GEMINI_API_KEY},
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        logger.info("Gemini request returned HTTP %s", response.status_code)
        if response.status_code != 200:
            logger.warning("Gemini API request failed with HTTP %s", response.status_code)
            return messages["api_error"], history

        data = response.json()
        candidates = data.get("candidates", [])
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        answer = clean_for_alexa("".join(part.get("text", "") for part in parts))
        if not answer:
            return messages["empty_result"], history
        history.append({"role": "model", "parts": [{"text": answer}]})
        return answer, history[-MAX_HISTORY_MESSAGES:]
    except requests.exceptions.Timeout:
        logger.warning("Gemini request timed out")
        return messages["timeout"], history
    except (requests.RequestException, ValueError, KeyError, IndexError):
        logger.exception("Unexpected Gemini API error")
        return messages["generic_error"], history


class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        return (
            handler_input.response_builder
            .speak(t(handler_input, "launch"))
            .ask(t(handler_input, "reprompt"))
            .response
        )


class ChatIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("ChatIntent")(handler_input)

    def handle(self, handler_input):
        messages = TEXT[locale_for(handler_input)]
        slots = handler_input.request_envelope.request.intent.slots or {}
        query_slot = slots.get("query")
        question = clean_for_alexa(getattr(query_slot, "value", ""))
        if not question:
            return (
                handler_input.response_builder
                .speak(messages["empty"])
                .ask(messages["repeat"])
                .response
            )

        attributes = handler_input.attributes_manager.session_attributes
        answer, history = ask_gemini(
            question,
            attributes.get("history", []),
            locale_for(handler_input),
            messages,
        )
        attributes["history"] = history
        return (
            handler_input.response_builder
            .speak(clean_for_alexa(answer))
            .ask(messages["more"])
            .response
        )


class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        return (
            handler_input.response_builder
            .speak(t(handler_input, "help"))
            .ask(t(handler_input, "reprompt"))
            .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.CancelIntent")(handler_input) or is_intent_name(
            "AMAZON.StopIntent"
        )(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.speak(t(handler_input, "goodbye")).response


class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        return (
            handler_input.response_builder
            .speak(t(handler_input, "fallback"))
            .ask(t(handler_input, "repeat"))
            .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.exception("Unhandled Alexa request error")
        return (
            handler_input.response_builder
            .speak(t(handler_input, "generic_error"))
            .ask(t(handler_input, "repeat"))
            .response
        )


sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(ChatIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_exception_handler(CatchAllExceptionHandler())
lambda_handler = sb.lambda_handler()
