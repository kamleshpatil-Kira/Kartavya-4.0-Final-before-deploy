import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List
from utils.logger import logger, log_activity
import shutil
import os
import hashlib
import re
import markdown

# UI label translations for all 18 supported languages
UI_LABELS = {
    "English": {
        "knowledge_check": "Knowledge Check", "real_world_scenario": "Real-World Scenario",
        "what_to_do": "What you should do:", "why_it_matters": "Why does it matter:",
        "submit_answer": "Submit Answer", "continue_btn": "Continue", "correct": "Correct!",
        "try_again": "Try Again!", "skip_continue": "Skip & Continue",
        "purpose_of_training": "Purpose of this Training",
        "objectives_intro": "By completing this course, learners will be able to:",
        "start_course": "START COURSE", "start_course_lower": "Start Course",
        "course_instructions": "Course Instructions",
        "lesson_x_of_y": "Lesson {0} of {1}",
        "lock_text": "Complete the content above before moving on.",
        "pct_complete": "COMPLETE", "module_x_of_y": "Module {0} of {1}",
        "reviewing_module": "Reviewing Completed Module",
        "module_summary": "Module Summary", "module_word": "Module",
        "no_content": "No content available.",
        "course_outline": "Course Outline", "course_overview": "Course Overview",
        "course_learning_obj": "Course Learning Objectives",
        "final_quiz": "Final Quiz",
        "quiz_completed_msg": "You have completed all modules. Ready to test your knowledge?",
        "quiz_pass_req": "The quiz consists of {0} questions. You need to score at least 80% to pass.",
        "start_quiz": "Start Quiz", "question": "Question",
        "question_x_of_y": "Question {0} of {1}",
        "next_btn": "Next", "submit_quiz": "Submit Quiz",
        "quiz_results": "Quiz Results",
        "you_scored": "You scored {0} out of {1} ({2}%).",
        "congratulations": "Congratulations!",
        "passed_quiz_msg": "You have successfully passed the final quiz with a score of {0}%.",
        "certificate_title": "Certificate of Completion",
        "certificate_body": "This certifies that you have completed the course requirements.",
        "thank_you": "Thank You for Learning!",
        "course_completed": "Congratulations! You have successfully completed the course.",
        "course_valuable": "We hope you found this course valuable and informative.",
        "exit_course": "Exit Course", "try_again_title": "Try Again",
        "try_again_msg": "You scored {0}%. You need at least 80% to pass. Please review the course material and try again.",
        "attempts_remaining": "Attempts remaining: {0} of {1}",
        "no_attempts": "No attempts remaining. You have used all {0} allowed attempts.",
        "contact_instructor": "Please contact your instructor for assistance.",
        "ai_disclaimer": "This course is created with AI assistance. Please review the content before use.",
        "incorrect": "Incorrect.",
        "flashcards_title": "Interactive Flashcards", "flashcards_hint": "Click on each card to flip and learn key concepts!", "click_to_flip": "Click to flip",
        "error_refresh": "An error occurred. Please refresh the page and try again.",
        "complete_prev_module": "Please complete the previous module before proceeding.",
        "no_modules_found": "No modules found. Please refresh the page.",
        "select_answer": "Please select an answer before proceeding.",
        "instructions_welcome": "Welcome to your {0}.",
        "instructions_duration": "This course will take approximately {0} minutes to complete.",
        "instructions_kc": "At the end of each module, you will see short knowledge checks. These are practice questions that you can retry as many times as needed. They do not count towards your final score.",
        "instructions_quiz": "At the end of the course, there is a final quiz. You have a maximum of 3 quiz attempts to pass with a score of 80% or higher. Your best score will be recorded.",
        "instructions_audio": "An auto-audio player is built into this course. Narration will begin automatically when each slide loads, guiding you through the content. If you need, you can pause, replay, or adjust the volume at any time.",
        "instructions_support": "If you experience technical issues, or if something does not work as expected, please reach out to your administrator or support team.",
        "instructions_goal": "The goal of this training is to provide you with the knowledge and skills needed to succeed. Let us begin.",
    },
    "Spanish":    {"knowledge_check": "Verificación de Conocimiento", "real_world_scenario": "Escenario del Mundo Real", "what_to_do": "Qué debes hacer:", "why_it_matters": "Por qué es importante:", "submit_answer": "Enviar Respuesta", "continue_btn": "Continuar", "correct": "¡Correcto!", "try_again": "¡Inténtalo de nuevo!", "skip_continue": "Omitir y Continuar", "purpose_of_training": "Propósito de esta Capacitación", "objectives_intro": "Al completar este curso, los estudiantes podrán:", "start_course": "INICIAR CURSO", "start_course_lower": "Iniciar Curso", "course_instructions": "Instrucciones del Curso", "lesson_x_of_y": "Lección {0} de {1}", "lock_text": "Complete el contenido anterior antes de continuar.", "pct_complete": "COMPLETADO", "module_x_of_y": "Módulo {0} de {1}", "reviewing_module": "Revisando Módulo Completado", "module_summary": "Resumen del Módulo", "module_word": "Módulo", "no_content": "No hay contenido disponible.", "course_outline": "Esquema del Curso", "course_overview": "Descripción General del Curso", "course_learning_obj": "Objetivos de Aprendizaje", "final_quiz": "Examen Final", "quiz_completed_msg": "Ha completado todos los módulos. ¿Está listo para evaluar sus conocimientos?", "quiz_pass_req": "El examen consta de {0} preguntas. Necesita al menos 80% para aprobar.", "start_quiz": "Iniciar Examen", "question": "Pregunta", "question_x_of_y": "Pregunta {0} de {1}", "next_btn": "Siguiente", "submit_quiz": "Enviar Examen", "quiz_results": "Resultados del Examen", "you_scored": "Obtuvo {0} de {1} ({2}%).", "congratulations": "¡Felicidades!", "passed_quiz_msg": "Ha aprobado el examen final con {0}%.", "certificate_title": "Certificado de Finalización", "certificate_body": "Certifica que ha completado los requisitos del curso.", "thank_you": "¡Gracias por Aprender!", "course_completed": "¡Felicidades! Ha completado el curso exitosamente.", "course_valuable": "Esperamos que este curso le haya resultado valioso.", "exit_course": "Salir del Curso", "try_again_title": "Intentar de Nuevo", "try_again_msg": "Obtuvo {0}%. Necesita al menos 80%. Revise el material e intente de nuevo.", "attempts_remaining": "Intentos restantes: {0} de {1}", "no_attempts": "Sin intentos restantes. Ha usado los {0} intentos permitidos.", "contact_instructor": "Comuníquese con su instructor.", "ai_disclaimer": "Curso creado con asistencia de IA. Revise el contenido antes de usarlo.", "incorrect": "Incorrecto.", "flashcards_title": "Fichas Interactivas", "flashcards_hint": "¡Haz clic en cada ficha para voltearla y aprender conceptos clave!", "click_to_flip": "Clic para voltear", "instructions_welcome": "Bienvenido a su {0}.", "instructions_duration": "Este curso tomará aproximadamente {0} minutos.", "instructions_kc": "Al final de cada módulo hay verificaciones de conocimiento. Son preguntas de práctica que no cuentan para su puntuación final.", "instructions_quiz": "Al final del curso hay un examen final. Tiene 3 intentos para aprobar con 80% o más.", "instructions_audio": "Este curso incluye narración automática que comienza con cada diapositiva.", "instructions_support": "Si experimenta problemas técnicos, contacte a su administrador.", "instructions_goal": "El objetivo es proporcionarle los conocimientos necesarios. Comencemos.", "error_refresh": "Ocurrió un error. Actualice la página e intente de nuevo.", "complete_prev_module": "Complete el módulo anterior antes de continuar.", "no_modules_found": "No se encontraron módulos. Actualice la página.", "select_answer": "Seleccione una respuesta antes de continuar."},
    "French":     {"knowledge_check": "Vérification des Connaissances", "real_world_scenario": "Scénario Réel", "what_to_do": "Que devez-vous faire :", "why_it_matters": "Pourquoi est-ce important :", "submit_answer": "Soumettre la Réponse", "continue_btn": "Continuer", "correct": "Correct !", "try_again": "Réessayez !", "skip_continue": "Passer et Continuer", "purpose_of_training": "Objectif de cette Formation", "objectives_intro": "À la fin de ce cours, les apprenants seront en mesure de :", "start_course": "DÉMARRER LE COURS", "start_course_lower": "Démarrer le Cours", "course_instructions": "Instructions du Cours", "lesson_x_of_y": "Leçon {0} sur {1}", "lock_text": "Complétez le contenu ci-dessus avant de continuer.", "pct_complete": "TERMINÉ", "module_x_of_y": "Module {0} sur {1}", "reviewing_module": "Révision du Module Terminé", "module_summary": "Résumé du Module", "module_word": "Module", "no_content": "Aucun contenu disponible.", "course_outline": "Plan du Cours", "course_overview": "Aperçu du Cours", "course_learning_obj": "Objectifs d'Apprentissage", "final_quiz": "Quiz Final", "quiz_completed_msg": "Vous avez terminé tous les modules. Prêt à tester vos connaissances ?", "quiz_pass_req": "Le quiz comprend {0} questions. Vous devez obtenir au moins 80%.", "start_quiz": "Commencer le Quiz", "question": "Question", "question_x_of_y": "Question {0} sur {1}", "next_btn": "Suivant", "submit_quiz": "Soumettre le Quiz", "quiz_results": "Résultats du Quiz", "you_scored": "Vous avez obtenu {0} sur {1} ({2}%).", "congratulations": "Félicitations !", "passed_quiz_msg": "Vous avez réussi le quiz final avec {0}%.", "certificate_title": "Certificat de Réussite", "certificate_body": "Certifie que vous avez satisfait aux exigences du cours.", "thank_you": "Merci d'avoir Appris !", "course_completed": "Félicitations ! Vous avez terminé le cours.", "course_valuable": "Nous espérons que ce cours vous a été utile.", "exit_course": "Quitter le Cours", "try_again_title": "Réessayer", "try_again_msg": "Vous avez obtenu {0}%. Il faut au moins 80%. Veuillez revoir le contenu.", "attempts_remaining": "Tentatives restantes : {0} sur {1}", "no_attempts": "Plus de tentatives. Vous avez utilisé les {0} tentatives.", "contact_instructor": "Veuillez contacter votre instructeur.", "ai_disclaimer": "Cours créé avec l'aide de l'IA. Vérifiez le contenu avant utilisation.", "incorrect": "Incorrect.", "flashcards_title": "Fiches Interactives", "flashcards_hint": "Cliquez sur chaque fiche pour la retourner et apprendre les concepts clés !", "click_to_flip": "Cliquez pour retourner", "instructions_welcome": "Bienvenue dans votre {0}.", "instructions_duration": "Ce cours prendra environ {0} minutes.", "instructions_kc": "À la fin de chaque module, des vérifications des connaissances sont proposées. Ce sont des questions pratiques.", "instructions_quiz": "À la fin du cours, il y a un quiz final. Vous avez 3 tentatives pour obtenir 80% ou plus.", "instructions_audio": "Ce cours inclut un lecteur audio automatique.", "instructions_support": "En cas de problèmes techniques, contactez votre administrateur.", "instructions_goal": "L'objectif est de vous fournir les connaissances nécessaires. Commençons.", "error_refresh": "Une erreur est survenue. Veuillez rafraîchir la page et réessayer.", "complete_prev_module": "Veuillez compléter le module précédent avant de continuer.", "no_modules_found": "Aucun module trouvé. Veuillez rafraîchir la page.", "select_answer": "Veuillez sélectionner une réponse avant de continuer."},
    "German":     {"knowledge_check": "Wissenstest", "real_world_scenario": "Praxisbeispiel", "what_to_do": "Was Sie tun sollten:", "why_it_matters": "Warum ist das wichtig:", "submit_answer": "Antwort senden", "continue_btn": "Weiter", "correct": "Richtig!", "try_again": "Nochmal versuchen!", "skip_continue": "Überspringen & Weiter", "purpose_of_training": "Zweck dieser Schulung", "objectives_intro": "Nach Abschluss dieses Kurses werden die Lernenden in der Lage sein:", "start_course": "KURS STARTEN", "start_course_lower": "Kurs Starten", "course_instructions": "Kursanweisungen", "lesson_x_of_y": "Lektion {0} von {1}", "lock_text": "Schließen Sie den obigen Inhalt ab, bevor Sie fortfahren.", "pct_complete": "ABGESCHLOSSEN", "module_x_of_y": "Modul {0} von {1}", "reviewing_module": "Abgeschlossenes Modul wird überprüft", "module_summary": "Modulzusammenfassung", "module_word": "Modul", "no_content": "Kein Inhalt verfügbar.", "course_outline": "Kursübersicht", "course_overview": "Kursüberblick", "course_learning_obj": "Lernziele des Kurses", "final_quiz": "Abschlusstest", "quiz_completed_msg": "Sie haben alle Module abgeschlossen. Bereit, Ihr Wissen zu testen?", "quiz_pass_req": "Der Test besteht aus {0} Fragen. Sie benötigen mindestens 80%.", "start_quiz": "Test Starten", "question": "Frage", "question_x_of_y": "Frage {0} von {1}", "next_btn": "Weiter", "submit_quiz": "Test Absenden", "quiz_results": "Testergebnisse", "you_scored": "Sie haben {0} von {1} erreicht ({2}%).", "congratulations": "Herzlichen Glückwunsch!", "passed_quiz_msg": "Sie haben den Abschlusstest mit {0}% bestanden.", "certificate_title": "Abschlusszertifikat", "certificate_body": "Dies bestätigt, dass Sie die Kursanforderungen erfüllt haben.", "thank_you": "Vielen Dank fürs Lernen!", "course_completed": "Herzlichen Glückwunsch! Sie haben den Kurs erfolgreich abgeschlossen.", "course_valuable": "Wir hoffen, dieser Kurs war wertvoll für Sie.", "exit_course": "Kurs Beenden", "try_again_title": "Erneut Versuchen", "try_again_msg": "Sie haben {0}% erreicht. Mindestens 80% erforderlich. Bitte wiederholen Sie das Material.", "attempts_remaining": "Verbleibende Versuche: {0} von {1}", "no_attempts": "Keine Versuche übrig. Sie haben alle {0} Versuche aufgebraucht.", "contact_instructor": "Bitte kontaktieren Sie Ihren Dozenten.", "ai_disclaimer": "Kurs mit KI-Unterstützung erstellt. Bitte überprüfen Sie den Inhalt.", "incorrect": "Falsch.", "flashcards_title": "Interaktive Lernkarten", "flashcards_hint": "Klicken Sie auf jede Karte, um sie umzudrehen und Schlüsselkonzepte zu lernen!", "click_to_flip": "Klick zum Umdrehen", "instructions_welcome": "Willkommen zu Ihrem {0}.", "instructions_duration": "Dieser Kurs dauert ca. {0} Minuten.", "instructions_kc": "Am Ende jedes Moduls gibt es Wissenstests. Diese sind Übungsfragen ohne Einfluss auf Ihre Endnote.", "instructions_quiz": "Am Ende gibt es einen Abschlusstest. Sie haben 3 Versuche für mindestens 80%.", "instructions_audio": "Dieser Kurs enthält automatische Audionarration.", "instructions_support": "Bei technischen Problemen wenden Sie sich an Ihren Administrator.", "instructions_goal": "Ziel ist es, Ihnen das nötige Wissen zu vermitteln. Beginnen wir.", "error_refresh": "Ein Fehler ist aufgetreten. Bitte laden Sie die Seite neu.", "complete_prev_module": "Bitte schließen Sie das vorherige Modul ab, bevor Sie fortfahren.", "no_modules_found": "Keine Module gefunden. Bitte laden Sie die Seite neu.", "select_answer": "Bitte wählen Sie eine Antwort aus, bevor Sie fortfahren."},
    "Portuguese": {"knowledge_check": "Verificação de Conhecimento", "real_world_scenario": "Cenário do Mundo Real", "what_to_do": "O que você deve fazer:", "why_it_matters": "Por que isso importa:", "submit_answer": "Enviar Resposta", "continue_btn": "Continuar", "correct": "Correto!", "try_again": "Tente Novamente!", "skip_continue": "Pular e Continuar", "purpose_of_training": "Objetivo deste Treinamento", "objectives_intro": "Ao concluir este curso, os alunos serão capazes de:", "start_course": "INICIAR CURSO", "start_course_lower": "Iniciar Curso", "course_instructions": "Instruções do Curso", "lesson_x_of_y": "Lição {0} de {1}", "lock_text": "Conclua o conteúdo acima antes de continuar.", "pct_complete": "CONCLUÍDO", "module_x_of_y": "Módulo {0} de {1}", "reviewing_module": "Revisando Módulo Concluído", "module_summary": "Resumo do Módulo", "module_word": "Módulo", "no_content": "Nenhum conteúdo disponível.", "course_outline": "Estrutura do Curso", "course_overview": "Visão Geral do Curso", "course_learning_obj": "Objetivos de Aprendizagem", "final_quiz": "Questionário Final", "quiz_completed_msg": "Você concluiu todos os módulos. Pronto para testar seus conhecimentos?", "quiz_pass_req": "O questionário possui {0} perguntas. Você precisa de pelo menos 80%.", "start_quiz": "Iniciar Questionário", "question": "Pergunta", "question_x_of_y": "Pergunta {0} de {1}", "next_btn": "Próximo", "submit_quiz": "Enviar Questionário", "quiz_results": "Resultados", "you_scored": "Você acertou {0} de {1} ({2}%).", "congratulations": "Parabéns!", "passed_quiz_msg": "Você passou com {0}%.", "certificate_title": "Certificado de Conclusão", "certificate_body": "Certifica que você concluiu os requisitos do curso.", "thank_you": "Obrigado por Aprender!", "course_completed": "Parabéns! Você concluiu o curso.", "course_valuable": "Esperamos que este curso tenha sido valioso.", "exit_course": "Sair do Curso", "try_again_title": "Tentar Novamente", "try_again_msg": "Você obteve {0}%. Necessário 80%. Revise o material.", "attempts_remaining": "Tentativas restantes: {0} de {1}", "no_attempts": "Sem tentativas. Você usou todas as {0} tentativas.", "contact_instructor": "Entre em contato com seu instrutor.", "ai_disclaimer": "Curso criado com assistência de IA. Revise o conteúdo.", "incorrect": "Incorreto.", "flashcards_title": "Flashcards Interativos", "flashcards_hint": "Clique em cada cartão para virar e aprender conceitos chave!", "click_to_flip": "Clique para virar", "instructions_welcome": "Bem-vindo ao seu {0}.", "instructions_duration": "Este curso levará aproximadamente {0} minutos.", "instructions_kc": "Ao final de cada módulo, há verificações de conhecimento.", "instructions_quiz": "Ao final há um questionário. Você tem 3 tentativas para 80%.", "instructions_audio": "Este curso inclui narração automática.", "instructions_support": "Para problemas técnicos, contate seu administrador.", "instructions_goal": "O objetivo é fornecer o conhecimento necessário. Vamos começar.", "error_refresh": "Ocorreu um erro. Atualize a página e tente novamente.", "complete_prev_module": "Conclua o módulo anterior antes de prosseguir.", "no_modules_found": "Nenhum módulo encontrado. Atualize a página.", "select_answer": "Selecione uma resposta antes de prosseguir."},
    "Italian":    {"knowledge_check": "Verifica delle Conoscenze", "real_world_scenario": "Scenario Reale", "what_to_do": "Cosa dovresti fare:", "why_it_matters": "Perché è importante:", "submit_answer": "Invia Risposta", "continue_btn": "Continua", "correct": "Corretto!", "try_again": "Riprova!", "skip_continue": "Salta e Continua", "purpose_of_training": "Scopo di questa Formazione", "objectives_intro": "Al termine di questo corso, i partecipanti saranno in grado di:", "start_course": "AVVIA CORSO", "start_course_lower": "Avvia Corso", "course_instructions": "Istruzioni del Corso", "lesson_x_of_y": "Lezione {0} di {1}", "lock_text": "Completa il contenuto sopra prima di procedere.", "pct_complete": "COMPLETATO", "module_x_of_y": "Modulo {0} di {1}", "reviewing_module": "Revisione Modulo Completato", "module_summary": "Riepilogo del Modulo", "module_word": "Modulo", "no_content": "Nessun contenuto disponibile.", "course_outline": "Schema del Corso", "course_overview": "Panoramica del Corso", "course_learning_obj": "Obiettivi di Apprendimento", "final_quiz": "Quiz Finale", "quiz_completed_msg": "Hai completato tutti i moduli. Pronto a testare le tue conoscenze?", "quiz_pass_req": "Il quiz comprende {0} domande. Servono almeno l'80%.", "start_quiz": "Inizia Quiz", "question": "Domanda", "question_x_of_y": "Domanda {0} di {1}", "next_btn": "Avanti", "submit_quiz": "Invia Quiz", "quiz_results": "Risultati del Quiz", "you_scored": "Hai ottenuto {0} su {1} ({2}%).", "congratulations": "Congratulazioni!", "passed_quiz_msg": "Hai superato il quiz finale con {0}%.", "certificate_title": "Certificato di Completamento", "certificate_body": "Certifica che hai completato i requisiti del corso.", "thank_you": "Grazie per aver Imparato!", "course_completed": "Congratulazioni! Hai completato il corso.", "course_valuable": "Speriamo che questo corso ti sia stato utile.", "exit_course": "Esci dal Corso", "try_again_title": "Riprova", "try_again_msg": "Hai ottenuto {0}%. Servono almeno 80%. Rivedi il materiale.", "attempts_remaining": "Tentativi rimasti: {0} di {1}", "no_attempts": "Nessun tentativo rimasto. Hai usato tutti i {0} tentativi.", "contact_instructor": "Contatta il tuo istruttore.", "ai_disclaimer": "Corso creato con assistenza IA. Verifica il contenuto.", "incorrect": "Sbagliato.", "flashcards_title": "Schede Interattive", "flashcards_hint": "Clicca su ogni scheda per girarla e apprendere i concetti chiave!", "click_to_flip": "Clicca per girare", "instructions_welcome": "Benvenuto al tuo {0}.", "instructions_duration": "Questo corso richiederà circa {0} minuti.", "instructions_kc": "Alla fine di ogni modulo ci sono verifiche delle conoscenze.", "instructions_quiz": "Alla fine c'è un quiz finale. Hai 3 tentativi per l'80%.", "instructions_audio": "Questo corso include narrazione automatica.", "instructions_support": "Per problemi tecnici, contatta il tuo amministratore.", "instructions_goal": "L'obiettivo è fornirti le conoscenze necessarie. Iniziamo.", "error_refresh": "Si è verificato un errore. Aggiorna la pagina e riprova.", "complete_prev_module": "Completa il modulo precedente prima di procedere.", "no_modules_found": "Nessun modulo trovato. Aggiorna la pagina.", "select_answer": "Seleziona una risposta prima di procedere."},
    "Dutch":      {"knowledge_check": "Kennistoets", "real_world_scenario": "Praktijkscenario", "what_to_do": "Wat u moet doen:", "why_it_matters": "Waarom is het belangrijk:", "submit_answer": "Antwoord Verzenden", "continue_btn": "Doorgaan", "correct": "Juist!", "try_again": "Probeer Opnieuw!", "skip_continue": "Overslaan & Doorgaan", "purpose_of_training": "Doel van deze Training", "objectives_intro": "Na afronding van deze cursus kunnen deelnemers:", "start_course": "CURSUS STARTEN", "start_course_lower": "Cursus Starten", "course_instructions": "Cursinstructies", "lesson_x_of_y": "Les {0} van {1}", "lock_text": "Voltooi de bovenstaande inhoud voordat u verdergaat.", "pct_complete": "VOLTOOID", "module_x_of_y": "Module {0} van {1}", "reviewing_module": "Voltooide Module Bekijken", "module_summary": "Module Samenvatting", "module_word": "Module", "no_content": "Geen inhoud beschikbaar.", "course_outline": "Cursusoverzicht", "course_overview": "Cursusoverzicht", "course_learning_obj": "Leerdoelen", "final_quiz": "Eindtoets", "quiz_completed_msg": "U heeft alle modules voltooid. Klaar om uw kennis te testen?", "quiz_pass_req": "De toets bestaat uit {0} vragen. U heeft minimaal 80% nodig.", "start_quiz": "Toets Starten", "question": "Vraag", "question_x_of_y": "Vraag {0} van {1}", "next_btn": "Volgende", "submit_quiz": "Toets Indienen", "quiz_results": "Toetsresultaten", "you_scored": "U scoorde {0} van {1} ({2}%).", "congratulations": "Gefeliciteerd!", "passed_quiz_msg": "U heeft de eindtoets gehaald met {0}%.", "certificate_title": "Certificaat van Voltooiing", "certificate_body": "Dit bevestigt dat u aan de cursusvereisten heeft voldaan.", "thank_you": "Bedankt voor het Leren!", "course_completed": "Gefeliciteerd! U heeft de cursus voltooid.", "course_valuable": "We hopen dat deze cursus waardevol was.", "exit_course": "Cursus Verlaten", "try_again_title": "Opnieuw Proberen", "try_again_msg": "U scoorde {0}%. Minimaal 80% vereist. Bekijk het materiaal opnieuw.", "attempts_remaining": "Resterende pogingen: {0} van {1}", "no_attempts": "Geen pogingen meer. U heeft alle {0} pogingen gebruikt.", "contact_instructor": "Neem contact op met uw docent.", "ai_disclaimer": "Cursus gemaakt met AI-hulp. Controleer de inhoud.", "incorrect": "Onjuist.", "flashcards_title": "Interactieve Flashcards", "flashcards_hint": "Klik op elke kaart om deze om te draaien en kernconcepten te leren!", "click_to_flip": "Klik om te draaien", "instructions_welcome": "Welkom bij uw {0}.", "instructions_duration": "Deze cursus duurt ongeveer {0} minuten.", "instructions_kc": "Aan het einde van elke module zijn er kennistoetsen.", "instructions_quiz": "Aan het einde is er een eindtoets. U heeft 3 pogingen voor 80%.", "instructions_audio": "Deze cursus bevat automatische gesproken tekst.", "instructions_support": "Bij technische problemen, neem contact op met uw beheerder.", "instructions_goal": "Het doel is u de nodige kennis te bieden. Laten we beginnen.", "error_refresh": "Er is een fout opgetreden. Vernieuw de pagina en probeer opnieuw.", "complete_prev_module": "Voltooi de vorige module voordat u verdergaat.", "no_modules_found": "Geen modules gevonden. Vernieuw de pagina.", "select_answer": "Selecteer een antwoord voordat u verdergaat."},
    "Russian":    {"knowledge_check": "Проверка Знаний", "real_world_scenario": "Реальный Сценарий", "what_to_do": "Что следует сделать:", "why_it_matters": "Почему это важно:", "submit_answer": "Отправить Ответ", "continue_btn": "Продолжить", "correct": "Правильно!", "try_again": "Попробуйте ещё раз!", "skip_continue": "Пропустить и Продолжить", "purpose_of_training": "Цель этого Обучения", "objectives_intro": "По завершении этого курса учащиеся смогут:", "start_course": "НАЧАТЬ КУРС", "start_course_lower": "Начать Курс", "course_instructions": "Инструкции к Курсу", "lesson_x_of_y": "Урок {0} из {1}", "lock_text": "Завершите содержание выше, прежде чем продолжить.", "pct_complete": "ЗАВЕРШЕНО", "module_x_of_y": "Модуль {0} из {1}", "reviewing_module": "Просмотр завершённого модуля", "module_summary": "Итоги Модуля", "module_word": "Модуль", "no_content": "Содержание недоступно.", "course_outline": "Структура Курса", "course_overview": "Обзор Курса", "course_learning_obj": "Учебные Цели", "final_quiz": "Итоговый Тест", "quiz_completed_msg": "Вы завершили все модули. Готовы проверить свои знания?", "quiz_pass_req": "Тест содержит {0} вопросов. Необходимо набрать не менее 80%.", "start_quiz": "Начать Тест", "question": "Вопрос", "question_x_of_y": "Вопрос {0} из {1}", "next_btn": "Далее", "submit_quiz": "Отправить Тест", "quiz_results": "Результаты Теста", "you_scored": "Вы набрали {0} из {1} ({2}%).", "congratulations": "Поздравляем!", "passed_quiz_msg": "Вы прошли итоговый тест с результатом {0}%.", "certificate_title": "Сертификат о Прохождении", "certificate_body": "Подтверждает выполнение требований курса.", "thank_you": "Спасибо за Обучение!", "course_completed": "Поздравляем! Вы успешно завершили курс.", "course_valuable": "Надеемся, курс был полезным.", "exit_course": "Выйти из Курса", "try_again_title": "Попробовать Снова", "try_again_msg": "Вы набрали {0}%. Необходимо 80%. Пересмотрите материал.", "attempts_remaining": "Осталось попыток: {0} из {1}", "no_attempts": "Попыток не осталось. Вы использовали все {0} попыток.", "contact_instructor": "Свяжитесь с вашим инструктором.", "ai_disclaimer": "Курс создан с помощью ИИ. Проверьте содержание.", "incorrect": "Неверно.", "flashcards_title": "Интерактивные Карточки", "flashcards_hint": "Нажмите на каждую карточку, чтобы перевернуть и изучить ключевые концепции!", "click_to_flip": "Нажмите, чтобы перевернуть", "instructions_welcome": "Добро пожаловать на ваш {0}.", "instructions_duration": "Этот курс займёт примерно {0} минут.", "instructions_kc": "В конце каждого модуля есть проверка знаний.", "instructions_quiz": "В конце курса — итоговый тест. 3 попытки для 80%.", "instructions_audio": "Курс включает автоматическое озвучивание.", "instructions_support": "При технических проблемах обратитесь к администратору.", "instructions_goal": "Цель — дать вам необходимые знания. Начнём.", "error_refresh": "Произошла ошибка. Обновите страницу и попробуйте снова.", "complete_prev_module": "Пожалуйста, завершите предыдущий модуль.", "no_modules_found": "Модули не найдены. Обновите страницу.", "select_answer": "Выберите ответ перед продолжением."},
    "Chinese":    {"knowledge_check": "知识检查", "real_world_scenario": "现实场景", "what_to_do": "你应该怎么做：", "why_it_matters": "为什么重要：", "submit_answer": "提交答案", "continue_btn": "继续", "correct": "正确！", "try_again": "再试一次！", "skip_continue": "跳过并继续", "purpose_of_training": "本培训的目的", "objectives_intro": "完成本课程后，学员将能够：", "start_course": "开始课程", "start_course_lower": "开始课程", "course_instructions": "课程说明", "lesson_x_of_y": "第{0}课 / 共{1}课", "lock_text": "请先完成以上内容再继续。", "pct_complete": "已完成", "module_x_of_y": "模块{0} / {1}", "reviewing_module": "正在复习已完成的模块", "module_summary": "模块总结", "module_word": "模块", "no_content": "暂无内容。", "course_outline": "课程大纲", "course_overview": "课程概述", "course_learning_obj": "课程学习目标", "final_quiz": "期末测验", "quiz_completed_msg": "您已完成所有模块。准备好测试您的知识了吗？", "quiz_pass_req": "测验共{0}题。需要至少80%才能通过。", "start_quiz": "开始测验", "question": "问题", "question_x_of_y": "第{0}题 / 共{1}题", "next_btn": "下一题", "submit_quiz": "提交测验", "quiz_results": "测验结果", "you_scored": "您答对了{1}题中的{0}题（{2}%）。", "congratulations": "恭喜！", "passed_quiz_msg": "您以{0}%的成绩通过了期末测验。", "certificate_title": "结业证书", "certificate_body": "证明您已完成课程要求。", "thank_you": "感谢您的学习！", "course_completed": "恭喜！您已成功完成课程。", "course_valuable": "希望本课程对您有价值。", "exit_course": "退出课程", "try_again_title": "再试一次", "try_again_msg": "您获得了{0}%。需要至少80%。请复习材料后重试。", "attempts_remaining": "剩余尝试：{0} / {1}", "no_attempts": "没有剩余尝试。您已用完所有{0}次尝试。", "contact_instructor": "请联系您的讲师。", "ai_disclaimer": "本课程由AI辅助创建。请在使用前检查内容。", "incorrect": "不正确。", "flashcards_title": "互动闪卡", "flashcards_hint": "点击每张卡片翻转并学习关键概念！", "click_to_flip": "点击翻转", "instructions_welcome": "欢迎来到您的{0}。", "instructions_duration": "本课程大约需要{0}分钟。", "instructions_kc": "每个模块末尾有知识测验。", "instructions_quiz": "课程末尾有期末测验。您有3次机会获得80%。", "instructions_audio": "本课程包含自动音频旁白。", "instructions_support": "如遇技术问题，请联系管理员。", "instructions_goal": "目标是为您提供所需知识。让我们开始吧。", "error_refresh": "发生错误。请刷新页面后重试。", "complete_prev_module": "请先完成上一个模块再继续。", "no_modules_found": "未找到模块。请刷新页面。", "select_answer": "请在继续之前选择一个答案。"},
    "Japanese":   {"knowledge_check": "知識チェック", "real_world_scenario": "実世界シナリオ", "what_to_do": "あなたがすべきこと：", "why_it_matters": "なぜ重要か：", "submit_answer": "回答を送信", "continue_btn": "続ける", "correct": "正解！", "try_again": "もう一度！", "skip_continue": "スキップして続ける", "purpose_of_training": "このトレーニングの目的", "objectives_intro": "このコースを修了すると、受講者は以下ができるようになります：", "start_course": "コースを開始", "start_course_lower": "コースを開始", "course_instructions": "コースの手順", "lesson_x_of_y": "レッスン{0} / {1}", "lock_text": "続行する前に上記の内容を完了してください。", "pct_complete": "完了", "module_x_of_y": "モジュール{0} / {1}", "reviewing_module": "完了したモジュールを復習中", "module_summary": "モジュールの要約", "module_word": "モジュール", "no_content": "コンテンツがありません。", "course_outline": "コース概要", "course_overview": "コース概要", "course_learning_obj": "学習目標", "final_quiz": "最終テスト", "quiz_completed_msg": "すべてのモジュールが完了しました。知識をテストしますか？", "quiz_pass_req": "テストは{0}問です。合格には80%以上が必要です。", "start_quiz": "テスト開始", "question": "問題", "question_x_of_y": "問題{0} / {1}", "next_btn": "次へ", "submit_quiz": "テスト提出", "quiz_results": "テスト結果", "you_scored": "{1}問中{0}問正解（{2}%）。", "congratulations": "おめでとうございます！", "passed_quiz_msg": "{0}%で最終テストに合格しました。", "certificate_title": "修了証", "certificate_body": "コース要件を満たしたことを証明します。", "thank_you": "学習ありがとうございます！", "course_completed": "おめでとうございます！コースを修了しました。", "course_valuable": "このコースが有益であったことを願います。", "exit_course": "コースを終了", "try_again_title": "もう一度", "try_again_msg": "{0}%でした。80%以上が必要です。教材を復習してください。", "attempts_remaining": "残り回数：{0} / {1}", "no_attempts": "残り回数なし。{0}回すべて使用しました。", "contact_instructor": "講師にお問い合わせください。", "ai_disclaimer": "AI支援で作成されたコースです。使用前に内容を確認してください。", "incorrect": "不正解。", "flashcards_title": "インタラクティブフラッシュカード", "flashcards_hint": "各カードをクリックして裏返し、重要な概念を学びましょう！", "click_to_flip": "クリックして裏返す", "instructions_welcome": "{0}へようこそ。", "instructions_duration": "このコースは約{0}分です。", "instructions_kc": "各モジュールの最後に知識チェックがあります。", "instructions_quiz": "最後に最終テストがあります。3回の受験機会があります。", "instructions_audio": "このコースには自動音声ナレーションが含まれています。", "instructions_support": "技術的な問題がある場合は管理者に連絡してください。", "instructions_goal": "必要な知識を提供することが目的です。始めましょう。", "error_refresh": "エラーが発生しました。ページを更新してもう一度お試しください。", "complete_prev_module": "前のモジュールを完了してから進んでください。", "no_modules_found": "モジュールが見つかりません。ページを更新してください。", "select_answer": "続行する前に回答を選択してください。"},
    "Korean":     {"knowledge_check": "지식 확인", "real_world_scenario": "실제 시나리오", "what_to_do": "무엇을 해야 하는가:", "why_it_matters": "왜 중요한가:", "submit_answer": "답변 제출", "continue_btn": "계속", "correct": "정답!", "try_again": "다시 시도!", "skip_continue": "건너뛰고 계속", "purpose_of_training": "이 교육의 목적", "objectives_intro": "이 과정을 완료하면 학습자는 다음을 할 수 있습니다:", "start_course": "과정 시작", "start_course_lower": "과정 시작", "course_instructions": "과정 안내", "lesson_x_of_y": "강의 {0} / {1}", "lock_text": "계속하기 전에 위의 내용을 완료하세요.", "pct_complete": "완료", "module_x_of_y": "모듈 {0} / {1}", "reviewing_module": "완료된 모듈 복습 중", "module_summary": "모듈 요약", "module_word": "모듈", "no_content": "콘텐츠가 없습니다.", "course_outline": "과정 개요", "course_overview": "과정 개요", "course_learning_obj": "학습 목표", "final_quiz": "최종 시험", "quiz_completed_msg": "모든 모듈을 완료했습니다. 시험을 볼 준비가 되셨나요?", "quiz_pass_req": "시험은 {0}문항입니다. 80% 이상이 필요합니다.", "start_quiz": "시험 시작", "question": "문제", "question_x_of_y": "문제 {0} / {1}", "next_btn": "다음", "submit_quiz": "시험 제출", "quiz_results": "시험 결과", "you_scored": "{1}문제 중 {0}문제 정답 ({2}%).", "congratulations": "축하합니다!", "passed_quiz_msg": "{0}%로 최종 시험에 합격했습니다.", "certificate_title": "수료증", "certificate_body": "과정 요건을 완료했음을 증명합니다.", "thank_you": "학습해 주셔서 감사합니다!", "course_completed": "축하합니다! 과정을 성공적으로 완료했습니다.", "course_valuable": "이 과정이 유익했기를 바랍니다.", "exit_course": "과정 종료", "try_again_title": "다시 시도", "try_again_msg": "{0}%를 받았습니다. 80% 이상 필요합니다. 자료를 복습하세요.", "attempts_remaining": "남은 시도: {0} / {1}", "no_attempts": "시도 횟수가 없습니다. {0}회 모두 사용했습니다.", "contact_instructor": "강사에게 문의하세요.", "ai_disclaimer": "AI 지원으로 만들어진 과정입니다. 내용을 확인하세요.", "incorrect": "오답.", "flashcards_title": "인터랙티브 플래시카드", "flashcards_hint": "각 카드를 클릭하여 뒤집고 핵심 개념을 학습하세요!", "click_to_flip": "클릭하여 뒤집기", "instructions_welcome": "{0}에 오신 것을 환영합니다.", "instructions_duration": "이 과정은 약 {0}분 소요됩니다.", "instructions_kc": "각 모듈 끝에 지식 확인이 있습니다.", "instructions_quiz": "과정 끝에 최종 시험이 있습니다. 3번의 기회가 있습니다.", "instructions_audio": "이 과정에는 자동 오디오 나레이션이 포함됩니다.", "instructions_support": "기술 문제 시 관리자에게 문의하세요.", "instructions_goal": "필요한 지식을 제공하는 것이 목표입니다. 시작합시다.", "error_refresh": "오류가 발생했습니다. 페이지를 새로고침하고 다시 시도하세요.", "complete_prev_module": "이전 모듈을 완료한 후 진행하세요.", "no_modules_found": "모듈을 찾을 수 없습니다. 페이지를 새로고침하세요.", "select_answer": "계속하기 전에 답변을 선택하세요."},
    "Arabic":     {"knowledge_check": "اختبار المعرفة", "real_world_scenario": "سيناريو واقعي", "what_to_do": "ما يجب عليك فعله:", "why_it_matters": "لماذا هذا مهم:", "submit_answer": "إرسال الإجابة", "continue_btn": "متابعة", "correct": "!صحيح", "try_again": "!حاول مرة أخرى", "skip_continue": "تخطي ومتابعة", "purpose_of_training": "الغرض من هذا التدريب", "objectives_intro": "عند إتمام هذه الدورة، سيتمكن المتعلمون من:", "start_course": "ابدأ الدورة", "start_course_lower": "ابدأ الدورة", "course_instructions": "تعليمات الدورة", "lesson_x_of_y": "الدرس {0} من {1}", "lock_text": "أكمل المحتوى أعلاه قبل المتابعة.", "pct_complete": "مكتمل", "module_x_of_y": "الوحدة {0} من {1}", "reviewing_module": "مراجعة الوحدة المكتملة", "module_summary": "ملخص الوحدة", "module_word": "الوحدة", "no_content": "لا يوجد محتوى.", "course_outline": "مخطط الدورة", "course_overview": "نظرة عامة", "course_learning_obj": "أهداف التعلم", "final_quiz": "الاختبار النهائي", "quiz_completed_msg": "لقد أكملت جميع الوحدات. هل أنت مستعد لاختبار معرفتك؟", "quiz_pass_req": "يتكون الاختبار من {0} أسئلة. تحتاج 80% على الأقل.", "start_quiz": "ابدأ الاختبار", "question": "سؤال", "question_x_of_y": "سؤال {0} من {1}", "next_btn": "التالي", "submit_quiz": "إرسال الاختبار", "quiz_results": "نتائج الاختبار", "you_scored": "حصلت على {0} من {1} ({2}%).", "congratulations": "!تهانينا", "passed_quiz_msg": "لقد اجتزت الاختبار بنسبة {0}%.", "certificate_title": "شهادة إتمام", "certificate_body": "تشهد بإتمامك متطلبات الدورة.", "thank_you": "!شكراً للتعلم", "course_completed": "تهانينا! لقد أتممت الدورة بنجاح.", "course_valuable": "نأمل أن تكون الدورة مفيدة.", "exit_course": "الخروج من الدورة", "try_again_title": "حاول مرة أخرى", "try_again_msg": "حصلت على {0}%. تحتاج 80%. راجع المادة.", "attempts_remaining": "المحاولات المتبقية: {0} من {1}", "no_attempts": "لا محاولات متبقية. استخدمت جميع المحاولات {0}.", "contact_instructor": "تواصل مع المدرب.", "ai_disclaimer": "دورة مُنشأة بمساعدة الذكاء الاصطناعي. راجع المحتوى.", "incorrect": ".خطأ", "flashcards_title": "بطاقات تفاعلية", "flashcards_hint": "!انقر على كل بطاقة لقلبها وتعلم المفاهيم الأساسية", "click_to_flip": "انقر للقلب", "instructions_welcome": "مرحباً بك في {0}.", "instructions_duration": "ستستغرق هذه الدورة حوالي {0} دقيقة.", "instructions_kc": "في نهاية كل وحدة اختبار معرفة.", "instructions_quiz": "في النهاية اختبار نهائي. لديك 3 محاولات.", "instructions_audio": "تتضمن الدورة سرداً صوتياً تلقائياً.", "instructions_support": "للمشاكل التقنية، تواصل مع المسؤول.", "instructions_goal": "الهدف توفير المعرفة اللازمة. لنبدأ.", "error_refresh": "حدث خطأ. يرجى تحديث الصفحة والمحاولة مرة أخرى.", "complete_prev_module": "يرجى إكمال الوحدة السابقة قبل المتابعة.", "no_modules_found": "لم يتم العثور على وحدات. يرجى تحديث الصفحة.", "select_answer": "يرجى اختيار إجابة قبل المتابعة."},
    "Hindi":      {"knowledge_check": "ज्ञान जांच", "real_world_scenario": "वास्तविक परिदृश्य", "what_to_do": "आपको क्या करना चाहिए:", "why_it_matters": "यह क्यों महत्वपूर्ण है:", "submit_answer": "उत्तर जमा करें", "continue_btn": "जारी रखें", "correct": "सही!", "try_again": "पुनः प्रयास करें!", "skip_continue": "छोड़ें और जारी रखें", "purpose_of_training": "इस प्रशिक्षण का उद्देश्य", "objectives_intro": "इस पाठ्यक्रम को पूरा करने पर, शिक्षार्थी सक्षम होंगे:", "start_course": "पाठ्यक्रम शुरू करें", "start_course_lower": "पाठ्यक्रम शुरू करें", "course_instructions": "पाठ्यक्रम निर्देश", "lesson_x_of_y": "पाठ {0} / {1}", "lock_text": "आगे बढ़ने से पहले ऊपर की सामग्री पूरी करें।", "pct_complete": "पूर्ण", "module_x_of_y": "मॉड्यूल {0} / {1}", "reviewing_module": "पूर्ण मॉड्यूल की समीक्षा", "module_summary": "मॉड्यूल सारांश", "module_word": "मॉड्यूल", "no_content": "कोई सामग्री उपलब्ध नहीं है।", "course_outline": "पाठ्यक्रम रूपरेखा", "course_overview": "पाठ्यक्रम अवलोकन", "course_learning_obj": "पाठ्यक्रम शिक्षण उद्देश्य", "final_quiz": "अंतिम प्रश्नोत्तरी", "quiz_completed_msg": "आपने सभी मॉड्यूल पूरे कर लिए हैं। क्या आप तैयार हैं?", "quiz_pass_req": "प्रश्नोत्तरी में {0} प्रश्न हैं। उत्तीर्ण होने के लिए 80% आवश्यक है।", "start_quiz": "प्रश्नोत्तरी शुरू करें", "question": "प्रश्न", "question_x_of_y": "प्रश्न {0} / {1}", "next_btn": "अगला", "submit_quiz": "प्रश्नोत्तरी जमा करें", "quiz_results": "प्रश्नोत्तरी परिणाम", "you_scored": "आपने {1} में से {0} अंक प्राप्त किए ({2}%)।", "congratulations": "बधाई हो!", "passed_quiz_msg": "आपने {0}% अंकों के साथ उत्तीर्ण किया है।", "certificate_title": "पूर्णता प्रमाणपत्र", "certificate_body": "यह प्रमाणित करता है कि आपने पाठ्यक्रम पूरा कर लिया है।", "thank_you": "सीखने के लिए धन्यवाद!", "course_completed": "बधाई हो! आपने पाठ्यक्रम सफलतापूर्वक पूरा किया है।", "course_valuable": "हमें आशा है कि यह पाठ्यक्रम उपयोगी रहा।", "exit_course": "पाठ्यक्रम से बाहर निकलें", "try_again_title": "पुनः प्रयास करें", "try_again_msg": "आपने {0}% प्राप्त किए। 80% आवश्यक है। कृपया सामग्री की समीक्षा करें।", "attempts_remaining": "शेष प्रयास: {0} / {1}", "no_attempts": "कोई प्रयास शेष नहीं। आपने सभी {0} प्रयास उपयोग किए।", "contact_instructor": "कृपया अपने प्रशिक्षक से संपर्क करें।", "ai_disclaimer": "यह पाठ्यक्रम AI सहायता से बनाया गया है। कृपया सामग्री की समीक्षा करें।", "incorrect": "गलत।", "flashcards_title": "इंटरैक्टिव फ्लैशकार्ड", "flashcards_hint": "प्रमुख अवधारणाओं को सीखने के लिए प्रत्येक कार्ड पर क्लिक करें!", "click_to_flip": "पलटने के लिए क्लिक करें", "instructions_welcome": "आपके {0} में स्वागत है।", "instructions_duration": "यह पाठ्यक्रम लगभग {0} मिनट का है।", "instructions_kc": "प्रत्येक मॉड्यूल के अंत में ज्ञान जांच होगी। ये अभ्यास प्रश्न हैं।", "instructions_quiz": "पाठ्यक्रम के अंत में अंतिम प्रश्नोत्तरी है। 80% के लिए 3 प्रयास हैं।", "instructions_audio": "इस पाठ्यक्रम में स्वचालित ऑडियो है।", "instructions_support": "तकनीकी समस्याओं के लिए अपने व्यवस्थापक से संपर्क करें।", "instructions_goal": "इस प्रशिक्षण का लक्ष्य आपको आवश्यक ज्ञान प्रदान करना है। शुरू करते हैं।", "error_refresh": "एक त्रुटि हुई। कृपया पृष्ठ को रीफ्रेश करें और पुनः प्रयास करें।", "complete_prev_module": "कृपया आगे बढ़ने से पहले पिछला मॉड्यूल पूरा करें।", "no_modules_found": "कोई मॉड्यूल नहीं मिला। कृपया पृष्ठ को रीफ्रेश करें।", "select_answer": "कृपया आगे बढ़ने से पहले एक उत्तर चुनें।"},
    "Turkish":    {"knowledge_check": "Bilgi Kontrolü", "real_world_scenario": "Gerçek Dünya Senaryosu", "what_to_do": "Ne yapmalısınız:", "why_it_matters": "Neden önemli:", "submit_answer": "Cevabı Gönder", "continue_btn": "Devam", "correct": "Doğru!", "try_again": "Tekrar Deneyin!", "skip_continue": "Atla ve Devam Et", "purpose_of_training": "Bu Eğitimin Amacı", "objectives_intro": "Bu kursu tamamladıktan sonra öğrenciler şunları yapabileceklerdir:", "start_course": "KURSA BAŞLA", "start_course_lower": "Kursa Başla", "course_instructions": "Kurs Talimatları", "lesson_x_of_y": "Ders {0} / {1}", "lock_text": "Devam etmeden önce yukarıdaki içeriği tamamlayın.", "pct_complete": "TAMAMLANDI", "module_x_of_y": "Modül {0} / {1}", "reviewing_module": "Tamamlanan Modül İnceleniyor", "module_summary": "Modül Özeti", "module_word": "Modül", "no_content": "İçerik mevcut değil.", "course_outline": "Kurs Taslağı", "course_overview": "Kurs Genel Bakışı", "course_learning_obj": "Öğrenme Hedefleri", "final_quiz": "Final Sınavı", "quiz_completed_msg": "Tüm modülleri tamamladınız. Bilginizi test etmeye hazır mısınız?", "quiz_pass_req": "Sınav {0} sorudan oluşmaktadır. Geçmek için en az %80 gereklidir.", "start_quiz": "Sınava Başla", "question": "Soru", "question_x_of_y": "Soru {0} / {1}", "next_btn": "İleri", "submit_quiz": "Sınavı Gönder", "quiz_results": "Sınav Sonuçları", "you_scored": "{1} sorudan {0} doğru ({2}%).", "congratulations": "Tebrikler!", "passed_quiz_msg": "Final sınavını %{0} ile geçtiniz.", "certificate_title": "Tamamlama Sertifikası", "certificate_body": "Kurs gereksinimlerini tamamladığınızı onaylar.", "thank_you": "Öğrendiğiniz için Teşekkürler!", "course_completed": "Tebrikler! Kursu başarıyla tamamladınız.", "course_valuable": "Bu kursun faydalı olduğunu umuyoruz.", "exit_course": "Kurstan Çık", "try_again_title": "Tekrar Dene", "try_again_msg": "%{0} aldınız. En az %80 gerekli. Materyali gözden geçirin.", "attempts_remaining": "Kalan denemeler: {0} / {1}", "no_attempts": "Deneme kalmadı. Tüm {0} denemeyi kullandınız.", "contact_instructor": "Eğitmeninizle iletişime geçin.", "ai_disclaimer": "AI destekli kurs. İçeriği kullanmadan önce inceleyin.", "incorrect": "Yanlış.", "flashcards_title": "Etkileşimli Bilgi Kartları", "flashcards_hint": "Her karta tıklayarak çevirin ve temel kavramları öğrenin!", "click_to_flip": "Çevirmek için tıkla", "instructions_welcome": "{0}'a hoş geldiniz.", "instructions_duration": "Bu kurs yaklaşık {0} dakika sürecektir.", "instructions_kc": "Her modülün sonunda bilgi kontrolü vardır.", "instructions_quiz": "Sonunda final sınavı var. 3 deneme hakkınız var.", "instructions_audio": "Bu kurs otomatik sesli anlatım içerir.", "instructions_support": "Teknik sorunlar için yöneticinize başvurun.", "instructions_goal": "Amaç gerekli bilgiyi sağlamaktır. Başlayalım.", "error_refresh": "Bir hata oluştu. Lütfen sayfayı yenileyin ve tekrar deneyin.", "complete_prev_module": "Devam etmeden önce önceki modülü tamamlayın.", "no_modules_found": "Modül bulunamadı. Sayfayı yenileyin.", "select_answer": "Devam etmeden önce bir cevap seçin."},
    "Polish":     {"knowledge_check": "Sprawdzian Wiedzy", "real_world_scenario": "Scenariusz z Życia", "what_to_do": "Co powinieneś zrobić:", "why_it_matters": "Dlaczego to ważne:", "submit_answer": "Wyślij Odpowiedź", "continue_btn": "Dalej", "correct": "Poprawnie!", "try_again": "Spróbuj ponownie!", "skip_continue": "Pomiń i Dalej", "purpose_of_training": "Cel tego Szkolenia", "objectives_intro": "Po ukończeniu tego kursu uczestnicy będą w stanie:", "start_course": "ROZPOCZNIJ KURS", "start_course_lower": "Rozpocznij Kurs", "course_instructions": "Instrukcje Kursu", "lesson_x_of_y": "Lekcja {0} z {1}", "lock_text": "Ukończ powyższą treść przed kontynuowaniem.", "pct_complete": "UKOŃCZONO", "module_x_of_y": "Moduł {0} z {1}", "reviewing_module": "Przegląd Ukończonego Modułu", "module_summary": "Podsumowanie Modułu", "module_word": "Moduł", "no_content": "Brak dostępnej treści.", "course_outline": "Plan Kursu", "course_overview": "Przegląd Kursu", "course_learning_obj": "Cele Kształcenia", "final_quiz": "Egzamin Końcowy", "quiz_completed_msg": "Ukończyłeś wszystkie moduły. Gotowy na test?", "quiz_pass_req": "Egzamin ma {0} pytań. Wymagane minimum 80%.", "start_quiz": "Rozpocznij Egzamin", "question": "Pytanie", "question_x_of_y": "Pytanie {0} z {1}", "next_btn": "Dalej", "submit_quiz": "Wyślij Egzamin", "quiz_results": "Wyniki Egzaminu", "you_scored": "Wynik: {0} z {1} ({2}%).", "congratulations": "Gratulacje!", "passed_quiz_msg": "Zdałeś egzamin z wynikiem {0}%.", "certificate_title": "Certyfikat Ukończenia", "certificate_body": "Potwierdza ukończenie wymagań kursu.", "thank_you": "Dziękujemy za Naukę!", "course_completed": "Gratulacje! Kurs ukończony.", "course_valuable": "Mamy nadzieję, że kurs był wartościowy.", "exit_course": "Zakończ Kurs", "try_again_title": "Spróbuj Ponownie", "try_again_msg": "Wynik: {0}%. Wymagane 80%. Przejrzyj materiał.", "attempts_remaining": "Pozostałe próby: {0} z {1}", "no_attempts": "Brak prób. Wykorzystałeś wszystkie {0} prób.", "contact_instructor": "Skontaktuj się z instruktorem.", "ai_disclaimer": "Kurs stworzony z pomocą AI. Sprawdź treść.", "incorrect": "Niepoprawnie.", "flashcards_title": "Interaktywne Fiszki", "flashcards_hint": "Kliknij każdą kartę, aby ją obrócić i poznać kluczowe pojęcia!", "click_to_flip": "Kliknij, aby obrócić", "instructions_welcome": "Witamy w {0}.", "instructions_duration": "Ten kurs trwa około {0} minut.", "instructions_kc": "Na końcu każdego modułu jest sprawdzian wiedzy.", "instructions_quiz": "Na końcu jest egzamin. Masz 3 próby na 80%.", "instructions_audio": "Kurs zawiera automatyczną narrację.", "instructions_support": "W razie problemów technicznych skontaktuj się z administratorem.", "instructions_goal": "Celem jest przekazanie niezbędnej wiedzy. Zacznijmy.", "error_refresh": "Wystąpił błąd. Odśwież stronę i spróbuj ponownie.", "complete_prev_module": "Ukończ poprzedni moduł przed kontynuowaniem.", "no_modules_found": "Nie znaleziono modułów. Odśwież stronę.", "select_answer": "Wybierz odpowiedź przed kontynuowaniem."},
    "Vietnamese": {"knowledge_check": "Kiểm Tra Kiến Thức", "real_world_scenario": "Tình Huống Thực Tế", "what_to_do": "Bạn nên làm gì:", "why_it_matters": "Tại sao điều này quan trọng:", "submit_answer": "Gửi Câu Trả Lời", "continue_btn": "Tiếp tục", "correct": "Chính xác!", "try_again": "Thử lại!", "skip_continue": "Bỏ qua và Tiếp tục", "purpose_of_training": "Mục đích của Khóa Đào tạo", "objectives_intro": "Sau khi hoàn thành khóa học, học viên sẽ có thể:", "start_course": "BẮT ĐẦU KHÓA HỌC", "start_course_lower": "Bắt đầu Khóa học", "course_instructions": "Hướng dẫn Khóa học", "lesson_x_of_y": "Bài {0} / {1}", "lock_text": "Hoàn thành nội dung trên trước khi tiếp tục.", "pct_complete": "HOÀN THÀNH", "module_x_of_y": "Mô-đun {0} / {1}", "reviewing_module": "Đang xem lại Mô-đun đã hoàn thành", "module_summary": "Tóm tắt Mô-đun", "module_word": "Mô-đun", "no_content": "Không có nội dung.", "course_outline": "Đề cương Khóa học", "course_overview": "Tổng quan Khóa học", "course_learning_obj": "Mục tiêu Học tập", "final_quiz": "Bài kiểm tra Cuối cùng", "quiz_completed_msg": "Bạn đã hoàn thành tất cả mô-đun. Sẵn sàng kiểm tra kiến thức?", "quiz_pass_req": "Bài kiểm tra gồm {0} câu hỏi. Cần đạt ít nhất 80%.", "start_quiz": "Bắt đầu Kiểm tra", "question": "Câu hỏi", "question_x_of_y": "Câu hỏi {0} / {1}", "next_btn": "Tiếp", "submit_quiz": "Nộp bài", "quiz_results": "Kết quả", "you_scored": "Bạn đạt {0}/{1} ({2}%).", "congratulations": "Chúc mừng!", "passed_quiz_msg": "Bạn đã đạt {0}% bài kiểm tra cuối.", "certificate_title": "Chứng nhận Hoàn thành", "certificate_body": "Chứng nhận bạn đã hoàn thành yêu cầu khóa học.", "thank_you": "Cảm ơn bạn đã Học!", "course_completed": "Chúc mừng! Bạn đã hoàn thành khóa học.", "course_valuable": "Hy vọng khóa học hữu ích cho bạn.", "exit_course": "Thoát Khóa học", "try_again_title": "Thử lại", "try_again_msg": "Bạn đạt {0}%. Cần 80%. Hãy xem lại tài liệu.", "attempts_remaining": "Lần thử còn lại: {0} / {1}", "no_attempts": "Hết lần thử. Đã dùng hết {0} lần.", "contact_instructor": "Liên hệ giảng viên.", "ai_disclaimer": "Khóa học tạo bởi AI. Vui lòng kiểm tra nội dung.", "incorrect": "Sai.", "flashcards_title": "Thẻ Ghi Nhớ Tương Tác", "flashcards_hint": "Nhấp vào mỗi thẻ để lật và học các khái niệm chính!", "click_to_flip": "Nhấp để lật", "instructions_welcome": "Chào mừng đến {0}.", "instructions_duration": "Khóa học kéo dài khoảng {0} phút.", "instructions_kc": "Cuối mỗi mô-đun có kiểm tra kiến thức.", "instructions_quiz": "Cuối khóa có bài kiểm tra. Bạn có 3 lần thử.", "instructions_audio": "Khóa học có âm thanh tự động.", "instructions_support": "Nếu gặp sự cố, liên hệ quản trị viên.", "instructions_goal": "Mục tiêu là cung cấp kiến thức cần thiết. Hãy bắt đầu.", "error_refresh": "Đã xảy ra lỗi. Vui lòng tải lại trang và thử lại.", "complete_prev_module": "Vui lòng hoàn thành mô-đun trước đó trước khi tiếp tục.", "no_modules_found": "Không tìm thấy mô-đun. Vui lòng tải lại trang.", "select_answer": "Vui lòng chọn câu trả lời trước khi tiếp tục."},
    "Thai":       {"knowledge_check": "ตรวจสอบความรู้", "real_world_scenario": "สถานการณ์จริง", "what_to_do": "สิ่งที่คุณควรทำ:", "why_it_matters": "ทำไมจึงสำคัญ:", "submit_answer": "ส่งคำตอบ", "continue_btn": "ดำเนินการต่อ", "correct": "ถูกต้อง!", "try_again": "ลองอีกครั้ง!", "skip_continue": "ข้ามและดำเนินการต่อ", "purpose_of_training": "วัตถุประสงค์ของการฝึกอบรม", "objectives_intro": "เมื่อจบหลักสูตร ผู้เรียนจะสามารถ:", "start_course": "เริ่มหลักสูตร", "start_course_lower": "เริ่มหลักสูตร", "course_instructions": "คำแนะนำหลักสูตร", "lesson_x_of_y": "บทที่ {0} จาก {1}", "lock_text": "กรุณาทำเนื้อหาด้านบนให้เสร็จก่อนดำเนินการต่อ", "pct_complete": "เสร็จสิ้น", "module_x_of_y": "โมดูล {0} จาก {1}", "reviewing_module": "กำลังทบทวนโมดูลที่เสร็จแล้ว", "module_summary": "สรุปโมดูล", "module_word": "โมดูล", "no_content": "ไม่มีเนื้อหา", "course_outline": "โครงร่างหลักสูตร", "course_overview": "ภาพรวมหลักสูตร", "course_learning_obj": "วัตถุประสงค์การเรียนรู้", "final_quiz": "แบบทดสอบสุดท้าย", "quiz_completed_msg": "คุณทำโมดูลทั้งหมดเสร็จแล้ว พร้อมทดสอบความรู้หรือยัง?", "quiz_pass_req": "แบบทดสอบมี {0} คำถาม ต้องได้อย่างน้อย 80%", "start_quiz": "เริ่มทดสอบ", "question": "คำถาม", "question_x_of_y": "คำถามที่ {0} จาก {1}", "next_btn": "ถัดไป", "submit_quiz": "ส่งแบบทดสอบ", "quiz_results": "ผลการทดสอบ", "you_scored": "คุณได้ {0} จาก {1} ({2}%)", "congratulations": "ยินดีด้วย!", "passed_quiz_msg": "คุณผ่านแบบทดสอบด้วย {0}%", "certificate_title": "ใบรับรองการผ่านหลักสูตร", "certificate_body": "รับรองว่าคุณผ่านข้อกำหนดหลักสูตร", "thank_you": "ขอบคุณที่เรียนรู้!", "course_completed": "ยินดีด้วย! คุณเรียนจบหลักสูตรแล้ว", "course_valuable": "หวังว่าหลักสูตรจะเป็นประโยชน์", "exit_course": "ออกจากหลักสูตร", "try_again_title": "ลองอีกครั้ง", "try_again_msg": "คุณได้ {0}% ต้องได้ 80% กรุณาทบทวน", "attempts_remaining": "โอกาสที่เหลือ: {0} จาก {1}", "no_attempts": "หมดโอกาส ใช้ไปทั้ง {0} ครั้ง", "contact_instructor": "กรุณาติดต่อผู้สอน", "ai_disclaimer": "หลักสูตรสร้างด้วย AI กรุณาตรวจสอบเนื้อหา", "incorrect": "ไม่ถูกต้อง", "flashcards_title": "บัตรคำแบบโต้ตอบ", "flashcards_hint": "คลิกที่แต่ละการ์ดเพื่อพลิกและเรียนรู้แนวคิดสำคัญ!", "click_to_flip": "คลิกเพื่อพลิก", "instructions_welcome": "ยินดีต้อนรับสู่ {0}", "instructions_duration": "หลักสูตรใช้เวลาประมาณ {0} นาที", "instructions_kc": "ท้ายแต่ละโมดูลมีการตรวจสอบความรู้", "instructions_quiz": "ท้ายหลักสูตรมีแบบทดสอบ มี 3 โอกาส", "instructions_audio": "หลักสูตรมีเสียงบรรยายอัตโนมัติ", "instructions_support": "หากมีปัญหาทางเทคนิค กรุณาติดต่อผู้ดูแล", "instructions_goal": "เป้าหมายคือให้ความรู้ที่จำเป็น เริ่มกันเลย", "error_refresh": "เกิดข้อผิดพลาด กรุณารีเฟรชหน้าเว็บแล้วลองอีกครั้ง", "complete_prev_module": "กรุณาทำโมดูลก่อนหน้าให้เสร็จก่อนดำเนินการต่อ", "no_modules_found": "ไม่พบโมดูล กรุณารีเฟรชหน้าเว็บ", "select_answer": "กรุณาเลือกคำตอบก่อนดำเนินการต่อ"},
    "Indonesian": {"knowledge_check": "Pemeriksaan Pengetahuan", "real_world_scenario": "Skenario Dunia Nyata", "what_to_do": "Apa yang harus Anda lakukan:", "why_it_matters": "Mengapa ini penting:", "submit_answer": "Kirim Jawaban", "continue_btn": "Lanjutkan", "correct": "Benar!", "try_again": "Coba Lagi!", "skip_continue": "Lewati dan Lanjutkan", "purpose_of_training": "Tujuan Pelatihan Ini", "objectives_intro": "Setelah menyelesaikan kursus ini, peserta akan mampu:", "start_course": "MULAI KURSUS", "start_course_lower": "Mulai Kursus", "course_instructions": "Petunjuk Kursus", "lesson_x_of_y": "Pelajaran {0} dari {1}", "lock_text": "Selesaikan konten di atas sebelum melanjutkan.", "pct_complete": "SELESAI", "module_x_of_y": "Modul {0} dari {1}", "reviewing_module": "Meninjau Modul yang Selesai", "module_summary": "Ringkasan Modul", "module_word": "Modul", "no_content": "Tidak ada konten.", "course_outline": "Garis Besar Kursus", "course_overview": "Ikhtisar Kursus", "course_learning_obj": "Tujuan Pembelajaran", "final_quiz": "Kuis Akhir", "quiz_completed_msg": "Anda telah menyelesaikan semua modul. Siap menguji pengetahuan?", "quiz_pass_req": "Kuis terdiri dari {0} pertanyaan. Diperlukan minimal 80%.", "start_quiz": "Mulai Kuis", "question": "Pertanyaan", "question_x_of_y": "Pertanyaan {0} dari {1}", "next_btn": "Berikutnya", "submit_quiz": "Kirim Kuis", "quiz_results": "Hasil Kuis", "you_scored": "Skor Anda {0} dari {1} ({2}%).", "congratulations": "Selamat!", "passed_quiz_msg": "Anda lulus kuis akhir dengan {0}%.", "certificate_title": "Sertifikat Penyelesaian", "certificate_body": "Menyatakan Anda telah memenuhi persyaratan kursus.", "thank_you": "Terima Kasih telah Belajar!", "course_completed": "Selamat! Anda berhasil menyelesaikan kursus.", "course_valuable": "Semoga kursus ini bermanfaat.", "exit_course": "Keluar Kursus", "try_again_title": "Coba Lagi", "try_again_msg": "Skor Anda {0}%. Minimal 80%. Tinjau materi.", "attempts_remaining": "Percobaan tersisa: {0} dari {1}", "no_attempts": "Tidak ada percobaan tersisa. Semua {0} percobaan telah digunakan.", "contact_instructor": "Hubungi instruktur Anda.", "ai_disclaimer": "Kursus dibuat dengan bantuan AI. Periksa konten.", "incorrect": "Salah.", "flashcards_title": "Kartu Flash Interaktif", "flashcards_hint": "Klik setiap kartu untuk membalik dan pelajari konsep kunci!", "click_to_flip": "Klik untuk membalik", "instructions_welcome": "Selamat datang di {0}.", "instructions_duration": "Kursus ini memakan waktu sekitar {0} menit.", "instructions_kc": "Di akhir setiap modul ada pemeriksaan pengetahuan.", "instructions_quiz": "Di akhir ada kuis final. Anda memiliki 3 kesempatan.", "instructions_audio": "Kursus ini menyertakan narasi audio otomatis.", "instructions_support": "Jika ada masalah teknis, hubungi administrator.", "instructions_goal": "Tujuannya memberi Anda pengetahuan yang diperlukan. Mari mulai.", "error_refresh": "Terjadi kesalahan. Muat ulang halaman dan coba lagi.", "complete_prev_module": "Selesaikan modul sebelumnya sebelum melanjutkan.", "no_modules_found": "Modul tidak ditemukan. Muat ulang halaman.", "select_answer": "Pilih jawaban sebelum melanjutkan."},
}

class xAPIGenerator:
    """Generate xAPI (TinCan) compliant LMS package"""

    def _get_labels(self, language: str = "English") -> dict:
        """Get UI labels for the given language, falling back to English for missing keys."""
        english = UI_LABELS["English"]
        lang_labels = UI_LABELS.get(language, english)
        # Merge: language-specific labels override English defaults
        merged = dict(english)
        merged.update(lang_labels)
        return merged
    
    def generate_package(self, course_data: Dict[str, Any], output_path: str) -> str:
        """Generate complete xAPI package"""
        log_activity("xAPI package generation started", {"output_path": output_path})
        
        try:
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            assets_dir = output_dir / "assets"
            assets_dir.mkdir(exist_ok=True)
            
            # Generate all files
            self._generate_index_html(course_data, output_dir)
            self._generate_tincan_xml(course_data, output_dir)
            self._generate_course_json(course_data, output_dir)
            self._copy_assets(course_data, assets_dir)
            
            log_activity("xAPI package generation completed", {"output_path": output_path})
            return str(output_dir)
        except Exception as e:
            logger.error(f"Failed to generate xAPI package: {e}", exc_info=True)
            raise
    
    def _generate_index_html(self, course_data: Dict, output_dir: Path):
        """Generate index.html file"""
        html_content = self._build_html_content(course_data)
        html_path = output_dir / "index.html"
        html_path.write_text(html_content, encoding='utf-8')
        log_activity("index.html generated", {"path": str(html_path)})
    
    def _generate_tincan_xml(self, course_data: Dict, output_dir: Path):
        """Generate tincan.xml file matching RISE 365 format"""
        course_root = course_data.get('course', {})
        if not isinstance(course_root, dict):
            course_root = {}

        course_id = self._safe_text(course_root.get('id', 'course-1'), 'course-1')
        course_title = self._safe_text(course_root.get('title', 'Course'), 'Course')
        course_description = self._safe_text(course_root.get('description', ''), '')
        
        # Generate a unique course ID (similar to RISE format)
        course_hash = hashlib.sha256(f"{course_id}{course_title}".encode()).hexdigest()[:32]
        base_course_id = f"http://{course_hash}_rise"
        
        # Create root element with proper namespaces
        root = ET.Element('tincan')
        root.set('xmlns', 'http://projecttincan.com/tincan.xsd')
        root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        root.set('xmlns:xsd', 'http://www.w3.org/2001/XMLSchema')
        
        activities = ET.SubElement(root, 'activities')
        
        # Main course activity
        course_activity = ET.SubElement(activities, 'activity', 
                                       id=base_course_id,
                                       type='http://adlnet.gov/expapi/activities/course')
        
        # Course name (using lang attribute, not langstring)
        name_elem = ET.SubElement(course_activity, 'name', lang='en-US')
        name_elem.text = course_title
        
        # Course description (using lang attribute with HTML content)
        desc_elem = ET.SubElement(course_activity, 'description', lang='en-US')
        # Format description - ElementTree handles escaping automatically
        # If description contains HTML, use it directly; otherwise wrap in paragraph
        if '<' in course_description and '>' in course_description:
            # Description already contains HTML
            desc_elem.text = course_description
        else:
            # Wrap plain text in paragraph tag (ElementTree will escape special chars)
            import html
            desc_elem.text = f'<p>{html.escape(course_description)}</p>'
        
        # Launch configuration - use index.html for our package structure
        # LMS will handle the actual launch path
        launch_elem = ET.SubElement(course_activity, 'launch', lang='en-US')
        launch_elem.text = 'index.html'
        
        # Add module activities
        modules = course_data.get('modules', [])
        if not isinstance(modules, list):
            modules = []
        for idx, module in enumerate(modules, 1):
            if not isinstance(module, dict):
                continue
            module_title = self._safe_text(module.get('moduleTitle', f'Module {idx}'), f'Module {idx}')
            
            # Generate module ID (similar to RISE format)
            module_hash = hashlib.sha256(f"{base_course_id}/{module_title}".encode()).hexdigest()[:32]
            module_activity_id = f"{base_course_id}/{module_hash}"
            
            module_activity = ET.SubElement(activities, 'activity',
                                          id=module_activity_id,
                                          type='http://adlnet.gov/expapi/activities/module')
            
            module_name = ET.SubElement(module_activity, 'name', lang='en-US')
            module_name.text = f"{module_title}/blocks"
            
            module_desc = ET.SubElement(module_activity, 'description', lang='en-US')
            module_desc.text = ''  # Empty description for modules
        
        # Add quiz activity if quiz exists
        quiz = course_data.get('quiz', {})
        if not isinstance(quiz, dict):
            quiz = {}
        if quiz and quiz.get('questions'):
            quiz_hash = hashlib.sha256(f"{base_course_id}/Quiz".encode()).hexdigest()[:32]
            quiz_activity_id = f"{base_course_id}/{quiz_hash}"
            
            quiz_activity = ET.SubElement(activities, 'activity',
                                        id=quiz_activity_id,
                                        type='http://adlnet.gov/expapi/activities/module')
            
            quiz_name = ET.SubElement(quiz_activity, 'name', lang='en-US')
            quiz_name.text = 'Quiz/quiz'
            
            quiz_desc = ET.SubElement(quiz_activity, 'description', lang='en-US')
            quiz_description_text = f'<h2>{course_title}</h2>This quiz is designed to assess your understanding of the key concepts covered in this course. It will include multiple-choice questions covering the main topics you have learned.'
            attempts_raw = quiz.get('attempts', 3)
            try:
                attempts = int(attempts_raw)
            except (TypeError, ValueError):
                attempts = 3
            if attempts > 1:
                quiz_description_text += f'<strong>Note:</strong> You have a total of {attempts} attempts to score 80% or higher. Your best score will be recorded.'
            quiz_desc.text = quiz_description_text
            
            # Add quiz question activities
            questions = quiz.get('questions', [])
            if not isinstance(questions, list):
                questions = []
            for q_idx, question in enumerate(questions):
                if not isinstance(question, dict):
                    continue
                question_text = self._safe_text(question.get('question', ''), f'Question {q_idx + 1}')
                question_hash = hashlib.sha256(f"{quiz_activity_id}/{question_text}".encode()).hexdigest()[:32]
                question_id = f"{quiz_activity_id}/{question_hash}"
                
                question_activity = ET.SubElement(activities, 'activity',
                                                id=question_id,
                                                type='http://adlnet.gov/expapi/activities/cmi.interaction')
                
                q_name = ET.SubElement(question_activity, 'name', lang='en-US')
                q_name.text = question_text
                
                q_desc = ET.SubElement(question_activity, 'description', lang='en-US')
                q_desc.text = ''
                
                # Interaction type
                interaction_type = ET.SubElement(question_activity, 'interactionType')
                interaction_type.text = 'choice'
                
                # Correct response
                correct_response_patterns = ET.SubElement(question_activity, 'correctResponsePatterns')
                correct_answer = question.get('correctAnswer', '')
                options = self._normalize_question_options(question)
                correct_choice_id = self._resolve_correct_choice_id(question_text, options, correct_answer, q_idx)
                correct_pattern = ET.SubElement(correct_response_patterns, 'correctResponsePattern')
                correct_pattern.text = correct_choice_id
                
                # Choices
                choices = ET.SubElement(question_activity, 'choices')
                
                # Add all choices
                for option_key, option_value in options.items():
                    choice_id = self._generate_choice_id(question_text, option_value, q_idx, option_key)
                    component = ET.SubElement(choices, 'component')
                    comp_id = ET.SubElement(component, 'id')
                    comp_id.text = choice_id
                    comp_desc = ET.SubElement(component, 'description', lang='en-US')
                    comp_desc.text = option_value
        
        # Write XML with proper formatting
        self._indent_xml(root)
        tree = ET.ElementTree(root)
        xml_path = output_dir / "tincan.xml"
        
        # Write with XML declaration and proper encoding
        tree.write(xml_path, encoding='utf-8', xml_declaration=True)
        log_activity("tincan.xml generated", {"path": str(xml_path)})

    def _safe_text(self, value: Any, default: str = "") -> str:
        """Convert arbitrary values to safe text for XML/HTML writing."""
        if value is None:
            return default
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float, bool)):
            return str(value)
        if isinstance(value, dict):
            for key in ("text", "label", "value", "title", "description", "question"):
                candidate = value.get(key)
                if isinstance(candidate, (str, int, float, bool)):
                    candidate_text = str(candidate).strip()
                    if candidate_text:
                        return candidate_text
            return default
        if isinstance(value, list):
            text_parts = []
            for item in value:
                item_text = self._safe_text(item, "").strip()
                if item_text:
                    text_parts.append(item_text)
            if text_parts:
                return " ".join(text_parts)
            return default
        return str(value)

    def _normalize_question_options(self, question: Dict[str, Any]) -> Dict[str, str]:
        """Normalize quiz options and drop non-option payload keys."""
        raw_options = question.get('options', {})
        normalized: Dict[str, str] = {}

        if isinstance(raw_options, dict):
            preferred: Dict[str, str] = {}
            for key, value in raw_options.items():
                key_text = self._safe_text(key, "").strip()
                value_text = self._safe_text(value, "").strip()
                if not key_text or not value_text:
                    continue
                if re.fullmatch(r"[A-Z]", key_text) or re.fullmatch(r"\d+", key_text) or key_text.lower().startswith("option"):
                    preferred[key_text] = value_text
            if preferred:
                return preferred

            for key, value in raw_options.items():
                key_text = self._safe_text(key, "").strip()
                value_text = self._safe_text(value, "").strip()
                if key_text and value_text:
                    normalized[key_text] = value_text
            return normalized

        if isinstance(raw_options, list):
            for idx, value in enumerate(raw_options):
                value_text = self._safe_text(value, "").strip()
                if not value_text:
                    continue
                if idx < 26:
                    key_text = chr(65 + idx)
                else:
                    key_text = f"Option{idx + 1}"
                normalized[key_text] = value_text
        return normalized

    def _resolve_correct_choice_id(
        self,
        question_text: str,
        options: Dict[str, str],
        correct_answer: Any,
        question_index: int
    ) -> str:
        """Resolve the correct choice id from either option key or option text."""
        correct_text = self._safe_text(correct_answer, "").strip()
        if not options:
            return self._generate_choice_id(question_text, correct_text, question_index)

        if correct_text in options:
            return self._generate_choice_id(question_text, options[correct_text], question_index, correct_text)

        for option_key, option_value in options.items():
            if option_value == correct_text:
                return self._generate_choice_id(question_text, option_value, question_index, option_key)

        lower_correct = correct_text.lower()
        if lower_correct:
            for option_key, option_value in options.items():
                if option_key.lower() == lower_correct or option_value.lower() == lower_correct:
                    return self._generate_choice_id(question_text, option_value, question_index, option_key)

        first_key = next(iter(options))
        return self._generate_choice_id(question_text, options[first_key], question_index, first_key)
    
    def _generate_choice_id(self, question_text: Any, choice_text: Any, question_index: int, choice_key: Any = None) -> str:
        """Generate a unique choice ID similar to RISE format"""
        question_text_value = self._safe_text(question_text, "")
        choice_text_value = self._safe_text(choice_text, "")
        choice_key_value = self._safe_text(choice_key, "").strip() if choice_key is not None else ""

        # Create a deterministic hash-based ID
        if choice_key_value:
            hash_input = f"{question_text_value}{choice_key_value}{choice_text_value}{question_index}"
        else:
            hash_input = f"{question_text_value}{choice_text_value}{question_index}"
        
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()[:32]
        return f"choice_{hash_value}"
    
    def _indent_xml(self, elem, level=0):
        """Add indentation to XML for better readability"""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    
    def _generate_course_json(self, course_data: Dict, output_dir: Path):
        """Generate course.json manifest"""
        json_path = output_dir / "course.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(course_data, f, indent=2, ensure_ascii=False)
        log_activity("course.json generated", {"path": str(json_path)})
    
    def _copy_assets(self, course_data: Dict, assets_dir: Path):
        """Copy assets (images, audio) to assets folder"""
        # Track copied files to avoid duplicates
        copied_files = set()
        
        # Copy images and audio from modules
        for module in course_data.get('modules', []):
            module_num = module.get('moduleNumber', 'unknown')
            
            # Copy image with error handling
            if module.get('imagePath'):
                src = Path(module['imagePath'])
                if src.exists() and src.name not in copied_files:
                    try:
                        dst = assets_dir / src.name
                        shutil.copy2(src, dst)
                        copied_files.add(src.name)
                        logger.info(f"Copied image for module {module_num}: {src} -> {dst}")
                    except Exception as e:
                        logger.error(f"Failed to copy image for module {module_num}: {e}")
                elif not src.exists():
                    logger.warning(f"Image file not found for module {module_num}: {src}")
            
            # Copy module-level audio with error handling - support both single file and multiple chunks
            audio_paths = module.get('audioPaths')
            if audio_paths and len(audio_paths) > 0:
                # Copy all audio chunks
                for audio_path in audio_paths:
                    if audio_path:
                        src = Path(audio_path)
                        if src.exists() and src.name not in copied_files:
                            try:
                                dst = assets_dir / src.name
                                shutil.copy2(src, dst)
                                copied_files.add(src.name)
                                logger.info(f"Copied audio chunk for module {module_num}: {src} -> {dst}")
                            except Exception as e:
                                logger.error(f"Failed to copy audio chunk for module {module_num}: {e}")
                        elif not src.exists():
                            logger.warning(f"Audio chunk file not found for module {module_num}: {src}")
            elif module.get('audioPath'):
                # Single audio file (backward compatible)
                src = Path(module['audioPath'])
                if src.exists() and src.name not in copied_files:
                    try:
                        dst = assets_dir / src.name
                        shutil.copy2(src, dst)
                        copied_files.add(src.name)
                        logger.info(f"Copied audio for module {module_num}: {src} -> {dst}")
                    except Exception as e:
                        logger.error(f"Failed to copy audio for module {module_num}: {e}")
                elif not src.exists():
                    logger.warning(f"Audio file not found for module {module_num}: {src}")
            
            # Copy section-level audio files (current implementation uses sections)
            content_data = module.get('content', {})
            if isinstance(content_data, dict):
                sections = content_data.get('sections', [])
                for section_idx, section in enumerate(sections, 1):
                    section_num = section_idx
                    # Check for section audio paths (can be single or multiple chunks)
                    section_audio_paths = section.get('audioPaths', [])
                    if section_audio_paths and len(section_audio_paths) > 0:
                        # Multiple audio chunks for this section
                        for audio_path in section_audio_paths:
                            if audio_path:
                                src = Path(audio_path)
                                if src.exists() and src.name not in copied_files:
                                    try:
                                        dst = assets_dir / src.name
                                        shutil.copy2(src, dst)
                                        copied_files.add(src.name)
                                        logger.info(f"Copied section audio chunk for module {module_num}, section {section_num}: {src} -> {dst}")
                                    except Exception as e:
                                        logger.error(f"Failed to copy section audio chunk for module {module_num}, section {section_num}: {e}")
                                elif not src.exists():
                                    logger.warning(f"Section audio chunk file not found for module {module_num}, section {section_num}: {src}")
                    elif section.get('audioPath'):
                        # Single audio file for this section
                        src = Path(section['audioPath'])
                        if src.exists() and src.name not in copied_files:
                            try:
                                dst = assets_dir / src.name
                                shutil.copy2(src, dst)
                                copied_files.add(src.name)
                                logger.info(f"Copied section audio for module {module_num}, section {section_num}: {src} -> {dst}")
                            except Exception as e:
                                logger.error(f"Failed to copy section audio for module {module_num}, section {section_num}: {e}")
                        elif not src.exists():
                            logger.warning(f"Section audio file not found for module {module_num}, section {section_num}: {src}")
        
        # Copy instructions audio if it exists
        instructions = course_data.get('instructions', {})
        if instructions and instructions.get('audioPath'):
            src = Path(instructions['audioPath'])
            if src.exists():
                try:
                    dst = assets_dir / "instructions-audio.mp3"
                    shutil.copy2(src, dst)
                    logger.info(f"Copied instructions audio: {src} -> {dst}")
                except Exception as e:
                    logger.error(f"Failed to copy instructions audio: {e}")
            else:
                logger.warning(f"Instructions audio file not found: {src}")
        
        # Generate CSS and JS files
        self._generate_assets_files(assets_dir)
    
    def _generate_assets_files(self, assets_dir: Path):
        """Generate CSS and JavaScript files"""
        css_content = self._get_css_content()
        js_content = self._get_js_content()
        xapi_wrapper_content = self._get_xapi_wrapper_content()
        
        (assets_dir / "styles.css").write_text(css_content, encoding='utf-8')
        (assets_dir / "script.js").write_text(js_content, encoding='utf-8')
        (assets_dir / "xapiwrapper.min.js").write_text(xapi_wrapper_content, encoding='utf-8')
    
    def _build_html_content(self, course_data: Dict) -> str:
        """Build complete HTML content"""
        course = course_data['course']
        modules = course_data.get('modules', [])
        quiz = course_data.get('quiz', {})
        total_modules = len(modules)  # Get total modules count
        
        # Get translated UI labels based on course language
        course_language = course.get('courseLanguage', 'English')
        self._labels = self._get_labels(course_language)
        self._show_ai_footer = course.get('showAiFooter', True)
        
        html_parts = [self._get_html_header(course.get('courseTitle', course.get('title', 'Course')))]
        
        # Home/intro screen (shown initially)
        html_parts.append(self._get_home_screen(course, modules))
        
        # Course Instructions section (shown after START COURSE is clicked)
        # Determine if course has any audio (instructions or module-level)
        instructions_audio_path = course_data.get('instructions', {}).get('audioPath')
        has_instructions_audio = bool(instructions_audio_path and str(instructions_audio_path).strip().lower() not in ('none', 'null', ''))
        has_course_audio = has_instructions_audio
        if not has_course_audio:
            for m in modules:
                if m.get('audioPath') or m.get('audioPaths'):
                    has_course_audio = True
                    break
                m_content = m.get('content', {})
                if isinstance(m_content, dict):
                    for sec in m_content.get('sections', []):
                        if sec.get('audioPath') or sec.get('audioPaths'):
                            has_course_audio = True
                            break
                    if has_course_audio:
                        break
        html_parts.append(self._get_course_instructions_section(course, modules, has_instructions_audio, has_course_audio))
        
        # Sidebar (hidden initially, shown when course starts)
        html_parts.append(self._get_sidebar(modules, course))
        
        # Main content area (hidden initially)
        html_parts.append('<main class="main-content" id="mainContent" style="display: none;">')  # Open main content area
        
        # Add a hamburger button for desktop to toggle the sidebar
        html_parts.append('''
        <button class="desktop-sidebar-toggle" onclick="toggleDesktopSidebar()" title="Toggle Sidebar">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
        </button>
        ''')
        
        # Course outline section removed - now part of home screen
        
        for module in modules:
            # Pass total_modules to each module section
            html_parts.append(self._get_module_section(module, total_modules))
        
        html_parts.append(self._get_quiz_section(quiz))
        html_parts.append(self._get_completion_section())
        html_parts.append('</main>')  # Close main content
        html_parts.append('</div>')  # Close course-layout
        html_parts.append(self._get_html_footer(course_data))
        
        return '\n'.join(html_parts)
    
    def _get_html_header(self, course_title: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self._escape_html(course_title)}</title>
    <link rel="stylesheet" href="assets/styles.css">
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
    <!-- xAPI Wrapper -->
    <script src="assets/xapiwrapper.min.js"></script>
    <script>
    // CRITICAL: Normalize actor from SCORM Cloud URL params
    // SCORM Cloud sends non-standard field names that the LRS rejects:
    //   accountServiceHomePage -> homePage
    //   accountName -> name
    // Also arrays need to be converted to single values
    (function() {{
        if (typeof ADL !== 'undefined' && ADL.XAPIWrapper && ADL.XAPIWrapper.lrs && ADL.XAPIWrapper.lrs.actor) {{
            try {{
                var actor = JSON.parse(ADL.XAPIWrapper.lrs.actor);
                // Convert arrays to single values
                if (Array.isArray(actor.name)) actor.name = actor.name[0] || "";
                if (Array.isArray(actor.account)) actor.account = actor.account[0] || {{}};
                if (Array.isArray(actor.mbox)) actor.mbox = actor.mbox[0] || "";
                if (Array.isArray(actor.mbox_sha1sum)) actor.mbox_sha1sum = actor.mbox_sha1sum[0] || "";
                if (Array.isArray(actor.openid)) actor.openid = actor.openid[0] || "";
                // Rename SCORM Cloud non-standard account fields to xAPI standard
                if (actor.account && typeof actor.account === 'object') {{
                    if (actor.account.accountServiceHomePage && !actor.account.homePage) {{
                        actor.account.homePage = actor.account.accountServiceHomePage;
                        delete actor.account.accountServiceHomePage;
                    }}
                    if (actor.account.accountName && !actor.account.name) {{
                        actor.account.name = actor.account.accountName;
                        delete actor.account.accountName;
                    }}
                }}
                ADL.XAPIWrapper.lrs.actor = JSON.stringify(actor);
                console.log("Actor normalized for ADL wrapper:", JSON.stringify(actor));
            }} catch(e) {{
                console.warn("Failed to normalize actor:", e);
            }}
        }}
    }})();
    </script>
</head>
<body>
    <div class="course-container">
    <div class="course-layout">"""
    
    def _get_home_screen(self, course: Dict, modules: list) -> str:
        """Generate home/intro screen matching reference design"""
        course_title = self._escape_html(course.get('title', 'Course'))
        course_description = self._escape_html(course.get('description', ''))
        course_overview = self._escape_html(course.get('overview', ''))
        learning_objectives = course.get('learningObjectives', [])
        
        # Build learning objectives list
        objectives_html = ""
        if learning_objectives:
            objectives_html = '<ul class="learning-objectives-list">'
            for obj in learning_objectives:
                objectives_html += f'<li>{self._escape_html(obj)}</li>'
            objectives_html += '</ul>'
        
        # Use background image style - single full-width header with overlay
        background_image_style = ""
        if modules and modules[0].get('imagePath'):
            image_path_obj = Path(modules[0]['imagePath'])
            image_name = image_path_obj.name
            background_image_style = f'background-image: url("assets/{image_name}");'
        
        return f'''
        <section class="home-screen" id="homeScreen">
            <div class="home-top-section" style="{background_image_style}">
                <div class="home-header-overlay">
                    <h1 class="home-course-title">{course_title}</h1>
                    <div class="home-buttons-container">
                        <button class="btn-start-course" onclick="startCourse()">{self._labels["start_course"]}</button>
                    </div>
                </div>
            </div>
            <div class="home-content-section">
                <h2 class="home-content-heading">{self._labels["purpose_of_training"]}</h2>
                <p class="home-content-description">{course_description}</p>
                {f'<p class="home-content-overview">{course_overview}</p>' if course_overview else ''}
                {f'<div class="home-learning-objectives"><p class="objectives-intro">{self._labels["objectives_intro"]}</p>{objectives_html}</div>' if learning_objectives else ''}
            </div>
        </section>'''
    
    def _get_course_instructions_section(self, course: Dict, modules: list, has_instructions_audio: bool = False, has_course_audio: bool = False) -> str:
        """Generate Course Instructions page with audio and locked navigation"""
        course_title = self._escape_html(course.get('title', 'Course'))
        total_modules = len(modules)
        
        # Calculate estimated course duration (assuming ~5-7 minutes per module)
        estimated_minutes = total_modules * 6
        
        # Generate instructions text using translated labels
        # Audio paragraph is only included if the course actually has audio
        parts = [
            self._labels["instructions_welcome"].format(course_title),
            self._labels["instructions_duration"].format(estimated_minutes),
            self._labels["instructions_kc"],
            self._labels["instructions_quiz"],
        ]
        if has_course_audio:
            parts.append(self._labels["instructions_audio"])
        parts.append(self._labels["instructions_support"])
        parts.append(self._labels["instructions_goal"])
        instructions_text = "\n\n".join(parts)
        
        # Escape HTML in instructions
        instructions_html = self._escape_html(instructions_text).replace('\n\n', '</p><p>').replace('\n', '<br>')
        instructions_html = f'<p>{instructions_html}</p>'
        
        # Only render audio player if instructions audio was actually generated
        audio_source = 'assets/instructions-audio.mp3'
        
        return f'''
        <section class="course-instructions-section" id="courseInstructionsSection" style="display: none;">
            <div class="instructions-header">
                <div class="instructions-header-content">
                    <div class="instructions-lesson-number">{self._labels["lesson_x_of_y"].format(1, total_modules + 1)}</div>
                    <h1 class="instructions-title">{self._labels["course_instructions"]}</h1>
                    <div class="instructions-header-line"></div>
                </div>
            </div>
            <div class="instructions-content">
                {instructions_html}
                        {'<div class="instructions-audio-player"><audio id="instructions-audio" controls><source src="' + audio_source + '" type="audio/mpeg">Your browser does not support the audio element.</audio><script>(function(){{const audio=document.getElementById("instructions-audio");let lastValidTime=0,audioCompleted=false,isUserSeeking=false;audio.addEventListener("timeupdate",function(){{if(audioCompleted&&audio.currentTime===0){{audioCompleted=false;lastValidTime=0;return;}}if(!isUserSeeking){{if(audio.currentTime>=lastValidTime)lastValidTime=audio.currentTime;else audio.currentTime=lastValidTime;}}}});audio.addEventListener("seeking",function(){{isUserSeeking=true;if(audioCompleted&&audio.currentTime===0){{audioCompleted=false;lastValidTime=0;isUserSeeking=false;return;}}if(audio.currentTime>lastValidTime)audio.currentTime=lastValidTime;else if(audio.currentTime<lastValidTime)audio.currentTime=lastValidTime;}});audio.addEventListener("seeked",function(){{isUserSeeking=false;if(!audioCompleted&&audio.currentTime!==lastValidTime)audio.currentTime=lastValidTime;}});audio.addEventListener("play",function(){{if(audioCompleted&&audio.currentTime===0){{audioCompleted=false;lastValidTime=0;}}}});audio.addEventListener("ended",function(){{audioCompleted=true;lastValidTime=audio.duration||0;}});audio.addEventListener("loadedmetadata",function(){{if(audio.currentTime===0)lastValidTime=0;}});}})();</script></div>' if has_instructions_audio else ''}
            <div class="instructions-navigation-bar" id="instructionsNavBar">
                <div class="nav-bar-locked" id="instructionsLockMsg">
                    <span class="nav-lock-icon">
                        <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg" style="vertical-align: -1px; margin-right: 2px;"><path fill-rule="evenodd" clip-rule="evenodd" d="M8 1a3.5 3.5 0 0 0-3.5 3.5V6H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-.5V4.5A3.5 3.5 0 0 0 8 1Zm1.5 5V4.5a1.5 1.5 0 0 0-3 0V6h3ZM8 9.5a1 1 0 1 0 0 2 1 1 0 0 0 0-2Z"/></svg>
                    </span>
                    <span class="nav-lock-text">{self._labels["lock_text"]}</span>
                </div>
                <button class="nav-continue-button" id="instructionsContinueBtn" onclick="completeInstructions()" disabled style="display: none;">
                    {self._labels['continue_btn']}
                </button>
            </div>
        </section>'''
    
    def _get_sidebar(self, modules: list, course: Dict) -> str:
        """Generate sidebar with module navigation"""
        sidebar_html = f'''
        <aside class="sidebar" id="sidebar" style="display: none;">
        <button class="sidebar-toggle" onclick="toggleSidebar()">☰</button>
        <div class="sidebar-header">
            <h3>{self._escape_html(course.get('title', 'Course'))}</h3>
            <div class="sidebar-progress">
                <div class="sidebar-progress-fill" id="sidebarProgressFill" style="width: 0%"></div>
                <div class="sidebar-progress-text" id="sidebarProgressText">0% {self._labels["pct_complete"]}</div>
            </div>
        </div>
        <div class="sidebar-actions" style="padding: 10px 20px; border-bottom: 1px solid #e0e0e0; display: flex; justify-content: flex-end; background: #f5f5f5;">
            <button id="toggleAllBtn" onclick="toggleAllModules()" class="collapse-all-btn" style="background: none; border: none; font-size: 11pt; color: #666; cursor: pointer; display: flex; align-items: center; gap: 4px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m18 15-6-6-6 6"/></svg> 
                Collapse All
            </button>
        </div>
        <nav class="sidebar-nav">
            <ul class="module-list">'''
        
        for idx, module in enumerate(modules, 1):
            module_num = module.get('moduleNumber', idx)
            module_title = module.get('moduleTitle', f'Module {module_num}')
            module_title = self._truncate_title(module_title, max_words=6)
            content_data = module.get('content', {})
            module_summary = "" # Summary option removed from left side as requested
                
            # Module starts locked except first one
            is_locked = module_num > 1
            locked_class = 'locked' if is_locked else 'active'
            onclick = '' if is_locked else f'onclick="navigateToModule({module_num})"'
            circle_style = 'style="background: #025e9b; border-color: #025e9b; box-shadow: 0 0 0 2px rgba(2, 94, 155, 0.2);"' if module_num == 1 else ''
            
            # The first module is expanded by default
            accordion_display = 'block' if module_num == 1 else 'none'
            chevron_rot = 'rotate(180deg)' if module_num == 1 else 'rotate(0deg)'
            
            sidebar_html += f'''
                <li class="module-nav-wrapper" data-module="{module_num}">
                    <div class="module-nav-item {locked_class}" data-module="{module_num}">
                        <div class="module-nav-item-clickable" {onclick}>
                            <span class="module-nav-circle" {circle_style}></span>
                            <span class="module-nav-title">{self._escape_html(module_title)}</span>
                            <span class="module-status">
                                <span class="status-icon locked-icon" style="display: {'inline' if is_locked else 'none'}">
                                    <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg" style="vertical-align: -1px; margin-right: 2px;"><path fill-rule="evenodd" clip-rule="evenodd" d="M8 1a3.5 3.5 0 0 0-3.5 3.5V6H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-.5V4.5A3.5 3.5 0 0 0 8 1Zm1.5 5V4.5a1.5 1.5 0 0 0-3 0V6h3ZM8 9.5a1 1 0 1 0 0 2 1 1 0 0 0 0-2Z"/></svg>
                                </span>
                                <span class="status-icon completed-icon" style="display: none">
                                    <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg" style="vertical-align: -1px; margin-right: 2px;"><path fill-rule="evenodd" clip-rule="evenodd" d="M13.707 4.707a1 1 0 0 0-1.414-1.414L6 9.586 3.707 7.293a1 1 0 0 0-1.414 1.414l3 3a1 1 0 0 0 1.414 0l7-7Z"/></svg>
                                </span>
                            </span>
                        </div>
                        <button class="accordion-toggle-btn" onclick="toggleModuleAccordion({module_num}, event)" aria-expanded="{'true' if module_num == 1 else 'false'}">
                            <svg class="chevron-icon-{module_num}" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="transition: transform 0.2s; transform: {chevron_rot};"><path d="m6 9 6 6 6-6"/></svg>
                        </button>
                    </div>
                    <div class="module-accordion-content" id="accordion-content-{module_num}" style="display: {accordion_display};">
                        {self._get_section_nav_items(module, module_num)}
                    </div>
                </li>'''
        
        total_modules = len(modules)
        quiz = course.get('quiz', {})
        quiz_nav_html = ''
        if quiz and quiz.get('questions'):
            quiz_nav_html = f'''
            <div id="quiz-nav-item" onclick="navigateToQuiz()" style="display: none; align-items: center; gap: 10px; padding: 10px 20px; cursor: pointer; border-top: 1px solid #e0e0e0; color: #025e9b; font-size: 13px; font-weight: 500;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                <span>{self._labels["final_quiz"]}</span>
            </div>'''
        sidebar_html += f'''
            </ul>
        </nav>
        {quiz_nav_html}
        <div class="sidebar-footer">
            <div class="sidebar-total-lessons">
                <span class="footer-icon">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
                </span>
                <span class="footer-text">Total Modules</span>
                <span class="footer-count">{total_modules}</span>
            </div>
        </div>
        </aside>'''
        return sidebar_html
    
    def _get_section_nav_items(self, module: Dict, module_num: int) -> str:
        """Generate section-level navigation items under a module in the sidebar"""
        content_data = module.get('content', {})
        if not isinstance(content_data, dict):
            return ''
        sections = content_data.get('sections', [])
        if not sections:
            return ''
        
        items_html = '<ul class="section-nav-list">'
        for idx, section in enumerate(sections, 1):
            section_title = section.get('sectionTitle', f'Section {idx}')
            display_title = self._truncate_title(section_title, max_words=6)
            items_html += f'''
                <li class="section-nav-item" id="section-nav-{module_num}-{idx}" 
                    onclick="navigateToSection({module_num}, {idx})" title="{self._escape_html(section_title)}">
                    <span class="section-nav-dot"></span>
                    <span class="section-nav-title">{self._escape_html(display_title)}</span>
                </li>'''
        items_html += '</ul>'
        return items_html
    
    def _get_course_outline_section(self, course: Dict, modules: list) -> str:
        outline_items = []
        for module in modules:
            outline_items.append(
                f'<li class="outline-item">'
                f'<span class="module-number">{self._labels["module_word"]} {module["moduleNumber"]}</span>'
                f'<span class="module-title">{self._escape_html(module["moduleTitle"])}</span>'
                f'</li>'
            )
        
        return f"""
        <section class="course-outline" id="courseOutline">
            <h2>{self._labels['course_outline']}</h2>
            <p class="course-description">{self._escape_html(course.get('description', ''))}</p>
            {f'<div class="course-overview"><h3>{self._labels["course_overview"]}</h3><p>{self._escape_html(course.get("overview", ""))}</p></div>' if course.get('overview') else ''}
            {f'<div class="course-learning-objectives"><h3>{self._labels["course_learning_obj"]}</h3><ul>{"".join([f"<li>{self._escape_html(obj)}</li>" for obj in course.get("learningObjectives", [])])}</ul></div>' if course.get('learningObjectives') else ''}
            <ul class="outline-list">
                {''.join(outline_items)}
            </ul>
            <button class="btn-primary" onclick="startCourse()">{self._labels['start_course_lower']}</button>
        </section>"""
    
    def _truncate_title(self, title: str, max_words: int = 6) -> str:
        """Truncate title to a maximum number of words."""
        if not title:
            return ""
        words = title.strip().split()
        if len(words) <= max_words:
            return title
        return " ".join(words[:max_words]) + "..."
        
    def _get_module_section(self, module: Dict, total_modules: int = 2) -> str:
        module_num = module['moduleNumber']
        module_title = self._escape_html(module['moduleTitle'])
        
        # Get sections count for organizing interactives
        content_data = module.get('content', {})
        content_dict = content_data if isinstance(content_data, dict) else {}
        sections = content_data.get('sections', []) if isinstance(content_data, dict) else []
        total_sections = len(sections) if sections else 0
        
        # Prepare image HTML for first section with preloading
        module_image_html = ""
        if module.get('imagePath'):
            image_path_obj = Path(module['imagePath'])
            image_name = image_path_obj.name
            # Use eager loading and add preload link
            module_image_html = f'''<link rel="preload" as="image" href="assets/{image_name}">
            <div class="module-image" style="display: block; visibility: visible;">
                <img src="assets/{image_name}" alt="{module_title}" loading="eager" fetchpriority="high" id="module-{module_num}-image" data-image-id="assets/{image_name}" style="max-width: 100%; height: auto; display: block;" onerror="console.error('Image failed to load: assets/{image_name}'); this.parentElement.style.display='none';" onload="if(typeof trackImageViewed === 'function') trackImageViewed('assets/{image_name}');">
            </div>'''
        
        # Build content HTML with hierarchical section numbering and section audio
        # Pass image HTML to be inserted in first section, and module data for interactives
        content_html = self._build_module_content_html(
            module.get('content', {}), 
            module_num, 
            module_image_html if total_sections > 0 else "",
            module  # Pass full module for flashcards and knowledge check
        )
        
        # Image HTML - only used if no sections (legacy support)
        image_html = ""
        if total_sections == 0 and module.get('imagePath'):
            image_html = module_image_html
        
        # Module-level audio removed - sections have their own audio
        audio_html = ""
        # Legacy support: if module has audio but no sections, keep module-level audio
        if (not sections or total_sections == 0) and (module.get('audioPath') or module.get('audioPaths')):
            transcript = self._escape_html(module.get('transcript', ''))
            
            # Check if we have multiple chunks
            audio_paths = module.get('audioPaths')
            if audio_paths and len(audio_paths) > 1:
                # Multiple chunks - use sequential playback
                audio_files_json = []
                for audio_path in audio_paths:
                    if audio_path:
                        audio_path_obj = Path(audio_path)
                        audio_files_json.append(f'"assets/{audio_path_obj.name}"')
                
                audio_files_str = ', '.join(audio_files_json)
                audio_html = f'''
            <div class="module-audio">
                <audio id="audio-{module_num}" controls autoplay></audio>
                <script>
                    // Initialize sequential audio playback for module {module_num}
                    (function() {{
                        const audioFiles = [{audio_files_str}];
                        const audio = document.getElementById('audio-{module_num}');
                        audio.setAttribute('data-chunked', 'true');
                        let currentChunk = 0;
                        let lastValidTime = 0;
                        let audioCompleted = false;
                        let isUserSeeking = false;
                        
                        // Prevent seeking forward or backward
                        audio.addEventListener('timeupdate', function() {{
                            // Allow restart only if audio has completed
                            if (audioCompleted && audio.currentTime === 0) {{
                                audioCompleted = false;
                                lastValidTime = 0;
                                return;
                            }}
                            
                            // Only check if user is not seeking (to allow normal playback)
                            if (!isUserSeeking) {{
                                // Allow natural forward progress
                                if (audio.currentTime >= lastValidTime) {{
                                    lastValidTime = audio.currentTime;
                                }} else {{
                                    // Backward movement detected (user tried to seek backward)
                                    audio.currentTime = lastValidTime;
                                }}
                            }}
                        }});
                        
                        // Prevent seeking via seeking event - immediate block
                        audio.addEventListener('seeking', function() {{
                            isUserSeeking = true;
                            // Allow restart if audio completed
                            if (audioCompleted && audio.currentTime === 0) {{
                                audioCompleted = false;
                                lastValidTime = 0;
                                isUserSeeking = false;
                                return;
                            }}
                            // Prevent forward seeking - only allow if going back to last valid time
                            if (audio.currentTime > lastValidTime) {{
                                // User tried to seek forward, reset to last valid position
                                audio.currentTime = lastValidTime;
                            }} else if (audio.currentTime < lastValidTime) {{
                                // User tried to seek backward, reset to last valid position
                                audio.currentTime = lastValidTime;
                            }}
                        }});
                        
                        // Reset seeking flag after seek completes
                        audio.addEventListener('seeked', function() {{
                            isUserSeeking = false;
                            // Ensure we're at the last valid position
                            if (!audioCompleted && audio.currentTime !== lastValidTime) {{
                                audio.currentTime = lastValidTime;
                            }}
                        }});
                        
                        // Make loadNextChunk globally accessible for showModule()
                        window['loadNextChunk_{module_num}'] = function loadNextChunk() {{
                            if (currentChunk < audioFiles.length) {{
                                // Stop all other audio elements to prevent overlap
                                document.querySelectorAll('audio').forEach(otherAudio => {{
                                    if (otherAudio !== audio && !otherAudio.paused) {{
                                        otherAudio.pause();
                                        otherAudio.currentTime = 0;
                                    }}
                                }});
                                
                                audio.src = audioFiles[currentChunk];
                                audio.load();
                                lastValidTime = 0; // Reset for new chunk
                                audio.play().catch(e => console.log('Autoplay prevented:', e));
                            }}
                        }}
                        
                        // Track audio interactions and prevent overlap
                        audio.addEventListener('play', function() {{
                            // Stop all other audio elements when this one starts
                            document.querySelectorAll('audio').forEach(otherAudio => {{
                                if (otherAudio !== audio && !otherAudio.paused) {{
                                    otherAudio.pause();
                                    otherAudio.currentTime = 0;
                                }}
                            }});
                            
                            // Reset completion flag when user manually plays
                            if (audioCompleted && audio.currentTime === 0) {{
                                audioCompleted = false;
                                lastValidTime = 0;
                            }}
                            
                            if (typeof trackAudioListened === 'function') {{
                                trackAudioListened(audioFiles[currentChunk]);
                            }}
                        }});
                        
                        audio.addEventListener('pause', function() {{
                            if (!audio.ended && typeof trackAudioPaused === 'function') {{
                                trackAudioPaused(audioFiles[currentChunk]);
                            }}
                        }});
                        
                        audio.addEventListener('ended', function() {{
                            // Track completion of current chunk
                            if (typeof trackAudioListened === 'function') {{
                                trackAudioListened(audioFiles[currentChunk]);
                            }}
                            currentChunk++;
                            if (currentChunk < audioFiles.length) {{
                                // Load and play next chunk
                                lastValidTime = 0; // Reset for new chunk
                                window['loadNextChunk_{module_num}']();
                            }} else {{
                                // All chunks completed - allow restart
                                audioCompleted = true;
                                lastValidTime = audio.duration || 0;
                            }}
                        }});
                        
                        // Reset function to restart from beginning
                        window['resetAudio_{module_num}'] = function() {{
                            currentChunk = 0;
                            audio.currentTime = 0;
                            lastValidTime = 0;
                        }};
                        
                        // Reset lastValidTime when new chunk loads
                        audio.addEventListener('loadedmetadata', function() {{
                            if (audio.currentTime === 0) {{
                                lastValidTime = 0;
                            }}
                        }});
                    }})();
                </script>
            </div>'''
            else:
                # Single audio file (backward compatible)
                audio_path = module.get('audioPath')
                if audio_path:
                    audio_path_obj = Path(audio_path)
                    audio_name = audio_path_obj.name
                    audio_html = f'''
            <div class="module-audio">
                <audio id="audio-{module_num}" controls autoplay data-audio-path="assets/{audio_name}">
                    <source src="assets/{audio_name}" type="audio/mpeg">
                    Your browser does not support the audio element.
                </audio>
                <script>
                    // Track audio interactions for single file
                    (function() {{
                        const audio = document.getElementById('audio-{module_num}');
                        const audioPath = audio.getAttribute('data-audio-path');
                        let lastValidTime = 0;
                        let audioCompleted = false;
                        let isUserSeeking = false;
                        
                        // Prevent seeking forward or backward
                        audio.addEventListener('timeupdate', function() {{
                            // Allow restart only if audio has completed
                            if (audioCompleted && audio.currentTime === 0) {{
                                audioCompleted = false;
                                lastValidTime = 0;
                                return;
                            }}
                            
                            // Only check if user is not seeking (to allow normal playback)
                            if (!isUserSeeking) {{
                                // Allow natural forward progress
                                if (audio.currentTime >= lastValidTime) {{
                                    lastValidTime = audio.currentTime;
                                }} else {{
                                    // Backward movement detected (user tried to seek backward)
                                    audio.currentTime = lastValidTime;
                                }}
                            }}
                        }});
                        
                        // Prevent seeking via seeking event - immediate block
                        audio.addEventListener('seeking', function() {{
                            isUserSeeking = true;
                            // Allow restart if audio completed
                            if (audioCompleted && audio.currentTime === 0) {{
                                audioCompleted = false;
                                lastValidTime = 0;
                                isUserSeeking = false;
                                return;
                            }}
                            // Prevent forward seeking - only allow if going back to last valid time
                            if (audio.currentTime > lastValidTime) {{
                                // User tried to seek forward, reset to last valid position
                                audio.currentTime = lastValidTime;
                            }} else if (audio.currentTime < lastValidTime) {{
                                // User tried to seek backward, reset to last valid position
                                audio.currentTime = lastValidTime;
                            }}
                        }});
                        
                        // Reset seeking flag after seek completes
                        audio.addEventListener('seeked', function() {{
                            isUserSeeking = false;
                            // Ensure we're at the last valid position
                            if (!audioCompleted && audio.currentTime !== lastValidTime) {{
                                audio.currentTime = lastValidTime;
                            }}
                        }});
                        
                        if (audioPath) {{
                            audio.addEventListener('play', function() {{
                                // Stop all other audio elements to prevent overlap
                                document.querySelectorAll('audio').forEach(otherAudio => {{
                                    if (otherAudio !== audio && !otherAudio.paused) {{
                                        otherAudio.pause();
                                        otherAudio.currentTime = 0;
                                    }}
                                }});
                                
                                // Reset completion flag when user manually plays
                                if (audioCompleted && audio.currentTime === 0) {{
                                    audioCompleted = false;
                                    lastValidTime = 0;
                                }}
                                
                                if (typeof trackAudioListened === 'function') {{
                                    trackAudioListened(audioPath);
                                }}
                            }});
                            
                            audio.addEventListener('pause', function() {{
                                if (!audio.ended && typeof trackAudioPaused === 'function') {{
                                    trackAudioPaused(audioPath);
                                }}
                            }});
                            
                            audio.addEventListener('ended', function() {{
                                // Audio completed - allow restart
                                audioCompleted = true;
                                lastValidTime = audio.duration || 0;
                            }});
                        }}
                        
                        // Reset lastValidTime when audio loads
                        audio.addEventListener('loadedmetadata', function() {{
                            if (audio.currentTime === 0) {{
                                lastValidTime = 0;
                            }}
                        }});
                    }})();
                </script>
            </div>'''
        
        # Knowledge check and flashcards are now injected into the last section by _build_module_content_html
        # Only add them at module level if there are no sections (legacy support)
        kc_html = ""
        flashcards_html = ""
        if total_sections == 0:
            if module.get('knowledgeCheck'):
                kc_html = self._build_knowledge_check_html(module['knowledgeCheck'], module_num)

        # Add Interactive Block BEFORE flashcards (legacy module level)
        if total_sections == 0 and content_dict.get('interactiveBlock'):
            ib_html = self._render_interactive_block(
                content_dict['interactiveBlock'],
                module_num, 
                1
            )
            if ib_html:
                content_html += f'<div class="module-interactive-block interactive-theme-shell" id="module-{module_num}-ib" style="margin: 32px 0;">{ib_html}</div>'

            if module.get('flashcards'):
                # For legacy code path, use section 1 as default
                flashcards_html = self._build_flashcards_html(module['flashcards'], module_num, section_num=1)
        
        # Use passed total_modules (should be integer)
        total_modules_int = total_modules if isinstance(total_modules, int) else 2
        
        # Learning Objectives removed - only shown in course overview
        
        return f'''
        <section class="module-section" id="module-{module_num}" style="display: none;">
            <div class="module-header">
                <h2 class="module-title">{module_title}</h2>
                <div class="module-progress">{self._labels["module_x_of_y"].format(module_num, total_modules_int)}</div>

            </div>
            <div class="module-content">
                {content_html}
            </div>
            {image_html}
            {audio_html}
            {kc_html}
            {flashcards_html}
        </section>'''
    
    def _build_module_content_html(self, content: Dict, module_num: int = 1, module_image_html: str = "", module_data: Dict = None) -> str:
        """Build HTML from module content structure with hierarchical section numbering and per-section audio
        
        Args:
            content: Module content dict with sections
            module_num: Module number
            module_image_html: HTML for module image (inserted in first section)
            module_data: Full module data (for flashcards and knowledge check at end)
        """
        if isinstance(content, str):
            return f'<div class="content-text">{self._format_content(content)}</div>'
        
        html_parts = []
        
        if isinstance(content, dict) and 'sections' in content:
            sections = content['sections']
            for section_idx, section in enumerate(sections):
                section_num = section_idx + 1
                section_title = section.get("sectionTitle", f"Section {section_num}")
                section_id = f"module-{module_num}-section-{section_num}"
                
                # Hierarchical numbering: Module 1, Section 1.1, 1.2, etc.
                section_number_label = f"{module_num}.{section_num}"
                
                # All sections start hidden - only shown after Start Course is clicked
                section_html = f'<div class="content-section" id="{section_id}" style="display: none;">'
                section_html += f'<h3 class="section-title">{section_number_label} {self._escape_html(section_title)}</h3>'
                
                # Add section content FIRST
                section_html += f'<div class="section-content">{self._format_content(section.get("content", ""))}</div>'
                
                if 'concepts' in section:
                    scenario_rendered_this_section = False
                    for concept in section['concepts']:
                        section_html += f'<div class="concept-block">'
                        section_html += f'<h4 class="concept-title">{self._escape_html(concept.get("conceptTitle", ""))}</h4>'
                        section_html += f'<p class="concept-explanation">{self._format_content(concept.get("explanation", ""))}</p>'
                        if (not scenario_rendered_this_section
                                and concept.get('scenario')
                                and isinstance(concept.get('scenario'), dict)):
                            scenario = concept['scenario']
                            if scenario.get('whatToDo') or scenario.get('whyItMatters') or scenario.get('howToPrevent'):
                                prevent_html = ""
                                if scenario.get('howToPrevent'):
                                    prevent_html = (
                                        '<div class="vidhya-scenario-prevent">'
                                        '<p class="vidhya-scenario-label">How to prevent?</p>'
                                        f'<p class="vidhya-scenario-text">{self._format_content(scenario.get("howToPrevent", ""))}</p>'
                                        '</div>'
                                    )
                                section_html += f'''
                                <div class="vidhya-scenario-container">
                                    <h3 class="vidhya-scenario-header">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="vidhya-scenario-icon"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.9 1.2 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/></svg>
                                        {self._labels["real_world_scenario"]}
                                    </h3>
                                    <div class="vidhya-scenario-card">
                                        <h4 class="vidhya-scenario-title">Scenario</h4>
                                        <p class="vidhya-scenario-situation">{self._format_content(scenario.get("description", ""))}</p>
                                        <div class="vidhya-scenario-grid">
                                            <div class="vidhya-scenario-action">
                                                <p class="vidhya-scenario-label">{self._labels["what_to_do"]}</p>
                                                <p class="vidhya-scenario-text">{self._format_content(scenario.get("whatToDo", ""))}</p>
                                            </div>
                                            <div class="vidhya-scenario-reason">
                                                <p class="vidhya-scenario-label">{self._labels["why_it_matters"]}</p>
                                                <p class="vidhya-scenario-text">{self._format_content(scenario.get("whyItMatters", ""))}</p>
                                            </div>
                                        </div>
                                        {prevent_html}
                                    </div>
                                </div>'''
                                scenario_rendered_this_section = True

                        section_html += '</div>'
                
                # Add module image AFTER content (only in first section)
                if section_idx == 0 and module_image_html:
                    section_html += module_image_html
                
                # Add section audio AFTER image
                section_audio_path = section.get('audioPath')
                section_audio_paths = section.get('audioPaths')
                section_transcript = self._escape_html(section.get('transcript', ''))
                
                # Track if this section has audio for continue button logic
                section_has_audio = bool(section_audio_path or section_audio_paths)
                
                # Add section audio
                if section_has_audio:
                    audio_id = f"audio-{module_num}-{section_num}"
                    
                    if section_audio_paths and len(section_audio_paths) > 1:
                        # Multiple chunks for this section
                        audio_files_json = []
                        for audio_path in section_audio_paths:
                            if audio_path:
                                audio_path_obj = Path(audio_path)
                                audio_files_json.append(f'"assets/{audio_path_obj.name}"')
                        
                        audio_files_str = ', '.join(audio_files_json)
                        section_html += f'''
                <div class="section-audio">
                    <audio id="{audio_id}" controls data-audio-title="Audio: {section_number_label} {self._escape_html(section_title)}"></audio>
                    <script>
                        (function() {{
                            const audioFiles = [{audio_files_str}];
                            const audio = document.getElementById('{audio_id}');
                            audio.setAttribute('data-chunked', 'true');
                            let currentChunk = 0;
                            let lastValidTime = 0;
                            let audioCompleted = false;
                            let isUserSeeking = false;
                            
                            // Prevent seeking forward or backward
                            audio.addEventListener('timeupdate', function() {{
                                // Allow restart only if audio has completed
                                if (audioCompleted && audio.currentTime === 0) {{
                                    audioCompleted = false;
                                    lastValidTime = 0;
                                    return;
                                }}
                                
                                // Only check if user is not seeking (to allow normal playback)
                                if (!isUserSeeking) {{
                                    // Allow natural forward progress
                                    if (audio.currentTime >= lastValidTime) {{
                                        lastValidTime = audio.currentTime;
                                    }} else {{
                                        // Backward movement detected (user tried to seek backward)
                                        audio.currentTime = lastValidTime;
                                    }}
                                }}
                            }});
                            
                            // Prevent seeking via seeking event - immediate block
                            audio.addEventListener('seeking', function() {{
                                isUserSeeking = true;
                                // Allow restart if audio completed
                                if (audioCompleted && audio.currentTime === 0) {{
                                    audioCompleted = false;
                                    lastValidTime = 0;
                                    isUserSeeking = false;
                                    return;
                                }}
                                // Prevent forward seeking - only allow if going back to last valid time
                                if (audio.currentTime > lastValidTime) {{
                                    // User tried to seek forward, reset to last valid position
                                    audio.currentTime = lastValidTime;
                                }} else if (audio.currentTime < lastValidTime) {{
                                    // User tried to seek backward, reset to last valid position
                                    audio.currentTime = lastValidTime;
                                }}
                            }});
                            
                            // Reset seeking flag after seek completes
                            audio.addEventListener('seeked', function() {{
                                isUserSeeking = false;
                                // Ensure we're at the last valid position
                                if (!audioCompleted && audio.currentTime !== lastValidTime) {{
                                    audio.currentTime = lastValidTime;
                                }}
                            }});
                            
                            function loadNextChunk() {{
                                // Stop all other audio
                                document.querySelectorAll('audio').forEach(otherAudio => {{
                                    if (otherAudio !== audio && !otherAudio.paused) {{
                                        otherAudio.pause();
                                        otherAudio.currentTime = 0;
                                    }}
                                }});
                                
                                if (currentChunk < audioFiles.length) {{
                                    audio.src = audioFiles[currentChunk];
                                    audio.load();
                                    lastValidTime = 0; // Reset for new chunk
                                }}
                            }}
                            
                            audio.addEventListener('play', function() {{
                                document.querySelectorAll('audio').forEach(otherAudio => {{
                                    if (otherAudio !== audio && !otherAudio.paused) {{
                                        otherAudio.pause();
                                        otherAudio.currentTime = 0;
                                    }}
                                }});
                                
                                // Reset completion flag when user manually plays
                                if (audioCompleted && audio.currentTime === 0) {{
                                    audioCompleted = false;
                                    lastValidTime = 0;
                                }}
                                
                                if (typeof trackAudioListened === 'function') {{
                                    trackAudioListened(audioFiles[currentChunk]);
                                }}
                            }});
                            
                            audio.addEventListener('ended', function() {{
                                if (typeof trackAudioListened === 'function') {{
                                    trackAudioListened(audioFiles[currentChunk]);
                                }}
                                currentChunk++;
                                if (currentChunk < audioFiles.length) {{
                                    // Load and play next chunk
                                    lastValidTime = 0; // Reset for new chunk
                                    loadNextChunk();
                                    audio.play().catch(e => console.log('Autoplay prevented:', e));
                                }} else {{
                                    // All chunks completed - allow restart
                                    audioCompleted = true;
                                    lastValidTime = audio.duration || 0;
                                }}
                            }});
                            
                            // Auto-play only once per section (first time this section's audio comes into view)
                            // Track if this section's audio has been auto-played
                            const sectionAutoplayKey = 'section_' + moduleNum + '_' + sectionNum + '_audio_autoplayed';
                            
                            // Auto-play first chunk when audio element comes into view
                            // Only if course has started AND this section's audio hasn't been auto-played yet
                            const observer = new IntersectionObserver((entries) => {{
                                entries.forEach(entry => {{
                                    // Only play when the audio element itself comes into view AND course has started
                                    // AND this section's audio hasn't been auto-played yet
                                    if (entry.isIntersecting && entry.target.id === '{audio_id}' && window.courseStarted && !window[sectionAutoplayKey]) {{
                                        window[sectionAutoplayKey] = true; // Mark as auto-played for this section
                                        loadNextChunk();
                                        audio.play().catch(e => console.log('Autoplay prevented:', e));
                                    }}
                                }});
                            }}, {{ threshold: 0.7 }});
                            
                            // Observe the audio element, not the entire section
                            setTimeout(() => {{
                                const audioElement = document.getElementById('{audio_id}');
                                if (audioElement) {{
                                    observer.observe(audioElement);
                                }}
                            }}, 100);
                            
                        // Reset lastValidTime when new chunk loads
                        audio.addEventListener('loadedmetadata', function() {{
                            if (audio.currentTime === 0) {{
                                lastValidTime = 0;
                            }}
                        }});
                        }})();
                    </script>
                </div>'''
                    else:
                        # Single audio file for this section
                        audio_file = Path(section_audio_path if section_audio_path else section_audio_paths[0] if section_audio_paths else '')
                        section_html += f'''
                <div class="section-audio">
                    <audio id="{audio_id}" controls src="assets/{audio_file.name}" data-audio-title="Audio: {section_number_label} {self._escape_html(section_title)}"></audio>
                    <script>
                        (function() {{
                            const audio = document.getElementById('{audio_id}');
                            let lastValidTime = 0;
                            let audioCompleted = false;
                            let isUserSeeking = false;
                            
                            // Prevent seeking forward or backward
                            audio.addEventListener('timeupdate', function() {{
                                // Allow restart only if audio has completed
                                if (audioCompleted && audio.currentTime === 0) {{
                                    audioCompleted = false;
                                    lastValidTime = 0;
                                    return;
                                }}
                                
                                // Only check if user is not seeking (to allow normal playback)
                                if (!isUserSeeking) {{
                                    // Allow natural forward progress
                                    if (audio.currentTime >= lastValidTime) {{
                                        lastValidTime = audio.currentTime;
                                    }} else {{
                                        // Backward movement detected (user tried to seek backward)
                                        audio.currentTime = lastValidTime;
                                    }}
                                }}
                            }});
                            
                            // Prevent seeking via seeking event - immediate block
                            audio.addEventListener('seeking', function() {{
                                isUserSeeking = true;
                                // Allow restart if audio completed
                                if (audioCompleted && audio.currentTime === 0) {{
                                    audioCompleted = false;
                                    lastValidTime = 0;
                                    isUserSeeking = false;
                                    return;
                                }}
                                // Prevent forward seeking - only allow if going back to last valid time
                                if (audio.currentTime > lastValidTime) {{
                                    // User tried to seek forward, reset to last valid position
                                    audio.currentTime = lastValidTime;
                                }} else if (audio.currentTime < lastValidTime) {{
                                    // User tried to seek backward, reset to last valid position
                                    audio.currentTime = lastValidTime;
                                }}
                            }});
                            
                            // Reset seeking flag after seek completes
                            audio.addEventListener('seeked', function() {{
                                isUserSeeking = false;
                                // Ensure we're at the last valid position
                                if (!audioCompleted && audio.currentTime !== lastValidTime) {{
                                    audio.currentTime = lastValidTime;
                                }}
                            }});
                            
                            // Stop all other audio when this plays
                            const stopAllOtherAudio = function() {{
                                document.querySelectorAll('audio').forEach(otherAudio => {{
                                    if (otherAudio !== audio && !otherAudio.paused) {{
                                        otherAudio.pause();
                                        otherAudio.currentTime = 0;
                                    }}
                                }});
                            }};
                            
                            audio.addEventListener('play', function() {{
                                stopAllOtherAudio();
                                
                                // Reset completion flag when user manually plays
                                if (audioCompleted && audio.currentTime === 0) {{
                                    audioCompleted = false;
                                    lastValidTime = 0;
                                }}
                                
                                if (typeof trackAudioListened === 'function') {{
                                    trackAudioListened('assets/{audio_file.name}');
                                }}
                            }});
                            
                            audio.addEventListener('ended', function() {{
                                // Audio completed - allow restart
                                audioCompleted = true;
                                lastValidTime = audio.duration || 0;
                            }});
                            
                            // Auto-play only once per section (first time this section's audio comes into view)
                            // Track if this section's audio has been auto-played
                            const sectionAutoplayKey = 'section_' + moduleNum + '_' + sectionNum + '_audio_autoplayed';
                            
                            // Auto-play when audio element comes into view
                            // Only if course has started AND this section's audio hasn't been auto-played yet
                            const observer = new IntersectionObserver((entries) => {{
                                entries.forEach(entry => {{
                                    // Only play when the audio element itself comes into view AND course has started
                                    // AND this section's audio hasn't been auto-played yet
                                    if (entry.isIntersecting && entry.target.id === '{audio_id}' && window.courseStarted && !window[sectionAutoplayKey]) {{
                                        window[sectionAutoplayKey] = true; // Mark as auto-played for this section
                                        // Stop all other audios before playing this one
                                        stopAllOtherAudio();
                                        audio.play().catch(e => console.log('Autoplay prevented:', e));
                                    }}
                                }});
                            }}, {{ threshold: 0.7 }});
                            
                            // Observe the audio element, not the entire section
                            setTimeout(() => {{
                                const audioElement = document.getElementById('{audio_id}');
                                if (audioElement) {{
                                    observer.observe(audioElement);
                                }}
                            }}, 100);
                            
                        // Reset lastValidTime when audio loads
                        audio.addEventListener('loadedmetadata', function() {{
                            if (audio.currentTime === 0) {{
                                lastValidTime = 0;
                            }}
                        }});
                        }})();
                    </script>
                </div>'''
                

                # Add Interactive Block BEFORE flashcards (only in last section)
                is_last_section = (section_idx == len(sections) - 1)
                module_content = {}
                if module_data and isinstance(module_data.get('content'), dict):
                    module_content = module_data.get('content') or {}

                if is_last_section and module_content.get('interactiveBlock'):
                    ib_html = self._render_interactive_block(
                        module_content['interactiveBlock'],
                        module_num, 
                        section_num
                    )
                    if ib_html:
                        section_html += f'<div class="section-interactive-block interactive-theme-shell" id="section-{module_num}-{section_num}-ib" style="margin: 32px 0;">{ib_html}</div>'

                # Add flashcards AFTER audio (per-section flashcards)
                # Check if this section has its own flashcards first, then fall back to module-level
                section_flashcards = section.get('flashcards')
                if not section_flashcards and module_data:
                    section_flashcards = module_data.get('flashcards')
                
                if section_flashcards:
                    flashcards_html = self._build_flashcards_html(section_flashcards, module_num, section_num)
                    if flashcards_html:
                        # Use section-specific ID for tracking
                        section_html += f'<div class="section-interactives interactive-theme-shell" id="section-{module_num}-{section_num}-flashcards">{flashcards_html}</div>'
                
                # Add knowledge check AFTER flashcards (if module has knowledge check)
                # Show knowledge check only in the last section
                is_last_section = (section_idx == len(sections) - 1)
                if is_last_section and module_data and module_data.get('knowledgeCheck'):
                    kc_html = self._build_knowledge_check_html(module_data['knowledgeCheck'], module_num, has_audio=section_has_audio)
                    if kc_html:
                        # Use section-specific ID for tracking
                        section_html += f'<div class="section-knowledge-check" id="section-{module_num}-{section_num}-kc">{kc_html}</div>'
                
                # Add Continue button AFTER knowledge check (or after flashcards if no knowledge check)
                # Continue button for each section
                continue_button_id = f"continue-{module_num}-{section_num}"
                has_knowledge_check = is_last_section and module_data and module_data.get('knowledgeCheck')
                has_flashcards = module_data and module_data.get('flashcards')
                
                # Build continue button with proper tracking
                section_html += f'''
                <div class="continue-block-wrapper" id="section-{module_num}-{section_num}-continue">
                    <div class="continue-content">
                        <div class="continue-lock-message" id="lock-msg-{module_num}-{section_num}">
                            <svg class="lock-icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg" style="vertical-align: -2px; margin-right: 6px;">
                                <path fill-rule="evenodd" clip-rule="evenodd" d="M8 1a3.5 3.5 0 0 0-3.5 3.5V6H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-.5V4.5A3.5 3.5 0 0 0 8 1Zm1.5 5V4.5a1.5 1.5 0 0 0-3 0V6h3ZM8 9.5a1 1 0 1 0 0 2 1 1 0 0 0 0-2Z"/>
                            </svg>
                            <span>{self._labels["lock_text"]}</span>
                        </div>
                        <button class="btn-primary btn-continue" id="{continue_button_id}" 
                                onclick="continueToNextSection({module_num}, {section_num}, {len(sections)})" 
                                disabled>{self._labels['continue_btn']}</button>
                    </div>
                </div>
                <script>
                    // Initialize section completion tracking for section {module_num}.{section_num}
                    (function() {{
                        const sectionNum = {section_num};
                        const moduleNum = {module_num};
                        const hasAudio = {str(section_has_audio).lower()};
                        const hasFlashcards = {str(bool(has_flashcards)).lower()};
                        const hasKC = {str(bool(has_knowledge_check)).lower()};
                        const sectionId = 'module-' + moduleNum + '-section-' + sectionNum;
                        const trackingKey = 'section_' + moduleNum + '_' + sectionNum + '_tracking';
                        const funcName = 'checkSectionCompletion_' + moduleNum + '_' + sectionNum;
                        
                        // Track interactions for this section
                        window[trackingKey] = {{
                            audioPlayed: false,
                            audioCompleted: !hasAudio, // If no audio, mark as completed immediately
                            contentViewed: false, // Will be set when section is visible
                            flashcardsInteracted: !hasFlashcards, // If no flashcards, consider it "done"
                            kcCompleted: !hasKC, // If no KC, consider it "done"
                            allComplete: false
                        }};
                        
                        // Check section completion - SIMPLIFIED AND MORE AGGRESSIVE
                        window[funcName] = function() {{
                            // Ensure tracking object exists
                            if (!window[trackingKey]) {{
                                window[trackingKey] = {{
                                    audioPlayed: false,
                                    audioCompleted: !hasAudio,
                                    contentViewed: false,
                                    flashcardsInteracted: !hasFlashcards,
                                    kcCompleted: !hasKC,
                                    allComplete: false
                                }};
                            }}
                            
                            const tracking = window[trackingKey];
                            const continueBtn = document.getElementById('continue-{module_num}-{section_num}');
                            
                            if (!continueBtn) {{
                                console.warn('Continue button not found for section {module_num}.{section_num}, retrying...');
                                // Retry after a short delay
                                setTimeout(() => {{
                                    const retryBtn = document.getElementById('continue-{module_num}-{section_num}');
                                    if (retryBtn) {{
                                        window[funcName]();
                                    }}
                                }}, 500);
                                return;
                            }}
                            
                            // SIMPLIFIED: Only require content viewed - audio can play in background
                            // Flashcards and KC are optional - auto-approve after short delay
                            const contentOk = tracking.contentViewed;
                            
                            // Audio doesn't block - if audio exists, it should autoplay but user can continue anyway
                            // Only require audio completion if audio has started playing (user can't skip if they started it)
                            const audioOk = !hasAudio || tracking.audioCompleted || !tracking.audioPlayed;
                            
                            // For flashcards, auto-approve after 2 seconds if user hasn't interacted
                            // This prevents blocking - user can still interact if they want
                            const timeSinceLoad = Date.now() - (window[trackingKey + '_loadTime'] || Date.now());
                            const flashcardsOk = tracking.flashcardsInteracted || (timeSinceLoad > 2000);
                            
                            // Knowledge check requires completion - NO auto-approval
                            const kcOk = tracking.kcCompleted;
                            
                            // Minimum requirement: content viewed (audio can continue playing in background)
                            const minimumComplete = contentOk;
                            
                            tracking.allComplete = minimumComplete && flashcardsOk && kcOk && audioOk;
                            
                            console.log('Section {module_num}.{section_num} completion check:', {{
                                hasAudio: hasAudio,
                                audioOk, 
                                contentOk, 
                                flashcardsOk, 
                                kcOk, 
                                allComplete: tracking.allComplete,
                                timeSinceLoad: timeSinceLoad
                            }});
                            
                            // Sync inline tracker state to global tracker (Change 5)
                            const sectionKey = moduleNum + '.' + sectionNum;
                            if (typeof sectionAudioPlayed !== 'undefined') {{
                                sectionAudioPlayed[sectionKey] = tracking.audioCompleted;
                            }}
                            if (typeof sectionContentViewed !== 'undefined') {{
                                sectionContentViewed[sectionKey] = tracking.contentViewed;
                            }}
                            
                            if (tracking.allComplete) {{
                                continueBtn.disabled = false;
                                continueBtn.classList.remove('disabled');
                                continueBtn.style.opacity = '1';
                                continueBtn.style.cursor = 'pointer';
                                continueBtn.style.pointerEvents = 'auto';
                                const lockMsg = document.getElementById('lock-msg-' + moduleNum + '-' + sectionNum);
                                if (lockMsg) lockMsg.style.display = 'none';
                                console.log('Continue button ENABLED for section ' + moduleNum + '.' + sectionNum);
                                
                                // Also call global checkSectionCompletion for consistency (Change 6)
                                if (typeof checkSectionCompletion === 'function') {{
                                    checkSectionCompletion(moduleNum, sectionNum);
                                }}
                            }} else {{
                                continueBtn.disabled = true;
                                continueBtn.classList.add('disabled');
                                const lockMsg = document.getElementById('lock-msg-' + moduleNum + '-' + sectionNum);
                                if (lockMsg) lockMsg.style.display = 'flex';
                                console.log('Continue button DISABLED - missing:', {{
                                    audio: !audioOk ? 'audio' : null,
                                    content: !contentOk ? 'content' : null,
                                    flashcards: !flashcardsOk ? 'flashcards' : null,
                                    kc: !kcOk ? 'knowledge check' : null
                                }});
                                
                                // Enable knowledge check if audio is completed
                                if (hasKC && audioOk) {{
                                    const kcOptions = document.querySelectorAll(`#kc-{module_num} .kc-option-btn`);
                                    kcOptions.forEach(option => {{
                                        option.disabled = false;
                                    }});
                                    const lockMessage = document.getElementById('kc-lock-message-{module_num}');
                                    if (lockMessage) {{
                                        lockMessage.style.display = 'none';
                                    }}
                                }} else if (hasKC && !audioOk) {{
                                    // Show lock message if audio not completed
                                    const kcOptions = document.querySelectorAll(`#kc-{module_num} .kc-option-btn`);
                                    kcOptions.forEach(option => {{
                                        option.disabled = true;
                                    }});
                                    const lockMessage = document.getElementById('kc-lock-message-{module_num}');
                                    if (lockMessage) {{
                                        lockMessage.style.display = 'flex';
                                    }}
                                }}
                            }}
                        }};
                        
                        // Store load time for timeout logic
                        window[trackingKey + '_loadTime'] = Date.now();
                        
                        // Audio completion tracking
                        if (hasAudio) {{
                            const audioEl = document.getElementById('audio-{module_num}-{section_num}');
                            if (audioEl) {{
                                audioEl.addEventListener('play', function() {{
                                    window[trackingKey].audioPlayed = true;
                                    console.log('Audio started playing for section {module_num}.{section_num}');
                                }});
                                audioEl.addEventListener('ended', function() {{
                                    window[trackingKey].audioCompleted = true;
                                    console.log('Audio completed for section {module_num}.{section_num}');
                                    
                                    // Unlock knowledge check if it exists for this module
                                    const kcCheckbox = document.getElementById('kc-{module_num}');
                                    const kcLockMessage = document.getElementById('kc-lock-message-{module_num}');
                                    if (kcCheckbox) {{
                                        kcCheckbox.style.display = 'block';
                                        if (kcLockMessage) kcLockMessage.style.display = 'none';
                                        // Enable KC option buttons
                                        const kcButtons = kcCheckbox.querySelectorAll('.kc-option-btn');
                                        kcButtons.forEach(btn => {{
                                            btn.disabled = false;
                                        }});
                                        console.log('Knowledge check unlocked for module {module_num}');
                                    }}
                                    
                                    window[funcName]();
                                }});
                                // Also check if audio is already completed (user might have played it before tracking was set up)
                                setTimeout(() => {{
                                    if (audioEl.ended) {{
                                        window[trackingKey].audioCompleted = true;
                                        console.log('Audio already ended for section {module_num}.{section_num}');
                                        
                                        // Unlock knowledge check if it exists for this module
                                        const kcCheckbox = document.getElementById('kc-{module_num}');
                                        const kcLockMessage = document.getElementById('kc-lock-message-{module_num}');
                                        if (kcCheckbox) {{
                                            kcCheckbox.style.display = 'block';
                                            if (kcLockMessage) kcLockMessage.style.display = 'none';
                                            // Enable KC option buttons
                                            const kcButtons = kcCheckbox.querySelectorAll('.kc-option-btn');
                                            kcButtons.forEach(btn => {{
                                                btn.disabled = false;
                                            }});
                                            console.log('Knowledge check unlocked for module {module_num}');
                                        }}
                                        
                                        window[funcName]();
                                    }}
                                }}, 100);
                            }} else {{
                                console.warn('Audio element not found for section {module_num}.{section_num}');
                                // If audio element doesn't exist, mark as completed
                                window[trackingKey].audioCompleted = true;
                                
                                // Unlock knowledge check if it exists for this module
                                const kcCheckbox = document.getElementById('kc-{module_num}');
                                const kcLockMessage = document.getElementById('kc-lock-message-{module_num}');
                                if (kcCheckbox) {{
                                    kcCheckbox.style.display = 'block';
                                    if (kcLockMessage) kcLockMessage.style.display = 'none';
                                    // Enable KC option buttons
                                    const kcButtons = kcCheckbox.querySelectorAll('.kc-option-btn');
                                    kcButtons.forEach(btn => {{
                                        btn.disabled = false;
                                    }});
                                    console.log('Knowledge check unlocked for module {module_num}');
                                }}
                                
                                window[funcName]();
                            }}
                        }}
                        
                        // No-audio KC setTimeout hack removed (Change 4)
                        // KC now starts visible by default, and radio buttons are enabled
                        // when has_audio=False is passed to _build_knowledge_check_html.
                        // No runtime JS fixup needed.
                        
                        // Content viewed tracking (scroll) - mark as viewed when section is shown
                        const sectionEl = document.getElementById(sectionId);
                        if (sectionEl) {{
                            // Mark content as viewed immediately when section becomes visible
                            const markContentViewed = () => {{
                                if (!window[trackingKey].contentViewed) {{
                                    window[trackingKey].contentViewed = true;
                                    console.log('Content marked as viewed for section {module_num}.{section_num}');
                                    window[funcName]();
                                }}
                            }};
                            
                            // Check if section is already visible (for first section)
                            const checkVisibility = () => {{
                                const rect = sectionEl.getBoundingClientRect();
                                const isVisible = rect.top < window.innerHeight && rect.bottom > 0;
                                if (!isVisible) return false;
                                
                                const viewportHeight = window.innerHeight;
                                const visibleHeight = Math.min(rect.bottom, viewportHeight) - Math.max(rect.top, 0);
                                const visibleRatio = visibleHeight / rect.height;
                                
                                // Lower threshold to 50% for easier triggering
                                if (visibleRatio >= 0.5) {{
                                    markContentViewed();
                                    return true;
                                }}
                                return false;
                            }};
                            
                            // Check immediately if section is already visible
                            setTimeout(() => {{
                                checkVisibility();
                                
                                // Use observer for sections that aren't visible yet
                                const observer = new IntersectionObserver((entries) => {{
                                    entries.forEach(entry => {{
                                        // Lower threshold to 50% for easier triggering
                                        if (entry.isIntersecting && entry.intersectionRatio >= 0.5) {{
                                            markContentViewed();
                                            observer.unobserve(entry.target); // Stop observing once triggered
                                        }}
                                    }});
                                }}, {{ threshold: 0.5 }});
                                observer.observe(sectionEl);
                            }}, 200);
                            
                            // Also mark as viewed when section display changes to 'block'
                            const checkDisplay = () => {{
                                if (sectionEl.style.display === 'block' || sectionEl.style.display === '') {{
                                    markContentViewed();
                                }}
                            }};
                            
                            // Watch for display changes
                            const displayObserver = new MutationObserver(checkDisplay);
                            displayObserver.observe(sectionEl, {{ attributes: true, attributeFilter: ['style'] }});
                            checkDisplay(); // Initial check
                        }} else {{
                            console.warn('Section element not found: ' + sectionId);
                            // If section doesn't exist, mark content as viewed anyway
                            window[trackingKey].contentViewed = true;
                            window[funcName]();
                        }}
                        
                        // Periodic check to ensure button enables (fallback) - MORE AGGRESSIVE
                        let checkCount = 0;
                        const maxChecks = 40; // Check for up to 20 seconds
                        const periodicCheck = setInterval(() => {{
                            checkCount++;
                            const sectionEl = document.getElementById(sectionId);
                            const continueBtn = document.getElementById('continue-{module_num}-{section_num}');
                            
                            if (sectionEl && continueBtn && sectionEl.style.display !== 'none') {{
                                // Mark content as viewed if section is visible
                                const rect = sectionEl.getBoundingClientRect();
                                const isVisible = rect.top < window.innerHeight && rect.bottom > 0;
                                if (isVisible && !window[trackingKey].contentViewed) {{
                                    window[trackingKey].contentViewed = true;
                                    console.log('Content viewed (via periodic check) for section {module_num}.{section_num}');
                                }}
                                
                                // Re-check audio if it exists
                                if (hasAudio) {{
                                    const audioEl = document.getElementById('audio-{module_num}-{section_num}');
                                    if (audioEl && audioEl.ended && !window[trackingKey].audioCompleted) {{
                                        window[trackingKey].audioCompleted = true;
                                        console.log('Audio completed (via periodic check) for section {module_num}.{section_num}');
                                    }}
                                }}
                                
                                // Force enable after 5 seconds if minimum requirements met
                                const timeSinceLoad = Date.now() - (window[trackingKey + '_loadTime'] || Date.now());
                                if (timeSinceLoad > 5000) {{
                                    const audioOk = !hasAudio || window[trackingKey].audioCompleted;
                                    const contentOk = window[trackingKey].contentViewed;
                                    const kcOk = window[trackingKey].kcCompleted;
                                    if (audioOk && contentOk && kcOk) {{
                                        // Force enable - user has been on section long enough and KC is done
                                        continueBtn.disabled = false;
                                        continueBtn.classList.remove('disabled');
                                        continueBtn.style.opacity = '1';
                                        continueBtn.style.cursor = 'pointer';
                                        continueBtn.style.pointerEvents = 'auto';
                                        window[trackingKey].allComplete = true;
                                        console.log('Continue button FORCE ENABLED after 5 seconds for section {module_num}.{section_num}');
                                        clearInterval(periodicCheck);
                                        return;
                                    }}
                                }}
                                
                                window[funcName]();
                            }}
                            
                            if (checkCount >= maxChecks || window[trackingKey].allComplete) {{
                                clearInterval(periodicCheck);
                            }}
                        }}, 500); // Check every 500ms
                        
                        // Initial check when section becomes visible - run multiple times
                        const runInitialCheck = () => {{
                            // Ensure tracking exists
                            if (!window[trackingKey]) {{
                                window[trackingKey] = {{
                                    audioPlayed: false,
                                    audioCompleted: !hasAudio,
                                    contentViewed: false,
                                    flashcardsInteracted: !hasFlashcards,
                                    kcCompleted: !hasKC,
                                    allComplete: false
                                }};
                            }}
                            
                            const sectionEl = document.getElementById(sectionId);
                            const continueBtn = document.getElementById('continue-{module_num}-{section_num}');
                            
                            if (sectionEl && continueBtn) {{
                                // If section is visible, mark content as viewed
                                const computedStyle = window.getComputedStyle(sectionEl);
                                if (computedStyle.display !== 'none' && sectionEl.style.display !== 'none') {{
                                    if (!window[trackingKey].contentViewed) {{
                                        window[trackingKey].contentViewed = true;
                                        console.log('Content viewed (initial check) for section {module_num}.{section_num}');
                                    }}
                                }}
                                
                                // Run completion check
                                if (typeof window[funcName] === 'function') {{
                                    window[funcName]();
                                }}
                            }} else {{
                                // If elements not found, log for debugging
                                if (!sectionEl) console.warn('Section element not found:', sectionId);
                                if (!continueBtn) console.warn('Continue button not found:', 'continue-{module_num}-{section_num}');
                            }}
                        }};
                        
                        // Run initial check multiple times with delays
                        setTimeout(runInitialCheck, 500);
                        setTimeout(runInitialCheck, 1000);
                        setTimeout(runInitialCheck, 2000);
                        setTimeout(runInitialCheck, 3000);
                        setTimeout(runInitialCheck, 5000);
                        
                        // Flashcard interaction tracking
                        if (hasFlashcards) {{
                            const flashcardContainer = document.getElementById('section-{module_num}-{section_num}-flashcards');
                            if (flashcardContainer) {{
                                flashcardContainer.addEventListener('click', function() {{
                                    window[trackingKey].flashcardsInteracted = true;
                                    window[funcName]();
                                }}, {{ once: false }});
                            }}
                        }}
                        
                        // Knowledge check completion tracking
                        // NOTE: KC completion is handled by checkKnowledgeCheck() function
                        // which sets window[trackingKey].kcCompleted = true and calls window[funcName]()
                        // No onchange listener needed here - the Submit button flow handles it
                    }})();
                </script>'''
                
                # Close section div
                section_html += '</div>'
                html_parts.append(section_html)
        

        
        return ''.join(html_parts) if html_parts else f'<p>{self._labels["no_content"]}</p>'
    
    def _inject_interactives_into_last_section(self, content_html: str, interactives_html: str, module_num: int, last_section_num: int) -> str:
        """Inject flashcards, knowledge check, and continue button into the last section"""
        last_section_id = f'module-{module_num}-section-{last_section_num}'
        # Find the last section's closing div and insert interactives before it
        pattern = f'(<div class="content-section" id="{last_section_id}"[^>]*>.*?</div>\\s*</div>)'
        import re
        replacement = f'\\1{interactives_html}'
        content_html = re.sub(pattern, replacement, content_html, flags=re.DOTALL)
        return content_html
        

    
    def _build_knowledge_check_html(self, kc: Dict, module_num: int, has_audio: bool = True) -> str:
        """Build knowledge check HTML
        
        Args:
            kc: Knowledge check data dict with question, options, correctAnswer, feedback
            module_num: Module number (1-indexed)
            has_audio: Whether the section containing this KC has audio.
                       If True, KC starts locked (radio disabled, lock message shown).
                       If False, KC is immediately interactive.
        """
        question = self._escape_html(kc.get('question', ''))
        options = kc.get('options', {})
        
        # Radio buttons: disabled only if audio exists (user must listen first)
        radio_disabled = 'disabled' if has_audio else ''
        
        options_html = []
        for key, value in options.items():
            options_html.append(
                f'<button class="kc-option-btn" id="kc-{module_num}-{key}" onclick="selectKCOption({module_num}, &quot;{key}&quot;)" {radio_disabled}>'
                f'  <span class="kc-option-label">{key}</span>'
                f'  <span class="kc-option-text">{self._escape_html(value)}</span>'
                f'</button>'
            )
        
        # KC div: always visible (display: block). The parent section is hidden/shown,
        # so the KC visibility is controlled by the section's display state.
        # Lock message: only shown if audio exists; hidden if no audio.
        lock_display = 'flex' if has_audio else 'none'
        
        return f'''
        <div class="knowledge-check" id="kc-{module_num}" style="display: block;">
            <h3>{self._labels['knowledge_check']}</h3>
            <div class="question-block">
                <p class="question-text">{question}</p>
                <div class="options">
                    {''.join(options_html)}
                </div>
                <div id="kc-feedback-{module_num}" class="feedback"></div>
            </div>
        </div>
        <div id="kc-lock-message-{module_num}" class="lock-message" style="display: {lock_display};">
            <svg class="lock-icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg" style="vertical-align: -2px; margin-right: 6px;">
                <path fill-rule="evenodd" clip-rule="evenodd" d="M8 1a3.5 3.5 0 0 0-3.5 3.5V6H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-.5V4.5A3.5 3.5 0 0 0 8 1Zm1.5 5V4.5a1.5 1.5 0 0 0-3 0V6h3ZM8 9.5a1 1 0 1 0 0 2 1 1 0 0 0 0-2Z"/>
            </svg>
            <span>Please listen to the audio completely before attempting the knowledge check.</span>
        </div>'''
    
    def _build_flashcards_html(self, flashcards: List[Dict], module_num: int, section_num: int = None) -> str:
        """Build flashcards HTML with section-specific IDs"""
        if not flashcards:
            return ""
        
        cards_html = []
        for idx, card in enumerate(flashcards):
            front = self._escape_html(card.get('front', ''))
            back = self._escape_html(card.get('back', ''))
            # Make card IDs unique per section to avoid conflicts
            if section_num is not None:
                card_id = f"fc-{module_num}-{section_num}-{idx}"
            else:
                card_id = f"fc-{module_num}-{idx}"
            
            cards_html.append(f'''
            <div class="flashcard" id="{card_id}" onclick="flipCard('{card_id}')">
                <div class="flashcard-inner">
                    <div class="flashcard-front">
                        <p>{front}</p>
                        <span class="flip-hint">{self._labels["click_to_flip"]}</span>
                    </div>
                    <div class="flashcard-back">
                        <p>{back}</p>
                    </div>
                </div>
            </div>''')
        
        # Use section-specific ID for flashcards section container
        section_suffix = f"-{section_num}" if section_num is not None else ""
        return f'''
        <div class="flashcards-section" id="flashcards-{module_num}{section_suffix}">
            <h3>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg" style="vertical-align: -4px; margin-right: 8px;">
                    <path d="M21 4H7C5.89543 4 5 4.89543 5 6V18C5 19.1046 5.89543 20 7 20H21C22.1046 20 23 19.1046 23 18V6C23 4.89543 22.1046 4 21 4ZM7 6H21V18H7V6Z"/>
                    <path d="M3 2H17V4H3C2.44772 4 2 4.44772 2 5V17H0V5C0 3.34315 1.34315 2 3 2Z"/>
                </svg>
                {self._labels["flashcards_title"]}
            </h3>
            <p>{self._labels["flashcards_hint"]}</p>
            <div class="flashcards-container">
                {''.join(cards_html)}
            </div>
        </div>'''
    
    def _render_interactive_block(self, block: Dict, module_num: int, section_num: int) -> str:
        """Render an interactive block based on its type"""
        if not block or "type" not in block or "data" not in block:
            return ""
            
        b_type = block["type"].lower()  # Normalise capitalisation from Gemini (e.g. "Tabs" → "tabs")
        data = block["data"]
        base_id = f"ib-{module_num}-{section_num}-{b_type}"
        safe_base_id = base_id.replace('-', '_')
        html = []
        
        # Track JS wrapper (adds xAPI statement wrapper and script tags)
        def tracking_script(interaction_id_expr, verb):
            return f"""
            <script>
            function track_{safe_base_id}(id) {{
                if (window.xAPIReady && typeof ADL !== 'undefined' && ADL.XAPIWrapper) {{
                    var stmt = {{
                        "actor": window.currentActor || {{"mbox": "mailto:anonymous@example.com", "name": "Anonymous"}},
                        "verb": {{ "id": "http://adlnet.gov/expapi/verbs/" + "{verb}" }},
                        "object": {{
                            "id": (window.courseId || "course") + "/module-{module_num}/interactive/{b_type}/" + id,
                            "definition": {{ "type": "http://adlnet.gov/expapi/activities/interaction" }}
                        }}
                    }};
                    try {{ ADL.XAPIWrapper.sendStatement(stmt); }} catch (e) {{ console.error("xAPI interactive error:", e); }}
                }}
            }}
            </script>
            """
            
        if b_type == "tabs":
            tabs = data.get("tabs", [])
            if not tabs: return ""
            
            html.append(tracking_script("id", "interacted"))
            
            # CSS
            html.append(f"""
            <style>
            .ib-tabs-{base_id} {{ margin: 28px 0; border: 2px solid rgba(31, 111, 178, 0.38); border-radius: 16px; background: linear-gradient(180deg, #f7fbff 0%, #ffffff 38%); box-shadow: 0 8px 24px rgba(16, 24, 40, 0.08); overflow: hidden; }}
            .ib-tab-buttons-{base_id} {{ display: flex; align-items: center; overflow-x: auto; scrollbar-width: none; gap: 10px; padding: 12px; background: #f2f7fd; border-bottom: 1px solid var(--border-subtle, #dbe3ef); }}
            .ib-tab-buttons-{base_id}::-webkit-scrollbar {{ display: none; }}
            .ib-tab-btn-{base_id} {{ flex: 1; min-width: 140px; padding: 11px 16px; border: 1px solid transparent; background: transparent; cursor: pointer; font-weight: 700; font-size: 14px; text-align: center; color: #435266; transition: all 0.2s ease-in-out; white-space: nowrap; border-radius: 999px; }}
            .ib-tab-btn-{base_id}:hover {{ color: #1f2e40; background: #e7eff8; border-color: #d6e3f2; }}
            .ib-tab-btn-{base_id}:focus-visible {{ outline: 2px solid var(--primary-color, #1f6fb2); outline-offset: 2px; }}
            .ib-tab-btn-{base_id}.active {{ color: #ffffff; background: var(--primary-color, #1f6fb2); border-color: var(--primary-color, #1f6fb2); box-shadow: 0 6px 14px rgba(31, 111, 178, 0.28); }}
            .ib-tab-content-{base_id} {{ padding: 24px; display: none; font-size: 15px; line-height: 1.72; color: #243446; background: #ffffff; }}
            .ib-tab-content-{base_id}.active {{ display: block; animation: tabFadeIn 0.4s ease-out; }}
            @keyframes tabFadeIn {{ from {{ opacity: 0; transform: translateY(5px); }} to {{ opacity: 1; transform: translateY(0); }} }}
            @media (max-width: 768px) {{
                .ib-tabs-{base_id} {{ margin: 20px 0; border-radius: 12px; }}
                .ib-tab-buttons-{base_id} {{ padding: 10px; gap: 8px; }}
                .ib-tab-btn-{base_id} {{ min-width: 124px; font-size: 13px; padding: 10px 12px; }}
                .ib-tab-content-{base_id} {{ padding: 18px; font-size: 14px; }}
            }}
            </style>
            """)
            
            # HTML
            html.append(f'<div class="ib-tabs-{base_id}">')
            html.append(f'<div class="ib-tab-buttons-{base_id}">')
            for i, tab in enumerate(tabs):
                active = "active" if i == 0 else ""
                title = self._escape_html(tab.get("title", f"Tab {i+1}"))
                html.append(f'<button class="ib-tab-btn-{base_id} {active}" onclick="switchTab_{safe_base_id}({i})">{title}</button>')
            html.append('</div>')
            
            for i, tab in enumerate(tabs):
                active = "active" if i == 0 else ""
                content = self._format_content(tab.get("content", ""))
                html.append(f'<div class="ib-tab-content-{base_id} {active}" id="tab-content-{base_id}-{i}">{content}</div>')
                
            html.append('</div>')
            
            # JS
            html.append(f"""
            <script>
            function switchTab_{safe_base_id}(index) {{
                // Update buttons
                var btns = document.querySelectorAll('.ib-tab-btn-{base_id}');
                btns.forEach(function(b, i) {{ if(i===index) b.classList.add('active'); else b.classList.remove('active'); }});
                
                // Update content
                var contents = document.querySelectorAll('.ib-tab-content-{base_id}');
                contents.forEach(function(c, i) {{ if(i===index) c.classList.add('active'); else c.classList.remove('active'); }});
                
                // Tracking
                if (typeof track_{safe_base_id} === 'function') {{
                    track_{safe_base_id}('tab-' + index);
                }}
            }}
            </script>
            """)

        elif b_type == "accordion":
            items = data.get("items", [])
            if not items: return ""
            
            html.append(tracking_script("id", "interacted"))
            
            html.append(f"""
            <style>
            .ib-acc-{base_id} {{ display: flex; flex-direction: column; gap: 12px; margin: 28px 0; }}
            .ib-acc-item-{base_id} {{ border: 2px solid rgba(31, 111, 178, 0.35); border-radius: 14px; overflow: hidden; background: #ffffff; box-shadow: 0 6px 18px rgba(16, 24, 40, 0.06); }}
            .ib-acc-summary-{base_id} {{ padding: 16px 18px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; font-weight: 700; font-size: 15px; color: #243446; user-select: none; transition: background 0.2s, color 0.2s; list-style: none; background: linear-gradient(180deg, #f8fbff 0%, #f2f7fd 100%); }}
            .ib-acc-summary-{base_id}::-webkit-details-marker {{ display: none; }}
            .ib-acc-summary-{base_id}:hover {{ background: #e9f2fb; color: #1c3048; }}
            .ib-acc-icon-{base_id} {{ transition: transform 0.2s; color: var(--text-muted, #5b6777); flex-shrink: 0; margin-left: 12px; }}
            details[open] .ib-acc-icon-{base_id} {{ transform: rotate(180deg); }}
            details[open] .ib-acc-summary-{base_id} {{ background: #e2edf9; }}
            .ib-acc-content-{base_id} {{ padding: 16px 18px 18px 18px; font-size: 15px; line-height: 1.7; color: #2b3b4e; border-top: 1px solid var(--border-subtle, #dbe3ef); background: #ffffff; }}
            @media (max-width: 768px) {{
                .ib-acc-{base_id} {{ gap: 10px; margin: 20px 0; }}
                .ib-acc-summary-{base_id} {{ padding: 14px 14px; font-size: 14px; }}
                .ib-acc-content-{base_id} {{ padding: 14px; font-size: 14px; }}
            }}
            </style>
            """)
            
            html.append(f'<div class="ib-acc-{base_id}">')
            for i, item in enumerate(items):
                q = self._escape_html(item.get("question", f"Item {i+1}"))
                a = self._format_content(item.get("answer", ""))
                html.append(f"""
                <details class="ib-acc-item-{base_id}" ontoggle="if(this.open) track_{safe_base_id}('item-{i}')">
                    <summary class="ib-acc-summary-{base_id}">
                        <span>{q}</span>
                        <svg class="ib-acc-icon-{base_id}" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
                    </summary>
                    <div class="ib-acc-content-{base_id}">{a}</div>
                </details>
                """)
            html.append('</div>')

        elif b_type == "note":
            variant = data.get("variant", "info")
            text = self._format_content(data.get("text", ""))
            if not text: return ""
            
            colors = {
                "info":    {"bg": "#eef2ff", "border": "#6366f1", "icon": "ℹ️"},
                "tip":     {"bg": "#f0fdfa", "border": "#14b8a6", "icon": "💡"},
                "warning": {"bg": "#fffbeb", "border": "#f59e0b", "icon": "⚠️"}
            }
            theme = colors.get(variant, colors["info"])
            
            html.append(f"""
            <style>
            .ib-note-{base_id} {{ margin: 24px 0; background: {theme['bg']}; border: 2px solid rgba(31, 111, 178, 0.30); border-left: 5px solid {theme['border']}; padding: 14px 16px; border-radius: 12px; display: flex; gap: 12px; color: #1f2937; box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05); }}
            .ib-note-icon-{base_id} {{ font-size: 20px; line-height: 1; flex-shrink: 0; margin-top: 1px; }}
            .ib-note-content-{base_id} {{ font-size: 15px; line-height: 1.68; }}
            @media (max-width: 768px) {{
                .ib-note-{base_id} {{ margin: 18px 0; padding: 12px 13px; border-radius: 10px; gap: 10px; }}
                .ib-note-content-{base_id} {{ font-size: 14px; }}
            }}
            </style>
            <div class="ib-note-{base_id}">
                <div class="ib-note-icon-{base_id}">{theme['icon']}</div>
                <div class="ib-note-content-{base_id}">{text}</div>
            </div>
            """)

        elif b_type == "table":
            headers = data.get("headers", [])
            rows = data.get("rows", [])
            if not headers and not rows: return ""
            
            html.append(f"""
            <style>
            .ib-table-shell-{base_id} {{ margin: 28px 0; border: 2px solid rgba(31, 111, 178, 0.34); border-radius: 14px; box-shadow: 0 8px 20px rgba(16, 24, 40, 0.06); overflow: hidden; background: #ffffff; }}
            .ib-table-wrapper-{base_id} {{ overflow-x: auto; width: 100%; }}
            .ib-table-{base_id} {{ width: 100%; min-width: 540px; border-collapse: collapse; text-align: left; font-size: 14px; }}
            .ib-table-{base_id} th {{ background: #f2f7fd; padding: 13px 16px; font-weight: 700; border-bottom: 1px solid var(--border-subtle, #dbe3ef); color: #243446; }}
            .ib-table-{base_id} td {{ padding: 12px 16px; border-bottom: 1px solid var(--border-subtle, #dbe3ef); color: #324559; vertical-align: top; }}
            .ib-table-{base_id} tr:last-child td {{ border-bottom: none; }}
            .ib-table-{base_id} tbody tr:nth-child(odd) {{ background: #fcfdff; }}
            @media (max-width: 768px) {{
                .ib-table-shell-{base_id} {{ margin: 20px 0; border-radius: 12px; }}
                .ib-table-{base_id} {{ font-size: 13px; min-width: 460px; }}
                .ib-table-{base_id} th, .ib-table-{base_id} td {{ padding: 10px 12px; }}
            }}
            </style>
            """)
            
            html.append(f'<div class="ib-table-shell-{base_id}"><div class="ib-table-wrapper-{base_id}"><table class="ib-table-{base_id}">')
            if headers:
                html.append('<thead><tr>')
                for h in headers:
                    html.append(f'<th>{self._escape_html(h)}</th>')
                html.append('</tr></thead>')
                
            if rows:
                html.append('<tbody>')
                for row in rows:
                    html.append('<tr>')
                    for cell in row:
                        html.append(f'<td>{self._escape_html(cell)}</td>')
                    html.append('</tr>')
                html.append('</tbody>')
            html.append('</table></div></div>')

        elif b_type == "flipcard":
            cards = data.get("cards") or data.get("flashcards", [])
            if not cards: return ""
            
            html.append(tracking_script("id", "interacted"))
            
            html.append(f"""
            <style>
            .ib-flip-shell-{base_id} {{ margin: 28px 0; border: 2px solid rgba(31, 111, 178, 0.38); border-radius: 16px; background: linear-gradient(180deg, #f8fbff 0%, #ffffff 42%); box-shadow: 0 8px 24px rgba(16, 24, 40, 0.08); padding: 16px; }}
            .ib-flip-grid-{base_id} {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }}
            .ib-flip-card-{base_id} {{ background: transparent; height: 180px; perspective: 1000px; cursor: pointer; }}
            .ib-flip-inner-{base_id} {{ position: relative; width: 100%; height: 100%; text-align: center; transition: transform 0.6s; transform-style: preserve-3d; border-radius: 12px; }}
            .ib-flip-card-{base_id}.flipped .ib-flip-inner-{base_id} {{ transform: rotateY(180deg); }}
            .ib-flip-front-{base_id}, .ib-flip-back-{base_id} {{ position: absolute; width: 100%; height: 100%; backface-visibility: hidden; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 16px; border-radius: 12px; border: 2px solid rgba(31, 111, 178, 0.42); }}
            .ib-flip-front-{base_id} {{ background: linear-gradient(160deg, #1f6fb2 0%, #18598f 100%); font-weight: 700; font-size: 16px; color: #ffffff; box-shadow: 0 10px 18px rgba(24, 89, 143, 0.30); }}
            .ib-flip-back-{base_id} {{ background: #ffffff; font-size: 14px; color: #2b3b4e; transform: rotateY(180deg); overflow-y: auto; line-height: 1.65; }}
            .ib-flip-hint-{base_id} {{ font-size: 11px; color: #d6e8fb; font-weight: 600; margin-top: 12px; text-transform: uppercase; letter-spacing: 0.5px; }}
            .ib-flip-card-{base_id}:hover .ib-flip-inner-{base_id} {{ transform: translateY(-2px); }}
            .ib-flip-card-{base_id}.flipped:hover .ib-flip-inner-{base_id} {{ transform: rotateY(180deg) translateY(-2px); }}
            @media (max-width: 768px) {{
                .ib-flip-shell-{base_id} {{ margin: 20px 0; border-radius: 12px; padding: 12px; }}
                .ib-flip-grid-{base_id} {{ grid-template-columns: 1fr; gap: 12px; }}
                .ib-flip-card-{base_id} {{ height: 170px; }}
                .ib-flip-front-{base_id} {{ font-size: 15px; }}
                .ib-flip-back-{base_id} {{ font-size: 13px; }}
            }}
            </style>
            """)
            
            html.append(f'<div class="ib-flip-shell-{base_id}"><div class="ib-flip-grid-{base_id}">')
            for i, card in enumerate(cards):
                front = self._escape_html(card.get("front", f"Card {i+1}"))
                back = self._format_content(card.get("back", ""))
                html.append(f"""
                <div class="ib-flip-card-{base_id}" id="{base_id}-card-{i}" onclick="this.classList.toggle('flipped'); track_{safe_base_id}('card-{i}')">
                    <div class="ib-flip-inner-{base_id}">
                        <div class="ib-flip-front-{base_id}">
                            {front}
                            <div class="ib-flip-hint-{base_id}">{self._labels["click_to_flip"]}</div>
                        </div>
                        <div class="ib-flip-back-{base_id}">
                            {back}
                        </div>
                    </div>
                </div>
                """)
            html.append('</div></div>')
            
        return "\n".join(html)


    def _get_quiz_section(self, quiz: Dict) -> str:
        """Build quiz section HTML"""
        if not quiz or 'questions' not in quiz:
            return ""
        
        questions_html = []
        for idx, question in enumerate(quiz['questions']):
            q_html = f'<div class="question-block" id="q-{idx}">'
            q_html += f'<p class="question-number">{self._labels["question"]} {idx + 1}</p>'
            q_html += f'<p class="question-text">{self._escape_html(question.get("question", ""))}</p>'
            q_html += '<div class="options">'
            
            for key, value in question.get('options', {}).items():
                q_html += f'<button class="kc-option-btn" id="quiz-q-{idx}-{key}" onclick="selectQuizOption({idx}, &quot;{key}&quot;)">'
                q_html += f'<span class="kc-option-label">{key}.</span>'
                q_html += f'<span class="kc-option-text">{self._escape_html(value)}</span>'
                q_html += '</button>'
            
            q_html += '</div>'
            q_html += f'<div id="quiz-feedback-{idx}" class="feedback"></div>'
            q_html += '</div>'
            questions_html.append(q_html)
        
        return f'''
        <section class="quiz-intro-section" id="quizIntroSection" style="display: none;">
            <div class="quiz-intro-content">
                <h2>{self._labels["final_quiz"]}</h2>
                <p>{self._labels["quiz_completed_msg"]}</p>
                <p>{self._labels["quiz_pass_req"].format(len(quiz.get("questions", [])))}</p>
                <button class="btn-primary btn-start-quiz" onclick="startQuiz()">{self._labels["start_quiz"]}</button>
            </div>
        </section>
        <section class="quiz-section" id="quizSection" style="display: none;">
            <div class="quiz-progress-bar">
                <div class="quiz-progress-fill" id="quizProgressFill"></div>
                <span class="quiz-progress-text" id="quizProgressText">{self._labels["question_x_of_y"].format(1, len(quiz.get("questions", [])))}</span>
            </div>
            <div id="quizSlideContainer" class="quiz-slide-container">
                <!-- Quiz questions will be shown one at a time -->
            </div>
            <div class="quiz-navigation" id="quiz-navigation">
                <button class="btn-primary" id="quizNextBtn" onclick="nextQuizQuestion()" disabled>{self._labels["next_btn"]}</button>
            </div>
        </section>
        <section class="quiz-results-section" id="quizResultsSection" style="display: none;">
            <div class="quiz-results-page" id="quizResultsPage"></div>
        </section>'''
    
    def _get_completion_section(self) -> str:
        return f'''
        <section class="completion-section" id="completionSection" style="display: none;">
            <div class="completion-content">
                <div class="completion-icon">&#10003;</div>
                <h2>{self._labels["thank_you"]}</h2>
                <p>{self._labels["course_completed"]}</p>
                <p>{self._labels["course_valuable"]}</p>
                <div class="completion-buttons">

                    <button class="btn-primary btn-exit" onclick="exitCourse()">{self._labels["exit_course"]}</button>
                </div>
            </div>
        </section>'''
    
    def _get_html_footer(self, course_data: Dict) -> str:
        course_json = json.dumps(course_data).replace('</script>', '<\\/script>')
        js_content = self._get_js_content()
        
        # AI disclaimer footer (only if enabled)
        ai_footer_html = ''
        if getattr(self, '_show_ai_footer', True):
            ai_footer_html = f'''
    <div id="ai-disclaimer-footer" style="position: fixed; bottom: 0; left: 0; right: 0; z-index: 9999; background: rgba(30, 30, 30, 0.92); backdrop-filter: blur(6px); color: #b0b0b0; text-align: center; padding: 8px 16px; font-size: 12px; font-family: 'Roboto', 'Arial', sans-serif; border-top: 1px solid rgba(255,255,255,0.08);">
        <div class="ai-disclaimer">
        <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg" style="vertical-align: -2px; margin-right: 4px;"><path fill-rule="evenodd" clip-rule="evenodd" d="M8 0l1.938 4.062L14 6l-4.062 1.938L8 12l-1.938-4.062L2 6l4.062-1.938L8 0zm4 10l1.292 2.708L16 14l-2.708 1.292L12 18l-1.292-2.708L8 14l2.708-1.292L12 10z"/></svg> {self._labels["ai_disclaimer"]}
        </div>
    <style>
        /* Add bottom padding so footer doesn't overlap course content */
        body {{ padding-bottom: 60px; }}
    </style>'''
        
        return f'''
    {ai_footer_html}
    <script>
        window.courseData = {course_json};
        window.uiLabels = {json.dumps({k: v for k, v in self._labels.items() if k in [
            'quiz_results','you_scored','congratulations','passed_quiz_msg',
            'certificate_title','certificate_body','exit_course','try_again_title',
            'try_again_msg','attempts_remaining','no_attempts','contact_instructor',
            'submit_quiz','question_x_of_y','pct_complete','incorrect','question',
            'flashcards_title','flashcards_hint','click_to_flip',
            'error_refresh','complete_prev_module','no_modules_found','select_answer',
            'thank_you','course_completed','course_valuable', 'kc_lock_message',
            'next_btn','continue_btn','correct','try_again'
        ]}, ensure_ascii=False)};
        {js_content}
    </script>
</body>
</html>'''
    
    def _format_content(self, content: str) -> str:
        """Format content with paragraphs and markdown"""
        if not content:
            return ""
            
        # Parse markdown if present
        try:
            return markdown.markdown(content)
        except Exception as e:
            logger.error(f"Markdown formatting error: {e}")
            
        # Fallback if markdown parser fails
        if any(tag in content for tag in ['<p>', '<h3>', '<h4>', '<ul>', '<ol>', '<li>', '<strong>', '<em>']):
            return content
            
        # Split by double newlines for plain text paragraphs
        paragraphs = content.split('\n\n')
        formatted = []
        for para in paragraphs:
            para = para.strip().replace('\n', '<br>')
            if para:
                formatted.append(f'<p>{self._escape_html(para)}</p>')
        return ''.join(formatted)
    
    def _escape_html(self, text: Any) -> str:
        """Escape HTML special characters"""
        import html
        if text is None:
            return ""
        text = str(text)
        # Unescape first to prevent double-escaping (e.g. &amp; -> &amp;amp;)
        text = html.unescape(text)
        return (text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace('"', "&quot;")
                   .replace("'", "&#039;"))
    
    def _get_xapi_wrapper_content(self) -> str:
        """Get official ADL xAPI Wrapper content from file"""
        # Read the official ADL xAPIWrapper v1.11.0 from the project directory
        import os
        wrapper_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'xapiwrapper.min.js')
        try:
            with open(wrapper_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Official xAPIWrapper not found at {wrapper_path}")
            raise FileNotFoundError(f"Official ADL xAPIWrapper file not found at: {wrapper_path}. Please ensure xapiwrapper.min.js is in the project root.")

    def _get_css_content(self) -> str:
        """Get complete CSS content from external file"""
        import os
        css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'styles.css')
        with open(css_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _get_js_content(self) -> str:
        """Get complete JavaScript content from external file"""
        import os
        js_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'script.js')
        with open(js_path, 'r', encoding='utf-8') as f:
            return f.read()


# Create instance
xAPIGenerator_instance = xAPIGenerator()
